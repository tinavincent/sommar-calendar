"""Step 1: Discover episodes from presentation page."""

import json
import sys
import urllib.error
import urllib.request

from season_import.paths import discover_cache, fixtures_dir, list_fixture
from sr_parser import parse_list_page


def fetch_url(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", "ignore")


def run_discover(year: int, source_url: str, refresh: bool = False) -> list[dict]:
    fixture_dir = fixtures_dir(year)
    fixture_dir.mkdir(parents=True, exist_ok=True)
    list_path = list_fixture(year)

    if refresh or not list_path.exists():
        print(f"Fetching presentation page for {year}...")
        try:
            content = fetch_url(source_url)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            if list_path.exists():
                print(f"Fetch failed ({exc!r}), using cached list page.", file=sys.stderr)
                content = list_path.read_text(encoding="utf-8")
            else:
                print(f"Discover failed: {exc!r}", file=sys.stderr)
                sys.exit(1)
        else:
            list_path.write_text(content, encoding="utf-8")
            print(f"Saved list page to {list_path}")
    else:
        print(f"Using cached list page: {list_path}")
        content = list_path.read_text(encoding="utf-8")

    entries = parse_list_page(content, year=year)
    cache_path = discover_cache(year)
    cache_path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Discovered {len(entries)} episodes for {year}")
    return entries
