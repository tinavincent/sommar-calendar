# Sommar Calendar

A data pipeline and calendar generator for **Sommar i P1**.

The project serves two purposes:

1. Generate calendar events for Sommar i P1.
2. Produce structured episode data consumed by applications such as Sommarkompis.

Sommarkompis and other apps read the generated JSON files. They do not fetch from Sveriges Radio at runtime.

---

## Quick Start

```bash
# Import a season (discover → enrich → validate → export)
python3 import_season.py

# Generate calendar file
python3 generate.py
```

Import writes:

- `data/seasons/2026.json` — primary season data for apps
- `data/sommar-2026.json` — legacy shim for calendar generation
- `data/seasons-index.json` — active season pointer

Calendar output:

- `output/sommar-2026.ics`

---

## Import Pipeline

Each season is imported from a Sveriges Radio presentation page, for example:

`https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan`

```text
Presentation page
      ↓  discover
Episode list + URLs
      ↓  enrich
Episode page metadata
      ↓  validate
Quality report + warnings
      ↓  export
data/seasons/{year}.json
data/seasons-index.json
data/sommar-{year}.json   (legacy shim)
```

### Steps

| Step | Command | What it does |
|------|---------|--------------|
| **Discover** | `--step discover` | Fetch/parse presentation page, find all hosts and episode URLs from links |
| **Enrich** | `--step enrich` | Fetch individual episode pages (max 5 per run, 5–10s delay) |
| **Validate** | `--step validate` | Report completeness; warnings do not block export |
| **Export** | `--step export` | Write season JSON, legacy shim, and update `activeSeason` |

Run all steps (default):

```bash
python3 import_season.py
```

Run one step:

```bash
python3 import_season.py --step discover
python3 import_season.py --step enrich
python3 import_season.py --step validate
python3 import_season.py --step export
```

Options:

```bash
python3 import_season.py --year 2026
python3 import_season.py --url <presentation-page-url>
python3 import_season.py --step enrich --limit 3
python3 import_season.py --step discover --refresh-list
```

### Rate limiting

Sveriges Radio may return 403 or rate-limit responses. Enrichment is intentionally slow:

- Max **5 episode pages per run**
- **5–10 second** delay between requests
- Valid fixtures are cached and never overwritten
- Invalid/rate-limited responses are discarded, not saved

Run enrich multiple times until all fixtures are valid:

```bash
python3 import_season.py --step enrich
python3 import_season.py --step export
```

---

## Calendar Generation

```bash
python3 generate.py
python3 generate.py --year 2026
```

Reads `data/seasons-index.json` for `activeSeason`, falls back to the latest season file, then to `data/sommar-2026.json`.

Events are created as all-day reminders with a 07:00 alarm (`Europe/Stockholm`), marked as free (`TRANSP:TRANSPARENT`).

---

## Data Layout

```text
data/
  seasons/
    2026.json
  seasons-index.json
  sommar-2026.json          # legacy shim

fixtures/
  full/                     # cached SR pages for 2026 (also fixtures/2026/)
    list-page.txt
    discover.json
    episode-{id}.txt

output/
  sommar-2026.ics
```

---

## Data Model

### Season file (`data/seasons/{year}.json`)

```json
{
  "year": 2026,
  "sourceUrl": "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan",
  "generatedAt": "2026-07-05T15:49:35Z",
  "episodeCount": 58,
  "episodes": []
}
```

### Episode (Sommarkompis format)

```json
{
  "name": "Helena Bergström",
  "date": "2026-06-20",
  "episodeUrl": "https://www.sverigesradio.se/avsnitt/2815462",
  "imageUrl": "https://image-api.sr.se/v1/static/...",
  "shortDescription": "Skådespelaren om när livet stannade upp...",
  "longDescription": "",
  "aboutHost": "",
  "hostEpithet": "skådespelare",
  "previousSommarYears": [2011],
  "source": {
    "presentationPage": "https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan",
    "episodePage": "https://www.sverigesradio.se/avsnitt/2815462"
  }
}
```

### Seasons index (`data/seasons-index.json`)

```json
{
  "activeSeason": 2026,
  "seasons": [2026]
}
```

Apps should use `activeSeason` when present. If missing or invalid, use the latest available season.

### Legacy shim (`data/sommar-2026.json`)

Parallel format for calendar generation and backward compatibility:

```json
{
  "id": "2026-06-20-sommar-i-p1-helena-bergstrom",
  "year": 2026,
  "date": "2026-06-20",
  "channel": "sommar-i-p1",
  "host": "Helena Bergström",
  "hostEpithet": "skådespelare",
  "srUrl": "https://www.sverigesradio.se/avsnitt/2815462",
  "episodeTeaser": "...",
  "episodeDescription": "",
  "hostBio": "",
  "imageUrl": "...",
  "previousSommarYears": [2011]
}
```

---

## Field Sources

| Field | Source |
|-------|--------|
| `name`, `date`, `hostEpithet`, `episodeUrl` | Presentation page |
| `imageUrl` | Episode page (first image) |
| `shortDescription` | Episode page (teaser paragraph) |
| `longDescription` | Episode page (`## {name} om sitt Sommarprat`) |
| `aboutHost` | Episode page (bio paragraph) |
| `previousSommarYears` | Episode page (related episodes) |

Truncated text ending with `...` or `…` is discarded and stored as empty.

---

## Episode IDs

Format: `YYYY-MM-DD-channel-host-slug`

Example: `2026-06-20-sommar-i-p1-kajsa-ollongren`

Episode IDs are immutable. User-generated data in downstream apps may depend on stable IDs.

Mutable fields (safe to refresh): `hostEpithet`, descriptions, `imageUrl`, `episodeUrl`, bios.

---

## Project Structure

| File / directory | Purpose |
|------------------|---------|
| `import_season.py` | Main import CLI |
| `season_import/` | Discover, enrich, validate, export modules |
| `sr_parser.py` | Shared SR page parsing |
| `generate.py` | JSON → ICS calendar |
| `fetch.py` | Legacy wrapper → export step |
| `fetch_fixtures.py` | Legacy wrapper → enrich step |
| `validate_sample.py` | Validate data model on 5 episodes |
| `product-description.md` | Product vision and requirements |
| `tasks.md` | Sprint and backlog |

---

## Relationship to Sommarkompis

```text
Sveriges Radio
      ↓
Sommar Calendar (import pipeline)
      ↓
data/seasons/{year}.json
      ↓
Sommarkompis
```

---

## Status

Active development on branch `episode-details`.

Current focus:

- Rich episode metadata (images, descriptions, bios)
- Multi-season support
- Stable data contracts for Sommarkompis
- Incremental, rate-limit-safe enrichment

---

## Out of Scope

* Audio playback
* Podcast hosting
* User accounts
* Social features
* Recommendations, ratings, notes
* AI assistants

These belong in consumer applications such as Sommarkompis.

---

## License

Personal project — not yet licensed for public distribution.
