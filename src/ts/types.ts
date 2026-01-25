export type JsonPrimitive = string | number | boolean | null;

export type JsonValue =
  | JsonPrimitive
  | JsonValue[]
  | { [key: string]: JsonValue };

export type ShortcutAction = {
  identifier: string;
  parameters: Record<string, JsonValue>;
};

export type ActionSource = "system" | "apps" | "library" | "curated";

export type ActionParameter = {
  name: string;
  title: string | null;
  value_type: string;
  is_optional: boolean;
  description: string | null;
};

export type ActionInfo = {
  identifier: string;
  source: ActionSource;
  title: string | null;
  description: string | null;
  category: string;
  parameters: ActionParameter[];
  platform_availability: Record<string, string> | null;
  usage_count: number;
  example_params: Record<string, JsonValue> | null;
};
