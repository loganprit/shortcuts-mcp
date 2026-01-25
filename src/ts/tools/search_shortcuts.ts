import { z } from "zod";

import {
  getAllShortcuts,
  getShortcutActions,
  searchShortcutsByName,
} from "../database.js";
import { actionSearchBlob, parseActions } from "../parser.js";
import type { ShortcutMetadata } from "../types.js";

export const TOOL_NAME = "search_shortcuts";

export const INPUT_SCHEMA = {
  query: z.string(),
  search_in: z.enum(["name", "actions", "both"]).optional(),
} satisfies z.ZodRawShape;

export type SearchShortcutsInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const searchShortcuts = async (
  input: SearchShortcutsInput,
): Promise<unknown> => {
  const searchIn = input.search_in ?? "name";
  const matches = new Map<string, ShortcutMetadata>();

  if (searchIn === "name" || searchIn === "both") {
    const rows = await searchShortcutsByName(input.query);
    for (const row of rows) {
      matches.set(row.name, {
        name: row.name,
        id: row.workflowId,
        folder: row.folder,
        action_count: row.actionCount,
        last_modified: row.modifiedAt,
      });
    }
  }

  if (searchIn === "actions" || searchIn === "both") {
    const rows = await getAllShortcuts();
    for (const row of rows) {
      const data = await getShortcutActions(row.pk);
      if (!data) {
        continue;
      }
      const actions = parseActions(data);
      const blob = actionSearchBlob(actions).toLowerCase();
      if (blob.includes(input.query.toLowerCase())) {
        matches.set(row.name, {
          name: row.name,
          id: row.workflowId,
          folder: row.folder,
          action_count: row.actionCount,
          last_modified: row.modifiedAt,
        });
      }
    }
  }

  return { shortcuts: Array.from(matches.values()) };
};
