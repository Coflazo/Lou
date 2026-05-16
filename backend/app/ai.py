from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


def openai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def parse_command_with_openai(command: str) -> dict[str, Any] | None:
    if not openai_enabled():
        return None

    client = OpenAI()
    response = client.chat.completions.create(
        model=os.getenv("LOU_OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "Return compact JSON for a legal workspace command. "
                    "Allowed intents: approve, reject, export, analyze_contract, open_playbook, note."
                ),
            },
            {"role": "user", "content": command},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    return json.loads(content)
