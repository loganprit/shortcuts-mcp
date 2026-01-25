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
    delete_shortcut,
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
    ShortcutIcon,
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
    icon: ShortcutIcon | None = None,
    validate: bool = True,
    install: bool = True,
    sign_mode: Literal["anyone", "people-who-know-me"] = "anyone",
    if_exists: Literal["error", "rename", "replace"] = "error",
    wait_for_import: bool = True,
    wait_timeout_s: int = 10,
) -> dict[str, object]:
    """Create and import a new shortcut from provided actions."""
    warnings: list[str] = []

    # Check for existing shortcuts (including " signed" variants)
    existing = await _find_existing_shortcut(name)
    resolved_name = name

    if existing:
        if if_exists == "error":
            raise ValueError(f"Shortcut already exists: {existing}")
        elif if_exists == "replace":
            # Delete the existing shortcut before import
            try:
                await delete_shortcut(existing)
                warnings.append(f"Replaced existing shortcut '{existing}'.")
            except RuntimeError as e:
                warnings.append(f"Could not delete existing shortcut: {e}")
        elif if_exists == "rename":
            resolved_name = await _generate_unique_name(name)
            warnings.append(
                f"Shortcut '{name}' already exists. Using '{resolved_name}' instead."
            )

    if validate:
        warnings.extend(await _validate_actions(actions))

    temp_dir = Path(tempfile.mkdtemp(prefix="shortcuts-mcp-"))
    filename = _safe_shortcut_filename(resolved_name)
    unsigned_path = temp_dir / f"{filename}.shortcut"
    signed_temp_path = temp_dir / f"{filename} signed.shortcut"

    payload = build_workflow_plist(
        resolved_name,
        actions,
        input_types=input_types,
        icon=icon,
    )
    unsigned_path.write_bytes(payload)
    await sign_shortcut_file(str(unsigned_path), str(signed_temp_path), sign_mode)

    # Rename signed file to remove " signed" suffix for clean import
    # macOS Shortcuts uses the filename (minus extension) as the shortcut name
    unsigned_path.unlink()  # Remove unsigned version
    final_import_path = temp_dir / f"{filename}.shortcut"
    signed_temp_path.rename(final_import_path)

    import_confirmed: bool | None = None
    imported_name: str | None = None

    if install:
        await open_file(str(final_import_path))
        if wait_for_import:
            # Check for both the intended name and potential " signed" variant
            imported_name, import_confirmed = await _wait_for_shortcut_import_flexible(
                resolved_name, timeout_s=wait_timeout_s
            )
            if not import_confirmed:
                warnings.append(
                    "Import not confirmed yet. Shortcuts may still be prompting."
                )
            elif imported_name and imported_name != resolved_name:
                warnings.append(
                    f"Shortcut was imported as '{imported_name}' "
                    f"instead of '{resolved_name}'."
                )

    return {
        "success": True,
        "name": resolved_name,
        "imported_name": imported_name,
        "file_path": str(final_import_path),
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


async def _find_existing_shortcut(name: str) -> str | None:
    """Check if a shortcut with the given name (or " signed" variant) exists.

    Returns the actual name if found, None otherwise.
    """
    # Check exact name first
    if await get_shortcut_by_name(name):
        return name

    # Check for " signed" variant (legacy naming issue)
    signed_name = f"{name} signed"
    if await get_shortcut_by_name(signed_name):
        return signed_name

    return None


async def _generate_unique_name(name: str) -> str:
    """Generate a unique shortcut name by appending a suffix."""
    suffix = 2
    while True:
        candidate = f"{name} ({suffix})"
        if await _find_existing_shortcut(candidate) is None:
            return candidate
        suffix += 1


async def _wait_for_shortcut_import_flexible(
    name: str, timeout_s: int
) -> tuple[str | None, bool]:
    """Wait for shortcut import, checking both exact name and " signed" variant.

    Returns (imported_name, success) tuple.
    """
    if timeout_s <= 0:
        return None, False

    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s

    # Names to check (prioritize exact name)
    names_to_check = [name, f"{name} signed"]

    while loop.time() < deadline:
        for check_name in names_to_check:
            if await get_shortcut_by_name(check_name):
                return check_name, True
        await asyncio.sleep(0.5)

    return None, False


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

    # Standard parameters added automatically (not user-provided)
    auto_params = {"UUID", "GroupingIdentifier"}

    for action in actions:
        info = action_map.get(action.identifier)
        if info is None:
            raise ValueError(f"Unknown action identifier: {action.identifier}")
        if not info.parameters:
            continue

        param_names = set(action.parameters.keys())
        allowed = {param.name for param in info.parameters}

        # Check for unknown parameters (excluding auto-generated ones)
        unknown = sorted(
            key for key in param_names if key not in allowed and key not in auto_params
        )
        if unknown:
            keys = ", ".join(unknown)
            warnings.append(
                f"Action {action.identifier} has unknown parameter keys: {keys}"
            )

        # Check for missing required parameters
        required_params = {
            param.name for param in info.parameters if not param.is_optional
        }
        # GroupingIdentifier is often "required" in schema but auto-provided
        provided = param_names | auto_params
        missing = sorted(required_params - provided)
        if missing:
            keys = ", ".join(missing)
            warnings.append(
                f"Action {action.identifier} may be missing required parameters: {keys}"
            )

    return warnings


if __name__ == "__main__":
    main()
