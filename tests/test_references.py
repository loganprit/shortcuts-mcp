"""Tests for the reference transformation module."""

from typing import Any, cast

import pytest

from shortcuts_mcp.models import ShortcutAction
from shortcuts_mcp.references import transform_references


class TestTransformReferences:
    """Tests for transform_references function."""

    def test_assigns_uuids_to_all_actions(self) -> None:
        """All actions should get UUIDs assigned if they don't have one."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={},
            ),
        ]

        result = transform_references(actions)

        assert len(result) == 2
        for action in result:
            assert "UUID" in action.parameters
            uuid = action.parameters["UUID"]
            assert isinstance(uuid, str)
            assert len(uuid) == 36  # Standard UUID format

    def test_preserves_existing_uuids(self) -> None:
        """Existing UUIDs should not be replaced."""
        existing_uuid = "MY-CUSTOM-UUID-1234"
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello", "UUID": existing_uuid},
            ),
        ]

        result = transform_references(actions)

        assert result[0].parameters["UUID"] == existing_uuid

    def test_ref_previous(self) -> None:
        """$ref: 'previous' should reference the immediately preceding action."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "previous"}},
            ),
        ]

        result = transform_references(actions)

        # Get the UUID of the first action
        first_uuid = result[0].parameters["UUID"]

        # Check that the output parameter has been transformed
        output_param = cast(dict[str, Any], result[1].parameters["WFOutput"])
        assert output_param["WFSerializationType"] == "WFTextTokenAttachment"
        value = cast(dict[str, Any], output_param["Value"])
        assert value["Type"] == "ActionOutput"
        assert value["OutputUUID"] == first_uuid

    def test_ref_previous_from_first_action_raises(self) -> None:
        """$ref: 'previous' from the first action should raise an error."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "previous"}},
            ),
        ]

        with pytest.raises(ValueError, match="Cannot reference 'previous'"):
            transform_references(actions)

    def test_ref_by_uuid(self) -> None:
        """$ref: 'uuid:XXXX' should reference a specific action by UUID."""
        target_uuid = "TARGET-UUID-12345"
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello", "UUID": target_uuid},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": f"uuid:{target_uuid}"}},
            ),
        ]

        result = transform_references(actions)

        output_param = cast(dict[str, Any], result[1].parameters["WFOutput"])
        value = cast(dict[str, Any], output_param["Value"])
        assert value["OutputUUID"] == target_uuid

    def test_ref_by_numeric_index(self) -> None:
        """$ref with numeric index should reference action at that position."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "First"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Second"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "0"}},  # Reference first action
            ),
        ]

        result = transform_references(actions)

        first_uuid = result[0].parameters["UUID"]
        output_param = cast(dict[str, Any], result[2].parameters["WFOutput"])
        value = cast(dict[str, Any], output_param["Value"])
        assert value["OutputUUID"] == first_uuid

    def test_ref_by_negative_index(self) -> None:
        """$ref with negative index should reference relative to current action."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "First"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Second"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "-2"}},  # Two actions back
            ),
        ]

        result = transform_references(actions)

        first_uuid = result[0].parameters["UUID"]
        output_param = cast(dict[str, Any], result[2].parameters["WFOutput"])
        value = cast(dict[str, Any], output_param["Value"])
        assert value["OutputUUID"] == first_uuid

    def test_var_reference(self) -> None:
        """$var should create a variable reference."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$var": "myVariable"}},
            ),
        ]

        result = transform_references(actions)

        output_param = cast(dict[str, Any], result[0].parameters["WFOutput"])
        assert output_param["WFSerializationType"] == "WFTextTokenAttachment"
        value = cast(dict[str, Any], output_param["Value"])
        assert value["Type"] == "Variable"
        assert value["VariableName"] == "myVariable"

    def test_var_empty_name_raises(self) -> None:
        """$var with empty name should raise an error."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$var": ""}},
            ),
        ]

        with pytest.raises(ValueError, match="cannot be empty"):
            transform_references(actions)

    def test_input_reference(self) -> None:
        """$input should create an extension input reference."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$input": True}},
            ),
        ]

        result = transform_references(actions)

        output_param = cast(dict[str, Any], result[0].parameters["WFOutput"])
        assert output_param["WFSerializationType"] == "WFTextTokenAttachment"
        value = cast(dict[str, Any], output_param["Value"])
        assert value["Type"] == "ExtensionInput"

    def test_ask_reference(self) -> None:
        """$ask should create an ask-each-time reference."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ask": True}},
            ),
        ]

        result = transform_references(actions)

        output_param = cast(dict[str, Any], result[0].parameters["WFOutput"])
        assert output_param["WFSerializationType"] == "WFTextTokenAttachment"
        value = cast(dict[str, Any], output_param["Value"])
        assert value["Type"] == "Ask"

    def test_clipboard_reference(self) -> None:
        """$clipboard should create a clipboard reference."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$clipboard": True}},
            ),
        ]

        result = transform_references(actions)

        output_param = cast(dict[str, Any], result[0].parameters["WFOutput"])
        assert output_param["WFSerializationType"] == "WFTextTokenAttachment"
        value = cast(dict[str, Any], output_param["Value"])
        assert value["Type"] == "Clipboard"

    def test_nested_dict_transformation(self) -> None:
        """References inside nested dicts should be transformed."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.dictionary",
                parameters={"WFItems": {"nested": {"value": {"$ref": "previous"}}}},
            ),
        ]

        result = transform_references(actions)

        first_uuid = result[0].parameters["UUID"]
        wf_items = cast(dict[str, Any], result[1].parameters["WFItems"])
        nested = cast(dict[str, Any], wf_items["nested"]["value"])
        value = cast(dict[str, Any], nested["Value"])
        assert value["OutputUUID"] == first_uuid

    def test_list_transformation(self) -> None:
        """References inside lists should be transformed."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.list",
                parameters={
                    "WFItems": [
                        "static",
                        {"$ref": "previous"},
                        {"$var": "myVar"},
                    ]
                },
            ),
        ]

        result = transform_references(actions)

        first_uuid = result[0].parameters["UUID"]
        items = cast(list[Any], result[1].parameters["WFItems"])
        assert items[0] == "static"
        item1 = cast(dict[str, Any], items[1])
        value1 = cast(dict[str, Any], item1["Value"])
        assert value1["OutputUUID"] == first_uuid
        item2 = cast(dict[str, Any], items[2])
        value2 = cast(dict[str, Any], item2["Value"])
        assert value2["VariableName"] == "myVar"

    def test_preserves_non_reference_parameters(self) -> None:
        """Non-reference parameters should pass through unchanged."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={
                    "WFTextActionText": "Hello",
                    "SomeNumber": 42,
                    "SomeBool": True,
                    "SomeList": [1, 2, 3],
                },
            ),
        ]

        result = transform_references(actions)

        params = result[0].parameters
        assert params["WFTextActionText"] == "Hello"
        assert params["SomeNumber"] == 42
        assert params["SomeBool"] is True
        assert params["SomeList"] == [1, 2, 3]

    def test_invalid_ref_value_raises(self) -> None:
        """Invalid $ref values should raise an error."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "invalid_reference"}},
            ),
        ]

        with pytest.raises(ValueError, match="Invalid \\$ref value"):
            transform_references(actions)

    def test_ref_future_action_raises(self) -> None:
        """Referencing a future action should raise an error."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "1"}},  # Can't reference forward
            ),
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
        ]

        with pytest.raises(ValueError, match="Cannot reference action"):
            transform_references(actions)

    def test_ref_out_of_range_raises(self) -> None:
        """$ref with out-of-range index should raise an error."""
        actions = [
            ShortcutAction(
                identifier="is.workflow.actions.gettext",
                parameters={"WFTextActionText": "Hello"},
            ),
            ShortcutAction(
                identifier="is.workflow.actions.output",
                parameters={"WFOutput": {"$ref": "5"}},  # Only 2 actions
            ),
        ]

        with pytest.raises(ValueError, match="out of range"):
            transform_references(actions)
