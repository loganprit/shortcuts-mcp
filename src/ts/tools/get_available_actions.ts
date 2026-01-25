import { z } from "zod";

export const TOOL_NAME = "get_available_actions";

export const INPUT_SCHEMA = {
  source: z.enum(["system", "apps", "library", "curated"]).nullable().optional(),
  category: z.string().nullable().optional(),
  search: z.string().nullable().optional(),
  include_parameters: z.boolean().optional(),
  include_examples: z.boolean().optional(),
  force_refresh: z.boolean().optional(),
} satisfies z.ZodRawShape;

export type GetAvailableActionsInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const getAvailableActions = async (
  _input: GetAvailableActionsInput,
): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
