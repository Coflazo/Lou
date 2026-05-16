from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import SQLModel


class Role(StrEnum):
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    ADMIN = "ADMIN"


class ProposalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class FindingStatus(StrEnum):
    MAPPED = "mapped"
    UNMAPPED = "unmapped"


class PlaybookPosition(SQLModel):
    id: str
    playbook_id: str
    topic: str
    preferred_position: str
    fallback_position: str
    risk: str
    keywords: list[str] = Field(default_factory=list)
    columns: dict[str, str] = Field(default_factory=dict)


class Playbook(SQLModel):
    id: str
    slug: str
    name: str
    category: str
    description: str
    owner: str
    version: int
    columns: list[str] = Field(default_factory=list)
    positions: list[PlaybookPosition] = Field(default_factory=list)


class ContractFinding(SQLModel):
    id: str
    contract_id: str
    playbook_position_id: Optional[str]
    topic: str
    excerpt: str
    status: FindingStatus
    risk: str
    location: str
    recommendation: str
    start: Optional[int] = None
    end: Optional[int] = None
    match_score: Optional[float] = None
    match_method: Optional[str] = None


class Contract(SQLModel):
    id: str
    playbook_id: str
    name: str
    text: str
    findings: list[ContractFinding] = Field(default_factory=list)
    sections: list[dict] = Field(default_factory=list)
    highlights: list[dict] = Field(default_factory=list)
    risk_posterior: Optional[dict] = None


class Proposal(SQLModel):
    id: str
    playbook_id: str
    topic: str
    source: str
    proposed_text: str
    rationale: str
    status: ProposalStatus = ProposalStatus.PENDING
    created_by_role: Role = Role.JUNIOR
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    voice_match_scores: Optional[dict] = None
    voice_session_id: Optional[str] = None


class Commit(SQLModel):
    id: str
    proposal_id: str
    playbook_id: str
    message: str
    author_role: Role
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class LoginRequest(BaseModel):
    role: Role


class AnalyzeContractRequest(BaseModel):
    playbook_id: str
    name: str
    text: str


class PlaybookPositionUpdateRequest(BaseModel):
    columns: dict[str, str]


class VoiceTranscriptRequest(BaseModel):
    playbook_id: str
    transcript: str
    language: str = "en"


class ReviewActionRequest(BaseModel):
    edited_text: Optional[str] = None
    reason: Optional[str] = None


class CommandRequest(BaseModel):
    command: str
    playbook_id: Optional[str] = None


class VoiceSessionRequest(BaseModel):
    playbook_id: Optional[str] = None
    language: str = "en"
