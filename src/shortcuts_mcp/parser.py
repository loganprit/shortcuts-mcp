from __future__ import annotations

import plistlib
from typing import cast

from .models import ShortcutAction


def _string_key_dict(value: dict[object, object]) -> dict[str, object]:
    return {str(key): item for key, item in value.items()}


def parse_actions(data: bytes) -> list[ShortcutAction]:
    """Parse a Shortcuts actions plist blob into structured actions.

    The ZDATA column stores actions as a list directly (not wrapped in a dict).
    """
    try:
        plist: object = plistlib.loads(data)
    except (ValueError, plistlib.InvalidFileException):
        return []

    # Handle both formats: direct list or wrapped in dict
    raw_actions: list[dict[str, object]] = []
    if isinstance(plist, list):
        for item in cast(list[object], plist):
            if isinstance(item, dict):
                raw_actions.append(_string_key_dict(cast(dict[object, object], item)))
    elif isinstance(plist, dict):
        plist_dict = _string_key_dict(cast(dict[object, object], plist))
        possible_actions = plist_dict.get("WFWorkflowActions", [])
        if isinstance(possible_actions, list):
            for item in cast(list[object], possible_actions):
                if isinstance(item, dict):
                    raw_actions.append(
                        _string_key_dict(cast(dict[object, object], item))
                    )
    else:
        return []

    actions: list[ShortcutAction] = []
    for item in raw_actions:
        identifier = item.get("WFWorkflowActionIdentifier")
        if not isinstance(identifier, str) or not identifier:
            continue
        raw_parameters = item.get("WFWorkflowActionParameters", {})
        parameters: dict[str, object] = {}
        if isinstance(raw_parameters, dict):
            parameters = {
                str(key): value
                for key, value in cast(dict[object, object], raw_parameters).items()
            }
        actions.append(ShortcutAction(identifier=identifier, parameters=parameters))
    return actions


def parse_input_types(data: bytes) -> list[str] | None:
    """Extract input type classes from a Shortcuts actions plist blob.

    Note: Input types may not be present in the ZDATA blob format.
    """
    try:
        plist: object = plistlib.loads(data)
    except (ValueError, plistlib.InvalidFileException):
        return None

    if isinstance(plist, dict):
        plist_dict = _string_key_dict(cast(dict[object, object], plist))
        input_types = plist_dict.get("WFWorkflowInputContentItemClasses")
        if isinstance(input_types, list):
            return [str(item) for item in cast(list[object], input_types)]

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
