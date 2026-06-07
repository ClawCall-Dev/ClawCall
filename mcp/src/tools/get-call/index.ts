import { clawcallFetch } from '../../clawcall/client.js';
import { presentGetCall } from '../../clawcall/present.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { GetCallInput, GetCallView } from './types.js';

/**
 * Poll a call's lifecycle and read the high-signal result. The poll/resume
 * primitive — context-cheap by design (the full transcript array is split out
 * to `get_call_transcript`). `outcome` is the PHONE-NETWORK result, NOT task
 * success: read the transcript and judge against the task.
 */
export const tool: ToolDef = {
  name: 'get_call',
  description: TOOLS.get_call.description,
  annotations: { readOnlyHint: true, openWorldHint: true },
  inputSchema,
  async execute(args: GetCallInput): Promise<GetCallView> {
    const { json, headers } = await clawcallFetch(
      `/call/${encodeURIComponent(args.call_id)}`,
      { method: 'GET' },
    );
    return presentGetCall(json, headers) as GetCallView;
  },
};
