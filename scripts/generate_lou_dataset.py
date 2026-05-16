#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from openpyxl import Workbook


ROOT = Path(__file__).resolve().parents[1]
DEMO_DATA = ROOT / "demo-data"
PLAYBOOK_XLSX = DEMO_DATA / "siemens-mutual-nda-playbook.xlsx"
DATASET_JSONL = DEMO_DATA / "lou-pioneer-playbook-datasets-50.jsonl"
PIONEER_REQUEST = DEMO_DATA / "pioneer-playbook-generation-request.json"
PIONEER_RESPONSE = DEMO_DATA / "pioneer-playbook-generation-response.json"
OLD_DATASETS = [
    DEMO_DATA / "lou-clause-classification-280.jsonl",
    DEMO_DATA / "pioneer-generate-request.json",
]
API_KEYS = ROOT / "api-keys.txt"
PIONEER_CHAT_URL = "https://api.pioneer.ai/v1/chat/completions"
DEFAULT_MODEL = "Qwen/Qwen3-8B"
DATASET_COLUMNS = [
    "Topic",
    "Preferred Position",
    "Fallback 1",
    "Fallback 2",
    "Fallback 3",
    "Red Line",
    "Deal Breaker",
]


def load_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    if API_KEYS.exists():
        for line in API_KEYS.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def delete_old_datasets() -> None:
    for path in OLD_DATASETS:
        path.unlink(missing_ok=True)


def build_messages(count: int, batch_index: int, total_batches: int) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "You generate legal playbook dataset records as strict JSON only. "
                "Do not include markdown, commentary, citations, numbering outside JSON, or extra keys."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Generate {count} distinct legal negotiation playbook dataset records for Lou. "
                f"This is batch {batch_index} of {total_batches}; make this batch different from the other batches. "
                "Each record must follow exactly the same pattern and contain exactly these string fields: "
                "Topic, Preferred Position, Fallback 1, Fallback 2, Fallback 3, Red Line, Deal Breaker. "
                "For each record: the Preferred Position must be the ideal legal position; the three fallbacks must "
                "be progressively less preferred but still acceptable; the Red Line must be language requiring escalation; "
                "the Deal Breaker must be a concise unacceptable position. "
                "Use realistic commercial legal playbook topics across NDAs, SaaS, data processing, security, IP, "
                "procurement, AI vendor terms, professional services, and enterprise software. "
                "Keep wording concise, product-ready, and usable in a legal operations workspace. "
                'Return only this JSON shape: {"items":[{...}]}'
            ),
        },
    ]


def pioneer_chat(messages: list[dict[str, str]], model: str, api_key: str) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.8,
        "max_tokens": 4096,
    }
    request = urllib.request.Request(
        PIONEER_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))
    return str(body["choices"][0]["message"]["content"])


def parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def validate_items(items: list[Any]) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []
    seen_topics: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Pioneer returned a non-object dataset item.")
        row = {}
        for column in DATASET_COLUMNS:
            value = item.get(column)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Pioneer returned an item missing {column}.")
            row[column] = value.strip()
        topic_key = row["Topic"].lower()
        if topic_key in seen_topics:
            raise ValueError(f"Pioneer returned a duplicate topic: {row['Topic']}")
        seen_topics.add(topic_key)
        validated.append(row)
    return validated


def generate_with_pioneer(total_count: int, batch_size: int, model: str, api_key: str) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    batches = (total_count + batch_size - 1) // batch_size
    all_rows: list[dict[str, str]] = []
    raw_batches: list[dict[str, Any]] = []
    for batch_index in range(1, batches + 1):
        current_count = min(batch_size, total_count - len(all_rows))
        messages = build_messages(current_count, batch_index, batches)
        content = pioneer_chat(messages, model, api_key)
        parsed = parse_json_object(content)
        rows = validate_items(parsed.get("items", []))
        all_rows.extend(rows)
        raw_batches.append({"batch": batch_index, "messages": messages, "response": parsed})
        time.sleep(0.4)
    return all_rows[:total_count], raw_batches


def write_artifacts(rows: list[dict[str, str]], raw_batches: list[dict[str, Any]], model: str) -> None:
    DEMO_DATA.mkdir(exist_ok=True)

    with DATASET_JSONL.open("w") as file:
        for index, row in enumerate(rows, start=1):
            file.write(json.dumps({"id": f"lou-pioneer-{index:03d}", **row}) + "\n")

    request_artifact = {
        "provider": "pioneer",
        "endpoint": PIONEER_CHAT_URL,
        "model": model,
        "count": len(rows),
        "columns": DATASET_COLUMNS,
        "schema": {"items": [dict.fromkeys(DATASET_COLUMNS, "string")]},
    }
    PIONEER_REQUEST.write_text(json.dumps(request_artifact, indent=2) + "\n")
    PIONEER_RESPONSE.write_text(json.dumps({"batches": raw_batches}, indent=2) + "\n")

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "NDA Playbook"
    sheet.append(DATASET_COLUMNS)
    for row in rows:
        sheet.append([row[column] for column in DATASET_COLUMNS])
    workbook.save(PLAYBOOK_XLSX)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Lou playbook datasets with Pioneer. No local fallback is used.")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    if args.count < 1:
        raise SystemExit("--count must be positive")
    if args.batch_size < 1:
        raise SystemExit("--batch-size must be positive")

    keys = {**load_env_file(), **os.environ}
    api_key = keys.get("PIONEER_API_KEY", "")
    if not api_key:
        raise SystemExit("Missing PIONEER_API_KEY. Refusing to write non-Pioneer fallback data.")

    delete_old_datasets()
    try:
        rows, raw_batches = generate_with_pioneer(args.count, args.batch_size, args.model, api_key)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as error:
        print(f"Pioneer generation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    write_artifacts(rows, raw_batches, args.model)
    print(
        json.dumps(
            {
                "provider": "pioneer",
                "rows": len(rows),
                "dataset": str(DATASET_JSONL),
                "workbook": str(PLAYBOOK_XLSX),
                "request": str(PIONEER_REQUEST),
                "response": str(PIONEER_RESPONSE),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
