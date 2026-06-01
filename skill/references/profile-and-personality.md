# Profile And Personality

Read this when the user wants to set up how ClawCall sounds, introduces itself, behaves on calls, or answers an inbound reserved number.

## Field Map

- `voice`: sound only. Valid values are `jessica` (default), `sarah`, `chris`, and `eric`.
- `personality`: reusable style for both outbound and inbound calls. Put identity, tone, persistence, caution, and standing boundaries here.
- Top-level `greeting`: preferred outbound opener. Keep it short. Do not put task details or required instructions here.
- `inbound.instructions`: standing profile for future calls to the user's reserved number.
- `inbound.greeting`: short answer line for inbound calls.
- `inbound.handoff_number`: number to call when the inbound assistant should connect the reserved-number owner.

## Good Personality

Use 1-3 concise sentences:

```text
Alex, a calm assistant calling on behalf of Jordan Lee. Be concise, polite, and persistent with phone menus; confirm names, dates, and numbers before acting. Never make commitments, share private details, or approve payments outside the call instructions.
```

Include:

- assistant name or role
- relationship to the user
- tone: calm, direct, warm, formal, persistent
- operating rules: confirm details, ask clarifying questions, summarize blockers
- boundaries: no payments, no irreversible changes, no private disclosures unless explicitly provided

Do not include one-off facts such as reservation dates, order numbers, account numbers, OTPs, or appointment details. Put those in the outbound `task` or inbound `instructions`.

## Good Outbound Setup

For a reusable outbound profile:

```json
{
  "voice": "jessica",
  "personality": "Alex, a calm assistant calling on behalf of Jordan Lee. Be concise, polite, and persistent with phone menus; confirm names, dates, and numbers before acting. Never make commitments, share private details, or approve payments outside the call instructions.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee."
}
```

For one call, still put the real job in `task`; the profile only shapes how the agent behaves.

## Good Inbound Profile

Inbound instructions should work for unknown future callers. Include:

- who the assistant represents
- what caller details to collect: name, organization, reason, urgency, callback number
- which topics to handle: appointments, orders, deliveries, billing, scheduling, messages
- when to hand off to the owner
- what never to promise, disclose, or decide
- what the transcript should make clear after the call

Example:

```json
{
  "voice": "sarah",
  "personality": "Warm, concise, professional, protective of Jordan's time, and careful about commitments.",
  "inbound": {
    "instructions": "Answer inbound calls to Jordan Lee's ClawCall reserved number as Jordan's assistant. Find out who is calling, what organization they represent if any, why they are calling, urgency, and the best callback number. For appointments, deliveries, orders, repairs, reservations, or billing calls, collect concrete details: dates, times, locations, confirmation or ticket numbers, quoted amounts, deadlines, and requested next steps. If the caller asks for Jordan and the matter is urgent, sensitive, or requires a real-time decision, use handoff if available. Do not claim to be Jordan, provide payment information, agree to legal or financial commitments, disclose private information, or invent facts. If a caller wants to leave a message, take a concise message and confirm their callback number. After each call, the transcript should make it easy to tell who called, why, urgency, callback number, and recommended follow-up.",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "handoff_number": "+15559876543"
  }
}
```

When updating only the inbound profile or clearing it, first read current preferences and echo existing top-level `voice`, `personality`, and `greeting` in the `PUT` body so they are not reset.
