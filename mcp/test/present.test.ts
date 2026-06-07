import { test } from 'node:test';
import assert from 'node:assert/strict';

import { presentGetCall, balanceFromHeaders } from '../dist/clawcall/present.js';

function makeTranscript(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    role: i % 2 === 0 ? 'assistant' : 'user',
    text: `turn ${i} ` + 'x'.repeat(300),
    timestamp: `2026-06-06T00:00:${String(i).padStart(2, '0')}.000Z`,
  }));
}

test('presentGetCall strips the full transcript and emits a bounded transcript_tail', () => {
  const raw = {
    id: 'call_1',
    direction: 'outbound',
    lifecycle: 'finalized',
    numbers: { to: '+14155550123', from: '+14155550000', bridge_from: null },
    timestamps: {
      queued_at: '2026-06-06T00:00:00.000Z',
      dialing_at: '2026-06-06T00:00:01.000Z',
      answered_at: '2026-06-06T00:00:02.000Z',
      finalized_at: '2026-06-06T00:01:00.000Z',
    },
    outcome: 'answered',
    outcome_detail: { hangup_cause: 'normal_clearing', sip_hangup_cause: null, hangup_source: 'caller' },
    talk_seconds: 58,
    recording_url: 'https://rec.example/x',
    transcript: makeTranscript(12),
  };

  const view = presentGetCall(raw) as Record<string, any>;

  // The unbounded full array must NOT be inlined.
  assert.ok(!('transcript' in view), 'transcript array must be stripped');
  assert.ok(!('transcript_summary' in view), 'no transcript_summary key (it is fiction server-side)');

  assert.equal(view.transcript_available, true);
  assert.ok(Array.isArray(view.transcript_tail));
  assert.ok(view.transcript_tail.length <= 6, 'tail must be <= 6 entries');
  // Tail is the LAST turns.
  assert.equal(view.transcript_tail.length, 6);
  for (const turn of view.transcript_tail) {
    assert.ok(turn.text.length <= 200, `tail text truncated to <=200, got ${turn.text.length}`);
  }
});

test('presentGetCall reports transcript_available:false and an empty tail when transcript is null', () => {
  const raw = {
    id: 'call_2',
    direction: 'outbound',
    lifecycle: 'dialing',
    numbers: { to: '+14155550123', from: '+14155550000', bridge_from: null },
    timestamps: { queued_at: '2026-06-06T00:00:00.000Z', finalized_at: null },
    transcript: null,
  };

  const view = presentGetCall(raw) as Record<string, any>;
  assert.equal(view.transcript_available, false);
  assert.deepEqual(view.transcript_tail, []);
  assert.ok(!('transcript' in view));
});

test('in-flight view OMITS terminal-only fields', () => {
  const raw = {
    id: 'call_3',
    direction: 'outbound',
    lifecycle: 'dialing',
    numbers: { to: '+14155550123', from: '+14155550000', bridge_from: null },
    timestamps: { queued_at: '2026-06-06T00:00:00.000Z', finalized_at: null },
    transcript: null,
  };

  const view = presentGetCall(raw) as Record<string, any>;
  assert.equal(view.lifecycle, 'dialing');
  assert.ok(!('outcome' in view), 'outcome omitted in-flight');
  assert.ok(!('outcome_detail' in view), 'outcome_detail omitted in-flight');
  assert.ok(!('talk_seconds' in view), 'talk_seconds omitted in-flight');
  assert.ok(!('recording_url' in view), 'recording_url omitted in-flight');
});

test('terminal view INCLUDES outcome, outcome_detail, talk_seconds, recording_url', () => {
  const raw = {
    id: 'call_4',
    direction: 'outbound',
    lifecycle: 'finalized',
    numbers: { to: '+14155550123', from: '+14155550000', bridge_from: null },
    timestamps: {
      queued_at: '2026-06-06T00:00:00.000Z',
      finalized_at: '2026-06-06T00:01:00.000Z',
    },
    outcome: 'no_answer',
    outcome_detail: { hangup_cause: 'no_answer', sip_hangup_cause: null, hangup_source: null },
    talk_seconds: null,
    recording_url: null,
    transcript: makeTranscript(2),
  };

  const view = presentGetCall(raw) as Record<string, any>;
  assert.equal(view.lifecycle, 'finalized');
  assert.equal(view.outcome, 'no_answer');
  assert.deepEqual(view.outcome_detail, {
    hangup_cause: 'no_answer',
    sip_hangup_cause: null,
    hangup_source: null,
  });
  assert.ok('talk_seconds' in view);
  assert.ok('recording_url' in view);
});

test('balanceFromHeaders folds X-ClawCall-Balance-Seconds and tier', () => {
  const headers = new Headers({
    'X-ClawCall-Balance-Seconds': '742',
    'X-ClawCall-Tier': 'paid',
  });
  const folded = balanceFromHeaders(headers);
  assert.equal(folded.balance_seconds, 742);
  assert.equal(folded.tier, 'paid');
});

test('balanceFromHeaders omits absent fields', () => {
  const headers = new Headers({ 'X-ClawCall-Balance-Seconds': '100' });
  const folded = balanceFromHeaders(headers);
  assert.equal(folded.balance_seconds, 100);
  assert.ok(!('tier' in folded), 'tier omitted when header absent');
});

test('balanceFromHeaders returns an empty object when no balance headers are present', () => {
  const folded = balanceFromHeaders(new Headers());
  assert.ok(!('balance_seconds' in folded));
  assert.ok(!('tier' in folded));
});
