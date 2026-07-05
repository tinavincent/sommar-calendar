"""Step 4: Export season files and legacy shim."""

import json

from season_import.models import build_season_file, season_episode_to_legacy
from season_import.paths import SEASONS_DIR, SEASONS_INDEX, legacy_shim_for_year, season_file
from season_import.validate import build_episodes


def update_seasons_index(year: int) -> None:
    index = {"activeSeason": year, "seasons": []}
    if SEASONS_INDEX.exists():
        try:
            index = json.loads(SEASONS_INDEX.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    seasons = set(index.get("seasons", []))
    seasons.add(year)
    index["activeSeason"] = year
    index["seasons"] = sorted(seasons)
    SEASONS_INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_export(year: int, source_url: str) -> dict:
    episodes = build_episodes(year, source_url)
    season = build_season_file(year, source_url, episodes)

    SEASONS_DIR.mkdir(parents=True, exist_ok=True)
    season_path = season_file(year)
    season_path.write_text(json.dumps(season, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    legacy_episodes = [season_episode_to_legacy(ep, year) for ep in episodes]
    legacy_path = legacy_shim_for_year(year)
    legacy_path.write_text(json.dumps(legacy_episodes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    update_seasons_index(year)

    print(f"\nExported season to {season_path}")
    print(f"Legacy shim written to {legacy_path}")
    print(f"Updated {SEASONS_INDEX} (activeSeason={year})")

    return {"season_path": season_path, "legacy_path": legacy_path, "season": season}
