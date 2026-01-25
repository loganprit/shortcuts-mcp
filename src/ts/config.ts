import os from "node:os";
import path from "node:path";

export const DEFAULT_DB_PATH = path.join(os.homedir(), "Library", "Shortcuts", "Shortcuts.sqlite");
export const DEFAULT_TIMEOUT_SECONDS = 30;
export const DEFAULT_LOG_LEVEL = "INFO";

const expandHomePath = (value: string): string => {
  if (value === "~") {
    return os.homedir();
  }

  if (value.startsWith("~/") || value.startsWith("~\\")) {
    return path.join(os.homedir(), value.slice(2));
  }

  return value;
};

export const getDbPath = (): string => {
  const rawPath = process.env.SHORTCUTS_DB_PATH ?? DEFAULT_DB_PATH;
  return expandHomePath(rawPath);
};

export const getDefaultTimeoutSeconds = (): number => {
  const rawValue = process.env.SHORTCUTS_DEFAULT_TIMEOUT ?? `${DEFAULT_TIMEOUT_SECONDS}`;
  const parsed = Number.parseInt(rawValue, 10);
  return Number.isNaN(parsed) ? DEFAULT_TIMEOUT_SECONDS : parsed;
};

export const getLogLevel = (): string => {
  return process.env.SHORTCUTS_LOG_LEVEL ?? DEFAULT_LOG_LEVEL;
};
