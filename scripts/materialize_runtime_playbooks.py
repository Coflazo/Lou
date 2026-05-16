#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = ROOT / "demo-data"
SOURCE_DATASET = DEMO_DATA / "lou-pioneer-playbook-datasets-50.jsonl"
MATRIX_DATASET = DEMO_DATA / "lou-pioneer-playbook-matrix-50x50.jsonl"
PLAYBOOKS_JSONL = DEMO_DATA / "playbooks.jsonl"
POSITIONS_JSONL = DEMO_DATA / "playbook_positions.jsonl"

RUNTIME_COLUMNS = [
    "Topic",
    "Preferred Position",
    "Fallback 1",
    "Fallback 2",
    "Fallback 3",
    "Red Line",
    "Deal Breaker",
]

PLAYBOOK_SPECS = [
    {
        "id": "pb-mutual-nda",
        "slug": "mutual-nda",
        "name": "Siemens Mutual NDA Playbook",
        "category": "Confidentiality",
        "description": "Default negotiation positions for supplier and partner mutual NDAs.",
        "owner": "Siemens Legal Ops",
        "patterns": ["nda", "confidential", "non-disclosure", "nondisclosure", "disclosure"],
    },
    {
        "id": "pb-dpa-privacy",
        "slug": "data-processing-privacy",
        "name": "Data Processing Playbook",
        "category": "Privacy",
        "description": "Controller, processor, breach, transfer, consent, and data residency positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["data processing", "data breach", "data privacy", "data transfer", "consent", "gdpr", "ccpa"],
    },
    {
        "id": "pb-saas",
        "slug": "saas-commercial",
        "name": "SaaS Playbook",
        "category": "SaaS",
        "description": "Subscription, SLA, renewal, data ownership, and cloud-service positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["saas", "service level", "subscription", "uptime"],
    },
    {
        "id": "pb-ai-vendor",
        "slug": "ai-vendor",
        "name": "AI Vendor Playbook",
        "category": "AI",
        "description": "AI vendor data use, model access, training, ethics, and usage-control positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["ai vendor", "ai model", "model training", "model access", "ethical"],
    },
    {
        "id": "pb-security",
        "slug": "security-compliance",
        "name": "Security Playbook",
        "category": "Security",
        "description": "Security controls, audit rights, incident response, and compliance positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["security", "incident", "iso 27001", "soc 2", "audit"],
    },
    {
        "id": "pb-ip-licensing",
        "slug": "ip-licensing",
        "name": "IP Licensing Playbook",
        "category": "Intellectual Property",
        "description": "IP ownership, assignment, licensing, derivative work, and commercialization positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["ip ", "intellectual property", "licensing", "ownership", "assignment"],
    },
    {
        "id": "pb-procurement",
        "slug": "procurement",
        "name": "Procurement Playbook",
        "category": "Procurement",
        "description": "Supplier pricing, delivery, payment, performance, and purchasing positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["procurement", "supplier", "payment", "delivery", "goods"],
    },
    {
        "id": "pb-professional-services",
        "slug": "professional-services",
        "name": "Services Playbook",
        "category": "Professional Services",
        "description": "Services scope, deliverables, payment milestones, term, and termination positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["professional services", "scope of work", "deliverables"],
    },
    {
        "id": "pb-enterprise-software",
        "slug": "enterprise-software",
        "name": "Software Playbook",
        "category": "Enterprise Software",
        "description": "Enterprise software licensing, customization, maintenance, and use-right positions.",
        "owner": "Siemens Legal Ops",
        "patterns": ["enterprise software", "software licensing", "customization", "license"],
    },
]


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:54] or "playbook"


def playbook_code(playbook_id: str, fallback_index: int) -> str:
    match = re.search(r"pb-(\d+)", playbook_id)
    if match:
        return f"PB{int(match.group(1)):02d}"
    return f"PB{fallback_index:02d}"


def human_title(name: str) -> str:
    acronyms = {
        "ai": "AI",
        "dpa": "DPA",
        "dsar": "DSAR",
        "ip": "IP",
        "nda": "NDA",
        "saas": "SaaS",
        "sla": "SLA",
    }
    parts = re.split(r"(\W+)", name.strip())
    titled = []
    for part in parts:
        lowered = part.lower()
        if lowered in acronyms:
            titled.append(acronyms[lowered])
        elif part.isalpha():
            titled.append(part[:1].upper() + part[1:].lower())
        else:
            titled.append(part)
    return "".join(titled)


def display_playbook_name(playbook_id: str, name: str, fallback_index: int) -> str:
    code = playbook_code(playbook_id, fallback_index)
    cleaned = re.sub(r"^PB\d{2}\s*[-:]\s*", "", name.strip(), flags=re.IGNORECASE)
    return f"{code} - {human_title(cleaned)}"


def infer_keywords(values: Iterable[str], limit: int = 8) -> list[str]:
    stop = {
        "agreement",
        "client",
        "customer",
        "vendor",
        "position",
        "fallback",
        "preferred",
        "limited",
        "defined",
        "include",
        "includes",
    }
    seen: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z-]{3,}", " ".join(values)):
        lowered = word.lower()
        if lowered in stop or lowered in seen:
            continue
        seen.append(lowered)
        if len(seen) == limit:
            break
    return seen


