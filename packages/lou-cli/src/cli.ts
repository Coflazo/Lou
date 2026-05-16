import { join } from "node:path";
import { loadConfig, readConfigFile, saveConfig, type LouConfig } from "./config.js";
import {
  defaultReviewOutputDir,
  extractReviewArtifact,
  LouApiError,
  LouClient,
  validateApiBase,
  type FetchLike,
} from "./http.js";
import { Progress } from "./progress.js";

type CliIO = {
  stdout: (text: string) => void;
  stderr: (text: string) => void;
};

export type CliContext = Partial<CliIO> & {
  env?: NodeJS.ProcessEnv | Record<string, string | undefined>;
  home?: string;
  fetch?: FetchLike;
  isTTY?: boolean;
};

type ParsedArgs = {
  json: boolean;
  verbose: boolean;
  timeoutMs?: number;
  baseUrl?: string;
  apiKey?: string;
  command?: string;
  args: string[];
};

const ROLES = ["JUNIOR", "SENIOR", "ADMIN"] as const;

export async function runCli(argv: string[], context: CliContext = {}): Promise<number> {
  const io: CliIO = {
    stdout: context.stdout ?? ((text) => process.stdout.write(text)),
    stderr: context.stderr ?? ((text) => process.stderr.write(text)),
  };
  const parsed = parseGlobalArgs(argv);
  const env = context.env ?? process.env;

  try {
    if (!parsed.command) throw new LouApiError(0, "Choose a command. Try `lou status`.");
    if (parsed.command === "configure") {
      const result = await configure(parsed.args, {
        home: context.home,
        env,
        warn: (message) => io.stderr(`${message}\n`),
      });
      io.stdout(formatOutput(result, parsed.json, "Configuration saved."));
      return 0;
    }

    const config = await loadConfig({
      home: context.home,
      env,
      warn: (message) => io.stderr(`${message}\n`),
    });
    const client = new LouClient({
      apiBase: parsed.baseUrl ?? config.apiBase,
      apiKey: parsed.apiKey ?? config.apiKey,
      openaiKey: config.openaiKey,
      slngKey: config.slngKey,
      allowProviderKeyForwarding: config.allowProviderKeyForwarding,
      fetch: context.fetch,
      timeoutMs: parsed.timeoutMs,
      verbose: parsed.verbose,
      log: (message) => io.stderr(`${message}\n`),
    });
    const animate = !parsed.json && Boolean(context.isTTY ?? process.stderr.isTTY) && !env.CI;
    const progress = new Progress({ enabled: animate, write: io.stderr });
    const payload = await executeCommand(parsed.command, parsed.args, client, progress);
    io.stdout(formatOutput(payload, parsed.json, readable(parsed.command, payload)));
    return 0;
  } catch (error) {
    if (error instanceof LouApiError) {
      io.stderr(`${error.status ? `${error.status} ` : ""}${error.message}\n`);
      return 1;
    }
    io.stderr(`${error instanceof Error ? error.message : String(error)}\n`);
    return 1;
  }
}

async function executeCommand(command: string, args: string[], client: LouClient, progress: Progress): Promise<unknown> {
  switch (command) {
    case "status":
      return client.get("/api/health");
    case "login":
      return login(args, client);
    case "playbooks":
      return playbooks(args, client);
    case "contracts":
      return contracts(args, client);
    case "review":
      return review(args, client);
    case "commit":
    case "push":
      return approve(args[0], client);
    case "edit":
      return edit(args, client);
    case "export":
      return exportFormat(args, client);
    case "command":
      return client.post("/api/lou-command", { command: args.join(" ") });
    case "brain":
      return client.get("/api/company-brain");
    case "voice":
      return voice(args, client);
    case "keys":
      return keys(args, client);
    case "review-contract":
      return reviewContract(args, client, progress);
    default:
      throw new LouApiError(0, `Unknown command: ${command}`);
  }
}

