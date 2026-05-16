"""Consistent error envelope: {"error": {"code", "message", "details"}}."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException


class LouError(HTTPException):
    def __init__(self, status_code: int, code: str, message: str, details: Any = None):
        body = {"error": {"code": code, "message": message}}
        if details is not None:
            body["error"]["details"] = details
        super().__init__(status_code=status_code, detail=body)
        self.code = code


def invalid_input(message: str, details: Any = None) -> LouError:
    return LouError(422, "INVALID_INPUT", message, details)


def not_found(message: str = "Resource not found") -> LouError:
    return LouError(404, "NOT_FOUND", message)


def forbidden(message: str = "Not authorized for this action") -> LouError:
    return LouError(403, "FORBIDDEN", message)


def upload_too_large(limit_bytes: int) -> LouError:
    return LouError(
        413,
        "UPLOAD_TOO_LARGE",
        f"Upload exceeds the {limit_bytes} byte limit. Set LOU_MAX_UPLOAD_BYTES to increase.",
    )


def unsupported_media(message: str) -> LouError:
    return LouError(415, "UNSUPPORTED_MEDIA", message)


def rate_limited(retry_after_seconds: int) -> LouError:
    err = LouError(
        429,
        "RATE_LIMITED",
        "Too many requests. Retry after a short delay.",
        {"retry_after_seconds": retry_after_seconds},
    )
    err.headers = {"Retry-After": str(retry_after_seconds)}
    return err


def upstream_failure(message: str) -> LouError:
    return LouError(502, "UPSTREAM_FAILURE", message)


def request_timeout(message: str = "Processing timed out.") -> LouError:
    return LouError(504, "REQUEST_TIMEOUT", message)
