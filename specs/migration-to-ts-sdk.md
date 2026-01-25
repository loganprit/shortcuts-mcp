# Migration to MCP TypeScript SDK (Bun + stdio)

## Goal

Replace the Python FastMCP server with a TypeScript MCP server built on the
Model Context Protocol TypeScript SDK, using Bun for package management and
runtime, and stdio transport for local CLI integration.

## Scope

- Preserve tool names, arguments, and response shapes.
- Maintain environment variables and default behavior.
- Use stdio transport for MCP server connectivity.
- Remove Python implementation after parity is verified.

## Out of Scope

- Streamable HTTP or SSE transports.
- New tools or behavioral changes beyond parity fixes.
- Database write operations.

## Current Tool Surface (parity required)

- list_shortcuts(folder?, include_actions?)
- get_shortcut(name, include_actions?)
- search_shortcuts(query, search_in?)
- get_folders()
- get_available_actions(source?, category?, search?, include_parameters?, include_examples?, force_refresh?)
- run_shortcut(name, input?, wait_for_result?, timeout?)

## Environment Variables (parity required)

- SHORTCUTS_DB_PATH (default: ~/Library/Shortcuts/Shortcuts.sqlite)
- SHORTCUTS_DEFAULT_TIMEOUT (default: 30)
- SHORTCUTS_LOG_LEVEL (default: INFO)

## Decisions Locked

- Transport: stdio (local process integration)
- Runtime: Bun (no Node-only tooling in the final setup)
- Python removal: safe to remove after parity checks, main branch retains Python

## Acceptance Criteria

- Bun can run the MCP server over stdio without additional build steps.
- All tools match current names, inputs, and output shapes.
- Default timeouts, db path, and log level behave the same.
- Tools that read Shortcuts data return the same results for the same inputs.
- README and Claude Code config use Bun entrypoint.
- CI script uses Bun to run lint/typecheck/tests.
- Python implementation removed after parity verification.

## Validation

- Run scripts/ci.sh after each build iteration.
- Use local manual checks for a subset of tools via stdio transport.
