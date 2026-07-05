"""Shared Sveriges Radio parsing utilities."""

import re
import unicodedata
from typing import Optional

YEAR = 2026
CHANNEL = "sommar-i-p1"

MONTHS = {
    "juni": 6,
    "jun": 6,
    "juli": 7,
    "jul": 7,
    "augusti": 8,
    "aug": 8,
}

SWEDISH_TRANSLATION = str.maketrans(
    {"å": "a", "ä": "a", "ö": "o", "Å": "a", "Ä": "a", "Ö": "o"}
)

LIST_PATTERN = re.compile(
    r"(?i)(\d{1,2})\s+(juni|jun|juli|jul|augusti|aug):\s*"
    r"\[([^\]]+)\]\(([^)]+)\)"
    r"(?:,\s*([^[\n]+?))?"
    r"(?=\s*\d{1,2}\s+(?:juni|jun|juli|jul|augusti|aug):|$|##)"
)

SKIP_LINE_PATTERNS = (
    re.compile(r"^!\["),
    re.compile(r"^#"),
    re.compile(r"^Dela$"),
    re.compile(r"^Avsnittet finns inte"),
    re.compile(r"^Kommande$"),
    re.compile(r"Sommar & Vinter i P1"),
    re.compile(r"Foto:"),
    re.compile(r"^Ansvarig utgivare:"),
    re.compile(r"^Vi bygger om!"),
    re.compile(r"^\["),
    re.compile(r"^Mer$"),
    re.compile(r"^Sök$"),
    re.compile(r"^Nyheter$"),
    re.compile(r"^Poddar"),
    re.compile(r"^Kanaler$"),
    re.compile(r"^Gå direkt till"),
    re.compile(r"^http"),
    re.compile(r"^\(\)"),
)


def slugify(text: str) -> str:
    text = text.translate(SWEDISH_TRANSLATION)
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return re.sub(r"-+", "-", slug).strip("-")


def build_id(date: str, host: str) -> str:
    return f"{date}-{CHANNEL}-{slugify(host)}"


def normalize_sr_url(url: str) -> str:
    match = re.search(r"/avsnitt/(\d+)", url)
    if match:
        return f"https://www.sverigesradio.se/avsnitt/{match.group(1)}"
    return url.strip()


def extract_body(text: str) -> str:
    if "Markdown Content:" in text:
        return text.split("Markdown Content:", 1)[1]
    return text


def normalize_list_text(text: str) -> str:
    return re.sub(r"\s+", " ", extract_body(text))


def is_truncated(text: str) -> bool:
    stripped = text.rstrip()
    return stripped.endswith("...") or stripped.endswith("…")


def sanitize_text_field(text: str) -> str:
    if is_truncated(text):
        return ""
    return text


def sanitize_host_bio(bio: str) -> str:
    return sanitize_text_field(bio)


def sanitize_episode_description(description: str) -> str:
    return sanitize_text_field(description)


def should_skip_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    return any(pattern.search(stripped) for pattern in SKIP_LINE_PATTERNS)


def parse_list_page(text: str, year: int = YEAR) -> list[dict]:
    normalized = normalize_list_text(text)
    entries = []

    for day, month_name, host, url, epithet in LIST_PATTERN.findall(normalized):
        month = MONTHS[month_name.lower()]
        date = f"{year}-{month:02d}-{int(day):02d}"
        host = host.strip()
        entries.append(
            {
                "id": build_id(date, host),
                "year": year,
                "date": date,
                "channel": CHANNEL,
                "host": host,
                "hostEpithet": epithet.strip() if epithet else "",
                "srUrl": normalize_sr_url(url),
            }
        )

    if not entries:
        raise ValueError("Could not parse any entries from list page.")

    entries.sort(key=lambda item: item["date"])
    return entries


def find_host_heading_index(lines: list, host: str) -> Optional[int]:
    target = f"# {host}"
    matches = [index for index, line in enumerate(lines) if line.strip() == target]
    return matches[-1] if matches else None


def collect_paragraphs(lines: list, start: int) -> tuple[list, int]:
    paragraphs = []
    current = []
    index = start

    while index < len(lines):
        line = lines[index].strip()

        if line.startswith("## ") or line.startswith("Läs mer"):
            break
        if line.startswith("Ansvarig utgivare:"):
            break

        if should_skip_line(line):
            if current:
                paragraphs.append(" ".join(current))
                current = []
            index += 1
            continue

        current.append(line)
        index += 1

    if current:
        paragraphs.append(" ".join(current))

    return paragraphs, index


def parse_episode_description_section(lines: list, host: str) -> str:
    heading = re.compile(rf"^##\s+{re.escape(host)}\s+om sitt Sommarprat\s*$", re.I)
    start = next((index for index, line in enumerate(lines) if heading.match(line.strip())), None)
    if start is None:
        return ""

    parts = []
    for line in lines[start + 1 :]:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Läs mer") or stripped.startswith("## ") or stripped.startswith("Ansvarig"):
            break
        parts.append(stripped)

    return " ".join(parts).strip()


def parse_previous_sommar_years(text: str, host: str) -> list:
    body = extract_body(text)
    related_match = re.search(r"## Relaterade avsnitt", body)
    if not related_match:
        return []

    related_section = body[related_match.start() : related_match.start() + 4000]
    pattern = re.compile(rf"###\s*\[{re.escape(host)}\s+(\d{{4}})\]", re.I)
    return sorted({int(match.group(1)) for match in pattern.finditer(related_section)})


def parse_image_url(text: str) -> str:
    body = extract_body(text)
    match = re.search(r"!\[[^\]]*\]\((https?://[^)]+)\)", body)
    return match.group(1) if match else ""


