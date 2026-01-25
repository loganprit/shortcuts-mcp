import plistlib

from shortcuts_mcp.builder import build_workflow_plist
from shortcuts_mcp.models import ShortcutAction, ShortcutIcon
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
        client_version="4046.0.2.2",
    )
    parsed = parse_actions(payload)

    assert len(parsed) == 1
    assert parsed[0].identifier == "is.workflow.actions.gettext"
    # Check that original parameters are preserved
    assert parsed[0].parameters["WFTextActionText"] == "Hello"
    # UUID is auto-assigned by reference transformation
    assert "UUID" in parsed[0].parameters
    assert isinstance(parsed[0].parameters["UUID"], str)


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
        client_version="4046.0.2.2",
    )
    parsed = parse_actions(payload)

    # Check that original parameters are preserved and None values are dropped
    assert parsed[0].parameters["WFCommentActionText"] == "Hi"
    assert "WFUnused" not in parsed[0].parameters
    # UUID is auto-assigned by reference transformation
    assert "UUID" in parsed[0].parameters


def test_build_workflow_plist_preserves_existing_uuid():
    """Verify that existing UUIDs are preserved, not replaced."""
    existing_uuid = "CUSTOM-UUID-12345"
    actions = [
        ShortcutAction(
            identifier="is.workflow.actions.gettext",
            parameters={"WFTextActionText": "Hello", "UUID": existing_uuid},
        )
    ]

    payload = build_workflow_plist(
        "Sample",
        actions,
        client_release="7.0",
        client_version="4046.0.2.2",
    )
    parsed = parse_actions(payload)

    assert parsed[0].parameters["UUID"] == existing_uuid


def test_build_workflow_plist_sets_icon() -> None:
    actions = [
        ShortcutAction(
            identifier="is.workflow.actions.gettext",
            parameters={"WFTextActionText": "Hello"},
        )
    ]

    payload = build_workflow_plist(
        "Sample",
        actions,
        icon=ShortcutIcon(glyph_number=42, color="blue"),
        client_release="7.0",
        client_version="4046.0.2.2",
    )
    plist = plistlib.loads(payload)

    assert "WFWorkflowIcon" in plist
    icon = plist["WFWorkflowIcon"]
    assert icon["WFWorkflowIconGlyphNumber"] == 42
    assert icon["WFWorkflowIconStartColor"] == 463140863
