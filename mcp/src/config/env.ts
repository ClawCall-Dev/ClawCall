/**
 * Read env once. Centralizes all environment-derived configuration so the
 * rest of the package never touches `process.env` directly.
 *
 * NOTE: ENV_API_KEY is consumed by key-store's resolveApiKey (key-store
 * imports it from here); it is not used for injection in this module. It is
 * exported so the single key resolver can layer it as the operator override.
 */

/** Parse an integer env var, falling back to `def`, then clamping to [min, max]. */
function clampInt(
  raw: string | undefined,
  def: number,
  min: number,
  max: number,
): number {
  const n = raw === undefined ? NaN : Number.parseInt(raw, 10);
  const value = Number.isFinite(n) ? n : def;
  return Math.min(max, Math.max(min, value));
}

export const BASE_URL =
  process.env.CLAWCALL_BASE_URL ?? 'https://api.clawcall.dev';

export const FRONTEND_URL =
  process.env.CLAWCALL_FRONTEND_URL ?? 'https://clawcall.dev';

/**
 * Operator/CI override. When set, it shadows the persisted key file. The live
 * value is read directly from `process.env` inside key-store's resolveApiKey
 * (so a key exported after start still applies); this export is retained as the
 * documented config surface and is NOT used for header injection here.
 */
export const ENV_API_KEY = process.env.CLAWCALL_API_KEY?.trim() || undefined;

/** Fixed poll cadence for in-flight call status (matches the skill's 3s contract). */
export const POLL_INTERVAL_MS = 3000;

/**
 * Per-request network timeout (ms). Node's global fetch has NO default timeout,
 * so a server that accepts the TCP connection but never responds would otherwise
 * hang a request forever — defeating place_call_and_wait's hard cap. Every
 * individual fetch in clawcallFetch is bounded by this via an AbortController.
 * Default 30s, host-tunable, clamped to [1s, 120s].
 */
export const REQUEST_TIMEOUT_MS = clampInt(
  process.env.CLAWCALL_REQUEST_TIMEOUT_MS,
  30_000,
  1_000,
  120_000,
);

/** Default hard cap for place_call_and_wait, host-tunable, clamped to [5, 600]. */
export const WAIT_DEFAULT_SECONDS = clampInt(
  process.env.CLAWCALL_WAIT_DEFAULT,
  180,
  5,
  600,
);

/** Ceiling for max_wait_seconds, clamped to [5, 600]. */
export const WAIT_CEILING_SECONDS = clampInt(
  process.env.CLAWCALL_WAIT_CEILING,
  240,
  5,
  600,
);
