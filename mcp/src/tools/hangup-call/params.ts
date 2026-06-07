import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import type { HangupCallInput } from './types.js';

const P = TOOLS.hangup_call.params;

/** Raw zod shape for `hangup_call`. */
export const inputSchema = {
  call_id: z.string().min(1).describe(P.call_id),
} as const;

export type { HangupCallInput };
