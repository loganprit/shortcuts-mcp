import type { JsonValue } from "./types.js";

export type CommandResult = {
  stdout: string;
  stderr: string;
  exitCode: number;
};

export type CommandOptions = {
  timeoutMs?: number | null;
};

export type CommandRunner = (
  command: string,
  args: string[],
  options?: CommandOptions,
) => Promise<CommandResult>;

export type RunResult = {
  output: string;
  elapsedMs: number;
  returncode: number;
};

const readStream = async (stream: ReadableStream<Uint8Array> | null): Promise<string> => {
  if (!stream) {
    return "";
  }
  const response = new Response(stream);
  return response.text();
};

const runCommand: CommandRunner = async (command, args, options = {}): Promise<CommandResult> => {
  const subprocess = Bun.spawn([command, ...args], {
    stdout: "pipe",
    stderr: "pipe",
  });

  const timeoutMs = options.timeoutMs ?? null;
  let timeoutId: ReturnType<typeof setTimeout> | null = null;
  let timedOut = false;

  if (timeoutMs !== null && timeoutMs > 0) {
    timeoutId = setTimeout(() => {
      timedOut = true;
      subprocess.kill();
    }, timeoutMs);
  }

  const [stdout, stderr, exitCode] = await Promise.all([
    readStream(subprocess.stdout),
    readStream(subprocess.stderr),
    subprocess.exited,
  ]);

  if (timeoutId) {
    clearTimeout(timeoutId);
  }

  if (timedOut) {
    throw new Error(`Command timed out after ${timeoutMs ?? 0} ms`);
  }

  return { stdout, stderr, exitCode };
};

export const stringifyInput = (value: JsonValue | null): string => {
  if (value === null) {
    return "";
  }
  if (typeof value === "string") {
    return value;
  }
  return JSON.stringify(value);
};

export const applescriptLiteral = (value: string): string => {
  return JSON.stringify(value);
};

export const buildApplescript = (name: string, inputValue: JsonValue | null): string => {
  const nameLiteral = applescriptLiteral(name);
  const script = ['tell application "Shortcuts Events"'];
  if (inputValue === null) {
    script.push(`    run the shortcut named ${nameLiteral}`);
  } else {
    const inputLiteral = applescriptLiteral(stringifyInput(inputValue));
    script.push(`    run the shortcut named ${nameLiteral} with input ${inputLiteral}`);
  }
  script.push("end tell");
  return script.join("\n");
};

export const buildShortcutUrl = (name: string, inputValue: JsonValue | null): string => {
  let url = `shortcuts://run-shortcut?name=${encodeURIComponent(name)}`;
  if (inputValue !== null) {
    url += `&input=${encodeURIComponent(stringifyInput(inputValue))}`;
  }
  return url;
};

export const runViaApplescript = async (
  name: string,
  inputValue: JsonValue | null = null,
  timeoutSeconds: number | null = null,
  runner: CommandRunner = runCommand,
): Promise<RunResult> => {
  const start = performance.now();
  const script = buildApplescript(name, inputValue);
  const timeoutMs = timeoutSeconds === null ? null : timeoutSeconds * 1000;
  const { stdout, stderr, exitCode } = await runner("osascript", ["-e", script], { timeoutMs });
  const trimmedStdout = stdout.trim();
  const trimmedStderr = stderr.trim();
  let output = trimmedStdout;
  if (trimmedStderr.length > 0) {
    output = `${output}\n${trimmedStderr}`.trim();
  }
  const elapsedMs = Math.round(performance.now() - start);
  return { output, elapsedMs, returncode: exitCode };
};

export const runViaUrlScheme = async (
  name: string,
  inputValue: JsonValue | null = null,
  timeoutSeconds: number | null = null,
  runner: CommandRunner = runCommand,
): Promise<void> => {
  const url = buildShortcutUrl(name, inputValue);
  const timeoutMs = timeoutSeconds === null ? null : timeoutSeconds * 1000;
  const { stdout, stderr, exitCode } = await runner("open", [url], {
    timeoutMs,
  });

  if (exitCode !== 0) {
    const trimmedStderr = stderr.trim();
    const trimmedStdout = stdout.trim();
    const message = trimmedStderr || trimmedStdout || `open returned ${exitCode}`;
    throw new Error(message);
  }
};
