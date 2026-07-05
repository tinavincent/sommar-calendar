#!/usr/bin/env python3
"""Validate episode data model on a small sample (5 episodes)."""

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

from sr_parser import build_episode, parse_list_page, print_summary

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "sommar-2026-sample.json"
FIXTURES_DIR = ROOT / "fixtures" / "sample"
SOURCE_URL = "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan"
SAMPLE_SIZE = 5
EPISODE_TIMEOUT = 10


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


def fetch_episode_page(sr_url: str) -> Optional[str]:
    try:
        return fetch_url(sr_url, timeout=EPISODE_TIMEOUT)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"  Episode fetch failed: {exc!r}", file=sys.stderr)
        return None


def load_fixture(name: str) -> str:
    path = FIXTURES_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing fixture: {path}")
    return path.read_text(encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate episode data model on 5 episodes.")
    parser.add_argument("--offline", action="store_true", help="Use fixtures/sample/.")
    args = parser.parse_args()

    failed_urls = []

    print(f"[1/{SAMPLE_SIZE + 1}] Fetching list page...")
    if args.offline:
        list_text = load_fixture("list-page.txt")
    else:
        try:
            list_text = fetch_url(SOURCE_URL)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"List fetch failed: {exc!r}", file=sys.stderr)
            sys.exit(1)

    list_entries = parse_list_page(list_text)[:SAMPLE_SIZE]
    episodes = []

    for index, entry in enumerate(list_entries, start=2):
        host = entry["host"]
        print(f"[{index}/{SAMPLE_SIZE + 1}] Processing {host}...")

        if args.offline:
            episode_id = entry["srUrl"].rstrip("/").split("/")[-1]
            try:
                episode_page = load_fixture(f"episode-{episode_id}.txt")
            except FileNotFoundError:
                episode_page = None
                failed_urls.append(entry["srUrl"])
        else:
            episode_page = fetch_episode_page(entry["srUrl"])
            if episode_page is None:
                failed_urls.append(entry["srUrl"])

        episodes.append(build_episode(entry, episode_page))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print_summary(episodes, OUTPUT, failed_urls)


if __name__ == "__main__":
    main()
