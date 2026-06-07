/**
 * Hand-copied TypeScript mirrors of the ClawCall REST contract.
 *
 * These are intentionally NOT imported from `server/src` — this package is a
 * standalone client over the public REST surface. Field names and shapes
 * mirror the contract documented in skill/SKILL.md and the server code.
 */

/** Persisted credential file: ~/.config/clawcall/key.json */
export interface KeyFile {
  api_key?: string;
  user_phone_number?: string;
}

/** Public call lifecycle projection. Only `finalized` is terminal. */
export type Lifecycle = 'queued' | 'dialing' | 'answered' | 'finalized';

/** One turn in the call transcript. `user` = callee, `assistant` = voice agent. */
export interface TranscriptEntry {
  role: string;
  text: string;
  timestamp?: string;
  tool?: string;
  toolArgs?: unknown;
}

/** Phone-network hangup detail, present only on terminal calls. */
export interface OutcomeDetail {
  hangup_cause: string | null;
  sip_hangup_cause: string | null;
  hangup_source: string | null;
}

/**
 * Response shape for GET /call/:id.
 *
 * `transcript` is present both in-flight (accumulating live, null until the
 * agent's first turn) and terminal. The `outcome*` / `talk_seconds` /
 * `recording_url` fields are ABSENT while in-flight and added on finalize.
 */
export interface CallResponse {
  id: string;
  direction: 'outbound' | 'inbound';
  lifecycle: Lifecycle;
  numbers?: unknown;
  timestamps?: {
    queued_at?: string | null;
    dialing_at?: string | null;
    answered_at?: string | null;
    finalized_at?: string | null;
  };
  transcript: TranscriptEntry[] | null;
  // terminal-only (absent while in-flight):
  outcome?: string;
  outcome_detail?: OutcomeDetail;
  talk_seconds?: number | null;
  recording_url?: string | null;
}

/**
 * The `action` block from an error envelope. URLs are personalized
 * (proto-key embedded) and MUST be forwarded byte-for-byte.
 */
export interface ErrorAction {
  url?: string;
  label?: string;
  sign_in_url?: string;
  [k: string]: unknown;
}

/**
 * The `quota` block from a trial_exhausted (or legacy quota_exceeded) error.
 * Trial limits are read from here — NEVER hardcoded in tool prose.
 */
export interface ErrorQuota {
  used_seconds?: number;
  remaining_seconds?: number;
  limit_seconds?: number;
  tier?: string;
  [k: string]: unknown;
}

/** Standard server error envelope: {error:{code, message, action?, quota?}}. */
export interface ErrorEnvelope {
  error: {
    code: string;
    message: string;
    action?: ErrorAction;
    quota?: ErrorQuota;
  };
}

/** Account/balance status. Balance is surfaced via headers, never the body. */
export interface Balance {
  balance_seconds?: number;
  tier?: string;
}
