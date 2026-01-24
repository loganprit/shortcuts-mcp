from __future__ import annotations

import plistlib
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, cast

from .models import ShortcutAction

SHORTCUTS_INFO_PLIST = Path("/System/Applications/Shortcuts.app/Contents/Info.plist")

_client_info: tuple[str | None, str | None] | None = None
_DROP = object()


def get_shortcuts_client_info(
    info_plist_path: Path = SHORTCUTS_INFO_PLIST,
) -> tuple[str | None, str | None]:
    global _client_info
    if info_plist_path == SHORTCUTS_INFO_PLIST and _client_info is not None:
        return _client_info

    if not info_plist_path.exists():
        return None, None

    try:
        with info_plist_path.open("rb") as handle:
            payload = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException):
        return None, None

    release = payload.get("CFBundleShortVersionString")
    client_release = release if isinstance(release, str) else None
    client_version = _parse_bundle_version(payload.get("CFBundleVersion"))

    if info_plist_path == SHORTCUTS_INFO_PLIST:
        _client_info = (client_release, client_version)

    return client_release, client_version


def build_workflow_payload(
    name: str,
    actions: Iterable[ShortcutAction],
    input_types: list[str] | None = None,
    client_release: str | None = None,
    client_version: str | None = None,
) -> dict[str, object]:
    if client_release is None or client_version is None:
        detected_release, detected_version = get_shortcuts_client_info()
        if client_release is None:
            client_release = detected_release
        if client_version is None:
            client_version = detected_version

    payload: dict[str, object] = {
        "WFWorkflowName": name,
        "WFWorkflowActions": build_workflow_actions(actions),
    }
    if input_types:
        payload["WFWorkflowInputContentItemClasses"] = list(input_types)
    if client_release:
        payload["WFWorkflowClientRelease"] = client_release
    if client_version is not None:
        payload["WFWorkflowClientVersion"] = client_version
    return payload


def build_workflow_plist(
    name: str,
    actions: Iterable[ShortcutAction],
    input_types: list[str] | None = None,
    client_release: str | None = None,
    client_version: str | None = None,
) -> bytes:
    payload = build_workflow_payload(
        name,
        actions,
        input_types=input_types,
        client_release=client_release,
        client_version=client_version,
    )
    return plistlib.dumps(payload, fmt=plistlib.FMT_BINARY)


def build_workflow_actions(
    actions: Iterable[ShortcutAction],
) -> list[dict[str, object]]:
    built: list[dict[str, object]] = []
    for action in actions:
        params = _coerce_plist_mapping(action.parameters)
        built.append(
            {
                "WFWorkflowActionIdentifier": action.identifier,
                "WFWorkflowActionParameters": params,
            }
        )
    return built


def _parse_bundle_version(value: object) -> str | None:
    if isinstance(value, int):
        return str(value)
    if not isinstance(value, str) or not value:
        return None
    return value


def _coerce_plist_mapping(value: dict[str, object]) -> dict[str, object]:
    output: dict[str, object] = {}
    for key, item in value.items():
        coerced = _coerce_plist_value(item)
        if coerced is _DROP:
            continue
        output[str(key)] = coerced
    return output


def _coerce_plist_value(value: object) -> object:
    if value is None:
        return _DROP
    if isinstance(value, (str, int, float, bool, bytes)):
        return value
    if isinstance(value, (datetime, date)):
        return value
    if isinstance(value, list):
        items: list[object] = []
        for item in cast(list[object], value):
            coerced = _coerce_plist_value(item)
            if coerced is _DROP:
                continue
            items.append(coerced)
        return items
    if isinstance(value, dict):
        output: dict[str, object] = {}
        for key, item in cast(dict[object, object], value).items():
            coerced = _coerce_plist_value(item)
            if coerced is _DROP:
                continue
            output[str(key)] = coerced
        return output
    raise ValueError(f"Unsupported parameter value type: {type(value).__name__}")
