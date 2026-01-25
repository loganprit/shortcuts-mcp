import { z } from "zod";

import { getAllShortcuts, getShortcutActions } from "../database.js";
import { actionTypes, parseActions } from "../parser.js";
import type { McpToolResponse, ShortcutMetadata } from "../types.js";

export const TOOL_NAME = "list_shortcuts";

export const INPUT_SCHEMA = {
  folder: z.string().nullable().optional(),
  include_actions: z.boolean().optional(),
} satisfies z.ZodRawShape;

export type ListShortcutsInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const listShortcuts = async (input: ListShortcutsInput): Promise<McpToolResponse> => {
  const rows = await getAllShortcuts(input.folder ?? null);
  const shortcuts: ShortcutMetadata[] = [];

  for (const row of rows) {
    let actionTypesList: string[] | null = null;
    if (input.include_actions) {
      const data = await getShortcutActions(row.pk);
      if (data) {
        const actions = parseActions(data);
        actionTypesList = actionTypes(actions);
      }
    }

    shortcuts.push({
      name: row.name,
      id: row.workflowId,
      folder: row.folder,
      action_count: row.actionCount,
      last_modified: row.modifiedAt,
      action_types: actionTypesList,
    });
  }

  return {
    content: [{ type: "text", text: JSON.stringify({ shortcuts }) }],
  };
};
