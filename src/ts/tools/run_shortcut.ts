import { z } from "zod";

import { jsonValueSchema } from "./schemas.js";

export const TOOL_NAME = "run_shortcut";

export const INPUT_SCHEMA = {
  name: z.string(),
  input: jsonValueSchema.nullable().optional(),
  wait_for_result: z.boolean().optional(),
  timeout: z.number().int().nullable().optional(),
} satisfies z.ZodRawShape;

export type RunShortcutInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const runShortcut = async (
  _input: RunShortcutInput,
): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
