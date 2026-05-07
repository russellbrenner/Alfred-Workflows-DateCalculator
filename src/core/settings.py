"""Settings management — load, save, and migrate workflow settings.

Replaces versioning.py and the deanishe Workflow.settings API.
Uses JSON stored in $ALFRED_WORKFLOW_DATA for persistence.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from src.core.mappings import (
    DEFAULT_ANNIVERSARIES,
    DEFAULT_DATE_FORMAT,
    DEFAULT_DATE_TIME_FORMAT,
    DEFAULT_TIME_FORMAT,
    DEFAULT_WORKFLOW_SETTINGS,
)


@dataclass
class Settings:
    """Workflow settings with migration-aware defaults."""
    date_format: str = DEFAULT_DATE_FORMAT
    time_format: str = DEFAULT_TIME_FORMAT
    date_time_format: str = DEFAULT_DATE_TIME_FORMAT
    anniversaries: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_ANNIVERSARIES))


def get_workflow_data_dir() -> Path:
    """Return the Alfred workflow data directory.

    Uses $ALFRED_WORKFLOW_DATA if set, otherwise falls back to a local dir.
    """
    env_dir = os.environ.get("ALFRED_WORKFLOW_DATA")
    if env_dir:
        return Path(env_dir)
    # Fallback for development/testing
    return Path.home() / ".local" / "share" / "alfred-date-calc"


def _ensure_data_dir(path: Path) -> None:
    """Create the data directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def load_settings(data_dir: Path | None = None) -> Settings:
    """Load settings from JSON file, applying defaults for missing keys.

    If no file exists, returns default settings.
    If an old deanishe plist-format settings file exists, migrates it.
    """
    data_dir = data_dir or get_workflow_data_dir()
    settings_file = data_dir / "settings.json"

    if not settings_file.exists():
        # Check for old deanishe format and migrate
        migrated = _try_migrate_old_settings(data_dir)
        if migrated:
            return migrated
        return Settings()

    with open(settings_file, "r") as f:
        raw = json.load(f)

    return _apply_defaults(raw)


def save_settings(settings: Settings, data_dir: Path | None = None) -> None:
    """Persist settings to JSON file."""
    data_dir = data_dir or get_workflow_data_dir()
    _ensure_data_dir(data_dir)
    settings_file = data_dir / "settings.json"

    with open(settings_file, "w") as f:
        json.dump(
            {
                "date-format": settings.date_format,
                "time-format": settings.time_format,
                "date-time-format": settings.date_time_format,
                "anniversaries": settings.anniversaries,
            },
            f,
            indent=2,
        )


def _apply_defaults(raw: dict) -> Settings:
    """Merge loaded settings with defaults (migration for new keys)."""
    return Settings(
        date_format=raw.get("date-format", DEFAULT_DATE_FORMAT),
        time_format=raw.get("time-format", DEFAULT_TIME_FORMAT),
        date_time_format=raw.get("date-time-format", DEFAULT_DATE_TIME_FORMAT),
        anniversaries=raw.get("anniversaries", dict(DEFAULT_ANNIVERSARIES)),
    )


def _try_migrate_old_settings(data_dir: Path) -> Settings | None:
    """Attempt to migrate old deanishe plist-format settings.

    The old workflow stored settings as a plist via the deanishe library.
    This checks for the old settings.json (deanishe's JSON format) and
    converts it to the new format if the keys differ.
    """
    # deanishe stored settings as JSON in the workflow data dir
    old_file = data_dir / "settings.json"
    if not old_file.exists():
        return None

    try:
        with open(old_file, "r") as f:
            raw = json.load(f)

        # If it already has the new keys, no migration needed
        if "date-format" in raw:
            return None

        # Convert old-style keys to new-style
        migrated = {
            "date-format": raw.get("date-format", raw.get("date_format", DEFAULT_DATE_FORMAT)),
            "time-format": raw.get("time-format", raw.get("time_format", DEFAULT_TIME_FORMAT)),
            "date-time-format": raw.get(
                "date-time-format", raw.get("date_time_format", DEFAULT_DATE_TIME_FORMAT)
            ),
            "anniversaries": raw.get("anniversaries", dict(DEFAULT_ANNIVERSARIES)),
        }

        # Save migrated format
        save_settings(_apply_defaults(migrated), data_dir)
        return _apply_defaults(migrated)
    except (json.JSONDecodeError, KeyError):
        return None


# ── Module-level convenience (for entry points) ───────────────────────

def load() -> Settings:
    """Load settings using the default data directory."""
    return load_settings()


def save(settings: Settings) -> None:
    """Save settings using the default data directory."""
    save_settings(settings)
