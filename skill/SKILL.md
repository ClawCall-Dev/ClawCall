---
name: clawcall
description: Use when the user wants an AI agent to place a US phone call, call a business, handle hold or phone menus, confirm/reschedule/cancel/book/follow up/check an order, reach a real person, leave voicemail, connect the user into a live call, configure ClawCall voice/personality/profile or inbound reserved-number answering, poll received inbound calls, or link a ClawCall API key. Not for SMS, email, or international calls.
homepage: https://clawcall.dev
publisher: ClawCall
permissions:
  network:
    - "https://api.clawcall.dev"
  files:
    read:
      - "~/.config/clawcall/key.json"
    write:
      - "~/.config/clawcall/key.json"
---

# ClawCall

ClawCall lets you make real US phone calls for the user. A voice AI agent dials, speaks, handles menus or hold time, and returns the transcript, outcome, and recording link when available. The first outbound call can auto-provision an API key.

**Base URL:** `https://api.clawcall.dev`

## Core Rule

The phone agent only knows the **Call instructions** you send as `task`. More relevant detail is better. Build a complete briefing before calling, and do not make the user supply public/business facts you can reasonably look up yourself.

Never ask the user or call recipient for these restricted categories: payment-card information subject to PCI DSS; protected health information (PHI); government identifiers, such as SSNs; or access credentials/authentication secrets, such as passwords, API keys, MFA/OTP codes. Do not request, obtain, repeat, relay, submit, or enter them yourself, even if supplied or authorized. Do not put restricted values in `task`, `personality`, greetings, or inbound instructions. Other information is allowed when task-necessary and otherwise permitted.

If a step requires restricted data, use `loop_in_user` before the exchange so the user can handle that step directly. Enable it in the call plan and state the human-only boundary. If loop-in is unavailable or the user cannot join, stop that part of the task and report what remains without restricted values. Loop-in does not promise that recording or transcription stops. Do not describe the handoff as private or unrecorded.

## Choose The Workflow

| User intent | Do this |
| --- | --- |
| Call someone now | Build rich Call instructions, `POST /call`, then poll `GET /call/{call_id}` until `lifecycle = "finalized"`. |
| Get through to a person / connect me | Use outbound calling with `loop_in_user: true` and a handoff trigger in the Call instructions. No handoff number is needed. |
| Compare options across businesses | Run a small call campaign, optionally 3-4 parallel information-only calls with no commitments. |
| Set up my ClawCall profile/personality | Configure global voice/personality/greeting and, if needed, inbound answering profile. |
| Configure how my number answers calls | Use inbound profile setup. Do not `POST /call`. |
| What calls came in? | Poll inbound history with `GET /me/calls?direction=inbound...`. |
| Link this agent to my ClawCall account | Use the saved API key to produce the sign-in link. |
| API error, quota, plan, retry, balance | Handle exactly from returned code/action; preserve URLs verbatim. |

## Product Coaching

Educate at decision points, not as a generic pitch.

- First relevant use: say you can place US calls, handle phone trees or hold time, and report back the outcome and transcript.
- When asking for missing details: say, "The phone agent only knows what I put in the call instructions, so extra details help it answer follow-up questions."
- Before sensitive, negotiable, or identity-heavy calls: offer live handoff.
- Before complex calls, surface likely verification, OTP, payment, fee, or live-decision points and offer the right call plan.
- For option searches, offer to call several places and compare without committing unless the user gave clear approval boundaries.
- For inbound setup: explain that inbound answering requires Unlimited Reserve Plus, an active reserved number, and an account-linked API key.
- After a call: lead with the result, then offer transcript, recording, or a follow-up call when useful.

## Persistent State

At the start of any conversation involving ClawCall, check `~/.config/clawcall/key.json` or the host secret store. If an API key exists, send it as `X-Api-Key`. A saved user phone may supply callback or reservation contact details. For live handoff, use `loop_in_user: true`; the server selects the verified account phone, not a host-saved number.

The first unauthenticated `POST /call` response can include an `api_key`. Save it immediately. When you first collect the user's own phone number, save that too:

```json
{
  "api_key": "clawcall_sk_...",
  "user_phone_number": "+15559876543"
}
```

