"""Season data models and format conversion."""

from datetime import datetime, timezone

from sr_parser import build_id, normalize_sr_url

CHANNEL = "sommar-i-p1"


def empty_season_episode(name: str, date: str, episode_url: str, presentation_url: str) -> dict:
    return {
        "name": name,
        "date": date,
        "episodeUrl": episode_url,
        "imageUrl": None,
        "hostPortraitUrl": None,
        "shortDescription": None,
        "longDescription": None,
        "aboutHost": None,
        "duration": None,
        "broadcastDate": None,
        "programTitle": None,
        "enrichStatus": None,
        "source": {
            "presentationPage": presentation_url,
            "episodePage": episode_url,
        },
    }


def discover_entry_to_episode(entry: dict, presentation_url: str) -> dict:
    episode = empty_season_episode(
        name=entry["host"],
        date=entry["date"],
        episode_url=entry["srUrl"],
        presentation_url=presentation_url,
    )
    if entry.get("hostEpithet"):
        episode["hostEpithet"] = entry["hostEpithet"]
    return episode


def apply_enrichment(episode: dict, enriched: dict) -> dict:
    merged = episode.copy()
    for field in (
        "imageUrl",
        "hostPortraitUrl",
        "shortDescription",
        "longDescription",
        "aboutHost",
        "duration",
        "broadcastDate",
        "programTitle",
        "enrichStatus",
    ):
        if field in enriched:
            merged[field] = enriched[field]
    if enriched.get("previousSommarYears"):
        merged["previousSommarYears"] = enriched["previousSommarYears"]
    return merged


def build_season_file(year: int, source_url: str, episodes: list[dict]) -> dict:
    return {
        "year": year,
        "sourceUrl": source_url,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "episodeCount": len(episodes),
        "episodes": episodes,
    }


def _legacy_value(value) -> str:
    return value if value is not None else ""


def season_episode_to_legacy(episode: dict, year: int) -> dict:
    name = episode["name"]
    date = episode["date"]
    episode_url = episode.get("episodeUrl", "")
    return {
        "id": build_id(date, name),
        "year": year,
        "date": date,
        "channel": CHANNEL,
        "host": name,
        "hostEpithet": episode.get("hostEpithet", ""),
        "srUrl": normalize_sr_url(episode_url) if episode_url else "",
        "episodeTeaser": _legacy_value(episode.get("shortDescription")),
        "episodeDescription": _legacy_value(episode.get("longDescription")),
        "hostBio": _legacy_value(episode.get("aboutHost")),
        "previousSommarYears": episode.get("previousSommarYears") or [],
        "imageUrl": _legacy_value(episode.get("imageUrl")),
        "hostPortraitUrl": _legacy_value(episode.get("hostPortraitUrl")),
    }


def legacy_episode_to_calendar(episode: dict) -> dict:
    if "host" in episode:
        return episode
    return season_episode_to_legacy(episode, episode.get("year", 2026))
