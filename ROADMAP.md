# Complete Product Roadmap

## What Is Left

1. Auth and tenancy
   Replace role buttons with real SSO, company workspaces, audit identities, and scoped access tokens.

2. Durable data model
   Move from the demo snapshot store to normalized playbook, clause, contract, proposal, comment, commit, and export tables with migrations.

3. Document ingestion
   Add robust DOCX/PDF parsing, clause boundary detection, page/section coordinates, and original-file preservation.

4. AI quality
   Add benchmark sets, prompt/version tracking, deterministic fallbacks, human evaluation, and confidence thresholds before findings become user-facing.

5. Pioneer dataset pipeline
   Use Pioneer synthetic data generation for clause classification and NER examples, then track dataset versions and training runs.

6. SLNG live listening
   Add server-side WebSocket proxying for browser auth, live audio capture, diarization, transcript streaming, and voice summary playback.

7. Review workflow
   Add comments, assigned reviewers, diff views, conflict handling, approval policies, and rollback.

8. Exports and integrations
   Add production XLSX styling, graph images from real graph layouts, JSON schemas, webhooks, API keys, and CLI auth.

9. Security and compliance
   Add encryption, secret management, PII redaction, legal hold, retention policies, and complete access logs.

10. Production operations
    Add deployment, monitoring, background workers, queues, retry policies, error reporting, backups, and load tests.

## Non-OpenAI Technologies

- SLNG: voice sessions, STT, TTS, and listening mode.
- Pioneer: synthetic legal dataset generation and future fine-tuning data management.
