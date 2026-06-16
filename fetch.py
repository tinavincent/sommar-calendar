#!/usr/bin/env python3
"""Fetch Sommar i P1 2026 host dates and write them to data/sommar-2026.json."""

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent
OUTPUT = ROOT / "data" / "sommar-2026.json"
SOURCE_URL = "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan"
FALLBACK_URL = "https://r.jina.ai/http://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan"
MONTHS = {
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "augusti": 8,
    "aug": 8,
}


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def normalize_markdown(text: str) -> str:
    # Collapse soft line wraps but keep paragraph breaks.
    return re.sub(r"(?<!\n)\n(?!\n)", " ", text)


def parse_schedule(text: str) -> list[dict]:
    normalized = normalize_markdown(text)
    pattern = re.compile(
        r"(?i)(\d{1,2})\s+(juni|jun|juli|jul|augusti|aug):\s+\[([^\]]+)\]\(([^)]+)\)"
    )
    entries = []

    for day, month_name, host, url in pattern.findall(normalized):
        month = MONTHS[month_name.lower()]
        date = f"2026-{month:02d}-{int(day):02d}"

        match = re.search(r"/avsnitt/(\d+)", url)
        if match:
            url = f"https://www.sverigesradio.se/avsnitt/{match.group(1)}"

        entries.append({"date": date, "host": host.strip(), "url": url.strip()})

    if not entries:
        raise ValueError("Could not parse any schedule entries from source content.")

    entries.sort(key=lambda item: item["date"])
    return entries


def main() -> None:
    try:
        source = fetch_url(SOURCE_URL)
    except Exception as first_exc:
        print(f"Direct fetch failed: {first_exc!r}. Falling back to proxy.", file=sys.stderr)
        source = fetch_url(FALLBACK_URL)

    episodes = parse_schedule(source)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(episodes, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(episodes)} episodes to {OUTPUT}")


if __name__ == "__main__":
    main()
