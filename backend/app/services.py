from __future__ import annotations

import io
import json
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from docx import Document
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from pypdf import PdfReader

from .ai import parse_command_with_openai
from .algorithms import (
    BayesianRiskScorer,
    ClauseMatcher,
    CompanyBrainGraph,
    HMMSectionDetector,
    VoiceMatcher,
)
from .algorithms.risk_scoring import RiskObservation
from .config import settings
from .db import init_db, write_snapshot
from .models import (
    Commit,
    Contract,
    ContractFinding,
    FindingStatus,
    Playbook,
    PlaybookPosition,
    Proposal,
    ProposalStatus,
    Role,
)
from .seeder import seed_all


ROLE_RANK = {Role.JUNIOR: 1, Role.SENIOR: 2, Role.ADMIN: 3}
SLNG_STT_MODEL = "slng/deepgram/nova:3-multi"
SLNG_TTS_MODEL = "slng/rime/arcana:3-en"
SLNG_STT_PATH = f"/v1/bridges/unmute/stt/{SLNG_STT_MODEL}"
SLNG_TTS_PATH = f"/v1/bridges/unmute/tts/{SLNG_TTS_MODEL}"


@dataclass
class Store:
    current_role: Role = Role.JUNIOR
    playbooks: dict[str, Playbook] = field(default_factory=dict)
    contracts: dict[str, Contract] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    commits: dict[str, Commit] = field(default_factory=dict)
    entities: list[dict] = field(default_factory=list)
    relations: list[dict] = field(default_factory=list)

    def reset(self) -> None:
        data = seed_all()
        self.current_role = Role.JUNIOR
        self.playbooks = data["playbooks"]
        self.contracts = data["contracts"]
        self.proposals = data["proposals"]
        self.commits = data["commits"]
        self.entities = data["entities"]
        self.relations = data["relations"]


