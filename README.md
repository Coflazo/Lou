<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/lou-wordmark-on-dark.png">
    <img alt="Lou" src="frontend/public/lou-wordmark-on-light.png" height="64">
  </picture>
</p>

<p align="center">
  AI legal workspace for contract review, playbook negotiation, and voice-driven proposal capture.
</p>

<p align="center">
  Built for the <strong>{Tech: Europe} Paris AI Hackathon</strong>.
</p>

## What Lou Does

Lou helps legal teams turn contract review into controlled legal memory.

A junior reviewer can upload a contract, map clauses against the company playbook, see risk and uncertainty, and propose updates. A senior lawyer can approve, reject, edit, export, and publish those changes back into the playbook. Voice notes and meeting transcripts can also become proposed playbook updates, so negotiation knowledge does not disappear after the call.

The first version of this idea was only a proof of concept from an earlier event. It got early signal from Siemens Legal Operations and Legora. This repository is a from-zero rebuild for this hackathon: new backend, new frontend, new data layer, new algorithms, new design system, and a full demo workflow.

## Demo Walkthrough

Use this path for a 2-minute judge demo:

1. Log in as **Junior** and open one of the generated legal playbooks.
2. Upload or analyze a contract.
3. Show mapped clauses, unmapped clauses, risk badges, and the Bayesian risk posterior.
4. Open voice mode, paste or record a legal discussion, and generate proposed playbook updates.
5. Switch to **Senior**, review a proposal, approve it, and show the commit.
6. Switch to **Admin** and show Company Brain: playbooks as the top-level legal memory, with each playbook opening into its own mini-brain.

## Hackathon Partner Technologies

Lou uses hackathon partner technologies in the core product path:

| Partner | How Lou Uses It |
| --- | --- |
| **Pioneer by Fastino** | Generated the 50-record legal playbook dataset. Each record includes one preferred position, three fallbacks, one red line, and one deal breaker. Lou materializes those rows into 9 runtime playbooks across NDA, DPA/privacy, SaaS, AI vendor, security, IP licensing, procurement, services, and software. |
| **SLNG** | Powers the intended live voice path for STT/TTS. When `LOU_SLNG_API_KEY` is not set, Lou still runs in transcript fallback mode so judges can test the workflow without external credentials. |
| **OpenAI** | Optional command parsing and dense semantic search fusion. Lou falls back to deterministic local behavior when `LOU_OPENAI_API_KEY` is absent. |

## Product Surface

- **Playbooks**: structured negotiation positions, fallbacks, red lines, deal breakers, and edit flow.
- **Contracts**: upload/analyze text, PDF, or DOCX contracts against the selected playbook.
- **Findings**: mapped and unmapped clauses with location, recommendation, risk, and match score.
- **Review**: senior approval queue for playbook updates.
- **Voice**: live voice-session contract plus transcript fallback for meeting-derived proposals.
- **Company Brain**: graph view of teams, vendors, policies, clauses, and their relationships.
- **Exports**: JSON, XLSX, and graph-image placeholder routes for review artifacts.

## Technical Architecture

### Backend

- Python 3.13
- FastAPI
- SQLModel-style data models for the demo state
- Pydantic Settings for configuration
- JSONL seed data in `demo-data/`
- Eight FastAPI routers:
  - `auth`
  - `playbooks`
  - `contracts`
  - `voice`
  - `review`
  - `exports`
  - `brain`
  - `commands`

The backend is centered around an `AlgorithmRegistry` that owns fitted playbook matchers, risk scorers, section detectors, voice matchers, and graph metrics.

### Algorithms

Lou uses local, inspectable algorithms so the demo is not just a wrapper around an LLM:

| Module | Purpose |
| --- | --- |
| `clause_matching.py` | TF-IDF sparse vectors and cosine similarity to map contract clauses to playbook positions. |
| `risk_scoring.py` | Dirichlet-Categorical Bayesian posterior with 95% credible intervals for contract-level risk. |
| `section_detector.py` | HMM Viterbi decoding in log-space to segment legal text into sections. |
| `voice_matching.py` | Jaro-Winkler, edit distance, and TF-IDF matching to connect transcripts to playbook topics. |
| `semantic_search.py` | BM25 plus optional OpenAI embeddings, fused with reciprocal rank fusion. |
| `company_brain.py` | Recursive `.mm`-style mind-map JSON for a readable Company Brain view. |

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- Framer Motion
- TanStack Query
- Zustand
- D3 Force
- React Dropzone

The UI has a custom design system in `frontend/src/design-system/`: OKLCH color tokens, Instrument Serif display type, DM Mono data labels, geometric spacing, and motion presets.

## Run Locally

### Terminal Launch

```bash
./scripts/launch_lou.sh
```

The launcher checks local tools, installs Python and Node dependencies, runs backend tests, runs frontend tests, builds the production frontend, starts the backend, runs live smoke checks, and serves the Vite preview build.

Open:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

If a port is already in use:

```bash
BACKEND_PORT=8010 FRONTEND_PORT=5180 ./scripts/launch_lou.sh
```

### Manual Development

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Demo Roles

