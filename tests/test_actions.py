from shortcuts_mcp.actions import parse_actionsdata_payload, parse_curated_payload


def testparse_actionsdata_payload():
    payload = {
        "actions": {
            "ActionName": {
                "identifier": "com.apple.ShortcutsActions.MyAction",
                "fullyQualifiedTypeName": "ShortcutsActions.MyAction",
                "title": {"key": "My Action"},
                "descriptionMetadata": {"descriptionText": {"key": "Does thing"}},
                "parameters": [
                    {
                        "name": "value",
                        "title": {"key": "Value"},
                        "valueType": {"primitiveType": "String"},
                        "isOptional": True,
                    }
                ],
                "availabilityAnnotations": {
                    "LNPlatformNameMACOS": {"introducedVersion": "14.0"}
                },
            }
        }
    }

    actions = parse_actionsdata_payload(payload, source="system")
    assert len(actions) == 1
    action = actions[0]
    assert action.identifier == "com.apple.ShortcutsActions.MyAction"
    assert action.title == "My Action"
    assert action.description == "Does thing"
    assert action.category == "apple.shortcuts"
    assert action.parameters[0].value_type == "string"
    assert action.parameters[0].is_optional is True
    assert action.platform_availability == {"LNPlatformNameMACOS": "14.0"}


def testparse_curated_payload_top_level():
    payload = {
        "is.workflow.actions.gettext": {
            "title": "Text",
            "description": "Passes text",
            "parameters": [
                {
                    "name": "WFTextActionText",
                    "title": "Text",
                    "value_type": "string",
                    "is_optional": False,
                }
            ],
        }
    }

    actions = parse_curated_payload(payload)
    assert len(actions) == 1
    action = actions[0]
    assert action.identifier == "is.workflow.actions.gettext"
    assert action.source == "curated"
    assert action.category == "workflow"
    assert action.parameters[0].name == "WFTextActionText"
