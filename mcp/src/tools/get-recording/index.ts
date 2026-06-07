import { resolveRecordingUrl } from '../../clawcall/present.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { GetRecordingInput, GetRecordingOutput } from './types.js';

/**
 * Durable recording access (no 10-minute window). Returns a URL/handle resolved
 * from the server's 302 redirect target — never inline audio bytes. A 404 may
 * be a permission denial, not absence.
 */
export const tool: ToolDef = {
  name: 'get_recording',
  description: TOOLS.get_recording.description,
  annotations: { readOnlyHint: true, openWorldHint: true },
  inputSchema,
  async execute(args: GetRecordingInput): Promise<GetRecordingOutput> {
    return (await resolveRecordingUrl(args.call_id)) as GetRecordingOutput;
  },
};
