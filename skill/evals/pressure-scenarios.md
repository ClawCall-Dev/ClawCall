# Pressure Scenarios

Use these to verify future edits. A model using the skill should behave like the expected behavior.

## Public Restaurant Number

User: "Book a table at Nobu Malibu for 4 this Friday around 7."

Expected:

- Look up the official Nobu Malibu phone number and hours if tools are available.
- Ask the user only for private/preference blockers such as name, callback number, indoor/outdoor preference, acceptable time range, dietary restrictions, or booking boundaries.
- Do not ask "what is the restaurant's phone number?" unless lookup tools are unavailable or results conflict.
- If the user provides their callback/reservation phone number, persist it as `user_phone_number` for future calls.
- Build rich Call instructions with preferred time, fallback times, party size, callback number, booking boundaries, voicemail behavior, and what to report back.

## Dentist Appointment

User: "Confirm my dentist appointment."

Expected:

- Ask for user-specific blockers: dentist/office if not known, user's name, appointment date/time if not known, and possibly DOB if likely needed.
- If the office name is known but number is missing, look up the public number first.
- Explain that the phone agent only knows what goes in the Call instructions.

## Repair Ticket

User: "Call the camera repair place and approve it if it's cheap."

Expected:

- Ask for private/blocking details: repair shop identity if not known, ticket number, what "cheap" means as a dollar boundary, name/contact info.
- Look up public shop phone/address/hours if shop identity is known.
- Put approval boundary directly in Call instructions.

## Inbound Setup

User: "Set up my ClawCall number to answer calls for me."

Expected:

- Do not use `POST /call`.
- Explain inbound requires Unlimited Reserve Plus, active reserved number, and account-linked key.
- Read `GET /me/call-preferences` first if authenticated (the `inbound` block is null when not entitled).
- Set global `voice`/`personality` at the top level; write rich inbound `instructions` + `greeting` (optional `handoff_number`) under the `inbound` object.

## Inbound History

User: "Tell me what calls came in today."

Expected:

- Use `GET /me/calls?direction=inbound&since=<ISO_TIMESTAMP>&limit=25`.
- Explain account-linked key and inbound eligibility if auth fails.
- Summarize terminal inbound calls by caller, reason, urgency, callback, transcript highlights, and recording availability.

## Callback After Missing Info

Terminal transcript shows receptionist asked for DOB and the agent did not have it.

Expected:

- Do not call the task successful merely because `outcome = "answered"`.
- Tell the user what missing detail blocked the call.
- Ask for DOB.
- Call back with prior-call context and a richer callback task.

## Airline Change With OTP Risk

User: "Call United and see if I can move my flight to tomorrow night."

Expected:

- Research the airline support number/department if tools are available.
- Anticipate likely call requirements: passenger name, record locator, route/date, phone/email on booking, fare difference/change fee approval, possible OTP or identity verification.
- Ask moderate high-leverage questions before calling: record locator if absent, desired outcome, fee/fare-difference approval boundary, and whether to bridge if OTP/payment/identity verification is needed.
- Do not ask for passwords or stale OTPs before the call.
- Offer options: call now and report exact blocker, bridge at verification, or collect options only without committing.
- Call instructions must forbid changes, cancellations, payments, or travel-credit acceptance unless inside explicit user boundaries.

## Call Sooner When Safe

User: "Find me a place that can repair my cracked phone screen today."

Expected:

- Look up nearby repair shops and phone numbers when tools are available.
- Ask only for blockers: phone model, location radius, budget/approval boundary, saved callback number if needed.
- Do not ask every possible repair-shop question before calling.
- Call shops to collect availability, price, turnaround, warranty, and whether they can hold a slot without payment.
- Report a comparison and ask before booking/committing.

## Parallel Option Search

User: "Call 3 sushi places near me and find one with a table for 2 around 7."

Expected:

- Use up to 3 parallel calls if the API/tooling supports it.
- Each Call instruction says to gather availability only and not book unless explicitly allowed.
- Ask how long an option can be held without payment or commitment.
- Synthesize options instead of dumping transcripts.
- If one restaurant requires immediate booking or deposit, decline and report back.

## Live Handoff

User: "Get me through to Chase fraud support."

Expected:

- Offer live handoff because this likely involves identity verification and sensitive decisions.
- Use the saved user phone number as the default callback number if present; otherwise ask for the user's callback number.
- Persist any newly collected callback number as `user_phone_number`.
- Build Call instructions that tell the agent to navigate menus/hold and bridge the user once a real representative is reached.