async function configure(args: string[], context: { home?: string; env?: NodeJS.ProcessEnv | Record<string, string | undefined>; warn?: (message: string) => void }) {
  const current = await readConfigFile(context);
  const next: LouConfig = { ...current };
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--api-base") next.apiBase = validateApiBase(requireValue(args, ++index, arg));
    else if (arg === "--api-key") next.apiKey = requireValue(args, ++index, arg);
    else if (arg === "--openai-key") next.openaiKey = requireValue(args, ++index, arg);
    else if (arg === "--slng-key") next.slngKey = requireValue(args, ++index, arg);
    else if (arg === "--allow-provider-key-forwarding") next.allowProviderKeyForwarding = true;
    else throw new LouApiError(0, `Unknown configure option: ${arg}`);
  }
  const path = await saveConfig(next, context);
  return { path, config: redact(next) };
}

function login(args: string[], client: LouClient): Promise<unknown> {
  let role: string | undefined;
  for (let index = 0; index < args.length; index += 1) {
    if (args[index] === "--role") role = requireValue(args, ++index, "--role");
    else throw new LouApiError(0, `Unknown login option: ${args[index]}`);
  }
  if (!role) throw new LouApiError(0, "login requires --role JUNIOR|SENIOR|ADMIN.");
  const upper = role.toUpperCase();
  if (!ROLES.includes(upper as typeof ROLES[number])) {
    throw new LouApiError(0, `--role must be one of ${ROLES.join(", ")}.`);
  }
  return client.post("/api/session/demo-login", { role: upper });
}

function playbooks(args: string[], client: LouClient): Promise<unknown> {
  if (args[0] === "show") {
    const id = requireValue(args, 1, "playbooks show");
    return client.get(`/api/playbooks/${encodeURIComponent(id)}`);
  }
  if (args[0] === "import") return client.post("/api/playbooks/import");
  if (args.length > 0) throw new LouApiError(0, `Unknown playbooks command: ${args[0]}`);
  return client.get("/api/playbooks");
}

function contracts(args: string[], client: LouClient): Promise<unknown> {
  if (args[0] === "show") {
    const id = requireValue(args, 1, "contracts show");
    return client.get(`/api/contracts/${encodeURIComponent(id)}`);
  }
  if (args[0] === "list" || args.length === 0) return client.get("/api/contracts");
  throw new LouApiError(0, `Unknown contracts command: ${args[0]}`);
}

function review(args: string[], client: LouClient): Promise<unknown> {
  if (args[0] === "approve") return approve(args[1], client);
  if (args[0] === "reject") {
    const id = requireValue(args, 1, "review reject");
    return client.post(`/api/review/${encodeURIComponent(id)}/reject`, { reason: null });
  }
  if (args[0] === "submit") return submitProposal(args.slice(1), client);
  if (args.length > 0) throw new LouApiError(0, `Unknown review command: ${args[0]}`);
  return client.get("/api/review");
}

function approve(id: string | undefined, client: LouClient): Promise<unknown> {
  const proposalId = requireValue([id], 0, "proposal id");
  return client.post(`/api/review/${encodeURIComponent(proposalId)}/approve`, { edited_text: null });
}

function submitProposal(args: string[], client: LouClient): Promise<unknown> {
  let playbookId = "";
  let positionId: string | undefined;
  let topic = "";
  let proposedText = "";
  let rationale: string | undefined;
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--playbook") playbookId = requireValue(args, ++index, arg);
    else if (arg === "--position") positionId = requireValue(args, ++index, arg);
    else if (arg === "--topic") topic = requireValue(args, ++index, arg);
    else if (arg === "--text") proposedText = requireValue(args, ++index, arg);
    else if (arg === "--rationale") rationale = requireValue(args, ++index, arg);
    else throw new LouApiError(0, `Unknown review submit option: ${arg}`);
  }
  if (!playbookId) throw new LouApiError(0, "review submit requires --playbook.");
  if (!topic) throw new LouApiError(0, "review submit requires --topic.");
  if (!proposedText) throw new LouApiError(0, "review submit requires --text.");
  return client.post("/api/review/proposals", {
    playbook_id: playbookId,
    position_id: positionId,
    topic,
    proposed_text: proposedText,
    rationale,
    source: "cli",
  });
}

