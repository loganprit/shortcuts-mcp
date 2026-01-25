# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
bun run src/index.ts          # Run the MCP server locally
bun test                      # Run all tests
bun test tests/parser.test.ts # Run a single test file
bun run typecheck             # Type checking (tsc strict mode)
bun run lint                  # Lint code (Biome)
bun run format                # Format code (Biome)
bun run format:check          # Check formatting without modifying
scripts/ci.sh                 # Run full CI suite locally
```

## Architecture

TypeScript MCP server for macOS Shortcuts with read-only database access and two execution modes.

### Module Layout

- **index.ts** - Entrypoint that starts the MCP server with stdio transport
- **server.ts** - MCP server setup using `@modelcontextprotocol/sdk`. Registers all tools
- **database.ts** - SQLite queries via `bun:sqlite`. Read-only connection to `~/Library/Shortcuts/Shortcuts.sqlite`. Handles Cocoa epoch timestamps and UUID normalization
- **executor.ts** - Two execution strategies:
  - `runViaAppleScript()` - Synchronous execution with output capture via osascript
  - `runViaUrlScheme()` - Asynchronous execution via `shortcuts://` URL scheme with optional timeout
- **parser.ts** - Parses binary plist blobs (shortcut action data). Extracts `WFWorkflowActions` and `WFWorkflowInputContentItemClasses`
- **actions.ts** - Action catalog discovery from system frameworks, apps, and user's shortcut library
- **config.ts** - Environment variable handling for `SHORTCUTS_DB_PATH`, `SHORTCUTS_DEFAULT_TIMEOUT`, `SHORTCUTS_LOG_LEVEL`
- **types.ts** - Type aliases for JSON data structures (`JsonPrimitive`, `JsonValue`). Used throughout to avoid `any` types
- **tools/** - Individual MCP tool implementations with Zod schemas

### Data Flow

1. MCP tool receives request → 2. `database.ts` queries SQLite → 3. `parser.ts` deserializes action plist blobs → 4. Tool handler structures response → 5. (for `run_shortcut`) `executor.ts` runs via AppleScript or URL scheme

## Environment Variables

```bash
SHORTCUTS_DB_PATH="~/Library/Shortcuts/Shortcuts.sqlite"  # Database location
SHORTCUTS_DEFAULT_TIMEOUT=30                              # AppleScript timeout in seconds
SHORTCUTS_LOG_LEVEL="INFO"
```

## Key Implementation Details

- Database connection is always read-only (`readonly: true` in Bun sqlite)
- Cocoa epoch (2001-01-01) used for timestamp conversion in database.ts
- Shortcut UUIDs may be stored as 16-byte blobs or strings; `normalizeUuid()` handles both
- Action data stored as binary plist in `ZSHORTCUTACTIONS.ZDATA` column
- Plist parsing handles two formats: direct list of actions OR dict-wrapped with `WFWorkflowActions` key
- Type checking uses strict mode via `tsc`
- Tool handlers must return `{ content: [{ type: "text", text: JSON.stringify(...) }] }` format per MCP SDK

## btca

When you need up-to-date information about technologies used in this project, use btca to query source repositories directly.

**Available resources**: zod, typescript, bun, modelContextProtocol, biome

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
# Query MCP TypeScript SDK for implementation details
btca ask -r modelContextProtocol -q "How do I create a custom MCP tool with Zod schemas?"

# Query Bun for runtime-specific features
btca ask -r bun -q "How do I use bun:sqlite for read-only database access?"

# Query Biome for linting configuration
btca ask -r biome -q "How do I configure Biome for TypeScript strict mode?"
```
