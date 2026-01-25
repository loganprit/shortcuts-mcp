# Tool Parity Checklist (Python Baseline)

This inventory captures the current Python FastMCP tool inputs and output
shapes. Use it as the parity reference when porting to the TypeScript SDK.

## list_shortcuts

Inputs
- folder: string | null (default: null)
- include_actions: bool (default: false)

Output
- object with key `shortcuts` -> list of ShortcutMetadata

ShortcutMetadata shape
- name: string
- id: string | null
- folder: string | null
- action_count: int | null
- last_modified: string | null
- action_types: list[string] | null

Notes
- When include_actions is false, action_types is null.

## get_shortcut

Inputs
- name: string (required)
- include_actions: bool (default: true)

Output
- ShortcutDetail object

ShortcutDetail shape
- name: string
- id: string | null
- folder: string | null
- action_count: int | null
- last_modified: string | null
- actions: list[ShortcutAction] | null
- input_types: list[string] | null

ShortcutAction shape
- identifier: string
- parameters: object (string keys -> JSON values)

Notes
- Raises ValueError "Shortcut not found: {name}" when no match.
- When include_actions is false, actions and input_types are null.

## search_shortcuts

Inputs
- query: string (required)
- search_in: "name" | "actions" | "both" (default: "name")

Output
- object with key `shortcuts` -> list of ShortcutMetadata

Notes
- When search_in includes "actions", action content is searched via
  action_search_blob and a case-insensitive substring match.

## get_folders

Inputs
- none

Output
- object with key `folders` -> list of FolderInfo-like dicts

FolderInfo-like shape
- name: string
- shortcut_count: int

Notes
- shortcut_count is always 0 (not available in current schema).

## get_available_actions

Inputs
- source: "system" | "apps" | "library" | "curated" | null (default: null)
- category: string | null (default: null)
- search: string | null (default: null)
- include_parameters: bool (default: true)
- include_examples: bool (default: false)
- force_refresh: bool (default: false)

Output
- object with keys:
  - actions: list[ActionInfo]
  - categories: list[string]
  - sources: object (system/apps/library/curated -> int counts)
  - cached: bool

ActionInfo shape
- identifier: string
- source: "system" | "apps" | "library" | "curated"
- title: string | null
- description: string | null
- category: string
- parameters: list[ActionParameter]
- platform_availability: object | null (string -> string)
- usage_count: int
- example_params: object | null (string -> JSON values)

ActionParameter shape
- name: string
- title: string | null
- value_type: string
- is_optional: bool
- description: string | null

Notes
- When include_parameters is false, parameters is an empty list.
- When include_examples is false, example_params is null.

## run_shortcut

Inputs
- name: string (required)
- input: JSON value | null (default: null)
- wait_for_result: bool (default: true)
- timeout: int | null (default: null; uses SHORTCUTS_DEFAULT_TIMEOUT when null)

Output
- RunResult object

RunResult shape
- success: bool
- output: string | null
- execution_time_ms: int | null

Behavior notes
- wait_for_result = true: uses AppleScript execution and returns output and
  execution_time_ms. Non-zero returncode => success false.
- wait_for_result = false: uses URL scheme, returns success true on launch and
  omits output/execution_time_ms.
- Timeout (wait_for_result=true) => success false, output "Timeout waiting for shortcut".
- Exceptions are caught and returned as success false with output = str(error).
