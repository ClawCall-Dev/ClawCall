import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import type { GetCallTranscriptInput } from './types.js';

const P = TOOLS.get_call_transcript.params;

/** Raw zod shape for `get_call_transcript`. */
export const inputSchema = {
  call_id: z.string().min(1).describe(P.call_id),
} as const;

export type { GetCallTranscriptInput };
