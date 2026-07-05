"""Refresh host portrait URLs from SR episode pages."""

import json
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from season_import.enrich import enrich_episode_from_fixture, load_discovered_entries
from season_import.paths import (
    EPISODE_TIMEOUT,
    MAX_FETCH_DELAY,
    MIN_FETCH_DELAY,
    fixtures_dir,
    portraits_cache,
)
from sr_api import api_fixture_path, extract_episode_id, has_portrait
from sr_parser import (
    episode_slug_candidates,
    fixture_path_for,
    is_valid_fixture,
    parse_portrait_url,
)


def fetch_url(url: str, timeout: int = EPISODE_TIMEOUT) -> str:
    current = url
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "sv-SE,sv;q=0.9",
    }

    for _ in range(5):
        request = urllib.request.Request(current, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as exc:
            if exc.code in (301, 302, 303, 307, 308):
                location = exc.headers.get("Location")
                if not location:
                    raise
                current = urllib.parse.urljoin(current, location)
                continue
            raise

    raise urllib.error.URLError(f"Too many redirects for {url}")


def load_portraits_cache(year: int) -> dict:
    path = portraits_cache(year)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_portraits_cache(year: int, portraits: dict) -> None:
    path = portraits_cache(year)
    path.write_text(json.dumps(portraits, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_api_title(fixture_dir, episode_id: str) -> str:
    path = api_fixture_path(fixture_dir, episode_id)
    if not path.exists():
        return ""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    episode = payload.get("episode")
    if not isinstance(episode, dict):
        return ""
    return episode.get("title") or ""


def portrait_page_urls(entry: dict, year: int, fixture_dir) -> list[str]:
    episode_id = entry["episodeId"]
    api_title = load_api_title(fixture_dir, episode_id)
    urls = episode_slug_candidates(entry["host"], year, api_title=api_title)
    numeric_url = entry["srUrl"]
    if numeric_url not in urls:
        urls.append(numeric_url)
    return urls


def episodes_missing_portrait(year: int) -> list[dict]:
    fixture_dir = fixtures_dir(year)
    entries = load_discovered_entries(year)
    missing = []

    for entry in entries:
        enriched = enrich_episode_from_fixture(entry, fixture_dir, year)
        if has_portrait(enriched):
            continue
        episode_id = extract_episode_id(entry["srUrl"])
        if not episode_id:
            continue
        missing.append({**entry, "episodeId": episode_id})

    return missing


def refresh_episode_portrait(entry: dict, year: int, fixture_dir, cache: dict) -> str:
    """Return 'fetched', 'skipped', or 'failed'."""
    episode_id = entry["episodeId"]
    if cache.get(episode_id):
        return "skipped"

    api_title = load_api_title(fixture_dir, episode_id)
    html_path = fixture_path_for(fixture_dir, entry["srUrl"])

    for url in portrait_page_urls(entry, year, fixture_dir):
        print(f"Fetching portrait page for {entry['host']} ({url})...")
        try:
            content = fetch_url(url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"  Failed: {exc!r}", file=sys.stderr)
            continue

        portrait_url = parse_portrait_url(content)
        if not portrait_url:
            print("  Failed: no portrait found in response", file=sys.stderr)
            continue

        cache[episode_id] = portrait_url
        if is_valid_fixture(content, entry["host"], alt_hosts=(api_title,)):
            html_path.write_text(content, encoding="utf-8")
            print(f"  Saved HTML fixture: {html_path.name}")
        print(f"  Saved portrait: {portrait_url}")
        return "fetched"

    return "failed"


def run_refresh_portraits(year: int, limit: int = 5) -> dict:
    fixture_dir = fixtures_dir(year)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    cache = load_portraits_cache(year)
    pending = episodes_missing_portrait(year)

    print(f"\nEpisodes missing portrait: {len(pending)}")
    if not pending:
        print("Nothing to refresh.")
        return {"fetched": 0, "skipped": 0, "failed": [], "pending": 0}

    batch = pending[:limit]
    print(f"Refreshing up to {len(batch)} portrait(s) this run...")

    fetched = 0
    skipped = 0
    failed = []

    for index, entry in enumerate(batch):
        if index > 0:
            delay = random.uniform(MIN_FETCH_DELAY, MAX_FETCH_DELAY)
            print(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

        if cache.get(entry["episodeId"]):
            skipped += 1
            continue

        result = refresh_episode_portrait(entry, year, fixture_dir, cache)
        if result == "fetched":
            fetched += 1
        elif result == "skipped":
            skipped += 1
        else:
            failed.append({"host": entry["host"], "episodeUrl": entry["srUrl"]})

    save_portraits_cache(year, cache)
    remaining = len(episodes_missing_portrait(year))
    print(f"\nPortraits cached: {len(cache)}")
    print(f"Still missing portrait: {remaining}")

    return {"fetched": fetched, "skipped": skipped, "failed": failed, "pending": remaining}
