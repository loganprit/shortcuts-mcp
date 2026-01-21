import plistlib

from shortcuts_mcp.parser import action_types, parse_actions, parse_input_types


def _sample_plist() -> bytes:
    data = {
        "WFWorkflowActions": [
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.delay",
                "WFWorkflowActionParameters": {"WFDelayTime": 5},
            },
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.comment",
                "WFWorkflowActionParameters": {"WFCommentActionText": "Hello"},
            },
            {
                "WFWorkflowActionIdentifier": "is.workflow.actions.delay",
                "WFWorkflowActionParameters": {"WFDelayTime": 1},
            },
        ],
        "WFWorkflowInputContentItemClasses": ["WFTextContentItem"],
    }
    return plistlib.dumps(data)


def test_parse_actions():
    actions = parse_actions(_sample_plist())
    assert len(actions) == 3
    assert actions[0].identifier == "is.workflow.actions.delay"
    assert actions[1].parameters["WFCommentActionText"] == "Hello"


def test_action_types_unique():
    actions = parse_actions(_sample_plist())
    types = action_types(actions)
    assert types == ["is.workflow.actions.delay", "is.workflow.actions.comment"]


def test_parse_input_types():
    input_types = parse_input_types(_sample_plist())
    assert input_types == ["WFTextContentItem"]
