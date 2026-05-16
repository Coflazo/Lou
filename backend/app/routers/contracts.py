from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models import AnalyzeContractRequest
from ..services import analyze_contract, analyze_uploaded_contract, store


router = APIRouter(tags=["contracts"])


@router.post("/api/contracts/analyze")
def analyze(payload: AnalyzeContractRequest):
    if payload.playbook_id not in store.playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return analyze_contract(payload.playbook_id, payload.name, payload.text)


@router.post("/api/contracts/upload")
async def upload_contract(playbook_id: str = Form(...), file: UploadFile = File(...)):
    if playbook_id not in store.playbooks:
        raise HTTPException(status_code=404, detail="Playbook not found")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Upload a non-empty PDF or DOCX contract.")
    try:
        return analyze_uploaded_contract(playbook_id, file.filename or "contract", content)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


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
        for contract in store.contracts.values()
    ]


@router.get("/api/contracts/{contract_id}")
def get_contract(contract_id: str):
    contract = store.contracts.get(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract
