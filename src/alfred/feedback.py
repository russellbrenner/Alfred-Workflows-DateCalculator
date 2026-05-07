"""Alfred 5.x JSON Script Filter feedback builder.

Produces valid JSON output per the Alfred Script Filter JSON spec:
https://www.alfredapp.com/help/workflows/inputs/script-filter/json/
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ItemMods:
    """Modifier key configurations for an item."""
    cmd: dict[str, Any] | None = None
    ctrl: dict[str, Any] | None = None
    shift: dict[str, Any] | None = None
    alt: dict[str, Any] | None = None
    fn: dict[str, Any] | None = None


@dataclass
class Item:
    """A single result item in Alfred's result list.

    Attributes:
        title: Main text shown in the result row.
        subtitle: Secondary text shown below title.
        arg: Value passed to downstream actions when item is actioned.
        valid: Whether the item can be actioned (Enter).
        uid: Unique ID for Alfred to learn/sort items across runs.
        icon: Icon filename or path (relative to workflow root, or special tokens).
        icontype: 'fileicon', 'filetype', or omitted for bundled icons.
        autocomplete: Text expanded when item is TABbed.
        mods: Modifier key configurations (cmd/ctrl/shift/alt/fn).
        variables: Workflow variables set when item is actioned.
        match: Custom text for Alfred's filtering (when alfredfiltersresults=True).
    """
    title: str
    subtitle: str = ""
    arg: str | None = None
    valid: bool = True
    uid: str | None = None
    icon: str | None = None
    icontype: str | None = None
    autocomplete: str | None = None
    mods: dict[str, dict[str, Any]] | None = None
    variables: dict[str, str] | None = None
    match: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to Alfred JSON item dict."""
        d: dict[str, Any] = {"title": self.title}

        if self.subtitle:
            d["subtitle"] = self.subtitle

        if self.arg is not None:
            d["arg"] = self.arg

        d["valid"] = self.valid

        if self.uid is not None:
            d["uid"] = self.uid

        if self.icon is not None:
            icon_dict: dict[str, Any] = {"path": self.icon}
            if self.icontype:
                icon_dict["type"] = self.icontype
            d["icon"] = icon_dict

        if self.autocomplete is not None:
            d["autocomplete"] = self.autocomplete

        if self.mods:
            d["mods"] = self.mods

        if self.variables:
            d["variables"] = self.variables

        if self.match is not None:
            d["match"] = self.match

        return d


@dataclass
class Feedback:
    """A collection of items for Alfred Script Filter output.

    Attributes:
        items: List of result items.
        rerun: Seconds before Alfred re-runs the script (0 = disabled).
        skipknowledge: If True, Alfred won't reorder items based on user history.
        variables: Workflow-wide variables.
    """
    items: list[Item] = field(default_factory=list)
    rerun: float = 0
    skipknowledge: bool = False
    variables: dict[str, str] | None = None

    def add_item(self, **kwargs: Any) -> Item:
        """Add an item and return it for chaining."""
        item = Item(**kwargs)
        self.items.append(item)
        return item

    def to_json(self) -> str:
        """Serialize to Alfred-compatible JSON string."""
        output: dict[str, Any] = {"items": [item.to_dict() for item in self.items]}

        if self.rerun > 0:
            output["rerun"] = self.rerun

        if self.skipknowledge:
            output["skipknowledge"] = True

        if self.variables:
            output["variables"] = self.variables

        return json.dumps(output, ensure_ascii=False)


# ── Icon constants (Alfred built-in icon tokens) ─────────────────────

ICON_INFO = "icon.png"
ICON_WARNING = "icon.png"
ICON_ERROR = "icon.png"
