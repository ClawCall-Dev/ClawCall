import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import type { GetCallInput } from './types.js';

const P = TOOLS.get_call.params;

/** Raw zod shape for `get_call`. */
export const inputSchema = {
  call_id: z.string().min(1).describe(P.call_id),
} as const;

export type { GetCallInput };