class AlgorithmRegistry:
    """Singleton holding per-playbook fitted matchers and the shared brain graph."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._matchers: dict[str, ClauseMatcher] = {}
        self._brain = CompanyBrainGraph(
            pagerank_damping=settings.PAGERANK_DAMPING,
            pagerank_tolerance=settings.PAGERANK_TOLERANCE,
            pagerank_max_iterations=settings.PAGERANK_MAX_ITERATIONS,
        )
        self._brain.cache_ttl_seconds = float(settings.BRAIN_CACHE_TTL_SECONDS)

    def get_matcher(self, playbook: Playbook) -> ClauseMatcher:
        with self._lock:
            matcher = self._matchers.get(playbook.id)
            if matcher is None:
                matcher = ClauseMatcher(min_score=settings.CLAUSE_MATCH_MIN_SCORE)
                matcher.fit(playbook.positions)
                self._matchers[playbook.id] = matcher
            return matcher

    def invalidate(self, playbook_id: str | None = None) -> None:
        with self._lock:
            if playbook_id is None:
                self._matchers.clear()
            else:
                self._matchers.pop(playbook_id, None)
        self._brain.invalidate()

    def voice_matcher(self, playbook: Playbook) -> VoiceMatcher:
        return VoiceMatcher(
            clause_matcher=self.get_matcher(playbook),
            threshold=settings.VOICE_MATCH_THRESHOLD,
            jaro_weight=settings.VOICE_MATCH_JARO_WEIGHT,
            tfidf_weight=settings.VOICE_MATCH_TFIDF_WEIGHT,
            edit_weight=settings.VOICE_MATCH_EDIT_WEIGHT,
        )

    def risk_scorer(self) -> BayesianRiskScorer:
        return BayesianRiskScorer(
            levels=settings.RISK_LEVELS,
            prior_alpha=settings.RISK_PRIOR_ALPHA,
        )

    def section_detector(self) -> HMMSectionDetector:
        return HMMSectionDetector(
            init_inside=settings.HMM_INIT_INSIDE,
            init_begin=settings.HMM_INIT_BEGIN,
            transition_inside_to_inside=settings.HMM_TRANSITION_INSIDE_TO_INSIDE,
            transition_begin_to_begin=settings.HMM_TRANSITION_BEGIN_TO_BEGIN,
        )

    def brain(self) -> CompanyBrainGraph:
        return self._brain


registry = AlgorithmRegistry()
store = Store()
store.reset()
init_db()


def role_at_least(role: Role) -> bool:
    return ROLE_RANK[store.current_role] >= ROLE_RANK[role]


def summarize_playbook(playbook: Playbook) -> dict[str, Any]:
    return {
        "id": playbook.id,
        "slug": playbook.slug,
        "name": playbook.name,
        "category": playbook.category,
        "description": playbook.description,
        "owner": playbook.owner,
        "version": playbook.version,
        "position_count": len(playbook.positions),
    }


def persist_state() -> None:
    payload = {
        "playbooks": [playbook.model_dump() for playbook in store.playbooks.values()],
        "contracts": [contract.model_dump() for contract in store.contracts.values()],
        "proposals": [proposal.model_dump() for proposal in store.proposals.values()],
        "commits": [commit.model_dump() for commit in store.commits.values()],
    }
    write_snapshot("lou-demo-state", json.dumps(payload))


def _normalize(name: str) -> str:
    return "".join(ch.lower() for ch in name if ch.isalnum())


def _column_value(values: dict[str, str], name: str) -> str:
    normalised = _normalize(name)
    for key, value in values.items():
        if _normalize(key) == normalised:
            return value
    return ""


def _first_column_value(values: dict[str, str], names: list[str]) -> str:
    for name in names:
        value = _column_value(values, name)
        if value:
            return value
    return ""


def _infer_keywords(values: dict[str, str]) -> list[str]:
    text = " ".join(values.values())
    words = re.findall(r"[A-Za-z][A-Za-z-]{4,}", text)
    stop = {"position", "fallback", "preferred", "party", "legal", "terms", "clause", "agreement"}
    seen: list[str] = []
    for word in words:
        lowered = word.lower()
        if lowered in stop or lowered in seen:
            continue
        seen.append(lowered)
        if len(seen) == 8:
            break
    return seen


def sync_position_from_columns(position: PlaybookPosition) -> None:
    position.topic = _column_value(position.columns, "Topic") or position.topic
    position.preferred_position = _column_value(position.columns, "Preferred Position") or position.preferred_position
    position.fallback_position = _first_column_value(
        position.columns, ["Fallback Position", "Fallback 1", "Fallback"]
    ) or position.fallback_position
    position.risk = _first_column_value(position.columns, ["Risk", "Red Line", "Deal Breaker"]) or position.risk or "Medium"
    keywords = _first_column_value(position.columns, ["Keywords"])
    if keywords:
        position.keywords = [item.strip().lower() for item in keywords.split(";") if item.strip()]
    elif not position.keywords:
        position.keywords = _infer_keywords(position.columns)


def update_playbook_position(playbook_id: str, position_id: str, columns: dict[str, str]) -> PlaybookPosition:
    playbook = store.playbooks[playbook_id]
    position = next((item for item in playbook.positions if item.id == position_id), None)
    if position is None:
        raise KeyError(position_id)

    allowed_columns = set(playbook.columns)
    position.columns = {column: str(columns.get(column, position.columns.get(column, ""))) for column in playbook.columns}
    for column, value in columns.items():
        if column in allowed_columns:
            continue
        position.columns[column] = str(value)
        playbook.columns.append(column)

    sync_position_from_columns(position)
    playbook.version += 1
    registry.invalidate(playbook_id)
    persist_state()
    return position


def split_clauses(text: str) -> list[str]:
    raw = re.split(r"(?<=[.;:!?])\s+|\n+", text.strip())
    clauses = [item.strip() for item in raw if len(item.strip()) > 12]
    return clauses or [text.strip()]


def split_paragraphs(text: str) -> list[str]:
    return [chunk.strip() for chunk in re.split(r"\n{2,}", text) if chunk.strip()]


def sectionize_text(text: str) -> list[dict[str, Any]]:
    detector = registry.section_detector()
    paragraphs = split_paragraphs(text)
    if not paragraphs:
        return []
    sections = detector.segment(paragraphs)

    payload: list[dict[str, Any]] = []
    cursor = 0
    for section in sections:
        start = text.find(section.text, cursor)
        if start < 0:
            start = cursor
        end = start + len(section.text)
        payload.append(
            {
                "id": f"section-{section.index}",
                "title": section.title or f"Section {section.index}",
                "text": section.text,
                "start": start,
                "end": end,
            }
        )
        cursor = end
    return payload


def location_for(text: str, excerpt: str, sections: list[dict[str, Any]]) -> str:
    pos = text.find(excerpt)
    if pos < 0:
        return "Unlocated clause"
    for section in sections:
        if section["start"] <= pos < section["end"]:
            return section["title"]
    return f"Section near char {pos}"


def build_highlights(contract: Contract) -> list[dict[str, Any]]:
    highlights = []
    search_from = 0
    for finding in contract.findings:
        start = contract.text.find(finding.excerpt, search_from)
        if start < 0:
            start = contract.text.find(finding.excerpt)
        if start < 0:
            continue
        end = start + len(finding.excerpt)
        finding.start = start
        finding.end = end
        search_from = end
        highlights.append(
            {
                "id": f"hl-{finding.id}",
                "finding_id": finding.id,
                "status": finding.status.value,
                "topic": finding.topic,
                "start": start,
                "end": end,
                "excerpt": finding.excerpt,
                "risk": finding.risk,
            }
        )
    return highlights


def create_proposal(
    playbook_id: str,
    topic: str,
    source: str,
    proposed_text: str,
    rationale: str,
    voice_match_scores: dict | None = None,
    voice_session_id: str | None = None,
) -> Proposal:
    proposal = Proposal(
        id=f"prop-{uuid.uuid4().hex[:10]}",
        playbook_id=playbook_id,
        topic=topic,
        source=source,
        proposed_text=proposed_text,
        rationale=rationale,
        created_by_role=store.current_role,
        voice_match_scores=voice_match_scores,
        voice_session_id=voice_session_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    store.proposals[proposal.id] = proposal
    return proposal


def _find_position(playbook: Playbook, position_id: str) -> PlaybookPosition | None:
    return next((item for item in playbook.positions if item.id == position_id), None)


def analyze_contract(
    playbook_id: str,
    name: str,
    text: str,
    sections: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    playbook = store.playbooks[playbook_id]
    matcher = registry.get_matcher(playbook)
    risk_scorer = registry.risk_scorer()

    contract = Contract(
        id=f"con-{uuid.uuid4().hex[:10]}",
        playbook_id=playbook_id,
        name=name,
        text=text,
        sections=sections or sectionize_text(text),
    )
    proposed_updates: list[Proposal] = []
    observations: list[RiskObservation] = []

    for index, clause in enumerate(split_clauses(text), start=1):
        match = matcher.best_match(clause)
        if match is not None:
            position = _find_position(playbook, match.position_id)
            finding = ContractFinding(
                id=f"find-{uuid.uuid4().hex[:10]}",
                contract_id=contract.id,
                playbook_position_id=match.position_id,
                topic=match.topic,
                excerpt=clause,
                status=FindingStatus.MAPPED,
                risk=position.risk if position else "Medium",
                location=location_for(text, clause, contract.sections),
                recommendation=position.preferred_position if position else "",
                match_score=match.score,
                match_method=match.method,
            )
            observations.append(RiskObservation(risk_label=finding.risk, weight=match.score))
        else:
            topic = infer_topic(clause)
            risk_label = "High" if re.search(r"non-solicit|penalty|perpetual|unlimited", clause, re.IGNORECASE) else "Medium"
            finding = ContractFinding(
                id=f"find-{uuid.uuid4().hex[:10]}",
                contract_id=contract.id,
                playbook_position_id=None,
                topic=topic,
                excerpt=clause,
                status=FindingStatus.UNMAPPED,
                risk=risk_label,
                location=f"Unmapped clause {index}",
                recommendation="No playbook position matched. Propose guidance before treating this clause as acceptable.",
                match_score=0.0,
                match_method="unmapped",
            )
            observations.append(RiskObservation(risk_label=risk_label, weight=0.5))
            proposed_updates.append(
                create_proposal(
                    playbook_id=playbook_id,
                    topic=topic,
                    source="contract",
                    proposed_text=f"Create guidance for {topic}: {clause[:200]}",
                    rationale="Contract analysis found language outside the current playbook coverage.",
                )
            )
        contract.findings.append(finding)

    contract.highlights = build_highlights(contract)
    posterior = risk_scorer.score(observations)
    contract.risk_posterior = posterior.to_dict()
    store.contracts[contract.id] = contract
    persist_state()
    return {
        "contract": contract,
        "sections": contract.sections,
        "findings": contract.findings,
        "highlights": contract.highlights,
        "risk_posterior": contract.risk_posterior,
        "proposed_updates": proposed_updates,
        "review_suggestions": review_suggestions(contract),
    }


def review_suggestions(contract: Contract) -> list[dict[str, str]]:
    suggestions = []
    for finding in contract.findings:
        if finding.status == FindingStatus.MAPPED:
            suggestions.append(
                {
                    "finding_id": finding.id,
                    "title": f"{finding.topic} is covered",
                    "body": f"Confirm the clause tracks the preferred position (match {finding.match_score:.2f}).",
                }
            )
        else:
            suggestions.append(
                {
                    "finding_id": finding.id,
                    "title": f"Add guidance for {finding.topic}",
                    "body": "Route this clause to the review queue before treating it as approved.",
                }
            )
    return suggestions


def extract_pdf_document(filename: str, content: bytes) -> tuple[str, list[dict[str, Any]]]:
    reader = PdfReader(io.BytesIO(content))
    sections = []
    parts = []
    cursor = 0
    for index, page in enumerate(reader.pages, start=1):
        page_text = (page.extract_text() or "").strip()
        if not page_text:
            continue
        if parts:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(page_text)
        cursor += len(page_text)
        sections.append({"id": f"page-{index}", "title": f"Page {index}", "text": page_text, "start": start, "end": cursor})
    text = "".join(parts).strip()
    if not text:
        raise ValueError(f"{filename} has no extractable text. Scanned-image OCR is not supported in this build.")
    return text, sections


def extract_docx_document(filename: str, content: bytes) -> tuple[str, list[dict[str, Any]]]:
    document = Document(io.BytesIO(content))
    paragraphs = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    sections = []
    parts = []
    cursor = 0
    for index, paragraph in enumerate(paragraphs, start=1):
        if parts:
            parts.append("\n\n")
            cursor += 2
        start = cursor
        parts.append(paragraph)
        cursor += len(paragraph)
        sections.append({"id": f"section-{index}", "title": f"Section {index}", "text": paragraph, "start": start, "end": cursor})
    text = "".join(parts).strip()
    if not text:
        raise ValueError(f"{filename} has no extractable text.")
    return text, sections


def analyze_uploaded_contract(playbook_id: str, filename: str, content: bytes) -> dict[str, Any]:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        text, sections = extract_pdf_document(filename, content)
    elif lower.endswith(".docx"):
        text, sections = extract_docx_document(filename, content)
    else:
        raise ValueError("Upload a text-based PDF or DOCX contract.")
    return analyze_contract(playbook_id, filename, text, sections)


def infer_topic(text: str) -> str:
    lower = text.lower()
    if "non-solicit" in lower or "employee" in lower:
        return "Expanded Non-Solicit"
    if "residual" in lower:
        return "Residual Knowledge"
    if "archival" in lower:
        return "Archival Retention"
    words = [word.title() for word in re.findall(r"[A-Za-z][A-Za-z-]{4,}", text)[:3]]
    return " ".join(words) or "Unmapped Clause"


def normalize_language(language: str) -> str:
    languages = set(settings.VOICE_LANGUAGES)
    return language if language in languages else "en"


def voice_session(playbook_id: str | None, language: str = "en") -> dict[str, Any]:
    api_key_present = bool(settings.SLNG_API_KEY)
    selected_language = normalize_language(language)
    return {
        "provider": "SLNG",
        "mode": "live" if api_key_present else "transcript-fallback",
        "playbook_id": playbook_id,
        "language": selected_language,
        "supported_languages": sorted(set(settings.VOICE_LANGUAGES)),
        "stt": {
            "model": SLNG_STT_MODEL,
            "http_url": f"https://api.slng.ai{SLNG_STT_PATH}",
            "websocket_url": f"wss://api.slng.ai{SLNG_STT_PATH}",
            "request": {
                "language": selected_language,
                "punctuate": True,
                "smart_format": True,
                "utterances": True,
                "keywords": ["confidentiality", "residual knowledge", "non-solicit", "data protection"],
            },
        },
        "tts": {
            "model": SLNG_TTS_MODEL,
            "http_url": f"https://api.slng.ai{SLNG_TTS_PATH}",
            "websocket_url": f"wss://api.slng.ai{SLNG_TTS_PATH}",
            "request": {
                "speaker": "luna",
                "text": "Lou is listening for proposed playbook updates.",
                "audioFormat": "audio/wav",
                "sample_rate": 24000,
                "speed": 1,
            },
        },
        "auth_note": "Browser WebSocket clients cannot set Authorization headers; proxy through the backend or pass a short-lived token as a query parameter.",
        "api_key_present": api_key_present,
    }


def transcript_to_updates(playbook_id: str, transcript: str, language: str = "en") -> dict[str, Any]:
    playbook = store.playbooks[playbook_id]
    voice_matcher = registry.voice_matcher(playbook)
    candidates = [(position.id, position.topic, position.preferred_position) for position in playbook.positions]
    sentences = split_clauses(transcript) or [transcript.strip()]
    proposals: list[Proposal] = []

    for sentence in sentences:
        if not sentence:
            continue
        matches = voice_matcher.match(sentence, candidates, top_k=3)
        match_scores = [
            {
                "position_id": match.position_id,
                "topic": match.topic,
                "score": match.score,
                "jaro": match.jaro,
                "tfidf": match.tfidf,
                "edit": match.edit,
            }
            for match in matches
        ]
        topic = matches[0].topic if matches else infer_topic(sentence)
        proposals.append(
            create_proposal(
                playbook_id=playbook_id,
                topic=topic,
                source="voice",
                proposed_text=f"Discussion note: {sentence[:220]}",
                rationale="Captured from listening-mode transcript.",
                voice_match_scores={"matches": match_scores},
            )
        )

    if not proposals:
        proposals.append(
            create_proposal(
                playbook_id=playbook_id,
                topic="Meeting Follow-up",
                source="voice",
                proposed_text=f"Review transcript for possible playbook impact: {transcript[:220]}",
                rationale="Listening mode captured a legal discussion without a direct playbook match.",
            )
        )

    persist_state()
    return {
        "mode": "transcript-fallback",
        "language": normalize_language(language),
        "proposed_updates": proposals,
    }


def approve_proposal(proposal_id: str, author_role: Role, edited_text: str | None = None) -> dict[str, Any]:
    proposal = store.proposals[proposal_id]
    if edited_text:
        proposal.proposed_text = edited_text
    proposal.status = ProposalStatus.APPROVED
    commit = Commit(
        id=f"commit-{uuid.uuid4().hex[:8]}",
        proposal_id=proposal.id,
        playbook_id=proposal.playbook_id,
        message=f"Approved {proposal.topic}",
        author_role=author_role,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    store.commits[commit.id] = commit
    playbook = store.playbooks[proposal.playbook_id]
    playbook.version += 1
    registry.invalidate(proposal.playbook_id)
    persist_state()
    return {"proposal": proposal, "commit": commit}


def reject_proposal(proposal_id: str, reason: str | None) -> Proposal:
    proposal = store.proposals[proposal_id]
    proposal.status = ProposalStatus.REJECTED
    if reason:
        proposal.rationale = f"{proposal.rationale} Rejected: {reason}"
    persist_state()
    return proposal


def graph_for_playbook(playbook: Playbook) -> dict[str, Any]:
    """Render a hierarchical Playbook -> Topic -> P1/F1/R/X graph with proposal + commit overlays."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    topic_ids: dict[str, str] = {}

    nodes.append(
        {
            "id": playbook.id,
            "label": playbook.name,
            "kind": "playbook",
            "summary": "Playbook",
            "group": playbook.id,
            "x": 360.0,
            "y": 44.0,
        }
    )

    topic_count = max(len(playbook.positions), 1)
    columns = min(7, topic_count)
    rows = (topic_count + columns - 1) // columns
    x_gap = 600 / max(columns - 1, 1) if columns > 1 else 0
    y_gap = 156 / max(rows - 1, 1) if rows > 1 else 0

    for index, position in enumerate(playbook.positions, start=1):
        topic_id = f"topic-{position.id}"
        preferred_id = f"{position.id}-p1"
        fallback_id = f"{position.id}-f1"
        rationale_id = f"{position.id}-r"
        exception_id = f"{position.id}-x"
        topic_ids[position.topic.lower()] = topic_id

        row = (index - 1) // columns
        column = (index - 1) % columns
        x = 60 + column * x_gap
        y = 132 + row * y_gap
        direction = 1 if row % 2 == 0 else -1

        nodes.append(
            {
                "id": topic_id,
                "label": position.topic,
                "kind": "topic",
                "summary": _short_summary(position.topic),
                "group": topic_id,
                "order": index,
                "x": x,
                "y": y,
            }
        )
        nodes.append(
            {
                "id": preferred_id,
                "label": "P1",
                "kind": "preferred",
                "summary": position.preferred_position,
                "group": topic_id,
                "order": index,
                "x": x,
                "y": y + direction * 28,
            }
        )
        nodes.append(
            {
                "id": fallback_id,
                "label": "F1",
                "kind": "fallback",
                "summary": position.fallback_position,
                "group": topic_id,
                "order": index,
                "x": x,
                "y": y + direction * 56,
            }
        )
        nodes.append(
            {
                "id": rationale_id,
                "label": "R",
                "kind": "rationale",
                "summary": f"Escalation level: {position.risk}",
                "group": topic_id,
                "order": index,
                "x": x,
                "y": y + direction * 84,
                "risk": position.risk,
            }
        )
        if position.keywords:
            nodes.append(
                {
                    "id": exception_id,
                    "label": "X",
                    "kind": "exception",
                    "summary": ", ".join(position.keywords[:3]),
                    "group": topic_id,
                    "order": index,
                    "x": x,
                    "y": y + direction * 112,
                }
            )

        edges.append({"source": playbook.id, "target": topic_id, "kind": "hierarchy", "label": "topic"})
        edges.append({"source": topic_id, "target": preferred_id, "kind": "hierarchy", "label": "preferred"})
        edges.append({"source": preferred_id, "target": fallback_id, "kind": "hierarchy", "label": "fallback"})
        edges.append({"source": fallback_id, "target": rationale_id, "kind": "hierarchy", "label": "rationale"})
        if position.keywords:
            edges.append({"source": rationale_id, "target": exception_id, "kind": "hierarchy", "label": "terms"})

    for source, target, strength in _topic_relation_edges(playbook):
        edges.append(
            {
                "source": f"topic-{source.id}",
                "target": f"topic-{target.id}",
                "kind": "topic_relation",
                "label": "related",
                "strength": strength,
            }
        )

    for proposal in store.proposals.values():
        if proposal.playbook_id != playbook.id:
            continue
        parent = topic_ids.get(proposal.topic.lower(), playbook.id)
        parent_node = next((node for node in nodes if node["id"] == parent), None)
        base_x = parent_node["x"] if parent_node else 360
        base_y = parent_node["y"] if parent_node else 250
        nodes.append(
            {
                "id": proposal.id,
                "label": proposal.topic[:24],
                "kind": "proposal",
                "summary": proposal.status.value,
                "group": parent,
                "x": min(680, base_x + 34),
                "y": max(36, min(326, base_y + 34)),
            }
        )
        edges.append({"source": parent, "target": proposal.id, "kind": "hierarchy", "label": "proposed"})

    for commit in store.commits.values():
        if commit.playbook_id != playbook.id:
            continue
        proposal = store.proposals.get(commit.proposal_id)
        parent = topic_ids.get((proposal.topic if proposal else "").lower(), playbook.id)
        parent_node = next((node for node in nodes if node["id"] == parent), None)
        base_x = parent_node["x"] if parent_node else 360
        base_y = parent_node["y"] if parent_node else 280
        nodes.append(
            {
                "id": commit.id,
                "label": "Published",
                "kind": "commit",
                "summary": commit.message,
                "group": parent,
                "x": min(680, base_x + 60),
                "y": max(36, min(326, base_y + 60)),
            }
        )
        edges.append({"source": commit.proposal_id, "target": commit.id, "kind": "hierarchy", "label": "approved"})

    for node in nodes:
        node["x"] = round(float(node["x"]), 2)
        node["y"] = round(float(node["y"]), 2)

    return {"nodes": nodes, "edges": edges}


