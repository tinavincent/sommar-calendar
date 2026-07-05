#!/usr/bin/env python3
"""Import a Sommar season: discover → enrich → validate → export."""

import argparse
import sys

from season_import.discover import run_discover
from season_import.enrich import run_enrich
from season_import.export import run_export
from season_import.paths import DEFAULT_SOURCE_URL_2026, MAX_ENRICH_PER_RUN
from season_import.portraits import run_refresh_portraits
from season_import.validate import run_validate


def default_source_url(year: int) -> str:
    if year == 2026:
        return DEFAULT_SOURCE_URL_2026
    raise ValueError(f"No default source URL for year {year}. Pass --url explicitly.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Import a Sommar season from Sveriges Radio.")
    parser.add_argument("--year", type=int, default=2026, help="Season year (default: 2026)")
    parser.add_argument("--url", help="Presentation page URL")
    parser.add_argument(
        "--step",
        choices=["discover", "enrich", "refresh-portraits", "validate", "export", "all"],
        default="all",
        help="Pipeline step to run (default: all)",
    )
    parser.add_argument(
        "--refresh-list",
        action="store_true",
        help="Re-fetch presentation page during discover",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=MAX_ENRICH_PER_RUN,
        help=f"Max episode pages to enrich per run (default: {MAX_ENRICH_PER_RUN})",
    )
    args = parser.parse_args()

    source_url = args.url or default_source_url(args.year)
    step = args.step

    print(f"=== Sommar import {args.year} ===")
    print(f"Source: {source_url}")
    print(f"Step: {step}\n")

    if step in ("discover", "all"):
        print("--- Discover ---")
        run_discover(args.year, source_url, refresh=args.refresh_list or step == "all")

    if step in ("enrich", "all"):
        print("\n--- Enrich ---")
        result = run_enrich(args.year, limit=args.limit)
        if result["failed"]:
            print("\nEnrich failures this run:")
            for item in result["failed"]:
                print(f"  - {item['host']}: {item['episodeUrl']}")

    if step == "refresh-portraits":
        print("\n--- Refresh portraits ---")
        result = run_refresh_portraits(args.year, limit=args.limit)
        if result["failed"]:
            print("\nPortrait refresh failures this run:")
            for item in result["failed"]:
                print(f"  - {item['host']}: {item['episodeUrl']}")

    if step in ("validate", "all"):
        print("\n--- Validate ---")
        run_validate(args.year, source_url)

    if step in ("export", "all"):
        print("\n--- Export ---")
        run_export(args.year, source_url)

    print("\n=== Done ===")
    if step == "all":
        print("Next: python3 generate.py")


if __name__ == "__main__":
    main()
