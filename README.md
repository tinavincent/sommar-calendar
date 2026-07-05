# Sommar Calendar

A data pipeline and calendar generator for **Sommar i P1**.

The project serves two purposes:

1. Generate calendar events for Sommar i P1.
2. Produce structured episode data that can be consumed by applications such as Sommarkompis.

---

## Purpose

Sveriges Radio publishes hosts, dates and episode information for Sommar i P1.

This project collects and structures that information so it can be:

* Imported into calendars
* Used by companion applications
* Extended with metadata such as themes and descriptions
* Reused across multiple projects

---

## Current Capabilities

### Calendar Generation

* Fetches Sommarvärdar from Sveriges Radio
* Generates JSON
* Generates ICS calendar files
* Imports into Google Calendar
* Creates events at 07:00 Europe/Stockholm

### Episode Data Generation

* Produces structured episode data
* Stores host information
* Stores episode dates
* Stores Sveriges Radio URLs
* Supports episode descriptions
* Provides stable identifiers for downstream applications

---

## Relationship to Sommarkompis

This project is the source of truth for Sommar episode data.

```text
Sveriges Radio
      ↓
Sommar Calendar
      ↓
Structured JSON
      ↓
Sommarkompis
```

Sommarkompis consumes generated episode data but does not fetch directly from Sveriges Radio.

---
## Episode Data Model

Episodes are generated from two sources.

### Main List Page

Provides:

- date
- host
- hostEpithet
- srUrl

### Individual Episode Page

Provides:

- episodeTeaser
- episodeDescription
- hostBio
- previousSommarYears

The generated JSON combines data from both sources.

## Data Model

Example:

```json
{
  "id": "2026-06-20-sommar-i-p1-kajsa-ollongren",
  "year": 2026,
  "date": "2026-06-20",
  "host": "Kajsa Ollongren",
  "description": "Episode description",
  "srUrl": "https://sverigesradio.se/..."
}
```

---

## Episode IDs

Episode IDs are immutable.

User-generated data in downstream applications may depend on stable IDs.

Format:

```text
YYYY-MM-DD-channel-host-slug
```

Example:

```text
2026-06-20-sommar-i-p1-kajsa-ollongren
```

Once published, an episode ID must never change.

---
The following fields may be refreshed over time without affecting consumers:

- hostEpithet
- episodeTeaser
- episodeDescription
- hostBio
- previousSommarYears
- srUrl

Downstream applications should treat these fields as mutable while treating the episode ID as permanent.

## Status

Status: Active Development

Current focus:

* Rich episode metadata
* Episode descriptions
* Stable data contracts
* Integration with Sommarkompis

---

## Future Roadmap

### Near Term

* Complete 2026 episode descriptions
* Improve data quality
* Support richer themes and metadata

### Medium Term

* Import previous Sommar years
* Support Vinter i P1
* Automated data refresh workflows

### Long Term

* Hosted calendar feeds
* Public subscription support
* Multiple downstream consumers

---

## Project Documentation

| File                        | Purpose                                    |
| --------------------------- | ------------------------------------------ |
| product-description.md      | Product vision and requirements            |
| tasks.md                    | Sprint and backlog management              |
| VIBECODING_COACHING_MODE.md | Development workflow and learning approach |

---

## Success Criteria

### Calendar

* All episodes appear on correct dates
* ICS imports correctly into major calendar applications

### Data

* Episode metadata is complete and accurate
* IDs remain stable over time
* Downstream applications can update data without losing user content

---

## Out of Scope

* Audio playback
* Podcast hosting
* User accounts
* Social features
* Recommendations
* Ratings
* Notes
* AI assistants

These belong in consumer applications such as Sommarkompis.

---

## License

Personal project — not yet licensed for public distribution.