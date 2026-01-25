import { describe, expect, it } from "bun:test";

import {
  deriveCategory,
  mergeAction,
  parseActionsdataPayload,
  parseCuratedPayload,
} from "../../src/ts/actions.js";

import type { ActionInfo } from "../../src/ts/types.js";

describe("actions internal helpers", () => {
  it("extracts localized text from strings or objects", () => {
    // We need to access these via parseActionsdataPayload or similar if they are not exported,
    // but they are used by parseActionsdataPayload.
    const payload = {
      actions: {
        "test.action": {
          identifier: "test.action",
          title: "Plain String",
          descriptionMetadata: {
            descriptionText: { key: "Localized Key" },
          },
          parameters: [],
        },
      },
    };
    const actions = parseActionsdataPayload(payload, "system");
    expect(actions[0]?.title).toBe("Plain String");
    expect(actions[0]?.description).toBe("Localized Key");
  });

  it("handles null and non-record values in localized text", () => {
    const payload = {
      actions: {
        "test.action": {
          identifier: "test.action",
          title: 123,
          descriptionMetadata: {
            descriptionText: null,
          },
        },
      },
    };
    const actions = parseActionsdataPayload(payload, "system");
    expect(actions[0]?.title).toBeNull();
    expect(actions[0]?.description).toBeNull();
  });
});

describe("actions catalog parsing", () => {
  it("parses actionsdata payloads", () => {
    const payload = {
      actions: {
        "com.apple.TestAction": {
          identifier: "com.apple.TestAction",
          title: { key: "Test Action" },
          descriptionMetadata: { descriptionText: { key: "Does a thing" } },
          parameters: [
            {
              name: "stringVal",
              title: "String",
              valueType: "String",
            },
            {
              name: "primitiveVal",
              valueType: { primitiveType: "Integer" },
            },
            {
              name: "entityVal",
              valueType: { entityType: "Contact" },
            },
            {
              name: "enumVal",
              valueType: { enumType: "Unit" },
            },
            {
              name: "typeNameVal",
              valueType: { typeName: "MyType" },
            },
            {
              name: "idVal",
              valueType: { identifier: "some.id" },
            },
            {
              name: "unknownVal",
              valueType: {},
            },
          ],
          availabilityAnnotations: { iOS: { introducedVersion: "16.0" } },
          fullyQualifiedTypeName: "ShortcutsActions.TestAction",
        },
      },
    };

    const actions = parseActionsdataPayload(payload, "system");
    expect(actions).toHaveLength(1);
    expect(actions[0]?.parameters[0]?.value_type).toBe("String");
    expect(actions[0]?.parameters[1]?.value_type).toBe("integer");
    expect(actions[0]?.parameters[2]?.value_type).toBe("entity:Contact");
    expect(actions[0]?.parameters[3]?.value_type).toBe("enum:Unit");
    expect(actions[0]?.parameters[4]?.value_type).toBe("MyType");
    expect(actions[0]?.parameters[5]?.value_type).toBe("some.id");
    expect(actions[0]?.parameters[6]?.value_type).toBe("unknown");
  });

  it("parses curated payloads", () => {
    const payload = {
      actions: {
        "is.workflow.actions.comment": {
          title: "Comment",
          description: "Add a comment",
          category: "is.workflow.actions",
          parameters: [
            {
              name: "WFCommentActionText",
              title: "Text",
              value_type: "string",
              is_optional: false,
              description: "Comment text",
            },
          ],
        },
      },
    };

    const actions = parseCuratedPayload(payload);
    expect(actions).toHaveLength(1);
    expect(actions[0]?.source).toBe("curated");
    expect(actions[0]?.category).toBe("is.workflow.actions");
    expect(actions[0]?.parameters[0]?.name).toBe("WFCommentActionText");
  });

  it("derives categories from identifiers", () => {
    expect(deriveCategory("is.workflow.actions.delay", null)).toBe("workflow");
    expect(deriveCategory("com.apple.ShortcutsActions.Test", null)).toBe("apple.shortcuts");
    expect(deriveCategory("com.apple.Foo", null)).toBe("apple.system");
    expect(deriveCategory("com.example.App", null)).toBe("third-party");
  });

  it("merges library actions into existing entries", () => {
    const base: ActionInfo = {
      identifier: "com.apple.TestAction",
      source: "system",
      title: "System Title",
      description: null,
      category: "apple.system",
      parameters: [],
      platform_availability: null,
      usage_count: 0,
      example_params: null,
    };
    const incoming: ActionInfo = {
      identifier: "com.apple.TestAction",
      source: "library",
      title: null,
      description: "Used in library",
      category: "apple.system",
      parameters: [
        {
          name: "value",
          title: null,
          value_type: "string",
          is_optional: false,
          description: null,
        },
      ],
      platform_availability: null,
      usage_count: 2,
      example_params: { value: "hello" },
    };

    const merged = mergeAction(base, incoming);
    expect(merged.source).toBe("system");
    expect(merged.parameters).toHaveLength(1);
    expect(merged.description).toBe("Used in library");
    expect(merged.usage_count).toBe(2);
    expect(merged.example_params?.value).toBe("hello");
  });

  it("filters actions in the catalog", async () => {
    const { ActionCatalog } = await import("../../src/ts/actions.js");
    const catalog = new ActionCatalog();

    // Mock internal state to avoid filesystem/DB access
    // We use type casting to access private cache for testing
    (catalog as unknown as { cache: Record<string, unknown> }).cache = {
      "is.workflow.actions.delay": {
        identifier: "is.workflow.actions.delay",
        source: "system",
        title: "Delay",
        description: "Waits a bit",
        category: "workflow",
        parameters: [],
        platform_availability: null,
        usage_count: 0,
        example_params: null,
      },
      "com.apple.TestAction": {
        identifier: "com.apple.TestAction",
        source: "apps",
        title: "Test",
        description: "App action",
        category: "apple.system",
        parameters: [],
        platform_availability: null,
        usage_count: 0,
        example_params: null,
      },
    };

    const all = await catalog.getAllActions();
    expect(all.actions).toHaveLength(2);

    const filtered = await catalog.getAllActions({ source: "system" });
    expect(filtered.actions).toHaveLength(1);
    expect(filtered.actions[0]?.identifier).toBe("is.workflow.actions.delay");

    const searched = await catalog.getAllActions({ search: "App" });
    expect(searched.actions).toHaveLength(1);
    expect(searched.actions[0]?.identifier).toBe("com.apple.TestAction");

    const categorized = await catalog.getAllActions({ category: "workflow" });
    expect(categorized.actions).toHaveLength(1);
    expect(categorized.actions[0]?.identifier).toBe("is.workflow.actions.delay");
  });
});
