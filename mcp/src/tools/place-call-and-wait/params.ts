import { z } from 'zod';
import { usPhone, voiceEnum } from '../shared.js';
import { TOOLS } from '../../config/metadata.js';
import { WAIT_DEFAULT_SECONDS, WAIT_CEILING_SECONDS } from '../../config/env.js';
import type { PlaceCallAndWaitInput } from './types.js';

const P = TOOLS.place_call_and_wait.params;

/** Raw zod shape for `place_call_and_wait` — `place_call` plus a wait budget. */
export const inputSchema = {
  to: usPhone.describe(P.to),
  task: z.string().min(1).describe(P.task),
  voice: voiceEnum.optional().describe(P.voice),
  personality: z.string().optional().describe(P.personality),
  greeting: z.string().optional().describe(P.greeting),
  bridge_number: usPhone.optional().describe(P.bridge_number),
  max_wait_seconds: z
    .number()
    .int()
    .min(5)
    .max(WAIT_CEILING_SECONDS)
    .default(WAIT_DEFAULT_SECONDS)
    .optional()
    .describe(P.max_wait_seconds),
} as const;

export type { PlaceCallAndWaitInput };
