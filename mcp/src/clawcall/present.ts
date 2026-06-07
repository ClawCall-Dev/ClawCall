/**
 * Presentation helpers. These shape raw REST responses into model-friendly
 * objects WITHOUT mutating truth — get_call strips the unbounded transcript
 * array to keep frequent 3s polls context-cheap, while get_call_transcript
 * returns the full array verbatim. The split is presentation, not truth.
 *
 * No network here except resolveRecordingUrl, which uses the single network
 * writer (clawcallFetch).
 */

import type { Balance, CallResponse, TranscriptEntry } from './types.js';
import { clawcallFetch } from './client.js';
import { normalizeError } from './errors.js';

const TAIL_COUNT = 6;
const TEXT_MAX = 200;

/**
 * Read balance from response headers. Balance is NEVER in the JSON body.
 * Returns only the fields that are present.
 */
export function balanceFromHeaders(headers?: Headers): Balance {
  const out: Balance = {};
  if (!headers) return out;

  const secondsRaw = headers.get('X-ClawCall-Balance-Seconds');
  if (secondsRaw !== null && secondsRaw !== '') {
    const n = Number(secondsRaw);
    if (Number.isFinite(n)) out.balance_seconds = n;
  }

  const tier = headers.get('X-ClawCall-Tier');
  if (tier !== null && tier !== '') {
    out.tier = tier;
  }

  return out;
}

function truncate(text: string): string {
  if (text.length <= TEXT_MAX) return text;
  // Keep the total length (including the ellipsis) within TEXT_MAX.
  return text.slice(0, TEXT_MAX - 1) + '…';
}

/**
 * Shape GET /call/:id for the model. STRIPS the full transcript array and
 * substitutes a bounded `transcript_tail` (last 6 turns, each text truncated
 * to 200 chars) plus `transcript_available`. Folds balance from headers.
 *
 * Terminal calls (lifecycle === 'finalized') additionally include
 * {outcome, outcome_detail, talk_seconds, recording_url}.
 */
export function presentGetCall(
  json: CallResponse,
  headers?: Headers,
): Record<string, unknown> {
  const transcript = json.transcript ?? [];
  const tail = transcript.slice(-TAIL_COUNT).map((entry) => ({
    ...entry,
    text: truncate(entry.text),
  }));

  const out: Record<string, unknown> = {
    id: json.id,
    direction: json.direction,
    lifecycle: json.lifecycle,
    timestamps: json.timestamps,
    transcript_tail: tail,
    transcript_available: (json.transcript?.length ?? 0) > 0,
  };

  const balance = balanceFromHeaders(headers);
  if (balance.balance_seconds !== undefined) {
    out.balance_seconds = balance.balance_seconds;
  }
  if (balance.tier !== undefined) {
    out.tier = balance.tier;
  }

  if (json.lifecycle === 'finalized') {
    out.outcome = json.outcome;
    out.outcome_detail = json.outcome_detail;
    out.talk_seconds = json.talk_seconds;
    out.recording_url = json.recording_url;
  }

  return out;
}

/** Return the full transcript array verbatim. */
export function presentTranscript(json: CallResponse): {
  transcript: TranscriptEntry[];
} {
  return { transcript: json.transcript ?? [] };
}

/**
 * Resolve a durable recording URL from the 302 redirect target.
 * GET /call/:id/recording returns a 302 to a signed/Telnyx URL; we fetch
 * with redirect:'manual' and read the Location header rather than following
 * into the audio bytes.
 */
export async function resolveRecordingUrl(
  callId: string,
): Promise<{ recording_url: string }> {
  const result = await clawcallFetch(`/call/${callId}/recording`, {
    method: 'GET',
    redirect: 'manual',
  });

  const location = result.headers.get('location');
  if (result.status !== 302 || !location) {
    throw normalizeError(result.status, result.json);
  }

  return { recording_url: location };
}
