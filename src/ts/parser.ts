import { Buffer } from "node:buffer";

import { parse as parseXml } from "plist";
import { parseBuffer } from "bplist-parser";

import type { JsonValue, ShortcutAction } from "./types.js";

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const decodePlist = (data: Uint8Array): unknown | null => {
  if (data.byteLength === 0) {
    return null;
  }

  const header = new TextDecoder("utf-8").decode(data.subarray(0, 8));
  if (header.startsWith("bplist")) {
    try {
      const parsed = parseBuffer(Buffer.from(data));
      return parsed.length > 0 ? parsed[0] : null;
    } catch {
      return null;
    }
  }

  try {
    const text = new TextDecoder("utf-8", { fatal: false }).decode(data);
    return parseXml(text);
  } catch {
    return null;
  }
};

const coerceJsonValue = (value: unknown): JsonValue => {
  if (
    value === null ||
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean"
  ) {
    return value;
  }
  if (value instanceof Date) {
    return value.toISOString();
  }
  if (value instanceof Uint8Array) {
    return new TextDecoder("utf-8", { fatal: false }).decode(value);
  }
  if (value instanceof ArrayBuffer) {
    return new TextDecoder("utf-8", { fatal: false }).decode(
      new Uint8Array(value),
    );
  }
  if (Array.isArray(value)) {
    return value.map((item) => coerceJsonValue(item));
  }
  if (isRecord(value)) {
    const mapped: Record<string, JsonValue> = {};
    for (const [key, entry] of Object.entries(value)) {
      mapped[String(key)] = coerceJsonValue(entry);
    }
    return mapped;
  }
  return String(value);
};

const stringKeyDict = (value: Record<string, unknown>): Record<string, unknown> => {
  const mapped: Record<string, unknown> = {};
  for (const [key, entry] of Object.entries(value)) {
    mapped[String(key)] = entry;
  }
  return mapped;
};

export const parseActions = (data: Uint8Array): ShortcutAction[] => {
  const plist = decodePlist(data);
  if (plist === null) {
    return [];
  }

  const rawActions: Array<Record<string, unknown>> = [];
  if (Array.isArray(plist)) {
    for (const item of plist) {
      if (isRecord(item)) {
        rawActions.push(stringKeyDict(item));
      }
    }
  } else if (isRecord(plist)) {
    const plistDict = stringKeyDict(plist);
    const possibleActions = plistDict.WFWorkflowActions;
    if (Array.isArray(possibleActions)) {
      for (const item of possibleActions) {
        if (isRecord(item)) {
          rawActions.push(stringKeyDict(item));
        }
      }
    }
  } else {
    return [];
  }

  const actions: ShortcutAction[] = [];
  for (const item of rawActions) {
    const identifier = item.WFWorkflowActionIdentifier;
    if (typeof identifier !== "string" || identifier.length === 0) {
      continue;
    }
    const rawParameters = item.WFWorkflowActionParameters;
    const parameters: Record<string, JsonValue> = {};
    if (isRecord(rawParameters)) {
      for (const [key, value] of Object.entries(rawParameters)) {
        parameters[String(key)] = coerceJsonValue(value);
      }
    }
    actions.push({ identifier, parameters });
  }

  return actions;
};

export const parseInputTypes = (data: Uint8Array): string[] | null => {
  const plist = decodePlist(data);
  if (!isRecord(plist)) {
    return null;
  }

  const plistDict = stringKeyDict(plist);
  const inputTypes = plistDict.WFWorkflowInputContentItemClasses;
  if (Array.isArray(inputTypes)) {
    return inputTypes.map((item) => String(item));
  }

  return null;
};

export const actionTypes = (actions: ShortcutAction[]): string[] => {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const action of actions) {
    if (seen.has(action.identifier)) {
      continue;
    }
    seen.add(action.identifier);
    ordered.push(action.identifier);
  }
  return ordered;
};

export const actionSearchBlob = (actions: ShortcutAction[]): string => {
  const parts: string[] = [];
  for (const action of actions) {
    parts.push(action.identifier);
    if (Object.keys(action.parameters).length > 0) {
      parts.push(JSON.stringify(action.parameters));
    }
  }
  return parts.join(" ");
};
