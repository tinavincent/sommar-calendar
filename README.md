# Sommar Calendar 2026

A simple service that generates a calendar with all **Sommar i P1** episodes for 2026 — so you can see each day's Sommarvärd and get a reminder when the episode is released.

## Purpose

Sommar i P1 publishes a schedule of hosts and dates, but listeners who rely on their calendar currently need to check Sveriges Radio manually, add reminders themselves, and keep track of dates across the entire summer. This project automates that.

## What you get

- All Sommarvärdar for 2026 in your calendar
- Reminders at **07:00 Europe/Stockholm** on each episode day
- A shareable calendar you can import into Google Calendar, Apple Calendar, Outlook, or subscribe to via webcal

Each event is titled `Sommar i P1: {Host Name}` and includes the host, date, and Sveriges Radio episode URL when available.

## Status

Status: MVP Complete

Current capabilities:
- Fetches all Sommarvärdar from Sveriges Radio
- Generates JSON
- Generates ICS
- Imports into Google Calendar

Future improvements:
- Hosted calendar
- Subscription support
- Automatic publishing

## Project docs

| File | Purpose |
|------|---------|
| [product-description.md](./product-description.md) | Full product spec, requirements, and success criteria |
| [tasks.md](./tasks.md) | Sprint backlog, product backlog, and learning backlog |
| [VIBECODING_COACHING_MODE.md](./VIBECODING_COACHING_MODE.md) | Development workflow and coaching guidelines |

## Success criteria (v1)

- All Sommar 2026 episodes appear in the generated calendar
- Events occur on the correct date at 07:00 Europe/Stockholm
- The `.ics` file imports successfully into Google Calendar and Apple Calendar

## Out of scope (v1)

User accounts, social features, ratings, notes, recommendations, AI summaries, podcast playback, Spotify integration, and mobile apps.

## Data format

Schedule data is stored as JSON:

```json
{
  "date": "2026-06-20",
  "host": "Example Name",
  "url": "https://..."
}
```

## License

Personal project — not yet licensed for public distribution.
