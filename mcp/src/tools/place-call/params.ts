import { usPhone, voiceEnum } from '../shared.js';
import type { PlaceCallInput } from './types.js';
import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';

const P = TOOLS.place_call.params;

/** Raw zod shape for `place_call`. Descriptions are pulled from metadata. */
export const inputSchema = {
  to: usPhone.describe(P.to),
  task: z.string().min(1).describe(P.task),
  voice: voiceEnum.optional().describe(P.voice),
  personality: z.string().optional().describe(P.personality),
  greeting: z.string().optional().describe(P.greeting),
  bridge_number: usPhone.optional().describe(P.bridge_number),
} as const;

export type { PlaceCallInput };
