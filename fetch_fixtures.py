#!/usr/bin/env python3
"""Legacy wrapper — runs enrich step of season import."""

import sys

from season_import.enrich import run_enrich
from season_import.paths import MAX_ENRICH_PER_RUN


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Incrementally fetch episode fixtures.")
    parser.add_argument("--refresh-list", action="store_true")
    parser.add_argument("--limit", type=int, default=MAX_ENRICH_PER_RUN)
    args = parser.parse_args()

    print("fetch_fixtures.py is deprecated. Use: python3 import_season.py --step enrich", file=sys.stderr)

    if args.refresh_list:
        from season_import.discover import run_discover
        from season_import.paths import DEFAULT_SOURCE_URL_2026

        run_discover(2026, DEFAULT_SOURCE_URL_2026, refresh=True)

    result = run_enrich(2026, limit=args.limit)
    if result["failed"]:
        print("\nFailures:")
        for item in result["failed"]:
            print(f"  - {item['host']}")


if __name__ == "__main__":
    main()
