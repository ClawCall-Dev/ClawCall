# Outbound Calls

Read this before placing a call now, retrying a call, or using live handoff.

Never ask the user or call recipient for payment-card information subject to PCI DSS; protected health information (PHI); government identifiers, such as SSNs; or access credentials/authentication secrets, such as passwords, API keys, MFA/OTP codes. Do not request, obtain, repeat, relay, submit, or enter them yourself, even if supplied or authorized. Do not put restricted values in task, personality, greetings, inbound instructions, tool arguments, or reports. Other information is allowed when task-necessary and otherwise permitted.

If a step requires restricted data, use `loop_in_user` before the exchange so the user can handle that step directly. If loop-in is unavailable or the user cannot join, stop that part of the task and report what remains without restricted values. Loop-in does not promise that recording or transcription stops. These boundaries apply to all example briefings below.

## Gather Details Without Pestering

Before asking the user, make a real effort to fill in public or standard details yourself.

Find these yourself when lookup tools are available:

- business phone numbers, addresses, hours, official websites, and locations
- restaurant reservation lines, front-desk numbers, store departments, repair-shop contact details
- public policies, menus, service areas, holiday hours, and ordinary business context

Ask the user mainly for private or decision-making details:

- user's name, callback number, preferences, constraints, consent
- permitted appointment logistics, customer names, dates of birth, ordinary account/order/ticket numbers, and other task-necessary details outside the restricted categories
- budget, acceptable alternatives, what to approve, what not to disclose

When you first collect the user's own phone number for a callback, reservation contact, or live handoff, persist it as `user_phone_number` in the ClawCall state file or host secret store. Reuse it until the user changes or removes it.

Do not ask "what is the restaurant's phone number?" if a normal web or local-business lookup should find it. Look it up, pick the official or most reliable number, and ask only if there are multiple plausible locations, conflicting numbers, or low confidence.

If the business is likely closed before 8 AM, after 6 PM, or on a weekend local time, mention it and ask whether to try now or wait.

## Pre-Call Recon And Moderate Probing

For complex calls, do call reconnaissance before dialing. Research and infer the likely phone call shape:

- correct company, number, department, location, phone tree, and hours
- likely identity checks: name, DOB, account number, reservation code, ticket number, record locator, address, email, phone on file, last-four questions
- likely OTP, payment, fee, refund, cancellation, booking, approval, or live-decision points
- whether the call should be information-only, may commit within a boundary, or should bridge the user in

Ask the few high-leverage questions that prevent a useless or risky call. Do not interrogate the user for every possible edge case before calling.

For OTPs, payment details, passwords, identity verification, or sensitive decisions:

- do not ask for passwords
- never ask for OTPs or other restricted values, before or during the call
- tell the user the call may require live verification
- offer to bridge the user once the agent reaches a person or verification step
- offer to call first and report which step requires the user, without collecting restricted values

Example coaching:

```text
Airline calls often require the passenger name, record locator, flight details, and may trigger identity verification or an OTP. I can call now to handle the menu and hold time, then either bridge you in if they need live verification/payment approval or come back with the exact blocker.
```

## Build Call Instructions

Call instructions are the complete briefing the phone agent receives. Send them as the `task` field.

Include:

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

Weak:

```text
Check on my appointment.
```

Strong:

```text
Call Dr. Rivera's office on behalf of Jordan Lee. Jordan is calling about an existing dental cleaning appointment currently believed to be Tuesday, March 30 at 2:30 PM. Confirm whether that appointment is still on the calendar, confirm the office location, and ask whether Jordan needs to bring updated insurance information. If the office says the appointment must be rescheduled, ask for openings on Wednesday or Thursday after 2 PM; do not accept a morning slot or a different provider without checking with Jordan first. If they ask for Jordan's date of birth, say you do not have it available and will call back with that information. If you reach voicemail, leave a concise message asking them to call Jordan back to confirm the appointment and mention that Jordan is trying to confirm the Tuesday March 30 2:30 PM appointment. If the office is closed or the line does not answer, hang up and report that back.
```


## Make The Call

