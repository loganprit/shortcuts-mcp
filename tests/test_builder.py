from shortcuts_mcp.builder import build_workflow_plist
from shortcuts_mcp.models import ShortcutAction
from shortcuts_mcp.parser import parse_actions


def test_build_workflow_plist_roundtrip():
    actions = [
        ShortcutAction(
            identifier="is.workflow.actions.gettext",
            parameters={"WFTextActionText": "Hello"},
        )
    ]

    payload = build_workflow_plist(
        "Sample",
        actions,
        client_release="7.0",
        client_version=4046,
    )
    parsed = parse_actions(payload)

    assert len(parsed) == 1
    assert parsed[0].identifier == "is.workflow.actions.gettext"
    assert parsed[0].parameters == {"WFTextActionText": "Hello"}


def test_build_workflow_plist_drops_none_values():
    actions = [
        ShortcutAction(
            identifier="is.workflow.actions.comment",
            parameters={"WFCommentActionText": "Hi", "WFUnused": None},
        )
    ]

    payload = build_workflow_plist(
        "Sample",
        actions,
        client_release="7.0",
        client_version=4046,
    )
    parsed = parse_actions(payload)

    assert parsed[0].parameters == {"WFCommentActionText": "Hi"}
