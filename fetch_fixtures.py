#!/usr/bin/env python3
"""Incrementally fetch episode page fixtures (max 5 per run)."""

import argparse
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from sr_parser import (
    audit_fixtures,
    fixture_path_for,
    is_valid_fixture,
    parse_list_page,
    print_fixture_summary,
)

ROOT = Path(__file__).parent
FIXTURES_DIR = ROOT / "fixtures" / "full"
LIST_FIXTURE = FIXTURES_DIR / "list-page.txt"
SOURCE_URL = "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan"
MAX_PER_RUN = 5
MIN_DELAY = 5
MAX_DELAY = 10
EPISODE_TIMEOUT = 15


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


def ensure_list_fixture(refresh_list: bool) -> None:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    if refresh_list or not LIST_FIXTURE.exists():
        print("Fetching list page...")
        try:
            content = fetch_url(SOURCE_URL, timeout=30)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"List fetch failed: {exc!r}", file=sys.stderr)
            if not LIST_FIXTURE.exists():
                sys.exit(1)
            print("Using existing list fixture.", file=sys.stderr)
            return
        LIST_FIXTURE.write_text(content, encoding="utf-8")
        print(f"Saved list page to {LIST_FIXTURE}")


def load_list_entries() -> list:
    if not LIST_FIXTURE.exists():
        print(f"Missing list fixture: {LIST_FIXTURE}", file=sys.stderr)
        print("Run: python3 fetch_fixtures.py --refresh-list", file=sys.stderr)
        sys.exit(1)
    return parse_list_page(LIST_FIXTURE.read_text(encoding="utf-8"))


def fetch_episode(entry: dict) -> tuple[bool, str]:
    host = entry["host"]
    sr_url = entry["srUrl"]
    path = fixture_path_for(FIXTURES_DIR, sr_url)

    print(f"Fetching {host} ({sr_url})...")
    try:
        content = fetch_url(sr_url)
    except urllib.error.HTTPError as exc:
        return False, f"HTTP {exc.code}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return False, repr(exc)

    if not is_valid_fixture(content, host):
        return False, "rate-limited or invalid response"

    path.write_text(content, encoding="utf-8")
    print(f"  Saved valid fixture: {path.name}")
    return True, ""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Incrementally fetch episode fixtures (max 5 per run)."
    )
    parser.add_argument(
        "--refresh-list",
        action="store_true",
        help="Refresh the list page fixture before fetching episodes.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_PER_RUN,
        help=f"Max episode pages to fetch this run (default: {MAX_PER_RUN}).",
    )
    args = parser.parse_args()

    ensure_list_fixture(args.refresh_list)
    list_entries = load_list_entries()
    audit = audit_fixtures(list_entries, FIXTURES_DIR)

    print_fixture_summary(audit)

    pending = audit["missing"] + audit["failed"]
    if not pending:
        print("\nNothing to fetch.")
        return

    batch = pending[: args.limit]
    print(f"\nFetching up to {len(batch)} episode page(s) this run...")

    fetched = 0
    fetch_failed = []

    for index, record in enumerate(batch):
        if index > 0:
            delay = random.uniform(MIN_DELAY, MAX_DELAY)
            print(f"Waiting {delay:.1f}s...")
            time.sleep(delay)

        entry = next(e for e in list_entries if e["srUrl"] == record["srUrl"])
        ok, reason = fetch_episode(entry)
        if ok:
            fetched += 1
        else:
            print(f"  Failed: {reason}", file=sys.stderr)
            fetch_failed.append({"host": entry["host"], "reason": reason})

    audit = audit_fixtures(list_entries, FIXTURES_DIR)
    print_fixture_summary(audit, fetched=fetched, fetch_failed=fetch_failed)


if __name__ == "__main__":
    main()
