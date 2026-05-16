from __future__ import annotations

from fastapi import APIRouter

from ..models import LoginRequest
from ..services import store


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
