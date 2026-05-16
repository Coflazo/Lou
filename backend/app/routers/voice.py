from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models import VoiceSessionRequest, VoiceTranscriptRequest
from .. import services
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


@router.post("/api/voice/transcribe-audio")
async def create_voice_audio_transcript(
    playbook_id: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
):
    if playbook_id not in store.playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")

    audio = await file.read()
    try:
        return services.transcribe_audio_to_updates(
            playbook_id=playbook_id,
            audio=audio,
            filename=file.filename or "lou-recording.webm",
            content_type=file.content_type,
            language=language,
        )
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
