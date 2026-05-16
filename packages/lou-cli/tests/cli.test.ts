import { mkdtemp, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it, vi } from "vitest";

import { loadConfig, saveConfig } from "../src/config.js";
import { LouClient } from "../src/http.js";
import { runCli } from "../src/cli.js";

function jsonResponse(payload: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(payload), {
    status: init.status ?? 200,
    headers: { "content-type": "application/json", ...(init.headers ?? {}) },
  });
}

describe("config", () => {
  it("writes ~/.lou/config.json with owner-only permissions", async () => {
    const home = await mkdtemp(join(tmpdir(), "lou-cli-home-"));
    const path = await saveConfig(
      {
        apiBase: "http://localhost:8000",
        apiKey: "lou_test",
        openaiKey: "sk-test",
        slngKey: "slng-test",
        allowProviderKeyForwarding: false,
      },
      { home },
    );

    const mode = (await stat(path)).mode & 0o777;
    expect(mode).toBe(0o600);
    expect(JSON.parse(await readFile(path, "utf8"))).toEqual({
      apiBase: "http://localhost:8000",
      apiKey: "lou_test",
      openaiKey: "sk-test",
      slngKey: "slng-test",
      allowProviderKeyForwarding: false,
    });
  });

  it("loads config using environment variables before file values", async () => {
    const home = await mkdtemp(join(tmpdir(), "lou-cli-home-"));
    await saveConfig({ apiBase: "http://from-file", apiKey: "file-key", openaiKey: "file-openai" }, { home });

    const config = await loadConfig({
      home,
      env: {
        LOU_API_BASE: "http://from-env",
        LOU_API_KEY: "env-key",
        LOU_OPENAI_API_KEY: "env-openai",
      },
    });

    expect(config.apiBase).toBe("http://from-env");
    expect(config.apiKey).toBe("env-key");
    expect(config.openaiKey).toBe("env-openai");
  });
});

describe("LouClient", () => {
  it("forwards provider keys to localhost only by default", async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse({ ok: true })));
    const local = new LouClient({
      apiBase: "http://localhost:8000",
      openaiKey: "sk-local",
      slngKey: "slng-local",
      fetch: fetchMock,
    });

    await local.get("/api/health");
    const localHeaders = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(localHeaders.get("X-Lou-OpenAI-Key")).toBe("sk-local");
    expect(localHeaders.get("X-Lou-SLNG-Key")).toBe("slng-local");

    fetchMock.mockClear();
    const remote = new LouClient({
      apiBase: "https://lou.example",
      openaiKey: "sk-remote",
      slngKey: "slng-remote",
      fetch: fetchMock,
    });

    await remote.get("/api/health");
    const remoteHeaders = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(remoteHeaders.has("X-Lou-OpenAI-Key")).toBe(false);
    expect(remoteHeaders.has("X-Lou-SLNG-Key")).toBe(false);
  });

  it("forwards provider keys to remote APIs only when explicitly allowed", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    const client = new LouClient({
      apiBase: "https://lou.example",
      openaiKey: "sk-remote",
      slngKey: "slng-remote",
      allowProviderKeyForwarding: true,
      fetch: fetchMock,
    });

    await client.get("/api/health");

    const headers = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(headers.get("X-Lou-OpenAI-Key")).toBe("sk-remote");
    expect(headers.get("X-Lou-SLNG-Key")).toBe("slng-remote");
  });

  it("uploads review artifacts as multipart form data", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(new Blob(["zip-bytes"]), {
        status: 200,
        headers: { "content-type": "application/zip" },
      }),
    );
    const client = new LouClient({ apiBase: "http://localhost:8000", fetch: fetchMock });
    const file = await mkdtemp(join(tmpdir(), "lou-cli-contract-")).then(async (dir) => {
      const path = join(dir, "contract.pdf");
      await writeFile(path, "contract text");
      return path;
    });

    await client.reviewContract(file, "pb-saas");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8000/api/contracts/review-artifact");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(fetchMock.mock.calls[0][1].body).toBeInstanceOf(FormData);
  });
});

