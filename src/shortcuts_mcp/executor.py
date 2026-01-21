from __future__ import annotations

import asyncio
import json
import subprocess
import time
from typing import Any
from urllib.parse import quote


def _stringify_input(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value)


def _applescript_literal(value: str) -> str:
    return json.dumps(value)


async def run_via_applescript(name: str, input_value: Any | None = None) -> tuple[str, int]:
    start = time.perf_counter()
    name_literal = _applescript_literal(name)
    script = [
        'tell application "Shortcuts Events"',
    ]
    if input_value is None:
        script.append(f"    run the shortcut named {name_literal}")
    else:
        input_literal = _applescript_literal(_stringify_input(input_value))
        script.append(f"    run the shortcut named {name_literal} with input {input_literal}")
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
    if stderr:
        output = f"{output}\n{stderr.decode().strip()}".strip()
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return output, elapsed_ms


async def run_via_url_scheme(name: str, input_value: Any | None = None) -> None:
    url = f"shortcuts://run-shortcut?name={quote(name)}"
    if input_value is not None:
        url += f"&input={quote(_stringify_input(input_value))}"

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, subprocess.run, ["open", url])
