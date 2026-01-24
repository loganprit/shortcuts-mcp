# PRD: get-available-actions Tool

## Overview

Add a new MCP tool `get_available_actions` that discovers and catalogs all Shortcuts actions available on the system, including Apple system actions, third-party app actions, and classic Shortcuts actions. This enables programmatic shortcut creation by providing a complete registry of usable actions with their parameters and metadata.

## Problem Statement

Currently, the shortcuts-mcp server can list shortcuts and extract actions from existing shortcuts, but there's no way to discover **all available actions** that could be used to build new shortcuts. Users building shortcuts programmatically need to know:
1. What actions exist
2. What parameters each action accepts
3. How those parameters should be structured

## Goals

1. **Discovery**: Enumerate all available Shortcuts actions from system and installed apps
2. **Documentation**: Provide rich metadata including descriptions, parameters, and platform availability
3. **Examples**: Include real usage examples from the user's shortcuts library
4. **Usability**: Support filtering and grouping for manageable result sets
5. **Performance**: Cache results to avoid repeated filesystem/binary parsing

## Non-Goals (v1)

1. Creating/building shortcuts (future `build_shortcut` tool)
2. Real-time action monitoring (watching for new app installs)
3. Fetching external action catalogs from the internet
4. Providing localized action names/descriptions

## Data Sources

### 1. System AppIntents (Primary)
**Location**: `/System/Library/PrivateFrameworks/*/Metadata.appintents/extract.actionsdata`

Modern AppIntents actions from Apple frameworks. ~34 framework bundles containing ~252+ actions.

**Format**: JSON with structure:
```json
{
  "actions": {
    "ActionName": {
      "identifier": "ActionName",
      "fullyQualifiedTypeName": "FrameworkName.ActionName",
      "title": {"key": "Display Name", "table": "AppIntents"},
      "descriptionMetadata": {
        "descriptionText": {"key": "Description...", "table": "AppIntents"},
        "searchKeywords": []
      },
      "parameters": [
        {
          "name": "paramName",
          "title": {"key": "Parameter Title"},
          "valueType": {...},
          "isOptional": false
        }
      ],
      "availabilityAnnotations": {
        "LNPlatformNameMACOS": {"introducedVersion": "14.0"}
      },
      "requiredCapabilities": []
    }
  }
}
```

### 2. Third-Party App Actions
**Location**: `/Applications/*/Resources/Metadata.appintents/extract.actionsdata`

Same JSON format as system actions. ~33+ apps with actions on typical installs.

### 3. Classic Shortcuts Actions (Curated)
**Identifier Pattern**: `is.workflow.actions.*`

These are the original Workflow/Shortcuts actions. No formal catalog exists on disk. We'll include a curated list of common actions with basic metadata.

**Source for curation**: Extract unique identifiers from user's shortcuts library + reference community documentation.

### 4. User Library Actions (Discovery)
**Source**: Parse all shortcuts in `~/Library/Shortcuts/Shortcuts.sqlite`

Extract unique action identifiers and their parameter patterns from actual usage. Useful for discovering app-specific intents (e.g., `com.openai.chat.OpenNewChatInAppShortcutIntent`).

## Technical Design

### New Module: `actions.py`

```python
# src/shortcuts_mcp/actions.py

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ActionSource = Literal["system", "apps", "library", "curated"]

@dataclass
class ActionParameter:
    name: str
    title: str | None
    value_type: str  # e.g., "string", "boolean", "entity:TypeName"
    is_optional: bool
    description: str | None = None

@dataclass
class ActionInfo:
    identifier: str
    source: ActionSource
    title: str | None
    description: str | None
    category: str  # Derived from identifier prefix or framework
    parameters: list[ActionParameter]
    platform_availability: dict[str, str] | None  # {platform: version}
    usage_count: int = 0  # From user library
    example_params: dict[str, object] | None = None  # From user library

class ActionCatalog:
    """Manages action discovery and caching."""

    _cache: dict[str, ActionInfo] | None = None
    _cache_time: float = 0

    async def get_all_actions(
        self,
        source: ActionSource | None = None,
        category: str | None = None,
        search: str | None = None,
        force_refresh: bool = False,
    ) -> list[ActionInfo]:
        ...

    async def _scan_system_actions(self) -> list[ActionInfo]:
        """Parse all extract.actionsdata from PrivateFrameworks."""
        ...

    async def _scan_app_actions(self) -> list[ActionInfo]:
        """Parse all extract.actionsdata from /Applications."""
        ...

    async def _scan_library_actions(self) -> list[ActionInfo]:
        """Extract unique actions from user's shortcuts."""
        ...

    def _get_curated_actions(self) -> list[ActionInfo]:
        """Return curated list of is.workflow.actions.* with metadata."""
        ...
```

### New Models: `models.py` additions

```python
class ActionParameter(BaseModel):
    name: str
    title: str | None = None
    value_type: str
    is_optional: bool = False
    description: str | None = None

class ActionInfo(BaseModel):
    identifier: str
    source: Literal["system", "apps", "library", "curated"]
    title: str | None = None
    description: str | None = None
    category: str
    parameters: list[ActionParameter] = Field(default_factory=list)
    platform_availability: dict[str, str] | None = None
    usage_count: int = 0
    example_params: dict[str, object] | None = None
```

### New Tool: `server.py` addition

