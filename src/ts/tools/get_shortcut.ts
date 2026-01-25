import { z } from "zod";

import { getShortcutActions, getShortcutByName } from "../database.js";
import { parseActions, parseInputTypes } from "../parser.js";
import type { ShortcutDetail } from "../types.js";

export const TOOL_NAME = "get_shortcut";

export const INPUT_SCHEMA = {
  name: z.string(),
  include_actions: z.boolean().optional(),
} satisfies z.ZodRawShape;

export type GetShortcutInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const getShortcut = async (input: GetShortcutInput): Promise<ShortcutDetail> => {
  const row = await getShortcutByName(input.name);
  if (!row) {
    throw new Error(`Shortcut not found: ${input.name}`);
  }

  let actionsList = null;
  let inputTypes = null;
  if (input.include_actions !== false) {
    const data = await getShortcutActions(row.pk);
    if (data) {
      actionsList = parseActions(data);
      inputTypes = parseInputTypes(data);
    }
  }

  return {
    name: row.name,
    id: row.workflowId,
    folder: row.folder,
    action_count: row.actionCount,
    last_modified: row.modifiedAt,
    actions: actionsList,
    input_types: inputTypes,
  };
};
