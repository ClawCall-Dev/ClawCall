import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { ClawCallError } from '../clawcall/errors.js';
import { toMcpResult, toMcpError, type ToolDef } from './shared.js';

import { tool as placeCall } from './place-call/index.js';
import { tool as placeCallAndWait } from './place-call-and-wait/index.js';
import { tool as getCall } from './get-call/index.js';
import { tool as getCallTranscript } from './get-call-transcript/index.js';
import { tool as hangupCall } from './hangup-call/index.js';
import { tool as listCalls } from './list-calls/index.js';
import { tool as getRecording } from './get-recording/index.js';
import { tool as getBalance } from './get-balance/index.js';
import { tool as getAccountLinkUrl } from './get-account-link-url/index.js';
import { tool as setApiKeyTool } from './set-api-key/index.js';

/** Every tool the ClawCall MCP server exposes (outbound-only v1 surface). */
export const ALL_TOOLS: ToolDef[] = [
  placeCall,
  placeCallAndWait,
  getCall,
  getCallTranscript,
  hangupCall,
  listCalls,
  getRecording,
  getBalance,
  getAccountLinkUrl,
  setApiKeyTool,
];

/**
 * Register all ClawCall tools with the MCP server.
 *
 * `inputSchema` is passed as the RAW zod shape — `registerTool` (NOT the legacy
 * `server.tool()`, NOT the v2 alpha surface) wraps it internally. ClawCall API
 * errors are normalized into MCP error results so the agent can read the
 * personalized action URLs; anything else propagates as a real failure.
 */
export function registerAllTools(server: McpServer): void {
  for (const t of ALL_TOOLS) {
    server.registerTool(
      t.name,
      {
        description: t.description,
        inputSchema: t.inputSchema,
        annotations: t.annotations,
      },
      async (args: any) => {
        try {
          return toMcpResult(await t.execute(args));
        } catch (e) {
          if (e instanceof ClawCallError) return toMcpError(e);
          throw e;
        }
      },
    );
  }
}