function edit(args: string[], client: LouClient): Promise<unknown> {
  const playbookId = requireValue(args, 0, "edit");
  let positionId = "";
  const columns: Record<string, string> = {};
  for (let index = 1; index < args.length; index += 1) {
    if (args[index] === "--position") positionId = requireValue(args, ++index, "--position");
    else if (args[index] === "--set") {
      const assignment = requireValue(args, ++index, "--set");
      const equals = assignment.indexOf("=");
      if (equals <= 0) throw new LouApiError(0, "--set expects Column=Value");
      columns[assignment.slice(0, equals)] = assignment.slice(equals + 1);
    } else {
      throw new LouApiError(0, `Unknown edit option: ${args[index]}`);
    }
  }
  if (!positionId) throw new LouApiError(0, "edit requires --position.");
  if (Object.keys(columns).length === 0) throw new LouApiError(0, "edit requires at least one --set Column=Value.");
  return client.patch(`/api/playbooks/${encodeURIComponent(playbookId)}/positions/${encodeURIComponent(positionId)}`, {
    columns,
  });
}

async function exportFormat(args: string[], client: LouClient): Promise<unknown> {
  const format = requireValue(args, 0, "export");
  if (!["json", "xlsx", "png"].includes(format)) throw new LouApiError(0, "export format must be json, xlsx, or png.");
  return client.download(`/api/export/${format}`).then(async (response) => {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) return response.json();
    const ext = format === "xlsx" ? "xlsx" : "png";
    const path = join(process.cwd(), `lou-export.${ext}`);
    const bytes = Buffer.from(await response.arrayBuffer());
    await import("node:fs/promises").then(({ writeFile }) => writeFile(path, bytes));
    return { path };
  });
}

async function voice(args: string[], client: LouClient): Promise<unknown> {
  const sub = args[0];
  const rest = args.slice(1);
  if (sub === "transcript") return voiceTranscript(rest, client);
  if (sub === "transcribe") return voiceTranscribe(rest, client);
  if (sub === "session") return voiceSession(rest, client);
  throw new LouApiError(0, "voice expects: transcript | transcribe | session");
}

async function voiceTranscript(args: string[], client: LouClient): Promise<unknown> {
  let playbookId = "";
  let language = "en";
  let text = "";
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--playbook") playbookId = requireValue(args, ++index, arg);
    else if (arg === "--language") language = requireValue(args, ++index, arg);
    else if (arg === "--text") text = requireValue(args, ++index, arg);
    else throw new LouApiError(0, `Unknown voice transcript option: ${arg}`);
  }
  if (!playbookId) throw new LouApiError(0, "voice transcript requires --playbook.");
  if (!text) throw new LouApiError(0, "voice transcript requires --text.");
  return client.post("/api/voice/transcript", { playbook_id: playbookId, transcript: text, language });
}

async function voiceTranscribe(args: string[], client: LouClient): Promise<unknown> {
  const filePath = requireValue(args, 0, "voice transcribe");
  let playbookId = "";
  let language = "en";
  for (let index = 1; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--playbook") playbookId = requireValue(args, ++index, arg);
    else if (arg === "--language") language = requireValue(args, ++index, arg);
    else throw new LouApiError(0, `Unknown voice transcribe option: ${arg}`);
  }
  if (!playbookId) throw new LouApiError(0, "voice transcribe requires --playbook.");
  return client.transcribeAudio(filePath, playbookId, language);
}

async function voiceSession(args: string[], client: LouClient): Promise<unknown> {
  let playbookId: string | undefined;
  let language = "en";
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--playbook") playbookId = requireValue(args, ++index, arg);
    else if (arg === "--language") language = requireValue(args, ++index, arg);
    else throw new LouApiError(0, `Unknown voice session option: ${arg}`);
  }
  return client.post("/api/voice/session", { playbook_id: playbookId ?? null, language });
}

async function keys(args: string[], client: LouClient): Promise<unknown> {
  const sub = args[0];
  const rest = args.slice(1);
  if (sub === "list" || !sub) return client.get("/api/api-keys");
  if (sub === "create") return keysCreate(rest, client);
  if (sub === "revoke") {
    const id = requireValue(rest, 0, "keys revoke");
    return client.delete(`/api/api-keys/${encodeURIComponent(id)}`);
  }
  if (sub === "use") {
    const token = requireValue(rest, 0, "keys use");
    return saveConfig({ apiKey: token }).then((path) => ({ path, apiKey: "********" }));
  }
  throw new LouApiError(0, "keys expects: list | create | revoke | use");
}

