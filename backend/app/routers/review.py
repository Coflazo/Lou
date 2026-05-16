from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import ReviewActionRequest, Role
from ..services import approve_proposal, reject_proposal, store
from ._deps import require_role


router = APIRouter(tags=["review"])


@router.get("/api/review")
def list_review_items():
    require_role(Role.SENIOR)
    return [proposal for proposal in store.proposals.values() if proposal.status == "pending"]


@router.post("/api/review/{proposal_id}/approve")
def approve_review_item(proposal_id: str, payload: ReviewActionRequest):
    require_role(Role.SENIOR)
    if proposal_id not in store.proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return approve_proposal(proposal_id, store.current_role, payload.edited_text)


@router.post("/api/review/{proposal_id}/reject")
def reject_review_item(proposal_id: str, payload: ReviewActionRequest):
    require_role(Role.SENIOR)
    if proposal_id not in store.proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return reject_proposal(proposal_id, payload.reason)


@router.get("/api/commits")
def list_commits():
    return list(store.commits.values())
