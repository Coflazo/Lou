from __future__ import annotations

import os
from contextvars import ContextVar, Token
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderKeys:
    openai: str | None = None
    slng: str | None = None


_provider_keys: ContextVar[ProviderKeys] = ContextVar("provider_keys", default=ProviderKeys())


def set_provider_keys(keys: ProviderKeys) -> Token[ProviderKeys]:
    return _provider_keys.set(keys)


def reset_provider_keys(token: Token[ProviderKeys]) -> None:
    _provider_keys.reset(token)


def current_provider_keys() -> ProviderKeys:
    return _provider_keys.get()


def current_openai_key() -> str | None:
    keys = current_provider_keys()
    return keys.openai or os.getenv("OPENAI_API_KEY") or os.getenv("LOU_OPENAI_API_KEY")


def current_slng_key(settings_value: str | None = None) -> str | None:
    keys = current_provider_keys()
    return keys.slng or settings_value or os.getenv("LOU_SLNG_API_KEY") or os.getenv("SLNG_API_KEY")
