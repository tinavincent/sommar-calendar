"""Step 2: Enrich episodes from Sveriges Radio API (cached HTML fallback only)."""

import json
import random
import sys
import time
import urllib.error
import urllib.request
from typing import Optional

from season_import.paths import (
    EPISODE_TIMEOUT,
    MAX_ENRICH_PER_RUN,
    MAX_FETCH_DELAY,
    MIN_FETCH_DELAY,
    discover_cache,
    fixtures_dir,
    list_fixture,
)
from sr_api import (
    IMPORTANT_ENRICH_FIELDS,
    SR_API_EPISODE_URL,
    api_fixture_path,
    audit_api_fixtures,
    compute_enrich_status,
    empty_enrichment,
    extract_episode_id,
    is_valid_api_fixture,
    parse_api_fixture,
)
from sr_parser import (
    fixture_path_for,
    is_valid_fixture,
    parse_enriched_episode,
    parse_list_page,
)


def fetch_url(url: str, timeout: int = EPISODE_TIMEOUT) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def load_discovered_entries(year: int) -> list[dict]:
    cache = discover_cache(year)
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    return parse_list_page(list_fixture(year).read_text(encoding="utf-8"), year=year)


def fetch_api_episode(episode_id: str) -> tuple[Optional[dict], Optional[str]]:
    url = SR_API_EPISODE_URL.format(episode_id=episode_id)
    try:
        raw = fetch_url(url)
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, repr(exc)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"

    episode = payload.get("episode")
    if not isinstance(episode, dict):
        return None, "missing episode object"

    return payload, None


def fill_missing_from_html_fixture(enriched: dict, entry: dict, fixture_dir) -> dict:
    if enriched.get("enrichStatus") == "api_failed":
        return enriched
    if all(enriched.get(field) for field in IMPORTANT_ENRICH_FIELDS):
        return enriched

    html_path = fixture_path_for(fixture_dir, entry["srUrl"])
    if not html_path.exists():
        return enriched

    content = html_path.read_text(encoding="utf-8", errors="ignore")
    if not is_valid_fixture(content, entry["host"]):
        return enriched

    parsed = parse_enriched_episode(content, entry["host"])
    for field in IMPORTANT_ENRICH_FIELDS:
        if enriched.get(field) is None and parsed.get(field):
            enriched[field] = parsed[field]

    if enriched.get("previousSommarYears") is None and parsed.get("previousSommarYears"):
        enriched["previousSommarYears"] = parsed["previousSommarYears"]

    enriched["enrichStatus"] = compute_enrich_status(enriched)
    return enriched


def fetch_episode_api(entry: dict, fixture_dir) -> str:
    """Return 'skipped', 'fetched', or 'failed'."""
    episode_id = extract_episode_id(entry["srUrl"])
    if not episode_id:
        print(f"Skipping {entry['host']} — no episode id in URL.", file=sys.stderr)
        return "failed"

    path = api_fixture_path(fixture_dir, episode_id)
    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="ignore")
        if is_valid_api_fixture(existing, episode_id):
            print(f"Skipping {entry['host']} — valid API fixture already exists.")
            return "skipped"

    print(f"Fetching API metadata for {entry['host']} ({episode_id})...")
    payload, error = fetch_api_episode(episode_id)
    if error:
        print(f"  Failed: {error}", file=sys.stderr)
        return "failed"

    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"  Saved API fixture: {path.name}")
    return "fetched"


def enrich_episode_from_fixture(entry: dict, fixture_dir) -> dict:
    episode_id = extract_episode_id(entry["srUrl"])
    if not episode_id:
        return empty_enrichment("api_failed")

    path = api_fixture_path(fixture_dir, episode_id)
    if not path.exists():
        return empty_enrichment("api_failed")

    raw = path.read_text(encoding="utf-8", errors="ignore")
    if not is_valid_api_fixture(raw, episode_id):
        return empty_enrichment("api_failed")

    enriched = parse_api_fixture(raw, entry["host"])
    enriched = fill_missing_from_html_fixture(enriched, entry, fixture_dir)
    enriched["enrichStatus"] = compute_enrich_status(enriched)
    return enriched


def run_enrich(year: int, limit: int = MAX_ENRICH_PER_RUN) -> dict:
    fixture_dir = fixtures_dir(year)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    entries = load_discovered_entries(year)
    audit = audit_api_fixtures(entries, fixture_dir)

    print(f"\nValid API fixtures: {len(audit['valid'])}")
    print(f"Missing API fixtures: {len(audit['missing'])}")
    print(f"Failed API fixtures: {len(audit['failed'])}")

    pending = audit["missing"] + audit["failed"]
    if not pending:
        print("\nNothing to enrich.")
        return {"fetched": 0, "skipped": 0, "failed": [], "audit": audit}

    batch = pending[:limit]
    print(f"\nEnriching up to {len(batch)} episode(s) via API this run...")

    fetched = 0
    skipped = 0
    failed = []

    for index, record in enumerate(batch):
        if index > 0:
            delay = random.uniform(MIN_FETCH_DELAY, MAX_FETCH_DELAY)
            print(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

        entry = next(item for item in entries if item["srUrl"] == record["episodeUrl"])
        result = fetch_episode_api(entry, fixture_dir)
        if result == "fetched":
            fetched += 1
        elif result == "skipped":
            skipped += 1
        else:
            failed.append({"host": entry["host"], "episodeUrl": entry["srUrl"]})

    audit = audit_api_fixtures(entries, fixture_dir)
    return {"fetched": fetched, "skipped": skipped, "failed": failed, "audit": audit}