If the user provides a ClawCall API key, replace any saved key with it.

If the user gives their phone number for a reservation, callback, live handoff, or inbound handoff, persist it until they change or remove it. Do not treat the saved user phone number as account verification or ownership proof.

To connect this agent to the user's ClawCall account, load the saved API key and send:

```text
https://clawcall.dev/sign-in?token=<api_key>
```

Do not create a new key for account linking. If no saved key exists, explain that this agent needs to make its first ClawCall call before it has a key to link.

## Profile, Personality, And Voice

Use profile setup when the user asks how ClawCall should sound, introduce itself, or answer calls.

- `voice` is the audio voice only: `jessica` (default), `sarah`, `chris`, or `eric`.
- `personality` is reusable style and behavior for outbound and inbound calls. Include assistant identity, tone, persistence, caution, and decision boundaries. Do not put one-call facts, dates, account numbers, or booking details here.
- Top-level `greeting` is the user's preferred outbound opener. Keep it short; do not rely on it for instructions, AI disclosure, or recording disclosure.
- Inbound profile `instructions` are the standing briefing for future unknown callers: who the assistant represents, what to collect, when to hand off, what never to promise or disclose, and what to report.

For a good setup, ask only for the assistant name/role, desired tone, hard boundaries, and whether to enable loop-in. No handoff number is required. See [profile and personality](references/profile-and-personality.md).

## Outbound Call Prep

Before asking the user, make a real effort to fill in public or standard details yourself.

Find these yourself when lookup tools are available:

- business phone numbers, addresses, hours, official websites, and locations
- reservation lines, front-desk numbers, store departments, repair-shop contact details
- public policies, menus, service areas, holiday hours, and ordinary business context

Ask the user mainly for private or decision-making details:

- user's name, callback number, preferences, constraints, consent
- permitted appointment logistics, customer names, dates of birth, ordinary account/order/ticket numbers, and other task-necessary details outside the restricted categories
- budget, acceptable alternatives, what to approve, what not to disclose

Do not ask "what is the restaurant's phone number?" if a normal lookup should find it. Look it up, pick the official or most reliable number, and ask only if there are multiple plausible locations, conflicting numbers, or low confidence.

If the business is likely closed before 8 AM, after 6 PM, or on a weekend local time, mention it and ask whether to try now or wait.

## Pre-Call Recon And Moderate Probing

For complex calls, do call reconnaissance before dialing. Use public research and common sense to anticipate the call shape:

- right company, number, department, location, phone tree, and hours
- likely identity checks: name, DOB, account number, reservation code, ticket number, record locator, address, email, phone on file, last-four questions
- likely OTP, payment, fee, refund, cancellation, booking, approval, or live-decision points
- whether the call should be information-only, can commit within a boundary, or should bridge the user in

Do moderate probing. Ask for the few facts that prevent a useless or risky call, then call. Do not front-load every possible question.

For a step requiring any restricted category, never ask for the values, either before or during the call. Explain the human-only loop-in plan and its capture limitation. Ordinary verification or decisions that do not involve restricted data remain allowed within the task's boundaries. Offer options:

- "I can call now and report what step needs you, without collecting restricted information."
- "I can bridge you in once I reach a person or verification step."
- "I can collect prices/availability only and not commit."
- "I can call several options and compare."

## Call Instructions

`task` is the API field name. **Call instructions** are the product concept.

Write the Call instructions like a briefing memo:

- who the agent is calling for and how to identify itself
- the goal of the call
- all known facts and reference details
- questions to ask
- acceptable alternatives
- decision boundaries
- anticipated verification, OTP, payment, fee, or handoff points
- what not to agree to, promise, or disclose
- what to do if asked for missing information
- what to do on voicemail, no answer, closure, or transfer
- what to report back

Add `personality`, `greeting`, and `voice` only when useful or explicitly specified. Defaults are good. Personality is style, not the call task. Voices: `jessica` (default, female), `sarah` (female), `chris` (male), `eric` (male).

Use [examples](references/examples.md) for rich task shapes.

## Place And Poll Outbound Calls

