from __future__ import annotations

from fastapi import APIRouter

from ..models import CommandRequest
from ..services import parse_lou_command


router = APIRouter(tags=["commands"])


@router.post("/api/lou-command")
async def lou_command(payload: CommandRequest):
    return await parse_lou_command(payload.command, payload.playbook_id)
