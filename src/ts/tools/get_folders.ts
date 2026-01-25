import { z } from "zod";

export const TOOL_NAME = "get_folders";

export const INPUT_SCHEMA = {} satisfies z.ZodRawShape;

export type GetFoldersInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export const getFolders = async (_input: GetFoldersInput): Promise<unknown> => {
  throw new Error(`Tool ${TOOL_NAME} not implemented`);
};
