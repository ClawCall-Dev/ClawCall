import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import type { GetRecordingInput } from './types.js';

const P = TOOLS.get_recording.params;

/** Raw zod shape for `get_recording`. */
export const inputSchema = {
  call_id: z.string().min(1).describe(P.call_id),
} as const;

export type { GetRecordingInput };
