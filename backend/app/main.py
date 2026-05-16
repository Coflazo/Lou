from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .routers import ROUTERS
from .services import reset_request_role, role_for_api_key, set_request_role


app = FastAPI(title="Lou Legal Workspace", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def apply_api_key_role(request: Request, call_next):
    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    context_token = None
    if token:
        role = role_for_api_key(token)
        if role is None:
            return JSONResponse(status_code=401, content={"detail": "Invalid Lou API key"})
        context_token = set_request_role(role)
    try:
        return await call_next(request)
    finally:
        if context_token is not None:
            reset_request_role(context_token)


for router in ROUTERS:
    app.include_router(router)
