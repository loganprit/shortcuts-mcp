import shutil

import pytest

from shortcuts_mcp.models import ShortcutAction
from shortcuts_mcp import server


@pytest.mark.asyncio
async def test_create_shortcut_writes_signed_file(monkeypatch, tmp_path):
    async def fake_sign(
        input_path: str, output_path: str, mode: str, timeout=None
    ) -> str:
        shutil.copyfile(input_path, output_path)
        return "signed"

    async def fake_open(path: str, timeout=None) -> None:
        return None

    async def fake_get_shortcut_by_name(name: str):
        return None

    monkeypatch.setattr(server, "sign_shortcut_file", fake_sign)
    monkeypatch.setattr(server, "open_file", fake_open)
    monkeypatch.setattr(server, "get_shortcut_by_name", fake_get_shortcut_by_name)
    monkeypatch.setattr(server.tempfile, "mkdtemp", lambda prefix: str(tmp_path))

    actions = [
        ShortcutAction(
            identifier="is.workflow.actions.gettext",
            parameters={"WFTextActionText": "Hello"},
        )
    ]

    result = await server.create_shortcut(
        name="Test Shortcut",
        actions=actions,
        validate=False,
        install=True,
        wait_for_import=False,
    )

    assert result["success"] is True
    assert result["name"] == "Test Shortcut"

    unsigned_path = tmp_path / "Test Shortcut.shortcut"
    signed_path = tmp_path / "Test Shortcut signed.shortcut"
    assert unsigned_path.exists()
    assert signed_path.exists()
