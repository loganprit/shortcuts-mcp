# Repository Guidelines

## Project Structure & Module Organization
- `src/shortcuts_mcp/`: core library and MCP server implementation.
  - `server.py`: MCP tool definitions and entrypoint.
  - `database.py`: read-only access to the Shortcuts SQLite DB.
  - `executor.py`: AppleScript + URL scheme execution helpers.
  - `parser.py`, `models.py`, `config.py`: parsing, schemas, and config.
- `tests/`: pytest suite (currently `tests/test_parser.py`).
- `README.md` / `CLAUDE.md`: usage notes and local run commands.

## Build, Test, and Development Commands
- `uv run shortcuts-mcp`: run the MCP server locally.
- `uv run pytest`: execute the test suite.
- `scripts/ci.sh`: run after code changes to ensure tests, lint, and typing pass.

## Coding Style & Naming Conventions
- Python 3.10+ with type hints and async/await patterns.
- PEP 8 formatting: 4-space indentation, snake_case for functions/variables, PascalCase for classes.
- Avoid `Any` in type hints; prefer concrete types or `object` when needed.
- Keep public tool functions small; delegate logic to `database.py`, `executor.py`, and `parser.py`.

## Testing Guidelines
- Framework: `pytest` with `pytest-asyncio` for async tests.
- Name tests `tests/test_*.py` with functions `test_*`.
- Prefer fast, deterministic unit tests; avoid requiring live Shortcuts data unless explicitly intended.

## Commit & Pull Request Guidelines
- Recent commits are short, imperative subjects (e.g., "Update path in README for shortcuts-mcp").
- Merge commits are present; keep branch names descriptive when opening PRs.
- PRs should include a concise description, test results, and any config or environment changes required to run locally.

## Configuration & Environment Notes
- Default Shortcuts DB path: `SHORTCUTS_DB_PATH=~/Library/Shortcuts/Shortcuts.sqlite`.
- Optional env vars: `SHORTCUTS_DEFAULT_TIMEOUT` (seconds), `SHORTCUTS_LOG_LEVEL`.
- macOS-specific project due to AppleScript/Shortcuts integration.

## Ralph Wiggum Loop Operations

When operating within the Ralph loop:

### Iteration Discipline
- Complete ONE task per iteration
- Always read IMPLEMENTATION_PLAN.md first
- Update IMPLEMENTATION_PLAN.md before finishing
- Run full validation via scripts/ci.sh

### Plan Updates
- Mark completed tasks with [x]
- Document bugs immediately with priority
- Set STATUS: COMPLETE when all tasks done

### Validation Flow
1. Implement code changes
2. Run `scripts/ci.sh` (pytest + basedpyright + ruff)
3. Fix any failures before completing iteration

## btca

When you need up-to-date information about technologies used in this project, use btca to query source repositories directly.

**Available resources**: zod, typescript, bun, modelContextProtocol, pydantic, biome, pytest, gemini

### Usage

```bash
btca ask -r <resource> -q "<question>"
```

Use multiple `-r` flags to query multiple resources at once:

```bash
btca ask -r zod -r typescript -q "How do I use Zod with TypeScript for runtime validation?"
```

### Examples

```bash
# Query MCP Python SDK for implementation details
btca ask -r modelContextProtocol -q "How do I create a custom MCP tool with async handlers?"

# Query Gemini CLI for troubleshooting terminal output
btca ask -r gemini -q "Why aren't agent responses showing in terminal output?"

# Query multiple testing frameworks
btca ask -r pytest -r pydantic -q "How to validate async test fixtures with Pydantic models?"
```
