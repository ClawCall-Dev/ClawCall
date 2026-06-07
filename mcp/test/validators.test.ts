import { test } from 'node:test';
import assert from 'node:assert/strict';

import { usPhone, voiceEnum, listCallsSince } from '../dist/tools/shared.js';

function ok(schema: { safeParse: (v: unknown) => { success: boolean } }, value: unknown): boolean {
  return schema.safeParse(value).success;
}

test('usPhone accepts a valid US E.164 number', () => {
  assert.equal(ok(usPhone, '+14155550123'), true);
});

test('usPhone rejects a number that is too short', () => {
  assert.equal(ok(usPhone, '+1415555012'), false);
});

test('usPhone rejects a non-US (+44) number', () => {
  assert.equal(ok(usPhone, '+442071838750'), false);
});

test('usPhone rejects a number with no +1 prefix', () => {
  assert.equal(ok(usPhone, '4155550123'), false);
});

test('usPhone rejects an area code whose first digit is 1', () => {
  // +1 1155550123 -> area code "115" starts with 1, invalid per NANP.
  assert.equal(ok(usPhone, '+11155550123'), false);
});

test('usPhone rejects an area code whose first digit is 0', () => {
  assert.equal(ok(usPhone, '+10155550123'), false);
});

test('voiceEnum accepts the four canonical voices', () => {
  for (const v of ['jessica', 'sarah', 'chris', 'eric']) {
    assert.equal(ok(voiceEnum, v), true, `${v} should be accepted`);
  }
});

test('voiceEnum rejects unknown voices', () => {
  for (const v of ['rachel', 'bella', 'adam', 'josh', 'JESSICA', '', 'bob']) {
    assert.equal(ok(voiceEnum, v), false, `${v} should be rejected`);
  }
});

test('list_calls since accepts an ISO-8601 timestamp with offset', () => {
  assert.equal(ok(listCallsSince, '2026-06-06T12:00:00Z'), true);
  assert.equal(ok(listCallsSince, '2026-06-06T12:00:00+00:00'), true);
  assert.equal(ok(listCallsSince, '2026-06-06T12:00:00.500-07:00'), true);
});

test('list_calls since rejects a bare calendar date', () => {
  assert.equal(ok(listCallsSince, '2026-06-06'), false);
});
