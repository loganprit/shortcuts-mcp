import { Database } from "bun:sqlite";

import { getDbPath } from "./config.js";

const COCOA_EPOCH_MS = Date.UTC(2001, 0, 1, 0, 0, 0, 0);

export type ShortcutRow = {
  pk: number;
  name: string;
  actionCount: number | null;
  modifiedAt: string | null;
  workflowId: string | null;
  folder: string | null;
};

export type FolderRow = {
  name: string;
  shortcutCount: number;
};

const connect = (): Database => {
  const dbPath = getDbPath();
  return new Database(dbPath, { readonly: true });
};

const normalizeUuid = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number") {
    return `${value}`;
  }
  if (value instanceof Uint8Array) {
    if (value.byteLength === 16) {
      const hex = Array.from(value, (byte) => byte.toString(16).padStart(2, "0"));
      const parts = [
        hex.slice(0, 4).join(""),
        hex.slice(4, 6).join(""),
        hex.slice(6, 8).join(""),
        hex.slice(8, 10).join(""),
        hex.slice(10, 16).join(""),
      ];
      return parts.join("-");
    }

    try {
      const decoder = new TextDecoder("utf-8", { fatal: true });
      return decoder.decode(value);
    } catch {
      return null;
    }
  }

  return String(value);
};

const convertCocoaDate = (value: unknown): string | null => {
  if (value === null || value === undefined) {
    return null;
  }

  let seconds: number | null = null;
  if (typeof value === "number") {
    seconds = value;
  } else if (typeof value === "string") {
    const parsed = Number.parseFloat(value);
    seconds = Number.isNaN(parsed) ? null : parsed;
  }

  if (seconds === null) {
    return null;
  }

  const date = new Date(COCOA_EPOCH_MS + seconds * 1000);
  const iso = date.toISOString();
  if (date.getUTCMilliseconds() === 0) {
    return iso.replace(".000Z", "+00:00");
  }
  return iso.replace("Z", "+00:00");
};

const requireString = (value: unknown, field: string): string => {
  if (typeof value === "string") {
    return value;
  }
  if (value === null || value === undefined) {
    throw new Error(`Expected ${field} to be string`);
  }
  return String(value);
};

const asNumberOrNull = (value: unknown): number | null => {
  if (value === null || value === undefined) {
    return null;
  }
  if (typeof value === "number") {
    return Number.isNaN(value) ? null : value;
  }
  const parsed = Number.parseFloat(String(value));
  return Number.isNaN(parsed) ? null : parsed;
};

export const getAllShortcuts = async (folder: string | null = null): Promise<ShortcutRow[]> => {
  const query = `
    SELECT
      Z_PK AS pk,
      ZNAME AS name,
      ZACTIONCOUNT AS action_count,
      ZMODIFICATIONDATE AS modified_at,
      ZWORKFLOWID AS workflow_id
    FROM ZSHORTCUT
    WHERE ZNAME IS NOT NULL
    ORDER BY ZNAME COLLATE NOCASE
  `;

  const db = connect();
  try {
    const rows = db.query(query).all() as Array<Record<string, unknown>>;
    return rows.map((row) => ({
      pk: Number(row.pk ?? 0),
      name: requireString(row.name, "name"),
      actionCount: asNumberOrNull(row.action_count),
      modifiedAt: convertCocoaDate(row.modified_at),
      workflowId: normalizeUuid(row.workflow_id),
      folder: folder ?? null,
    }));
  } finally {
    db.close();
  }
};

export const getShortcutByName = async (name: string): Promise<ShortcutRow | null> => {
  const query = `
    SELECT
      Z_PK AS pk,
      ZNAME AS name,
      ZACTIONCOUNT AS action_count,
      ZMODIFICATIONDATE AS modified_at,
      ZWORKFLOWID AS workflow_id
    FROM ZSHORTCUT
    WHERE ZNAME = ?
    LIMIT 1
  `;

  const db = connect();
  try {
    const row = db.query(query).get(name) as Record<string, unknown> | null;
    if (!row) {
      return null;
    }

    return {
      pk: Number(row.pk ?? 0),
      name: requireString(row.name, "name"),
      actionCount: asNumberOrNull(row.action_count),
      modifiedAt: convertCocoaDate(row.modified_at),
      workflowId: normalizeUuid(row.workflow_id),
      folder: null,
    };
  } finally {
    db.close();
  }
};

export const getShortcutActions = async (shortcutPk: number): Promise<Uint8Array | null> => {
  const query = `
    SELECT ZDATA AS data
    FROM ZSHORTCUTACTIONS
    WHERE ZSHORTCUT = ?
    LIMIT 1
  `;

  const db = connect();
  try {
    const row = db.query(query).get(shortcutPk) as Record<string, unknown> | null;
    if (!row || row.data === null || row.data === undefined) {
      return null;
    }

    const data = row.data;
    if (data instanceof Uint8Array) {
      return data;
    }
    if (data instanceof ArrayBuffer) {
      return new Uint8Array(data);
    }
    if (typeof data === "string") {
      return new TextEncoder().encode(data);
    }

    return null;
  } finally {
    db.close();
  }
};

export const getFolders = async (): Promise<FolderRow[]> => {
  const query = `
    SELECT
      COALESCE(ZTEMPORARYSYNCFOLDERNAME, ZIDENTIFIER) AS name
    FROM ZCOLLECTION
    WHERE ZIDENTIFIER IS NOT NULL
    ORDER BY name COLLATE NOCASE
  `;

  const db = connect();
  try {
    const rows = db.query(query).all() as Array<Record<string, unknown>>;
    return rows
      .map((row) => {
        const name = row.name;
        if (typeof name !== "string" || name.length === 0) {
          return null;
        }
        return { name, shortcutCount: 0 };
      })
      .filter((row): row is FolderRow => row !== null);
  } finally {
    db.close();
  }
};

export const searchShortcutsByName = async (query: string): Promise<ShortcutRow[]> => {
  const sql = `
    SELECT
      Z_PK AS pk,
      ZNAME AS name,
      ZACTIONCOUNT AS action_count,
      ZMODIFICATIONDATE AS modified_at,
      ZWORKFLOWID AS workflow_id
    FROM ZSHORTCUT
    WHERE ZNAME LIKE ?
    ORDER BY ZNAME COLLATE NOCASE
  `;
  const like = `%${query}%`;

  const db = connect();
  try {
    const rows = db.query(sql).all(like) as Array<Record<string, unknown>>;
    return rows.map((row) => ({
      pk: Number(row.pk ?? 0),
      name: requireString(row.name, "name"),
      actionCount: asNumberOrNull(row.action_count),
      modifiedAt: convertCocoaDate(row.modified_at),
      workflowId: normalizeUuid(row.workflow_id),
      folder: null,
    }));
  } finally {
    db.close();
  }
};
