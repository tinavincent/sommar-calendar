# Sommar Calendar

A data pipeline and calendar generator for **Sommar i P1**.

The project serves two purposes:

1. Generate calendar events for Sommar i P1.
2. Produce structured episode data consumed by applications such as Sommarkompis.

Sommarkompis and other apps read the generated JSON files. They do not fetch from Sveriges Radio at runtime.

---

## Quick Start

Full import and calendar generation:

```bash
# 1. Import season (discover → enrich → refresh-portraits → validate → export)
python3 import_season.py

# 2. Generate calendar file
python3 generate.py

# 3. Copy data to Sommarkompis (adjust path if needed)
cp data/sommar-2026.json ../sommar-kompis/src/data/sommar-2026.json
```

Then in Sommarkompis:

```bash
cd ../sommar-kompis
npm run dev
```

Import writes:

- `data/seasons/2026.json` — primary season data for apps
- `data/sommar-2026.json` — legacy shim for Sommarkompis and calendar generation
- `data/seasons-index.json` — active season pointer

Calendar output:

- `output/sommar-2026.ics`

---

## Run Everything (End-to-End)

Use this when setting up from scratch or refreshing a full season.

### 1. Import from Sveriges Radio

```bash
# Discover all episodes from the presentation page
python3 import_season.py --step discover

# Fetch API metadata (max 5 per run, 5–10s delay between requests)
python3 import_season.py --step enrich --limit 58

# Fetch host portraits for episodes missing images (max 5 per run)
python3 import_season.py --step refresh-portraits --limit 58

# Check completeness
python3 import_season.py --step validate

# Write JSON output files
python3 import_season.py --step export
```

Or run discover + enrich + validate + export in one go (portraits must be refreshed separately):

```bash
python3 import_season.py
python3 import_season.py --step refresh-portraits --limit 58
python3 import_season.py --step export
```

Repeat `enrich` and `refresh-portraits` until validate reports no missing data.

### 2. Generate calendar

```bash
python3 generate.py
```

### 3. Sync to Sommarkompis

Sommarkompis reads a local JSON file — there is no automatic sync.

```bash
cp data/sommar-2026.json ../sommar-kompis/src/data/sommar-2026.json
cd ../sommar-kompis
npm run dev
```

Restart the dev server if it is already running.

### 4. Verify

```bash
# In sommar-calendar
python3 import_season.py --step validate

# Expect: 58 episodes, 58 host portraits, 0 API failures
```

In Sommarkompis (dev mode), the browser console warns about any episodes still missing portraits.

---

## Import Pipeline

Each season is imported from a Sveriges Radio presentation page, for example:

`https://www.sverigesradio.se/artikel/sommarpratare-2026-hela-listan`

```text
Presentation page
      ↓  discover
Episode list + URLs
      ↓  enrich (SR API)
Episode metadata (JSON fixtures)
      ↓  refresh-portraits (episode pages, cached)
Host portrait URLs
      ↓  validate
Quality report + warnings
      ↓  export
data/seasons/{year}.json
data/seasons-index.json
data/sommar-{year}.json   (legacy shim)
      ↓  manual copy
Sommarkompis
```

### Steps

| Step | Command | What it does |
|------|---------|--------------|
| **Discover** | `--step discover` | Fetch/parse presentation page, find all hosts and episode URLs from links |
| **Enrich** | `--step enrich` | Fetch episode metadata from SR API (`episode-{id}.json`), max 5 per run |
| **Refresh portraits** | `--step refresh-portraits` | Fetch host portrait URLs from episode pages, max 5 per run |
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
python3 import_season.py --step refresh-portraits
python3 import_season.py --step validate
python3 import_season.py --step export
```

Options:

```bash
python3 import_season.py --year 2026
python3 import_season.py --url <presentation-page-url>
python3 import_season.py --step enrich --limit 58
python3 import_season.py --step refresh-portraits --limit 58
python3 import_season.py --step discover --refresh-list
```

### Rate limiting

Sveriges Radio may return 403 or rate-limit responses on HTML pages. The pipeline is intentionally slow:

- Max **5 requests per run** (enrich and refresh-portraits)
- **5–10 second** delay between requests
- Valid API fixtures (`episode-{id}.json`) are cached and never overwritten
- Portraits are cached in `fixtures/full/portraits.json`
- Cached HTML fixtures (`.txt`) are used as fallback for text fields only

Run enrich and refresh-portraits multiple times until validate reports complete data:

```bash
python3 import_season.py --step enrich --limit 58
python3 import_season.py --step refresh-portraits --limit 58
python3 import_season.py --step validate
python3 import_season.py --step export
cp data/sommar-2026.json ../sommar-kompis/src/data/sommar-2026.json
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
  full/                     # cached SR data for 2026 (also fixtures/2026/)
    list-page.txt
    discover.json
    episode-{id}.json       # SR API responses
    episode-{id}.txt        # cached HTML (fallback for text/portraits)
    portraits.json          # cached host portrait URLs

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
  "hostPortraitUrl": "https://image-api.sr.se/v1/static/AA/2071/...",
  "imageUrl": null,
  "shortDescription": "Skådespelaren om när livet stannade upp...",
  "longDescription": null,
  "aboutHost": "Hon är en av Sveriges mest folkkära skådespelare...",
  "duration": 3947,
  "broadcastDate": "2026-06-20",
  "programTitle": "Sommar & Vinter i P1",
  "enrichStatus": "partial",
  "hostEpithet": "skådespelare",
  "previousSommarYears": [1992, 2011],
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
  "hostBio": "...",
  "hostPortraitUrl": "https://image-api.sr.se/v1/static/AA/2071/...",
  "imageUrl": "",
  "previousSommarYears": [1992, 2011]
}
```

---

## Field Sources

| Field | Source |
|-------|--------|
| `name`, `date`, `hostEpithet`, `episodeUrl` | Presentation page (discover) |
| `shortDescription` / `episodeTeaser` | SR API `description` |
| `longDescription` / `episodeDescription` | SR API `text` ("om sitt Sommarprat" section) |
| `aboutHost` / `hostBio` | SR API `text` (bio paragraph) |
| `hostPortraitUrl` | Episode page HTML or `portraits.json` cache |
| `imageUrl` | SR API `imageurltemplate` (null if generic program image) |
| `duration`, `broadcastDate`, `programTitle` | SR API |
| `previousSommarYears` | SR API `text` or related episodes |

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
| `season_import/` | Discover, enrich, validate, export, portraits modules |
| `sr_api.py` | SR open API parsing |
| `sr_parser.py` | Shared SR page parsing and portrait extraction |
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
data/sommar-2026.json
      ↓  cp (manual)
sommar-kompis/src/data/sommar-2026.json
      ↓
Sommarkompis (npm run dev)
```

Sommarkompis field mapping:

| Sommarkompis | sommar-calendar (legacy shim) |
|--------------|-------------------------------|
| `hostPortraitUrl` | `hostPortraitUrl` |
| `episodeTeaser` | `episodeTeaser` / `shortDescription` |
| `episodeDescription` | `episodeDescription` / `longDescription` |
| `hostBio` | `hostBio` / `aboutHost` |

After each export, copy the legacy shim:

```bash
cp data/sommar-2026.json ../sommar-kompis/src/data/sommar-2026.json
```

---

## Status

Active development on branch `episode-details`.

Current focus:

- API-based enrichment with portrait refresh
- Rich episode metadata (portraits, descriptions, bios)
- Multi-season support
- Stable data contracts for Sommarkompis

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
