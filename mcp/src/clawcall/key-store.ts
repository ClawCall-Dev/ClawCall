/**
 * Single-writer credential custody over `~/.config/clawcall/key.json`.
 *
 * This module is the ONLY writer of the ClawCall key file. The skill-agent and
 * the MCP-agent share this exact path and schema so that running both does not
 * fork identity.
 *
 * Path:   {XDG_CONFIG_HOME ?? ~/.config}/clawcall/key.json
 * Schema: { api_key?: string; user_phone_number?: string }   (byte-for-byte the
 *         skill's schema — do NOT add fields).
 *
 * The API key is NEVER logged from this module.
 */

import { mkdir, writeFile, rename } from "node:fs/promises";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { randomUUID } from "node:crypto";

/**
 * Operator/CI override, read LIVE from the environment on each resolution so a
 * key exported after process start still shadows the persisted file.
 */
function envApiKey(): string | undefined {
  return process.env.CLAWCALL_API_KEY?.trim() || undefined;
}

/**
 * The persisted credential file shape. Matches the skill exactly — only these
 * two optional fields. Do not extend.
 */
export interface KeyFile {
  api_key?: string;
  user_phone_number?: string;
}

const keyDir = (): string =>
  join(
    process.env.XDG_CONFIG_HOME ?? join(homedir(), ".config"),
    "clawcall",
  );

const keyPath = (): string => join(keyDir(), "key.json");

/**
 * Absolute path to the persisted credential file. Resolved at call time so the
 * value reflects the current `XDG_CONFIG_HOME` (tests rebind it per case).
 */
export function keyFilePath(): string {
  return keyPath();
}

/**
 * Tolerant SYNCHRONOUS read of the key file. Returns `{}` on any error
 * (missing file, corrupt JSON, permission error, non-object payload). Kept
 * synchronous so the request path can resolve the key cheaply per call.
 */
function readKeyFileSync(): KeyFile {
  try {
    const raw = readFileSync(keyPath(), "utf8");
    const parsed = JSON.parse(raw) as unknown;
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed)) {
      return {};
    }

    const record = parsed as Record<string, unknown>;
    const result: KeyFile = {};
    if (typeof record.api_key === "string") {
      result.api_key = record.api_key;
    }
    if (typeof record.user_phone_number === "string") {
      result.user_phone_number = record.user_phone_number;
    }
    return result;
  } catch {
    return {};
  }
}

/**
 * Tolerant read of the persisted key file. Returns `{}` if the file is
 * missing, corrupt, or otherwise unreadable.
 */
export function readKeyFile(): KeyFile {
  return readKeyFileSync();
}

/**
 * Resolve the active API key for the request path:
 *   1. ENV_API_KEY (operator/CI override — shadows the file)
 *   2. persisted api_key from key.json
 *   3. undefined (first place_call goes out unauthenticated)
 *
 * Synchronous so the client can call it per request without async overhead.
 */
export function resolveApiKey(): string | undefined {
  return resolveApiKeyWithSource().key;
}

/** Where a resolved key originated, so callers can gate file mutations. */
export type ApiKeySource = "env" | "file" | "none";

export interface ResolvedApiKey {
  key: string | undefined;
  source: ApiKeySource;
}

/**
 * Resolve the active API key AND report its origin so the request path can
 * decide whether a credential failure may mutate the persisted file.
 *
 * The env override is operator-owned: a 401 on an env key must NEVER delete the
 * user's saved proto-key (a different credential), and clearing the file would
 * be futile anyway because the env key still shadows the now-empty file on the
 * next call. This is the SINGLE source of env-vs-file precedence — callers must
 * not re-derive the ordering.
 */
export function resolveApiKeyWithSource(): ResolvedApiKey {
  const envKey = envApiKey();
  if (envKey) {
    return { key: envKey, source: "env" };
  }

  const file = readKeyFileSync();
  if (file.api_key) {
    return { key: file.api_key, source: "file" };
  }

  return { key: undefined, source: "none" };
}

/**
 * Module-level mutex. All writes serialize through this promise chain so that
 * concurrent first-`place_call`s cannot double-mint a proto-key or clobber
 * `user_phone_number`.
 */
let chain: Promise<void> = Promise.resolve();

interface WriteOptions {
  /** Delete the `api_key` field from the merged result (preserving everything else). */
  clearApiKey?: boolean;
}

/**
 * The SINGLE private writer. Every mutator routes through here.
 *
 * - Serializes via the module-level mutex.
 * - Ensures the key dir exists (0700).
 * - Reads existing file (tolerant) and shallow-merges the patch over it.
 * - On `clearApiKey`, removes only `api_key` while PRESERVING `user_phone_number`.
 * - Writes atomically: temp file (0600) then rename into place.
 */
function writeKeyFile(patch: KeyFile, opts?: WriteOptions): Promise<void> {
  const run = async (): Promise<void> => {
    const dir = keyDir();
    const path = keyPath();
    await mkdir(dir, { recursive: true, mode: 0o700 });

    const existing = readKeyFileSync();
    const merged: KeyFile = { ...existing, ...patch };

    if (opts?.clearApiKey) {
      delete merged.api_key;
    }

    const tmp = `${path}.${process.pid}.${randomUUID()}.tmp`;
    await writeFile(tmp, JSON.stringify(merged, null, 2), { mode: 0o600 });
    await rename(tmp, path);
  };

  chain = chain.then(run, run);
  return chain;
}

/**
 * Persist the auto-issued proto-key captured on receipt from the first
 * anonymous `POST /call`. Merge-preserves `user_phone_number`.
 */
export async function captureProtoKey(apiKey: string): Promise<void> {
  await writeKeyFile({ api_key: apiKey });
}

/**
 * Persist a user-supplied key (honors "user-supplied key overrides saved").
 * Merge-preserves `user_phone_number`. Never echoes the key.
 */
export async function setApiKey(apiKey: string): Promise<void> {
  await writeKeyFile({ api_key: apiKey });
}

/**
 * Clear the saved API key (self-heal on a genuine `invalid_api_key` 401) while
 * preserving `user_phone_number` so the next call re-provisions a fresh
 * proto-key without losing the user's identity hint.
 */
export async function clearApiKey(): Promise<void> {
  await writeKeyFile({}, { clearApiKey: true });
}
