"""Sveriges Radio open API parsing for episode enrichment."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sr_parser import sanitize_episode_description, sanitize_host_bio

SR_API_EPISODE_URL = "https://api.sr.se/api/v2/episodes/{episode_id}?format=json"
IMPORTANT_ENRICH_FIELDS = ("imageUrl", "shortDescription", "longDescription", "aboutHost")


def extract_episode_id(episode_url: str) -> Optional[str]:
    match = re.search(r"/avsnitt/(\d+)", episode_url)
    return match.group(1) if match else None


def api_fixture_path(fixtures_dir, episode_id: str) -> Path:
    return Path(fixtures_dir) / f"episode-{episode_id}.json"


def parse_sr_date_ms(value: str) -> Optional[datetime]:
    if not value:
        return None
    match = re.search(r"(\d+)", value)
    if not match:
        return None
    return datetime.fromtimestamp(int(match.group(1)) / 1000, tz=timezone.utc)


def parse_api_text_fields(text: str, title: str) -> dict:
    if not text:
        return {"aboutHost": None, "longDescription": None, "previousSommarYears": None}

    lines = text.replace("\r\n", "\n").strip().split("\n")
    sommarprat_re = re.compile(rf"^{re.escape(title)}\s+om sitt Sommarprat\s*$", re.I)
    om_re = re.compile(rf"^Om\s+{re.escape(title)}\s*$", re.I)
    producent_re = re.compile(r"^Producent:", re.I)

    markers = []
    for index, line in enumerate(lines):
        stripped = line.strip()
        if sommarprat_re.match(stripped):
            markers.append(("sommarprat", index))
        elif om_re.match(stripped):
            markers.append(("om", index))
        elif producent_re.match(stripped):
            markers.append(("producent", index))

    first_marker = min((marker[1] for marker in markers), default=len(lines))
    pre_lines = [line.strip() for line in lines[:first_marker] if line.strip()]
    about_host = sanitize_host_bio(" ".join(pre_lines).strip()) or None

    long_description = None
    sommarprat_index = next((marker[1] for marker in markers if marker[0] == "sommarprat"), None)
    if sommarprat_index is not None:
        end_index = min(
            (marker[1] for marker in markers if marker[1] > sommarprat_index),
            default=len(lines),
        )
        parts = [line.strip() for line in lines[sommarprat_index + 1 : end_index] if line.strip()]
        long_description = sanitize_episode_description(" ".join(parts).strip()) or None

    previous_years = []
    years_match = re.search(r"Tidigare Sommarvärd\s+([\d,\s]+)", text, re.I)
    if years_match:
        previous_years = sorted(
            {
                int(year.strip())
                for year in years_match.group(1).split(",")
                if year.strip().isdigit()
            }
        )

    return {
        "aboutHost": about_host,
        "longDescription": long_description,
        "previousSommarYears": previous_years or None,
    }


def extract_duration(episode: dict) -> Optional[int]:
    for key in ("listenpodfile", "downloadpodfile"):
        duration = episode.get(key, {}).get("duration")
        if duration:
            return int(duration)

    broadcast = episode.get("broadcast") or {}
    playlist_duration = (broadcast.get("playlist") or {}).get("duration")
    if playlist_duration:
        return int(playlist_duration)

    broadcast_time = episode.get("broadcasttime") or {}
    start = parse_sr_date_ms(broadcast_time.get("starttimeutc", ""))
    end = parse_sr_date_ms(broadcast_time.get("endtimeutc", ""))
    if start and end and end > start:
        return int((end - start).total_seconds())

    return None


def extract_broadcast_date(episode: dict) -> Optional[str]:
    broadcast_time = episode.get("broadcasttime") or {}
    start = parse_sr_date_ms(broadcast_time.get("starttimeutc", ""))
    if start:
        return start.date().isoformat()

    publish = parse_sr_date_ms(episode.get("publishdateutc", ""))
    if publish:
        return publish.date().isoformat()

    return None


def empty_enrichment(enrich_status: str = "api_failed") -> dict:
    return {
        "imageUrl": None,
        "shortDescription": None,
        "longDescription": None,
        "aboutHost": None,
        "duration": None,
        "broadcastDate": None,
        "programTitle": None,
        "previousSommarYears": None,
        "enrichStatus": enrich_status,
    }


def compute_enrich_status(enriched: dict) -> str:
    if enriched.get("enrichStatus") == "api_failed":
        return "api_failed"
    if all(enriched.get(field) for field in IMPORTANT_ENRICH_FIELDS):
        return "complete"
    return "partial"


def map_api_episode(episode: dict, host: str) -> dict:
    text_fields = parse_api_text_fields(episode.get("text", ""), episode.get("title") or host)
    image_url = episode.get("imageurltemplate") or episode.get("imageurl")
    short_description = (episode.get("description") or "").strip() or None
    program = episode.get("program") or {}

    enriched = {
        "imageUrl": image_url or None,
        "shortDescription": short_description,
        "longDescription": text_fields["longDescription"],
        "aboutHost": text_fields["aboutHost"],
        "duration": extract_duration(episode),
        "broadcastDate": extract_broadcast_date(episode),
        "programTitle": program.get("name") or None,
        "previousSommarYears": text_fields["previousSommarYears"],
        "enrichStatus": "partial",
    }
    enriched["enrichStatus"] = compute_enrich_status(enriched)
    return enriched


def parse_api_fixture(raw: str, host: str) -> dict:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return empty_enrichment("api_failed")

    episode = payload.get("episode")
    if not isinstance(episode, dict):
        return empty_enrichment("api_failed")

    return map_api_episode(episode, host)


def is_valid_api_fixture(raw: str, episode_id: str) -> bool:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return False

    episode = payload.get("episode")
    if not isinstance(episode, dict):
        return False

    return str(episode.get("id")) == str(episode_id)


def classify_api_fixture(path, episode_id: str) -> str:
    fixture_path = Path(path)
    if not fixture_path.exists():
        return "missing"
    raw = fixture_path.read_text(encoding="utf-8", errors="ignore")
    if is_valid_api_fixture(raw, episode_id):
        return "valid"
    return "failed"


def audit_api_fixtures(list_entries: list, fixtures_dir) -> dict:
    valid, missing, failed = [], [], []

    for entry in list_entries:
        episode_id = extract_episode_id(entry["srUrl"])
        if not episode_id:
            failed.append(
                {
                    "host": entry["host"],
                    "episodeUrl": entry["srUrl"],
                    "path": "",
                    "reason": "missing episode id",
                }
            )
            continue

        path = api_fixture_path(fixtures_dir, episode_id)
        status = classify_api_fixture(path, episode_id)
        record = {
            "host": entry["host"],
            "episodeUrl": entry["srUrl"],
            "episodeId": episode_id,
            "path": str(path),
        }
        if status == "valid":
            valid.append(record)
        elif status == "missing":
            missing.append(record)
        else:
            failed.append(record)

    return {"valid": valid, "missing": missing, "failed": failed}
