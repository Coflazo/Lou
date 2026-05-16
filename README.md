<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/lou-wordmark-on-dark.png">
    <img alt="Lou" src="frontend/public/lou-wordmark-on-light.png" height="64">
  </picture>
</p>

<p align="center">
  Controlled legal memory for contracts, playbooks, voice notes, and approvals.
</p>

## What Lou Is

Lou is a legal workspace for contract teams. It maps contracts against approved negotiation playbooks, turns gaps into reviewable proposals, and commits senior-approved changes back into reusable legal memory.

The product has three surfaces:

- **Web app** for contract review, playbooks, voice notes, senior approval, exports, and the Company Brain.
- **FastAPI backend** for analysis, review artifacts, voice transcript processing, exports, API keys, and command routing.
- **npm CLI** published as `@lou-ai/cli` so terminal users can inspect playbooks, review contracts, approve proposals, edit positions, and export data.

## Core Workflow

1. A legal user uploads or analyzes a contract.
2. Lou maps clauses to a playbook position when the clause is covered.
3. Lou marks uncovered clauses as unmapped and proposes new guidance.
4. Senior counsel approves, rejects, edits, or commits proposals.
5. Approved knowledge becomes part of the controlled playbook memory.
6. The Company Brain shows the connected graph of playbooks, topics, commits, and legal memory.

## Quick Start

```bash
./scripts/launch_lou.sh
```

Open the web app:

```text
http://localhost:5173
```

Backend API:

```text
http://localhost:8000
```

If a port is already in use:

```bash
BACKEND_PORT=8010 FRONTEND_PORT=5180 ./scripts/launch_lou.sh
```

`launch_lou.sh` prepares Python and frontend dependencies, materializes the 50-playbook runtime data, runs tests/builds, starts the backend, runs smoke checks, and serves the built frontend preview.

## Demo Roles

Role switching is available in the sidebar for local demo use.

- **Junior counsel** reviews contracts, sees mapped and unmapped clauses, records voice notes, and submits proposals.
- **Senior counsel** reviews proposals, approves or rejects them, edits playbook positions, commits changes, and exports artifacts.
- **Legal operations** opens the Company Brain and manages higher-level controls such as imports and API keys.

## Playbooks And Upload Contracts

Runtime playbooks live in:

```text
demo-data/playbooks.jsonl
demo-data/playbook_positions.jsonl
```

The app now labels playbooks with explicit codes:

```text
PB01 - NDA Negotiation and Enforcement Playbook
PB02 - SaaS Contract Lifecycle Management Playbook
PB03 - Data Processing Agreement (DPA) Framework Playbook
...
PB50 - Public Sector Contract Compliance Audit Playbook
```

Upload-ready contract PDFs are paired by the same code:

```text
demo-data/generated-contract-pdfs-50x50/
```

Examples:

```text
PB01 - NDA Negotiation and Enforcement Playbook - Contract 01 Demo Agreement.pdf
PB02 - SaaS Contract Lifecycle Management Playbook - Contract 01 Demo Agreement.pdf
PB03 - Data Processing Agreement DPA Framework Playbook - Contract 01 Demo Agreement.pdf
```

Use `PB01` contracts with the `PB01` playbook, `PB02` contracts with the `PB02` playbook, and so on. The folder also has `manifest.json` with the `playbook_id`, `playbook_code`, `playbook_name`, and PDF path for each contract.

There is also a smaller full-text sample set:

```text
demo-data/generated-contract-pdfs/
```

Those files are also named with their related playbook code and playbook name where there is a direct match, for example `PB01 - NDA Negotiation and Enforcement Playbook - Mutual Non-Disclosure Agreement.pdf`.

## Browser Usage

Important web flows:

- **Dashboard** shows active playbooks, positions, contracts, review count, voice entry point, and commit history.
- **Playbooks** lists all playbooks and opens position-level guidance, fallback ladders, red lines, and deal breakers.
- **Contracts** accepts text-based PDF/DOCX uploads, maps clauses, shows risk, highlights findings, and routes gaps into proposals.
- **Review queue** lets senior counsel approve, reject, edit, and commit proposed playbook updates.
- **Voice session** processes typed transcript notes or uploaded audio into review-ready suggestions.
- **Company Brain** renders the legal memory graph across playbooks, topics, entities, commits, and relationships.
- **Exports** produces JSON, XLSX, and PNG snapshots.

The shell, split panes, contract lists, navigation, and top command bar have responsive behavior for mobile, tablet, and desktop layouts.

**Mobile contract negotiations.** On screens narrower than 768px the Voice
session page exposes a `Fullscreen` button. Tap it for an edge-to-edge listening
view: a top bar with live status, the voice orb up top, the scrollable
transcript taking the middle, and a sticky bottom row with language picker,
listen/stop, and Send-to-playbook actions. Tap the collapse icon (or press Esc)
to return to the normal page.

## npm CLI

Install the CLI:

```bash
npm install -g @lou-ai/cli
```

Configure it:

```bash
lou configure --api-base http://localhost:8000 --api-key lou_xxxxx
```

Useful commands:

