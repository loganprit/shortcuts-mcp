from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import FastMCP

from .actions import catalog as action_catalog
from .builder import build_workflow_plist
from .config import get_default_timeout
from .database import (
    get_all_shortcuts,
    get_shortcut_actions,
    get_shortcut_by_name,
    search_shortcuts_by_name,
)
from .database import get_folders as fetch_folders
from .executor import (
    open_file,
    run_via_applescript,
    run_via_url_scheme,
    sign_shortcut_file,
)
from .models import (
    ActionInfo,
    ActionSource,
    RunResult,
    SearchIn,
    ShortcutAction,
    ShortcutDetail,
    ShortcutMetadata,
)
from .parser import action_search_blob, action_types, parse_actions, parse_input_types
from .types import JsonValue

mcp = FastMCP(name="Shortcuts MCP")


@mcp.tool()
async def list_shortcuts(
    folder: str | None = None, include_actions: bool = False
) -> dict[str, list[dict[str, object]]]:
    """List all available macOS shortcuts."""
    rows = await get_all_shortcuts(folder=folder)
    shortcuts: list[dict[str, object]] = []

    for row in rows:
        action_types_list: list[str] | None = None
        if include_actions:
            data = await get_shortcut_actions(row.pk)
            if data:
                actions = parse_actions(data)
                action_types_list = action_types(actions)

        shortcuts.append(
            ShortcutMetadata(
                name=row.name,
                id=row.workflow_id,
                folder=row.folder,
                action_count=row.action_count,
                last_modified=row.modified_at,
                action_types=action_types_list,
            ).model_dump()
        )

    return {"shortcuts": shortcuts}


@mcp.tool()
async def get_shortcut(name: str, include_actions: bool = True) -> dict[str, object]:
    """Get detailed information about a specific shortcut."""
    row = await get_shortcut_by_name(name)
    if not row:
        raise ValueError(f"Shortcut not found: {name}")

    actions_list = None
    input_types = None
    if include_actions:
        data = await get_shortcut_actions(row.pk)
        if data:
            actions_list = parse_actions(data)
            input_types = parse_input_types(data)

    detail = ShortcutDetail(
        name=row.name,
        id=row.workflow_id,
        folder=row.folder,
        action_count=row.action_count,
        last_modified=row.modified_at,
        actions=actions_list,
        input_types=input_types,
    )
    return detail.model_dump()


@mcp.tool()
async def run_shortcut(
    name: str,
    input: object = None,
    wait_for_result: bool = True,
    timeout: int | None = None,
) -> dict[str, object]:
    """Execute a shortcut with optional input.

    The input parameter accepts any JSON-serializable value (str, int, float,
    bool, None, list, or dict). We use 'object' here because Pydantic's schema
    generation cannot handle the recursive JsonValue TypeAlias.
    """
    timeout_value = timeout if timeout is not None else get_default_timeout()
    # Cast to JsonValue for the executor functions
    input_value: JsonValue = input  # type: ignore[assignment]

    if wait_for_result:
        try:
            output, elapsed_ms, returncode = await asyncio.wait_for(
                run_via_applescript(name, input_value), timeout=timeout_value
            )
            if returncode == 0:
                result = RunResult(
                    success=True, output=output, execution_time_ms=elapsed_ms
                )
            else:
                result = RunResult(
                    success=False, output=output, execution_time_ms=elapsed_ms
                )
        except asyncio.TimeoutError:
            result = RunResult(success=False, output="Timeout waiting for shortcut")
        except Exception as exc:  # noqa: BLE001
            result = RunResult(success=False, output=str(exc))
        return result.model_dump()

    try:
        await run_via_url_scheme(name, input_value, timeout=timeout_value)
        return RunResult(success=True).model_dump()
    except Exception as exc:  # noqa: BLE001
        return RunResult(success=False, output=str(exc)).model_dump()


@mcp.tool()
async def search_shortcuts(
    query: str, search_in: SearchIn = "name"
) -> dict[str, list[dict[str, object]]]:
    """Search shortcuts by name or action content."""
    matches: dict[str, ShortcutMetadata] = {}

    if search_in in {"name", "both"}:
        rows = await search_shortcuts_by_name(query)
        for row in rows:
            matches[row.name] = ShortcutMetadata(
                name=row.name,
                id=row.workflow_id,
                folder=row.folder,
                action_count=row.action_count,
                last_modified=row.modified_at,
            )

    if search_in in {"actions", "both"}:
        rows = await get_all_shortcuts()
        for row in rows:
            data = await get_shortcut_actions(row.pk)
            if not data:
                continue
            actions = parse_actions(data)
            blob = action_search_blob(actions).lower()
            if query.lower() in blob:
                matches[row.name] = ShortcutMetadata(
                    name=row.name,
                    id=row.workflow_id,
                    folder=row.folder,
                    action_count=row.action_count,
                    last_modified=row.modified_at,
                )

    return {"shortcuts": [item.model_dump() for item in matches.values()]}


