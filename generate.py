#!/usr/bin/env python3
"""Generate Sommar i P1 calendar from JSON."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).parent
INPUT = ROOT / "data" / "sommar-2026.json"
OUTPUT = ROOT / "output" / "sommar-2026.ics"

TIMEZONE = "Europe/Stockholm"
DURATION_MINUTES = 15

VTIMEZONE = """BEGIN:VTIMEZONE
TZID:Europe/Stockholm
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
TZOFFSETTO:+0200
TZNAME:CEST
DTSTART:19700329T020000
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
TZOFFSETTO:+0100
TZNAME:CET
DTSTART:19701025T030000
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
END:STANDARD
END:VTIMEZONE"""


def escape_ics_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def format_datetime(date: str, hour: int, minute: int) -> str:
    year, month, day = date.split("-")
    return f"{year}{month}{day}T{hour:02d}{minute:02d}00"


def format_date(date: str) -> str:
    return date.replace("-", "")


def add_minutes(dt: str, minutes: int) -> str:
    parsed = datetime.strptime(dt, "%Y%m%dT%H%M%S")
    return (parsed + timedelta(minutes=minutes)).strftime("%Y%m%dT%H%M%S")


def build_description(host: str, sr_url: str, description: str) -> str:
    lines = [
        "Sommar i P1",
        "",
        f"Host: {host}",
    ]
    if description:
        lines.extend(["", description])
    lines.extend(["", "Listen on Sveriges Radio:", sr_url])
    return "\n".join(lines)


def build_event(episode: dict) -> str:
    host = episode["host"]
    date = episode["date"]
    sr_url = episode.get("srUrl", episode.get("url", ""))
    description = episode.get("episodeTeaser") or episode.get("description", "")
    episode_id = episode.get("id", f"{date}-sommar-i-p1-{host.lower().replace(' ', '-')}")

    dtstart = format_date(date)
    dtend = format_date((datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"))
    alarm_time = format_datetime(date, 7, 0)
    uid = f"{episode_id}@sommar-calendar"
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{dtstart}",
        f"DTEND;VALUE=DATE:{dtend}",
        f"SUMMARY:{escape_ics_text(f'Sommar i P1: {host}')}",
        f"DESCRIPTION:{escape_ics_text(build_description(host, sr_url, description))}",
        "TRANSP:TRANSPARENT",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        "DESCRIPTION:Sommar i P1 episode starts at 07:00",
        f"TRIGGER;TZID={TIMEZONE}:{alarm_time}",
        "END:VALARM",
        "END:VEVENT",
    ]
    return "\r\n".join(lines)


def main() -> None:
    episodes = json.loads(INPUT.read_text(encoding="utf-8"))

    calendar = "\r\n".join(
        [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Sommar Calendar//Sommar i P1 2026//EN",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            "X-WR-CALNAME:Sommar i P1 2026",
            f"X-WR-TIMEZONE:{TIMEZONE}",
            VTIMEZONE,
            *[build_event(episode) for episode in episodes],
            "END:VCALENDAR",
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(calendar, encoding="utf-8")
    print(f"Wrote {len(episodes)} events to {OUTPUT}")


if __name__ == "__main__":
    main()
