import { z } from "zod";

export const TOOL_NAME = "list_shortcuts";

export const INPUT_SCHEMA = {
  folder: z.string().nullable().optional(),
  include_actions: z.boolean().optional(),
} satisfies z.ZodRawShape;

export type ListShortcutsInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const listShortcuts = async (
  _input: ListShortcutsInput,
): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
