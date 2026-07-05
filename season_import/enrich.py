"""Step 2: Enrich episodes from individual episode pages."""

import random
import sys
import time
import urllib.error
import urllib.request

from season_import.paths import (
    EPISODE_TIMEOUT,
    MAX_ENRICH_PER_RUN,
    MAX_FETCH_DELAY,
    MIN_FETCH_DELAY,
    discover_cache,
    fixtures_dir,
)
from sr_parser import (
    audit_fixtures,
    classify_fixture,
    fixture_path_for,
    is_valid_fixture,
    parse_enriched_episode,
    parse_list_page,
)
from season_import.paths import list_fixture


def fetch_url(url: str, timeout: int = EPISODE_TIMEOUT) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def load_discovered_entries(year: int) -> list[dict]:
    cache = discover_cache(year)
    if cache.exists():
        import json

        return json.loads(cache.read_text(encoding="utf-8"))
    return parse_list_page(list_fixture(year).read_text(encoding="utf-8"), year=year)


def fetch_episode(entry: dict, fixture_dir) -> str:
    """Return 'skipped', 'fetched', or 'failed'."""
    host = entry["host"]
    sr_url = entry["srUrl"]
    path = fixture_path_for(fixture_dir, sr_url)

    if path.exists():
        existing = path.read_text(encoding="utf-8", errors="ignore")
        if is_valid_fixture(existing, host):
            print(f"Skipping {host} — valid fixture already exists.")
            return "skipped"

    print(f"Fetching {host} ({sr_url})...")
    try:
        content = fetch_url(sr_url)
    except urllib.error.HTTPError as exc:
        print(f"  Failed: HTTP {exc.code}", file=sys.stderr)
        return "failed"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  Failed: {exc!r}", file=sys.stderr)
        return "failed"

    if not is_valid_fixture(content, host):
        if path.exists():
            path.unlink()
        print("  Failed: rate-limited or invalid response", file=sys.stderr)
        return "failed"

    path.write_text(content, encoding="utf-8")
    print(f"  Saved valid fixture: {path.name}")
    return "fetched"


def run_enrich(year: int, limit: int = MAX_ENRICH_PER_RUN) -> dict:
    fixture_dir = fixtures_dir(year)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    entries = load_discovered_entries(year)
    audit = audit_fixtures(entries, fixture_dir)

    print(f"\nValid fixtures: {len(audit['valid'])}")
    print(f"Missing fixtures: {len(audit['missing'])}")
    print(f"Failed fixtures: {len(audit['failed'])}")

    pending = audit["missing"] + audit["failed"]
    if not pending:
        print("\nNothing to enrich.")
        return {"fetched": 0, "skipped": 0, "failed": [], "audit": audit}

    batch = pending[:limit]
    print(f"\nEnriching up to {len(batch)} episode page(s) this run...")

    fetched = 0
    skipped = 0
    failed = []

    for index, record in enumerate(batch):
        if index > 0:
            delay = random.uniform(MIN_FETCH_DELAY, MAX_FETCH_DELAY)
            print(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

        entry = next(item for item in entries if item["srUrl"] == record["srUrl"])
        result = fetch_episode(entry, fixture_dir)
        if result == "fetched":
            fetched += 1
        elif result == "skipped":
            skipped += 1
        else:
            failed.append({"host": entry["host"], "episodeUrl": entry["srUrl"]})

    audit = audit_fixtures(entries, fixture_dir)
    return {"fetched": fetched, "skipped": skipped, "failed": failed, "audit": audit}


def enrich_episode_from_fixture(entry: dict, fixture_dir) -> dict:
    path = fixture_path_for(fixture_dir, entry["srUrl"])
    if classify_fixture(path, entry["host"]) != "valid":
        return parse_enriched_episode("", entry["host"])
    return parse_enriched_episode(path.read_text(encoding="utf-8"), entry["host"])