def spec_for(row: dict) -> dict:
    text = " ".join(str(row.get(column, "")) for column in RUNTIME_COLUMNS).lower()
    topic = str(row.get("Topic", "")).lower()
    best_spec = PLAYBOOK_SPECS[-1]
    best_score = -1
    for spec in PLAYBOOK_SPECS:
        score = -1
        for pattern in spec["patterns"]:
            if pattern in topic:
                score = max(score, 100 + len(pattern))
            elif pattern in text:
                score = max(score, len(pattern))
        if score > best_score:
            best_spec = spec
            best_score = score
    return best_spec


def risk_for(row: dict) -> str:
    deal_breaker = str(row.get("Deal Breaker", "")).lower()
    red_line = str(row.get("Red Line", "")).lower()
    if any(term in deal_breaker for term in ["no ", "without", "unrestricted", "not required", "not permitted"]):
        return "High"
    if any(term in red_line for term in ["no ", "without", "unrestricted", "must"]):
        return "High"
    return "Medium"


def materialize() -> dict:
    if MATRIX_DATASET.exists():
        return materialize_matrix_dataset(MATRIX_DATASET)

    if not SOURCE_DATASET.exists():
        raise SystemExit(f"Missing source dataset: {SOURCE_DATASET}")

    rows = read_jsonl(SOURCE_DATASET)
    grouped: dict[str, list[dict]] = {spec["id"]: [] for spec in PLAYBOOK_SPECS}
    for row in rows:
        grouped[spec_for(row)["id"]].append(row)

    active_specs = [spec for spec in PLAYBOOK_SPECS if grouped[spec["id"]]]

    with PLAYBOOKS_JSONL.open("w", encoding="utf-8") as handle:
        for index, spec in enumerate(active_specs, start=1):
            payload = {
                "id": spec["id"],
                "slug": spec["slug"],
                "name": display_playbook_name(spec["id"], spec["name"], index),
                "category": spec["category"],
                "description": spec["description"],
                "owner": spec["owner"],
                "version": 1,
                "columns": RUNTIME_COLUMNS,
            }
            handle.write(json.dumps(payload) + "\n")

    with POSITIONS_JSONL.open("w", encoding="utf-8") as handle:
        for spec in active_specs:
            for index, row in enumerate(grouped[spec["id"]], start=1):
                columns = {column: str(row.get(column, "")).strip() for column in RUNTIME_COLUMNS}
                payload = {
                    "id": f"{spec['slug']}-pos-{index:03d}",
                    "playbook_id": spec["id"],
                    "topic": columns["Topic"],
                    "preferred_position": columns["Preferred Position"],
                    "fallback_position": columns["Fallback 1"],
                    "risk": risk_for(row),
                    "keywords": infer_keywords(columns.values()),
                    "columns": columns,
                }
                handle.write(json.dumps(payload) + "\n")

    return {
        "source_rows": len(rows),
        "playbooks": len(active_specs),
        "positions": sum(len(grouped[spec["id"]]) for spec in active_specs),
        "playbooks_file": str(PLAYBOOKS_JSONL),
        "positions_file": str(POSITIONS_JSONL),
    }


def materialize_matrix_dataset(path: Path) -> dict:
    rows = read_jsonl(path)
    grouped: dict[str, list[dict]] = {}
    specs: dict[str, dict] = {}
    for row in rows:
        playbook_id = str(row.get("playbook_id", "")).strip()
        playbook_name = str(row.get("playbook_name", "")).strip()
        if not playbook_id or not playbook_name:
            continue
        grouped.setdefault(playbook_id, []).append(row)
        specs.setdefault(
            playbook_id,
            {
                "id": playbook_id,
                "slug": slugify(playbook_name),
                "name": playbook_name,
                "category": str(row.get("category", "Commercial")).strip() or "Commercial",
                "description": str(row.get("description", "")).strip() or f"Generated playbook for {playbook_name}.",
                "owner": "Siemens Legal Ops",
                "version": 1,
                "columns": RUNTIME_COLUMNS,
            },
        )

    ordered_ids = sorted(grouped, key=lambda value: int(value.split("-")[1]) if re.match(r"pb-\d+", value) else value)

    with PLAYBOOKS_JSONL.open("w", encoding="utf-8") as handle:
        for index, playbook_id in enumerate(ordered_ids, start=1):
            payload = dict(specs[playbook_id])
            payload["name"] = display_playbook_name(playbook_id, payload["name"], index)
            handle.write(json.dumps(payload) + "\n")

    with POSITIONS_JSONL.open("w", encoding="utf-8") as handle:
        for playbook_id in ordered_ids:
            for index, row in enumerate(grouped[playbook_id], start=1):
                columns = {column: str(row.get(column, "")).strip() for column in RUNTIME_COLUMNS}
                payload = {
                    "id": f"{specs[playbook_id]['slug']}-pos-{index:03d}",
                    "playbook_id": playbook_id,
                    "topic": columns["Topic"],
                    "preferred_position": columns["Preferred Position"],
                    "fallback_position": columns["Fallback 1"],
                    "risk": risk_for(row),
                    "keywords": infer_keywords(columns.values()),
                    "columns": columns,
                }
                handle.write(json.dumps(payload) + "\n")

    return {
        "source": str(path),
        "source_rows": len(rows),
        "playbooks": len(ordered_ids),
        "positions": sum(len(grouped[playbook_id]) for playbook_id in ordered_ids),
        "playbooks_file": str(PLAYBOOKS_JSONL),
        "positions_file": str(POSITIONS_JSONL),
    }


def main() -> None:
    print(json.dumps(materialize(), indent=2))


if __name__ == "__main__":
    main()
