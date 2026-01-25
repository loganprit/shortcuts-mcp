import os from "node:os";
import path from "node:path";
import { mkdtemp, rm } from "node:fs/promises";
import { Database } from "bun:sqlite";
import { describe, expect, it } from "bun:test";

import {
  getAllShortcuts,
  getFolders,
  getShortcutActions,
  getShortcutByName,
  searchShortcutsByName,
} from "../../src/ts/database.js";

const withEnv = async <T>(
  key: string,
  value: string | undefined,
  fn: () => Promise<T>,
): Promise<T> => {
  const previous = process.env[key];

  if (value === undefined) {
    delete process.env[key];
  } else {
    process.env[key] = value;
  }

  try {
    return await fn();
  } finally {
    if (previous === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = previous;
    }
  }
};

const setupDatabase = async (): Promise<{
  dbPath: string;
  cleanup: () => Promise<void>;
}> => {
  const dir = await mkdtemp(path.join(os.tmpdir(), "shortcuts-mcp-"));
  const dbPath = path.join(dir, "Shortcuts.sqlite");
  const db = new Database(dbPath);

  try {
    db.run(`
      CREATE TABLE ZSHORTCUT (
        Z_PK INTEGER PRIMARY KEY,
        ZNAME TEXT,
        ZACTIONCOUNT INTEGER,
        ZMODIFICATIONDATE REAL,
        ZWORKFLOWID BLOB
      );
    `);
    db.run(`
      CREATE TABLE ZSHORTCUTACTIONS (
        ZSHORTCUT INTEGER,
        ZDATA BLOB
      );
    `);
    db.run(`
      CREATE TABLE ZCOLLECTION (
        ZIDENTIFIER TEXT,
        ZTEMPORARYSYNCFOLDERNAME TEXT
      );
    `);

    const uuidBytes = Buffer.from(
      "00112233445566778899aabbccddeeff",
      "hex",
    );

    db.run(
      `
        INSERT INTO ZSHORTCUT
          (Z_PK, ZNAME, ZACTIONCOUNT, ZMODIFICATIONDATE, ZWORKFLOWID)
        VALUES
          (1, 'Alpha', 4, 0, ?),
          (2, 'beta', 2, 86400, NULL)
      `,
      [uuidBytes],
    );

    db.run(
      `
        INSERT INTO ZSHORTCUTACTIONS (ZSHORTCUT, ZDATA)
        VALUES (1, ?)
      `,
      [new Uint8Array([1, 2, 3])],
    );

    db.run(
      `
        INSERT INTO ZCOLLECTION (ZIDENTIFIER, ZTEMPORARYSYNCFOLDERNAME)
        VALUES ('Root', NULL), ('ShareSheet', 'Share Sheet')
      `,
    );
  } finally {
    db.close();
  }

  return {
    dbPath,
    cleanup: async () => {
      await rm(dir, { recursive: true, force: true });
    },
  };
};

describe("database access", () => {
  it("loads shortcuts with normalized metadata", async () => {
    const { dbPath, cleanup } = await setupDatabase();

    try {
      const shortcuts = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getAllShortcuts(),
      );

      expect(shortcuts).toHaveLength(2);
      expect(shortcuts[0]?.name).toBe("Alpha");
      expect(shortcuts[1]?.name).toBe("beta");
      expect(shortcuts[0]?.modifiedAt).toBe("2001-01-01T00:00:00+00:00");
      expect(shortcuts[1]?.modifiedAt).toBe("2001-01-02T00:00:00+00:00");
      expect(shortcuts[0]?.workflowId).toBe(
        "00112233-4455-6677-8899-aabbccddeeff",
      );
      expect(shortcuts[1]?.workflowId).toBeNull();
    } finally {
      await cleanup();
    }
  });

  it("returns a shortcut by name", async () => {
    const { dbPath, cleanup } = await setupDatabase();

    try {
      const shortcut = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getShortcutByName("beta"),
      );
      expect(shortcut?.actionCount).toBe(2);

      const missing = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getShortcutByName("does-not-exist"),
      );
      expect(missing).toBeNull();
    } finally {
      await cleanup();
    }
  });

  it("returns shortcut action data", async () => {
    const { dbPath, cleanup } = await setupDatabase();

    try {
      const data = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getShortcutActions(1),
      );
      expect(data).toBeInstanceOf(Uint8Array);
      expect(Array.from(data ?? [])).toEqual([1, 2, 3]);

      const missing = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getShortcutActions(999),
      );
      expect(missing).toBeNull();
    } finally {
      await cleanup();
    }
  });

  it("returns collections as folders", async () => {
    const { dbPath, cleanup } = await setupDatabase();

    try {
      const folders = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        getFolders(),
      );
      expect(folders).toEqual([
        { name: "Root", shortcutCount: 0 },
        { name: "Share Sheet", shortcutCount: 0 },
      ]);
    } finally {
      await cleanup();
    }
  });

  it("searches shortcuts by name", async () => {
    const { dbPath, cleanup } = await setupDatabase();

    try {
      const results = await withEnv("SHORTCUTS_DB_PATH", dbPath, () =>
        searchShortcutsByName("et"),
      );
      expect(results).toHaveLength(1);
      expect(results[0]?.name).toBe("beta");
    } finally {
      await cleanup();
    }
  });
});
