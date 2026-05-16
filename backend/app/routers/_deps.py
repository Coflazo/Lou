from __future__ import annotations

from fastapi import HTTPException

from ..models import Role
from ..services import role_at_least


def require_role(role: Role) -> None:
    if not role_at_least(role):
        raise HTTPException(status_code=403, detail=f"{role.value} access required")
