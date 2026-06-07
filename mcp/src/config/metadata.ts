/**
 * Single source of all tool prose and shared workflow / caveat constants.
 *
 * Drift-control: every piece of workflow knowledge, every caveat, and every
 * per-field input description for the ClawCall MCP tools lives HERE and nowhere
 * else, so it is reviewed in one place and cannot diverge per-tool.
 *
 * NO LOGIC in this file — only exported strings/objects.
 * NO TRIAL NUMBERS anywhere in this file — trial limits are read at runtime
 * from the live `quota` object in the error envelope, never hardcoded.
 */

/**
 * The load-bearing workflow. Embedded in the write + poll tool descriptions so
 * the agent always learns the fire-and-poll contract and the outcome-vs-task
 * distinction at tool-selection time.
 */
export const WORKFLOW =
  "After placing a call, poll get_call every 3s until lifecycle === 'finalized'. The outcome field is the PHONE-NETWORK result (answered/no_answer/busy/…), NOT task success — read the transcript (get_call_transcript) and judge it against the task yourself. A call that reached voicemail still finalizes as answered or no_answer — detect it from the transcript, not the outcome.";

/**
 * `greeting` is outbound-opener context only. The agent's actual first spoken
 * line is hardcoded server-side to a recording disclosure and ignores this
 * field — do NOT promise an agent that greeting sets the opening line.
 */
export const GREETING_CAVEAT =
  "Optional outbound opener context. Does NOT set the agent's first spoken line — the opener is hardcoded server-side to a recording disclosure.";

/**
 * 402 gating is permanent. Surface the personalized action URLs verbatim and do
 * not retry. Trial limits are never assumed — they come from the live quota
 * object in the error envelope.
 */
export const GATE_CAVEAT =
  "402 errors (trial_exhausted / plan_required / reserved_number_required) are PERMANENT gating, not retryable. Surface action.url and action.sign_in_url to the user verbatim. Do not retry. Trial limits come from the live quota object in the error envelope — never assume a fixed number.";

/**
 * Campaigns (3-4 parallel interchangeable info-gathering calls) use the
 * non-blocking primitive directly with a get_call fan-out, never the awaited
 * convenience tool.
 */
export const CAMPAIGN_NOTE =
  "For 3-4 parallel interchangeable info-gathering calls, call place_call directly per number and fan-out get_call. Do NOT use place_call_and_wait for campaigns.";

/** Shape of a single tool's centralized prose. */
export interface ToolMetadata {
  /** Top-level tool description shown to the model at selection time. */
  description: string;
  /** Per-field input descriptions, keyed by the tool's schema field names. */
  params: Record<string, string>;
}

/**
 * All 10 tools' prose. Field descriptions match the schemas the tools bundle
 * declares (US E.164 +1, the four canonical voices, ISO 8601 timestamps, etc.).
 */
export const TOOLS: Record<string, ToolMetadata> = {
  place_call: {
    description:
      `Place an outbound US phone call. THE canonical write; non-blocking, returns immediately. ${WORKFLOW} ${CAMPAIGN_NOTE}`,
    params: {
      to: "US phone number in E.164, +1XXXXXXXXXX",
      task: "Full briefing memo — the agent's ONLY knowledge of the call's purpose and context",
      voice: "Optional voice: jessica (default), sarah, chris, or eric",
      personality: "Optional reusable style/tone. Do NOT put one-call facts here",
      greeting: GREETING_CAVEAT,
      bridge_number:
        "Optional US E.164; enables mid-call loop_in_user handoff to this number",
    },
  },

  place_call_and_wait: {
    description:
      `OPTIONAL convenience for a SINGLE foreground call. Internally polls until finalized or a ~180s hard cap, then degrades to the non-blocking contract (returns call_id to keep polling). NOT for campaigns. ${GATE_CAVEAT}`,
    params: {
      to: "US phone number in E.164, +1XXXXXXXXXX",
      task: "Full briefing memo — the agent's ONLY knowledge of the call's purpose and context",
      voice: "Optional voice: jessica (default), sarah, chris, or eric",
      personality: "Optional reusable style/tone. Do NOT put one-call facts here",
      greeting: GREETING_CAVEAT,
      bridge_number:
        "Optional US E.164; enables mid-call loop_in_user handoff to this number",
      max_wait_seconds:
        "Seconds to wait before degrading to poll. Default 180, ceiling 240.",
    },
  },

  get_call: {
    description:
      `Poll primitive; context-cheap. Returns lifecycle + a short transcript_tail, NOT the full transcript (use get_call_transcript for that). ${WORKFLOW}`,
    params: {
      call_id: "The call_id returned by place_call",
    },
  },

  get_call_transcript: {
    description:
      "Full turn-by-turn transcript array. Split out so get_call stays cheap for frequent polling.",
    params: {
      call_id: "The call_id returned by place_call",
    },
  },

  hangup_call: {
    description:
      "Cancel or hang up a call you initiated. Idempotent — already-finalized is a no-op success. Use for mid-call control during your own poll loop.",
    params: {
      call_id: "The call_id returned by place_call",
    },
  },

  list_calls: {
    description:
      "List call history. Requires account linking (a proto-key with no linked user returns 401 — call get_account_link_url). Inbound history requires a reserved-number plan.",
    params: {
      limit: "Max results, default 25, 1-200",
      direction: "Optional: inbound or outbound",
      since: "Optional ISO 8601 timestamp lower bound",
    },
  },

  get_recording: {
    description:
      "Durable recording access (no 10-minute window). Returns a URL, never inline audio. A 404 may be a permission denial, not absence.",
    params: {
      call_id: "The call_id returned by place_call",
    },
  },

  get_balance: {
    description:
      "Cheap balance/tier status. Do NOT pre-check before every call — just place the call and handle errors.",
    params: {},
  },

  get_account_link_url: {
    description:
      "Build the browser sign-in link to attach this agent's key, calls, balance, and history to a ClawCall account. Reads the saved key; mints nothing. If no key is saved, place a call first.",
    params: {},
  },

  set_api_key: {
    description:
      "Save a user-supplied ClawCall API key (clawcall_sk_...) to the shared config file. Overrides any saved key. Never echoes the key back.",
    params: {
      api_key: "A ClawCall API key starting with clawcall_sk_",
    },
  },
};
