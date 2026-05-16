from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "lou.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})


class AppSnapshot(SQLModel, table=True):
    key: str = Field(primary_key=True)
    payload: str
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def write_snapshot(key: str, payload: str) -> None:
    with Session(engine) as session:
        record = session.get(AppSnapshot, key)
        if record is None:
            record = AppSnapshot(key=key, payload=payload)
            session.add(record)
        else:
            record.payload = payload
            record.updated_at = datetime.now(timezone.utc).isoformat()
            session.add(record)
        session.commit()
