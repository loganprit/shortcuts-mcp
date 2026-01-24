from __future__ import annotations

import json
import time
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Mapping, cast

from .database import get_all_shortcuts, get_shortcut_actions
from .models import ActionInfo, ActionParameter, ActionSource
from .parser import parse_actions
from .types import JsonValue


class ActionCatalog:
    """Manages action discovery and caching."""

    _cache: dict[str, ActionInfo] | None = None
    _cache_time: float = 0.0

    async def get_all_actions(
        self,
        source: ActionSource | None = None,
        category: str | None = None,
        search: str | None = None,
        force_refresh: bool = False,
    ) -> tuple[list[ActionInfo], bool]:
        cached = False
        if self._cache is None or force_refresh:
            await self._refresh_cache()
        else:
            cached = True

        actions = list(self._cache.values()) if self._cache else []

        if source is not None:
            actions = [item for item in actions if item.source == source]

        if category is not None:
            category_lower = category.lower()
            actions = [
                item
                for item in actions
                if item.category.lower() == category_lower
                or item.identifier.lower().startswith(category_lower)
            ]

        if search:
            query = search.lower()

            def matches(action: ActionInfo) -> bool:
                haystack = " ".join(
                    part
                    for part in [
                        action.identifier,
                        action.title or "",
                        action.description or "",
                    ]
                    if part
                ).lower()
                return query in haystack

            actions = [item for item in actions if matches(item)]

        return actions, cached

    async def _refresh_cache(self) -> None:
        system_actions = await self._scan_system_actions()
        app_actions = await self._scan_app_actions()
        library_actions = await self._scan_library_actions()
        curated_actions = self._get_curated_actions()

        merged: dict[str, ActionInfo] = {}
        for action in system_actions + app_actions + curated_actions:
            merged[action.identifier] = action

        for action in library_actions:
            existing = merged.get(action.identifier)
            if existing is None:
                merged[action.identifier] = action
                continue
            merged[action.identifier] = _merge_action(existing, action)

        self._cache = merged
        self._cache_time = time.time()

    async def _scan_system_actions(self) -> list[ActionInfo]:
        root = Path("/System/Library/PrivateFrameworks")
        paths = root.glob("*/Metadata.appintents/extract.actionsdata")
        return _scan_actionsdata_paths(paths, source="system")

    async def _scan_app_actions(self) -> list[ActionInfo]:
        root = Path("/Applications")
        paths = list(
            root.glob(
                "*.app/Contents/Resources/Metadata.appintents/extract.actionsdata"
            )
        )
        paths += list(
            root.glob("*.app/Resources/Metadata.appintents/extract.actionsdata")
        )
        return _scan_actionsdata_paths(paths, source="apps")

    async def _scan_library_actions(self) -> list[ActionInfo]:
        rows = await get_all_shortcuts()
        usage_counts: dict[str, int] = {}
        example_params: dict[str, dict[str, object]] = {}

        for row in rows:
            data = await get_shortcut_actions(row.pk)
            if not data:
                continue
            for action in parse_actions(data):
                usage_counts[action.identifier] = (
                    usage_counts.get(action.identifier, 0) + 1
                )
                if action.identifier not in example_params and action.parameters:
                    example_params[action.identifier] = _coerce_json_mapping(
                        action.parameters
                    )

        actions: list[ActionInfo] = []
        for identifier, count in usage_counts.items():
            actions.append(
                ActionInfo(
                    identifier=identifier,
                    source="library",
                    title=None,
                    description=None,
                    category=_derive_category(identifier, None),
                    parameters=[],
                    platform_availability=None,
                    usage_count=count,
                    example_params=example_params.get(identifier),
                )
            )

        return actions

    def _get_curated_actions(self) -> list[ActionInfo]:
        curated_path = Path(__file__).resolve().parent / "data" / "curated_actions.json"
        if not curated_path.exists():
            return []

        try:
            payload = json.loads(curated_path.read_text())
        except json.JSONDecodeError:
            return []

        payload_map = _as_mapping(payload)
        if payload_map is None:
            return []

        return parse_curated_payload(payload_map)


def _as_mapping(value: object) -> dict[str, object] | None:
    if isinstance(value, dict):
        return cast(dict[str, object], value)
    return None


def _coerce_json_value(value: object) -> JsonValue:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_coerce_json_value(item) for item in cast(list[object], value)]
    if isinstance(value, tuple):
        return [_coerce_json_value(item) for item in cast(tuple[object, ...], value)]
    if isinstance(value, dict):
        return {
            str(key): _coerce_json_value(val)
            for key, val in cast(dict[object, object], value).items()
        }
    return str(value)


def _coerce_json_mapping(value: Mapping[str, object]) -> dict[str, object]:
    return {key: cast(object, _coerce_json_value(val)) for key, val in value.items()}


def parse_curated_payload(payload: Mapping[str, object]) -> list[ActionInfo]:
    actions_data = _as_mapping(payload.get("actions"))
    curated_actions: Mapping[str, object] = actions_data or payload

    actions: list[ActionInfo] = []
    for identifier, entry in curated_actions.items():
        entry_map = _as_mapping(entry)
        if entry_map is None:
            continue
        parameters = _parse_curated_parameters(entry_map.get("parameters"))
        category = _safe_text(entry_map.get("category")) or _derive_category(
            identifier, None
        )
        actions.append(
            ActionInfo(
                identifier=identifier,
                source="curated",
                title=_safe_text(entry_map.get("title")),
                description=_safe_text(entry_map.get("description")),
                category=category,
                parameters=parameters,
                platform_availability=None,
                usage_count=0,
                example_params=None,
            )
        )
    return actions


