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

## Choose The Workflow

| User intent | Do this |
| --- | --- |
| Call someone now | Build rich Call instructions, `POST /call`, then poll `GET /call/{call_id}` until `lifecycle = "finalized"`. |
| Get through to a person / connect me | Use outbound calling with `bridge_number` and a handoff trigger in the Call instructions. |
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

At the start of any conversation involving ClawCall, check `~/.config/clawcall/key.json` or the host secret store. If an API key exists, send it as `X-Api-Key`. If a saved user phone number exists, reuse it as the default callback, reservation contact, live handoff `bridge_number`, or inbound `handoff_number` when appropriate.

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

For a good setup, ask only for the assistant name/role, desired tone, hard boundaries, and default handoff/callback number when useful. See [profile and personality](references/profile-and-personality.md).

## Outbound Call Prep

Before asking the user, make a real effort to fill in public or standard details yourself.

Find these yourself when lookup tools are available:

- business phone numbers, addresses, hours, official websites, and locations
- reservation lines, front-desk numbers, store departments, repair-shop contact details
- public policies, menus, service areas, holiday hours, and ordinary business context

Ask the user mainly for private or decision-making details:

- user's name, callback number, preferences, constraints, consent
- appointment dates, patient/customer names, dates of birth, account/order/ticket numbers, insurance details
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

For OTPs, payment details, passwords, identity verification, or sensitive decisions: do not ask for passwords or stale OTPs up front. Tell the user the call may require live verification and offer options:

- "I can call now and come back if they need private info."
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

Only `to` and `task` are required. Include `bridge_number` only for live handoff.

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

Terminal responses include `outcome`, `talk_seconds`, `transcript`, and `recording_url`. `outcome` is phone-network outcome, not task success. An `answered` call can still fail to accomplish the user's goal. Read the transcript before reporting.

Cancel/hang up:

```http
POST /call/{call_id}/hangup
X-Api-Key: clawcall_sk_...
```

## After The Call

Lead with the result, not the transcript dump. Include which number was called.

When `lifecycle = "finalized"`:

1. Check `outcome`.
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

Ask for the user's own callback number, then include it as `bridge_number`. The Call instructions must include a clear trigger like: "Once you are speaking with someone who can help, tell them you are connecting Jordan now, then bridge Jordan into the live call."

If a saved user phone number exists, use it as the default `bridge_number`; confirm only when the call is sensitive, the number may be stale, or the user asks to use a different number. If you collect a new bridge/callback number, persist it.

The transcript covers everything before handoff. After the user joins, the live conversation is private.

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

Top-level `voice`/`personality`/`greeting` are global (also drive outbound) and work for any user. The `inbound` object requires Reserve Plus + an active reserved number. Inbound required: `instructions`, `greeting`. Optional: `handoff_number`.

`handoff_number` is structured data. It receives inbound terminal SMS notifications and is the number the voice agent can bridge into an inbound call. It cannot be the user's active reserved number or any ClawCall-owned number. If a saved user phone number exists, offer it as the default `handoff_number`; persist any new handoff number the user provides.

Clear the inbound assistant. To preserve global voice/personality/greeting, first `GET /me/call-preferences`, then echo those top-level values in the `PUT` body:

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

New users get trial access for 10 calls and 10 minutes, whichever lasts later. A trial call counts only after it finalizes with at least 5 seconds of talk time.

## References

Rich details live here:

- [Outbound calls](references/outbound-calls.md): deeper prep, live handoff, callbacks, after-call diagnosis.
- [Profile and personality](references/profile-and-personality.md): global voice/personality/greeting and inbound profile setup.
- [Inbound reserved numbers](references/inbound-reserved-numbers.md): full inbound profile setup and polling guidance.
- [API contract](references/api-contract.md): complete request/response shapes.
- [Examples](references/examples.md): rich outbound, callback, handoff, and inbound examples.
- [Errors and limits](references/errors-and-limits.md): full error/outcome tables.
- [Account linking and data](references/account-linking-and-data.md): API key, sign-in link, recordings, transcripts.
- [Pressure scenarios](evals/pressure-scenarios.md): behavior checks for future edits.
