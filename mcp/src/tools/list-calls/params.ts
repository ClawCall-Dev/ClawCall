import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import { listCallsSince } from '../shared.js';
import type { ListCallsInput } from './types.js';

const P = TOOLS.list_calls.params;

/** Raw zod shape for `list_calls`. Pagination is pass-through (never fetch-all). */
export const inputSchema = {
  limit: z.number().int().min(1).max(200).default(25).optional().describe(P.limit),
  direction: z.enum(['inbound', 'outbound']).optional().describe(P.direction),
  since: listCallsSince.optional().describe(P.since),
} as const;

export type { ListCallsInput };
