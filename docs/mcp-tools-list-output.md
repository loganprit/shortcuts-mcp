# MCP `tools/list` Output (Shortcuts MCP)

Date of capture: 2026-01-25
Method: local JSON-RPC over stdio (initialize + tools/list)
Server reported version: 1.25.0
Protocol version: 2025-11-25

## Capture Method (High Level)
1) Start server (`uv run shortcuts-mcp`).
2) Send JSON-RPC `initialize` with protocol version `2025-11-25`.
3) Send JSON-RPC `tools/list` with empty params.
4) Capture JSON response and store verbatim below.

## `initialize` Response (verbatim)
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2025-11-25",
    "capabilities": {
      "experimental": {},
      "prompts": {
        "listChanged": false
      },
      "resources": {
        "subscribe": false,
        "listChanged": false
      },
      "tools": {
        "listChanged": false
      }
    },
    "serverInfo": {
      "name": "Shortcuts MCP",
      "version": "1.25.0"
    }
  }
}
```

## `tools/list` Response (verbatim)
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "list_shortcuts",
        "description": "List all available macOS shortcuts.",
        "inputSchema": {
          "properties": {
            "folder": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Folder"
            },
            "include_actions": {
              "default": false,
              "title": "Include Actions",
              "type": "boolean"
            }
          },
          "title": "list_shortcutsArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array"
          },
          "title": "list_shortcutsDictOutput",
          "type": "object"
        }
      },
      {
        "name": "get_shortcut",
        "description": "Get detailed information about a specific shortcut.",
        "inputSchema": {
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "include_actions": {
              "default": true,
              "title": "Include Actions",
              "type": "boolean"
            }
          },
          "required": [
            "name"
          ],
          "title": "get_shortcutArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": true,
          "title": "get_shortcutDictOutput",
          "type": "object"
        }
      },
      {
        "name": "run_shortcut",
        "description": "Execute a shortcut with optional input.\n\nThe input parameter accepts any JSON-serializable value (str, int, float,\nbool, None, list, or dict). We use 'object' here because Pydantic's schema\ngeneration cannot handle the recursive JsonValue TypeAlias.\n",
        "inputSchema": {
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "input": {
              "default": null,
              "title": "Input"
            },
            "wait_for_result": {
              "default": true,
              "title": "Wait For Result",
              "type": "boolean"
            },
            "timeout": {
              "anyOf": [
                {
                  "type": "integer"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Timeout"
            }
          },
          "required": [
            "name"
          ],
          "title": "run_shortcutArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": true,
          "title": "run_shortcutDictOutput",
          "type": "object"
        }
      },
      {
        "name": "search_shortcuts",
        "description": "Search shortcuts by name or action content.",
        "inputSchema": {
          "properties": {
            "query": {
              "title": "Query",
              "type": "string"
            },
            "search_in": {
              "default": "name",
              "enum": [
                "name",
                "actions",
                "both"
              ],
              "title": "Search In",
              "type": "string"
            }
          },
          "required": [
            "query"
          ],
          "title": "search_shortcutsArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": {
            "items": {
              "additionalProperties": true,
              "type": "object"
            },
            "type": "array"
          },
          "title": "search_shortcutsDictOutput",
          "type": "object"
        }
      },
      {
        "name": "get_available_actions",
        "description": "Get all available Shortcuts actions from system and installed apps.\n\nArgs:\n    source: Filter by source - \"system\" (Apple frameworks), \"apps\" (third-party),\n        \"library\" (from user's shortcuts), \"curated\" (classic is.workflow.actions.*)\n    category: Filter by action category/prefix\n        (e.g., \"is.workflow.actions\", \"com.apple\")\n    search: Search query to filter by identifier, title, or description\n    include_parameters: Include parameter definitions (default: True)\n    include_examples: Include example parameters from user's library\n        (default: False)\n    force_refresh: Bypass cache and rescan all sources (default: False)\n\nReturns:\n    Dictionary with:\n    - actions: List of ActionInfo objects\n    - categories: List of unique category prefixes found\n    - sources: Count of actions per source\n    - cached: Whether results came from cache\n",
        "inputSchema": {
          "properties": {
            "source": {
              "anyOf": [
                {
                  "enum": [
                    "system",
                    "apps",
                    "library",
                    "curated"
                  ],
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Source"
            },
            "category": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Category"
            },
            "search": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Search"
            },
            "include_parameters": {
              "default": true,
              "title": "Include Parameters",
              "type": "boolean"
            },
            "include_examples": {
              "default": false,
              "title": "Include Examples",
              "type": "boolean"
            },
            "force_refresh": {
              "default": false,
              "title": "Force Refresh",
              "type": "boolean"
            }
          },
          "title": "get_available_actionsArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": true,
          "title": "get_available_actionsDictOutput",
          "type": "object"
        }
      },
      {
        "name": "create_shortcut",
        "description": "Create and import a new shortcut from provided actions.",
        "inputSchema": {
          "$defs": {
            "ShortcutAction": {
              "properties": {
                "identifier": {
                  "title": "Identifier",
                  "type": "string"
                },
                "parameters": {
                  "additionalProperties": true,
                  "title": "Parameters",
                  "type": "object"
                }
              },
              "required": [
                "identifier"
              ],
              "title": "ShortcutAction",
              "type": "object"
            },
            "ShortcutIcon": {
              "properties": {
                "glyph_number": {
                  "title": "Glyph Number",
                  "type": "integer"
                },
                "color": {
                  "enum": [
                    "red",
                    "dark_orange",
                    "orange",
                    "yellow",
                    "green",
                    "teal",
                    "light_blue",
                    "blue",
                    "dark_blue",
                    "violet",
                    "purple",
                    "dark_gray",
                    "pink",
                    "taupe",
                    "gray"
                  ],
                  "title": "Color",
                  "type": "string"
                }
              },
              "required": [
                "glyph_number",
                "color"
              ],
              "title": "ShortcutIcon",
              "type": "object"
            }
          },
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "actions": {
              "items": {
                "$ref": "#/$defs/ShortcutAction"
              },
              "title": "Actions",
              "type": "array"
            },
            "input_types": {
              "anyOf": [
                {
                  "items": {
                    "type": "string"
                  },
                  "type": "array"
                },
                {
                  "type": "null"
                }
              ],
              "default": null,
              "title": "Input Types"
            },
            "icon": {
              "anyOf": [
                {
                  "$ref": "#/$defs/ShortcutIcon"
                },
                {
                  "type": "null"
                }
              ],
              "default": null
            },
            "validate": {
              "default": true,
              "title": "Validate",
              "type": "boolean"
            },
            "install": {
              "default": true,
              "title": "Install",
              "type": "boolean"
            },
            "sign_mode": {
              "default": "anyone",
              "enum": [
                "anyone",
                "people-who-know-me"
              ],
              "title": "Sign Mode",
              "type": "string"
            },
            "if_exists": {
              "default": "error",
              "enum": [
                "error",
                "rename",
                "replace"
              ],
              "title": "If Exists",
              "type": "string"
            },
            "wait_for_import": {
              "default": true,
              "title": "Wait For Import",
              "type": "boolean"
            },
            "wait_timeout_s": {
              "default": 10,
              "title": "Wait Timeout S",
              "type": "integer"
            }
          },
          "required": [
            "name",
            "actions"
          ],
          "title": "create_shortcutArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": true,
          "title": "create_shortcutDictOutput",
          "type": "object"
        }
      },
      {
        "name": "get_folders",
        "description": "List shortcut folders/collections.",
        "inputSchema": {
          "properties": {},
          "title": "get_foldersArguments",
          "type": "object"
        },
        "outputSchema": {
          "additionalProperties": {
            "items": {
              "additionalProperties": {
                "anyOf": [
                  {
                    "type": "string"
                  },
                  {
                    "type": "integer"
                  }
                ]
              },
              "type": "object"
            },
            "type": "array"
          },
          "title": "get_foldersDictOutput",
          "type": "object"
        }
      }
    ]
  }
}
```

## Spec Comparison Notes
- `tools` capability is present in initialize response (`listChanged: false`), matching spec requirements.
- Each tool includes `name`, `description`, and `inputSchema` as required by the spec.
- `outputSchema` is present for all tools, which is optional but valid.
- `inputSchema` values are valid JSON Schema objects.
- No `$schema` is provided, so JSON Schema 2020-12 applies (per spec).

## Shortcut Creation Schema Details (From `tools/list`)

From `create_shortcut.inputSchema`:
- Required: `name` (string), `actions` (array of `ShortcutAction`).
- `actions[]` requires `identifier` (string); `parameters` is open object.
- `input_types`: array of strings or null.
- `icon`: object or null. `icon` requires **both** `glyph_number` (int) and `color` (enum).
- `sign_mode` enum: `anyone`, `people-who-know-me`.
- `if_exists` enum: `error`, `rename`, `replace`.
- `wait_for_import` default `true`, `wait_timeout_s` default `10`.

