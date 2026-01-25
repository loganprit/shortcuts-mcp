import { join } from "node:path";
import { Glob } from "bun";

import { getAllShortcuts, getShortcutActions } from "./database.js";
import { parseActions } from "./parser.js";
import type { ActionInfo, ActionParameter, ActionSource, JsonValue } from "./types.js";

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === "object" && value !== null && !Array.isArray(value);

const asRecord = (value: unknown): Record<string, unknown> | null =>
  isRecord(value) ? value : null;

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
    return new TextDecoder("utf-8", { fatal: false }).decode(new Uint8Array(value));
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

const coerceJsonMapping = (value: Record<string, JsonValue>): Record<string, JsonValue> => {
  const mapped: Record<string, JsonValue> = {};
  for (const [key, entry] of Object.entries(value)) {
    mapped[key] = coerceJsonValue(entry);
  }
  return mapped;
};

const safeText = (value: unknown): string | null => (typeof value === "string" ? value : null);

const extractLocalizedText = (value: unknown): string | null => {
  if (typeof value === "string") {
    return value;
  }
  const valueMap = asRecord(value);
  if (!valueMap) {
    return null;
  }
  const key = valueMap.key;
  return typeof key === "string" ? key : null;
};

const parseValueType = (value: unknown): string => {
  if (typeof value === "string") {
    return value;
  }
  const valueMap = asRecord(value);
  if (!valueMap) {
    return "unknown";
  }
  const primitive = valueMap.primitiveType;
  if (typeof primitive === "string") {
    return primitive.toLowerCase();
  }
  const entity = valueMap.entityType;
  if (typeof entity === "string") {
    return `entity:${entity}`;
  }
  const enumType = valueMap.enumType;
  if (typeof enumType === "string") {
    return `enum:${enumType}`;
  }
  const typeName = valueMap.typeName;
  if (typeof typeName === "string") {
    return typeName;
  }
  const identifier = valueMap.identifier;
  if (typeof identifier === "string") {
    return identifier;
  }
  return "unknown";
};

const parseAvailability = (value: unknown): Record<string, string> | null => {
  const valueMap = asRecord(value);
  if (!valueMap) {
    return null;
  }
  const availability: Record<string, string> = {};
  for (const [platform, meta] of Object.entries(valueMap)) {
    const metaMap = asRecord(meta);
    if (!metaMap) {
      continue;
    }
    const version = metaMap.introducedVersion;
    if (typeof version === "string") {
      availability[platform] = version;
    }
  }
  return Object.keys(availability).length > 0 ? availability : null;
};

export const deriveCategory = (identifier: string, fqtn: string | null): string => {
  if (identifier.startsWith("is.workflow.actions.")) {
    return "workflow";
  }
  if (identifier.startsWith("com.apple.ShortcutsActions.")) {
    return "apple.shortcuts";
  }
  if (fqtn?.startsWith("ShortcutsActions.")) {
    return "apple.shortcuts";
  }
  if (identifier.startsWith("com.apple.")) {
    return "apple.system";
  }
  return "third-party";
};

const parseActionsdataParameters = (value: unknown): ActionParameter[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  const parameters: ActionParameter[] = [];
  for (const item of value) {
    const itemMap = asRecord(item);
    if (!itemMap) {
      continue;
    }
    const name = safeText(itemMap.name);
    if (!name) {
      continue;
    }
    parameters.push({
      name,
      title: extractLocalizedText(itemMap.title),
      value_type: parseValueType(itemMap.valueType),
      is_optional: Boolean(itemMap.isOptional ?? false),
      description: null,
    });
  }
  return parameters;
};

const parseCuratedParameters = (value: unknown): ActionParameter[] => {
  if (!Array.isArray(value)) {
    return [];
  }
  const parameters: ActionParameter[] = [];
  for (const item of value) {
    const itemMap = asRecord(item);
    if (!itemMap) {
      continue;
    }
    const name = safeText(itemMap.name);
    if (!name) {
      continue;
    }
    parameters.push({
      name,
      title: safeText(itemMap.title),
      value_type: safeText(itemMap.value_type) ?? "unknown",
      is_optional: Boolean(itemMap.is_optional ?? false),
      description: safeText(itemMap.description),
    });
  }
  return parameters;
};

