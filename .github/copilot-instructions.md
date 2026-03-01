# Copilot Instructions for NewtArr

## Project Overview

NewtArr is a Python/Flask application that orchestrates media hunting across *arr applications (Sonarr, Radarr, Lidarr, Readarr, Whisparr, Eros, Swaparr). It is a fork of NewtArr v6.6.3, maintained by ElfHosted. The app continuously searches media libraries for missing content and quality upgrades while rate-limiting indexer usage.

## Build & Run

```bash
# Run locally (primary method)
docker compose up --build

# Build image only
docker build -t newtarr .
```

There is no test framework, linter, or Makefile. The app runs on port 9705. No CI test or lint steps exist.

## Architecture

`main.py` bootstraps two concurrent systems:
1. **Web server** — Waitress WSGI serving the Flask app (`src/primary/web_server.py`)
2. **Background processor** — `src/primary/background.py` spawns one thread per *arr app via `app_specific_loop()`, which **dynamically imports** each app's modules at runtime using `importlib.import_module(f'src.primary.apps.{app_type}')`.

**Module structure for each *arr app** (`src/primary/apps/<app>/`):
- `__init__.py` — exports `get_configured_instances()` and the two main functions
- `api.py` — all HTTP communication with the *arr API via `arr_request()`
- `missing.py` — `process_missing_<items>()` function
- `upgrade.py` — `process_cutoff_upgrades()` function
- `<app>_routes.py` (in `src/primary/apps/`) — Flask blueprint for app-specific API routes

Adding a new *arr app requires replicating all of the above files and registering the blueprint in `src/primary/apps/blueprints.py` and `src/primary/web_server.py`.

**Routes live in two places:**
- `src/primary/routes/` — shared routes (common, history, scheduler)
- `src/primary/apps/<app>_routes.py` — per-app Flask blueprints, centrally imported via `src/primary/apps/blueprints.py`

**Settings** are JSON files stored at `/config/<app_name>.json` at runtime. Default schemas live in `src/primary/default_configs/<app_name>.json`. Settings are loaded/saved via `src/primary/settings_manager.py`, which has a 5-second in-memory cache (`CACHE_TTL = 5`).

**Stateful tracking** (preventing reprocessing of already-searched items) lives in `/config/stateful/<app_type>/` as JSON files, managed by `src/primary/stateful_manager.py`. Items expire after `stateful_management_hours` (default: 168 hours/7 days).

**Frontend** is vanilla JS/CSS/HTML. Templates use Jinja2 (`frontend/templates/`), static assets in `frontend/static/`.

## Key Conventions

**Import paths**: Always use `src.primary.*` for absolute imports (e.g., `from src.primary.utils.logger import get_logger`). Do not use relative imports outside of `auth.py`.

**Logging**: Use `get_logger("<app_name>")` from `src.primary.utils.logger` — this returns an app-specific logger writing to `/config/logs/<app>.log`. Each app module defines its logger at module level: `app_logger = get_logger("sonarr")`.

**Multi-instance support**: Each app's settings have an `instances` list. `get_configured_instances()` in `__init__.py` filters for enabled instances with non-empty `api_url` and `api_key`. The background loop iterates over all instances.

**Stop signal propagation**: All long-running functions accept a `stop_check: Callable[[], bool]` parameter. Check it in inner loops to respect graceful shutdown. The global `stop_event` in `background.py` is the source of truth.

**Advanced settings**: Use `get_advanced_setting("key", default)` from `settings_manager` for cross-app tunables (e.g., `api_timeout`, `command_wait_delay`). These live in `general.json`.

**Known app types**: `KNOWN_APP_TYPES = ["sonarr", "radarr", "lidarr", "readarr", "whisparr", "eros", "general", "swaparr"]` — this list in `settings_manager.py` must be updated when adding a new app.

**Authentication**: `src/primary/auth.py` handles session cookies (`newtarr_session`), bcrypt passwords, TOTP 2FA, and proxy auth bypass (for SSO via `authenticate_request()`). User credentials are stored in `/config/user/credentials.json`.

## Key Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | — | Flask session secret (required in production) |
| `PORT` | `9705` | Server port |
| `DEBUG` | `false` | Enables Flask dev server + DEBUG log level |
| `TZ` | `UTC` | Timezone |

## Configuration Files at Runtime

All runtime data lives under `/config/`:
- `/config/<app>.json` — per-app settings
- `/config/stateful/<app>/` — processed item tracking
- `/config/logs/<app>.log` — per-app logs
- `/config/user/credentials.json` — auth credentials

## CI/CD

GitHub Actions uses `release-please` for automated versioning on pushes to `main`. Renovate Bot handles dependency updates in `requirements.txt`.
