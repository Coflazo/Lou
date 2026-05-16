# Lou Backend

FastAPI demo service for Lou's role-aware legal workspace.

Run locally:

```bash
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

Optional environment:

```bash
OPENAI_API_KEY=...
SLNG_API_KEY=...
```

Without `SLNG_API_KEY`, voice mode returns transcript fallback metadata and still creates proposed playbook updates.
Without `OPENAI_API_KEY`, command parsing and clause mapping use deterministic local fallbacks.

State snapshots are written to `backend/lou.db` with SQLModel so the demo has a simple SQLite audit surface.
