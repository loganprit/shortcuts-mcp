from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import get_default_timeout
from .database import (
    get_all_shortcuts,
    get_shortcut_actions,
    get_shortcut_by_name,
    search_shortcuts_by_name,
)
from .database import (
    get_folders as fetch_folders,
)
from .executor import run_via_applescript, run_via_url_scheme
from .models import RunResult, SearchIn, ShortcutDetail, ShortcutMetadata
from .parser import action_search_blob, action_types, parse_actions, parse_input_types

mcp = FastMCP(name="Shortcuts MCP")


@mcp.tool()
async def list_shortcuts(
    folder: str | None = None, include_actions: bool = False
) -> dict:
    """List all available macOS shortcuts."""
    rows = await get_all_shortcuts(folder=folder)
    shortcuts: list[dict[str, Any]] = []

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
async def get_shortcut(name: str, include_actions: bool = True) -> dict:
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
    input: Any | None = None,
    wait_for_result: bool = True,
    timeout: int | None = None,
) -> dict:
    """Execute a shortcut with optional input."""
    timeout_value = timeout if timeout is not None else get_default_timeout()

    if wait_for_result:
        try:
            output, elapsed_ms, returncode = await asyncio.wait_for(
                run_via_applescript(name, input), timeout=timeout_value
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
        await run_via_url_scheme(name, input, timeout=timeout_value)
        return RunResult(success=True).model_dump()
    except Exception as exc:  # noqa: BLE001
        return RunResult(success=False, output=str(exc)).model_dump()


@mcp.tool()
async def search_shortcuts(query: str, search_in: SearchIn = "name") -> dict:
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
async def get_folders() -> dict:
    """List shortcut folders/collections."""
    folders = await fetch_folders()
    return {"folders": folders}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
