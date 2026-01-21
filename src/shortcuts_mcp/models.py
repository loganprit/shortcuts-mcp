from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ShortcutAction(BaseModel):
    identifier: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ShortcutMetadata(BaseModel):
    name: str
    id: str | None = None
    folder: str | None = None
    action_count: int | None = None
    last_modified: str | None = None
    action_types: list[str] | None = None


class ShortcutDetail(BaseModel):
    name: str
    id: str | None = None
    folder: str | None = None
    action_count: int | None = None
    last_modified: str | None = None
    actions: list[ShortcutAction] | None = None
    input_types: list[str] | None = None


class FolderInfo(BaseModel):
    name: str
    shortcut_count: int


class RunResult(BaseModel):
    success: bool
    output: str | None = None
    execution_time_ms: int | None = None


SearchIn = Literal["name", "actions", "both"]
