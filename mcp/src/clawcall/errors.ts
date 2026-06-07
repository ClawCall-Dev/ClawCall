/**
 * Error normalization. Maps an HTTP status + parsed body into a typed
 * ClawCallError, preserving the server's machine-readable code, personalized
 * action URLs, and quota object byte-for-byte.
 */

import type { ErrorAction, ErrorEnvelope, ErrorQuota } from './types.js';

export class ClawCallError extends Error {
  status: number;
  code: string;
  action?: ErrorAction;
  quota?: ErrorQuota;
  retryable: boolean;

  constructor(d: {
    status: number;
    code: string;
    message: string;
    action?: ErrorAction;
    quota?: ErrorQuota;
    retryable: boolean;
  }) {
    super(d.message);
    this.name = 'ClawCallError';
    this.status = d.status;
    this.code = d.code;
    this.action = d.action;
    this.quota = d.quota;
    this.retryable = d.retryable;
  }
}

/**
 * 4xx codes that are PERMANENT (not retryable). 402 gating
 * (trial_exhausted / plan_required / reserved_number_required) is permanent;
 * the agent must surface action.url verbatim, never retry.
 */
const NON_RETRYABLE_CODES = new Set<string>([
  'invalid_api_key',
  'auth_required',
  'trial_exhausted',
  'plan_required',
  'reserved_number_required',
  'inbound_plan_required',
  'not_found',
  'recording_not_available',
  'missing_fields',
  'invalid_phone',
  'invalid_query',
  'invalid_preferences',
  'invalid_profile',
  'invalid_handoff_number',
  'invalid_token',
  'account_link_required',
  'forbidden',
  'conflict',
  'minute_packs_discontinued',
]);

function isErrorEnvelope(body: unknown): body is ErrorEnvelope {
  return (
    typeof body === 'object' &&
    body !== null &&
    'error' in body &&
    typeof (body as { error: unknown }).error === 'object' &&
    (body as { error: unknown }).error !== null &&
    typeof (body as ErrorEnvelope).error.code === 'string'
  );
}

/**
 * If `body` is a `{error:{code,message,action?,quota?}}` envelope, copy
 * `action` (incl. url, sign_in_url) and `quota` byte-for-byte — never
 * reconstruct URLs, never read/interpret/hardcode trial numbers.
 *
 * Retryability:
 *  - false for known 4xx permanent codes (auth, gating, validation, conflict).
 *  - true for 429 and any 5xx.
 *  - true for missing/unparseable envelopes on 5xx.
 *
 * If no `{error}` envelope is present, synthesize a code of `http_<status>`.
 */
export function normalizeError(httpStatus: number, body: unknown): ClawCallError {
  if (isErrorEnvelope(body)) {
    const { code, message, action, quota } = body.error;
    let retryable: boolean;
    if (httpStatus === 429 || httpStatus >= 500) {
      retryable = true;
    } else if (NON_RETRYABLE_CODES.has(code)) {
      retryable = false;
    } else {
      // Unknown 4xx code: default to non-retryable (client-side fault).
      retryable = httpStatus >= 500;
    }
    return new ClawCallError({
      status: httpStatus,
      code,
      message,
      action,
      quota,
      retryable,
    });
  }

  // No envelope: synthesize from the raw status.
  const rawMessage =
    typeof body === 'string' && body.trim().length > 0
      ? body
      : 'request failed';
  return new ClawCallError({
    status: httpStatus,
    code: 'http_' + httpStatus,
    message: rawMessage,
    retryable: httpStatus >= 500,
  });
}
