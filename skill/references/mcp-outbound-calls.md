# Outbound calling guide

Prepare a complete briefing, recommend a call plan, and help the user act on the result.

## Restricted call data

Never ask the user or call recipient for payment-card information subject to PCI DSS; protected health information (PHI); government identifiers, such as SSNs; or access credentials/authentication secrets, such as passwords, API keys, MFA/OTP codes. Do not request, obtain, repeat, relay, submit, or enter them yourself, even if supplied or authorized. Do not put restricted values in `task`, `personality`, greetings, or tool arguments.

If a step requires one of these categories, use `loop_in_user` before the exchange so the user can handle that step directly. Set `loop_in_user: true` and put this human-only boundary in `task`. If loop-in is unavailable or the user cannot join, stop that part of the task and report what remains without restricted values. Loop-in does not promise that recording or transcription stops.

Other information is allowed when task-necessary and otherwise permitted. This is not a ban on all personal information, ordinary account/reference numbers, health topics, financial details, verification, payments, or calls to banks, clinics, insurers, or government offices. Public clinic hours and prices differ from obtaining an identified patient's clinical records or medical claim details. A safe information-only or hold-and-connect plan leaves every restricted exchange to the human. A loop-in flag alone does not make an instruction for the AI to handle restricted data acceptable. Do not silently change a prohibited task into a different call; explain the boundary and agree on a permitted plan. Existing safety refusals still apply.

## Give the phone agent a complete briefing

You are the requesting agent. ClawCall's phone agent is a separate actor. It does not know your conversation with the user, your research, or a previous call unless you put the relevant information into the Call instructions in `task`.

Every call needs the intended recipient, the person represented, a truthful assistant introduction, the purpose, the questions or actions, the permitted scope, fallback instructions, and what to report. A bare question such as "What time do you close today?" is not a complete briefing, even when you supply a phone number.

Use relevant detail, not filler. A simple information call needs a shorter briefing than a flight change, but it still needs context and an operating plan. Never invent names, preferences, authority, or missing facts.

Read this guide before every outbound call. Read `get_calling_guide` with topic `examples` when writing the task, and topic `errors` when a returned error needs explanation. Honor safety refusals; a different phrasing or loop-in does not override them.

## Recommend how to proceed before asking for details

Start with the user's desired outcome. Decide whether to gather information, act within approved boundaries, reach a person and loop the user in, or compare several options. Recommend the plan that gets useful work done while protecting the user's decisions.

- Information only: collect hours, status, availability, prices, or options. Say that you will not book, buy, cancel, or approve anything.
- Action within boundaries: include the exact booking, change, cancellation, or approval the user requested, plus limits on fees and alternatives.
- Loop the user in: offer to handle menus and hold time, then call the user's verified account phone when their participation is useful.
- Compare options: call a small set of suitable businesses without creating duplicate commitments.

Educate at the decision point. Explain a capability when it helps the user choose, not as a repeated sales pitch. Do not ask for a second approval of an action the user already authorized. Ask when a new commitment, material alternative, or spending limit is genuinely undecided.

### Example: Offer a useful choice

The user wants help changing a flight.

#### Say to the user

I can handle the phone menu and hold time, collect the change options and fees, and avoid accepting anything. If they need live verification or a decision, I can loop you in. Would you prefer that, or should I return with the options first?

## Research public facts and reuse known user details

- Look up the official business number, branch, address, department, and recipient-local hours when relevant. Include the useful results in the briefing.
- Research public policies, menus, service areas, and ordinary business context before asking the user to find them.
- Resolve conflicting numbers or multiple plausible locations. Ask which location the user means only when context and reliable research do not settle it.
- Reuse known names, callback details, preferences, dates, references, and prior-call context. Do not ask the user to repeat information already available.
- Ask focused questions for missing private facts or decisions: the relevant customer name, booking or ticket reference, acceptable times, budget, approval boundary, or desired fallback.
- Check hours before an early-morning, evening, or weekend attempt. These times are reasons to check, not proof that the business is closed. If it is likely closed, explain the choice to try now, leave an authorized message, or wait.

Explain why a question matters: "The phone agent only knows what I put in its instructions. I already have the shop and ticket details; what total repair amount may it approve?" Complete the briefing efficiently rather than asking about every hypothetical edge case.

