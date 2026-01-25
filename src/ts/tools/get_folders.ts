import { z } from "zod";

import { getFolders as fetchFolders } from "../database.js";

export const TOOL_NAME = "get_folders";

export const INPUT_SCHEMA = {} satisfies z.ZodRawShape;

export type GetFoldersInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export type GetFoldersResult = {
  folders: Array<{
    name: string;
    shortcut_count: number;
  }>;
};

export const getFolders = async (
  _input: GetFoldersInput,
): Promise<GetFoldersResult> => {
  const folders = await fetchFolders();
  return {
    folders: folders.map((f) => ({
      name: f.name,
      shortcut_count: f.shortcutCount,
    })),
  };
};
