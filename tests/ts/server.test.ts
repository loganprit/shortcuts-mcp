import { describe, expect, it } from "bun:test";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

import { createServer, startServer } from "../../src/ts/index.js";

describe("typescript server scaffold", () => {
  it("creates an MCP server instance", () => {
    const server = createServer();
    expect(server).toBeInstanceOf(McpServer);
  });

  it("exports startServer", () => {
    expect(typeof startServer).toBe("function");
  });
});
