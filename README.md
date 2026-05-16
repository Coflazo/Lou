<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/lou-wordmark-on-dark.png">
    <img alt="Lou" src="frontend/public/lou-wordmark-on-light.png" height="64">
  </picture>
</p>

<p align="center">
  <strong>Controlled legal memory for contracts, playbooks, voice notes, and approvals.</strong>
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@lou-ai/cli"><img alt="npm" src="https://img.shields.io/badge/npm-%40lou--ai%2Fcli-CB3837?logo=npm&logoColor=white"></a>
  <a href="#tests-and-verification"><img alt="tests" src="https://img.shields.io/badge/tests-63%20passing-3d6f58"></a>
  <a href="#license"><img alt="license" src="https://img.shields.io/badge/license-MIT-111314"></a>
</p>

---

## Table of contents

1. [Problem statement](#problem-statement)
2. [What Lou does](#what-lou-does)
3. [Live tour of the product](#live-tour-of-the-product)
4. [Architecture at a glance](#architecture-at-a-glance)
5. [Algorithms](#algorithms)
6. [How SLNG is used](#how-slng-is-used)
7. [How Pioneer (by Fastino) is used](#how-pioneer-by-fastino-is-used)
8. [Quick start](#quick-start)
9. [Install the npm CLI](#install-the-npm-cli)
10. [Run locally](#run-locally)
11. [Full CLI reference](#full-cli-reference)
12. [REST API](#rest-api)
13. [Mobile and responsive behavior](#mobile-and-responsive-behavior)
14. [Production hardening and configuration](#production-hardening-and-configuration)
15. [Datasets and demo contracts](#datasets-and-demo-contracts)
16. [Repository structure](#repository-structure)
17. [Tests and verification](#tests-and-verification)
18. [Roadmap](#roadmap)
19. [Credits](#credits)
20. [License](#license)

---

## Problem statement

Legal knowledge is scattered. Negotiation positions live in redlines, partner
emails, Slack threads, sales calls, and individual lawyers' memories. By the
time a junior counsel needs to negotiate the same clause again, the institutional
answer is gone, half-remembered, or stuck in someone's drafts folder.

The result:

- Junior lawyers re-argue settled positions every quarter.
- Senior counsel review the same redlines over and over.
- Approved guidance never makes it back into the playbook.
- Voice decisions from live calls evaporate.
- Compliance teams cannot prove what stance was approved, when, and by whom.

## What Lou does

Lou turns those scattered signals into **controlled legal memory**:

1. A junior lawyer uploads a contract (PDF or DOCX). Lou segments it, maps
   each clause to a playbook position, and surfaces unmapped clauses as
   proposed updates.
2. During a negotiation call, Lou can listen (SLNG live STT) or accept a pasted
   transcript and convert decisions into review-ready proposals.
3. Senior counsel works the review queue: approve, reject, edit, or commit
   proposals back into the playbook.
4. The Company Brain shows the evolving graph of playbooks, topics, commits,
   entities, and relationships so legal operations can see what the company
   actually believes about every clause.
5. Exports give downstream teams JSON, XLSX, or PNG snapshots.
6. Everything is also driveable from a terminal with the `@lou-ai/cli` npm
   package, so CI, audits, and integrations have the same surface as the UI.

Three roles gate the workflow:

| Role | Reads | Writes | Admin |
|------|-------|--------|-------|
| **Junior counsel** | playbooks, contracts, voice transcripts, mind map | propose updates, upload contracts | — |
| **Senior counsel** | everything Junior reads | edit positions, approve/reject/commit, export | — |
| **Legal operations / Admin** | everything | import playbooks, manage API keys | Company Brain |

## Live tour of the product

| Surface | What it does |
|---------|--------------|
| **Login** | Pick a demo role (Junior / Senior / Admin) and enter the workspace. |
| **Dashboard** | Active playbooks, positions, contract count, review queue size, voice entry, commit history. |
| **Playbooks** | All 50 playbooks with categories, positions, fallback ladders, red lines, deal breakers. Senior can edit positions inline. |
| **Contracts** | Upload a PDF/DOCX, see HMM-segmented sections, mapped/unmapped findings, Bayesian risk posture with credible intervals, click-to-highlight inside the document. |
| **Voice session** | Live SLNG listening or pasted transcript → voice-matched proposals → "Send to review". On phones, a **Fullscreen** toggle opens an immersive listening view tuned for live negotiations. |
| **Review queue** | Senior approves / rejects / edits / commits. Hotkeys `A` approves, `R` rejects. |
| **Company Brain** | SVG mind-map: playbooks → topics → preferred / fallback / red-line / deal-breaker leaves. Admin only. |
| **Exports** | JSON, XLSX, and PNG one-click downloads. |
| **Command bar** | Natural-language router: "approve the latest proposal", "export the playbook", "open the SaaS playbook". |

## Architecture at a glance

```
┌──────────────┐      ┌─────────────────────────────┐
│   Browser    │◀────▶│  React + Vite + TypeScript  │
│  Mobile/Web  │      │  (frontend/)                │
└──────────────┘      └─────────────────────────────┘
                                  │
                                  │ HTTP/JSON, FormData uploads
                                  ▼
┌──────────────┐      ┌─────────────────────────────┐
│  npm CLI     │◀────▶│  FastAPI + SQLModel + SQLite│
│ @lou-ai/cli  │      │  (backend/app/)             │
└──────────────┘      └─────────────────────────────┘
                                  │
        ┌──────────────────┬──────┴──────┬──────────────────┐
        ▼                  ▼             ▼                  ▼
   Clause matcher    Section HMM   Risk Bayes        Voice matcher
   (TF-IDF cosine)   (Viterbi)     (Dirichlet–Cat.)  (Jaro+TFIDF+Edit)
        │                                                   │
        └─────────────┐                            ┌────────┘
                      ▼                            ▼
                 ┌──────────────────────────────────────┐
                 │  Optional providers (request-scoped) │
                 │  • OpenAI for command routing +      │
                 │    contract drafting from notes      │
                 │  • SLNG for live STT + TTS + audio   │
                 │    upload transcription              │
                 └──────────────────────────────────────┘
```

- **Stateless per request.** The backend reads provider keys from request
  headers (`X-Lou-OpenAI-Key`, `X-Lou-SLNG-Key`) or environment, never persists
  them.
- **Deterministic fallback.** Every AI path has a deterministic fallback so the
  demo and tests run with zero external credentials.
- **One backend, three clients.** Web, CLI, and any HTTP integration share the
  same API and error envelope.

## Algorithms

All algorithm tunables live in [`backend/app/algorithms.yaml`](backend/app/algorithms.yaml)
and are loaded at startup by [`backend/app/algorithm_config.py`](backend/app/algorithm_config.py).
Override the path with `LOU_ALGORITHM_CONFIG_PATH`.

| Algorithm | What it does | Implementation |
|-----------|--------------|----------------|
| **Clause matching** | TF-IDF cosine similarity between contract clauses and playbook positions. | `backend/app/algorithms/clause_matching.py` |
| **HMM section detection** | Viterbi decoding in log-space over a 7-dimensional paragraph feature vector (relative position, numbering, all-caps ratio, average word length, log word count, ends-with-colon, section-keyword score). | `backend/app/algorithms/section_detector.py` |
| **Bayesian risk scoring** | Dirichlet–Categorical posterior over Low/Medium/High with 95% credible intervals. | `backend/app/algorithms/risk_scoring.py` |
| **Voice matching** | Hybrid Jaro-Winkler + TF-IDF + normalized edit distance with configurable weights and a threshold. | `backend/app/algorithms/voice_matching.py` |
| **Semantic search** | BM25 Okapi (k1=1.5, b=0.75) with optional OpenAI embeddings fused via reciprocal rank. | `backend/app/algorithms/semantic_search.py` |
| **Company Brain** | Deterministic mind-map builder with TTL cache. | `backend/app/algorithms/company_brain.py` |

## How SLNG is used

[**SLNG**](https://slng.ai) provides the voice infrastructure that turns live
contract negotiations into review-ready proposals.

Lou uses SLNG in three places, all gated behind a request-scoped API key:

1. **Voice session config** — `POST /api/voice/session` returns the SLNG STT and
   TTS endpoints, the model IDs (`deepgram/nova:3`, `slng/rime/arcana:3-en`),
   keyword bias list, and the language picker (en / fr / nl / de). The browser
   uses this metadata to drive a live listening UI. When no SLNG key is
   configured the same endpoint returns `mode: "transcript-fallback"` so the UI
   degrades gracefully.

2. **Audio upload transcription** — `POST /api/voice/audio-transcript`
   accepts a recorded blob (typically `audio/webm;codecs=opus` from a phone's
   microphone), forwards it to SLNG's STT HTTP endpoint with bearer auth, and
   returns diarized speaker segments plus a voice-matched proposal list.

3. **Pasted-transcript fallback** — `POST /api/voice/transcript` runs the same
   voice matcher on a text transcript so users without an SLNG key can still
   capture decisions from a call.

Configuration:

```bash
LOU_SLNG_API_KEY=slng_xxxxx     # required for live STT
LOU_SLNG_API_BASE_HTTP=https://api.slng.ai
LOU_SLNG_STT_MODEL=deepgram/nova:3
LOU_SLNG_TTS_MODEL=slng/rime/arcana:3-en
LOU_SLNG_TTS_SPEAKER=luna
LOU_SLNG_STT_KEYWORDS="confidentiality, residual knowledge, non-solicit, data protection"
```

For the npm CLI, end users can also pass their own SLNG key via
`lou configure --slng-key slng_xxxxx`. The key is forwarded to the backend as
the `X-Lou-SLNG-Key` header on a single request and never stored server-side.

## How Pioneer (by Fastino) is used

[**Pioneer by Fastino**](https://fastino.ai) generated the seed legal dataset
that powers Lou's playbooks. Pioneer's chat completion API was used in two
passes:

1. **Playbook seed generation** — [`scripts/generate_lou_dataset.py`](scripts/generate_lou_dataset.py)
   posts 50 prompts to Pioneer (model `Qwen/Qwen3-8B`), one per playbook topic,
   each requesting a row with: Topic, Preferred Position, Fallback 1–3, Red
   Line, Deal Breaker. The result lives at
   `demo-data/lou-pioneer-playbook-datasets-50.jsonl`. The Pioneer request and
   response payloads are checked in alongside it for auditability:
   `demo-data/pioneer-playbook-generation-request.json` and
   `demo-data/pioneer-playbook-generation-response.json`.

2. **Position matrix expansion** — [`scripts/generate_lou_playbook_matrix.py`](scripts/generate_lou_playbook_matrix.py)
   then expands each of the 50 playbooks into 50 positions, producing the
   2,500-row matrix at `demo-data/lou-pioneer-playbook-matrix-50x50.jsonl`
   (also rendered as XLSX). Recovery logic retries when Pioneer returns empty
   rows and falls back to a curated topic list rather than fabricating data.

3. **Runtime materialization** — [`scripts/materialize_runtime_playbooks.py`](scripts/materialize_runtime_playbooks.py)
   converts the Pioneer output into the two runtime JSONL files the backend
   loads on startup: `demo-data/playbooks.jsonl` and
   `demo-data/playbook_positions.jsonl`.

Configuration:

```bash
PIONEER_API_KEY=pio_sk_xxxxx
LOU_PIONEER_BASE=https://api.pioneer.ai
```

Generated Pioneer artifacts are **review artifacts**, not hidden product logic
— they are checked into the repo so you can audit exactly what prompt was sent
and what came back.

## Quick start

```bash
git clone https://github.com/Coflazo/Lou.git
cd Lou
./scripts/launch_lou.sh
```

That single script:

- Creates a Python 3.13 virtualenv and installs `backend/requirements.txt`.
- Installs frontend dependencies.
- Materializes Pioneer playbooks into runtime JSONL (idempotent — skips if the
  dataset already exists).
- Runs the backend test suite.
- Runs the frontend test suite.
- Builds the production frontend bundle.
- Starts the FastAPI backend on port `8000` (override with `BACKEND_PORT`).
- Runs the live smoke test against the backend.
- Starts the frontend preview on port `5173` (override with `FRONTEND_PORT`).
- Keeps both processes alive until you `Ctrl+C`.

Then open:

```text
Frontend:  http://localhost:5173
Backend:   http://localhost:8000
API docs:  http://localhost:8000/docs
```

If a port is already in use:

```bash
BACKEND_PORT=8010 FRONTEND_PORT=5180 ./scripts/launch_lou.sh
```

To reuse an already-running backend or frontend:

```bash
LOU_REUSE_RUNNING=1 ./scripts/launch_lou.sh
```

## Install the npm CLI

> [!IMPORTANT]
> **The npm CLI is production-ready and waiting on a one-time publish.**
> The package at `packages/lou-cli/` is fully built, fully tested (11 Vitest
> specs green), `npm pack --dry-run` clean, and carries complete metadata
> (license, repository, bugs, keywords, `publishConfig.access=public`). The
> only blocker for `npm install -g @lou-ai/cli` is reserving the **`@lou-ai`
> org** on npm — free, ~30 seconds at
> [npmjs.com/org/create](https://www.npmjs.com/org/create) (pick the
> "Unlimited public packages" free plan). After that, run from the repo root:
>
> ```bash
> cd packages/lou-cli && npm login && npm publish
> ```
>
> Until then, install directly from the repo with:
>
> ```bash
> cd packages/lou-cli && npm pack && npm install -g ./lou-ai-cli-0.1.0.tgz
> ```

Once published, install globally:

```bash
npm install -g @lou-ai/cli
```

Verify it:

```bash
lou --json status
```

Or, without a global install:

```bash
npx @lou-ai/cli status
```

Configure once per machine:

```bash
lou configure \
  --api-base http://localhost:8000 \
  --api-key  lou_xxxxx
```

For self-hosted backends you can also store provider keys locally:

```bash
lou configure --openai-key sk-... --slng-key slng_...
```

Provider keys are forwarded **only to localhost** by default. To send them to
a remote Lou backend you must opt in explicitly:

```bash
lou configure --allow-provider-key-forwarding
```

The CLI writes `~/.lou/config.json` with owner-only (`0600`) permissions and
warns if the file's permissions look loose.

## Run locally

If you would rather run the pieces by hand instead of using `launch_lou.sh`:

### 1. Backend (FastAPI)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend is now live at `http://127.0.0.1:8000`, with OpenAPI docs at
`/docs` and ReDoc at `/redoc`.

### 2. Frontend (React + Vite)

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Vite serves the dev build on `http://127.0.0.1:5173` and proxies `/api/*` to
the backend.

### 3. npm CLI from source

```bash
npm --prefix packages/lou-cli install
npm --prefix packages/lou-cli run build
node packages/lou-cli/dist/bin/lou.js status
```

### 4. Optional secrets

Drop credentials into `api-keys.txt` at the repo root (already gitignored):

```
OPENAI_API_KEY=sk-...
SLNG_API_KEY=slng_...
PIONEER_API_KEY=pio_sk_...
```

`launch_lou.sh` reads this file and exports the values **only into the backend
process** — never into the frontend build or test runners.

## Full CLI reference

Every browser feature has a CLI equivalent.

```bash
# session and health
lou status
lou login --role senior            # demo role switch (Junior | Senior | Admin)

# playbooks
lou playbooks                                                          # list
lou playbooks show pb-01-nda-negotiation-and-enforcement-playbook      # detail
lou playbooks import                                                   # admin only — reset from runtime data
lou edit pb-01-... --position pos-id --set "Preferred Position=Updated text"

# contracts
lou contracts list
lou contracts show contract-id
lou review-contract "demo-data/generated-contract-pdfs-50x50/PB01 - …Contract 01… .pdf" \
  --playbook pb-01-nda-negotiation-and-enforcement-playbook
# Writes lou-review/<contract-stem>/{review.json, annotated.pdf|docx}.

# review queue
lou review                                                            # list pending
lou review approve prop-id
lou review reject prop-id
lou review submit --playbook pb-01-… --topic "Scope" --text "Updated stance"
lou commit prop-id          # alias of approve
lou push prop-id            # alias of approve

# voice
lou voice transcript --playbook pb-01-… --language en --text "...notes..."
lou voice transcribe ./recording.webm --playbook pb-01-… --language en
lou voice session --playbook pb-01-… --language en

# company brain (admin)
lou brain

# exports
lou export json
lou export xlsx
lou export png

# API key management (admin)
lou keys list
lou keys create --name ci-bot --role SENIOR
lou keys revoke key-id
lou keys use lou_xxxxx           # saves to ~/.lou/config.json

# natural-language command bar
lou command "export the playbook"
lou command "approve the latest proposal"
```

Global flags work on every command:

| Flag | Effect |
|------|--------|
| `--json` | Print raw JSON instead of human summaries (scripts, CI, integrations) |
| `--verbose` / `-v` | Log HTTP method + URL of every request to stderr (no headers, no body) |
| `--timeout <ms>` | Per-request timeout via `AbortController` (default 60_000) |
| `--base-url <url>` | Override `apiBase` for one command |
| `--api-key <token>` | Override `apiKey` for one command |

Configuration precedence (highest wins): command-line flag → environment
(`LOU_API_BASE`, `LOU_API_KEY`, `LOU_OPENAI_API_KEY`, `LOU_SLNG_API_KEY`,
`LOU_ALLOW_PROVIDER_KEY_FORWARDING`) → `~/.lou/config.json`.

The legacy Python CLI at `cli/lou.py` is kept as a compatibility shim and
prints a deprecation banner when invoked interactively. New work should use
`@lou-ai/cli`.

## REST API

The backend exposes a small REST surface that the web app, the CLI, and any
HTTP integration share. All errors use a single envelope:

```json
{ "error": { "code": "UPLOAD_TOO_LARGE", "message": "...", "details": { ... } } }
```

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/api/health` | Liveness probe |
| POST   | `/api/session/demo-login` | Demo role switch (`JUNIOR` / `SENIOR` / `ADMIN`) |
| GET    | `/api/playbooks` | List playbooks |
| GET    | `/api/playbooks/{id}` | Playbook detail |
| POST   | `/api/playbooks/import` | Reset runtime store from demo data (admin) |
| PATCH  | `/api/playbooks/{id}/positions/{position_id}` | Edit playbook columns (senior) |
| GET    | `/api/playbooks/{id}/brain` | Mind-map graph for one playbook |
| POST   | `/api/contracts/analyze` | Analyze contract from raw text |
| POST   | `/api/contracts/upload` | Upload PDF/DOCX, return findings |
| POST   | `/api/contracts/review-artifact` | Upload PDF/DOCX, return ZIP with annotated doc + `review.json` |
| GET    | `/api/contracts` | List analyzed contracts |
| GET    | `/api/contracts/{id}` | Contract detail |
| GET    | `/api/review` | Pending proposals (senior) |
| POST   | `/api/review/proposals` | Submit a new proposal |
| POST   | `/api/review/{id}/approve` | Approve and commit |
| POST   | `/api/review/{id}/reject` | Reject |
| GET    | `/api/commits` | Commit history |
| POST   | `/api/voice/session` | Voice session metadata (SLNG endpoints + fallback flag) |
| POST   | `/api/voice/transcript` | Run voice matcher on pasted transcript |
| POST   | `/api/voice/audio-transcript` | Upload audio, transcribe with SLNG, return proposals |
| POST   | `/api/voice/contract-from-notes` | Draft a contract from voice notes (OpenAI) |
| GET    | `/api/company-brain` | Full mind-map (admin) |
| GET    | `/api/export/{json\|xlsx\|png}` | Streaming snapshot |
| POST   | `/api/lou-command` | Natural-language intent routing |
| POST   | `/api/api-keys` | Create API key (admin) |
| GET    | `/api/api-keys` | List API keys (admin) |
| DELETE | `/api/api-keys/{id}` | Revoke API key (admin) |

Authentication: `Authorization: Bearer lou_xxxxx`. Per-request provider keys go
in `X-Lou-OpenAI-Key` and `X-Lou-SLNG-Key`; they are scoped to a single request
and never persisted server-side.

Full interactive docs: `http://localhost:8000/docs` (Swagger UI) and `/redoc`.

## Mobile and responsive behavior

Lou is fully responsive on phone, tablet, and desktop. The interesting parts:

- **Sidebar** collapses below the `md` breakpoint into a slide-in drawer
  triggered by a hamburger button. ESC, scrim click, or navigating to a new
  route all close the drawer. Drawer animation uses a spring (stiffness 280,
  damping 26).
- **Command bar** in the TopBar becomes a full-width sheet on mobile,
  triggered by a search icon.
- **SplitPane** has a `collapseAt={"sm" | "md" | "lg"}` prop and stacks
  vertically below the chosen breakpoint. `ContractAnalysis` and
  `PlaybookDetail` use it.
- **ContractList** switches from a 3-column table to stacked cards on mobile.
- **Voice session fullscreen.** On screens narrower than 768px the Voice page
  exposes a `Fullscreen` button. Tapping it opens a Portal-mounted overlay
  with:
  - sticky top bar (live status pulse + language + exit icon),
  - centered voice orb,
  - scrollable transcript taking the middle,
  - sticky bottom row with language picker, Listen / Stop, and Send-to-playbook.
  ESC exits. Body scroll is locked while the overlay is open.
- **Min tap targets.** Sidebar nav, role pills, mobile icon buttons, and Select
  triggers all hit at least 44×44 px.
- **Accessibility.** Interactive `FindingCard`s expose `aria-expanded` and
  keyboard activation; `VoiceOrb`, waveform, and `RiskPosteriorBar` carry
  `role="img"` + descriptive labels; `Select` advertises `aria-haspopup` and
  `aria-expanded`; disabled buttons use `opacity-50 saturate-50` to meet WCAG
  AA contrast.

## Production hardening and configuration

Notable production-grade hardening built into the backend:

- **Upload size cap.** `LOU_MAX_UPLOAD_BYTES` (default 50 MB). Enforced on
  `Content-Length` before the body is read and again after read, returning
  `413 UPLOAD_TOO_LARGE`.
- **Audio cap.** `LOU_MAX_AUDIO_BYTES` (default 30 MB).
- **PDF page cap.** `LOU_MAX_PDF_PAGES` (default 300).
- **DOCX paragraph cap.** `LOU_MAX_DOCX_PARAGRAPHS` (default 10 000).
- **DOCX zip-bomb guard.** Uncompressed/compressed ratio is checked against
  `LOU_DOCX_MAX_COMPRESSION_RATIO` (default 100×) before parsing.
- **Magic-byte checks.** Uploads are sniffed for `%PDF-` or `PK\x03\x04` before
  the parser dispatches; unknown types return `415 UNSUPPORTED_MEDIA`.
- **Token-bucket rate limit.** Per-bearer (or per-IP) bucket sized to
  `LOU_RATE_LIMIT_PER_MINUTE` (default 600 / about 10 req/s sustained), with
  `Retry-After`. `/api/health` and `/api/session/demo-login` are exempt so
  liveness probes and role switches never drain the bucket. Single-process
  only — swap for Redis if you scale horizontally.
- **Structured JSON logging.** `backend/app/logging_config.py` emits one JSON
  object per log line with a `request_id` correlation token; every response
  carries `X-Request-ID`.
- **Standard error envelope.** `{"error": {"code", "message", "details"}}`
  across every endpoint. Codes: `INVALID_INPUT`, `NOT_FOUND`, `FORBIDDEN`,
  `RATE_LIMITED`, `UPLOAD_TOO_LARGE`, `UNSUPPORTED_MEDIA`, `UPSTREAM_FAILURE`,
  `REQUEST_TIMEOUT`.
- **Request-scoped provider keys.** `X-Lou-OpenAI-Key` and `X-Lou-SLNG-Key` are
  carried in `contextvars`, reset at the end of every request, and never
  written to disk or logs.
- **Algorithm tunables externalized.** `backend/app/algorithms.yaml` is loaded
  at startup; override path via `LOU_ALGORITHM_CONFIG_PATH`.
- **SECRET_KEY warning.** Backend logs a `WARNING` at startup when the demo
  default secret is in use.
- **`api-keys.txt`** is gitignored. `scripts/launch_lou.sh` injects its values
  only into the backend process, never into frontend builds or test runners.

### Environment variables (selected)

| Variable | Default | Purpose |
|----------|---------|---------|
| `LOU_API_BASE` | `http://localhost:8000` | CLI default backend URL |
| `LOU_SECRET_KEY` | `lou-dev-secret-rotate-in-production` | JWT signing secret (rotate in prod!) |
| `LOU_CORS_ORIGINS` | `localhost:5173,…` | Comma-separated allowlist |
| `LOU_OPENAI_API_KEY` | — | Optional, enables OpenAI command parsing + draft generation |
| `LOU_OPENAI_MODEL` | `gpt-4o-mini` | OpenAI chat model |
| `LOU_OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `LOU_SLNG_API_KEY` | — | Optional, enables SLNG live STT |
| `LOU_SLNG_API_BASE_HTTP` | `https://api.slng.ai` | SLNG HTTP base |
| `LOU_SLNG_STT_MODEL` | `deepgram/nova:3` | SLNG STT model id |
| `LOU_SLNG_TTS_MODEL` | `slng/rime/arcana:3-en` | SLNG TTS model id |
| `LOU_SLNG_STT_KEYWORDS` | `confidentiality, residual knowledge, non-solicit, data protection` | Keyword bias for STT |
| `LOU_VOICE_LANGUAGES` | `en, fr, nl, de` | Allowed languages |
| `LOU_DEMO_PLAYBOOK_XLSX` | `demo-data/siemens-mutual-nda-playbook.xlsx` | XLSX import path |
| `LOU_ALGORITHM_CONFIG_PATH` | `backend/app/algorithms.yaml` | Algorithm tunables YAML |
| `LOU_MAX_UPLOAD_BYTES` | `52428800` | Upload cap (50 MB) |
| `LOU_MAX_AUDIO_BYTES` | `31457280` | Audio cap (30 MB) |
| `LOU_MAX_PDF_PAGES` | `300` | PDF page cap |
| `LOU_MAX_DOCX_PARAGRAPHS` | `10000` | DOCX paragraph cap |
| `LOU_RATE_LIMIT_PER_MINUTE` | `600` | Token-bucket size (`/api/health` and `/api/session/demo-login` are exempt) |
| `LOU_DOCX_MAX_COMPRESSION_RATIO` | `100` | DOCX zip-bomb guard |
| `PIONEER_API_KEY` | — | Required only when regenerating the Pioneer dataset |

## Datasets and demo contracts

Runtime data the backend loads at startup:

```text
demo-data/playbooks.jsonl                  # 50 playbooks
demo-data/playbook_positions.jsonl         # 2 500 positions (50 per playbook)
demo-data/contracts.jsonl                  # seeded demo contract
demo-data/proposals.jsonl                  # initial review proposals (empty by default)
demo-data/commits.jsonl                    # commit history (empty by default)
demo-data/entities.jsonl                   # entities for the Company Brain graph
demo-data/relations.jsonl                  # relationships between entities and playbooks
demo-data/siemens-mutual-nda-playbook.xlsx # the demo XLSX import shape
```

Pioneer source artifacts (review-only, regenerate with `scripts/generate_lou_*`):

```text
demo-data/lou-pioneer-playbook-datasets-50.jsonl       # 50 seed rows
demo-data/lou-pioneer-playbook-matrix-50x50.jsonl      # 2 500-row matrix
demo-data/lou-pioneer-playbook-matrix-50x50.xlsx       # same matrix as XLSX
demo-data/pioneer-playbook-generation-request.json     # exact Pioneer request payload
demo-data/pioneer-playbook-generation-response.json    # raw Pioneer response
demo-data/pioneer-playbook-matrix-request.json
demo-data/pioneer-playbook-matrix-response.json
```

Demo contracts you can upload to the app or feed to the CLI:

```text
demo-data/generated-contract-pdfs-50x50/   # 1 contract per playbook, named "PB01 - ... - Contract 01 ...pdf"
demo-data/generated-contract-pdfs/         # a smaller curated sample with named playbook matches
```

Each subdirectory has a `manifest.json` mapping each PDF to its `playbook_id`,
`playbook_code`, and `playbook_name`. Match the `PBxx` prefix on the contract
to the same `PBxx` playbook when reviewing.

## Repository structure

```text
Lou/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middlewares, request_id, rate limit
│   │   ├── config.py                # Settings (LOU_* env-driven)
│   │   ├── algorithms.yaml          # Tunable ML constants
│   │   ├── algorithm_config.py      # YAML loader for algorithms.yaml
│   │   ├── db.py                    # SQLModel + SQLite engine
│   │   ├── models.py                # Pydantic / SQLModel schemas
│   │   ├── services.py              # Core business logic
│   │   ├── ai.py                    # OpenAI integration
│   │   ├── seeder.py                # Loads JSONL demo data into runtime store
│   │   ├── demo_data.py             # XLSX import helper
│   │   ├── provider_keys.py         # contextvars for per-request keys
│   │   ├── errors.py                # Standard {error: {code,message,details}}
│   │   ├── limits.py                # Upload + parse caps + magic-byte sniffer
│   │   ├── rate_limit.py            # Token-bucket limiter
│   │   ├── logging_config.py        # JSON formatter + request_id var
│   │   ├── routers/                 # FastAPI routers (auth, playbooks, contracts, …)
│   │   └── algorithms/              # Clause matcher, HMM, voice matcher, Bayes, BM25, brain
│   ├── tests/                       # Backend flow + algorithm tests (pytest)
│   ├── requirements.txt
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # Providers + RoleSync
│   │   ├── router.tsx               # React Router config + role gates
│   │   ├── pages/                   # Dashboard, Playbooks, Contracts, Review, Voice, Brain, Export
│   │   ├── components/
│   │   │   ├── layout/              # Shell, Sidebar (drawer), TopBar (mobile sheet), SplitPane
│   │   │   ├── primitives/          # Button, Input, Textarea, Select (a11y), Modal, Badge, …
│   │   │   ├── data/                # FindingCard, ProposalCard, RiskBadge, RiskPosteriorBar, …
│   │   │   ├── voice/               # VoiceOrb, WaveformViz, TranscriptRoll
│   │   │   ├── graph/               # BrainGraph SVG mind-map
│   │   │   └── shared/              # EmptyState, AnimatedNumber, RoleGate
│   │   ├── design-system/           # OKLCH tokens, typography, springs, motion variants
│   │   ├── hooks/                   # useApi (React Query), useAuth, useVoice
│   │   ├── stores/                  # Zustand auth + UI store
│   │   ├── lib/                     # api client, constants, utils
│   │   └── types/                   # Shared TypeScript types
│   ├── package.json
│   ├── vite.config.ts
│   └── vitest.config.ts
├── packages/
│   └── lou-cli/                     # @lou-ai/cli — npm-installable Lou CLI
│       ├── bin/lou.ts               # Entry shim
│       ├── src/cli.ts               # Command router (status, login, playbooks, contracts, review, voice, brain, keys, export, command, review-contract, configure)
│       ├── src/http.ts              # LouClient: provider-key forwarding, timeouts, error envelope
│       ├── src/config.ts            # ~/.lou/config.json with 0600 perms + permission warning
│       ├── src/progress.ts          # Non-blocking stderr spinner
│       └── tests/cli.test.ts        # Vitest suite (11 tests)
├── cli/
│   └── lou.py                       # Legacy Python CLI (deprecated; prints banner on TTY)
├── demo-data/                       # Runtime + Pioneer source + generated contract PDFs
├── scripts/
│   ├── launch_lou.sh                # One-shot dev/preview launcher
│   ├── smoke_lou.py                 # Live integration smoke test
│   ├── generate_demo_contract_pdfs.py
│   ├── generate_contracts_from_playbook_matrix.py
│   ├── generate_lou_dataset.py             # Pioneer seed (50 rows)
│   ├── generate_lou_playbook_matrix.py     # Pioneer expansion (50×50 = 2 500)
│   └── materialize_runtime_playbooks.py    # Pioneer → runtime JSONL
├── tests/                           # Legacy Python CLI tests
├── PRODUCT.md
├── DESIGN.md
├── ROADMAP.md
├── pytest.ini
├── pyproject.toml
└── README.md                        # ← you are here
```

## Tests and verification

Lou ships green test suites at every layer.

```bash
# Backend (45 tests)
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q

# Legacy Python CLI (7 tests)
.venv/bin/python -m pytest tests -q

# Frontend (7 tests — Vitest + Testing Library)
npm --prefix frontend test -- --run

# Frontend production build
npm --prefix frontend run build

# npm CLI (11 tests — Vitest)
npm --prefix packages/lou-cli test
npm --prefix packages/lou-cli run build
npm --prefix packages/lou-cli run pack:dry
```

Live integration smoke test against a running backend:

```bash
python scripts/smoke_lou.py http://localhost:8000
```

The smoke script verifies: health, demo login, playbook count (env-driven
threshold), Company Brain access, role gates, contract analyze, voice session
config, voice transcript fallback, proposal submit, senior approval, JSON +
XLSX + PNG export, and natural-language command routing.

## Roadmap

- Real SSO and tenant isolation (replace demo role switch).
- Postgres-backed normalized store (replace SQLite snapshot store).
- Live SLNG WebSocket proxy for browser auth + diarized streaming.
- Confidence thresholds, prompt versioning, and benchmark sets for the AI paths.
- Webhooks + signed download links for exports.
- Redis-backed rate limiting for multi-instance deployments.
- More languages (currently English, French, Dutch, German).

See [ROADMAP.md](ROADMAP.md) for the long list.

## Credits

- **SLNG** for voice infrastructure (live STT, TTS, audio-upload transcription).
  See <https://slng.ai>.
- **Pioneer by Fastino** for the synthetic legal dataset that powers the demo
  playbooks. See <https://fastino.ai>.
- **OpenAI** for the optional command-routing and contract-drafting paths.
- **Phosphor Icons**, **Framer Motion**, **Zustand**, **TanStack Query**,
  **Tailwind**, **Vite**, **FastAPI**, **SQLModel**, **PyMuPDF**, **scikit-learn**,
  **scipy**, **rank-bm25**, **jellyfish** — the open-source stack Lou is built on.

## License

MIT. See [LICENSE](LICENSE) for full text.
