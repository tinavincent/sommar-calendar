# Product Description

# Sommar Calendar 2026

## Purpose

Create a simple service that automatically generates a calendar containing all Sommar i P1 episodes for 2026.

The primary goal is personal use: making it easy to discover each day's Sommarvärd and receive a calendar reminder when the episode becomes available.

The calendar should be shareable and reusable by others.

---

# Problem Statement

Sommar i P1 publishes a schedule of hosts and dates, but listeners who rely on their calendar currently need to:

* Remember to check Sveriges Radio manually
* Add reminders themselves
* Keep track of dates across the entire summer

This project automates that process.

---

# Target Users

### Primary

Tina

A regular Sommar i P1 listener who wants each episode to appear automatically in her calendar.

### Secondary

Friends and family who may want to subscribe to the same calendar.

---

# Goals

Users can:

* See all Sommarvärdar for 2026 in their calendar
* Receive reminders when episodes are released
* Subscribe to a shared calendar
* Import the calendar into Google Calendar, Apple Calendar, Outlook, or similar tools

---

# Non-Goals

The following are explicitly out of scope for Version 1:

* User accounts
* Social features
* Ratings
* Notes
* Recommendations
* AI-generated summaries
* Podcast playback
* Spotify integration
* Mobile applications

These may become part of a future companion application.

---

# Data Source

Primary source:

* Sveriges Radio Sommar i P1 website

Future options:

* Sveriges Radio API (if available)
* RSS feeds
* Additional metadata sources

---

# Event Definition

Each calendar event represents a Sommar i P1 episode.

## Title

```text
Sommar i P1: {Host Name}
```

Example:

```text
Sommar i P1: Anders Hansen
```

## Time

Release time:

```text
07:00 Europe/Stockholm
```

## Duration

Default:

```text
15 minutes
```

The event exists primarily as a reminder rather than a representation of playback duration.

## Description

Include:

* Host name
* Date
* Sveriges Radio episode URL (when available)

Example:

```text
Sommar i P1

Host: Anders Hansen

Listen on Sveriges Radio:
https://...
```

---

# Functional Requirements

## FR-1 Fetch Schedule

The system shall retrieve the list of Sommarvärdar and dates for 2026.

## FR-2 Store Data

The system shall store schedule information in a structured format.

Recommended format:

```json
{
  "date": "2026-06-20",
  "host": "Example Name",
  "url": "https://..."
}
```

## FR-3 Generate Calendar

The system shall generate a valid iCalendar (.ics) file.

## FR-4 Time Zone Support

All events shall use:

```text
Europe/Stockholm
```

## FR-5 Shareability

The generated calendar shall be suitable for:

* Import into calendar applications
* Publication as a shared calendar

---

# Technical Approach

## Phase 1

Manual JSON input

```text
JSON
↓
ICS
```

Purpose:

Validate calendar generation before introducing scraping.

## Phase 2

Automated schedule retrieval

```text
Sveriges Radio
↓
JSON
↓
ICS
```

## Phase 3

Hosted calendar

```text
Sveriges Radio
↓
JSON
↓
ICS
↓
Public URL
```

Possible formats:

* Direct .ics download
* webcal subscription

---

# Success Criteria

Version 1 is successful when:

* All Sommar 2026 episodes appear in the generated calendar
* Events occur on the correct date
* Events occur at 07:00 Europe/Stockholm
* The .ics file imports successfully into Google Calendar
* The .ics file imports successfully into Apple Calendar

---

# Future Vision

This project may later become part of a broader companion application for Sommar i P1 and other audio storytelling formats.

Potential future capabilities:

* Listening history
* Personal notes
* AI-generated tags and summaries
* Recommendations
* Friend groups
* Shared recommendations
* Discovery based on trusted people
* Support for additional podcast and radio formats

These capabilities are intentionally excluded from the first version.
