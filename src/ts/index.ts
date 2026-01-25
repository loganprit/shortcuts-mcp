// Bun entrypoint for the MCP server (stdio transport).
import { startServer } from "./server.js";

export { createServer, startServer } from "./server.js";

if (import.meta.main) {
  void startServer();
}
