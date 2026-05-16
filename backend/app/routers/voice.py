from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, UploadFile

from ..errors import invalid_input, not_found, upload_too_large, upstream_failure
from ..limits import MAX_AUDIO_BYTES
from ..models import VoiceContractRequest, VoiceSessionRequest, VoiceTranscriptRequest
from .. import services
from ..services import store, transcript_to_updates, voice_session


router = APIRouter(tags=["voice"])
_log = logging.getLogger("lou.voice")


@router.post("/api/voice/session")
def create_voice_session(payload: VoiceSessionRequest):
    return voice_session(payload.playbook_id, payload.language)


@router.post("/api/voice/transcript")
def create_voice_transcript(payload: VoiceTranscriptRequest):
    if payload.playbook_id not in store.playbooks:
        raise not_found("Playbook not found")
    response = transcript_to_updates(payload.playbook_id, payload.transcript, payload.language)
    _log.info(
        "voice_transcript_processed",
        extra={
            "playbook_id": payload.playbook_id,
            "language": payload.language,
            "proposed_updates": len(response.get("proposed_updates", [])),
            "fallback": True,
        },
    )
    return response


@router.post("/api/voice/contract-from-notes")
def create_contract_from_voice_notes(payload: VoiceContractRequest):
    if payload.playbook_id not in store.playbooks:
        raise not_found("Playbook not found")
    try:
        return services.contract_from_voice_notes(payload.playbook_id, payload.transcript, payload.language)
    except ValueError as error:
        raise invalid_input(str(error)) from error


@router.post("/api/voice/audio-transcript")
@router.post("/api/voice/transcribe-audio")
async def create_voice_audio_transcript(
    playbook_id: str = Form(...),
    language: str = Form("en"),
    file: UploadFile = File(...),
):
    if playbook_id not in store.playbooks:
        raise not_found("Playbook not found")

    audio = await file.read()
    if not audio:
        raise invalid_input("Recorded audio was empty.")
    if len(audio) > MAX_AUDIO_BYTES:
        raise upload_too_large(MAX_AUDIO_BYTES)
    try:
        response = services.transcribe_audio_to_updates(
            playbook_id=playbook_id,
            audio=audio,
            filename=file.filename or "lou-recording.webm",
            content_type=file.content_type,
            language=language,
        )
    except ValueError as error:
        raise upstream_failure(str(error)) from error
    _log.info(
        "voice_audio_transcribed",
        extra={
            "playbook_id": playbook_id,
            "language": language,
            "audio_bytes": len(audio),
            "segments": len(response.get("speaker_segments", [])),
        },
    )
    return response
