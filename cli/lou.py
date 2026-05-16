#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import urllib.request


def request(method: str, path: str, payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://localhost:8000{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Lou demo CLI")
    parser.add_argument("command", choices=["login", "playbooks", "review", "commits"])
    parser.add_argument("--role", default="JUNIOR")
    args = parser.parse_args()

    if args.command == "login":
        print(json.dumps(request("POST", "/api/session/demo-login", {"role": args.role}), indent=2))
    elif args.command == "playbooks":
        print(json.dumps(request("GET", "/api/playbooks"), indent=2))
    elif args.command == "review":
        print(json.dumps(request("GET", "/api/review"), indent=2))
    elif args.command == "commits":
        print(json.dumps(request("GET", "/api/commits"), indent=2))


if __name__ == "__main__":
    main()
