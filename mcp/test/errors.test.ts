import { test } from 'node:test';
import assert from 'node:assert/strict';

import { normalizeError, ClawCallError } from '../dist/clawcall/errors.js';

test('normalizeError preserves action.url and action.sign_in_url byte-for-byte', () => {
  const url = 'https://clawcall.dev/sign-up?token=clawcall_sk_AbC123-_';
  const signInUrl = 'https://clawcall.dev/sign-in?token=clawcall_sk_AbC123-_';
  const envelope = {
    error: {
      code: 'trial_exhausted',
      message: 'Trial used up.',
      action: { type: 'sign_up', url, sign_in_url: signInUrl, description: 'Sign up' },
      quota: { used_seconds: 600, remaining_seconds: 0, limit_seconds: 600, tier: 'free' },
    },
  };

  const err = normalizeError(402, envelope);
  assert.ok(err instanceof ClawCallError);
  assert.equal(err.action?.url, url);
  assert.equal(err.action?.sign_in_url, signInUrl);
});

test('normalizeError keeps the quota object untouched (deep equal)', () => {
  const quota = { used_seconds: 600, remaining_seconds: 0, limit_seconds: 600, tier: 'free' };
  const envelope = {
    error: { code: 'trial_exhausted', message: 'used', action: { url: 'x' }, quota },
  };

  const err = normalizeError(402, envelope);
  assert.deepEqual(err.quota, quota);
});

test('402 codes are not retryable (permanent gating)', () => {
  for (const code of ['trial_exhausted', 'plan_required', 'reserved_number_required']) {
    const err = normalizeError(402, { error: { code, message: 'gated' } });
    assert.equal(err.code, code);
    assert.equal(err.retryable, false, `${code} must be non-retryable`);
  }
});

test('429 is retryable', () => {
  const err = normalizeError(429, { error: { code: 'balance_depleted', message: 'no balance' } });
  assert.equal(err.retryable, true);
});

test('5xx codes are retryable', () => {
  for (const status of [500, 502, 503]) {
    const err = normalizeError(status, {
      error: { code: 'dial_failed', message: 'transient' },
    });
    assert.equal(err.retryable, true, `${status} must be retryable`);
  }
});

test('a missing envelope on 500 synthesizes a retryable error', () => {
  const err = normalizeError(500, undefined);
  assert.ok(err instanceof ClawCallError);
  assert.equal(err.retryable, true);
  assert.equal(err.status, 500);
  assert.equal(typeof err.code, 'string');
});

test('a missing envelope on a 4xx synthesizes a non-retryable error', () => {
  const err = normalizeError(400, undefined);
  assert.equal(err.retryable, false);
  assert.equal(err.status, 400);
});

test('401 invalid_api_key is surfaced with its code (drives self-heal)', () => {
  const err = normalizeError(401, {
    error: { code: 'invalid_api_key', message: 'bad key' },
  });
  assert.equal(err.code, 'invalid_api_key');
  assert.equal(err.status, 401);
});

test('ClawCallError carries status, code, message, action, quota, retryable', () => {
  const err = new ClawCallError({
    status: 402,
    code: 'plan_required',
    message: 'need a plan',
    retryable: false,
    action: { url: 'https://clawcall.dev/dashboard/purchase' },
  });
  assert.equal(err.status, 402);
  assert.equal(err.code, 'plan_required');
  assert.equal(err.message, 'need a plan');
  assert.equal(err.retryable, false);
  assert.equal(err.action?.url, 'https://clawcall.dev/dashboard/purchase');
  assert.ok(err instanceof Error);
});
