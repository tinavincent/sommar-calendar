# Tasks

Source of truth for sprint planning, product backlog, and learning progress.

Last updated: 2026-06-15

---

## Sprint Backlog

*Current sprint: not started*

Sprint 2 is complete. Proposed Sprint 3 below — approve before starting.

### Proposed Sprint 3: Hosted calendar (Phase 3)

| Task | Status |
|------|--------|
| Choose hosting approach (e.g. GitHub Pages, static file host) | Todo |
| Publish `output/sommar-2026.ics` at a public URL | Todo |
| Document how to import or subscribe (download + webcal) | Todo |
| Test subscription/update flow in one calendar app | Todo |

**Why:** Makes the calendar shareable with friends and family — the last major piece of the v1 vision.

**Learning opportunities:** Static hosting, public URLs, webcal subscriptions, sharing a living calendar.

---

## Product Backlog

### Current Sprint

*Nothing active.*

### Planned

| Item | Description |
|------|-------------|
| Phase 3 — Hosted calendar | Public URL for download or webcal subscription |
| Regenerate on schedule updates | Re-run `fetch.py` + `generate.py` when SR publishes changes |

### Candidate

| Item | Notes |
|------|-------|
| One-command refresh | Script that runs fetch + generate in sequence |
| README usage guide | Document full workflow for personal use and sharing |

### Ideas

| Item | Notes |
|------|-------|
| Favorites | Mark preferred Sommarvärdar |
| Listening history | Track what you've heard |
| Personal notes | Annotations per episode |
| AI summaries and tags | Future companion app |
| Friend groups and shared recommendations | Social discovery |
| Support for other radio/podcast formats | Beyond Sommar i P1 |

### Done

| Item | Notes |
|------|-------|
| Phase 1 — Manual JSON → ICS | `generate.py` reads JSON and writes `.ics` |
| Phase 2 — Automated fetch | `fetch.py` scrapes SR and writes `data/sommar-2026.json` (58 episodes) |
| FR-1 Fetch schedule | Schedule retrieved from Sveriges Radio |
| FR-2 Store data | `data/sommar-2026.json` |
| FR-3 Generate calendar | `output/sommar-2026.ics` generated successfully |
| FR-4 Time zone support | All-day events with 07:00 alarm, `Europe/Stockholm` |
| FR-5 Shareability | `.ics` imports successfully in Google Calendar and Apple Calendar |
| Episode URL in event description | Host and SR link in DESCRIPTION |
| Events show as free | `TRANSP:TRANSPARENT` on all events |

---

## Learning Backlog

### Not Started

| Topic | Notes |
|-------|-------|
| Static hosting | Serve `.ics` from a public URL |
| webcal subscriptions | `webcal://` links for calendar apps |

### Introduced

*Nothing yet.*

### Practiced

| Topic | Notes |
|-------|-------|
| iCalendar (`.ics`) format | VCALENDAR, VEVENT, VALARM, TRANSP |
| Time zones in code | VTIMEZONE block, `TZID=Europe/Stockholm` |
| JSON data modeling | Schedule stored as array of `{ date, host, url }` |
| CLI / script basics | `python3 generate.py`, `python3 fetch.py` |
| Web scraping | Fetch and parse SR schedule page with regex |
| Manual QA | Import `.ics` and verify in calendar app |

### Comfortable

*Nothing yet.*

---

## Sprint history

| Sprint | Delivered | Date |
|--------|-----------|------|
| 1 — JSON → ICS | Sample JSON, `generate.py`, `output/sommar-2026.ics` | 2026-06-15 |
| 2 — Verify import | Import tested in calendar app; `TRANSP:TRANSPARENT` added | 2026-06-15 |

---

## Learning log

### Tools used

- Python 3 (stdlib: `json`, `pathlib`, `datetime`, `urllib`, `re`)
- Terminal (`python3 generate.py`, `python3 fetch.py`)
- Google Calendar / Apple Calendar (import testing)

### Concepts learned

- iCalendar structure and event fields
- Time zone and alarm handling in `.ics` files
- JSON → file generation pipeline
- Busy vs free availability (`TRANSP:OPAQUE` vs `TRANSP:TRANSPARENT`)
- Scraping structured data from a web page

### Technologies encountered

- RFC 5545 iCalendar format
- `Europe/Stockholm` / CEST in calendar files
- Sveriges Radio article page as data source

### Skills practiced

- Reading and writing structured data (JSON)
- Building small command-line scripts
- Verifying output with manual QA in a calendar app
- Fixing calendar behavior based on real import feedback
