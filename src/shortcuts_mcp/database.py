from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import aiosqlite

from .config import get_db_path

COCOA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)


@dataclass
class ShortcutRow:
    pk: int
    name: str
    action_count: int | None
    modified_at: str | None
    workflow_id: str | None
    folder: str | None


def _connect() -> aiosqlite.Connection:
    """Create a read-only connection to the Shortcuts database."""
    db_path = get_db_path()
    uri = f"file:{db_path}?mode=ro"
    return aiosqlite.connect(uri, uri=True)


def _normalize_uuid(value: str | bytes | int | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        if len(value) == 16:
            return str(uuid.UUID(bytes=value))
        try:
            return value.decode("utf-8")
        except UnicodeDecodeError:
            return None
    return str(value)


def _convert_cocoa_date(value: float | int | str | bytes | None) -> str | None:
    if value is None:
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    return (COCOA_EPOCH + timedelta(seconds=seconds)).isoformat()


async def get_all_shortcuts(folder: str | None = None) -> list[ShortcutRow]:
    """Get all shortcuts from the database.

    Note: folder filtering is not supported in current macOS schema.
    """
    query = """
        SELECT
            Z_PK AS pk,
            ZNAME AS name,
            ZACTIONCOUNT AS action_count,
            ZMODIFICATIONDATE AS modified_at,
            ZWORKFLOWID AS workflow_id
        FROM ZSHORTCUT
        WHERE ZNAME IS NOT NULL
        ORDER BY ZNAME COLLATE NOCASE
    """
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(query)).fetchall()

    return [
        ShortcutRow(
            pk=row["pk"],
            name=row["name"],
            action_count=row["action_count"],
            modified_at=_convert_cocoa_date(row["modified_at"]),
            workflow_id=_normalize_uuid(row["workflow_id"]),
            folder=None,  # Folder relationship not available in schema
        )
        for row in rows
    ]


async def get_shortcut_by_name(name: str) -> ShortcutRow | None:
    """Get a shortcut by its name."""
    query = """
        SELECT
            Z_PK AS pk,
            ZNAME AS name,
            ZACTIONCOUNT AS action_count,
            ZMODIFICATIONDATE AS modified_at,
            ZWORKFLOWID AS workflow_id
        FROM ZSHORTCUT
        WHERE ZNAME = ?
        LIMIT 1
    """
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        row = await (await conn.execute(query, [name])).fetchone()
    if not row:
        return None
    return ShortcutRow(
        pk=row["pk"],
        name=row["name"],
        action_count=row["action_count"],
        modified_at=_convert_cocoa_date(row["modified_at"]),
        workflow_id=_normalize_uuid(row["workflow_id"]),
        folder=None,
    )


async def get_shortcut_actions(shortcut_pk: int) -> bytes | None:
    query = """
        SELECT ZDATA AS data
        FROM ZSHORTCUTACTIONS
        WHERE ZSHORTCUT = ?
        LIMIT 1
    """
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        row = await (await conn.execute(query, [shortcut_pk])).fetchone()
    if not row:
        return None
    return row["data"]


async def get_folders() -> list[dict[str, str | int]]:
    """Get all collections/folders.

    Note: macOS Shortcuts uses ZCOLLECTION for system categories (Root, ShareSheet,
    etc.)
    rather than user-defined folders. Returns collection identifiers or display names.
    """
    query = """
        SELECT
            COALESCE(ZTEMPORARYSYNCFOLDERNAME, ZIDENTIFIER) AS name
        FROM ZCOLLECTION
        WHERE ZIDENTIFIER IS NOT NULL
        ORDER BY name COLLATE NOCASE
    """
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(query)).fetchall()
    return [
        {"name": row["name"], "shortcut_count": 0}  # Count not available without FK
        for row in rows
        if row["name"] is not None
    ]


async def search_shortcuts_by_name(query: str) -> list[ShortcutRow]:
    """Search shortcuts by name pattern."""
    sql = """
        SELECT
            Z_PK AS pk,
            ZNAME AS name,
            ZACTIONCOUNT AS action_count,
            ZMODIFICATIONDATE AS modified_at,
            ZWORKFLOWID AS workflow_id
        FROM ZSHORTCUT
        WHERE ZNAME LIKE ?
        ORDER BY ZNAME COLLATE NOCASE
    """
    like = f"%{query}%"
    async with _connect() as conn:
        conn.row_factory = aiosqlite.Row
        rows = await (await conn.execute(sql, [like])).fetchall()
    return [
        ShortcutRow(
            pk=row["pk"],
            name=row["name"],
            action_count=row["action_count"],
            modified_at=_convert_cocoa_date(row["modified_at"]),
            workflow_id=_normalize_uuid(row["workflow_id"]),
            folder=None,
        )
        for row in rows
    ]