Do not ask the user for the answer the call is meant to discover. An unknown price or closing time is not missing preparation. The recipient's identity, the user's context, and the questions to ask are preparation.

For callback or reservation contact details, reuse a suitable saved user number. Save a newly supplied number when the host supports that and the user has not limited its use. Do not confuse a saved contact with identity verification or the automatic loop-in destination.

## Build the Call instructions

Write `task` as a self-contained briefing. Cover all of the following. Resolve irrelevant branches with a simple explicit plan instead of guessing.

- Who is being called: business or person, location, and the department or role needed. A number alone is not a recipient briefing.
- Who the assistant represents and how it should introduce itself. Use the known user identity and relevant relationship; respect a deliberate choice not to disclose a name.
- Why this call is happening and the result the user wants.
- All relevant known facts and reference details, including dates, times, names, orders, tickets, preferences, and prior-call context.
- The questions to ask and any necessary sequence, such as confirming the record before discussing a change.
- Acceptable alternatives and what to do when the preferred result is unavailable. Do not invent flexibility.
- What may be booked, changed, cancelled, approved, or paid, with exact limits. For information-only calls, explicitly forbid commitments.
- What not to agree to, promise, disclose, or fabricate.
- Likely verification, one-time-code, payment, fee, or live-decision points, and the chosen loop-in or report-back plan.
- What to do if asked for information the phone agent does not have.
- What to do through menus, hold time, transfers, voicemail, no answer, or closure.
- What to report: confirmed facts, actions actually taken, alternatives, deadlines, and exact unresolved blockers.

A voicemail plan that requests a return call must include an authorized callback route. If no message is useful, say not to leave one. Do not assume ClawCall's caller ID reaches the user.

Keep one-call facts in `task`. `personality` holds reusable identity, tone, persistence, and standing boundaries. `voice` changes sound only; supported voices are `jessica`, `sarah`, `chris`, and `eric`. Defaults are fine. The MCP guide does not require a custom greeting.

Before submitting, read the briefing as if you had no access to the surrounding chat. Resolve contradictions between the task, personality, target, and permitted actions.

## Suggest loop-in when human participation would help

Proactively offer loop-in for hold-skipping, identity-heavy account work, likely one-time codes, payment approval, negotiation, or a decision the user has not delegated. Do not insist on it for every information-only call.

Use `loop_in_user: true` when the chosen plan includes loop-in. The server selects the eligible verified primary account phone, or the single eligible verified phone. Do not ask the user to type a handoff number by default. Do not substitute a host-saved number or caller ID.

The flag enables the phone agent's loop-in capability. It does not immediately connect the user. Put the trigger in `task`, such as "after reaching someone who can help," "before verification," or "before an unapproved fee." Define what the phone agent should do first and how to introduce the user.

Explain the experience: ClawCall calls the user's verified phone, explains why they are needed, and the user decides whether to join. Do not describe answering as automatic consent to connect.

Plan for no answer, a declined invitation, or a failed connection. The phone agent should avoid new commitments, collect the next step or authorized callback information, and return an actionable blocker. Do not promise that the user will be available.

Do not collect restricted values to prepare or carry out the call. Have the user handle a restricted exchange directly through the agreed loop-in plan, or stop that part if they cannot join.

Explicit `loop_in_user: false` disables loop-in. Omitting the flag preserves the documented legacy behavior. Use the automatic account-phone path for new loop-in plans. If the connected tool does not expose the flag, do not invent an argument or promise that capability; explain the mismatch and use an available, agreed call plan.

If the account phone is missing or ambiguous, follow the returned account-verification action. Treat lookup outages as temporary. Do not silently select an arbitrary number.

Do not promise that recording or transcription stops when the user joins. Post-handoff capture depends on the actual settings and supported behavior. Use the applicable disclosure, check known settings when privacy matters, and say when you cannot verify them.

## Keep the user informed while the call is in progress

Use `place_call` with the complete briefing and the selected options. The currently published calling flow returns a call ID. Poll `get_call` about every three seconds until the lifecycle is `finalized`; calls can take several minutes through menus and hold. Use `hangup_call` for a user-requested cancellation.

