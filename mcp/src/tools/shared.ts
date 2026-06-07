import { z } from 'zod';
import { clawcallFetch, type FetchResult } from '../clawcall/client.js';
import { ClawCallError } from '../clawcall/errors.js';
import { POLL_INTERVAL_MS } from '../config/env.js';

/**
 * Contract every tool module implements. The registry (`tools/index.ts`)
 * iterates over these and wires each into the MCP server via `registerTool`.
 *
 * - `inputSchema` is a RAW zod shape object (`{ field: z.string() }`), NOT a
 *   wrapped `z.object()` — the SDK's `registerTool` expects the raw shape.
 * - `annotations` are MCP tool hints (readOnlyHint, destructiveHint, ...).
 * - `execute` receives the already-validated args and returns a plain object
 *   that the registry JSON-stringifies into an MCP text result.
 */
export interface ToolDef {
  name: string;
  description: string;
  annotations: Record<string, unknown>;
  inputSchema: z.ZodRawShape;
  execute: (args: any) => Promise<unknown>;
}

/** US E.164 phone number, e.g. `+14155550123`. Area-code first digit 2-9. */
export const usPhone = z
  .string()
  .regex(/^\+1[2-9]\d{9}$/, 'US E.164 like +14155550123');

/** The four canonical ClawCall voices. */
export const voiceEnum = z.enum(['jessica', 'sarah', 'chris', 'eric']);

/**
 * `list_calls` `since` filter: an ISO-8601 timestamp WITH a timezone offset
 * (e.g. `...Z` or `...+00:00`). A bare calendar date is rejected — the server
 * expects a full instant.
 */
export const listCallsSince = z.string().datetime({ offset: true });

/** Wrap a plain result object into an MCP `CallToolResult`. */
export function toMcpResult(obj: unknown): any {
  return { content: [{ type: 'text', text: JSON.stringify(obj, null, 2) }] };
}

/**
 * Render a {@link ClawCallError} as an MCP error result. The text carries the
 * human-readable message plus any personalized action URLs and quota object so
 * the calling agent can surface them VERBATIM (they embed the proto-key token).
 */
export function toMcpError(e: ClawCallError): any {
  let text = e.message;
  const action = e.action;
  if (action && typeof action === 'object') {
    if (typeof action.url === 'string' && action.url.length > 0) {
      text += ` Link: ${action.url}`;
    }
    if (typeof action.sign_in_url === 'string' && action.sign_in_url.length > 0) {
      text += ` Sign-in: ${action.sign_in_url}`;
    }
  }
  if (e.quota && typeof e.quota === 'object') {
    text += ` Quota: ${JSON.stringify(e.quota)}`;
  }
  return { content: [{ type: 'text', text }], isError: true };
}

/**
 * Poll `GET /call/:id` every {@link POLL_INTERVAL_MS} until the call reaches
 * `lifecycle === 'finalized'` or the wall-clock budget is exhausted.
 *
 * On finalize, returns the full {@link FetchResult} (json + headers) so the
 * caller can present the terminal view and fold balance headers. On cap,
 * returns the last observed lifecycle so the caller can degrade to the
 * non-blocking "still running, poll get_call" contract.
 *
 * A {@link ClawCallError} (e.g. the call vanished, auth failed) propagates to
 * the caller untouched — UNLESS it is a transient/retryable error (a single
 * stalled or failed poll). Those are swallowed: we re-check the wall-clock
 * deadline and either retry the next tick or cap. Because each underlying
 * fetch is now bounded by REQUEST_TIMEOUT_MS, the deadline is genuinely
 * enforced and the wait cannot park indefinitely on a hung socket.
 */
export async function pollUntilFinalized(
  callId: string,
  maxWaitSec: number,
): Promise<
  | { finalized: true; result: FetchResult }
  | { finalized: false; lastLifecycle: string }
> {
  const deadline = Date.now() + maxWaitSec * 1000;
  let lastLifecycle = 'queued';

  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const result = await clawcallFetch(`/call/${encodeURIComponent(callId)}`, {
        method: 'GET',
      });
      const json = (result.json ?? {}) as { lifecycle?: string };
      if (typeof json.lifecycle === 'string') {
        lastLifecycle = json.lifecycle;
      }
      if (json.lifecycle === 'finalized') {
        return { finalized: true, result };
      }
    } catch (err) {
      // A permanent error (call vanished, auth failed) aborts the wait. A
      // transient one (timeout, 5xx, network) is swallowed so a single stalled
      // poll cannot consume the whole budget or hang past the deadline.
      if (!(err instanceof ClawCallError) || !err.retryable) {
        throw err;
      }
    }
    if (Date.now() >= deadline) {
      return { finalized: false, lastLifecycle };
    }
    await sleep(POLL_INTERVAL_MS);
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
