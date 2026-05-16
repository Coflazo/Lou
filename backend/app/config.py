from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]

for key in ("OPENAI_API_KEY", "SLNG_API_KEY"):
    prefixed = f"LOU_{key}"
    if prefixed not in os.environ and key in os.environ:
        os.environ[prefixed] = os.environ[key]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        env_prefix="LOU_",
        extra="ignore",
    )

    DATABASE_URL: str = f"sqlite:///{ROOT / 'lou.db'}"
    DEMO_DATA_DIR: str = str(ROOT / "demo-data")
    SEED_DEMO_DATA: bool = True

    SECRET_KEY: str = "lou-dev-secret-rotate-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 480

    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    SLNG_API_KEY: str | None = None
    ENABLE_VOICE: bool = True
    VOICE_LANGUAGES: list[str] = Field(default_factory=lambda: ["en", "fr", "nl", "de"])

    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
        ]
    )

    BM25_K1: float = 1.5
    BM25_B: float = 0.75

    CLAUSE_MATCH_MIN_SCORE: float = 0.22
    CLAUSE_MATCH_TOP_K: int = 3

    VOICE_MATCH_THRESHOLD: float = 0.55
    VOICE_MATCH_JARO_WEIGHT: float = 0.4
    VOICE_MATCH_TFIDF_WEIGHT: float = 0.3
    VOICE_MATCH_EDIT_WEIGHT: float = 0.3

    RISK_PRIOR_ALPHA: list[float] = Field(default_factory=lambda: [2.0, 2.0, 2.0])
    RISK_LEVELS: list[str] = Field(default_factory=lambda: ["Low", "Medium", "High"])

    HMM_INIT_INSIDE: float = 0.3
    HMM_INIT_BEGIN: float = 0.7
    HMM_TRANSITION_INSIDE_TO_INSIDE: float = 0.90
    HMM_TRANSITION_BEGIN_TO_BEGIN: float = 0.70

    BRAIN_CACHE_TTL_SECONDS: int = 300

    @field_validator("CORS_ORIGINS", "VOICE_LANGUAGES", "RISK_LEVELS", mode="before")
    @classmethod
    def _split_csv(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("RISK_PRIOR_ALPHA", mode="before")
    @classmethod
    def _split_alpha(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [float(item) for item in value.split(",") if item.strip()]
        return value


settings = Settings()
