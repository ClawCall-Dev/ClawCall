import { z } from 'zod';
import { TOOLS } from '../../config/metadata.js';
import type { SetApiKeyInput } from './types.js';

const P = TOOLS.set_api_key.params;

/** Raw zod shape for `set_api_key`. */
export const inputSchema = {
  api_key: z.string().startsWith('clawcall_sk_').describe(P.api_key),
} as const;

export type { SetApiKeyInput };
