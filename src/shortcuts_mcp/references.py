"""Reference transformation for simplified shortcut action syntax.

This module transforms user-friendly reference syntax into the proper
Shortcuts plist format that macOS Shortcuts understands.

Supported simplified syntax:
- {"$ref": "previous"}      → Reference output of previous action
- {"$ref": "uuid:ABC123"}   → Reference output of action with specific UUID
- {"$var": "MyVariable"}    → Reference a named variable
- {"$input": True}          → Reference the shortcut's input
- {"$ask": True}            → Ask user for input at runtime
- {"$clipboard": True}      → Use clipboard contents
"""

from __future__ import annotations

import uuid as uuid_module
from typing import cast

from .models import ShortcutAction


def transform_references(
    actions: list[ShortcutAction],
) -> list[ShortcutAction]:
    """Transform simplified reference syntax into proper Shortcuts format.

    This function:
    1. Assigns UUIDs to actions that don't have one
    2. Tracks action UUIDs for reference resolution
    3. Transforms $ref, $var, $input markers into proper format

    Args:
        actions: List of ShortcutAction objects with simplified syntax

    Returns:
        New list of ShortcutAction objects with transformed parameters
    """
    # First pass: assign UUIDs to all actions and track them
    action_uuids: list[str] = []
    processed_actions: list[ShortcutAction] = []

    for action in actions:
        params = dict(action.parameters)

        # Ensure action has a UUID
        action_uuid = _ensure_uuid(params)
        action_uuids.append(action_uuid)

        processed_actions.append(
            ShortcutAction(identifier=action.identifier, parameters=params)
        )

    # Second pass: transform references using the UUID list
    result: list[ShortcutAction] = []

    for idx, action in enumerate(processed_actions):
        transformed_params = _transform_parameters(
            action.parameters,
            action_uuids=action_uuids,
            current_index=idx,
        )
        result.append(
            ShortcutAction(
                identifier=action.identifier,
                parameters=transformed_params,
            )
        )

    return result


def _ensure_uuid(params: dict[str, object]) -> str:
    """Ensure parameters dict has a UUID, generating one if needed."""
    existing_uuid = params.get("UUID")
    if isinstance(existing_uuid, str) and existing_uuid:
        return existing_uuid

    new_uuid = str(uuid_module.uuid4()).upper()
    params["UUID"] = new_uuid
    return new_uuid


def _transform_parameters(
    params: dict[str, object],
    action_uuids: list[str],
    current_index: int,
) -> dict[str, object]:
    """Recursively transform all reference markers in parameters."""
    result: dict[str, object] = {}

    for key, value in params.items():
        result[key] = _transform_value(
            value,
            action_uuids=action_uuids,
            current_index=current_index,
        )

    return result


def _transform_value(
    value: object,
    action_uuids: list[str],
    current_index: int,
) -> object:
    """Transform a single value, handling nested dicts and lists."""
    if isinstance(value, dict):
        value_dict = cast(dict[str, object], value)

        # Check for reference markers
        if "$ref" in value_dict:
            return _transform_ref(
                value_dict["$ref"],
                action_uuids=action_uuids,
                current_index=current_index,
            )

        if "$var" in value_dict:
            return _transform_var(value_dict["$var"])

        if "$input" in value_dict:
            return _transform_input()

        if "$ask" in value_dict:
            return _transform_ask()

        if "$clipboard" in value_dict:
            return _transform_clipboard()

        # Recursively transform nested dicts
        return {
            k: _transform_value(
                v,
                action_uuids=action_uuids,
                current_index=current_index,
            )
            for k, v in value_dict.items()
        }

    if isinstance(value, list):
        return [
            _transform_value(
                item,
                action_uuids=action_uuids,
                current_index=current_index,
            )
            for item in cast(list[object], value)
        ]

    # Primitive values pass through unchanged
    return value


def _transform_ref(
    ref_value: object,
    action_uuids: list[str],
    current_index: int,
) -> dict[str, object]:
    """Transform a $ref marker into a proper action output reference."""
    if not isinstance(ref_value, str):
        raise ValueError(f"$ref value must be a string, got {type(ref_value).__name__}")

    # Handle "previous" - reference the immediately preceding action
    if ref_value == "previous":
        if current_index == 0:
            raise ValueError("Cannot reference 'previous' from the first action")
        target_uuid = action_uuids[current_index - 1]
        return _make_action_output_token(target_uuid)

    # Handle "uuid:XXXX" - reference specific action by UUID
    if ref_value.startswith("uuid:"):
        target_uuid = ref_value[5:].strip().upper()
        if not target_uuid:
            raise ValueError("$ref uuid: value cannot be empty")
        return _make_action_output_token(target_uuid)

    # Handle numeric index (e.g., "0", "1", "-1")
    try:
        index = int(ref_value)
        if index < 0:
            # Negative index: relative to current action
            target_idx = current_index + index
        else:
            # Positive index: absolute position
            target_idx = index

        if target_idx < 0 or target_idx >= len(action_uuids):
            raise ValueError(
                f"$ref index {ref_value} out of range (0-{len(action_uuids) - 1})"
            )
        if target_idx >= current_index:
            raise ValueError(
                f"Cannot reference action at index {target_idx} "
                f"from index {current_index}"
            )
        return _make_action_output_token(action_uuids[target_idx])
    except ValueError as e:
        if "invalid literal" not in str(e):
            raise
        # Not a number, continue to error

    raise ValueError(
        f"Invalid $ref value: {ref_value!r}. "
        "Use 'previous', 'uuid:XXXX', or a numeric index."
    )


def _transform_var(var_name: object) -> dict[str, object]:
    """Transform a $var marker into a variable reference."""
    if not isinstance(var_name, str):
        raise ValueError(f"$var value must be a string, got {type(var_name).__name__}")
    if not var_name:
        raise ValueError("$var variable name cannot be empty")

    return {
        "Value": {
            "VariableName": var_name,
            "Type": "Variable",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def _transform_input() -> dict[str, object]:
    """Transform a $input marker into a shortcut input reference."""
    return {
        "Value": {
            "Type": "ExtensionInput",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def _transform_ask() -> dict[str, object]:
    """Transform a $ask marker into an ask-each-time reference."""
    return {
        "Value": {
            "Type": "Ask",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def _transform_clipboard() -> dict[str, object]:
    """Transform a $clipboard marker into a clipboard reference."""
    return {
        "Value": {
            "Type": "Clipboard",
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }


def _make_action_output_token(
    output_uuid: str,
    output_name: str = "Output",
) -> dict[str, object]:
    """Create a properly formatted action output token."""
    return {
        "Value": {
            "OutputUUID": output_uuid,
            "Type": "ActionOutput",
            "OutputName": output_name,
        },
        "WFSerializationType": "WFTextTokenAttachment",
    }
