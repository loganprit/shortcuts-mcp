export type JsonPrimitive = string | number | boolean | null;

export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

/**
 * MCP tool response format required by the SDK.
 * Tools must return content as an array of typed content blocks.
 */
export type McpToolResponse = {
  content: Array<{ type: "text"; text: string }>;
};

export type ShortcutAction = {
  identifier: string;
  parameters: Record<string, JsonValue>;
};

export type ShortcutMetadata = {
  name: string;
  id: string | null;
  folder: string | null;
  action_count: number | null;
  last_modified: string | null;
  action_types?: string[] | null;
};

export type ShortcutDetail = {
  name: string;
  id: string | null;
  folder: string | null;
  action_count: number | null;
  last_modified: string | null;
  actions: ShortcutAction[] | null;
  input_types: string[] | null;
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
