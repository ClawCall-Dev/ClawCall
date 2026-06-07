import { clawcallFetch } from '../../clawcall/client.js';
import { balanceFromHeaders } from '../../clawcall/present.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { GetBalanceInput, GetBalanceOutput } from './types.js';

/**
 * Cheap account/balance status. Balance lives in response headers; the body may
 * add tier. Do NOT pre-check before every call — place the call and handle
 * errors.
 */
export const tool: ToolDef = {
  name: 'get_balance',
  description: TOOLS.get_balance.description,
  annotations: { readOnlyHint: true, openWorldHint: true },
  inputSchema,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async execute(_args: GetBalanceInput): Promise<GetBalanceOutput> {
    const result = await clawcallFetch('/balance', { method: 'GET' });
    const fromBody =
      result.json && typeof result.json === 'object'
        ? (result.json as Record<string, unknown>)
        : {};
    return {
      ...balanceFromHeaders(result.headers),
      ...fromBody,
    } as GetBalanceOutput;
  },
};
