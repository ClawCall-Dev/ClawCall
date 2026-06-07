import { clawcallFetch } from '../../clawcall/client.js';
import { presentTranscript } from '../../clawcall/present.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { GetCallTranscriptInput, GetCallTranscriptOutput } from './types.js';

/**
 * Opt-in full turn-by-turn transcript array, split out from `get_call` so that
 * frequent (every 3s) polling stays context-cheap. Splits PRESENTATION, not
 * truth — the server returns one transcript array, no summary mode exists.
 */
export const tool: ToolDef = {
  name: 'get_call_transcript',
  description: TOOLS.get_call_transcript.description,
  annotations: { readOnlyHint: true, openWorldHint: true },
  inputSchema,
  async execute(args: GetCallTranscriptInput): Promise<GetCallTranscriptOutput> {
    const { json } = await clawcallFetch(
      `/call/${encodeURIComponent(args.call_id)}`,
      { method: 'GET' },
    );
    return presentTranscript(json) as GetCallTranscriptOutput;
  },
};
