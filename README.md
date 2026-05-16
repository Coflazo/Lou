# Lou

Legal workspace for contract analysis, playbook negotiation, and voice-driven proposal capture.

- FastAPI backend with a typed algorithm registry: TF-IDF clause matching, Dirichlet-Categorical risk posteriors, HMM Viterbi section detection, Jaro-Winkler + edit-distance + TF-IDF voice alignment, BM25 + OpenAI semantic search, PageRank + betweenness + Louvain on the company brain.
- React 18 + TypeScript frontend with a paper-and-ink design system in OKLCH, Instrument Serif display type, DM Mono numerals, Framer Motion springs, Tailwind tokens, TanStack Query, Zustand stores, D3-force graph layout.

## Run

One-terminal launch:

```bash
./scripts/launch_lou.sh
```

The launcher checks tooling, installs Python and Node dependencies, runs backend pytest and frontend Vitest suites, builds the production frontend, starts the FastAPI backend, executes the live smoke pass, and serves the Vite preview build.

Manual:

```bash
# backend
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000

# frontend
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173`.

## Roles

- **JUNIOR** — read playbooks, upload contracts, propose updates.
- **SENIOR** — JUNIOR plus approve / reject proposals, edit positions, publish exports.
- **ADMIN** — SENIOR plus the company brain graph and admin imports.

Role switching is in the sidebar. Each switch issues a fresh demo session against the backend.

## Configuration

All tunable constants live in `backend/app/config.py` as a `pydantic-settings` model. Override with `.env` or `LOU_*` environment variables. The important ones:

| key | default | meaning |
| --- | --- | --- |
| `LOU_SEED_DEMO_DATA` | `true` | seed in-memory store from `demo-data/*.jsonl` on startup |
| `LOU_CLAUSE_MATCH_MIN_SCORE` | `0.22` | TF-IDF cosine threshold for "mapped" vs "unmapped" findings |
| `LOU_VOICE_MATCH_THRESHOLD` | `0.55` | combined Jaro-Winkler + cosine + edit similarity gate for voice matches |
| `LOU_RISK_PRIOR_ALPHA` | `2.0,2.0,2.0` | symmetric Dirichlet prior over Low/Medium/High |
| `LOU_PAGERANK_DAMPING` | `0.85` | brain graph PageRank damping factor |
| `LOU_OPENAI_API_KEY` | unset | enables OpenAI command parsing and dense semantic search fusion |
| `LOU_SLNG_API_KEY` | unset | enables SLNG STT/TTS bridges; absent ⇒ transcript fallback |

## Demo data

All seed records live in `demo-data/*.jsonl` (one JSON object per line). `backend/app/seeder.py` is the idempotent loader. The legacy `siemens-mutual-nda-playbook.xlsx` is no longer required at runtime, but its 50-row schema was the source of the JSONL extraction.

## Tests

```bash
python -m pytest backend/tests/      # 21 tests across algorithms + API flows
cd frontend && npm test               # Vitest unit suite
```