def _short_summary(topic: str) -> str:
    words = re.findall(r"[A-Za-z][A-Za-z-]+", topic)
    stop = {"of", "and", "or", "the", "for", "to"}
    selected = [word for word in words if word.lower() not in stop][:3]
    return " ".join(selected) or topic[:32]


def _topic_relation_edges(playbook: Playbook) -> list[tuple[PlaybookPosition, PlaybookPosition, float]]:
    relations = []
    positions = playbook.positions
    for index, source in enumerate(positions):
        source_terms = set(source.keywords) | {
            word.lower() for word in re.findall(r"[A-Za-z][A-Za-z-]{4,}", source.topic)
        }
        for target in positions[index + 1 :]:
            target_terms = set(target.keywords) | {
                word.lower() for word in re.findall(r"[A-Za-z][A-Za-z-]{4,}", target.topic)
            }
            overlap = source_terms & target_terms
            if overlap:
                denominator = max(min(len(source_terms), len(target_terms)), 1)
                strength = round(min(1.0, len(overlap) / denominator), 2)
                relations.append((source, target, strength))
    if not relations and len(positions) >= 2:
        relations.append((positions[0], positions[1], 0.2))
    return sorted(relations, key=lambda item: item[2], reverse=True)[:24]


def company_brain() -> dict[str, Any]:
    entities = list(store.entities)
    relations = list(store.relations)
    if not entities:
        return {"nodes": [], "edges": [], "metrics": {"node_count": 0, "edge_count": 0, "communities": 0, "modularity": 0.0, "density": 0.0}}
    snapshot = registry.brain().compute(entities, relations)
    return {"nodes": snapshot.nodes, "edges": snapshot.edges, "metrics": snapshot.metrics}


