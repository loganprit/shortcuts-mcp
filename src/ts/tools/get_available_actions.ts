import { z } from "zod";

import { catalog } from "../actions.js";
import type { ActionInfo } from "../types.js";

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
  input: GetAvailableActionsInput,
): Promise<{
  actions: ActionInfo[];
  categories: string[];
  sources: Record<string, number>;
  cached: boolean;
}> => {
  const { actions, cached } = await catalog.getAllActions({
    source: input.source,
    category: input.category,
    search: input.search,
    force_refresh: input.force_refresh,
  });

  const trimmed = actions.map((action) => {
    const item = { ...action };
    if (input.include_parameters === false) {
      item.parameters = [];
    }
    if (input.include_examples !== true) {
      item.example_params = null;
    }
    return item;
  });

  const categoriesSet = new Set<string>();
  const sources: Record<string, number> = {
    system: 0,
    apps: 0,
    library: 0,
    curated: 0,
  };

  for (const item of trimmed) {
    if (item.category) {
      categoriesSet.add(item.category);
    }
    sources[item.source] = (sources[item.source] || 0) + 1;
  }

  const categories = Array.from(categoriesSet).sort();

  return {
    actions: trimmed,
    categories,
    sources,
    cached,
  };
};
