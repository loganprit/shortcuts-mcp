from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DB_PATH = str(Path.home() / "Library/Shortcuts/Shortcuts.sqlite")
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_LOG_LEVEL = "INFO"


def get_db_path() -> Path:
    return Path(os.environ.get("SHORTCUTS_DB_PATH", DEFAULT_DB_PATH)).expanduser()


def get_default_timeout() -> int:
    value = os.environ.get("SHORTCUTS_DEFAULT_TIMEOUT", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        return int(value)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def get_log_level() -> str:
    return os.environ.get("SHORTCUTS_LOG_LEVEL", DEFAULT_LOG_LEVEL)
