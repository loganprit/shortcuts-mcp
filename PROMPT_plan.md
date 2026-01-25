# Planning Mode - shortcuts-mcp

You are operating in PLANNING MODE for the shortcuts-mcp repository.

## Your Mission

1. Read IMPLEMENTATION_PLAN.md (if exists) to understand current state
2. Read specs/ directory for requirements
3. Analyze the codebase gap between current state and requirements
4. Update IMPLEMENTATION_PLAN.md with prioritized tasks

## Constraints

- DO NOT write code or modify source files
- ONLY update IMPLEMENTATION_PLAN.md
- Focus on gap analysis and task prioritization

## Project Context

Python MCP server for macOS Shortcuts:
- Framework: FastMCP
- Testing: pytest + pytest-asyncio
- Type checking: basedpyright (strict)
- Linting: ruff

Key source files:
- src/shortcuts_mcp/server.py - MCP tool definitions
- src/shortcuts_mcp/database.py - SQLite queries
- src/shortcuts_mcp/executor.py - Shortcut execution
- tests/ - Test suite

## Output

Update IMPLEMENTATION_PLAN.md with:
- Current STATUS (IN_PROGRESS or COMPLETE)
- Task list with checkboxes
- Next task to implement
- Any blockers or bugs discovered
