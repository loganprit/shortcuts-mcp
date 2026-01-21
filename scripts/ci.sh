#!/usr/bin/env bash
set -euo pipefail

uv sync --all-extras --dev
uv run pytest
uv run basedpyright
uv run ruff check
uv run ruff format --check
