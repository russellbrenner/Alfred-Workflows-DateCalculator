"""Pytest fixtures for the date calculator test suite."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time

from src.core.settings import Settings

# ── Time fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def frozen_now():
    """Freeze time to a known reference point for deterministic tests.

    Default: 2024-06-15 14:30:00 (Saturday, mid-afternoon).
    Override with @pytest.mark.freeze_time('2024-01-01') on individual tests.
    """
    with freeze_time("2024-06-15 14:30:00") as frozen:
        yield frozen


@pytest.fixture
def now_fn(frozen_now):
    """Return a now() function that returns the frozen time."""
    return lambda: datetime(2024, 6, 15, 14, 30, 0)


# ── Settings fixtures ─────────────────────────────────────────────────


@pytest.fixture
def default_settings() -> Settings:
    """Return Settings with all default values."""
    return Settings()


@pytest.fixture
def us_settings() -> Settings:
    """Return Settings configured for US date format (MM/DD/YYYY)."""
    return Settings(
        date_format="mm/dd/yyyy",
        time_format="12-hour",
        date_time_format="at",
    )


@pytest.fixture
def iso_settings() -> Settings:
    """Return Settings configured for ISO date format (YYYY-MM-DD)."""
    return Settings(
        date_format="yyyy-mm-dd",
        time_format="24-hour",
        date_time_format="T",
    )


@pytest.fixture
def settings_with_anniversaries() -> Settings:
    """Return Settings with custom anniversaries."""
    s = Settings()
    s.anniversaries.update(
        {
            "birthday": "1990-03-15T00:00:00",
            "holiday": "2024-07-01T00:00:00",
        }
    )
    return s


# ── Temp directory fixture ────────────────────────────────────────────


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Return a temporary directory for workflow data."""
    return tmp_path
