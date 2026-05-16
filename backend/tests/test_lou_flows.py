import asyncio
import json
import zipfile

from fastapi.testclient import TestClient
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import delete
from sqlmodel import Session

from app import demo_data, services
from app.db import ApiKeyRecord, engine
from app.main import app
from app.rate_limit import rate_limiter


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    services.store.reset()
    rate_limiter.reset()
    with Session(engine) as session:
        session.exec(delete(ApiKeyRecord))
        session.commit()
    yield
    with Session(engine) as session:
        session.exec(delete(ApiKeyRecord))
        session.commit()


def login(role: str) -> dict:
    response = client.post("/api/session/demo-login", json={"role": role})
    assert response.status_code == 200
    return response.json()


def make_pdf_bytes(text: str) -> bytes:
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    font_ref = writer._add_object(font)
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )
    stream = DecodedStreamObject()
    safe_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream.set_data(f"BT /F1 12 Tf 72 720 Td ({safe_text}) Tj ET".encode("utf-8"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


def make_docx_bytes(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def test_imports_all_demo_playbooks_and_positions():
    login("ADMIN")
    response = client.get("/api/playbooks")
    assert response.status_code == 200
    playbooks = response.json()
    assert len(playbooks) == 50
    detail = client.get(f"/api/playbooks/{playbooks[0]['id']}").json()
    total_positions = sum(
        len(client.get(f"/api/playbooks/{playbook['id']}").json()["positions"])
        for playbook in playbooks
    )
    assert total_positions == 2500
    assert len(detail["positions"]) == 50
    assert detail["columns"] == ["Topic", "Preferred Position", "Fallback 1", "Fallback 2", "Fallback 3", "Red Line", "Deal Breaker"]
    assert detail["positions"][0]["columns"]["Preferred Position"]


def test_senior_can_manually_edit_playbook_position_columns():
    login("SENIOR")
    playbook = client.get("/api/playbooks").json()[0]
    detail = client.get(f"/api/playbooks/{playbook['id']}").json()
    position = detail["positions"][0]
    columns = dict(position["columns"])
    columns["Preferred Position"] = "Updated manually without prompting Lou."
    columns["Fallback 1"] = "Manual fallback one."

    response = client.patch(
        f"/api/playbooks/{playbook['id']}/positions/{position['id']}",
        json={"columns": columns},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preferred_position"] == "Updated manually without prompting Lou."
    assert body["fallback_position"] == "Manual fallback one."


def test_xlsx_loader_fails_clearly_when_source_file_is_missing(tmp_path, monkeypatch):
    missing = tmp_path / "missing-playbook.xlsx"
    monkeypatch.setattr(demo_data, "XLSX_PATH", missing)
    with pytest.raises(RuntimeError, match="Missing demo playbook XLSX"):
        demo_data.load_demo_playbook()


def test_contract_analysis_maps_known_and_unknown_clauses():
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    detail = client.get(f"/api/playbooks/{playbook['id']}").json()
    known = detail["positions"][0]["preferred_position"]
    response = client.post(
        "/api/contracts/analyze",
        json={
            "playbook_id": playbook["id"],
            "name": "Supplier NDA",
            "text": f"{known}. Xylophone nebula quartzboard cafeteria murals.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert any(finding["status"] == "mapped" for finding in body["findings"])
    assert any(finding["status"] == "unmapped" for finding in body["findings"])
    assert any(item["source"] == "contract" for item in body["proposed_updates"])
    login("SENIOR")
    assert client.get("/api/review").json() == []


def test_contract_upload_extracts_text_and_returns_review_payload():
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    detail = client.get(f"/api/playbooks/{playbook['id']}").json()
    known = detail["positions"][0]["preferred_position"]
    cases = [
        ("supplier-nda.pdf", "application/pdf", make_pdf_bytes(f"{known}. Xylophone nebula quartzboard cafeteria murals.")),
        (
            "supplier-nda.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            make_docx_bytes(f"{known}. Xylophone nebula quartzboard cafeteria murals."),
        ),
    ]
    for filename, content_type, payload in cases:
        response = client.post(
            "/api/contracts/upload",
            data={"playbook_id": playbook["id"]},
            files={"file": (filename, payload, content_type)},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["contract"]["name"] == filename
        assert "quartzboard" in body["contract"]["text"].lower()
        assert body["sections"]
        assert body["highlights"]
        assert any(finding["status"] == "mapped" for finding in body["findings"])
        assert any(finding["status"] == "unmapped" for finding in body["findings"])


def test_contract_review_artifact_returns_zip_with_annotated_pdf_and_review_json():
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    detail = client.get(f"/api/playbooks/{playbook['id']}").json()
    known = detail["positions"][0]["preferred_position"]

    response = client.post(
        "/api/contracts/review-artifact",
        data={"playbook_id": playbook["id"]},
        files={
            "file": (
                "supplier-nda.pdf",
                make_pdf_bytes(f"{known}. The agreement adds lunchroom seating obligations."),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/zip")
    archive = zipfile.ZipFile(BytesIO(response.content))
    assert sorted(archive.namelist()) == ["annotated-supplier-nda.pdf", "review.json"]
    review = json.loads(archive.read("review.json"))
    assert review["contract"]["name"] == "supplier-nda.pdf"
    assert review["findings"]
    assert review["risk_posterior"]
    assert isinstance(review["warnings"], list)
    annotated_pdf = fitz.open(stream=archive.read("annotated-supplier-nda.pdf"), filetype="pdf")
    assert any(page.first_annot for page in annotated_pdf)


def test_contract_review_artifact_returns_docx_and_warnings_for_unmatched_excerpts(monkeypatch):
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    original = services.analyze_uploaded_contract

    def fake_analyze_uploaded_contract(playbook_id, filename, content):
        result = original(playbook_id, filename, content)
        result["findings"][0].excerpt = "Text that is not present in the original document"
        return result

    monkeypatch.setattr(services, "analyze_uploaded_contract", fake_analyze_uploaded_contract)

    response = client.post(
        "/api/contracts/review-artifact",
        data={"playbook_id": playbook["id"]},
        files={
            "file": (
                "supplier-nda.docx",
                make_docx_bytes("The agreement adds lunchroom seating obligations."),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )

    assert response.status_code == 200
    archive = zipfile.ZipFile(BytesIO(response.content))
    assert sorted(archive.namelist()) == ["annotated-supplier-nda.docx", "review.json"]
    review = json.loads(archive.read("review.json"))
    assert review["warnings"]
    assert "not present" in review["warnings"][0].lower()


def test_contract_review_artifact_rejects_scanned_or_empty_pdfs():
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    output = BytesIO()
    writer.write(output)

    response = client.post(
        "/api/contracts/review-artifact",
        data={"playbook_id": playbook["id"]},
        files={"file": ("scanned.pdf", output.getvalue(), "application/pdf")},
    )

    assert response.status_code == 422
    assert "no extractable text" in response.json()["error"]["message"].lower()


def test_request_scoped_provider_keys_override_settings_for_one_request(monkeypatch):
    seen = []
    playbook = client.get("/api/playbooks").json()[0]
    monkeypatch.setattr(services.settings, "SLNG_API_KEY", "env-slng")

    def fake_post(url, *, headers, files, data, timeout):
        seen.append(headers["Authorization"])

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {"transcript": "Speaker 1: Review residual knowledge."}

        return FakeResponse()

    monkeypatch.setattr(services.httpx, "post", fake_post)

    response = client.post(
        "/api/voice/transcribe-audio",
        data={"playbook_id": playbook["id"], "language": "en"},
        files={"file": ("voice.webm", b"fake webm audio", "audio/webm")},
        headers={"X-Lou-SLNG-Key": "request-slng"},
    )

    assert response.status_code == 200
    assert seen == ["Bearer request-slng"]

    services.transcribe_audio_with_slng(b"fake webm audio", "voice.webm", "audio/webm")
    assert seen[-1] == "Bearer env-slng"


def test_voice_transcript_creates_proposed_updates():
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    session = client.post("/api/voice/session", json={"playbook_id": playbook["id"], "language": "fr"}).json()
    assert session["language"] == "fr"
    assert set(session["supported_languages"]) == {"en", "fr", "nl", "de"}
    assert "/v1/stt/deepgram/nova:3" in session["stt"]["websocket_url"]
    assert "/v1/bridges/unmute/tts/slng/rime/arcana:3-en" in session["tts"]["websocket_url"]

    response = client.post(
        "/api/voice/transcript",
        json={
            "playbook_id": playbook["id"],
            "language": "de",
            "transcript": "Partner insists residual knowledge carve-out should be acceptable.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "transcript-fallback"
    assert len(body["proposed_updates"]) >= 1
    login("SENIOR")
    assert client.get("/api/review").json() == []


def test_voice_audio_upload_transcribes_with_slng_and_creates_updates(monkeypatch):
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]
    # transcribe_audio_to_updates short-circuits to a friendly fallback when no
    # SLNG key is present; this test exercises the SLNG path so we set one.
    monkeypatch.setattr(services.settings, "SLNG_API_KEY", "env-slng-test")

    def fake_transcribe_audio_with_slng(audio, filename, content_type, language):
        assert audio == b"fake webm audio"
        assert filename == "voice.webm"
        assert content_type == "audio/webm"
        assert language == "nl"
        return {
            "provider": "SLNG",
            "mode": "slng-audio",
            "language": language,
            "transcript": "Speaker 1: Partner says residual knowledge should exclude pricing.",
            "speaker_segments": [
                {"speaker": "Speaker 1", "text": "Partner says residual knowledge should exclude pricing."}
            ],
            "raw": {"transcript": "Partner says residual knowledge should exclude pricing."},
        }

    monkeypatch.setattr(services, "transcribe_audio_with_slng", fake_transcribe_audio_with_slng)

    response = client.post(
        "/api/voice/transcribe-audio",
        data={"playbook_id": playbook["id"], "language": "nl"},
        files={"file": ("voice.webm", b"fake webm audio", "audio/webm")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "SLNG"
    assert body["mode"] == "slng-audio"
    assert body["language"] == "nl"
    assert "residual knowledge" in body["transcript"]
    assert body["speaker_segments"][0]["speaker"] == "Speaker 1"
    assert len(body["proposed_updates"]) >= 1
    login("SENIOR")
    assert client.get("/api/review").json() == []


def test_slng_diarization_words_become_speaker_separated_notes():
    payload = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "words": [
                                {"word": "we", "speaker": 0, "start": 0.0, "end": 0.1},
                                {"word": "need", "speaker": 0, "start": 0.1, "end": 0.3},
                                {"word": "liability", "speaker": 1, "start": 0.4, "end": 0.8},
                                {"word": "cap", "speaker": 1, "start": 0.8, "end": 1.0},
                            ]
                        }
                    ]
                }
            ]
        }
    }

    assert services.extract_slng_transcript(payload) == "Speaker 1: we need\nSpeaker 2: liability cap"


def test_voice_notes_generate_contract_and_analyze_with_openai(monkeypatch):
    login("JUNIOR")
    playbook = client.get("/api/playbooks").json()[0]

    def fake_draft_contract_from_notes(notes, playbook_name, playbook_category):
        assert "Speaker 1" in notes
        assert playbook_name
        assert playbook_category
        return {
            "title": "Generated Negotiation Agreement",
            "contract_text": (
                "Article 1. Scope. Supplier shall protect residual knowledge and exclude pricing. "
                "Article 2. Confidentiality. Confidential information may not be disclosed without approval. "
                "Article 3. Liability. Unlimited liability is rejected except for fraud."
            ),
        }

    monkeypatch.setattr(services, "draft_contract_from_notes", fake_draft_contract_from_notes)

    response = client.post(
        "/api/voice/contract-from-notes",
        json={
            "playbook_id": playbook["id"],
            "language": "en",
            "transcript": "Speaker 1: We need residual knowledge to exclude pricing.\nSpeaker 2: Liability cap is required.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "openai-contract-from-notes"
    assert body["generated_contract"]["title"] == "Generated Negotiation Agreement"
    assert body["contract"]["name"] == "Generated Negotiation Agreement"
    assert body["findings"]


def test_review_permissions_and_approval_commit_updates_graph():
    login("JUNIOR")
    pending = client.get("/api/review")
    assert pending.status_code == 403

    playbook = client.get("/api/playbooks").json()[0]
    created = client.post(
        "/api/review/proposals",
        json={
            "playbook_id": playbook["id"],
            "topic": "Residual Knowledge",
            "source": "voice",
            "proposed_text": "Add a residual knowledge position from the negotiation notes.",
            "rationale": "Junior explicitly submitted this suggestion for senior review.",
        },
    )
    assert created.status_code == 200

    login("SENIOR")
    review_items = client.get("/api/review").json()
    assert review_items
    approval = client.post(f"/api/review/{review_items[0]['id']}/approve", json={"edited_text": "Approved demo position."})
    assert approval.status_code == 200
    commits = client.get("/api/commits").json()
    assert any(commit["proposal_id"] == review_items[0]["id"] for commit in commits)

    playbook_id = review_items[0]["playbook_id"]
    brain = client.get(f"/api/playbooks/{playbook_id}/brain").json()
    assert any(node["kind"] == "commit" for node in brain["nodes"])


def test_lou_api_keys_authenticate_api_clients_and_can_be_revoked():
    login("ADMIN")
    created = client.post("/api/api-keys", json={"name": "Terminal senior", "role": "SENIOR"})
    assert created.status_code == 200
    senior_key = created.json()
    assert senior_key["key"].startswith("lou_")
    assert senior_key["key_prefix"] == f"{senior_key['key'][:8]}..."

    listed = client.get("/api/api-keys").json()
    assert any(item["id"] == senior_key["id"] for item in listed)
    assert all("key" not in item for item in listed)

    playbook = client.get("/api/playbooks").json()[0]
    submitted = client.post(
        "/api/review/proposals",
        json={
            "playbook_id": playbook["id"],
            "topic": "API Key Proposal",
            "source": "terminal",
            "proposed_text": "Add a position submitted from a terminal API client.",
            "rationale": "A real API client should be able to submit work for review.",
        },
    )
    assert submitted.status_code == 200

    login("JUNIOR")
    response = client.get("/api/review", headers={"Authorization": f"Bearer {senior_key['key']}"})
    assert response.status_code == 200
    assert any(item["id"] == submitted.json()["id"] for item in response.json())

    login("ADMIN")
    junior_key = client.post("/api/api-keys", json={"name": "Terminal junior", "role": "JUNIOR"}).json()
    login("SENIOR")
    forbidden = client.get("/api/review", headers={"Authorization": f"Bearer {junior_key['key']}"})
    assert forbidden.status_code == 403

    login("ADMIN")
    revoked = client.delete(f"/api/api-keys/{senior_key['id']}")
    assert revoked.status_code == 200
    unauthorized = client.get("/api/review", headers={"Authorization": f"Bearer {senior_key['key']}"})
    assert unauthorized.status_code == 401


def test_playbook_brain_exposes_topic_islands_and_relation_edges():
    login("SENIOR")
    playbook = client.get("/api/playbooks").json()[0]
    brain = client.get(f"/api/playbooks/{playbook['id']}/brain").json()
    kinds = {node["kind"] for node in brain["nodes"]}
    edge_kinds = {edge["kind"] for edge in brain["edges"]}
    assert {"topic", "preferred", "fallback"}.issubset(kinds)
    assert {"hierarchy", "topic_relation"}.issubset(edge_kinds)
    assert all("risk" not in node["label"].lower() for node in brain["nodes"])
    assert all({"x", "y"}.issubset(node) for node in brain["nodes"])
    assert any(edge.get("strength", 0) > 0 for edge in brain["edges"] if edge["kind"] == "topic_relation")


def test_exports_json_and_xlsx():
    login("SENIOR")
    json_response = client.get("/api/export/json")
    assert json_response.status_code == 200
    assert json_response.headers["content-type"].startswith("application/json")

    xlsx_response = client.get("/api/export/xlsx")
    assert xlsx_response.status_code == 200
    assert xlsx_response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_openai_command_result_gets_human_message_without_provenance(monkeypatch):
    monkeypatch.setattr(
        services,
        "parse_command_with_openai",
        lambda command: {"intent": "export", "provider": "OpenAI"},
    )
    body = asyncio.run(services.parse_lou_command("export the playbook", "pb-mutual-nda"))
    assert body["message"]
    assert "OpenAI" not in body["message"]
    assert "provider" not in body


def test_expanded_dataset_and_pioneer_request_exist():
    dataset = Path("demo-data/lou-pioneer-playbook-datasets-50.jsonl")
    pioneer_request = Path("demo-data/pioneer-playbook-generation-request.json")
    old_dataset = Path("demo-data/lou-clause-classification-280.jsonl")
    old_request = Path("demo-data/pioneer-generate-request.json")
    assert dataset.exists()
    assert pioneer_request.exists()
    assert not old_dataset.exists()
    assert not old_request.exists()
    assert len(dataset.read_text().splitlines()) == 50
    assert '"provider": "pioneer"' in pioneer_request.read_text()


def test_upload_rejects_unknown_magic_bytes_with_415():
    login("ADMIN")
    playbook = client.get("/api/playbooks").json()[0]
    response = client.post(
        "/api/contracts/upload",
        data={"playbook_id": playbook["id"]},
        files={"file": ("evil.txt", b"This is just text, not a contract.", "text/plain")},
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA"


def test_upload_rejects_payload_above_size_cap():
    from app import limits

    login("ADMIN")
    playbook = client.get("/api/playbooks").json()[0]
    fake_pdf = b"%PDF-" + b"\x00" * (limits.MAX_UPLOAD_BYTES + 16)
    response = client.post(
        "/api/contracts/upload",
        data={"playbook_id": playbook["id"]},
        files={"file": ("huge.pdf", fake_pdf, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "UPLOAD_TOO_LARGE"


def test_rate_limit_returns_429_with_retry_after(monkeypatch):
    from app import rate_limit

    rate_limiter.reset()
    monkeypatch.setattr(rate_limit.rate_limiter, "per_minute", 2)
    monkeypatch.setattr(rate_limit.rate_limiter, "refill_per_second", 0.0001)
    rate_limit.rate_limiter._buckets.clear()

    # /api/health and /api/session/demo-login are exempt; use /api/playbooks.
    assert client.get("/api/playbooks").status_code == 200
    assert client.get("/api/playbooks").status_code == 200
    limited = client.get("/api/playbooks")
    assert limited.status_code == 429
    assert "Retry-After" in limited.headers
    assert limited.json()["error"]["code"] == "RATE_LIMITED"


def test_error_responses_use_envelope():
    login("ADMIN")
    response = client.post(
        "/api/contracts/analyze",
        json={"playbook_id": "pb-does-not-exist", "name": "x", "text": "y"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"]


def test_request_id_is_propagated_in_response_header():
    response = client.get("/api/health", headers={"X-Request-ID": "test-abc-123"})
    assert response.headers["X-Request-ID"] == "test-abc-123"


def test_algorithm_config_loads_yaml_with_defaults():
    from app.algorithm_config import algorithm_config, load_algorithm_config
    from app import config as cfg

    reloaded = load_algorithm_config()
    assert reloaded.clause_matching.min_score == algorithm_config.clause_matching.min_score
    assert tuple(reloaded.hmm_section_detector.logistic.w_begin) == (-0.2, 3.8, 1.6, 0.4, -0.8, 0.7, 2.1)
    assert reloaded.semantic_search.bm25.k1 == 1.5
    assert str(reloaded.source_path).endswith("algorithms.yaml")
    # source path comes from settings
    assert Path(cfg.settings.ALGORITHM_CONFIG_PATH).exists()
