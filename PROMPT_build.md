# Building Mode - shortcuts-mcp

You are operating in BUILDING MODE for the shortcuts-mcp repository.

## Your Mission

1. Read IMPLEMENTATION_PLAN.md to find the NEXT uncompleted task
2. Implement ONLY that one task
3. Run validation: `scripts/ci.sh`
4. Update IMPLEMENTATION_PLAN.md to mark progress

## Constraints

- ONE task per iteration only
- Follow existing code patterns
- Maintain strict typing (no `Any` types - use JsonValue from types.py)
- Write tests for new functionality

## Project Standards

Type Checking (basedpyright strict):
- Use `from __future__ import annotations`
- Prefer `object` over `Any`

Code Style (ruff):
- Python 3.10+ syntax
- PEP 8: 4-space indent, snake_case
- Async/await for I/O operations

Testing (pytest):
- Files: tests/test_*.py
- Fast, deterministic unit tests

## Validation Commands

```bash
uv run pytest
uv run basedpyright
uv run ruff check
uv run ruff format --check
```

## Bug Documentation

If you find a bug:
1. Add to IMPLEMENTATION_PLAN.md under ## Bugs
2. Include priority (P0/P1/P2) and reproduction steps

## Completion

When task is done:
1. Mark task as [x] in IMPLEMENTATION_PLAN.md
2. If ALL tasks done, set STATUS: COMPLETE at top
