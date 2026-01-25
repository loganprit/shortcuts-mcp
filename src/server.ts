import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import {
  INPUT_SCHEMA as GET_AVAILABLE_ACTIONS_INPUT_SCHEMA,
  TOOL_NAME as GET_AVAILABLE_ACTIONS_NAME,
  getAvailableActions,
} from "./tools/get_available_actions.js";
import {
  INPUT_SCHEMA as GET_FOLDERS_INPUT_SCHEMA,
  TOOL_NAME as GET_FOLDERS_NAME,
  getFolders,
} from "./tools/get_folders.js";
import {
  INPUT_SCHEMA as GET_SHORTCUT_INPUT_SCHEMA,
  TOOL_NAME as GET_SHORTCUT_NAME,
  getShortcut,
} from "./tools/get_shortcut.js";
import {
  INPUT_SCHEMA as LIST_SHORTCUTS_INPUT_SCHEMA,
  TOOL_NAME as LIST_SHORTCUTS_NAME,
  listShortcuts,
} from "./tools/list_shortcuts.js";
import {
  INPUT_SCHEMA as RUN_SHORTCUT_INPUT_SCHEMA,
  TOOL_NAME as RUN_SHORTCUT_NAME,
  runShortcut,
} from "./tools/run_shortcut.js";
import {
  INPUT_SCHEMA as SEARCH_SHORTCUTS_INPUT_SCHEMA,
  TOOL_NAME as SEARCH_SHORTCUTS_NAME,
  searchShortcuts,
} from "./tools/search_shortcuts.js";

const SERVER_NAME = "Shortcuts MCP";
const SERVER_VERSION = "0.0.0";

export const createServer = (): McpServer => {
  const server = new McpServer({ name: SERVER_NAME, version: SERVER_VERSION });

  server.tool(LIST_SHORTCUTS_NAME, LIST_SHORTCUTS_INPUT_SCHEMA, listShortcuts);
  server.tool(GET_SHORTCUT_NAME, GET_SHORTCUT_INPUT_SCHEMA, getShortcut);
  server.tool(SEARCH_SHORTCUTS_NAME, SEARCH_SHORTCUTS_INPUT_SCHEMA, searchShortcuts);
  server.tool(GET_FOLDERS_NAME, GET_FOLDERS_INPUT_SCHEMA, getFolders);
  server.tool(GET_AVAILABLE_ACTIONS_NAME, GET_AVAILABLE_ACTIONS_INPUT_SCHEMA, getAvailableActions);
  server.tool(RUN_SHORTCUT_NAME, RUN_SHORTCUT_INPUT_SCHEMA, runShortcut);

  return server;
};

export const startServer = async (): Promise<McpServer> => {
  const server = createServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  return server;
};
