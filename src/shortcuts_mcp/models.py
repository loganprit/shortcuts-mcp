from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ShortcutAction(BaseModel):
    identifier: str
    parameters: dict[str, object] = Field(default_factory=dict)


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

ActionSource = Literal["system", "apps", "library", "curated"]


class ActionParameter(BaseModel):
    name: str
    title: str | None = None
    value_type: str
    is_optional: bool = False
    description: str | None = None


class ActionInfo(BaseModel):
    identifier: str
    source: ActionSource
    title: str | None = None
    description: str | None = None
    category: str
    parameters: list[ActionParameter] = Field(default_factory=list)
    platform_availability: dict[str, str] | None = None
    usage_count: int = 0
    example_params: dict[str, object] | None = None
