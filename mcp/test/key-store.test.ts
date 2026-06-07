import { test, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, statSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomUUID } from 'node:crypto';

// Module under test is imported lazily AFTER XDG_CONFIG_HOME is set, so the
// key-store resolves the temp config root and the real user config is never
// touched. Each test gets a fresh temp dir.
import {
  captureProtoKey,
  clearApiKey,
  setApiKey,
  resolveApiKey,
  keyFilePath,
  readKeyFile,
} from '../dist/clawcall/key-store.js';

let configHome: string;

function keyPath(): string {
  return join(configHome, 'clawcall', 'key.json');
}

beforeEach(() => {
  configHome = join(tmpdir(), `clawcall-mcp-test-${randomUUID()}`);
  mkdirSync(configHome, { recursive: true });
  process.env.XDG_CONFIG_HOME = configHome;
  // Ensure no operator override leaks in from CI.
  delete process.env.CLAWCALL_API_KEY;
});

afterEach(() => {
  try {
    rmSync(configHome, { recursive: true, force: true });
  } catch {
    /* best effort */
  }
});

test('keyFilePath resolves under XDG_CONFIG_HOME/clawcall/key.json', () => {
  assert.equal(keyFilePath(), keyPath());
});

test('captureProtoKey writes key.json with file mode 0o600 and dir 0o700', async () => {
  await captureProtoKey('clawcall_sk_abc123');

  const p = keyPath();
  assert.ok(existsSync(p), 'key.json should exist');

  const raw = readFileSync(p, 'utf8');
  const parsed = JSON.parse(raw);
  assert.equal(parsed.api_key, 'clawcall_sk_abc123');

  const fileMode = statSync(p).mode & 0o777;
  assert.equal(fileMode, 0o600, `file mode should be 0o600, got ${fileMode.toString(8)}`);

  const dirMode = statSync(join(configHome, 'clawcall')).mode & 0o777;
  assert.equal(dirMode, 0o700, `dir mode should be 0o700, got ${dirMode.toString(8)}`);
});

test('captureProtoKey merge-preserves an existing user_phone_number', async () => {
  const dir = join(configHome, 'clawcall');
  mkdirSync(dir, { recursive: true });
  writeFileSync(keyPath(), JSON.stringify({ user_phone_number: '+14155550123' }), 'utf8');

  await captureProtoKey('clawcall_sk_fresh');

  const parsed = JSON.parse(readFileSync(keyPath(), 'utf8'));
  assert.equal(parsed.api_key, 'clawcall_sk_fresh');
  assert.equal(parsed.user_phone_number, '+14155550123');
});

test('clearApiKey deletes ONLY api_key, preserves user_phone_number', async () => {
  const dir = join(configHome, 'clawcall');
  mkdirSync(dir, { recursive: true });
  writeFileSync(
    keyPath(),
    JSON.stringify({ api_key: 'clawcall_sk_old', user_phone_number: '+14155550123' }),
    'utf8',
  );

  await clearApiKey();

  const parsed = JSON.parse(readFileSync(keyPath(), 'utf8'));
  assert.equal(parsed.user_phone_number, '+14155550123');
  assert.ok(!('api_key' in parsed) || parsed.api_key == null, 'api_key should be removed');
});

test('clearApiKey is a no-op when no file exists', async () => {
  await assert.doesNotReject(() => clearApiKey());
});

test('setApiKey overrides an existing api_key', async () => {
  await captureProtoKey('clawcall_sk_first');
  await setApiKey('clawcall_sk_second');

  const parsed = JSON.parse(readFileSync(keyPath(), 'utf8'));
  assert.equal(parsed.api_key, 'clawcall_sk_second');
});

test('setApiKey preserves user_phone_number', async () => {
  const dir = join(configHome, 'clawcall');
  mkdirSync(dir, { recursive: true });
  writeFileSync(keyPath(), JSON.stringify({ user_phone_number: '+14155550123' }), 'utf8');

  await setApiKey('clawcall_sk_supplied');

  const parsed = JSON.parse(readFileSync(keyPath(), 'utf8'));
  assert.equal(parsed.api_key, 'clawcall_sk_supplied');
  assert.equal(parsed.user_phone_number, '+14155550123');
});

test('resolveApiKey prefers CLAWCALL_API_KEY env override over the saved file', async () => {
  await captureProtoKey('clawcall_sk_saved');
  process.env.CLAWCALL_API_KEY = 'clawcall_sk_env_override';
  try {
    const resolved = await resolveApiKey();
    assert.equal(resolved, 'clawcall_sk_env_override');
  } finally {
    delete process.env.CLAWCALL_API_KEY;
  }
});

test('resolveApiKey falls back to the saved file when no env override', async () => {
  await captureProtoKey('clawcall_sk_saved');
  const resolved = await resolveApiKey();
  assert.equal(resolved, 'clawcall_sk_saved');
});

test('resolveApiKey returns undefined when no key is available', async () => {
  const resolved = await resolveApiKey();
  assert.ok(resolved === undefined || resolved === null);
});

test('readKeyFile returns an empty object when the file is absent', async () => {
  const data = await readKeyFile();
  assert.deepEqual(data, {});
});

test('concurrent captureProtoKey writes do not corrupt the file (mutex + atomic rename)', async () => {
  await Promise.all([
    captureProtoKey('clawcall_sk_1'),
    captureProtoKey('clawcall_sk_2'),
    captureProtoKey('clawcall_sk_3'),
    captureProtoKey('clawcall_sk_4'),
    captureProtoKey('clawcall_sk_5'),
  ]);

  const raw = readFileSync(keyPath(), 'utf8');
  // Must be valid JSON — interleaved writes must never half-write.
  const parsed = JSON.parse(raw);
  assert.equal(typeof parsed.api_key, 'string');
  // Exactly one api_key field survives (the object has a single winner).
  const matches = raw.match(/"api_key"/g) ?? [];
  assert.equal(matches.length, 1, 'file must contain exactly one api_key entry');
  assert.ok(/^clawcall_sk_[1-5]$/.test(parsed.api_key), `unexpected winner ${parsed.api_key}`);
});
