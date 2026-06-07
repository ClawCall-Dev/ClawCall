#!/usr/bin/env node
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createServer } from './server.js';
import { log } from './logger.js';

async function main(): Promise<void> {
  const server = createServer();
  await server.connect(new StdioServerTransport());
  log.info('clawcall-mcp ready');
}

main().catch((e) => {
  log.error('fatal', e);
  process.exit(1);
});
