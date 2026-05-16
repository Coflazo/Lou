# Lou CLI

Terminal client for Lou, published as `@lou-ai/cli`.

The CLI talks to a running Lou backend. It does not install or run the Python backend.

## Install

```bash
npm install -g @lou-ai/cli
```

## Configure

```bash
lou configure --api-base http://localhost:8000 --api-key lou_xxxxx
```

Configuration is read from CLI flags, then environment variables, then `~/.lou/config.json`.

Supported environment variables:

```text
LOU_API_BASE
LOU_API_KEY
LOU_OPENAI_API_KEY
LOU_SLNG_API_KEY
LOU_ALLOW_PROVIDER_KEY_FORWARDING
```

Provider-key forwarding is disabled for remote backends unless explicitly enabled:

```bash
lou configure --allow-provider-key-forwarding
```

## Commands

```bash
lou status
lou playbooks
lou playbooks show <playbook-id>
lou review
lou review approve <proposal-id>
lou review reject <proposal-id>
lou commit <proposal-id>
lou push <proposal-id>
lou edit <playbook-id> --position <position-id> --set "Column=Value"
lou review-contract <file.pdf|file.docx> --playbook <playbook-id> [--out ./lou-review/name]
lou export json
lou export xlsx
lou export png
lou command "natural language command"
```

Use `--json` for machine-readable output:

```bash
lou --json playbooks
```

Use `--base-url` or `--api-key` to override config for a single command:

```bash
lou --base-url http://localhost:8010 --api-key lou_xxxxx review
```

## Contract Review Artifacts

`lou review-contract` uploads a PDF/DOCX to `/api/contracts/review-artifact`, downloads the ZIP response, and extracts the reviewed output locally.

Example with the paired PB01 demo contract:

```bash
lou review-contract "../../demo-data/generated-contract-pdfs-50x50/PB01 - NDA Negotiation and Enforcement Playbook - Contract 01 Demo Agreement.pdf" \
  --playbook pb-01-nda-negotiation-and-enforcement-playbook
```

The extracted directory contains `review.json` plus an annotated document when the backend can produce one.

## Development

```bash
npm --prefix packages/lou-cli test
npm --prefix packages/lou-cli run build
npm --prefix packages/lou-cli run pack:dry
```
