import { z } from "zod";

export const TOOL_NAME = "get_shortcut";

export const INPUT_SCHEMA = {
  name: z.string(),
  include_actions: z.boolean().optional(),
} satisfies z.ZodRawShape;

export type GetShortcutInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const getShortcut = async (
  _input: GetShortcutInput,
): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