def export_json() -> StreamingResponse:
    payload = {
        "playbooks": [playbook.model_dump() for playbook in store.playbooks.values()],
        "proposals": [proposal.model_dump() for proposal in store.proposals.values()],
        "commits": [commit.model_dump() for commit in store.commits.values()],
    }
    content = json.dumps(payload, indent=2)
    return StreamingResponse(io.BytesIO(content.encode("utf-8")), media_type="application/json")


def export_xlsx() -> StreamingResponse:
    wb = Workbook()
    ws = wb.active
    ws.title = "Playbook Positions"
    for playbook in store.playbooks.values():
        columns = ["Playbook", "Version", *playbook.columns]
        ws.append(columns)
        for position in playbook.positions:
            ws.append([playbook.name, playbook.version, *[position.columns.get(column, "") for column in playbook.columns]])
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=lou-playbooks.xlsx"},
    )


def export_png_placeholder() -> StreamingResponse:
    data = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000a49444154789c6360000002000100ffff03000006000557bfab0000000049454e44ae426082"
    )
    return StreamingResponse(io.BytesIO(data), media_type="image/png")


async def parse_lou_command(command: str, playbook_id: str | None) -> dict[str, Any]:
    try:
        ai_result = parse_command_with_openai(command)
    except Exception:
        ai_result = None
    if ai_result:
        intent = str(ai_result.get("intent") or "note")
        return {"intent": intent, "playbook_id": playbook_id, "message": command_message(intent)}

    lower = command.lower()
    if "approve" in lower:
        return {"intent": "approve", "message": command_message("approve")}
    if "export" in lower:
        return {"intent": "export", "message": command_message("export")}
    if "analyze" in lower or "review" in lower:
        return {"intent": "analyze_contract", "message": command_message("analyze_contract")}
    return {"intent": "note", "playbook_id": playbook_id, "message": command_message("note")}


def command_message(intent: str) -> str:
    messages = {
        "approve": "Open the review queue and approve the matching proposal.",
        "reject": "Open the review queue and reject the matching proposal.",
        "export": "Open exports for JSON, XLSX, or graph image.",
        "analyze_contract": "Upload a contract to start review.",
        "open_playbook": "Open the playbook workspace.",
        "note": "Saved as a workspace note.",
    }
    return messages.get(intent, messages["note"])