```bash
lou status
lou login --role senior
lou playbooks
lou playbooks show pb-01-nda-negotiation-and-enforcement-playbook
lou playbooks import
lou contracts list
lou contracts show contract-id
lou review
lou review approve prop-id
lou review reject prop-id
lou review submit --playbook pb-01-nda-negotiation-and-enforcement-playbook --topic "Scope" --text "Updated stance"
lou commit prop-id
lou push prop-id
lou edit pb-01-nda-negotiation-and-enforcement-playbook --position position-id --set "Preferred Position=Updated text"
lou review-contract "demo-data/generated-contract-pdfs-50x50/PB01 - NDA Negotiation and Enforcement Playbook - Contract 01 Demo Agreement.pdf" --playbook pb-01-nda-negotiation-and-enforcement-playbook
lou voice transcript --playbook pb-01-nda-negotiation-and-enforcement-playbook --language en --text "...notes..."
lou voice transcribe ./recording.webm --playbook pb-01-nda-negotiation-and-enforcement-playbook
lou brain
lou keys list
lou keys create --name ci-bot --role SENIOR
lou keys revoke key-id
lou keys use lou_xxxxx
lou export json
lou export xlsx
lou export png
lou command "export the playbook"
```

Global flags work on every command:

```bash
lou --json playbooks            # JSON output for scripts/integrations
lou --verbose status            # print HTTP method + URL of each request to stderr
lou --timeout 120000 review-contract ./big.pdf --playbook pb-saas
```

The legacy Python CLI at `cli/lou.py` is kept as a compatibility shim and shows a
deprecation banner when invoked interactively. New work should use `@lou-ai/cli`.

Provider keys can be stored locally for self-hosted backends:

```bash
lou configure --openai-key sk-... --slng-key slng_...
```

Provider keys are forwarded only to localhost by default. To forward them to a remote Lou backend, opt in explicitly:

```bash
lou configure --allow-provider-key-forwarding
```

The CLI writes `~/.lou/config.json` with owner-only permissions.

The old Python CLI at `cli/lou.py` is kept as a deprecated legacy shim for existing scripts. New terminal work should use `@lou-ai/cli`.

## Product API

Lou supports bearer-token API keys:

```http
Authorization: Bearer lou_xxxxx
```

Important API groups:

- `GET /api/health`
- `POST /api/session/demo-login`
- `GET /api/playbooks`
- `GET /api/playbooks/{playbook_id}`
- `PATCH /api/playbooks/{playbook_id}/positions/{position_id}`
- `POST /api/contracts/upload`
- `POST /api/contracts/analyze`
- `POST /api/contracts/review-artifact`
- `GET /api/review`
- `POST /api/review/proposals`
- `POST /api/review/{proposal_id}/approve`
- `POST /api/review/{proposal_id}/reject`
- `POST /api/voice/transcript`
- `POST /api/voice/transcribe-audio`
- `GET /api/company-brain`
- `GET /api/export/{json|xlsx|png}`
- `POST /api/lou-command`

API keys are managed through `/api/api-keys`. Demo role switching is for local development; production integrations should use API keys.

## Hardening And Configuration

Backend defaults live in `backend/app/config.py` and can be overridden with `LOU_*` environment variables.

Notable hardening in this branch:

- Upload size caps and media-type checks before contract parsing.
- PDF page caps and DOCX archive compression-ratio checks.
- Request IDs on responses and structured JSON logging.
- In-memory token-bucket rate limiting for single-instance demos.
- Consistent error envelopes: `{"error": {"code", "message", "details"}}`.
- Request-scoped provider key forwarding through `X-Lou-OpenAI-Key` and `X-Lou-SLNG-Key` without persistence.
- Algorithm tuning moved to `backend/app/algorithms.yaml`, overrideable with `LOU_ALGORITHM_CONFIG_PATH`.

Local secrets can be placed in `api-keys.txt`; the file is gitignored and should stay untracked.

## Algorithms

- **Clause matching** maps contract language to playbook positions.
- **Section detection** segments contracts before clause-level analysis.
- **Bayesian risk scoring** turns findings into contract-level risk posture.
- **Voice matching** converts negotiation notes into proposed playbook updates.
- **Company Brain** links playbooks, positions, commits, topics, entities, and relationships.
- **Semantic search and command parsing** can use OpenAI when configured, with deterministic fallbacks when not configured.

## Verification

Backend:

```bash
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
```

Legacy Python CLI tests:

```bash
.venv/bin/python -m pytest tests -q
```

Frontend:

```bash
npm --prefix frontend test -- --run
npm --prefix frontend run build
```

npm CLI:

```bash
npm --prefix packages/lou-cli test
npm --prefix packages/lou-cli run build
npm --prefix packages/lou-cli run pack:dry
```

Live smoke checks, with the backend running:

```bash
python scripts/smoke_lou.py http://localhost:8000
```

## Repository Map

```text
backend/app/              FastAPI app, routers, services, models, algorithms
backend/tests/            Backend flow and algorithm tests
frontend/src/             React app, design system, pages, components, hooks
packages/lou-cli/         npm-installable Lou CLI package
cli/                      Deprecated Python CLI shim
demo-data/                Runtime JSONL data, generated playbooks, generated contract PDFs
scripts/                  Launch, smoke test, data materialization, and demo PDF generators
tests/                    Legacy Python CLI tests
```
