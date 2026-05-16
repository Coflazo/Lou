from __future__ import annotations

import json
import urllib.error
from io import BytesIO
from pathlib import Path

import pytest

from cli import lou


class FakeResponse:
    def __init__(self, payload, status: int = 200, content_type: str = "application/json"):
        self.status = status
        self.headers = {"content-type": content_type}
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        if isinstance(self._payload, bytes):
            return self._payload
        return json.dumps(self._payload).encode("utf-8")


@pytest.fixture
def captured_requests(monkeypatch, tmp_path):
    calls = []

    def fake_urlopen(request, timeout=10):
        calls.append(
            {
                "method": request.get_method(),
                "url": request.full_url,
                "headers": dict(request.header_items()),
                "body": json.loads(request.data.decode("utf-8")) if request.data else None,
                "timeout": timeout,
            }
        )
        if request.full_url.endswith("/api/session/demo-login"):
            return FakeResponse({"role": calls[-1]["body"]["role"]})
        if request.full_url.endswith("/api/api-keys"):
            if request.get_method() == "POST":
                return FakeResponse(
                    {
                        "id": "key-123",
                        "name": calls[-1]["body"]["name"],
                        "role": calls[-1]["body"]["role"],
                        "key_prefix": "lou_abcd...",
                        "key": "lou_abcd1234",
                    }
                )
            return FakeResponse([{"id": "key-123", "name": "Harvey", "role": "SENIOR"}])
        if request.full_url.endswith("/api/playbooks"):
            return FakeResponse([{"id": "pb-1", "name": "Mutual NDA", "position_count": 8}])
        if request.full_url.endswith("/api/review"):
            return FakeResponse([{"id": "proposal-1", "topic": "Liability", "source": "voice"}])
        if request.full_url.endswith("/api/commits"):
            return FakeResponse([{"id": "commit-1", "message": "Approved Liability"}])
        if request.full_url.endswith("/api/lou-command"):
            return FakeResponse({"intent": "export", "message": "Export is ready."})
        if request.full_url.endswith("/api/health"):
            return FakeResponse({"status": "ok"})
        raise AssertionError(f"unexpected URL {request.full_url}")

    monkeypatch.setattr(lou.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("LOU_API_KEY", raising=False)
    monkeypatch.delenv("LOU_API_BASE", raising=False)
    return calls


def run_cli(args, capsys) -> tuple[str, str]:
    exit_code = lou.main(args)
    assert exit_code == 0
    output = capsys.readouterr()
    return output.out, output.err


def test_admin_sends_demo_login_request(captured_requests, capsys):
    stdout, _ = run_cli(["admin"], capsys)

    assert captured_requests[0]["method"] == "POST"
    assert captured_requests[0]["url"] == "http://localhost:8000/api/session/demo-login"
    assert captured_requests[0]["body"] == {"role": "ADMIN"}
    assert "ADMIN" in stdout


def test_admin_privileges_alias_behaves_like_admin(captured_requests, capsys):
    run_cli(["--admin-privileges"], capsys)

    assert captured_requests[0]["body"] == {"role": "ADMIN"}


def test_keys_create_posts_name_and_role(captured_requests, capsys):
    stdout, _ = run_cli(["keys", "create", "--role", "SENIOR", "--name", "Harvey integration"], capsys)

    assert captured_requests[0]["method"] == "POST"
    assert captured_requests[0]["url"] == "http://localhost:8000/api/api-keys"
    assert captured_requests[0]["body"] == {"name": "Harvey integration", "role": "SENIOR"}
    assert "lou_abcd1234" in stdout


def test_saved_api_key_is_used_as_bearer_token(captured_requests, capsys, tmp_path, monkeypatch):
    config_dir = Path(tmp_path) / ".lou"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(json.dumps({"api_key": "lou_saved"}), encoding="utf-8")

    run_cli(["review"], capsys)

    assert captured_requests[0]["headers"]["Authorization"] == "Bearer lou_saved"


def test_json_outputs_raw_json(captured_requests, capsys):
    stdout, _ = run_cli(["--json", "playbooks"], capsys)

    assert json.loads(stdout) == [{"id": "pb-1", "name": "Mutual NDA", "position_count": 8}]


def test_readable_mode_prints_concise_summary(captured_requests, capsys):
    stdout, _ = run_cli(["playbooks"], capsys)

    assert "Mutual NDA" in stdout
    assert "8 positions" in stdout
    assert not stdout.lstrip().startswith("[")


def test_http_errors_print_concise_message(monkeypatch, capsys, tmp_path):
    def fake_urlopen(request, timeout=10):
        raise urllib.error.HTTPError(
            request.full_url,
            403,
            "Forbidden",
            {},
            BytesIO(json.dumps({"detail": "SENIOR access required"}).encode("utf-8")),
        )

    monkeypatch.setattr(lou.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setenv("HOME", str(tmp_path))

    exit_code = lou.main(["review"])

    output = capsys.readouterr()
    assert exit_code == 1
    assert output.err.strip() == "403 SENIOR access required"
