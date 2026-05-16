from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .errors import LouError, rate_limited, upload_too_large
from .limits import MAX_UPLOAD_BYTES
from .logging_config import configure_logging, set_request_id
from .provider_keys import ProviderKeys, reset_provider_keys, set_provider_keys
from .rate_limit import rate_limiter
from .routers import ROUTERS
from .services import reset_request_role, role_for_api_key, set_request_role


configure_logging()

_DEFAULT_SECRET_KEY = "lou-dev-secret-rotate-in-production"
_log = logging.getLogger("lou")
if settings.SECRET_KEY == _DEFAULT_SECRET_KEY:
    _log.warning("SECRET_KEY is using the development default. Set LOU_SECRET_KEY in production.")


app = FastAPI(title="Lou Legal Workspace", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_UPLOAD_ROUTES = (
    "/api/contracts/upload",
    "/api/contracts/review-artifact",
    "/api/voice/audio-transcript",
    "/api/voice/transcribe-audio",
)


@app.exception_handler(LouError)
async def lou_error_handler(_request: Request, exc: LouError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=getattr(exc, "headers", None),
    )


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    set_request_id(request_id)

    content_length = request.headers.get("content-length")
    if request.url.path in _UPLOAD_ROUTES and content_length:
        try:
            if int(content_length) > MAX_UPLOAD_BYTES:
                err = upload_too_large(MAX_UPLOAD_BYTES)
                return JSONResponse(status_code=err.status_code, content=err.detail)
        except ValueError:
            pass

    bucket_key = request.headers.get("authorization") or (
        request.client.host if request.client else "anon"
    )
    allowed, retry_after = rate_limiter.check(bucket_key)
    if not allowed:
        err = rate_limited(retry_after)
        return JSONResponse(
            status_code=err.status_code,
            content=err.detail,
            headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
        )

    header = request.headers.get("authorization", "")
    token = header[7:].strip() if header.lower().startswith("bearer ") else ""
    context_token = None
    provider_token = None
    if token:
        role = role_for_api_key(token)
        if role is None:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "INVALID_API_KEY", "message": "Invalid Lou API key"}},
                headers={"X-Request-ID": request_id},
            )
        context_token = set_request_role(role)
    openai_key = request.headers.get("x-lou-openai-key")
    slng_key = request.headers.get("x-lou-slng-key")
    if openai_key or slng_key:
        provider_token = set_provider_keys(ProviderKeys(openai=openai_key, slng=slng_key))
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    finally:
        if provider_token is not None:
            reset_provider_keys(provider_token)
        if context_token is not None:
            reset_request_role(context_token)


for router in ROUTERS:
    app.include_router(router)