describe("runCli", () => {
  it("prints JSON and suppresses progress output when --json is used", async () => {
    const stdout: string[] = [];
    const stderr: string[] = [];
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));

    const code = await runCli(["--json", "status"], {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: (text) => stdout.push(text),
      stderr: (text) => stderr.push(text),
      fetch: fetchMock,
      isTTY: true,
    });

    expect(code).toBe(0);
    expect(stdout.join("")).toBe('{"status":"ok"}\n');
    expect(stderr.join("")).toBe("");
  });

  it("routes commit, push, edit, review approval, export, and fuzzy command calls", async () => {
    const calls: string[] = [];
    const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = input.toString();
      calls.push(`${init?.method ?? "GET"} ${new URL(url).pathname}`);
      return jsonResponse({ ok: true });
    });
    const baseOptions = {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: () => undefined,
      stderr: () => undefined,
      fetch: fetchMock,
      isTTY: false,
    };

    await runCli(["commit", "prop-1"], baseOptions);
    await runCli(["push", "prop-2"], baseOptions);
    await runCli(["edit", "pb-saas", "--position", "pos-1", "--set", "Preferred Position=Updated"], baseOptions);
    await runCli(["review", "approve", "prop-3"], baseOptions);
    await runCli(["review", "reject", "prop-4"], baseOptions);
    await runCli(["export", "json"], baseOptions);
    await runCli(["command", "export the playbook"], baseOptions);

    expect(calls).toEqual([
      "POST /api/review/prop-1/approve",
      "POST /api/review/prop-2/approve",
      "PATCH /api/playbooks/pb-saas/positions/pos-1",
      "POST /api/review/prop-3/approve",
      "POST /api/review/prop-4/reject",
      "GET /api/export/json",
      "POST /api/lou-command",
    ]);
  });

  it("rejects malformed api-base values from configure", async () => {
    const stderr: string[] = [];
    const code = await runCli(["configure", "--api-base", "not-a-url"], {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: () => undefined,
      stderr: (text) => stderr.push(text),
      fetch: vi.fn(),
      isTTY: false,
    });
    expect(code).toBe(1);
    expect(stderr.join("")).toMatch(/Invalid --api-base/);
  });

  it("parses error envelope from backend hardening responses", async () => {
    const stderr: string[] = [];
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "FORBIDDEN", message: "SENIOR access required" } }), {
        status: 403,
        headers: { "content-type": "application/json" },
      }),
    );
    const code = await runCli(["review"], {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: () => undefined,
      stderr: (text) => stderr.push(text),
      fetch: fetchMock,
      isTTY: false,
    });
    expect(code).toBe(1);
    expect(stderr.join("")).toMatch(/403 SENIOR access required/);
  });

  it("routes new commands: login, brain, contracts, keys, voice transcript", async () => {
    const calls: string[] = [];
    const fetchMock = vi.fn(async (input: string | URL | Request, init?: RequestInit) => {
      const url = input.toString();
      calls.push(`${init?.method ?? "GET"} ${new URL(url).pathname}`);
      return jsonResponse({ ok: true });
    });
    const baseOptions = {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: () => undefined,
      stderr: () => undefined,
      fetch: fetchMock,
      isTTY: false,
    };

    await runCli(["login", "--role", "senior"], baseOptions);
    await runCli(["brain"], baseOptions);
    await runCli(["contracts", "list"], baseOptions);
    await runCli(["contracts", "show", "c-1"], baseOptions);
    await runCli(["keys", "list"], baseOptions);
    await runCli(["keys", "create", "--name", "ci", "--role", "ADMIN"], baseOptions);
    await runCli(["keys", "revoke", "key-1"], baseOptions);
    await runCli(["voice", "transcript", "--playbook", "pb-1", "--text", "hello"], baseOptions);
    await runCli(["review", "submit", "--playbook", "pb-1", "--topic", "Scope", "--text", "..."], baseOptions);

    expect(calls).toEqual([
      "POST /api/session/demo-login",
      "GET /api/company-brain",
      "GET /api/contracts",
      "GET /api/contracts/c-1",
      "GET /api/api-keys",
      "POST /api/api-keys",
      "DELETE /api/api-keys/key-1",
      "POST /api/voice/transcript",
      "POST /api/review/proposals",
    ]);
  });

  it("verbose flag prints method and url to stderr", async () => {
    const stderr: string[] = [];
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: "ok" }));
    await runCli(["--verbose", "status"], {
      env: {},
      home: await mkdtemp(join(tmpdir(), "lou-cli-home-")),
      stdout: () => undefined,
      stderr: (text) => stderr.push(text),
      fetch: fetchMock,
      isTTY: false,
    });
    expect(stderr.join("")).toMatch(/GET http:\/\/localhost:8000\/api\/health/);
  });
});
