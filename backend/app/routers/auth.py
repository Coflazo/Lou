from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import ApiKeyCreateRequest, LoginRequest, Role
from ..services import create_api_key, list_api_keys, revoke_api_key, store
from ._deps import require_role


router = APIRouter(tags=["auth"])


@router.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/api/session/demo-login")
def demo_login(payload: LoginRequest) -> dict[str, str]:
    store.current_role = payload.role
    return {"role": payload.role.value}


@router.get("/api/session/current")
def current_session() -> dict[str, str]:
    return {"role": store.current_role.value}


@router.post("/api/api-keys")
def create_key(payload: ApiKeyCreateRequest):
    require_role(Role.ADMIN)
    try:
        return create_api_key(payload.name, payload.role)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("/api/api-keys")
def list_keys():
    require_role(Role.ADMIN)
    return list_api_keys()


@router.delete("/api/api-keys/{key_id}")
def revoke_key(key_id: str):
    require_role(Role.ADMIN)
    if not revoke_api_key(key_id):
        raise HTTPException(status_code=404, detail="API key not found")
    return {"revoked": key_id}
