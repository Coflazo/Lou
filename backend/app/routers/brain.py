from __future__ import annotations

from fastapi import APIRouter

from ..models import Role
from ..services import company_brain
from ._deps import require_role


router = APIRouter(tags=["brain"])


@router.get("/api/company-brain")
def get_company_brain():
    require_role(Role.ADMIN)
    return company_brain()
