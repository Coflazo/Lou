from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, UploadFile

from .. import services
from ..errors import (
    invalid_input,
    not_found,
    unsupported_media,
    upload_too_large,
)
from ..limits import MAX_UPLOAD_BYTES, detect_kind
from ..models import AnalyzeContractRequest


router = APIRouter(tags=["contracts"])
_log = logging.getLogger("lou.contracts")


def _require_playbook(playbook_id: str) -> None:
    if playbook_id not in services.store.playbooks:
        raise not_found("Playbook not found")


async def _read_capped(file: UploadFile) -> bytes:
    content = await file.read()
    if not content:
        raise invalid_input("Upload a non-empty contract.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise upload_too_large(MAX_UPLOAD_BYTES)
    kind = detect_kind(content)
    if kind == "unknown":
        raise unsupported_media("Only text-based PDF or DOCX uploads are accepted.")
    return content


@router.post("/api/contracts/analyze")
def analyze(payload: AnalyzeContractRequest):
    _require_playbook(payload.playbook_id)
    result = services.analyze_contract(payload.playbook_id, payload.name, payload.text)
    _log.info(
        "contract_analyzed",
        extra={
            "playbook_id": payload.playbook_id,
            "contract_name": payload.name,
            "finding_count": len(result.get("findings", [])),
        },
    )
    return result


@router.post("/api/contracts/upload")
async def upload_contract(playbook_id: str = Form(...), file: UploadFile = File(...)):
    _require_playbook(playbook_id)
    content = await _read_capped(file)
    try:
        result = services.analyze_uploaded_contract(playbook_id, file.filename or "contract", content)
    except ValueError as error:
        raise invalid_input(str(error)) from error
    _log.info(
        "contract_uploaded",
        extra={
            "playbook_id": playbook_id,
            "upload_filename": file.filename,
            "upload_bytes": len(content),
            "finding_count": len(result.get("findings", [])),
        },
    )
    return result


@router.post("/api/contracts/review-artifact")
async def review_contract_artifact(playbook_id: str = Form(...), file: UploadFile = File(...)):
    _require_playbook(playbook_id)
    content = await _read_capped(file)
    try:
        response = services.build_contract_review_artifact(
            playbook_id, file.filename or "contract", content,
        )
    except ValueError as error:
        raise invalid_input(str(error)) from error
    _log.info(
        "contract_review_artifact_generated",
        extra={"playbook_id": playbook_id, "upload_filename": file.filename, "upload_bytes": len(content)},
    )
    return response


@router.get("/api/contracts")
def list_contracts():
    return [
        {
            "id": contract.id,
            "playbook_id": contract.playbook_id,
            "name": contract.name,
            "finding_count": len(contract.findings),
            "risk_dominant": (contract.risk_posterior or {}).get("dominant"),
        }
        for contract in services.store.contracts.values()
    ]


@router.get("/api/contracts/{contract_id}")
def get_contract(contract_id: str):
    contract = services.store.contracts.get(contract_id)
    if not contract:
        raise not_found("Contract not found")
    return contract