def parse_episode_page(text: str, host: str) -> dict:
    body = extract_body(text)
    lines = body.splitlines()
    heading_index = find_host_heading_index(lines, host)
    if heading_index is None:
        return {
            "episodeTeaser": "",
            "episodeDescription": "",
            "hostBio": "",
            "imageUrl": parse_image_url(text),
            "previousSommarYears": parse_previous_sommar_years(text, host),
        }

    paragraphs, _ = collect_paragraphs(lines, heading_index + 1)
    episode_teaser = paragraphs[0] if paragraphs else ""
    host_bio = sanitize_host_bio(paragraphs[1] if len(paragraphs) > 1 else "")
    episode_description = sanitize_episode_description(
        parse_episode_description_section(lines, host)
    )

    return {
        "episodeTeaser": episode_teaser,
        "episodeDescription": episode_description,
        "hostBio": host_bio,
        "imageUrl": parse_image_url(text),
        "previousSommarYears": parse_previous_sommar_years(text, host),
    }


def parse_enriched_episode(text: str, host: str) -> dict:
    if not text:
        return {
            "imageUrl": "",
            "shortDescription": "",
            "longDescription": "",
            "aboutHost": "",
            "previousSommarYears": [],
        }

    parsed = parse_episode_page(text, host)
    return {
        "imageUrl": parsed.get("imageUrl", ""),
        "shortDescription": parsed.get("episodeTeaser", ""),
        "longDescription": parsed.get("episodeDescription", ""),
        "aboutHost": parsed.get("hostBio", ""),
        "previousSommarYears": parsed.get("previousSommarYears", []),
    }


def build_episode(list_entry: dict, episode_page: Optional[str]) -> dict:
    episode = {
        **list_entry,
        "episodeTeaser": "",
        "episodeDescription": "",
        "hostBio": "",
        "imageUrl": "",
        "previousSommarYears": [],
    }

    if episode_page:
        episode.update(parse_episode_page(episode_page, list_entry["host"]))

    return episode


def is_rate_limit_or_error(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return True
    if len(stripped) < 500:
        return True
    if stripped.startswith("{") and (
        "RateLimit" in stripped or '"code":429' in stripped or '"status":429' in stripped
    ):
        return True
    if "Access Denied" in stripped:
        return True
    if "upstream connect error" in stripped.lower():
        return True
    return False


def is_valid_fixture(content: str, host: str) -> bool:
    if is_rate_limit_or_error(content):
        return False
    body = extract_body(content)
    return f"# {host}" in body


def classify_fixture(path, host: str) -> str:
    """Return 'valid', 'missing', or 'failed'."""
    from pathlib import Path

    fixture_path = Path(path)
    if not fixture_path.exists():
        return "missing"
    content = fixture_path.read_text(encoding="utf-8", errors="ignore")
    if is_valid_fixture(content, host):
        return "valid"
    return "failed"


def fixture_path_for(fixtures_dir, sr_url: str):
    from pathlib import Path

    episode_id = sr_url.rstrip("/").split("/")[-1]
    return Path(fixtures_dir) / f"episode-{episode_id}.txt"


def audit_fixtures(list_entries: list, fixtures_dir) -> dict:
    valid, missing, failed = [], [], []

    for entry in list_entries:
        path = fixture_path_for(fixtures_dir, entry["srUrl"])
        status = classify_fixture(path, entry["host"])
        record = {"host": entry["host"], "srUrl": entry["srUrl"], "path": str(path)}
        if status == "valid":
            valid.append(record)
        elif status == "missing":
            missing.append(record)
        else:
            failed.append(record)

    return {"valid": valid, "missing": missing, "failed": failed}


def print_fixture_summary(audit: dict, fetched: int = 0, fetch_failed: list = None) -> None:
    fetch_failed = fetch_failed or []
    remaining = len(audit["missing"]) + len(audit["failed"])

    print("\n=== Fixture summary ===")
    print(f"Valid fixtures: {len(audit['valid'])}")
    print(f"Missing fixtures: {len(audit['missing'])}")
    print(f"Failed/rate-limited fixtures: {len(audit['failed'])}")
    if fetched:
        print(f"Fetched this run: {fetched}")
    if fetch_failed:
        print(f"Fetch failures this run: {len(fetch_failed)}")
        for item in fetch_failed:
            print(f"  - {item['host']}: {item['reason']}")

    if remaining:
        print("\nNext recommended command:")
        print("  python3 import_season.py --step enrich")
    else:
        print("\nAll fixtures valid. Rebuild JSON with:")
        print("  python3 import_season.py --step export")


def print_summary(episodes: list, output_path, failed_urls: list) -> None:
    epithets_found = sum(1 for episode in episodes if episode["hostEpithet"])
    descriptions_found = sum(1 for episode in episodes if episode["episodeDescription"])
    teasers_found = sum(1 for episode in episodes if episode["episodeTeaser"])
    bios_found = sum(1 for episode in episodes if episode["hostBio"])

    print(f"\nWrote {len(episodes)} episodes to {output_path}")
    print(f"Total episodes: {len(episodes)}")
    print(f"Epithets found: {epithets_found}")
    print(f"Teasers found: {teasers_found}")
    print(f"Descriptions found: {descriptions_found}")
    print(f"Bios found: {bios_found}")
    print(f"Descriptions missing: {len(episodes) - descriptions_found}")
    print(f"Bios missing: {len(episodes) - bios_found}")

    if failed_urls:
        print("Failed URLs:")
        for url in failed_urls:
            print(f"  - {url}")
    else:
        print("Failed URLs: none")
