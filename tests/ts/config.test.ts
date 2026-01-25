import os from "node:os";
import path from "node:path";
import { describe, expect, it } from "bun:test";

import {
  DEFAULT_DB_PATH,
  DEFAULT_LOG_LEVEL,
  DEFAULT_TIMEOUT_SECONDS,
  getDbPath,
  getDefaultTimeoutSeconds,
  getLogLevel,
} from "../../src/ts/config.js";

const withEnv = <T>(
  key: string,
  value: string | undefined,
  fn: () => T,
): T => {
  const previous = process.env[key];

  if (value === undefined) {
    delete process.env[key];
  } else {
    process.env[key] = value;
  }

  try {
    return fn();
  } finally {
    if (previous === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = previous;
    }
  }
};

describe("config defaults", () => {
  it("uses the expected default database path", () => {
    const expected = path.join(
      os.homedir(),
      "Library",
      "Shortcuts",
      "Shortcuts.sqlite",
    );
    expect(DEFAULT_DB_PATH).toBe(expected);
  });

  it("returns default values when env vars are not set", () => {
    const dbPath = withEnv("SHORTCUTS_DB_PATH", undefined, () => getDbPath());
    const timeout = withEnv("SHORTCUTS_DEFAULT_TIMEOUT", undefined, () =>
      getDefaultTimeoutSeconds(),
    );
    const logLevel = withEnv("SHORTCUTS_LOG_LEVEL", undefined, () =>
      getLogLevel(),
    );

    expect(dbPath).toBe(DEFAULT_DB_PATH);
    expect(timeout).toBe(DEFAULT_TIMEOUT_SECONDS);
    expect(logLevel).toBe(DEFAULT_LOG_LEVEL);
  });
});

describe("config overrides", () => {
  it("expands a tilde database path override", () => {
    const custom = withEnv("SHORTCUTS_DB_PATH", "~/Shortcuts.db", () =>
      getDbPath(),
    );
    expect(custom).toBe(path.join(os.homedir(), "Shortcuts.db"));
  });

  it("parses the timeout override", () => {
    const timeout = withEnv("SHORTCUTS_DEFAULT_TIMEOUT", "45", () =>
      getDefaultTimeoutSeconds(),
    );
    expect(timeout).toBe(45);
  });

  it("falls back on invalid timeout values", () => {
    const timeout = withEnv("SHORTCUTS_DEFAULT_TIMEOUT", "not-a-number", () =>
      getDefaultTimeoutSeconds(),
    );
    expect(timeout).toBe(DEFAULT_TIMEOUT_SECONDS);
  });

  it("reads the log level override", () => {
    const logLevel = withEnv("SHORTCUTS_LOG_LEVEL", "DEBUG", () =>
      getLogLevel(),
    );
    expect(logLevel).toBe("DEBUG");
  });
});
