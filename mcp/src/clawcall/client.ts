/**
 * The ONE network writer for the whole package. Every HTTP call to the
 * ClawCall REST API flows through clawcallFetch — this is the single point
 * for API-key injection, proto-key capture-on-receipt, error normalization,
 * and 401 self-heal.
 *
 * Key custody lives in the key-store bundle; this module depends on it ONLY
 * through the three named imports below.
 */

import { BASE_URL, REQUEST_TIMEOUT_MS } from '../config/env.js';
import { log } from '../logger.js';
import {
  resolveApiKeyWithSource,
  captureProtoKey,
  clearApiKey,
} from './key-store.js';
import { ClawCallError, normalizeError } from './errors.js';

export interface FetchOpts {
  method?: string;
  body?: unknown;
  redirect?: 'follow' | 'manual';
}

export interface FetchResult<T = any> {
  status: number;
  json: T;
  headers: Headers;
}

/** Defensively parse a response body as JSON. Returns {} for empty/non-JSON. */
async function parseJsonDefensive(res: Response): Promise<any> {
  let text: string;
  try {
    text = await res.text();
  } catch {
    return {};
  }
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function clawcallFetch<T = any>(
  path: string,
  opts: FetchOpts = {},
): Promise<FetchResult<T>> {
  const { body, method } = opts;
  const redirect = opts.redirect ?? 'follow';

  // 1. Resolve key (and its origin) and build headers. The source decides
  //    whether a later 401 may mutate the persisted file: an env key is
  //    operator-owned and must never trigger deletion of the saved proto-key.
  const { key, source: keySource } = resolveApiKeyWithSource();
  const keyWasSent = !!key;
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (key) headers['X-Api-Key'] = key;

  // 2. Issue the request, bounded by a hard per-request timeout. Node's global
  //    fetch has NO default timeout, so without this an open-but-stalled socket
  //    (wedged upstream, transparent proxy, half-open connection) would hang the
  //    call forever — silently breaking place_call_and_wait's wall-clock cap,
  //    since pollUntilFinalized only re-checks its deadline BETWEEN fetches.
  //    Wrap network failures AND timeouts in the same retryable network_error.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(BASE_URL + path, {
      method: method ?? 'GET',
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      redirect,
      signal: controller.signal,
    });
  } catch (err) {
    const timedOut =
      controller.signal.aborted ||
      (err instanceof Error && err.name === 'AbortError');
    if (timedOut) {
      log.error('network_timeout', method ?? 'GET', path, `${REQUEST_TIMEOUT_MS}ms`);
      throw new ClawCallError({
        status: 0,
        code: 'network_error',
        message: `Network request timed out after ${REQUEST_TIMEOUT_MS}ms.`,
        retryable: true,
      });
    }
    log.error('network_error', method ?? 'GET', path, String(err));
    throw new ClawCallError({
      status: 0,
      code: 'network_error',
      message: 'Network request failed.',
      retryable: true,
    });
  } finally {
    clearTimeout(timer);
  }

  // 3. Manual-redirect mode (get_recording): on an ACTUAL redirect (3xx with a
  //    Location header) return without parsing JSON — the caller reads
  //    headers.get('location') and never touches the body. On ANYTHING else
  //    (4xx/5xx error, or a non-redirect 2xx) we must fall through to step 4 so
  //    the body is parsed and the normal error path runs. Otherwise the server's
  //    documented 404 `{error:{code:'recording_not_available', message}}`
  //    envelope is silently dropped and the caller can only ever see a
  //    synthesized `http_404`/`request failed`.
  if (
    redirect === 'manual' &&
    res.status >= 300 &&
    res.status < 400 &&
    res.headers.get('location')
  ) {
    return { status: res.status, json: {} as T, headers: res.headers };
  }

  // 4. Parse the body defensively.
  const json = await parseJsonDefensive(res);

  // 5. Capture-on-receipt: persist the auto-issued proto-key the instant the
  //    first anonymous POST /call returns — BEFORE any poll loop — so a killed
  //    handler never loses the single-surfaced secret. Surfaced on BOTH the
  //    JSON `api_key` field AND the X-ClawCall-Api-Key response header.
  if (method === 'POST' && path === '/call' && !keyWasSent) {
    const fromBody =
      json && typeof json === 'object' && typeof json.api_key === 'string'
        ? (json.api_key as string)
        : undefined;
    const fromHeader = res.headers.get('X-ClawCall-Api-Key') ?? undefined;
    const found = fromBody || fromHeader || undefined;
    if (found) {
      // Best-effort: the call has ALREADY succeeded (placed/billed/possibly
      // ringing), so a persistence failure (read-only HOME, disk full, ENOTDIR
      // from XDG_CONFIG_HOME pointing at a file, EACCES, sandboxed FS) must
      // NEVER gate returning the result — that would drop both the secret AND
      // the call_id, leaving a live call the agent can neither poll nor hang up.
      // The proto-key is recoverable on the next key-less call; the call_id is
      // not. Swallow the rejection, log it (already redacted) to stderr, and
      // fall through to return the result.
      try {
        await captureProtoKey(found);
      } catch (err) {
        log.error('proto_key_persist_failed', String(err));
      }
    }
  }

  // 6. Error handling.
  if (!res.ok) {
    const code =
      json &&
      typeof json === 'object' &&
      json.error &&
      typeof json.error === 'object'
        ? (json.error as { code?: unknown }).code
        : undefined;

    // Self-heal ONLY on a genuine invalid_api_key 401 envelope, and ONLY when
    // the failing key came from the persisted FILE. Never clear on 5xx/network
    // (transient), and never delete the saved proto-key on behalf of an env
    // override (operator-owned, a DIFFERENT credential): doing so would destroy
    // the user's accumulated identity AND be futile, since the env key still
    // shadows the now-empty file on the next call. For an env-key 401 we emit a
    // redacted diagnostic and leave the file untouched.
    if (res.status === 401 && code === 'invalid_api_key') {
      if (keySource === 'file') {
        await clearApiKey();
      } else if (keySource === 'env') {
        log.error(
          'invalid_api_key_env_override',
          'CLAWCALL_API_KEY rejected (401); saved key left intact',
        );
      }
    }
    throw normalizeError(res.status, json);
  }

  // 7. Success.
  return { status: res.status, json: json as T, headers: res.headers };
}

/**
 * Thin convenience wrapper over `POST /call`. Returns the normalized
 * `{ call_id, ... }` shape (the server surfaces the id as either `id` or
 * `call_id`). Proto-key capture on the first anonymous call happens inside
 * `clawcallFetch`.
 */
export async function placeCall(body: {
  to: string;
  task: string;
  [k: string]: unknown;
}): Promise<{ call_id: string; status: string; message?: string }> {
  const { json } = await clawcallFetch('/call', { method: 'POST', body });
  const j = (json ?? {}) as { id?: string; call_id?: string; message?: string };
  return {
    call_id: (j.id ?? j.call_id) as string,
    status: 'queued',
    message: j.message,
  };
}
