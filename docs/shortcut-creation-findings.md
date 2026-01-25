# Shortcut Creation Tool Findings (Black-Box)

Date of testing: 2026-01-25
Environment: macOS Shortcuts MCP server (accessed via tool interface only; no code inspection)

## Scope
I tested the shortcut creation tool as a black box using only the server’s exposed API. I did not read server code. The goal was to record observed behavior, validation constraints, response shapes, and import confirmation behavior, including icon/color handling.

## Tool Calls and Observations (Chronological)

### 1) Baseline create with invalid `input_types`
Request:
- `name`: `Codex Test Shortcut`
- `actions`: `[]`
- `input_types`: `"text"` (string)
- `install`: `false`
- `wait_for_import`: `false`

Result:
- Tool returned a validation error.
- Error message (paraphrased): `input_types` must be a list; string rejected.
- Conclusion: `input_types` must be a list type, not a single string.

### 2) Baseline create with valid `input_types`
Request:
- `name`: `Codex Test Shortcut`
- `actions`: `[]`
- `input_types`: `["text"]`
- `install`: `false`
- `wait_for_import`: `false`

Result:
- `success: true`
- `file_path`: temp `.shortcut` file created under `/var/folders/.../shortcuts-mcp-.../`
- `import_attempted: false`
- `import_confirmed: null`
- `imported_name: null`
- `warnings: []`

Observations:
- Empty `actions` list is accepted.
- Shortcut file is created even when not installing.

### 3) Create with install enabled, without waiting
Request:
- `name`: `Codex Test Shortcut 2`
- `actions`: `[]`
- `input_types`: `["text"]`
- `install`: `true`
- `wait_for_import`: `false`

Result:
- `success: true`
- `import_attempted: true`
- `import_confirmed: null`
- `imported_name: null`

Observations:
- With `wait_for_import: false`, tool does not confirm import success.

### 4) Create with install enabled, waiting for import
Request:
- `name`: `Codex Test Shortcut 3`
- `actions`: `[]`
- `input_types`: `["text"]`
- `install`: `true`
- `wait_for_import`: `true`
- `wait_timeout_s`: `5`

Result:
- `success: true`
- `import_attempted: true`
- `import_confirmed: true`
- `imported_name`: `Codex Test Shortcut 3`

Observations:
- When waiting is enabled and completes within timeout, tool confirms import and provides `imported_name`.

### 5) Confirmed creation via list
I listed shortcuts after the above steps and saw:
- `Codex Test Shortcut 2` present, `action_count: 0`
- `Codex Test Shortcut 3` present, `action_count: 0`
- `last_modified` timestamps matched creation time (2026-01-25, UTC)

## Icon/Color Behavior Testing
User note: The shortcut’s color is encoded in the icon color parameter (even if that is not intuitive). I tested icon inputs based on this.

### 6) Icon with string input
Request:
- `name`: `Codex Icon Test A`
- `actions`: `[]`
- `input_types`: `["text"]`
- `icon`: `"blue"`
- `install`: `true`
- `wait_for_import`: `true`

Result:
- Validation error.
- Error message (paraphrased): `icon` must be a dict or `ShortcutIcon` model.

Observation:
- `icon` must be an object/dict, not a string.

### 7) Icon dict with color only
Request:
- `name`: `Codex Icon Test B`
- `actions`: `[]`
- `input_types`: `["text"]`
- `icon`: `{ "color": "blue" }`
- `install`: `true`
- `wait_for_import`: `true`

Result:
- Validation error.
- Error message (paraphrased): `icon.glyph_number` is required.

Observation:
- The server requires `glyph_number` when `icon` is provided.

### 8) Icon dict with color + glyph
Request:
- `name`: `Codex Icon Test C`
- `actions`: `[]`
- `input_types`: `["text"]`
- `icon`: `{ "color": "blue", "glyph_number": 1 }`
- `install`: `true`
- `wait_for_import`: `true`
- `wait_timeout_s`: `5`

Result:
- `success: true`
- `import_attempted: true`
- `import_confirmed: false`
- `warnings`: `Import not confirmed yet. Shortcuts may still be prompting.`

Observation:
- Even with wait enabled, the server can return `import_confirmed: false` and a warning.
- The shortcut appears in `list_shortcuts`, but icon metadata is not returned there or by `get_shortcut`.

### 9) Additional icon tests with varying glyph numbers
All used `install: true`, `wait_for_import: true`, `wait_timeout_s: 5`.

- `Codex Icon Test D`: `icon: { color: red, glyph_number: 1 }`
- `Codex Icon Test E`: `icon: { color: green, glyph_number: 50 }`
- `Codex Icon Test F`: `icon: { color: blue, glyph_number: 200 }`
- `Codex Icon Test G`: `icon: { color: yellow, glyph_number: 999 }`

Results:
- All returned `success: true`, `import_confirmed: true`, and `imported_name` matching shortcut name.

User verification in Shortcuts app:
- All colors applied correctly.
- No glyphs appeared for any of these shortcuts.

## Summary of Behavioral Findings

### Validation
- `input_types` must be a list (string is rejected).
- `icon` must be an object/dict (string is rejected).
- `icon.glyph_number` is required when `icon` is provided.

### Import Behavior
- When `install: false`, only a `.shortcut` file is produced in a temp directory.
- When `install: true`:
  - `wait_for_import: false` -> no import confirmation is provided.
  - `wait_for_import: true` -> sometimes confirms import; sometimes returns not confirmed + warning.

### Icon/Color
- `icon.color` does control shortcut color in the Shortcuts app.
- `icon.glyph_number` is accepted by the API but does not appear to affect the icon glyph in the app.
- `list_shortcuts` and `get_shortcut` do not surface icon metadata, so confirmation relies on visual inspection in the app.

## Raw Shortcut Names Created During Testing
- `Codex Test Shortcut`
- `Codex Test Shortcut 2`
- `Codex Test Shortcut 3`
- `Codex Icon Test A` (failed validation, not created)
- `Codex Icon Test B` (failed validation, not created)
- `Codex Icon Test C`
- `Codex Icon Test D`
- `Codex Icon Test E`
- `Codex Icon Test F`
- `Codex Icon Test G`

## Follow-Up Ideas (Implementation Targets)
- Improve validation messages for `input_types` and `icon` to provide example payloads.
- If `install: true`, always provide a definitive import status or a follow-up action hint.
- Consider making `glyph_number` optional if the platform ignores it, or document known limitations.
- Expose icon metadata in `get_shortcut` or a dedicated endpoint if possible.
