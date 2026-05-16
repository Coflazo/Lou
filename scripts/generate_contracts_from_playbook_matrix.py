#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import textwrap
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = ROOT / "demo-data"
PLAYBOOKS_JSONL = DEMO_DATA / "playbooks.jsonl"
POSITIONS_JSONL = DEMO_DATA / "playbook_positions.jsonl"
OUTPUT_DIR = DEMO_DATA / "generated-contract-pdfs-50x50"


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:80] or "contract"


def playbook_code(playbook: dict, fallback_index: int) -> str:
    match = re.search(r"pb-(\d+)", str(playbook.get("id", "")))
    if match:
        return f"PB{int(match.group(1)):02d}"
    return f"PB{fallback_index:02d}"


def clean_playbook_name(name: str) -> str:
    return re.sub(r"^PB\d{2}\s*[-:]\s*", "", name.strip(), flags=re.IGNORECASE)


def wrap_lines(text: str, width: int = 92) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, replace_whitespace=False) or [""]


def contract_text(playbook: dict, positions: list[dict], variant: int, code: str) -> str:
    selected = positions[:8]
    clean_name = clean_playbook_name(playbook["name"])
    title = f"{code} Contract {variant:02d} - {clean_name} Demo Agreement"
    party_a = "Siemens Legal Operations"
    party_b = f"{playbook['category'].title()} Counterparty {variant:02d}"
    clauses: list[str] = [
        f"{title}",
        "",
        f"This synthetic agreement is between {party_a} and {party_b}. It is generated for Lou contract review demos and is not legal advice.",
        "",
        "1. Commercial Background.",
        f"The parties are entering a transaction governed by playbook {code}: {clean_name}. The commercial purpose is: {playbook['description']}",
        "",
    ]

    for index, position in enumerate(selected, start=2):
        columns = position.get("columns", {})
        topic = position.get("topic") or columns.get("Topic", f"Topic {index}")
        if index % 4 == 0:
            body = columns.get("Fallback 2") or position.get("fallback_position")
            posture = "Fallback drafting position"
        elif index % 5 == 0:
            body = columns.get("Red Line") or position.get("preferred_position")
            posture = "Escalation issue"
        else:
            body = position.get("preferred_position") or columns.get("Preferred Position")
            posture = "Preferred drafting position"
        clauses.extend(
            [
                f"{index}. {topic}.",
                f"{posture}: {body}. The parties shall keep records showing compliance, notify each other of material deviations, and escalate unresolved issues to legal operations within five business days.",
                "",
            ]
        )

    clauses.extend(
        [
            f"{len(selected) + 2}. Operational Exception.",
            "The supplier may use experimental workflow tooling for internal reporting without prior written approval, provided no regulated data is exported. This clause is intentionally outside some playbook coverage so Lou can surface unmapped review findings.",
            "",
            f"{len(selected) + 3}. Signatures.",
            "The parties agree to the terms above through duly authorized representatives.",
        ]
    )
    return "\n".join(clauses)


def write_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    x = 56
    y = 56
    line_height = 13
    for paragraph in text.splitlines():
        lines = wrap_lines(paragraph)
        for line in lines:
            if y > 790:
                page = document.new_page(width=595, height=842)
                y = 56
            page.insert_text((x, y), line, fontsize=10, fontname="helv")
            y += line_height
        y += 4
    document.save(path)
    document.close()


def generate(output_dir: Path, contracts_per_playbook: int, limit: int | None) -> dict:
    playbooks = read_jsonl(PLAYBOOKS_JSONL)
    positions = read_jsonl(POSITIONS_JSONL)
    by_playbook: dict[str, list[dict]] = {}
    for position in positions:
        by_playbook.setdefault(position["playbook_id"], []).append(position)

    output_dir.mkdir(parents=True, exist_ok=True)
    for old_pdf in output_dir.glob("*.pdf"):
        old_pdf.unlink()
    generated = []
    selected_playbooks = playbooks[:limit] if limit is not None else playbooks
    for playbook_index, playbook in enumerate(selected_playbooks, start=1):
        playbook_positions = by_playbook.get(playbook["id"], [])
        if not playbook_positions:
            continue
        code = playbook_code(playbook, playbook_index)
        clean_name = clean_playbook_name(playbook["name"])
        for variant in range(1, contracts_per_playbook + 1):
            filename = f"{code}-contract-{variant:02d}-{slugify(clean_name)}.pdf"
            path = output_dir / filename
            write_pdf(path, contract_text(playbook, playbook_positions, variant, code))
            generated.append(
                {
                    "playbook_id": playbook["id"],
                    "playbook_code": code,
                    "playbook_name": playbook["name"],
                    "path": str(path),
                }
            )

    manifest = output_dir / "manifest.json"
    manifest.write_text(json.dumps({"contracts": generated}, indent=2) + "\n", encoding="utf-8")
    return {"contracts": len(generated), "output_dir": str(output_dir), "manifest": str(manifest)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate text-based demo contract PDFs from Lou runtime playbooks.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--contracts-per-playbook", type=int, default=1)
    parser.add_argument("--limit", type=int, help="Generate contracts for only the first N playbooks.")
    args = parser.parse_args()

    if args.contracts_per_playbook < 1:
        raise SystemExit("--contracts-per-playbook must be at least 1.")

    print(json.dumps(generate(args.output_dir, args.contracts_per_playbook, args.limit), indent=2))


if __name__ == "__main__":
    main()