```http
POST /call
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

Only `to` and `task` are required. Use `loop_in_user: true` for live handoff to the verified account phone.

Response includes:

```json
{
  "call_id": "ba645d75-...",
  "status": "queued",
  "api_key": "clawcall_sk_..."
}
```

Save `api_key` if present.

Poll every 3 seconds:

```http
GET /call/{call_id}
X-Api-Key: clawcall_sk_...
```

Poll until `lifecycle = "finalized"`. Lifecycle values are `queued`, `dialing`, `answered`, `finalized`.

Terminal responses include `outcome`, `outcome_detail.reason`, `talk_seconds`, `transcript`, and `recording_url`. For a non-answered call, relay the plain-language `outcome_detail.reason.message` and honor its `retryable` flag instead of inventing a generic failure explanation. `outcome` is phone-network outcome, not task success. An `answered` call can still fail to accomplish the user's goal. Read the transcript before reporting.

Cancel/hang up:

```http
POST /call/{call_id}/hangup
X-Api-Key: clawcall_sk_...
```

## After The Call

Lead with the result, not the transcript dump. Include which number was called.

When `lifecycle = "finalized"`:

1. Check `outcome` and `outcome_detail.reason`.
2. Read the transcript.
3. Decide whether the user's goal was achieved.
4. If blocked, identify exactly what was missing or what decision is needed.
5. Ask for the missing blocker or call back if you can fix it from context.

Offer transcript, recording, retry, callback, or live handoff when useful.

## Call Campaigns And Follow-Ups

Do not treat each call as isolated. Keep campaign state across related calls: target, purpose, known facts, constraints, result, blocker, next action, and user decision needed.

Call sooner when safe:

- Low or medium risk and no irreversible commitment needed: call with clear boundaries.
- Missing public info: look it up and call or call back.
- Missing user fact: ask one focused question, then call back with prior-call context.
- Decision required: summarize options, ask the user, then call back.
- Identity verification, OTP, payment, or sensitive decision likely: offer live handoff.

Use the previous transcript in follow-up Call instructions so the phone agent can resume naturally.

Parallel or small-batch calling is useful for option exploration. Use up to 3-4 parallel calls when targets are interchangeable and the call is information-gathering only: restaurants, vendors, appointment availability, inventory checks, or quote gathering.

Do not parallelize when calls can book, buy, cancel, change, approve, or otherwise commit unless the user explicitly gave safe boundaries and duplicate commitments are impossible.

For parallel option searches, every Call instruction must say not to commit unless explicitly allowed, to gather price/availability/timing, to ask how long an option can be held without payment or commitment, and to report back for comparison.

## Live Handoff

Use live handoff when the user wants to skip hold time, reach a real person, handle identity verification, negotiate, or make real-time decisions.

Set `loop_in_user: true` without asking for a phone number. The Call instructions must include a clear trigger for when the agent should use its loop-in tool.

The server prefers the verified primary account phone, otherwise exactly one eligible verified phone. Missing or ambiguous phones require account setup. A lookup outage is temporary, not a request to reverify. The flag enables capability, not automatic answering or acceptance. Legacy `bridge_number` works when the flag is omitted; explicit false disables loop-in and true ignores the legacy destination. See [API contract](references/api-contract.md) for exact precedence and validation.

Loop-in does not promise that recording or transcription stops after the user joins. Do not describe the live conversation as private or unrecorded.

## Inbound Reserved Numbers

Inbound setup configures how ClawCall answers future calls to the user's active reserved number. It is not an outbound call.

Requirements:

- account-linked API key
- active ClawCall reserved number
- Unlimited Reserve Plus entitlement

Read before editing (the `inbound` block is `null` when not entitled):

```http
GET /me/call-preferences
X-Api-Key: clawcall_sk_...
```

Update (voice/personality are global; the inbound assistant goes under `inbound`):

```http
PUT /me/call-preferences
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

Top-level `voice`/`personality`/`greeting` are global (also drive outbound) and work for any user. The `inbound` object requires Reserve Plus + an active reserved number. Inbound required: `instructions`, `greeting`. Use optional `loop_in_user` to enable account-phone loop-in.

