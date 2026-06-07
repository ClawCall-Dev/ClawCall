/**
 * stderr-ONLY logger with secret redaction.
 *
 * stdout is the JSON-RPC channel for the MCP stdio transport — a stray
 * console.log corrupts the protocol stream AND can leak the API key.
 * Every diagnostic goes to stderr, and any `clawcall_sk_...` token is
 * redacted before it is written.
 */

const REDACT = /clawcall_sk_[A-Za-z0-9_-]+/g;

const redact = (s: unknown): string =>
  String(typeof s === 'string' ? s : JSON.stringify(s)).replace(
    REDACT,
    'clawcall_sk_***',
  );

export const log = {
  info: (...a: unknown[]) =>
    process.stderr.write('[clawcall] ' + a.map(redact).join(' ') + '\n'),
  error: (...a: unknown[]) =>
    process.stderr.write('[clawcall][err] ' + a.map(redact).join(' ') + '\n'),
};
