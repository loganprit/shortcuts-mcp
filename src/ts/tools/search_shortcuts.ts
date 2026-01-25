import { z } from "zod";

export const TOOL_NAME = "search_shortcuts";

export const INPUT_SCHEMA = {
  query: z.string(),
  search_in: z.enum(["name", "actions", "both"]).optional(),
} satisfies z.ZodRawShape;

export type SearchShortcutsInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const searchShortcuts = async (
  _input: SearchShortcutsInput,
): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
