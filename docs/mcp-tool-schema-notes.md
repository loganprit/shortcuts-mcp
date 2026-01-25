# MCP Tool Schema Expectations (Spec Notes)

Date of research: 2026-01-25
Scope: What MCP servers should expose so clients can build *correct* tool calls

This document summarizes the *expected* MCP tool structure from the official MCP specification (2025-06-18) and draft extensions. It focuses on the canonical mechanism for tool calling structure: `tools/list` + `inputSchema` JSON Schema.

## 1) Capability declaration for tools

Servers that support tools MUST declare the `tools` capability during initialization. The capability can optionally include `listChanged`, which indicates the server will emit notifications when the tool list changes.

Example:
```
{
  "capabilities": {
    "tools": {
      "listChanged": true
    }
  }
}
```

## 2) Tool discovery: `tools/list`

### Request
- `tools/list` is a JSON-RPC request.
- Supports pagination via optional `cursor` parameter.

Example request:
```
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list",
  "params": {
    "cursor": "optional-cursor-value"
  }
}
```

### Response
The response returns a `tools` array and may include `nextCursor` for pagination.

Example response (shape):
```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "title": "Weather Information Provider",
        "description": "Get current weather information for a location",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": { "type": "string" }
          },
          "required": ["location"]
        }
      }
    ],
    "nextCursor": "next-page-cursor"
  }
}
```

## 3) Tool definition structure (core fields)

Each tool definition can include:
- `name` (required): unique identifier for the tool.
- `title` (optional): display-friendly name.
- `description` (recommended): human-readable description of functionality.
- `inputSchema` (required): JSON Schema describing expected arguments.
- `outputSchema` (optional): JSON Schema describing structured output.
- `annotations` (optional): hints about tool behavior (read-only, destructive, idempotent).
- `icons` (optional, in newer drafts): UI icons.

## 4) Tool name constraints (recommended)

The draft spec recommends tool names:
- Length between 1 and 128 characters (inclusive).
- Case-sensitive.
- Only ASCII letters, digits, underscore (`_`), hyphen (`-`), and dot (`.`).
- No spaces or special characters.
- Unique within a server.

## 5) JSON Schema requirements for `inputSchema` / `outputSchema`

MCP uses JSON Schema for validation across the protocol. Key rules:
- If `$schema` is omitted, the default dialect is JSON Schema 2020-12.
- Implementations MUST support 2020-12 for schemas without an explicit `$schema`.
- Schemas MUST be valid according to their declared or default dialect.

### No-parameter tools
If a tool accepts no parameters, `inputSchema` must still be a valid schema object (not `null`). The draft spec recommends:
- `{ "type": "object", "additionalProperties": false }` (recommended: only empty objects)
- `{ "type": "object" }` (accepts any object)

## 6) Tool invocation: `tools/call`

Clients must call tools using the `name` and pass `arguments` that conform to `inputSchema`. This is the canonical *expected tool calling structure*.

## 7) Tool results and output schema

Tool results can contain:
- **Unstructured content** via `content` (text, image, audio, resource links, embedded resources).
- **Structured content** via `structuredContent`.

If `outputSchema` is provided:
- Servers MUST return `structuredContent` that conforms to it.
- Clients SHOULD validate `structuredContent` against the schema.
- For backward compatibility, structured content SHOULD also be serialized into a TextContent block.

## 8) Why this matters for tool-call correctness

From the MCP spec perspective, the correct tool call shape is determined entirely by:
- Tool `name` (from `tools/list`).
- `inputSchema` (from `tools/list`).

Therefore, clients should always read and follow `inputSchema` to avoid malformed calls.

## Sources

Primary:
- MCP Spec (2025-06-18) Tools: https://modelcontextprotocol.io/specification/2025-06-18/server/tools
- MCP Spec (2025-11-25) JSON Schema Usage: https://modelcontextprotocol.io/specification/2025-11-25/basic

Draft / extensions:
- MCP Spec (draft) Tools: https://modelcontextprotocol.io/specification/draft/server/tools

