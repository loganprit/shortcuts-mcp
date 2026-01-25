# Implementation Plan - shortcuts-mcp

STATUS: IN_PROGRESS

## Overview

Migrate the MCP server from Python FastMCP to the MCP TypeScript SDK using Bun
as the runtime/package manager, with stdio transport and full tool parity.

## Task List

### Phase 0: Specs and Success Criteria

- [x] Task 0.1 - Create migration spec with goals, scope, and acceptance checks
- [x] Task 0.2 - Inventory current Python tool inputs/outputs for parity checklist

### Phase 1: Bun + TypeScript Scaffold

- [x] Task 1.1 - Initialize Bun project and TS config for MCP server
- [x] Task 1.2 - Define TS project layout (entrypoint, server, tool modules)
- [x] Task 1.3 - Add base lint/typecheck/test tooling for TS (Bun-friendly)

### Phase 2: Port Core Logic

- [x] Task 2.1 - Port config/env handling to TypeScript
- [x] Task 2.2 - Port database read access and queries to TypeScript
- [x] Task 2.3 - Port plist parsing + action extraction to TypeScript
- [x] Task 2.4 - Port action catalog discovery to TypeScript
- [x] Task 2.5 - Port execution helpers for run_shortcut parity

### Phase 3: MCP Server + Tools

- [x] Task 3.1 - Implement McpServer with stdio transport
- [x] Task 3.2 - Register tools with Zod schemas matching current behavior
- [x] Task 3.3 - Map tool responses to match Python output shapes

### Phase 4: Tests, Docs, Cleanup

- [x] Task 4.1 - Replace pytest coverage with Bun tests for parser/actions
- [ ] Task 4.2 - Add parity validation checklist/runbook for local stdio checks
- [ ] Task 4.3 - Update README + Claude Code config for Bun stdio server
- [ ] Task 4.4 - Update scripts/ci.sh for Bun lint/typecheck/test
- [ ] Task 4.5 - Remove Python implementation after parity verification
- [ ] Task 4.6 - Move /ts to /src and finalize project structure

## Completed Tasks

| Task | Iteration | Notes |
|------|-----------|-------|
| Task 0.1 | 1 | Added migration spec with scope and acceptance checks |
| Task 0.2 | 2 | Documented tool inputs/outputs parity checklist |
| Task 1.2 | 3 | Added TS entrypoint, server, and tool module skeletons |
| Task 1.3 | 4 | Added Biome linting, TS typecheck scripts, and Bun test scaffold |
| Task 2.1 | 5 | Ported config/env handling with Bun tests |
| Task 2.2 | 6 | Added Bun sqlite database access layer + tests |
| Task 2.3 | 7 | Ported plist parsing + action extraction with Bun tests |
| Task 2.4 | 8 | Ported action catalog discovery with Bun tests |
| Task 2.5 | 9 | Added execution helpers and Bun tests for run_shortcut |
| Task 3.1 | 10 | Added MCP server bootstrap with stdio transport |
| Task 3.2 | 11 | Registered MCP tools with Zod input schemas |
| Task 3.3 | 12 | Implemented tool logic and mapped responses to Python shapes |
| Task 4.1 | 13 | Ported parser and actions tests to Bun with high coverage |

## Current Focus

**Next Task:** Task 4.1
**Blockers:** None

## Bugs

| ID | Priority | Description | Status |
|----|----------|-------------|--------|

## Notes

- Iteration 1: defined migration spec and task breakdown for TS/Bun stdio move
