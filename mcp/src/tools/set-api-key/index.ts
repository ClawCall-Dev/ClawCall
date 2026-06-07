import { setApiKey } from '../../clawcall/key-store.js';
import { TOOLS } from '../../config/metadata.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { SetApiKeyInput, SetApiKeyOutput } from './types.js';

/**
 * Write a user-supplied key to the shared config file (a user-supplied key
 * overrides the saved one). LOCAL only. NEVER echoes the key back — it must not
 * land in conversation history or logs. `setApiKey` merge-preserves
 * `user_phone_number`.
 */
export const tool: ToolDef = {
  name: 'set_api_key',
  description: TOOLS.set_api_key.description,
  annotations: { readOnlyHint: false },
  inputSchema,
  async execute(args: SetApiKeyInput): Promise<SetApiKeyOutput> {
    await setApiKey(args.api_key);
    return { ok: true };
  },
};
