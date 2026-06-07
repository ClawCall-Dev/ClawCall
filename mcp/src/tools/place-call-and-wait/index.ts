import { clawcallFetch } from '../../clawcall/client.js';
import { ClawCallError } from '../../clawcall/errors.js';
import { presentGetCall } from '../../clawcall/present.js';
import { TOOLS } from '../../config/metadata.js';
import {
  WAIT_DEFAULT_SECONDS,
  WAIT_CEILING_SECONDS,
} from '../../config/env.js';
import { pollUntilFinalized, type ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { PlaceCallAndWaitInput, PlaceCallStillRunning } from './types.js';

/**
 * OPTIONAL convenience for a SINGLE foreground call: place it, then poll
 * `get_call` internally until finalized OR a hard wall-clock cap. On cap it
 * degrades to exactly the non-blocking contract — `{ still_running, call_id }`
 * with a hint to keep polling `get_call`. NOT for campaigns (use `place_call`
 * + `get_call` fan-out for parallel interchangeable info-gathering calls).
 */
export const tool: ToolDef = {
  name: 'place_call_and_wait',
  description: TOOLS.place_call_and_wait.description,
  annotations: { openWorldHint: true },
  inputSchema,
  async execute(
    args: PlaceCallAndWaitInput,
  ): Promise<Record<string, unknown> | PlaceCallStillRunning> {
    const requested = args.max_wait_seconds ?? WAIT_DEFAULT_SECONDS;
    const wait = Math.min(Math.max(requested, 5), WAIT_CEILING_SECONDS);

    const body: Record<string, unknown> = { to: args.to, task: args.task };
    if (args.voice !== undefined) body.voice = args.voice;
    if (args.personality !== undefined) body.personality = args.personality;
    if (args.greeting !== undefined) body.greeting = args.greeting;
    if (args.bridge_number !== undefined) body.bridge_number = args.bridge_number;

    const { json } = await clawcallFetch('/call', { method: 'POST', body });
    const j = (json ?? {}) as { id?: string; call_id?: string };
    const callId = (j.id ?? j.call_id) as string;

    // The call is already PLACED — `callId` is the single surface of a live,
    // possibly-ringing call (quota/billing already consumed). A transient poll
    // failure (502/503/429/5xx, or a network error) must NOT throw and drop the
    // id, or the model can never resume polling or hang up the stuck call. On
    // any such interruption, degrade to the non-blocking contract carrying the
    // id. Only a genuinely non-retryable envelope (auth / not_found) re-throws,
    // since those need their personalized action URLs surfaced verbatim.
    let outcome: Awaited<ReturnType<typeof pollUntilFinalized>>;
    try {
      outcome = await pollUntilFinalized(callId, wait);
    } catch (err) {
      if (err instanceof ClawCallError && !err.retryable) {
        throw err;
      }
      return {
        still_running: true,
        call_id: callId,
        last_lifecycle: 'unknown',
        hint: 'a transient error interrupted the wait; poll get_call with this id',
      };
    }

    if (outcome.finalized) {
      const view = presentGetCall(
        outcome.result.json,
        outcome.result.headers,
      ) as Record<string, unknown>;
      return { ...view, call_id: callId };
    }

    return {
      still_running: true,
      call_id: callId,
      last_lifecycle: outcome.lastLifecycle,
      hint: 'still running, poll get_call with this id',
    };
  },
};