def _scan_actionsdata_paths(
    paths: Iterable[Path], source: ActionSource
) -> list[ActionInfo]:
    actions: list[ActionInfo] = []

    for path in paths:
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        payload_map = _as_mapping(payload)
        if payload_map is None:
            continue
        actions.extend(parse_actionsdata_payload(payload_map, source=source))
    return actions


def parse_actionsdata_payload(
    payload: Mapping[str, object], source: ActionSource
) -> list[ActionInfo]:
    actions_data = _as_mapping(payload.get("actions"))
    if actions_data is None:
        return []

    parsed: list[ActionInfo] = []
    for identifier, entry in actions_data.items():
        entry_map = _as_mapping(entry)
        if entry_map is None:
            continue
        parsed_action = _parse_actionsdata_entry(identifier, entry_map, source)
        if parsed_action is not None:
            parsed.append(parsed_action)
    return parsed


def _parse_actionsdata_entry(
    fallback_identifier: str, entry: Mapping[str, object], source: ActionSource
) -> ActionInfo | None:
    identifier = _safe_text(entry.get("identifier")) or fallback_identifier
    title = _extract_localized_text(entry.get("title"))
    description = None
    description_meta = _as_mapping(entry.get("descriptionMetadata"))
    if description_meta is not None:
        description = _extract_localized_text(description_meta.get("descriptionText"))

    parameters = _parse_actionsdata_parameters(entry.get("parameters"))
    availability = _parse_availability(entry.get("availabilityAnnotations"))
    fqtn = _safe_text(entry.get("fullyQualifiedTypeName"))
    category = _derive_category(identifier, fqtn)

    return ActionInfo(
        identifier=identifier,
        source=source,
        title=title,
        description=description,
        category=category,
        parameters=parameters,
        platform_availability=availability,
        usage_count=0,
        example_params=None,
    )


def _parse_actionsdata_parameters(value: object) -> list[ActionParameter]:
    if not isinstance(value, list):
        return []
    parameters: list[ActionParameter] = []
    for item in cast(list[object], value):
        item_map = _as_mapping(item)
        if item_map is None:
            continue
        name = _safe_text(item_map.get("name"))
        if not name:
            continue
        title = _extract_localized_text(item_map.get("title"))
        value_type = _parse_value_type(item_map.get("valueType"))
        is_optional = bool(item_map.get("isOptional", False))
        parameters.append(
            ActionParameter(
                name=name,
                title=title,
                value_type=value_type,
                is_optional=is_optional,
                description=None,
            )
        )
    return parameters


def _parse_curated_parameters(value: object) -> list[ActionParameter]:
    if not isinstance(value, list):
        return []
    parameters: list[ActionParameter] = []
    for item in cast(list[object], value):
        item_map = _as_mapping(item)
        if item_map is None:
            continue
        name = _safe_text(item_map.get("name"))
        if not name:
            continue
        parameters.append(
            ActionParameter(
                name=name,
                title=_safe_text(item_map.get("title")),
                value_type=_safe_text(item_map.get("value_type")) or "unknown",
                is_optional=bool(item_map.get("is_optional", False)),
                description=_safe_text(item_map.get("description")),
            )
        )
    return parameters


def _parse_availability(value: object) -> dict[str, str] | None:
    value_map = _as_mapping(value)
    if value_map is None:
        return None
    availability: dict[str, str] = {}
    for platform, meta in value_map.items():
        meta_map = _as_mapping(meta)
        if meta_map is None:
            continue
        version = meta_map.get("introducedVersion")
        if isinstance(version, str):
            availability[platform] = version
    return availability or None


def _parse_value_type(value: object) -> str:
    if isinstance(value, str):
        return value
    value_map = _as_mapping(value)
    if value_map is None:
        return "unknown"

    primitive = value_map.get("primitiveType")
    if isinstance(primitive, str):
        return primitive.lower()

    entity = value_map.get("entityType")
    if isinstance(entity, str):
        return f"entity:{entity}"

    enum_type = value_map.get("enumType")
    if isinstance(enum_type, str):
        return f"enum:{enum_type}"

    type_name = value_map.get("typeName")
    if isinstance(type_name, str):
        return type_name

    identifier = value_map.get("identifier")
    if isinstance(identifier, str):
        return identifier

    return "unknown"


def _extract_localized_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    value_map = _as_mapping(value)
    if value_map is None:
        return None
    key = value_map.get("key")
    if isinstance(key, str):
        return key
    return None


def _safe_text(value: object) -> str | None:
    if isinstance(value, str):
        return value
    return None


def _derive_category(identifier: str, fqtn: str | None) -> str:
    if identifier.startswith("is.workflow.actions."):
        return "workflow"
    if identifier.startswith("com.apple.ShortcutsActions."):
        return "apple.shortcuts"
    if identifier.startswith("com.apple."):
        return "apple.system"
    if fqtn and fqtn.startswith("ShortcutsActions."):
        return "apple.shortcuts"
    return "third-party"


def _merge_action(base: ActionInfo, incoming: ActionInfo) -> ActionInfo:
    return ActionInfo(
        identifier=base.identifier,
        source=base.source if base.source != "library" else incoming.source,
        title=base.title or incoming.title,
        description=base.description or incoming.description,
        category=base.category or incoming.category,
        parameters=base.parameters or incoming.parameters,
        platform_availability=base.platform_availability
        or incoming.platform_availability,
        usage_count=base.usage_count + incoming.usage_count,
        example_params=base.example_params or incoming.example_params,
    )


catalog = ActionCatalog()
