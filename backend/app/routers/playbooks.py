from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import PlaybookPositionUpdateRequest, Role
from ..services import (
    graph_for_playbook,
    persist_state,
    store,
    summarize_playbook,
    update_playbook_position,
)
from ._deps import require_role


router = APIRouter(tags=["playbooks"])


@router.get("/api/playbooks")
def list_playbooks():
    return [summarize_playbook(playbook) for playbook in store.playbooks.values()]


@router.post("/api/playbooks/import")
def import_playbooks():
    require_role(Role.ADMIN)
    store.reset()
    persist_state()
    return {"imported": sum(len(playbook.positions) for playbook in store.playbooks.values())}


@router.get("/api/playbooks/{playbook_id}")
def get_playbook(playbook_id: str):
    playbook = store.playbooks.get(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return playbook


@router.patch("/api/playbooks/{playbook_id}/positions/{position_id}")
def update_position(playbook_id: str, position_id: str, payload: PlaybookPositionUpdateRequest):
    require_role(Role.SENIOR)
    playbook = store.playbooks.get(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    try:
        return update_playbook_position(playbook_id, position_id, payload.columns)
    except KeyError:
        raise HTTPException(status_code=404, detail="Position not found") from None


@router.get("/api/playbooks/{playbook_id}/brain")
def get_playbook_brain(playbook_id: str):
    playbook = store.playbooks.get(playbook_id)
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return graph_for_playbook(playbook)
