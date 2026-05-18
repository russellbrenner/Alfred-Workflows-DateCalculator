"""Tests for Alfred workflow metadata compatibility."""

from __future__ import annotations

import plistlib
from pathlib import Path


WORKFLOW_ROOT = Path(__file__).resolve().parents[1]


def load_info_plist() -> dict:
    return plistlib.loads((WORKFLOW_ROOT / "info.plist").read_bytes())


def test_script_filters_declare_json_output_for_alfred_5() -> None:
    """Alfred 5 Script Filters must declare JSON output explicitly."""
    plist = load_info_plist()
    script_filters = [obj for obj in plist["objects"] if obj["type"] == "alfred.workflow.input.scriptfilter"]

    assert script_filters
    assert all(obj["config"].get("type") == "json" for obj in script_filters)


def test_workflow_bundle_metadata_is_modernised() -> None:
    """Top-level workflow metadata should no longer point at the legacy release page."""
    plist = load_info_plist()

    assert plist["version"] == "3.0.0"
    assert plist["webaddress"] == "https://github.com/rbrenner/Alfred-Workflows-DateCalculator"
    assert "Alfred 5.x" in plist["description"]
