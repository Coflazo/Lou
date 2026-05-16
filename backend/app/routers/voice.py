from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import VoiceSessionRequest, VoiceTranscriptRequest
from ..services import store, transcript_to_updates, voice_session


router = APIRouter(tags=["voice"])


@router.post("/api/voice/session")
def create_voice_session(payload: VoiceSessionRequest):
    return voice_session(payload.playbook_id, payload.language)


@router.post("/api/voice/transcript")
def create_voice_transcript(payload: VoiceTranscriptRequest):
    if payload.playbook_id not in store.playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return transcript_to_updates(payload.playbook_id, payload.transcript, payload.language)