const parseActionsdataEntry = (
  fallbackIdentifier: string,
  entry: Record<string, unknown>,
  source: ActionSource,
): ActionInfo | null => {
  const identifier = safeText(entry.identifier) ?? fallbackIdentifier;
  const title = extractLocalizedText(entry.title);
  let description: string | null = null;
  const descriptionMeta = asRecord(entry.descriptionMetadata);
  if (descriptionMeta) {
    description = extractLocalizedText(descriptionMeta.descriptionText);
  }
  const parameters = parseActionsdataParameters(entry.parameters);
  const availability = parseAvailability(entry.availabilityAnnotations);
  const fqtn = safeText(entry.fullyQualifiedTypeName);
  const category = deriveCategory(identifier, fqtn);

  return {
    identifier,
    source,
    title,
    description,
    category,
    parameters,
    platform_availability: availability,
    usage_count: 0,
    example_params: null,
  };
};

export const parseActionsdataPayload = (
  payload: Record<string, unknown>,
  source: ActionSource,
): ActionInfo[] => {
  const actionsData = asRecord(payload.actions);
  if (!actionsData) {
    return [];
  }
  const parsed: ActionInfo[] = [];
  for (const [identifier, entry] of Object.entries(actionsData)) {
    const entryMap = asRecord(entry);
    if (!entryMap) {
      continue;
    }
    const parsedAction = parseActionsdataEntry(identifier, entryMap, source);
    if (parsedAction) {
      parsed.push(parsedAction);
    }
  }
  return parsed;
};

export const parseCuratedPayload = (payload: Record<string, unknown>): ActionInfo[] => {
  const actionsData = asRecord(payload.actions);
  const curatedActions = actionsData ?? payload;
  const actions: ActionInfo[] = [];
  for (const [identifier, entry] of Object.entries(curatedActions)) {
    const entryMap = asRecord(entry);
    if (!entryMap) {
      continue;
    }
    const parameters = parseCuratedParameters(entryMap.parameters);
    const category = safeText(entryMap.category) ?? deriveCategory(identifier, null);
    actions.push({
      identifier,
      source: "curated",
      title: safeText(entryMap.title),
      description: safeText(entryMap.description),
      category,
      parameters,
      platform_availability: null,
      usage_count: 0,
      example_params: null,
    });
  }
  return actions;
};

const scanActionsdataPaths = async (
  paths: string[],
  source: ActionSource,
): Promise<ActionInfo[]> => {
  const actions: ActionInfo[] = [];
  for (const path of paths) {
    try {
      const payload = (await Bun.file(path).json()) as unknown;
      const payloadMap = asRecord(payload);
      if (!payloadMap) {
        continue;
      }
      actions.push(...parseActionsdataPayload(payloadMap, source));
    } catch {
      // Skip malformed JSON files
    }
  }
  return actions;
};

const listGlobPaths = async (root: string, pattern: string): Promise<string[]> => {
  const glob = new Glob(pattern);
  const matches: string[] = [];
  for await (const relative of glob.scan({ cwd: root, onlyFiles: true })) {
    matches.push(join(root, relative));
  }
  return matches;
};

export const mergeAction = (base: ActionInfo, incoming: ActionInfo): ActionInfo => ({
  identifier: base.identifier,
  source: base.source !== "library" ? base.source : incoming.source,
  title: base.title ?? incoming.title,
  description: base.description ?? incoming.description,
  category: base.category || incoming.category,
  parameters: base.parameters.length > 0 ? base.parameters : incoming.parameters,
  platform_availability: base.platform_availability ?? incoming.platform_availability,
  usage_count: base.usage_count + incoming.usage_count,
  example_params: base.example_params ?? incoming.example_params,
});

export class ActionCatalog {
  private cache: Record<string, ActionInfo> | null = null;
  private cacheTime = 0;

