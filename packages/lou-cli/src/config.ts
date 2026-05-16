import { chmod, mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";

export const DEFAULT_API_BASE = "http://localhost:8000";

export type LouConfig = {
  apiBase?: string;
  apiKey?: string;
  openaiKey?: string;
  slngKey?: string;
  allowProviderKeyForwarding?: boolean;
};

export type ConfigContext = {
  home?: string;
  env?: NodeJS.ProcessEnv | Record<string, string | undefined>;
  warn?: (message: string) => void;
};

export class ConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ConfigError";
  }
}

export function configPath(home = process.env.HOME ?? process.cwd()): string {
  return join(home, ".lou", "config.json");
}

export async function readConfigFile(context: ConfigContext = {}): Promise<LouConfig> {
  const path = configPath(context.home);
  try {
    await warnIfWorldReadable(path, context.warn);
    return JSON.parse(await readFile(path, "utf8")) as LouConfig;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") return {};
    if (error instanceof SyntaxError) return {};
    throw error;
  }
}

export async function loadConfig(
  context: ConfigContext = {},
): Promise<Required<Pick<LouConfig, "apiBase">> & LouConfig> {
  const env = context.env ?? process.env;
  const file = await readConfigFile(context);
  const allowProviderKeyForwarding =
    parseBoolean(env.LOU_ALLOW_PROVIDER_KEY_FORWARDING, "LOU_ALLOW_PROVIDER_KEY_FORWARDING") ??
    file.allowProviderKeyForwarding ??
    false;

  return {
    ...file,
    apiBase: (env.LOU_API_BASE || file.apiBase || DEFAULT_API_BASE).replace(/\/+$/, ""),
    apiKey: env.LOU_API_KEY || file.apiKey,
    openaiKey: env.LOU_OPENAI_API_KEY || env.OPENAI_API_KEY || file.openaiKey,
    slngKey: env.LOU_SLNG_API_KEY || env.SLNG_API_KEY || file.slngKey,
    allowProviderKeyForwarding,
  };
}

export async function saveConfig(config: LouConfig, context: ConfigContext = {}): Promise<string> {
  const path = configPath(context.home);
  await mkdir(dirname(path), { recursive: true, mode: 0o700 });
  await writeFile(path, `${JSON.stringify(config, null, 2)}\n`, { mode: 0o600 });
  await chmod(path, 0o600);
  return path;
}

async function warnIfWorldReadable(path: string, warn?: (message: string) => void): Promise<void> {
  if (process.platform === "win32") return;
  try {
    const info = await stat(path);
    const worldOrGroupReadable = (info.mode & 0o077) !== 0;
    if (worldOrGroupReadable) {
      const message = `[lou] warning: ${path} permissions ${(info.mode & 0o777).toString(8)} are looser than 0600. Run 'chmod 600 ${path}'.`;
      (warn ?? ((text) => process.stderr.write(`${text}\n`)))(message);
    }
  } catch {
    /* ignore — file may not exist yet */
  }
}

function parseBoolean(value: string | undefined, label?: string): boolean | undefined {
  if (value == null || value === "") return undefined;
  const normalised = value.toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalised)) return true;
  if (["0", "false", "no", "off"].includes(normalised)) return false;
  throw new ConfigError(
    `${label ?? "boolean"} must be one of 1|true|yes|on|0|false|no|off; got '${value}'.`,
  );
}
