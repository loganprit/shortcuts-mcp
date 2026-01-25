import { describe, expect, it } from "bun:test";

import { createServer } from "../../src/ts/index.js";

describe("typescript server scaffold", () => {
  it("exports createServer", () => {
    expect(typeof createServer).toBe("function");
  });
});
