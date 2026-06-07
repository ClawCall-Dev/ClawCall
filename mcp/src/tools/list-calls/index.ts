import { clawcallFetch } from '../../clawcall/client.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { ListCallsInput, ListCallsOutput } from './types.js';

/**
 * List call history (account-linked keys only — a proto-key without a linked
 * userId gets 401; inbound needs Unlimited Reserve Plus). Pass-through
 * pagination: forwards the page the server returns, never fetches all.
 */
export const tool: ToolDef = {
  name: 'list_calls',
  description: TOOLS.list_calls.description,
  annotations: { readOnlyHint: true, openWorldHint: true },
  inputSchema,
  async execute(args: ListCallsInput): Promise<ListCallsOutput> {
    const qs = new URLSearchParams();
    if (args.limit !== undefined) qs.set('limit', String(args.limit));
    if (args.direction !== undefined) qs.set('direction', args.direction);
    if (args.since !== undefined) qs.set('since', args.since);

    const query = qs.toString();
    const path = query ? `/me/calls?${query}` : '/me/calls';

    const { json } = await clawcallFetch(path, { method: 'GET' });
    return (json ?? {}) as ListCallsOutput;
  },
};