```http
POST /call
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

Only `to` and `task` are required. Add `personality`, `voice`, and `greeting` only when useful or specified; see [profile and personality](profile-and-personality.md). Use `loop_in_user: true` for live handoff to the verified account phone.

Save `api_key` if present in the response.

## Polling

Poll every 3 seconds:

```http
GET /call/{call_id}
X-Api-Key: clawcall_sk_...
```

Poll until `lifecycle = "finalized"`. Calls can take several minutes because of phone trees, hold time, or long conversations.

## Cancel Or Hang Up

```http
POST /call/{call_id}/hangup
X-Api-Key: clawcall_sk_...
```

This is idempotent. Already-ended calls return success. You can only hang up calls you initiated.

## After The Call

Lead with the result and the number called:

- "I called +15551234567 (Dr. Rivera's office). Your appointment is confirmed for Tuesday at 2:30 PM, and they asked you to bring updated insurance."
- "I called +15551234567. They do not have Friday at 7 PM, but Saturday at 6:45 PM is available. Want me to call back and book it?"
- "I called +15551234567. They asked for your date of birth before they would discuss the appointment, so I did not get confirmation yet."

Then offer transcript, recording, retry, callback, or live handoff when useful.

## Diagnose Task Success

When `lifecycle = "finalized"`:

1. Check `outcome` and `outcome_detail.reason`; relay its message for non-answered calls.
2. Read the transcript.
3. Decide whether the user's goal was achieved.
4. If blocked, identify exactly what was missing or what decision is needed.
5. Ask for the missing blocker or call back if you can fix it from context.

`outcome` is phone-network outcome, not task success. An answered call can still fail to accomplish the user's goal.

## Follow-Up Calls

When a call comes back blocked, do not restart from scratch. Use the prior transcript and campaign state.

- Missing public info: look it up, then call back.
- Missing user fact: ask one focused question, then call back.
- Decision required: summarize options and ask the user, then call back.
- Restricted-data step: use live handoff before the exchange so the user handles it directly, or stop that part if they cannot join. Never have the user provide a code or other restricted value to the agent.
- Transient failure: retry once silently for `dial_failed`, `network_error`, or `number_pool_exhausted`; ask before retrying `no_answer`, `busy`, or `rejected`.

Follow-up Call instructions should say this is a callback, include the prior-call context, the newly supplied fact or decision, and the exact next step.

## Parallel Option Calls

Use up to 3-4 parallel calls when the user is exploring interchangeable options and the calls are information-gathering only:

- restaurant availability
- appointment availability across offices
- vendor or repair-shop quotes
- inventory checks
- policy or timing comparisons

Do not parallelize when calls can book, buy, cancel, change, approve, or otherwise commit unless the user explicitly gave safe boundaries and duplicate commitments are impossible.

Every parallel option-search task must include:

- do not commit unless explicitly allowed
- gather price/availability/timing and relevant constraints
- ask whether an option can be held without payment or commitment, and for how long
- report back for comparison instead of dumping transcripts

## Live Handoff

Use live handoff when the user wants to skip hold time, reach a real person, handle identity verification, negotiate, or make real-time decisions.

Set `loop_in_user: true` without asking for a phone number. The server selects the verified primary account phone, or its single eligible verified phone. With the default warm greeting, the user answers and decides whether to join. This flag only makes the loop-in tool available to the agent.

`warm_greeting` defaults to true. True gives the user a private greeting and asks whether to join. False connects as soon as the callback answers, without a greeting or acceptance question. A screening service or voicemail can answer too. This setting does not enable loop-in by itself. Save the choice as top-level `warm_greeting` in `/me/call-preferences` for both inbound and outbound loop-in. An optional `warm_greeting` on `POST /call` overrides it for that call; omission uses the saved choice.

Omitting the flag preserves legacy `bridge_number` behavior. Explicit false disables loop-in, even with a legacy number. Explicit true selects the account phone, ignoring the legacy destination. Missing or ambiguous verified phones fail before dialing; a temporary lookup outage has a separate unavailable error. Never substitute a host-saved number or caller ID.

The Call instructions need an explicit trigger:

```json
{
  "to": "+15551234567",
  "task": "Call Dr. Rivera's office on behalf of Jordan Lee. Navigate the phone menu and wait on hold if needed. Tell the receptionist Jordan needs to reschedule an existing appointment. Do not choose a new appointment time yourself. Once you are speaking with someone who can reschedule the appointment, tell them you are connecting Jordan now, then bridge Jordan into the live call. If the office asks identity-verification questions before the handoff, bridge Jordan rather than guessing. If the office is closed or no one answers, hang up and report that back.",
  "loop_in_user": true,
  "personality": "Alex, a calm assistant calling on behalf of Jordan Lee.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee about rescheduling an appointment."
}
```

Loop-in does not promise that recording or transcription stops after the user joins. Do not describe the live conversation as private or unrecorded.
