"""Tests for the Alfred JSON feedback builder."""
from __future__ import annotations

import json

import pytest

from src.alfred.feedback import Feedback, Item


class TestItem:
    """Test Item dataclass serialization."""

    def test_minimal_item(self):
        item = Item(title="Test")
        d = item.to_dict()
        assert d == {"title": "Test", "valid": True}

    def test_full_item(self):
        item = Item(
            title="Result",
            subtitle="Details",
            arg="payload",
            valid=True,
            uid="item-1",
            icon="icon.png",
            icontype="fileicon",
            autocomplete="auto",
            mods={"cmd": {"valid": True, "arg": "cmd-payload"}},
            variables={"key": "value"},
            match="result details",
        )
        d = item.to_dict()
        assert d["title"] == "Result"
        assert d["subtitle"] == "Details"
        assert d["arg"] == "payload"
        assert d["valid"] is True
        assert d["uid"] == "item-1"
        assert d["icon"] == {"path": "icon.png", "type": "fileicon"}
        assert d["autocomplete"] == "auto"
        assert d["mods"] == {"cmd": {"valid": True, "arg": "cmd-payload"}}
        assert d["variables"] == {"key": "value"}
        assert d["match"] == "result details"

    def test_item_with_no_icon(self):
        item = Item(title="Test", valid=False)
        d = item.to_dict()
        assert "icon" not in d
        assert d["valid"] is False

    def test_item_with_none_subtitle(self):
        item = Item(title="Test", subtitle="")
        d = item.to_dict()
        # Empty subtitle should be omitted
        assert "subtitle" not in d


class TestFeedback:
    """Test Feedback JSON output."""

    def test_empty_feedback(self):
        fb = Feedback()
        d = json.loads(fb.to_json())
        assert d == {"items": []}

    def test_feedback_with_items(self):
        fb = Feedback()
        fb.add_item(title="One", arg="a")
        fb.add_item(title="Two", arg="b")
        d = json.loads(fb.to_json())
        assert len(d["items"]) == 2
        assert d["items"][0]["title"] == "One"
        assert d["items"][1]["title"] == "Two"

    def test_feedback_with_rerun(self):
        fb = Feedback(rerun=0.5)
        d = json.loads(fb.to_json())
        assert d["rerun"] == 0.5

    def test_feedback_without_rerun(self):
        fb = Feedback()
        d = json.loads(fb.to_json())
        assert "rerun" not in d

    def test_feedback_with_skipknowledge(self):
        fb = Feedback(skipknowledge=True)
        d = json.loads(fb.to_json())
        assert d["skipknowledge"] is True

    def test_feedback_with_variables(self):
        fb = Feedback(variables={"setting": "value"})
        d = json.loads(fb.to_json())
        assert d["variables"] == {"setting": "value"}

    def test_valid_json_output(self):
        """Ensure output is always valid JSON."""
        fb = Feedback()
        fb.add_item(title="Test", subtitle="Sub", arg="arg1", valid=True)
        # Should not raise
        parsed = json.loads(fb.to_json())
        assert "items" in parsed

    def test_alfred_spec_compliance(self):
        """Verify output matches Alfred 5.x Script Filter JSON spec."""
        fb = Feedback()
        fb.add_item(
            title="Result",
            subtitle="Description",
            arg="value",
            valid=True,
            uid="unique-id",
            icon="icon.png",
        )
        d = json.loads(fb.to_json())

        # Must have items array
        assert isinstance(d["items"], list)
        assert len(d["items"]) == 1

        item = d["items"][0]
        # Required fields per spec
        assert "title" in item
        assert "valid" in item
        assert isinstance(item["valid"], bool)

        # Optional fields present when set
        assert item["subtitle"] == "Description"
        assert item["arg"] == "value"
        assert item["uid"] == "unique-id"
        assert item["icon"]["path"] == "icon.png"

    def test_add_item_returns_item(self):
        fb = Feedback()
        item = fb.add_item(title="Test")
        assert item.title == "Test"
        assert len(fb.items) == 1

    def test_unicode_content(self):
        """Ensure non-ASCII characters are preserved."""
        fb = Feedback()
        fb.add_item(title="Test \u2764", subtitle="\u00fc\u00f6\u00e4")
        d = json.loads(fb.to_json())
        assert d["items"][0]["title"] == "Test \u2764"
        assert d["items"][0]["subtitle"] == "\u00fc\u00f6\u00e4"