When an observable development matters, give a short factual update. For example, explain that the agent is on hold only if the returned status or transcript supports it. Do not invent progress from elapsed time alone.

Avoid repeated "still calling" messages that add no information. Update the user when there is a meaningful delay, an imminent planned loop-in, a blocker, or a decision they can usefully make. Whether a live update is possible depends on the host's conversation and notification capabilities.

Do not tell the user that you can rewrite a running call's instructions unless the connected tools explicitly support that. If new facts or authority are needed, use the planned loop-in path or return with the exact requirement for a follow-up call.

The phone agent must follow its prewritten plan when a new fee, verification step, or choice appears. Do not assume the user can answer a chat question quickly enough to control the live phone conversation.

### Example: Explain a meaningful live development

A current transcript confirms that the agent has reached a representative who needs identity verification.

#### Say to the user, if the host can deliver a live update

They've reached someone who can help, but the next step needs your verification. The call was set up to loop you in at this point, so expect a call to your verified account phone. You can decide whether to join.

#### If live updates are unavailable

Do not promise an in-chat alert. Let the configured loop-in flow contact the user, or use the briefing's report-back fallback.

## Report the result, explain the next step, and offer useful capabilities

1. Wait for `lifecycle = finalized`. Read the outcome and its reason, then use `get_call_transcript` to inspect the full conversation.
2. Determine whether the user's goal was achieved. A connected or answered call is not proof of a booking, approval, or resolution.
3. Lead with the result and the business or number called. State what was confirmed, changed, approved, declined, or left undecided.
4. If blocked, identify the exact missing fact, permission, person, or decision. Distinguish an unavailable option from a failed connection.
5. Recommend the next action. Research a missing public fact yourself, ask a focused user question, compare returned options, prepare a callback, or offer loop-in.
6. Offer a transcript or recording when it helps the user verify the result. Use `get_recording` for the available temporary link; do not promise a recording exists or treat its URL as permanent.

Teach through the result: "They need you to verify the account. Next time I can handle the hold and loop you in at that step." This is more useful than a generic list of ClawCall features.

If the user already authorized a follow-up within clear boundaries, explain and proceed when safe. If a new decision is needed, ask before booking, paying, cancelling, or accepting a material alternative. Do not create a recurring monitor or future callback schedule without the user's authorization and a supported scheduling mechanism.

Honor returned retry guidance and preserve action URLs exactly. Inspect an uncertain execution instead of blindly submitting a duplicate. Ask before retrying no answer, busy, or rejected calls unless that retry was already authorized.

## Use prior-call context and compare options without duplicate commitments

For a callback, include the relevant previous conversation, what blocked progress, the new detail or decision, and the exact next action. Do not assume the phone agent remembers the previous call. Do not copy irrelevant transcript material.

Maintain campaign context in the requesting agent: target, purpose, known facts, constraints, result, blocker, next action, and user decision needed.

For interchangeable information-gathering targets, use up to three or four parallel calls when the tools support it. Each call must still have a complete briefing. Do not parallelize commitments unless explicit user boundaries make duplicate commitments impossible.

Every option-search briefing should forbid commitments unless authorized, gather comparable availability, price, timing, and constraints, ask about a no-obligation hold and its expiry where useful, and return facts for comparison. If a recipient demands a deposit or immediate booking, follow the no-commitment or approved loop-in plan.

## Use complete examples, including what to tell the user

All names, businesses, phone numbers, dates, and amounts below are fictional illustration data. Replace them with researched or user-provided facts. Never copy example details into a real call.

### Example: A simple hours inquiry still needs context

Jordan wants Ember Table's downtown location's hours for September 10, 2026. The official contact has already been researched.

#### Before the call

I found the downtown location's number. I'll confirm its hours for September 10 and report back. This is information only; I won't make a booking.

#### Call request

