import { describe, expect, it } from "bun:test";
import { build } from "plist";

import {
  actionSearchBlob,
  actionTypes,
  parseActions,
  parseInputTypes,
} from "../../src/ts/parser.js";

const samplePlist = (): Uint8Array => {
  const data = {
    WFWorkflowActions: [
      {
        WFWorkflowActionIdentifier: "is.workflow.actions.delay",
        WFWorkflowActionParameters: { WFDelayTime: 5 },
      },
      {
        WFWorkflowActionIdentifier: "is.workflow.actions.comment",
        WFWorkflowActionParameters: { WFCommentActionText: "Hello" },
      },
      {
        WFWorkflowActionIdentifier: "is.workflow.actions.delay",
        WFWorkflowActionParameters: { WFDelayTime: 1 },
      },
    ],
    WFWorkflowInputContentItemClasses: ["WFTextContentItem"],
  };
  const xml = build(data);
  return new TextEncoder().encode(xml);
};

describe("plist parser", () => {
  it("parses actions from plist payloads", () => {
    const actions = parseActions(samplePlist());
    expect(actions.length).toBe(3);
    expect(actions[0]?.identifier).toBe("is.workflow.actions.delay");
    expect(actions[1]?.parameters.WFCommentActionText).toBe("Hello");
  });

  it("parses action lists stored as a root array", () => {
    const xml = build([
      {
        WFWorkflowActionIdentifier: "is.workflow.actions.delay",
        WFWorkflowActionParameters: { WFDelayTime: 5 },
      },
    ]);
    const actions = parseActions(new TextEncoder().encode(xml));
    expect(actions).toHaveLength(1);
    expect(actions[0]?.identifier).toBe("is.workflow.actions.delay");
  });

  it("deduplicates action identifiers for action types", () => {
    const actions = parseActions(samplePlist());
    const types = actionTypes(actions);
    expect(types).toEqual([
      "is.workflow.actions.delay",
      "is.workflow.actions.comment",
    ]);
  });

  it("extracts input types", () => {
    const inputTypes = parseInputTypes(samplePlist());
    expect(inputTypes).toEqual(["WFTextContentItem"]);
  });

  it("builds a search blob from identifiers and parameters", () => {
    const actions = parseActions(samplePlist());
    const blob = actionSearchBlob(actions);
    expect(blob).toContain("is.workflow.actions.comment");
    expect(blob).toContain("WFCommentActionText");
  });

  it("returns empty or null for invalid plist data", () => {
    const invalid = new TextEncoder().encode("not a plist");
    expect(parseActions(invalid)).toEqual([]);
    expect(parseInputTypes(invalid)).toBeNull();
  });
});
