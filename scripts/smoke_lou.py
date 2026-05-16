#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request


BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"


def request(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            content_type = response.headers.get("content-type", "")
            body = response.read()
            if "application/json" in content_type:
                return response.status, json.loads(body.decode("utf-8"))
            return response.status, body
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def wait_for_health() -> None:
    for _ in range(30):
        try:
            status, body = request("GET", "/api/health")
            if status == 200 and body.get("status") == "ok":
                return
        except Exception:
            pass
        time.sleep(0.5)
    raise AssertionError("Backend health check did not become ready")


def login(role: str) -> None:
    status, body = request("POST", "/api/session/demo-login", {"role": role})
    assert_true(status == 200 and body["role"] == role, f"{role} login failed")


def main() -> None:
    wait_for_health()

    login("ADMIN")
    status, playbooks = request("GET", "/api/playbooks")
    assert_true(status == 200 and len(playbooks) >= 1, "playbooks list failed")
    playbook_id = playbooks[0]["id"]

    status, playbook = request("GET", f"/api/playbooks/{playbook_id}")
    assert_true(status == 200 and len(playbook["positions"]) >= 1, "playbook detail did not expose positions")
    total_positions = len(playbook["positions"])
    for listed_playbook in playbooks[1:]:
        status, listed_detail = request("GET", f"/api/playbooks/{listed_playbook['id']}")
        assert_true(status == 200, f"playbook detail failed for {listed_playbook['id']}")
        total_positions += len(listed_detail["positions"])
    assert_true(total_positions >= 50, f"runtime playbooks exposed only {total_positions} total positions")
    known_text = playbook["positions"][0]["preferred_position"]

    status, company_brain = request("GET", "/api/company-brain")
    assert_true(status == 200 and company_brain["nodes"], "admin company brain failed")

    login("JUNIOR")
    status, _ = request("GET", "/api/review")
    assert_true(status == 403, "junior should not access review queue")

    status, analysis = request(
        "POST",
        "/api/contracts/analyze",
        {
            "playbook_id": playbook_id,
            "name": "Launch Smoke NDA",
            "text": f"{known_text} The agreement adds lunchroom seating obligations.",
        },
    )
    assert_true(status == 200, "contract analysis failed")
    statuses = {finding["status"] for finding in analysis["findings"]}
    assert_true({"mapped", "unmapped"}.issubset(statuses), "contract analysis did not produce mapped and unmapped findings")
    contract_id = analysis["contract"]["id"]

    status, contract = request("GET", f"/api/contracts/{contract_id}")
    assert_true(status == 200 and contract["findings"], "contract retrieval failed")

    status, voice = request("POST", "/api/voice/session", {"playbook_id": playbook_id, "language": "fr"})
    assert_true(status == 200 and voice["language"] == "fr", "SLNG voice session metadata failed")
    assert_true(set(voice["supported_languages"]) == {"de", "en", "fr", "nl"}, "voice language set is wrong")

    status, transcript = request(
        "POST",
        "/api/voice/transcript",
        {
            "playbook_id": playbook_id,
            "language": "nl",
            "transcript": "Partner says residual knowledge should be acceptable only if pricing is excluded.",
        },
    )
    assert_true(status == 200 and transcript["proposed_updates"], "voice transcript fallback failed")

    status, submitted = request("POST", "/api/review/proposals", transcript["proposed_updates"][0])
    assert_true(status == 200 and submitted["status"] == "pending", "explicit review proposal submission failed")

    login("SENIOR")
    status, queue = request("GET", "/api/review")
    assert_true(status == 200 and queue, "senior review queue failed")

    status, approval = request("POST", f"/api/review/{queue[0]['id']}/approve", {"edited_text": queue[0]["proposed_text"]})
    assert_true(status == 200 and approval["commit"]["id"], "approval commit failed")

    status, commits = request("GET", "/api/commits")
    assert_true(status == 200 and commits, "commit history failed")

    for format_name in ("json", "xlsx", "png"):
        status, body = request("GET", f"/api/export/{format_name}")
        assert_true(status == 200 and body, f"{format_name} export failed")

    status, command = request("POST", "/api/lou-command", {"command": "export the playbook"})
    assert_true(status == 200 and command["intent"] == "export", "Lou command routing failed")

    print("Lou live smoke checks passed")


if __name__ == "__main__":
    main()
