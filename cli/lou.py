#!/usr/bin/env python3
"""Legacy Lou CLI shim.

Deprecated as of 2026-05. Install the supported CLI:

    npm install -g @lou-ai/cli

This module is kept so existing scripts and tests keep working. It does not
receive new commands. See packages/lou-cli/ for the maintained surface.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Sequence


DEFAULT_BASE_URL = "http://localhost:8000"
CONFIG_DIR = ".lou"
CONFIG_FILE = "config.json"
ROLES = ("JUNIOR", "SENIOR", "ADMIN")
DEPRECATION_NOTICE = (
    "[deprecated] cli/lou.py is a legacy shim; install '@lou-ai/cli' for the supported CLI."
)


class LouHttpError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def config_path() -> Path:
    return Path.home() / CONFIG_DIR / CONFIG_FILE


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_api_key(api_key: str) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    config = load_config()
    config["api_key"] = api_key
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_base_url(args: argparse.Namespace) -> str:
    return (args.base_url or os.getenv("LOU_API_BASE") or DEFAULT_BASE_URL).rstrip("/")


def resolve_api_key(args: argparse.Namespace) -> str | None:
    return args.api_key or os.getenv("LOU_API_KEY") or load_config().get("api_key")


def request(
    method: str,
    path: str,
    *,
    base_url: str,
    api_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> Any:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(f"{base_url}{path}", data=data, method=method, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = response.read()
            if not raw:
                return None
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type:
                return json.loads(raw.decode("utf-8"))
            return raw.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as error:
        detail = error.reason or "HTTP error"
        raw_error = error.read().decode("utf-8", errors="replace")
        if raw_error:
            try:
                body = json.loads(raw_error)
                detail = str(body.get("detail") or body)
            except json.JSONDecodeError:
                detail = raw_error.strip()
        raise LouHttpError(error.code, detail) from error
    except urllib.error.URLError as error:
        raise LouHttpError(0, str(error.reason)) from error


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def plural(count: int, singular: str, pluralized: str | None = None) -> str:
    word = singular if count == 1 else (pluralized or f"{singular}s")
    return f"{count} {word}"


def readable(command: str, payload: Any, *, base_url: str = DEFAULT_BASE_URL) -> str:
    if command == "status":
        status = payload.get("status", "unknown") if isinstance(payload, dict) else "unknown"
        return f"Lou backend is {status} at {base_url}"

    if command in {"admin", "senior", "junior"}:
        role = payload.get("role", command.upper()) if isinstance(payload, dict) else command.upper()
        return f"Lou demo role: {role}"

    if command == "playbooks":
        if not payload:
            return "No playbooks found."
        lines = ["Playbooks:"]
        for item in payload:
            count = item.get("position_count", 0)
            lines.append(f"- {item.get('name', item.get('id', 'unknown'))}: {plural(count, 'position')}")
        return "\n".join(lines)

    if command == "review":
        if not payload:
            return "No pending review items."
        lines = [f"Review queue: {plural(len(payload), 'item')}"]
        for item in payload:
            source = item.get("source", "unknown")
            lines.append(f"- {item.get('topic', item.get('id', 'proposal'))} ({source})")
        return "\n".join(lines)

    if command == "commits":
        if not payload:
            return "No commits yet."
        lines = [f"Commits: {plural(len(payload), 'commit')}"]
        for item in payload:
            lines.append(f"- {item.get('message', item.get('id', 'commit'))}")
        return "\n".join(lines)

    if command == "command":
        if isinstance(payload, dict) and payload.get("message"):
            return payload["message"]
        if isinstance(payload, dict) and payload.get("intent"):
            return f"Lou command intent: {payload['intent']}"
        return "Lou command completed."

    if command == "keys-create":
        lines = [f"Created {payload.get('role')} API key {payload.get('id')} for {payload.get('name')}."]
        if payload.get("key"):
            lines.append(f"Key: {payload['key']}")
            lines.append(f"Save it with: lou keys use {payload['key']}")
        return "\n".join(lines)

    if command == "keys-list":
        if not payload:
            return "No active API keys."
        lines = [f"API keys: {plural(len(payload), 'key')}"]
        for item in payload:
            prefix = item.get("key_prefix", "")
            lines.append(f"- {item.get('id')} {item.get('role')} {item.get('name')} {prefix}".strip())
        return "\n".join(lines)

    if command == "keys-revoke":
        revoked = payload.get("revoked", "key") if isinstance(payload, dict) else "key"
        return f"Revoked {revoked}."

    if command == "keys-use":
        return "Saved Lou API key."

    return json.dumps(payload, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lou legal workspace CLI")
    parser.add_argument("--base-url", help="Lou API base URL")
    parser.add_argument("--api-key", help="Lou API key. Defaults to LOU_API_KEY, then ~/.lou/config.json.")
    parser.add_argument("--json", action="store_true", help="Print raw JSON for scripts.")
    parser.add_argument(
        "--admin-privileges",
        action="store_true",
        help="Shortcut for `lou admin` in local demo mode.",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status", help="Check backend health.")
    subparsers.add_parser("admin", help="Switch local demo session to ADMIN.")
    subparsers.add_parser("senior", help="Switch local demo session to SENIOR.")
    subparsers.add_parser("junior", help="Switch local demo session to JUNIOR.")
    subparsers.add_parser("playbooks", help="List playbooks.")
    subparsers.add_parser("review", help="List pending review proposals.")
    subparsers.add_parser("commits", help="List approval commits.")

    command_parser = subparsers.add_parser("command", help="Send a natural-language Lou command.")
    command_parser.add_argument("text", help="Command text, for example: 'export the playbook'.")
    command_parser.add_argument("--playbook-id", help="Optional playbook id for command context.")

    keys_parser = subparsers.add_parser("keys", help="Manage Lou API keys.")
    keys_subparsers = keys_parser.add_subparsers(dest="keys_command")

    keys_create = keys_subparsers.add_parser("create", help="Create a Lou API key.")
    keys_create.add_argument("--name", required=True, help="Human-readable key name.")
    keys_create.add_argument("--role", choices=ROLES, default="JUNIOR", help="Role granted to this key.")

    keys_subparsers.add_parser("list", help="List active Lou API keys.")

    keys_revoke = keys_subparsers.add_parser("revoke", help="Revoke a Lou API key.")
    keys_revoke.add_argument("key_id", help="API key id to revoke.")

    keys_use = keys_subparsers.add_parser("use", help="Save a Lou API key for future CLI calls.")
    keys_use.add_argument("api_key", help="Raw Lou API key, starting with lou_.")

    return parser


def execute(args: argparse.Namespace) -> tuple[str, Any]:
    if args.admin_privileges and args.command is None:
        args.command = "admin"
    if args.command is None:
        raise LouHttpError(0, "Choose a command. Try `lou status` or `lou admin`.")

    base_url = resolve_base_url(args)
    api_key = resolve_api_key(args)

    if args.command in {"admin", "senior", "junior"}:
        role = args.command.upper()
        return args.command, request(
            "POST",
            "/api/session/demo-login",
            base_url=base_url,
            api_key=api_key,
            payload={"role": role},
        )

    if args.command == "status":
        return "status", request("GET", "/api/health", base_url=base_url, api_key=api_key)

    if args.command == "playbooks":
        return "playbooks", request("GET", "/api/playbooks", base_url=base_url, api_key=api_key)

    if args.command == "review":
        return "review", request("GET", "/api/review", base_url=base_url, api_key=api_key)

    if args.command == "commits":
        return "commits", request("GET", "/api/commits", base_url=base_url, api_key=api_key)

    if args.command == "command":
        payload = {"command": args.text}
        if args.playbook_id:
            payload["playbook_id"] = args.playbook_id
        return "command", request("POST", "/api/lou-command", base_url=base_url, api_key=api_key, payload=payload)

    if args.command == "keys":
        if args.keys_command == "create":
            return "keys-create", request(
                "POST",
                "/api/api-keys",
                base_url=base_url,
                api_key=api_key,
                payload={"name": args.name, "role": args.role},
            )
        if args.keys_command == "list":
            return "keys-list", request("GET", "/api/api-keys", base_url=base_url, api_key=api_key)
        if args.keys_command == "revoke":
            return "keys-revoke", request(
                "DELETE",
                f"/api/api-keys/{args.key_id}",
                base_url=base_url,
                api_key=api_key,
            )
        if args.keys_command == "use":
            save_api_key(args.api_key)
            return "keys-use", {"saved": True}
        raise LouHttpError(0, "Choose a keys command: create, list, revoke, or use.")

    raise LouHttpError(0, f"Unknown command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    if (
        sys.stderr.isatty()
        and os.environ.get("LOU_SUPPRESS_DEPRECATION") != "1"
    ):
        print(DEPRECATION_NOTICE, file=sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        command, payload = execute(args)
    except LouHttpError as error:
        prefix = f"{error.status} " if error.status else ""
        print(f"{prefix}{error.detail}", file=sys.stderr)
        return 1

    if args.json:
        print_json(payload)
    else:
        print(readable(command, payload, base_url=resolve_base_url(args)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
