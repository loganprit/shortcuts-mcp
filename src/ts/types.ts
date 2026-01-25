export type JsonPrimitive = string | number | boolean | null;

export type JsonValue =
  | JsonPrimitive
  | JsonValue[]
  | { [key: string]: JsonValue };

export type ShortcutAction = {
  identifier: string;
  parameters: Record<string, JsonValue>;
};
