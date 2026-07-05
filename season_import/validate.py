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


def run_validate(year: int, source_url: str) -> dict:
    episodes = build_episodes(year, source_url)
    total = len(episodes)

    counts = {
        "episodes": total,
        "imageUrl": sum(1 for ep in episodes if ep.get("imageUrl")),
        "shortDescription": sum(1 for ep in episodes if ep.get("shortDescription")),
        "longDescription": sum(1 for ep in episodes if ep.get("longDescription")),
        "aboutHost": sum(1 for ep in episodes if ep.get("aboutHost")),
    }

    warnings = []
    if counts["imageUrl"] < total:
        warnings.append(f"Missing imageUrl on {total - counts['imageUrl']} episode(s)")
    if counts["shortDescription"] < total:
        warnings.append(
            f"Missing shortDescription on {total - counts['shortDescription']} episode(s)"
        )
    if counts["longDescription"] < total:
        warnings.append(
            f"Missing longDescription on {total - counts['longDescription']} episode(s)"
        )
    if counts["aboutHost"] < total:
        warnings.append(f"Missing aboutHost on {total - counts['aboutHost']} episode(s)")

    print("\n=== Validation ===")
    print(f"Episodes: {counts['episodes']}")
    print(f"Images: {counts['imageUrl']}")
    print(f"Short descriptions: {counts['shortDescription']}")
    print(f"Long descriptions: {counts['longDescription']}")
    print(f"About host: {counts['aboutHost']}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  ⚠ {warning}")
    else:
        print("\nNo warnings.")

    return {"counts": counts, "warnings": warnings, "episodes": episodes}
