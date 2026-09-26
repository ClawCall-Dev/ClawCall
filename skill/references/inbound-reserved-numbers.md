# Inbound Reserved Numbers

Read this when the user wants ClawCall to answer future calls to their reserved number, update their inbound assistant profile, or inspect received inbound calls.

Inbound setup is not "make a call." Do not use `POST /call`.

Never ask the user or call recipient for payment-card information subject to PCI DSS; protected health information (PHI); government identifiers, such as SSNs; or access credentials/authentication secrets, such as passwords, API keys, MFA/OTP codes. Do not request, obtain, repeat, relay, submit, or enter them yourself, even if supplied or authorized. Do not put restricted values in task, personality, greetings, inbound instructions, tool arguments, or reports. Other information is allowed when task-necessary and otherwise permitted.

If a step requires restricted data, use `loop_in_user` before the exchange so the user can handle that step directly. If loop-in is unavailable or the user cannot join, stop that part of the task and report what remains without restricted values. Loop-in does not promise that recording or transcription stops. These boundaries apply to all example briefings below.

## Requirements

Inbound reserved-number functionality requires:

- account-linked API key
- active ClawCall reserved number
- Unlimited Reserve Plus entitlement

A proto key that has not been linked to a ClawCall account cannot read, update, or poll inbound profile/history.

Coach briefly when needed: "Inbound answering is for calls to your ClawCall reserved number. It requires Unlimited Reserve Plus and an active reserved number; I can read or update the assistant profile if this key is linked to your account."

## Configure Profile

Voice and personality are **global** — they are shared with outbound calls and live at the top level of `/me/call-preferences`. The inbound-only instructions, answer-line greeting, and loop-in flag live under the `inbound` key. For reusable style guidance, read [profile and personality](profile-and-personality.md).

Read current preferences (includes the `inbound` block when the user is entitled, otherwise `inbound` is `null`):

```http
GET /me/call-preferences
X-Api-Key: clawcall_sk_...
```

Update the inbound assistant (you may set global voice/personality in the same call):

```http
PUT /me/call-preferences
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

```json
{
  "voice": "sarah",
  "personality": "Warm, concise, professional.",
  "inbound": {
    "instructions": "...",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "loop_in_user": true
  }
}
```

Top-level `voice`/`personality`/`greeting` are global and work for any authenticated user. The `inbound` object requires an active reserved number + Unlimited Reserve Plus — otherwise the request fails (402 `reserved_number_required` / 403 `inbound_plan_required`).

Inbound fields required: `instructions`, `greeting`. Set optional `loop_in_user: true` to enable loop-in without entering a phone number.

The server resolves the reserved-number owner's verified primary phone, otherwise exactly one eligible verified phone, when each call arrives. It cannot use the caller's number, the active reserved number, or another ClawCall-owned number. This destination also supplies existing terminal SMS notifications. Answering and consult acceptance do not change.

Saving true validates the account phone before writing the profile. Lookup failures during a later call disable loop-in for that call while preserving normal assistant or voicemail behavior. Do not substitute another number.

Explicit false disables loop-in and ignores `handoff_number`. Explicit true uses the account phone and ignores that legacy field. Omitting the flag preserves numbered legacy profiles and replacement requests. A REST PUT replaces the supplied inbound block: echo existing settings to retain them. Omitting the entire inbound block leaves it unchanged. Null for the flag is invalid; `inbound: null` still clears the whole profile.

Editing a profile affects only future inbound calls. Active calls keep the snapshot they started with.

Clear the inbound assistant. To preserve global voice/personality/greeting, first read current preferences and echo the top-level values:

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

(`DELETE /me/call-preferences` resets your **global** voice/personality/greeting, not the inbound block.)

## Good Inbound Instructions

Inbound instructions should help the assistant answer many unknown callers, not just one known task.

Include:

- how to identify itself
- what caller details to collect
- categories of calls to handle
- when to use handoff
- what never to promise or disclose
- what to capture for follow-up
- how to handle spam, solicitors, or vague callers

Example:

```json
{
  "voice": "sarah",
  "personality": "Warm, concise, professional, protective of Jordan's time, and careful about commitments.",
  "inbound": {
    "instructions": "Answer inbound calls to Jordan Lee's ClawCall reserved number as Jordan's assistant. Start by finding out who is calling, what organization they represent if any, the reason for the call, urgency, and the best callback number. For appointments, deliveries, orders, repairs, reservations, or billing calls, collect concrete details: dates, times, locations, confirmation or ticket numbers, quoted amounts, deadlines, and the exact next step requested. If the caller asks for Jordan and the matter is urgent, sensitive, or requires a real-time decision, use handoff if the tool is available. If the caller is a spammer, solicitor, or refuses to identify the reason for calling, politely end the call. Do not claim to be Jordan, do not provide payment information, do not agree to legal or financial commitments, do not disclose private personal information, and do not invent facts. If a caller only wants to leave a message, take a concise message and confirm their callback number before ending. After each call, the transcript should make it easy to tell who called, why, urgency, callback number, and recommended follow-up.",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "loop_in_user": true
  }
}
```

## Poll Received Calls

Use this for user-authorized agents that need periodic inbound history. Run from a cron every 30 minutes:

```http
GET /me/calls?direction=inbound&since=<ISO_TIMESTAMP>&limit=25
X-Api-Key: clawcall_sk_...
```

`since` is inclusive and filters by when the call finalized, not when it started. Use a small overlap from the previous successful poll and dedupe by call `id`. If `since` is omitted, the API returns the latest terminal inbound calls using the default page size.

Inbound polling returns only terminal inbound Calls and requires inbound eligibility. Non-inbound users can still read outbound history without the inbound filter.


## Passthrough

Set `inbound.passthrough_numbers` to caller numbers that should ring the owner's verified account phone directly. For example, `{"inbound":{"passthrough_numbers":["+14155550123"]}}` through `update_call_settings`. This replaces the list; send `[]` to clear it. Omitted lists stay unchanged. To add or remove a caller, read the current settings first and send the complete desired list. Up to 100 unique US E.164 numbers are supported.

Matched callers keep their incoming caller ID and bypass the assistant, greeting, recording and transcription. Passthrough works independently of `loop_in_user`, including when the assistant is handling another call. Unmatched callers follow the saved assistant behavior. The destination always comes from the verified account phone, never `handoff_number`. A missing eligible destination rejects the call. If the destination does not answer within 30 seconds, the call ends; the destination's voicemail may answer first. Avoid enabling passthrough if that phone forwards calls back to the reserved number.

Call history reports `handling_mode: "passthrough"`. Final handset display is controlled by the destination carrier.
