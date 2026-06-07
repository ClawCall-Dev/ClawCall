import { clawcallFetch } from '../../clawcall/client.js';
import { ClawCallError } from '../../clawcall/errors.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { HangupCallInput, HangupCallOutput } from './types.js';

/**
 * Cancel or hang up a call you initiated. Idempotent: an already-terminal call
 * (HTTP 409 / conflict envelope) is treated as a successful no-op. Any other
 * ClawCall error (e.g. `not_found`) propagates so the agent sees the real cause.
 */
export const tool: ToolDef = {
  name: 'hangup_call',
  description: TOOLS.hangup_call.description,
  annotations: {
    readOnlyHint: false,
    destructiveHint: true,
    idempotentHint: true,
    openWorldHint: true,
  },
  inputSchema,
  async execute(args: HangupCallInput): Promise<HangupCallOutput> {
    try {
      const { json } = await clawcallFetch(
        `/call/${encodeURIComponent(args.call_id)}/hangup`,
        { method: 'POST' },
      );
      const j = (json ?? {}) as { status?: string; message?: string };
      return {
        success: true,
        call_id: args.call_id,
        status: j.status ?? 'unknown',
        message: j.message ?? '',
      };
    } catch (e) {
      if (e instanceof ClawCallError && isAlreadyTerminal(e)) {
        return {
          success: true,
          call_id: args.call_id,
          status: 'already_terminal',
          message: 'no-op',
        };
      }
      throw e;
    }
  },
};

/** True when the error means the call already ended (so hangup is a no-op). */
function isAlreadyTerminal(e: ClawCallError): boolean {
  if (e.status === 409) return true;
  const code = e.code;
  return code === 'conflict' || code === 'already_terminal';
}
