import asyncio

from fastapi.testclient import TestClient
from io import BytesIO
from pathlib import Path

import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app import demo_data, services
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    services.store.reset()
    yield


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
    assert len(playbooks) >= 5
    nda = next(item for item in playbooks if item["slug"] == "mutual-nda")
    detail = client.get(f"/api/playbooks/{nda['id']}").json()
    total_positions = sum(
        len(client.get(f"/api/playbooks/{playbook['id']}").json()["positions"])
        for playbook in playbooks
    )
    assert total_positions == 50
    assert len(detail["positions"]) >= 1
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
            "text": f"{known} The agreement adds lunchroom seating obligations.",
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
        ("supplier-nda.pdf", "application/pdf", make_pdf_bytes(f"{known} The agreement adds lunchroom seating obligations.")),
        (
            "supplier-nda.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            make_docx_bytes(f"{known} The agreement adds lunchroom seating obligations."),
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
        assert "lunchroom seating" in body["contract"]["text"].lower()
        assert body["sections"]
        assert body["highlights"]
        assert any(finding["status"] == "mapped" for finding in body["findings"])
        assert any(finding["status"] == "unmapped" for finding in body["findings"])


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
