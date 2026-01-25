import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import {
  getAvailableActions,
  getFolders,
  getShortcut,
  listShortcuts,
  runShortcut,
  searchShortcuts,
} from "./tools/index.js";

export type ToolHandler = () => Promise<unknown>;

const TOOL_HANDLERS: Record<string, ToolHandler> = {
  list_shortcuts: listShortcuts,
  get_shortcut: getShortcut,
  search_shortcuts: searchShortcuts,
  get_folders: getFolders,
  get_available_actions: getAvailableActions,
  run_shortcut: runShortcut,
};

const SERVER_NAME = "Shortcuts MCP";
const SERVER_VERSION = "0.0.0";

export const createServer = (): McpServer => {
  void TOOL_HANDLERS;
  return new McpServer({ name: SERVER_NAME, version: SERVER_VERSION });
};

export const startServer = async (): Promise<McpServer> => {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  return server;
};
