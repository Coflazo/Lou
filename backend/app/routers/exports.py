from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models import Role
from ..services import export_json, export_png_placeholder, export_xlsx
from ._deps import require_role


router = APIRouter(tags=["exports"])


@router.get("/api/export/{format_name}")
def export(format_name: str):
    require_role(Role.SENIOR)
    if format_name == "json":
        return export_json()
    if format_name == "xlsx":
        return export_xlsx()
    if format_name == "png":
        return export_png_placeholder()
    raise HTTPException(status_code=404, detail="Unknown export format")
