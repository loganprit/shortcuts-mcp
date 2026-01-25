import { describe, expect, it } from "bun:test";

import {
  deriveCategory,
  mergeAction,
  parseActionsdataPayload,
  parseCuratedPayload,
} from "../../src/ts/actions.js";

import type { ActionInfo } from "../../src/ts/types.js";

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
              name: "value",
              title: { key: "Value" },
              valueType: { primitiveType: "String" },
              isOptional: true,
            },
          ],
          availabilityAnnotations: { iOS: { introducedVersion: "16.0" } },
          fullyQualifiedTypeName: "ShortcutsActions.TestAction",
        },
      },
    };

    const actions = parseActionsdataPayload(payload, "system");
    expect(actions).toHaveLength(1);
    expect(actions[0]?.identifier).toBe("com.apple.TestAction");
    expect(actions[0]?.title).toBe("Test Action");
    expect(actions[0]?.description).toBe("Does a thing");
    expect(actions[0]?.category).toBe("apple.shortcuts");
    expect(actions[0]?.parameters[0]?.value_type).toBe("string");
    expect(actions[0]?.platform_availability?.iOS).toBe("16.0");
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
    expect(deriveCategory("com.apple.ShortcutsActions.Test", null)).toBe(
      "apple.shortcuts",
    );
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
});
