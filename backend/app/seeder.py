from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .config import settings
from .models import (
    Commit,
    Contract,
    Playbook,
    PlaybookPosition,
    Proposal,
    ProposalStatus,
    Role,
)


def _iter_jsonl(path: Path) -> Iterable[dict]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def load_playbooks(demo_data_dir: Path) -> dict[str, Playbook]:
    playbooks: dict[str, Playbook] = {}
    for record in _iter_jsonl(demo_data_dir / "playbooks.jsonl"):
        playbook = Playbook(
            id=record["id"],
            slug=record["slug"],
            name=record["name"],
            category=record["category"],
            description=record["description"],
            owner=record["owner"],
            version=record["version"],
            columns=record.get("columns", []),
            positions=[],
        )
        playbooks[playbook.id] = playbook

    for record in _iter_jsonl(demo_data_dir / "playbook_positions.jsonl"):
        position = PlaybookPosition(
            id=record["id"],
            playbook_id=record["playbook_id"],
            topic=record["topic"],
            preferred_position=record["preferred_position"],
            fallback_position=record["fallback_position"],
            risk=record["risk"],
            keywords=record.get("keywords", []),
            columns=record.get("columns", {}),
        )
        playbook = playbooks.get(position.playbook_id)
        if playbook is None:
            continue
        playbook.positions.append(position)

    return playbooks


def load_proposals(demo_data_dir: Path) -> dict[str, Proposal]:
    proposals: dict[str, Proposal] = {}
    for record in _iter_jsonl(demo_data_dir / "proposals.jsonl"):
        proposal = Proposal(
            id=record["id"],
            playbook_id=record["playbook_id"],
            topic=record["topic"],
            source=record["source"],
            proposed_text=record["proposed_text"],
            rationale=record["rationale"],
            status=ProposalStatus(record.get("status", "pending")),
            created_by_role=Role(record.get("created_by_role", "JUNIOR")),
            created_at=record.get("created_at", ""),
        )
        proposals[proposal.id] = proposal
    return proposals


def load_contracts(demo_data_dir: Path) -> dict[str, Contract]:
    contracts: dict[str, Contract] = {}
    for record in _iter_jsonl(demo_data_dir / "contracts.jsonl"):
        contract = Contract(
            id=record["id"],
            playbook_id=record["playbook_id"],
            name=record["name"],
            text=record["text"],
        )
        contracts[contract.id] = contract
    return contracts


def load_commits(demo_data_dir: Path) -> dict[str, Commit]:
    commits: dict[str, Commit] = {}
    for record in _iter_jsonl(demo_data_dir / "commits.jsonl"):
        commit = Commit(
            id=record["id"],
            proposal_id=record["proposal_id"],
            playbook_id=record["playbook_id"],
            message=record["message"],
            author_role=Role(record.get("author_role", "SENIOR")),
            created_at=record.get("created_at", ""),
        )
        commits[commit.id] = commit
    return commits


def load_entities(demo_data_dir: Path) -> list[dict]:
    return list(_iter_jsonl(demo_data_dir / "entities.jsonl"))


def load_relations(demo_data_dir: Path) -> list[dict]:
    return list(_iter_jsonl(demo_data_dir / "relations.jsonl"))


def seed_all() -> dict:
    demo_data_dir = Path(settings.DEMO_DATA_DIR)
    return {
        "playbooks": load_playbooks(demo_data_dir),
        "proposals": load_proposals(demo_data_dir),
        "contracts": load_contracts(demo_data_dir),
        "commits": load_commits(demo_data_dir),
        "entities": load_entities(demo_data_dir),
        "relations": load_relations(demo_data_dir),
    }
