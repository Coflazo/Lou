from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI


def openai_enabled() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("LOU_OPENAI_API_KEY"))


def openai_client() -> OpenAI:
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("LOU_OPENAI_API_KEY"))


def parse_command_with_openai(command: str) -> dict[str, Any] | None:
    if not openai_enabled():
        return None

    client = openai_client()
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


def draft_contract_from_notes(notes: str, playbook_name: str, playbook_category: str) -> dict[str, str]:
    if not openai_enabled():
        raise ValueError("Set OPENAI_API_KEY or LOU_OPENAI_API_KEY to generate a contract from voice notes.")

    client = openai_client()
    response = client.chat.completions.create(
        model=os.getenv("LOU_OPENAI_MODEL", "gpt-4.1-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior commercial contracts lawyer. Return strict JSON only with keys "
                    "title and contract_text. Draft a complete, analyzable commercial contract from meeting notes. "
                    "Use formal contract language with these article headings: Parties and Background; Definitions; "
                    "Scope and Deliverables; Commercial Terms; Confidentiality; Data Protection and Security; "
                    "Intellectual Property; Compliance and Audit; Warranties, Indemnity, Liability and Insurance; "
                    "Term, Termination, Transition and Disputes. Do not include markdown or LaTeX commands."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Playbook: {playbook_name}\n"
                    f"Category: {playbook_category}\n"
                    f"Speaker-separated notes:\n{notes}\n\n"
                    "Create a new contract that reflects the business deal captured in the notes. "
                    "Preserve party-specific requests where speakers disagree, and convert unresolved items into draftable clauses "
                    "with brackets only where a fact is genuinely missing."
                ),
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.25,
    )
    content = response.choices[0].message.content or "{}"
    parsed = json.loads(content)
    title = str(parsed.get("title") or "Voice Notes Generated Contract").strip()
    contract_text = str(parsed.get("contract_text") or "").strip()
    if not contract_text:
        raise ValueError("OpenAI did not return contract text.")
    return {"title": title, "contract_text": contract_text}