`inbound.loop_in_user: true` selects the reserved-number owner's verified account phone when each inbound call arrives. It supplies the existing handoff and terminal-notification destination without storing a phone in preferences. No caller ID or reserved ClawCall number can substitute for it. If lookup fails, the assistant still answers with loop-in unavailable. Legacy `handoff_number` profiles remain supported when the flag is omitted. Read current preferences before a replacement update and retain fields the user did not change.

Add `inbound.passthrough_numbers` for callers who should ring the verified account phone directly with their incoming caller ID, bypassing the assistant and recording. Read the current list before adding or removing a caller and send the complete desired list, up to 100 US numbers. Omission preserves it; `[]` clears only passthrough. Preserve the other profile and global settings in REST replacement updates. Passthrough works independently of `loop_in_user`. See [inbound reserved numbers](references/inbound-reserved-numbers.md#passthrough) for routing and no-answer behavior.

Clear the full inbound profile, including passthrough. To preserve global voice/personality/greeting, first `GET /me/call-preferences`, then echo those top-level values in the `PUT` body:

```http
PUT /me/call-preferences
Content-Type: application/json
X-Api-Key: clawcall_sk_...

{
  "voice": "<current voice>",
  "personality": "<current personality or null>",
  "greeting": "<current greeting or null>",
  "inbound": null
}
```

Poll inbound history:

```http
GET /me/calls?direction=inbound&since=<ISO_TIMESTAMP>&limit=25
X-Api-Key: clawcall_sk_...
```

For cron polling, run every 30 minutes, overlap the window, and dedupe by call `id`. `since` filters by when the call finalized, not when it started.

## Error Policy

Always preserve returned `action.url` and `action.sign_in_url` exactly.

- `invalid_phone`: ask for a valid US `+1XXXXXXXXXX` number.
- `missing_fields`: add both `to` and rich `task` Call instructions.
- `auth_required` / `invalid_api_key`: ask for a valid key, remove the bad key, or use returned auth URL.
- `quota_exceeded` / `trial_exhausted` / `plan_required` / `balance_depleted`: send the returned action URL.
- `number_pool_exhausted` / `dial_failed` / `network_error`: retry once silently when appropriate.
- `reserved_number_required`: user needs Unlimited Reserve Plus with an active reserved number for inbound configuration.
- `inbound_plan_required`: Unlimited Reserve Plus is required for inbound calls.
- `invalid_preferences`: fix the global `voice` (must be `jessica`, `sarah`, `chris`, or `eric`).
- `invalid_profile`: fix missing/invalid inbound `instructions` or `greeting`.
- `invalid_handoff_number`: ask for an external reachable handoff number that is not a ClawCall number.
- `invalid_loop_in_user`: send a boolean, not null or a string.
- `account_phone_unavailable`: connect the account or correct its verified primary phone. Never replace it with a chat-supplied number.
- `account_phone_lookup_unavailable`: explain the temporary lookup failure; the user can try again shortly. Do not ask them to reverify.
- `invalid_loop_in_destination`: explain that the account phone cannot be the other participant or a ClawCall number.

New users get trial access for 30 calls and 30 minutes, whichever lasts later. A trial call counts only after it finalizes with at least 5 seconds of talk time.

## Must-Read References

These references are required, not optional background. Before acting, read the matching reference file for the workflow in front of you; read more than one when the task crosses workflows.

- [Outbound calls](references/outbound-calls.md): must read before placing, retrying, handing off, or following up on outbound calls.
- [Inbound reserved numbers](references/inbound-reserved-numbers.md): must read before configuring, clearing, inspecting, or polling inbound reserved-number behavior.
- [API contract](references/api-contract.md): must read when constructing requests, parsing responses, or relying on exact field names.
- [Examples](references/examples.md): must read when building rich outbound, callback, handoff, campaign, or inbound instruction shapes.
- [Errors and limits](references/errors-and-limits.md): must read before handling API errors, terminal outcomes, retries, quota, trial, or balance behavior.
- [Account linking and data](references/account-linking-and-data.md): must read before account linking, key handling, saved phone-number behavior, recordings, transcripts, or privacy answers.
- [Pressure scenarios](evals/pressure-scenarios.md): must read before evaluating or changing skill behavior.