```json
{
  "to": "+12025550110",
  "loop_in_user": false,
  "task": "Call Ember Table's downtown location on behalf of Jordan Lee. Introduce yourself as Jordan's personal assistant and confirm the location. Jordan wants the restaurant's opening and closing times for September 10, 2026, in the restaurant's local time. This is information only: do not book, order, pay, or make commitments. Ask for that day's hours and clarify the day or location if the answer is ambiguous. Navigate the menu or ask for someone who can confirm the hours; restate the purpose after a transfer. If this is the wrong location, ask for the correct contact and report it rather than making another call yourself. If asked for private information you lack, do not guess; explain that it is unavailable and report any blocker. If closed, unanswered, or sent to voicemail, do not leave a message; end and report. No loop-in is planned. Report the number and location reached, confirmed hours, and any uncertainty or reason the answer could not be obtained."
}
```

#### After the call, if those facts were confirmed

The downtown restaurant confirmed 11 AM–9 PM on September 10. I didn't make a reservation. If you want a table, tell me the party size and preferred time, and I can check availability next.

### Example: Reach a person and loop the user in

Jordan wants to reschedule an appointment personally after the assistant handles menus and hold.

#### Before the call

I can get through to the office and loop you in once someone who can reschedule is on the line. ClawCall will call your verified account phone, and you choose whether to join. If you can't join, I'll ask for the next step without changing the appointment.

#### Call request

```json
{
  "to": "+12025550111",
  "loop_in_user": true,
  "task": "Call River Dental's downtown office on behalf of Jordan Lee about the existing appointment on September 15, 2026, at 2:30 PM. Introduce yourself as Jordan's personal assistant. The goal is to reach someone who can reschedule, then connect Jordan so Jordan can choose the new time. Navigate menus and wait on hold. Confirm the correct office and restate the purpose after transfers. Do not choose a replacement time, cancel the existing appointment, accept a fee, or disclose facts you do not have. Once a representative who can help is available, explain that you are connecting Jordan, then use loop-in. If verification is required first, use loop-in at that point instead of guessing. If Jordan declines, is unavailable, or cannot be connected, ask what Jordan needs to provide and the best way to resume; make no appointment change. If the office is closed, unanswered, or reaches voicemail, do not leave a message. Report whether Jordan connected, whether any change was made before handoff, and any unresolved next step."
}
```

#### After the call, if Jordan could not join

I reached the scheduling desk, but you weren't available to join. Your existing appointment is unchanged. They said you'll need to verify your identity before choosing a new time. I can handle the hold again and loop you in when you're ready.

### Example: Approve a repair only within a supplied limit

Jordan has supplied ticket NCR-10427, a $250 total approval limit, and callback number +12025550142.

#### Before the call

I'll ask for the total repair price and pickup timing. I can approve up to $250 as you requested, but I won't accept a higher amount or provide payment details.

#### Call request

```json
{
  "to": "+12025550112",
  "loop_in_user": false,
  "task": "Call Northside Camera Repair on behalf of Jordan Lee about ticket NCR-10427 for the Sony A7 IV dropped off on September 3, 2026. Introduce yourself as Jordan's personal assistant. Ask whether the estimate is ready, the total cost including parts, labor, taxes, and fees, what work is included, and the expected completion and pickup time. Jordan authorizes this repair only if the full total is at most $250. If it costs more, do not approve; ask them to hold the decision and report the quote. Do not approve extra work or provide payment-card information. If more identification is needed, do not invent it; collect the exact requirement for a callback. Navigate menus and transfers to someone handling the ticket. If voicemail is reached, leave Jordan's name, ticket number, the request for an estimate and pickup update, and the authorized callback number +12025550142; do not leave other private details. If closed or unanswered without voicemail, end and report. No loop-in is planned. Report the estimate, what was included, whether anything was approved, pickup timing, and any next step."
}
```

#### After the call, if the quote exceeded the limit

The repair quote is $310 total, so I did not approve it. They're waiting for your decision. Would you like to approve $310, ask about a cheaper repair option, or arrange pickup without the repair?

### Example: Investigate a flight change without accepting it

Jordan supplied reservation H7K2Q9 and wants to compare an earlier outbound flight. Loop-in has been chosen for verification.

#### Before the call

I'll collect the flight options, fare difference, and change rules without accepting a change. If they need a live code or your verification, ClawCall can loop you in. Don't send me a password or code; you must handle that exchange directly. Loop-in does not guarantee that recording or transcription stops.

#### Call request