  async getAllActions(options?: {
    source?: ActionSource | null;
    category?: string | null;
    search?: string | null;
    force_refresh?: boolean;
  }): Promise<{ actions: ActionInfo[]; cached: boolean }> {
    const { source = null, category = null, search = null, force_refresh = false } = options ?? {};
    let cached = false;
    if (!this.cache || force_refresh) {
      await this.refreshCache();
    } else {
      cached = true;
    }

    let actions = Object.values(this.cache ?? {});
    if (source) {
      actions = actions.filter((item) => item.source === source);
    }
    if (category) {
      const categoryLower = category.toLowerCase();
      actions = actions.filter(
        (item) =>
          item.category.toLowerCase() === categoryLower ||
          item.identifier.toLowerCase().startsWith(categoryLower),
      );
    }
    if (search) {
      const query = search.toLowerCase();
      actions = actions.filter((action) => {
        const parts = [action.identifier, action.title ?? "", action.description ?? ""].filter(
          (part) => part.length > 0,
        );
        return parts.join(" ").toLowerCase().includes(query);
      });
    }
    return { actions, cached };
  }

  private async refreshCache(): Promise<void> {
    const systemActions = await this.scanSystemActions();
    const appActions = await this.scanAppActions();
    const libraryActions = await this.scanLibraryActions();
    const curatedActions = await this.getCuratedActions();

    const merged: Record<string, ActionInfo> = {};
    for (const action of [...systemActions, ...appActions, ...curatedActions]) {
      merged[action.identifier] = action;
    }

    for (const action of libraryActions) {
      const existing = merged[action.identifier];
      if (!existing) {
        merged[action.identifier] = action;
        continue;
      }
      merged[action.identifier] = mergeAction(existing, action);
    }

    this.cache = merged;
    this.cacheTime = Date.now();
  }

  private async scanSystemActions(): Promise<ActionInfo[]> {
    const root = "/System/Library/PrivateFrameworks";
    const paths = await listGlobPaths(root, "*/Metadata.appintents/extract.actionsdata");
    return scanActionsdataPaths(paths, "system");
  }

  private async scanAppActions(): Promise<ActionInfo[]> {
    const root = "/Applications";
    const paths = [
      ...(await listGlobPaths(
        root,
        "*.app/Contents/Resources/Metadata.appintents/extract.actionsdata",
      )),
      ...(await listGlobPaths(root, "*.app/Resources/Metadata.appintents/extract.actionsdata")),
    ];
    return scanActionsdataPaths(paths, "apps");
  }

  private async scanLibraryActions(): Promise<ActionInfo[]> {
    const rows = await getAllShortcuts();
    const usageCounts = new Map<string, number>();
    const exampleParams = new Map<string, Record<string, JsonValue>>();

    for (const row of rows) {
      const data = await getShortcutActions(row.pk);
      if (!data) {
        continue;
      }
      for (const action of parseActions(data)) {
        usageCounts.set(action.identifier, (usageCounts.get(action.identifier) ?? 0) + 1);
        if (!exampleParams.has(action.identifier) && Object.keys(action.parameters).length > 0) {
          exampleParams.set(action.identifier, coerceJsonMapping(action.parameters));
        }
      }
    }

    const actions: ActionInfo[] = [];
    for (const [identifier, count] of usageCounts.entries()) {
      actions.push({
        identifier,
        source: "library",
        title: null,
        description: null,
        category: deriveCategory(identifier, null),
        parameters: [],
        platform_availability: null,
        usage_count: count,
        example_params: exampleParams.get(identifier) ?? null,
      });
    }

    return actions;
  }

  private async getCuratedActions(): Promise<ActionInfo[]> {
    const curatedPath = new URL("../shortcuts_mcp/data/curated_actions.json", import.meta.url);
    try {
      const file = Bun.file(curatedPath);
      const exists = await file.exists();
      if (!exists) {
        return [];
      }
      const payload = (await file.json()) as unknown;
      const payloadMap = asRecord(payload);
      if (!payloadMap) {
        return [];
      }
      return parseCuratedPayload(payloadMap);
    } catch {
      return [];
    }
  }
}

export const catalog = new ActionCatalog();
