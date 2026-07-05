#!/usr/bin/env python3
"""Build data/sommar-2026.json from list + episode fixtures."""

import json
import sys
from pathlib import Path

from sr_parser import (
    audit_fixtures,
    build_episode,
    classify_fixture,
    fixture_path_for,
    parse_list_page,
    print_fixture_summary,
    print_summary,
)

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "sommar-2026.json"
FIXTURES_DIR = ROOT / "fixtures" / "full"
LIST_FIXTURE = FIXTURES_DIR / "list-page.txt"


def main() -> None:
    if not LIST_FIXTURE.exists():
        print(f"Missing list fixture: {LIST_FIXTURE}", file=sys.stderr)
        print("Run: python3 fetch_fixtures.py --refresh-list", file=sys.stderr)
        sys.exit(1)

    list_entries = parse_list_page(LIST_FIXTURE.read_text(encoding="utf-8"))
    audit = audit_fixtures(list_entries, FIXTURES_DIR)

    episodes = []
    failed_urls = []

    for entry in list_entries:
        path = fixture_path_for(FIXTURES_DIR, entry["srUrl"])
        status = classify_fixture(path, entry["host"])

        if status == "valid":
            episode_page = path.read_text(encoding="utf-8")
        else:
            episode_page = None
            failed_urls.append(entry["srUrl"])

        episodes.append(build_episode(entry, episode_page))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print_summary(episodes, OUTPUT, failed_urls)
    print_fixture_summary(audit)


if __name__ == "__main__":
    main()