- **JUNIOR**: read playbooks, analyze contracts, use listening mode, and submit proposed updates.
- **SENIOR**: Junior permissions plus review approvals, playbook edits, commits, and exports.
- **ADMIN**: Senior permissions plus Company Brain and admin import access.

Role switching is available in the app sidebar. Each switch updates the demo session on the backend.

## Configuration

All tunable constants live in `backend/app/config.py` as a `pydantic-settings` model. Override values through `.env` or `LOU_*` environment variables.

| Variable | Default | Meaning |
| --- | --- | --- |
| `LOU_SEED_DEMO_DATA` | `true` | Seed the in-memory store from `demo-data/*.jsonl`. |
| `LOU_CLAUSE_MATCH_MIN_SCORE` | `0.22` | TF-IDF cosine threshold for mapped findings. |
| `LOU_VOICE_MATCH_THRESHOLD` | `0.55` | Voice-to-playbook matching threshold. |
| `LOU_RISK_PRIOR_ALPHA` | `2.0,2.0,2.0` | Dirichlet prior for Low, Medium, High risk. |
| `LOU_OPENAI_API_KEY` | unset | Enables OpenAI command parsing and dense semantic search. |
| `LOU_SLNG_API_KEY` | unset | Enables live SLNG voice integrations. |

## API Overview

| Area | Routes |
| --- | --- |
| Health | `GET /api/health` |
| Session | `POST /api/session/demo-login` |
| Playbooks | `GET /api/playbooks`, `GET /api/playbooks/{id}`, `PATCH /api/playbooks/{id}/positions/{position_id}` |
| Contracts | `GET /api/contracts`, `POST /api/contracts/analyze`, `POST /api/contracts/upload`, `GET /api/contracts/{id}` |
| Voice | `POST /api/voice/session`, `POST /api/voice/transcript` |
| Review | `GET /api/review`, `POST /api/review/{id}/approve`, `POST /api/review/{id}/reject` |
| Company Brain | `GET /api/company-brain`, `GET /api/playbooks/{id}/brain` |
| Export | `GET /api/export/json`, `GET /api/export/xlsx`, `GET /api/export/png` |
| Commands | `POST /api/lou-command` |

## Demo Data

All runtime seed data lives in `demo-data/*.jsonl`, one JSON object per line:

- `playbooks.jsonl`
- `playbook_positions.jsonl`
- `contracts.jsonl`
- `proposals.jsonl`
- `commits.jsonl`
- `entities.jsonl`
- `relations.jsonl`

`demo-data/lou-pioneer-playbook-datasets-50.jsonl` is the Pioneer source dataset. `scripts/materialize_runtime_playbooks.py` converts it into the runtime `playbooks.jsonl` and `playbook_positions.jsonl` files used by the app. The workbook files are kept as review artifacts and are not required at runtime.

### Generate 50 Pioneer Playbooks

To generate a larger Pioneer matrix with 50 distinct playbooks and 50 rows per playbook, add your Pioneer key to `api-keys.txt`:

```bash
PIONEER_API_KEY=your_key_here
```

Then run:

```bash
python3 scripts/generate_lou_playbook_matrix.py --playbooks 50 --rows-per-playbook 50 --batch-size 5
```

This makes 2,500 total playbook rows. Playbook specifications are requested in smaller batches by default to avoid oversized Pioneer responses. If Pioneer still returns malformed JSON, rerun with a smaller spec batch:

```bash
python3 scripts/generate_lou_playbook_matrix.py --playbooks 50 --rows-per-playbook 50 --batch-size 5 --spec-batch-size 5
```

The generator writes:

- `demo-data/lou-pioneer-playbook-matrix-50x50.jsonl`
- `demo-data/lou-pioneer-playbook-matrix-50x50.xlsx`
- `demo-data/pioneer-playbook-matrix-request.json`
- `demo-data/pioneer-playbook-matrix-response.json`
- `demo-data/siemens-mutual-nda-playbook.xlsx`

For a faster validation run, keep 50 playbooks but lower the row count:

```bash
python3 scripts/generate_lou_playbook_matrix.py --playbooks 50 --rows-per-playbook 10 --batch-size 5
```

## Tests

Backend:

```bash
source .venv/bin/activate
python -m pytest backend/tests/
```

Frontend:

```bash
cd frontend
npm test
npm run build
```

Live smoke checks:

```bash
python scripts/smoke_lou.py http://localhost:8000
```

## Repository Map

```text
backend/app/              FastAPI app, routers, services, models, algorithms
backend/tests/            Backend flow and algorithm tests
frontend/src/             React app, design system, pages, components, hooks
demo-data/                Pioneer-generated and runtime JSONL seed data
scripts/                  Launch, smoke test, and dataset generation scripts
cli/                      Small local CLI entrypoint
```

## Submission Notes

- This project was built newly for the hackathon. An earlier event version existed only as a proof of concept; this repo is the rebuilt product.
- The repository is structured for jury review: setup instructions, partner technology usage, API overview, test commands, and architecture notes are included here.
- The app runs without paid API keys by using deterministic fallbacks and transcript mode. Adding `LOU_OPENAI_API_KEY` or `LOU_SLNG_API_KEY` unlocks the external integrations.