```json
{
  "to": "+12025550113",
  "loop_in_user": true,
  "task": "Call Horizon Airlines support on behalf of Jordan Lee about reservation H7K2Q9. Introduce yourself as Jordan's personal assistant. The current trip is San Francisco to New York on September 12, 2026, returning September 16. Ask about moving the outbound to the evening of September 11 while keeping the return unchanged. Obtain available departure and arrival times, the total fare difference, change fees, refund or credit conditions, and the deadline to decide. Ask whether an option can be held without payment or commitment and for how long. Do not change, cancel, pay, accept credit, or approve any fee. Navigate menus and hold to the appropriate representative. If live verification, a one-time code, payment approval, or a user decision is needed, explain why Jordan is needed and use loop-in before proceeding. If Jordan cannot join, collect the exact requirement and return without changing the booking. Do not fabricate account details or ask for passwords. If closed, unanswered, or on voicemail, leave no message and report. Report the options and costs, whether any free hold was explicitly confirmed, its expiry, and all unresolved decisions."
}
```

#### After the call, if an option was offered but not held

They offered an earlier flight for an $85 fare difference. I did not change the booking, and the option is not being held. Would you like that option, or should I ask about other departures? If you choose it, I can loop you in for verification and any payment.

### Example: Resume a blocked appointment call

An earlier call reached River Dental but could not proceed without a date of birth. Jordan has now chosen to provide verification live.

#### Before the callback

The last call stopped at identity verification. I'll include that context so we don't restart the conversation, and I'll loop you in when the receptionist is ready.

#### Call request

```json
{
  "to": "+12025550111",
  "loop_in_user": true,
  "task": "Call River Dental's downtown office back on behalf of Jordan Lee. Introduce yourself as Jordan's personal assistant and say this follows an earlier attempt to confirm Jordan's September 15, 2026, 2:30 PM appointment. The receptionist previously required Jordan's date of birth before confirming the record. Jordan has chosen to verify live, not provide that detail in this briefing. Reach the receptionist, explain the prior blocker, and use loop-in when verification is requested. Do not guess identity details. If the office can confirm the appointment without live verification, ask for the time, location, and preparation requirements. If Jordan joins, Jordan can complete the confirmation directly. Do not reschedule, cancel, accept fees, or approve a different provider. If Jordan cannot join, collect the next step and leave the appointment unchanged. Handle menus and transfers, but leave no voicemail if unanswered or closed. Report whether confirmation was obtained, whether Jordan connected, and any remaining blocker."
}
```

#### Afterward, if confirmation was still blocked

The callback reached the right desk, but verification still wasn't completed, so I can't say the appointment is confirmed. The next step is your live verification. I can try again when you're available, or you can contact the office directly.

### Example: One call in a three-restaurant comparison

Jordan wants options for four people on September 10, 2026, between 6:30 and 8 PM. No restaurant has been selected.

#### Before the calls

I can check three restaurants and compare suitable times, prices, and deposit rules. I won't book anything or pay a deposit. I'll bring you the options first.

#### One independently complete call request

```json
{
  "to": "+12025550114",
  "loop_in_user": false,
  "task": "Call Cedar Kitchen's downtown location on behalf of Jordan Lee. Introduce yourself as Jordan's personal assistant. This is one call in an information-only comparison of dinner options for four people on September 10, 2026, between 6:30 and 8 PM. Confirm the location and ask which times are available, seating options, any minimum spend, deposit, and cancellation rules. Ask whether an option can be held without payment or commitment and for how long. Do not book, reserve a committed slot, pay, or accept cancellation liability. If an immediate commitment is required, decline and report the option and deadline. Do not assume another call will coordinate or cancel this one. Handle menus and transfers to reservations. If asked for unavailable private information, do not guess; report what is needed. No loop-in is planned. If closed, unanswered, or on voicemail, leave no message and report. Return comparable facts: available times, relevant costs and conditions, location, and any explicitly confirmed no-obligation hold and expiry."
}
```

#### After the comparison, using only confirmed results

Two restaurants have suitable times. Cedar Kitchen offers 6:45 with a deposit; Ember Table offers 7:30 without one. Nothing is booked. I recommend Ember Table if avoiding a deposit matters more than the earlier time. Which would you like me to book?
