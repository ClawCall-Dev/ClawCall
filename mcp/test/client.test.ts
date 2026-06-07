import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, readFileSync, existsSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';

import { clawcallFetch, placeCall } from '../dist/clawcall/client.js';
import { ClawCallError } from '../dist/clawcall/errors.js';

let configHome: string;
const realFetch = globalThis.fetch;

function keyPath(): string {
  return join(configHome, 'clawcall', 'key.json');
}

function readKey(): Record<string, unknown> {
  if (!existsSync(keyPath())) return {};
  return JSON.parse(readFileSync(keyPath(), 'utf8'));
}

function jsonResponse(
  status: number,
  body: unknown,
  headers: Record<string, string> = {},
): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json', ...headers },
  });
}

beforeEach(() => {
  configHome = join(tmpdir(), `clawcall-mcp-client-${randomUUID()}`);
  mkdirSync(configHome, { recursive: true });
  process.env.XDG_CONFIG_HOME = configHome;
  process.env.CLAWCALL_BASE_URL = 'https://api.clawcall.dev';
  delete process.env.CLAWCALL_API_KEY;
});

afterEach(() => {
  globalThis.fetch = realFetch;
  try {
    rmSync(configHome, { recursive: true, force: true });
  } catch {
    /* best effort */
  }
});

test('capture-on-receipt: persists proto-key from the JSON api_key field before returning', async () => {
  globalThis.fetch = async () =>
    jsonResponse(
      201,
      { call_id: 'call_1', status: 'queued', message: 'queued', api_key: 'clawcall_sk_x' },
      { 'X-ClawCall-Api-Key': 'clawcall_sk_x' },
    );

  const result = await placeCall({ to: '+14155550123', task: 'do a thing' });

  assert.equal(result.call_id, 'call_1');
  // Key must be persisted via key-store BEFORE the call returns.
  assert.equal(readKey().api_key, 'clawcall_sk_x');
});

test('capture-on-receipt: captures the key when it is ONLY in the response header', async () => {
  globalThis.fetch = async () =>
    jsonResponse(
      201,
      { call_id: 'call_2', status: 'queued', message: 'queued' }, // no api_key in body
      { 'X-ClawCall-Api-Key': 'clawcall_sk_header_only' },
    );

  await placeCall({ to: '+14155550123', task: 'header-only key' });

  assert.equal(readKey().api_key, 'clawcall_sk_header_only');
});

test('capture-on-receipt: merge-preserves user_phone_number on the saved file', async () => {
  mkdirSync(join(configHome, 'clawcall'), { recursive: true });
  writeFileSync(keyPath(), JSON.stringify({ user_phone_number: '+14155559999' }), 'utf8');

  globalThis.fetch = async () =>
    jsonResponse(
      201,
      { call_id: 'call_3', status: 'queued', message: 'queued', api_key: 'clawcall_sk_y' },
      {},
    );

  await placeCall({ to: '+14155550123', task: 'merge' });

  const saved = readKey();
  assert.equal(saved.api_key, 'clawcall_sk_y');
  assert.equal(saved.user_phone_number, '+14155559999');
});

test('self-heal: a 401 invalid_api_key envelope clears the saved key', async () => {
  mkdirSync(join(configHome, 'clawcall'), { recursive: true });
  writeFileSync(
    keyPath(),
    JSON.stringify({ api_key: 'clawcall_sk_bad', user_phone_number: '+14155551111' }),
    'utf8',
  );

  globalThis.fetch = async () =>
    jsonResponse(401, { error: { code: 'invalid_api_key', message: 'bad key' } });

  await assert.rejects(
    () => clawcallFetch('/call', { method: 'POST', body: { to: '+14155550123', task: 't' } }),
    (err: unknown) => err instanceof ClawCallError && err.code === 'invalid_api_key',
  );

  const saved = readKey();
  assert.ok(!('api_key' in saved) || saved.api_key == null, 'api_key should be cleared');
  // user_phone_number must survive the self-heal.
  assert.equal(saved.user_phone_number, '+14155551111');
});

test('self-heal: a 500 does NOT clear the key and throws a retryable ClawCallError', async () => {
  mkdirSync(join(configHome, 'clawcall'), { recursive: true });
  writeFileSync(keyPath(), JSON.stringify({ api_key: 'clawcall_sk_keep' }), 'utf8');

  globalThis.fetch = async () =>
    jsonResponse(500, { error: { code: 'internal_error', message: 'boom' } });

  await assert.rejects(
    () => clawcallFetch('/call', { method: 'POST', body: { to: '+14155550123', task: 't' } }),
    (err: unknown) => err instanceof ClawCallError && err.retryable === true,
  );

  // Key must be untouched on a server error.
  assert.equal(readKey().api_key, 'clawcall_sk_keep');
});

test('redirect:manual path returns a FetchResult without throwing on a 302', async () => {
  let capturedRedirect: RequestRedirect | undefined;
  globalThis.fetch = async (_input: RequestInfo | URL, init?: RequestInit) => {
    capturedRedirect = init?.redirect;
    return new Response(null, {
      status: 302,
      headers: { Location: 'https://signed.example/recording.mp3' },
    });
  };

  const res = await clawcallFetch('/call/call_1/recording', {
    method: 'GET',
    redirect: 'manual',
  });

  assert.equal(capturedRedirect, 'manual');
  assert.equal(res.status, 302);
  assert.equal(res.headers.get('location'), 'https://signed.example/recording.mp3');
});

test('redirect:manual path surfaces a 404 recording_not_available envelope instead of dropping it', async () => {
  globalThis.fetch = async () =>
    jsonResponse(404, {
      error: { code: 'recording_not_available', message: 'no recording for this call' },
    });

  await assert.rejects(
    () =>
      clawcallFetch('/call/call_1/recording', {
        method: 'GET',
        redirect: 'manual',
      }),
    (err: unknown) =>
      err instanceof ClawCallError &&
      err.code === 'recording_not_available' &&
      err.message === 'no recording for this call' &&
      err.status === 404,
  );
});

test('clawcallFetch injects the X-Api-Key header from the resolved key', async () => {
  mkdirSync(join(configHome, 'clawcall'), { recursive: true });
  writeFileSync(keyPath(), JSON.stringify({ api_key: 'clawcall_sk_auth' }), 'utf8');

  let sentKey: string | null = null;
  globalThis.fetch = async (_input: RequestInfo | URL, init?: RequestInit) => {
    const headers = new Headers(init?.headers);
    sentKey = headers.get('X-Api-Key');
    return jsonResponse(200, { ok: true });
  };

  await clawcallFetch('/balance', { method: 'GET' });
  assert.equal(sentKey, 'clawcall_sk_auth');
});