@mcp.tool()
async def get_available_actions(
    source: ActionSource | None = None,
    category: str | None = None,
    search: str | None = None,
    include_parameters: bool = True,
    include_examples: bool = False,
    force_refresh: bool = False,
) -> dict[str, object]:
    """Get all available Shortcuts actions from system and installed apps.

    Args:
        source: Filter by source - "system" (Apple frameworks), "apps" (third-party),
            "library" (from user's shortcuts), "curated" (classic is.workflow.actions.*)
        category: Filter by action category/prefix
            (e.g., "is.workflow.actions", "com.apple")
        search: Search query to filter by identifier, title, or description
        include_parameters: Include parameter definitions (default: True)
        include_examples: Include example parameters from user's library
            (default: False)
        force_refresh: Bypass cache and rescan all sources (default: False)

    Returns:
        Dictionary with:
        - actions: List of ActionInfo objects
        - categories: List of unique category prefixes found
        - sources: Count of actions per source
        - cached: Whether results came from cache
    """
    actions, cached = await action_catalog.get_all_actions(
        source=source,
        category=category,
        search=search,
        force_refresh=force_refresh,
    )

    trimmed: list[ActionInfo] = []
    for action in actions:
        item = action.model_copy(deep=True)
        if not include_parameters:
            item.parameters = []
        if not include_examples:
            item.example_params = None
        trimmed.append(item)

    categories = sorted({item.category for item in trimmed})
    sources: dict[str, int] = {"system": 0, "apps": 0, "library": 0, "curated": 0}
    for item in trimmed:
        sources[item.source] = sources.get(item.source, 0) + 1

    return {
        "actions": [item.model_dump() for item in trimmed],
        "categories": categories,
        "sources": sources,
        "cached": cached,
    }


@mcp.tool()
async def create_shortcut(
    name: str,
    actions: list[ShortcutAction],
    input_types: list[str] | None = None,
    validate: bool = True,
    install: bool = True,
    sign_mode: Literal["anyone", "people-who-know-me"] = "anyone",
    if_exists: Literal["error", "rename"] = "error",
    wait_for_import: bool = True,
    wait_timeout_s: int = 10,
) -> dict[str, object]:
    """Create and import a new shortcut from provided actions."""
    warnings: list[str] = []
    resolved_name = await _resolve_shortcut_name(name, if_exists=if_exists)
    if resolved_name != name:
        warnings.append(
            f"Shortcut '{name}' already exists. Using '{resolved_name}' instead."
        )

    if validate:
        warnings.extend(await _validate_actions(actions))

    temp_dir = Path(tempfile.mkdtemp(prefix="shortcuts-mcp-"))
    filename = _safe_shortcut_filename(resolved_name)
    unsigned_path = temp_dir / f"{filename}.shortcut"
    signed_path = temp_dir / f"{filename} signed.shortcut"

    payload = build_workflow_plist(
        resolved_name,
        actions,
        input_types=input_types,
    )
    unsigned_path.write_bytes(payload)
    await sign_shortcut_file(str(unsigned_path), str(signed_path), sign_mode)

    import_confirmed: bool | None = None
    if install:
        await open_file(str(signed_path))
        if wait_for_import:
            import_confirmed = await _wait_for_shortcut_import(
                resolved_name, timeout_s=wait_timeout_s
            )
            if not import_confirmed:
                warnings.append(
                    "Import not confirmed yet. Shortcuts may still be prompting."
                )

    return {
        "success": True,
        "name": resolved_name,
        "unsigned_path": str(unsigned_path),
        "signed_path": str(signed_path),
        "import_attempted": install,
        "import_confirmed": import_confirmed,
        "warnings": warnings,
    }


@mcp.tool()
async def get_folders() -> dict[str, list[dict[str, str | int]]]:
    """List shortcut folders/collections."""
    folders = await fetch_folders()
    return {"folders": folders}


def main() -> None:
    mcp.run()


async def _resolve_shortcut_name(name: str, if_exists: str) -> str:
    existing = await get_shortcut_by_name(name)
    if not existing:
        return name
    if if_exists == "error":
        raise ValueError(f"Shortcut already exists: {name}")

    suffix = 2
    while True:
        candidate = f"{name} ({suffix})"
        if await get_shortcut_by_name(candidate) is None:
            return candidate
        suffix += 1


async def _wait_for_shortcut_import(name: str, timeout_s: int) -> bool:
    if timeout_s <= 0:
        return False
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while loop.time() < deadline:
        if await get_shortcut_by_name(name):
            return True
        await asyncio.sleep(0.5)
    return False


def _safe_shortcut_filename(name: str) -> str:
    cleaned = name.replace("/", "_").replace(":", "_").strip()
    return cleaned or "shortcut"


async def _validate_actions(actions: list[ShortcutAction]) -> list[str]:
    warnings: list[str] = []
    action_list, _cached = await action_catalog.get_all_actions()
    action_map = {action.identifier: action for action in action_list}

    if not action_map:
        warnings.append("Action catalog empty; skipping validation.")
        return warnings

    for action in actions:
        info = action_map.get(action.identifier)
        if info is None:
            raise ValueError(f"Unknown action identifier: {action.identifier}")
        if not info.parameters:
            continue
        allowed = {param.name for param in info.parameters}
        unknown = sorted(key for key in action.parameters.keys() if key not in allowed)
        if unknown:
            warnings.append(
                f"Action {action.identifier} has unknown parameter keys: {', '.join(unknown)}"
            )
    return warnings


if __name__ == "__main__":
    main()
