# CLAUDE.md

This file provides guidance to Agents when working with code in this repository.

## Project Overview

NewtArr is a Python/Flask application that orchestrates media hunting across *arr applications (Sonarr, Radarr, Lidarr, Readarr, Whisparr, Eros, Swaparr). Fork of Huntarr v6.6.3, maintained by ElfHosted. It continuously searches media libraries for missing content and quality upgrades while rate-limiting indexer usage.

## Development Commands

```bash
# Run locally with Docker Compose
docker compose up --build

# Build image only
docker build -t newtarr .
```

There is no test framework, linter, or Makefile configured. The app runs on port 9705.

## Architecture

**Entry point:** `main.py` starts two concurrent systems:
1. **Web server** (Waitress WSGI) — Flask app serving UI and API
2. **Background processor** — one thread per configured *arr app, running search cycles

**Key modules in `src/primary/`:**
- `web_server.py` — Flask app factory, blueprint registration, Jinja2 template serving
- `background.py` — Multi-threaded loop that dynamically imports and runs per-app search modules
- `settings_manager.py` — JSON-based settings persistence (stored in `/config/settings/`)
- `auth.py` — Authentication with 2FA (TOTP), proxy auth bypass for SSO deployments
- `scheduler_engine.py` — Cron-like scheduler with hourly API cap management

**Per-app modules** (`src/primary/apps/<app>/`): Each *arr app has `api.py`, `missing.py`, and `upgrade.py` following the same pattern. Adding a new app means replicating this structure.

**Routes** live in two places: `src/primary/routes/` for shared routes and `src/primary/apps/<app>/<app>_routes.py` for app-specific Flask blueprints.

**Frontend:** Vanilla JS/CSS/HTML in `frontend/`. Templates use Jinja2 (`frontend/templates/`), static assets in `frontend/static/`.

**Configuration:** All settings are JSON files under `/config/` (settings, stateful data, user data, logs). No database.

## Key Environment Variables

- `SECRET_KEY` — Flask session secret (must be set in production)
- `PORT` — Server port (default: 9705)
- `DEBUG` — Enable debug logging
- `TZ` — Timezone (default: UTC)

## Dependencies

Managed via `requirements.txt`. Renovate Bot handles automated dependency updates. Core deps: Flask, requests, waitress, bcrypt, qrcode, pyotp.

## CI/CD

GitHub Actions with `release-please` for automated versioning on pushes to main. No test or lint steps in CI.