```python
@mcp.tool()
async def get_available_actions(
    source: ActionSource | None = None,
    category: str | None = None,
    search: str | None = None,
    include_parameters: bool = True,
    include_examples: bool = False,
    force_refresh: bool = False,
) -> dict[str, object]:
    """Get all available Shortcuts actions from system and installed apps.

    Args:
        source: Filter by source - "system" (Apple frameworks), "apps" (third-party),
                "library" (from user's shortcuts), "curated" (classic is.workflow.actions.*)
        category: Filter by action category/prefix (e.g., "is.workflow.actions", "com.apple")
        search: Search query to filter by identifier, title, or description
        include_parameters: Include parameter definitions (default: True)
        include_examples: Include example parameters from user's library (default: False)
        force_refresh: Bypass cache and rescan all sources (default: False)

    Returns:
        Dictionary with:
        - actions: List of ActionInfo objects
        - categories: List of unique category prefixes found
        - sources: Count of actions per source
        - cached: Whether results came from cache
    """
```

### Curated Actions File

Create `src/shortcuts_mcp/data/curated_actions.json` containing common `is.workflow.actions.*`:

```json
{
  "is.workflow.actions.gettext": {
    "title": "Text",
    "description": "Passes the specified text to the next action.",
    "parameters": [
      {"name": "WFTextActionText", "title": "Text", "value_type": "string", "is_optional": false}
    ]
  },
  "is.workflow.actions.delay": {
    "title": "Wait",
    "description": "Waits for the specified number of seconds before continuing.",
    "parameters": [
      {"name": "WFDelayTime", "title": "Delay", "value_type": "number", "is_optional": false}
    ]
  }
  // ... more actions
}
```

## Categories

Actions will be categorized by identifier prefix:

| Category | Pattern | Description |
|----------|---------|-------------|
| `workflow` | `is.workflow.actions.*` | Classic Shortcuts actions |
| `apple.shortcuts` | `com.apple.ShortcutsActions.*` | Apple Shortcuts app actions |
| `apple.system` | `com.apple.*` (other) | Apple system app actions |
| `third-party` | Other bundle identifiers | Third-party app actions |

## Response Format

```json
{
  "actions": [
    {
      "identifier": "is.workflow.actions.gettext",
      "source": "curated",
      "title": "Text",
      "description": "Passes the specified text to the next action.",
      "category": "workflow",
      "parameters": [
        {
          "name": "WFTextActionText",
          "title": "Text",
          "value_type": "string",
          "is_optional": false
        }
      ],
      "usage_count": 15,
      "example_params": {
        "WFTextActionText": "Hello, World!"
      }
    }
  ],
  "categories": ["workflow", "apple.shortcuts", "apple.system", "third-party"],
  "sources": {
    "system": 252,
    "apps": 87,
    "library": 45,
    "curated": 120
  },
  "cached": true
}
```

## Implementation Plan

### Phase 1: Core Infrastructure
1. Create `actions.py` module with `ActionCatalog` class
2. Implement `_scan_system_actions()` to parse framework actionsdata files
3. Implement `_scan_app_actions()` to parse application actionsdata files
4. Add Pydantic models for ActionInfo and ActionParameter
5. Add basic caching mechanism

### Phase 2: Library Integration
1. Implement `_scan_library_actions()` to extract from user's shortcuts
2. Merge usage counts and example parameters into catalog
3. Handle action identifier normalization/deduplication

### Phase 3: Curated Actions
1. Create `curated_actions.json` with common is.workflow.actions.*
2. Implement `_get_curated_actions()` loader
3. Research and document ~50-100 most common classic actions

### Phase 4: Tool & API
1. Add `get_available_actions` tool to server.py
2. Implement filtering by source, category, search
3. Add force_refresh parameter for cache bypass
4. Write comprehensive docstrings for MCP schema

### Phase 5: Testing & Polish
1. Add unit tests for actionsdata parsing
2. Add integration tests for full catalog generation
3. Performance testing with large app installations
4. Documentation updates

## Testing Strategy

1. **Unit Tests**
   - Parse sample actionsdata JSON
   - Category derivation from identifiers
   - Parameter type normalization
   - Cache invalidation logic

2. **Integration Tests**
   - Full system scan (mocked filesystem)
   - Library action extraction
   - Filter/search functionality

3. **Manual Testing**
   - Verify action counts match expectations
   - Test with various installed apps
   - Performance with large result sets

## Success Metrics

1. Successfully catalogs 300+ actions from system + apps
2. Response time < 2s for cached results
3. Response time < 10s for full rescan
4. All existing tests continue to pass
5. Type checking passes in strict mode

## Open Questions

1. **Cache persistence**: Should cache persist across server restarts (file-based) or be memory-only?
   - **Proposed**: Memory-only initially, file-based as future enhancement

2. **Curated action list maintenance**: How to keep is.workflow.actions.* list updated?
   - **Proposed**: Start with ~100 most common, expand based on user feedback

3. **Localization**: Should we attempt to extract localized titles/descriptions?
   - **Proposed**: English-only for v1, localization as future enhancement

## Future Enhancements

1. **External catalogs**: Fetch/merge community action catalogs
2. **build_shortcut tool**: Create new shortcuts using discovered actions
3. **Action validation**: Validate action/parameter combinations before building
4. **Watch mode**: Monitor for newly installed apps with actions
5. **Export catalog**: Export full catalog as JSON for external tools
