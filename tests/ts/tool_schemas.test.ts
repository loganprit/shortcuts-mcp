import { describe, expect, it } from "bun:test";
import { z } from "zod";

import { INPUT_SCHEMA as GET_AVAILABLE_ACTIONS_INPUT_SCHEMA } from "../../src/ts/tools/get_available_actions.js";
import { INPUT_SCHEMA as GET_FOLDERS_INPUT_SCHEMA } from "../../src/ts/tools/get_folders.js";
import { INPUT_SCHEMA as GET_SHORTCUT_INPUT_SCHEMA } from "../../src/ts/tools/get_shortcut.js";
import { INPUT_SCHEMA as LIST_SHORTCUTS_INPUT_SCHEMA } from "../../src/ts/tools/list_shortcuts.js";
import { INPUT_SCHEMA as RUN_SHORTCUT_INPUT_SCHEMA } from "../../src/ts/tools/run_shortcut.js";
import { jsonValueSchema } from "../../src/ts/tools/schemas.js";
import { INPUT_SCHEMA as SEARCH_SHORTCUTS_INPUT_SCHEMA } from "../../src/ts/tools/search_shortcuts.js";

const toSchema = (shape: z.ZodRawShape) => z.object(shape);

describe("tool input schemas", () => {
  it("accepts empty input for list_shortcuts", () => {
    expect(() => toSchema(LIST_SHORTCUTS_INPUT_SCHEMA).parse({})).not.toThrow();
  });

  it("requires name for get_shortcut", () => {
    expect(() => toSchema(GET_SHORTCUT_INPUT_SCHEMA).parse({})).toThrow();
  });

  it("requires query for search_shortcuts", () => {
    expect(() => toSchema(SEARCH_SHORTCUTS_INPUT_SCHEMA).parse({})).toThrow();
  });

  it("accepts empty input for get_folders", () => {
    expect(() => toSchema(GET_FOLDERS_INPUT_SCHEMA).parse({})).not.toThrow();
  });

  it("accepts optional filters for get_available_actions", () => {
    expect(() =>
      toSchema(GET_AVAILABLE_ACTIONS_INPUT_SCHEMA).parse({ source: null }),
    ).not.toThrow();
  });

  it("accepts json input for run_shortcut", () => {
    const input = {
      name: "Example",
      input: { payload: ["value", 2, { ok: true }] },
      wait_for_result: false,
      timeout: null,
    };
    expect(() => toSchema(RUN_SHORTCUT_INPUT_SCHEMA).parse(input)).not.toThrow();
  });
});

describe("json value schema", () => {
  it("accepts nested json structures", () => {
    const schema = z.object({ input: jsonValueSchema });
    const value = {
      input: { foo: ["bar", { baz: 1 }], ok: true, empty: null },
    };
    expect(() => schema.parse(value)).not.toThrow();
  });
});
