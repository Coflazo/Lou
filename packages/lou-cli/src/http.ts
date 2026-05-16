import { mkdir, readFile, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";
import AdmZip from "adm-zip";

export type FetchLike = (input: string | URL | Request, init?: RequestInit) => Promise<Response>;

export type LouClientOptions = {
  apiBase: string;
  apiKey?: string;
  openaiKey?: string;
  slngKey?: string;
  allowProviderKeyForwarding?: boolean;
  fetch?: FetchLike;
  timeoutMs?: number;
  verbose?: boolean;
  log?: (message: string) => void;
};

export class LouApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code?: string,
  ) {
    super(message);
    this.name = "LouApiError";
  }
}

const DEFAULT_TIMEOUT_MS = 60_000;
const ALLOWED_ARTIFACT_EXTENSIONS = new Set([".json", ".pdf", ".docx", ".png", ".txt"]);

export function validateApiBase(value: string): string {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new LouApiError(0, `Invalid --api-base value: ${value}`);
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new LouApiError(0, "--api-base must be an http:// or https:// URL.");
  }
  if (!url.hostname) {
    throw new LouApiError(0, "--api-base must include a hostname.");
  }
  return value.replace(/\/+$/, "");
}

export class LouClient {
  private readonly fetchImpl: FetchLike;
  private readonly apiBase: string;
  private readonly timeoutMs: number;
  private readonly verbose: boolean;
  private readonly log: (message: string) => void;

  constructor(private readonly options: LouClientOptions) {
    this.apiBase = validateApiBase(options.apiBase);
    this.fetchImpl = options.fetch ?? fetch;
    this.timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.verbose = Boolean(options.verbose);
    this.log = options.log ?? ((message) => process.stderr.write(`${message}\n`));
  }

  get(path: string): Promise<unknown> {
    return this.request("GET", path);
  }

  post(path: string, payload?: unknown): Promise<unknown> {
    return this.request("POST", path, payload);
  }

  patch(path: string, payload?: unknown): Promise<unknown> {
    return this.request("PATCH", path, payload);
  }

  delete(path: string, payload?: unknown): Promise<unknown> {
    return this.request("DELETE", path, payload);
  }

  async download(path: string): Promise<Response> {
    const url = `${this.apiBase}${path}`;
    if (this.verbose) this.log(`GET ${url}`);
    const response = await this.fetchWithTimeout(url, {
      method: "GET",
      headers: this.headers(),
    });
    if (!response.ok) await this.raise(response);
    return response;
  }

  async request(method: string, path: string, payload?: unknown): Promise<unknown> {
    const isFormData = typeof FormData !== "undefined" && payload instanceof FormData;
    const url = `${this.apiBase}${path}`;
    if (this.verbose) this.log(`${method} ${url}`);
    const response = await this.fetchWithTimeout(url, {
      method,
      headers: this.headers(isFormData ? undefined : "application/json"),
      body: payload == null ? undefined : isFormData ? (payload as BodyInit) : JSON.stringify(payload),
    });
    if (!response.ok) await this.raise(response);
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) return response.json();
    if (contentType.includes("application/zip") || contentType.includes("application/octet-stream")) {
      return Buffer.from(await response.arrayBuffer());
    }
    return response.text();
  }

  async reviewContract(filePath: string, playbookId: string): Promise<Buffer> {
    const form = new FormData();
    const data = await readFile(filePath);
    form.append("playbook_id", playbookId);
    form.append("file", new Blob([data]), basename(filePath));
    const url = `${this.apiBase}/api/contracts/review-artifact`;
    if (this.verbose) this.log(`POST ${url}`);
    const response = await this.fetchWithTimeout(url, {
      method: "POST",
      headers: this.headers(),
      body: form,
    });
    if (!response.ok) await this.raise(response);
    return Buffer.from(await response.arrayBuffer());
  }

  async transcribeAudio(filePath: string, playbookId: string, language: string): Promise<unknown> {
    const form = new FormData();
    const data = await readFile(filePath);
    form.append("playbook_id", playbookId);
    form.append("language", language);
    form.append("file", new Blob([data]), basename(filePath));
    return this.request("POST", "/api/voice/audio-transcript", form);
  }

  private headers(contentType?: string): Headers {
    const headers = new Headers();
    if (contentType) headers.set("Content-Type", contentType);
    if (this.options.apiKey) headers.set("Authorization", `Bearer ${this.options.apiKey}`);
    if (this.shouldForwardProviderKeys()) {
      if (this.options.openaiKey) headers.set("X-Lou-OpenAI-Key", this.options.openaiKey);
      if (this.options.slngKey) headers.set("X-Lou-SLNG-Key", this.options.slngKey);
    }
    return headers;
  }

  private shouldForwardProviderKeys(): boolean {
    if (this.options.allowProviderKeyForwarding) return true;
    const url = new URL(this.apiBase);
    return ["localhost", "127.0.0.1", "::1", "0.0.0.0"].includes(url.hostname);
  }

  private async fetchWithTimeout(url: string, init: RequestInit): Promise<Response> {
    if (this.timeoutMs <= 0) return this.fetchImpl(url, init);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeoutMs);
    try {
      return await this.fetchImpl(url, { ...init, signal: controller.signal });
    } catch (error) {
      if ((error as { name?: string })?.name === "AbortError") {
        throw new LouApiError(0, `Request timed out after ${this.timeoutMs}ms`);
      }
      throw error;
    } finally {
      clearTimeout(timer);
    }
  }

  private async raise(response: Response): Promise<never> {
    let message = response.statusText || `HTTP ${response.status}`;
    let code: string | undefined;
    const text = await response.text();
    if (text) {
      try {
        const parsed = JSON.parse(text) as {
          detail?: unknown;
          error?: { code?: string; message?: string };
        };
        if (parsed?.error && typeof parsed.error.message === "string") {
          message = parsed.error.message;
          code = typeof parsed.error.code === "string" ? parsed.error.code : undefined;
        } else if (typeof parsed.detail === "string") {
          message = parsed.detail;
        } else if (parsed.detail) {
          message = JSON.stringify(parsed.detail);
        } else {
          message = JSON.stringify(parsed);
        }
      } catch {
        message = text;
      }
    }
    throw new LouApiError(response.status, message, code);
  }
}

export async function extractReviewArtifact(zipBytes: Buffer, targetDir: string): Promise<string[]> {
  const safeDir = resolve(targetDir);
  await mkdir(safeDir, { recursive: true });
  const archive = new AdmZip(zipBytes);
  const files: string[] = [];
  for (const entry of archive.getEntries()) {
    if (entry.isDirectory) continue;
    const output = resolve(safeDir, entry.entryName);
    if (!output.startsWith(safeDir)) continue;
    const ext = extname(output).toLowerCase();
    if (ALLOWED_ARTIFACT_EXTENSIONS.size > 0 && ext && !ALLOWED_ARTIFACT_EXTENSIONS.has(ext)) continue;
    await mkdir(dirname(output), { recursive: true });
    await writeFile(output, entry.getData());
    files.push(output);
  }
  return files.sort();
}

export function defaultReviewOutputDir(filePath: string): string {
  const name = basename(filePath, extname(filePath)).replace(/[^A-Za-z0-9._-]+/g, "-") || "contract";
  return resolve(process.cwd(), "lou-review", name);
}
