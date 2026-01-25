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

export const createServer = (): void => {
  void TOOL_HANDLERS;
  // TODO: Implement MCP server wiring in Task 3.1.
};
