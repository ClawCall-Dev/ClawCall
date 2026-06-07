import { clawcallFetch } from '../../clawcall/client.js';
import { TOOLS, WORKFLOW } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { PlaceCallInput, PlaceCallOutput } from './types.js';

/**
 * Place an outbound US call. THE canonical write and the load-bearing contract:
 * non-blocking, returns a `call_id` immediately, agent polls `get_call`.
 * Proto-key capture on the first anonymous call happens inside `clawcallFetch`.
 */
export const tool: ToolDef = {
  name: 'place_call',
  description: TOOLS.place_call.description,
  annotations: { openWorldHint: true },
  inputSchema,
  async execute(args: PlaceCallInput): Promise<PlaceCallOutput> {
    const body: Record<string, unknown> = { to: args.to, task: args.task };
    if (args.voice !== undefined) body.voice = args.voice;
    if (args.personality !== undefined) body.personality = args.personality;
    if (args.greeting !== undefined) body.greeting = args.greeting;
    if (args.bridge_number !== undefined) body.bridge_number = args.bridge_number;

    const { json } = await clawcallFetch('/call', {
      method: 'POST',
      body,
    });
    const j = (json ?? {}) as { id?: string; call_id?: string; message?: string };

    return {
      call_id: (j.id ?? j.call_id) as string,
      status: 'queued',
      message: j.message,
      workflow: WORKFLOW,
    };
  },
};
