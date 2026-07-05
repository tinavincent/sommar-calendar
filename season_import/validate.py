"""Step 3: Validate imported season data."""

from season_import.models import apply_enrichment, discover_entry_to_episode
from season_import.enrich import enrich_episode_from_fixture, load_discovered_entries
from season_import.paths import fixtures_dir


def build_episodes(year: int, source_url: str) -> list[dict]:
    fixture_dir = fixtures_dir(year)
    entries = load_discovered_entries(year)
    episodes = []

    for entry in entries:
        episode = discover_entry_to_episode(entry, source_url)
        enriched = enrich_episode_from_fixture(entry, fixture_dir)
        episodes.append(apply_enrichment(episode, enriched))

    return episodes


def _count_present(episodes: list[dict], field: str) -> int:
    return sum(1 for episode in episodes if episode.get(field))


def run_validate(year: int, source_url: str) -> dict:
    episodes = build_episodes(year, source_url)
    total = len(episodes)

    status_counts = {
        "api_failed": sum(1 for ep in episodes if ep.get("enrichStatus") == "api_failed"),
        "partial": sum(1 for ep in episodes if ep.get("enrichStatus") == "partial"),
        "complete": sum(1 for ep in episodes if ep.get("enrichStatus") == "complete"),
    }
    api_success = status_counts["partial"] + status_counts["complete"]

    field_counts = {
        "imageUrl": _count_present(episodes, "imageUrl"),
        "shortDescription": _count_present(episodes, "shortDescription"),
        "longDescription": _count_present(episodes, "longDescription"),
        "aboutHost": _count_present(episodes, "aboutHost"),
    }

    warnings = []
    if status_counts["api_failed"]:
        warnings.append(f"API failed for {status_counts['api_failed']} episode(s)")
    if status_counts["partial"]:
        warnings.append(f"Partial enrichment for {status_counts['partial']} episode(s)")
    for field, count in field_counts.items():
        if count < total:
            warnings.append(f"Missing {field} on {total - count} episode(s)")

    print("\n=== Validation ===")
    print(f"Episodes: {total}")
    print(f"API succeeded: {api_success}")
    print(f"API failed: {status_counts['api_failed']}")
    print(f"Partial: {status_counts['partial']}")
    print(f"Complete: {status_counts['complete']}")
    print(f"Images: {field_counts['imageUrl']}")
    print(f"Short descriptions: {field_counts['shortDescription']}")
    print(f"Long descriptions: {field_counts['longDescription']}")
    print(f"About host: {field_counts['aboutHost']}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print("\nNo warnings.")

    return {
        "counts": {
            "episodes": total,
            "api_success": api_success,
            **status_counts,
            **field_counts,
        },
        "warnings": warnings,
        "episodes": episodes,
    }
