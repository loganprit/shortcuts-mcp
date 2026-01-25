import { describe, expect, it } from "bun:test";

import {
  type CommandRunner,
  applescriptLiteral,
  buildApplescript,
  buildShortcutUrl,
  runViaApplescript,
  runViaUrlScheme,
  stringifyInput,
} from "../src/executor.js";
import type { JsonValue } from "../src/types.js";

describe("executor helpers", () => {
  it("stringifies input values", () => {
    expect(stringifyInput(null)).toBe("");
    expect(stringifyInput("hello")).toBe("hello");
    expect(stringifyInput({ a: 1, b: "x" })).toBe('{"a":1,"b":"x"}');
  });

  it("builds applescript literals", () => {
    expect(applescriptLiteral('Hello "World"')).toBe('"Hello \\"World\\""');
  });

  it("builds applescript for running shortcuts", () => {
    const script = buildApplescript("My Shortcut", null);
    expect(script).toBe(
      'tell application "Shortcuts Events"\n' +
        '    run the shortcut named "My Shortcut"\n' +
        "end tell",
    );

    const scriptWithInput = buildApplescript("My Shortcut", {
      foo: "bar",
    });
    expect(scriptWithInput).toContain("with input");
    expect(scriptWithInput).toContain('"{\\"foo\\":\\"bar\\"}"');
  });

  it("builds the shortcuts URL scheme", () => {
    expect(buildShortcutUrl("Hello World", null)).toBe(
      "shortcuts://run-shortcut?name=Hello%20World",
    );

    expect(buildShortcutUrl("Hello World", { value: 1 })).toBe(
      "shortcuts://run-shortcut?name=Hello%20World&input=%7B%22value%22%3A1%7D",
    );
  });
});

describe("executor commands", () => {
  it("runs via applescript with a custom runner", async () => {
    const calls: Array<{ command: string; args: string[] }> = [];
    const runner: CommandRunner = async (command, args) => {
      calls.push({ command, args });
      return { stdout: "ok\n", stderr: "warn\n", exitCode: 0 };
    };

    const result = await runViaApplescript("Test", "input", null, runner);
    expect(calls).toHaveLength(1);
    expect(calls[0]?.command).toBe("osascript");
    expect(calls[0]?.args[0]).toBe("-e");
    expect(result.output).toBe("ok\nwarn");
    expect(result.returncode).toBe(0);
    expect(result.elapsedMs).toBeGreaterThanOrEqual(0);
  });

  it("opens shortcuts URL scheme and handles errors", async () => {
    const runner: CommandRunner = async () => ({
      stdout: "",
      stderr: "open failed",
      exitCode: 1,
    });

    await expect(runViaUrlScheme("Test", "input", 1, runner)).rejects.toThrow("open failed");
  });

  it("handles empty stderr by using stdout on failure", async () => {
    const runner: CommandRunner = async () => ({
      stdout: "failed",
      stderr: "",
      exitCode: 1,
    });

    await expect(runViaUrlScheme("Test", "input", null, runner)).rejects.toThrow("failed");
  });

  it("uses a fallback error message when no output is present", async () => {
    const runner: CommandRunner = async () => ({
      stdout: "",
      stderr: "",
      exitCode: 2,
    });

    await expect(runViaUrlScheme("Test", null, null, runner)).rejects.toThrow("open returned 2");
  });

  it("passes timeout milliseconds to the runner", async () => {
    let receivedTimeout: number | null | undefined;
    const runner: CommandRunner = async (_command, _args, options) => {
      receivedTimeout = options?.timeoutMs;
      return { stdout: "", stderr: "", exitCode: 0 };
    };

    await runViaUrlScheme("Test", null, 5, runner);
    expect(receivedTimeout).toBe(5000);
  });

  it("stringifies non-string input for applescript", async () => {
    let capturedScript = "";
    const runner: CommandRunner = async (_command, args) => {
      capturedScript = args[1] ?? "";
      return { stdout: "", stderr: "", exitCode: 0 };
    };

    const inputValue: JsonValue = { count: 2 };
    await runViaApplescript("Test", inputValue, null, runner);
    expect(capturedScript).toContain('"{\\"count\\":2}"');
  });
});
