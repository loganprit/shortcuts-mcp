from __future__ import annotations

import plistlib
from typing import Any

from .models import ShortcutAction


def parse_actions(data: bytes) -> list[ShortcutAction]:
    """Parse a Shortcuts actions plist blob into structured actions.

    The ZDATA column stores actions as a list directly (not wrapped in a dict).
    """
    try:
        plist = plistlib.loads(data)
    except (ValueError, plistlib.InvalidFileException):
        return []

    # Handle both formats: direct list or wrapped in dict
    if isinstance(plist, list):
        action_list = plist
    elif isinstance(plist, dict):
        action_list = plist.get("WFWorkflowActions", [])
    else:
        return []

    actions: list[ShortcutAction] = []
    for action in action_list:
        if not isinstance(action, dict):
            continue
        identifier = action.get("WFWorkflowActionIdentifier")
        if not identifier:
            continue
        parameters = action.get("WFWorkflowActionParameters", {})
        actions.append(ShortcutAction(identifier=identifier, parameters=parameters))
    return actions


def parse_input_types(data: bytes) -> list[str] | None:
    """Extract input type classes from a Shortcuts actions plist blob.

    Note: Input types may not be present in the ZDATA blob format.
    """
    try:
        plist = plistlib.loads(data)
    except (ValueError, plistlib.InvalidFileException):
        return None

    if isinstance(plist, dict):
        input_types = plist.get("WFWorkflowInputContentItemClasses")
        if isinstance(input_types, list):
            return [str(item) for item in input_types]

    return None


def action_types(actions: list[ShortcutAction]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for action in actions:
        if action.identifier in seen:
            continue
        seen.add(action.identifier)
        ordered.append(action.identifier)
    return ordered


def action_search_blob(actions: list[ShortcutAction]) -> str:
    """Create a search-friendly string for action identifiers + parameters."""
    parts: list[str] = []
    for action in actions:
        parts.append(action.identifier)
        if action.parameters:
            parts.append(str(action.parameters))
    return " ".join(parts)
