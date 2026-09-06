# Repository guidelines

This MCP server integrates with macOS Shortcuts through AppleScript and the local Shortcuts database. Live integration requires macOS; unit tests should use fixtures rather than personal Shortcuts data.

- Use `uv sync --all-extras --dev` for development dependencies and `uv run shortcuts-mcp` to start the server.
- For Python changes, run affected tests with `uv run pytest`; `scripts/ci.sh` runs the full tests, typing, lint, formatting, and server-startup checks when broader verification is needed.
- Database access is read-only. Keep Shortcuts execution separate from database inspection.
- Configuration comes from `src/shortcuts_mcp/config.py`; use `SHORTCUTS_DB_PATH` to select a fixture database for integration checks.
