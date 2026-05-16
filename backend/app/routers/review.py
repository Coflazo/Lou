from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import ProposalCreateRequest, ReviewActionRequest, Role
from ..services import active_role, approve_proposal, create_proposal, reject_proposal, store
from ._deps import require_role


router = APIRouter(tags=["review"])


@router.get("/api/review")
def list_review_items():
    require_role(Role.SENIOR)
    return [proposal for proposal in store.proposals.values() if proposal.status == "pending"]


@router.post("/api/review/proposals")
def create_review_proposal(payload: ProposalCreateRequest):
    if payload.playbook_id not in store.playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return create_proposal(
        playbook_id=payload.playbook_id,
        topic=payload.topic,
        source=payload.source,
        proposed_text=payload.proposed_text,
        rationale=payload.rationale,
        voice_match_scores=payload.voice_match_scores,
        voice_session_id=payload.voice_session_id,
    )


@router.post("/api/review/{proposal_id}/approve")
def approve_review_item(proposal_id: str, payload: ReviewActionRequest):
    require_role(Role.SENIOR)
    if proposal_id not in store.proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return approve_proposal(proposal_id, active_role(), payload.edited_text)


@router.post("/api/review/{proposal_id}/reject")
def reject_review_item(proposal_id: str, payload: ReviewActionRequest):
    require_role(Role.SENIOR)
    if proposal_id not in store.proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return reject_proposal(proposal_id, payload.reason)


@router.get("/api/commits")
def list_commits():
    return list(store.commits.values())
