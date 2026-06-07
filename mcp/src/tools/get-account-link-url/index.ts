import { resolveApiKey } from '../../clawcall/key-store.js';
import { TOOLS } from '../../config/metadata.js';
import { FRONTEND_URL } from '../../config/env.js';
import type { ToolDef } from '../shared.js';
import { inputSchema } from './params.js';
import type { GetAccountLinkUrlInput, GetAccountLinkUrlOutput } from './types.js';

/**
 * Build the browser sign-in link that attaches this agent's key / calls /
 * balance / history to a ClawCall account. LOCAL only — reads the SAVED key and
 * mints nothing. Faithful to the skill contract (`/sign-in?token=<api_key>`).
 */
export const tool: ToolDef = {
  name: 'get_account_link_url',
  description: TOOLS.get_account_link_url.description,
  annotations: { readOnlyHint: true },
  inputSchema,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async execute(_args: GetAccountLinkUrlInput): Promise<GetAccountLinkUrlOutput> {
    const key = await resolveApiKey();
    if (!key) {
      return {
        message:
          'No saved key yet. Place a call first to provision one, then call this again.',
      };
    }
    return { url: `${FRONTEND_URL}/sign-in?token=${key}` };
  },
};
