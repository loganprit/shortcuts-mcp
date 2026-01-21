from __future__ import annotations

import asyncio
import json
import subprocess
import time
from urllib.parse import quote

from .types import JsonValue


def _stringify_input(value: JsonValue) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _applescript_literal(value: str) -> str:
    return json.dumps(value)


def _open_url(url: str, timeout: int | None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["open", url],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


async def run_via_applescript(
    name: str, input_value: JsonValue | None = None
) -> tuple[str, int, int]:
    start = time.perf_counter()
    name_literal = _applescript_literal(name)
    script = [
        'tell application "Shortcuts Events"',
    ]
    if input_value is None:
        script.append(f"    run the shortcut named {name_literal}")
    else:
        input_literal = _applescript_literal(_stringify_input(input_value))
        script.append(
            f"    run the shortcut named {name_literal} with input {input_literal}"
        )
    script.append("end tell")

    process = await asyncio.create_subprocess_exec(
        "osascript",
        "-e",
        "\n".join(script),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    output = stdout.decode().strip()
    stderr_text = stderr.decode().strip() if stderr else ""
    if stderr_text:
        output = f"{output}\n{stderr_text}".strip()
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    returncode = process.returncode if process.returncode is not None else 1
    return output, elapsed_ms, returncode


async def run_via_url_scheme(
    name: str, input_value: JsonValue | None = None, timeout: int | None = None
) -> None:
    url = f"shortcuts://run-shortcut?name={quote(name)}"
    if input_value is not None:
        url += f"&input={quote(_stringify_input(input_value))}"

    loop = asyncio.get_running_loop()
    completed = await loop.run_in_executor(None, _open_url, url, timeout)
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        stdout = (completed.stdout or "").strip()
        message = stderr or stdout or f"open returned {completed.returncode}"
        raise RuntimeError(message)