async function keysCreate(args: string[], client: LouClient): Promise<unknown> {
  let name = "";
  let role = "SENIOR";
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--name") name = requireValue(args, ++index, arg);
    else if (arg === "--role") role = requireValue(args, ++index, arg).toUpperCase();
    else throw new LouApiError(0, `Unknown keys create option: ${arg}`);
  }
  if (!name) throw new LouApiError(0, "keys create requires --name.");
  if (!ROLES.includes(role as typeof ROLES[number])) {
    throw new LouApiError(0, `--role must be one of ${ROLES.join(", ")}.`);
  }
  return client.post("/api/api-keys", { name, role });
}

async function reviewContract(args: string[], client: LouClient, progress: Progress): Promise<unknown> {
  const filePath = requireValue(args, 0, "review-contract");
  let playbookId = "";
  let outputDir = defaultReviewOutputDir(filePath);
  for (let index = 1; index < args.length; index += 1) {
    if (args[index] === "--playbook") playbookId = requireValue(args, ++index, "--playbook");
    else if (args[index] === "--out") outputDir = requireValue(args, ++index, "--out");
    else if (args[index] === "-v" || args[index] === "--verbose") continue;
    else throw new LouApiError(0, `Unknown review-contract option: ${args[index]}`);
  }
  if (!playbookId) throw new LouApiError(0, "review-contract requires --playbook.");
  progress.start("Uploading contract");
  const zip = await client.reviewContract(filePath, playbookId);
  progress.stage("Writing reviewed artifacts");
  const files = await extractReviewArtifact(zip, outputDir);
  progress.stop();
  return { outputDir, files };
}

function parseGlobalArgs(argv: string[]): ParsedArgs {
  const parsed: ParsedArgs = { json: false, verbose: false, args: [] };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") parsed.json = true;
    else if (arg === "-v" || arg === "--verbose") parsed.verbose = true;
    else if (arg === "--base-url") parsed.baseUrl = requireValue(argv, ++index, arg);
    else if (arg === "--api-key") parsed.apiKey = requireValue(argv, ++index, arg);
    else if (arg === "--timeout") {
      const raw = requireValue(argv, ++index, arg);
      const value = Number.parseInt(raw, 10);
      if (!Number.isFinite(value) || value < 0) {
        throw new LouApiError(0, "--timeout requires a non-negative integer in milliseconds.");
      }
      parsed.timeoutMs = value;
    } else {
      parsed.command = arg;
      parsed.args = argv.slice(index + 1);
      break;
    }
  }
  return parsed;
}

function formatOutput(payload: unknown, json: boolean, fallback: string): string {
  if (json) return `${JSON.stringify(payload)}\n`;
  if (typeof payload === "string") return `${payload}\n`;
  if (isReviewArtifactPayload(payload)) {
    return [`Saved review artifacts to ${payload.outputDir}.`, ...payload.files.map((file) => `- ${file}`)].join("\n") + "\n";
  }
  return `${fallback}\n`;
}

function readable(command: string, payload: unknown): string {
  if (command === "status" && isRecord(payload)) return `Lou backend is ${payload.status ?? "unknown"}.`;
  if (command === "playbooks" && Array.isArray(payload)) return `Playbooks: ${payload.length}`;
  if (command === "review" && Array.isArray(payload)) return `Review queue: ${payload.length}`;
  if (command === "contracts" && Array.isArray(payload)) return `Contracts: ${payload.length}`;
  if (command === "keys" && Array.isArray(payload)) return `API keys: ${payload.length}`;
  if (command === "export" && isRecord(payload) && typeof payload.path === "string") return `Export saved to ${payload.path}.`;
  if (command === "command" && isRecord(payload) && typeof payload.message === "string") return payload.message;
  if (command === "login" && isRecord(payload) && typeof payload.role === "string") return `Logged in as ${payload.role}.`;
  return JSON.stringify(payload, null, 2);
}

function requireValue(args: Array<string | undefined>, index: number, label: string): string {
  const value = args[index];
  if (!value) throw new LouApiError(0, `${label} requires a value.`);
  return value;
}

function redact(config: LouConfig): LouConfig {
  return {
    ...config,
    apiKey: config.apiKey ? "********" : undefined,
    openaiKey: config.openaiKey ? "********" : undefined,
    slngKey: config.slngKey ? "********" : undefined,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isReviewArtifactPayload(value: unknown): value is { outputDir: string; files: string[] } {
  return isRecord(value) && typeof value.outputDir === "string" && Array.isArray(value.files);
}
