#!/usr/bin/env python3
"""Legacy wrapper — runs export step of season import."""

import sys

from season_import.export import run_export
from season_import.paths import DEFAULT_SOURCE_URL_2026
from season_import.validate import run_validate


def main() -> None:
    year = 2026
    source_url = DEFAULT_SOURCE_URL_2026
    print("fetch.py is deprecated. Use: python3 import_season.py", file=sys.stderr)
    run_validate(year, source_url)
    run_export(year, source_url)


if __name__ == "__main__":
    main()
