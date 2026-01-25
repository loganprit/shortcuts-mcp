import { z } from "zod";

import { getDefaultTimeoutSeconds } from "../config.js";
import { runViaApplescript, runViaUrlScheme } from "../executor.js";
import type { McpToolResponse } from "../types.js";
import { jsonValueSchema } from "./schemas.js";

export const TOOL_NAME = "run_shortcut";

export const INPUT_SCHEMA = {
  name: z.string(),
  input: jsonValueSchema.nullable().optional(),
  wait_for_result: z.boolean().optional(),
  timeout: z.number().int().nullable().optional(),
} satisfies z.ZodRawShape;

export type RunShortcutInput = z.infer<z.ZodObject<typeof INPUT_SCHEMA>>;

export type RunShortcutResult = {
  success: boolean;
  output: string | null;
  execution_time_ms: number | null;
};

export const runShortcut = async (input: RunShortcutInput): Promise<McpToolResponse> => {
  const timeoutValue = input.timeout ?? getDefaultTimeoutSeconds();
  const waitForResult = input.wait_for_result !== false;

  let result: RunShortcutResult;

  if (waitForResult) {
    try {
      const { output, elapsedMs, returncode } = await runViaApplescript(
        input.name,
        input.input ?? null,
        timeoutValue,
      );

      result = {
        success: returncode === 0,
        output,
        execution_time_ms: elapsedMs,
      };
    } catch (error) {
      result = {
        success: false,
        output: error instanceof Error ? error.message : String(error),
        execution_time_ms: null,
      };
    }
  } else {
    try {
      await runViaUrlScheme(input.name, input.input ?? null, timeoutValue);
      result = {
        success: true,
        output: null,
        execution_time_ms: null,
      };
    } catch (error) {
      result = {
        success: false,
        output: error instanceof Error ? error.message : String(error),
        execution_time_ms: null,
      };
    }
  }

  return {
    content: [{ type: "text", text: JSON.stringify(result) }],
  };
};
