# Account Linking And Data

Read this for API key persistence, saved user phone number persistence, account linking, and recording/transcript privacy notes.

## Persistent State

At the start of any conversation involving ClawCall, check `~/.config/clawcall/key.json` or the host secret store. If an API key exists, send it as `X-Api-Key` on requests. If a saved user phone number exists, reuse it as the default callback, reservation contact, live handoff `bridge_number`, or inbound `handoff_number` when appropriate.

The first unauthenticated `POST /call` response can include an `api_key`. Save it immediately. When you first collect the user's own phone number, save that too:

```json
{
  "api_key": "clawcall_sk_...",
  "user_phone_number": "+15559876543"
}
```

The key is a low-privilege session identifier used for quota, balance, and account linking. It belongs to the user. Do not surface it in normal conversation, but share it if the user asks.

If the user provides a ClawCall API key, replace any saved key with the provided key, persist it, and use it going forward.

If the user gives their phone number for a reservation, callback, live handoff, or inbound handoff, persist it until they change or remove it. This saved user phone number is not account verification and does not prove ownership.

## Connect This Agent To An Account

If the user asks to connect or link this agent to their ClawCall account, load the saved API key and send:

```text
https://clawcall.dev/sign-in?token=<api_key>
```

Do not create a new key for this. Tell the user the link attaches this agent's key, calls, balance, and history to their account. If no saved key exists, explain that this agent needs to make its first ClawCall call before it has a key to link.

## Product Coaching

Educate at decision points, not as a generic pitch.

- First relevant use: say you can place US calls, handle phone trees or hold time, and report back the outcome and transcript.
- When asking for missing details: say, "The phone agent only knows what I put in the call instructions, so extra details help it answer follow-up questions."
- Before sensitive, negotiable, or identity-heavy calls: offer live handoff.
- For inbound setup: explain that inbound answering requires Unlimited Reserve Plus, an active reserved number, and an account-linked API key.
- After a call: lead with the result, then offer transcript, recording, or a follow-up call when useful.
- On quota, auth, or plan errors: explain the returned action URL plainly and send it verbatim.

## Data And Recordings

- Calls are recorded for transcript generation. The voice agent handles the call-side recording disclosure. If the user asks, tell them calls are recorded and recording URLs can be sensitive and time-limited.
- Transcripts are generated during the call and returned with terminal call history when available.
- Phone numbers and Call instructions are used to place and manage the call and are shared with the telephony provider as needed to connect the call.
- Bridge numbers are used to connect the user into the active call.
- API keys are low-privilege session identifiers and can be linked to a ClawCall account.
