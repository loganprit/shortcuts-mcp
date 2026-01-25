import shutil
from pathlib import Path

import pytest

from shortcuts_mcp import server
from shortcuts_mcp.models import ShortcutAction


@pytest.mark.asyncio
async def test_create_shortcut_writes_signed_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    async def fake_sign(
        input_path: str, output_path: str, mode: str, timeout: int | None = None
    ) -> str:
        shutil.copyfile(input_path, output_path)
        return "signed"

    async def fake_open(path: str, timeout: int | None = None) -> None:
        return None

    async def fake_get_shortcut_by_name(name: str) -> object | None:
        return None

    def fake_mkdtemp(prefix: str) -> str:
        return str(tmp_path)

    monkeypatch.setattr(server, "sign_shortcut_file", fake_sign)
    monkeypatch.setattr(server, "open_file", fake_open)
    monkeypatch.setattr(server, "get_shortcut_by_name", fake_get_shortcut_by_name)
    monkeypatch.setattr(server.tempfile, "mkdtemp", fake_mkdtemp)

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

    # After rename, only the final import path exists
    # (unsigned is deleted, signed is renamed)
    final_path = tmp_path / "Test Shortcut.shortcut"
    assert final_path.exists()
    assert result["file_path"] == str(final_path)
