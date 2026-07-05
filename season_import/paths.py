"""Paths and defaults for season import."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SEASONS_DIR = DATA_DIR / "seasons"
SEASONS_INDEX = DATA_DIR / "seasons-index.json"
LEGACY_SHIM = DATA_DIR / "sommar-2026.json"
DEFAULT_SOURCE_URL_2026 = (
    "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan"
)
MAX_ENRICH_PER_RUN = 5
MIN_FETCH_DELAY = 5
MAX_FETCH_DELAY = 10
EPISODE_TIMEOUT = 15


def fixtures_dir(year: int) -> Path:
    year_dir = ROOT / "fixtures" / str(year)
    if year_dir.exists():
        return year_dir
    legacy = ROOT / "fixtures" / "full"
    if year == 2026 and legacy.exists():
        return legacy
    return year_dir


def list_fixture(year: int) -> Path:
    return fixtures_dir(year) / "list-page.txt"


def discover_cache(year: int) -> Path:
    return fixtures_dir(year) / "discover.json"


def season_file(year: int) -> Path:
    return SEASONS_DIR / f"{year}.json"


def legacy_shim_for_year(year: int) -> Path:
    if year == 2026:
        return LEGACY_SHIM
    return DATA_DIR / f"sommar-{year}.json"
