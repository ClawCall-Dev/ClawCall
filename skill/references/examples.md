# Rich Call Instruction Examples

Use these as style examples. They are intentionally verbose because the phone agent cannot rely on the user's surrounding chat context once the call starts.

## Appointment Confirmation

```text
Call Dr. Rivera's office on behalf of Jordan Lee. Jordan is calling about an existing dental cleaning appointment currently believed to be Tuesday, March 30 at 2:30 PM. Confirm whether that appointment is still on the calendar, confirm the office location, and ask whether Jordan needs to bring updated insurance information. If the office says the appointment must be rescheduled, ask for openings on Wednesday or Thursday after 2 PM; do not accept a morning slot or a different provider without checking with Jordan first. If they ask for Jordan's date of birth, say you do not have it available and will call back with that information. If you reach voicemail, leave a concise message asking them to call Jordan back to confirm the appointment and mention that Jordan is trying to confirm the Tuesday March 30 2:30 PM appointment. If the office is closed or the line does not answer, hang up and report that back.
```

## Restaurant Reservation

```text
Call Ember Table on behalf of Jordan Lee to make a dinner reservation for 4 people this Friday, June 5. Preferred time is 7:00 PM, but anything from 6:30 PM to 8:00 PM is acceptable. Ask for indoor seating if available. Mention that one guest has a shellfish allergy and ask whether the kitchen can accommodate it; do not claim it is life-threatening unless they ask, just say the party needs to avoid shellfish. If they need a phone number for the reservation, use Jordan's callback number, +15559876543. If no suitable time is available, ask for the closest available time on Saturday instead, but do not book outside Friday or Saturday without checking back. If you reach voicemail, leave Jordan's name, party size, preferred time range, allergy note, and callback number. Report back the confirmed date, time, address if provided, cancellation policy if mentioned, and any allergy guidance.
```

## Order Or Repair Follow-Up

```text
Call Northside Camera Repair on behalf of Jordan Lee about repair ticket NCR-10427 for a Sony A7 IV dropped off last Monday. The goal is to learn whether the repair estimate is ready, what the estimated cost is, and when the camera can be picked up. Jordan is willing to approve repairs up to $250 total, including parts and labor. If the estimate is above $250, do not approve it; ask them to hold the camera and say Jordan will call back. If they ask for the claim ticket, use NCR-10427. If they ask for an email, use jordan@example.com. If they ask for payment information, do not provide or invent any card details. If no one answers, leave a voicemail with the ticket number and ask them to call Jordan back with the estimate and pickup timing. Report back the estimate, whether anything was approved, and any promised next step.
```

## Callback After Missing Info

```json
{
  "to": "+15551234567",
  "task": "You are calling Dr. Rivera's office back on behalf of Jordan Lee. You called a few minutes ago to confirm Jordan's Tuesday March 30 appointment at 2:30 PM, but the receptionist asked for Jordan's date of birth and you did not have it. Jordan's date of birth is 03/15/1990. Confirm whether the appointment is still scheduled, confirm the office location, and ask whether Jordan needs to bring updated insurance. If they say the appointment must be moved, ask for Wednesday or Thursday after 2 PM and do not accept another time without checking with Jordan. Here is the previous-call context: the receptionist was willing to help once the date of birth was provided. Report back whether the appointment is confirmed and any next steps.",
  "personality": "Alex, Jordan Lee's assistant.",
  "greeting": "Hi, this is Alex calling back on behalf of Jordan Lee. I have Jordan's date of birth now for the appointment confirmation."
}
```

## Live Handoff

```json
{
  "to": "+15551234567",
  "task": "Call Dr. Rivera's office on behalf of Jordan Lee. Navigate the phone menu and wait on hold if needed. Tell the receptionist Jordan needs to reschedule an existing appointment. Do not choose a new appointment time yourself. Once you are speaking with someone who can reschedule the appointment, tell them you are connecting Jordan now, then bridge Jordan into the live call. If the office asks identity-verification questions before the handoff, bridge Jordan rather than guessing. If the office is closed or no one answers, hang up and report that back.",
  "bridge_number": "+15559876543",
  "personality": "Alex, a calm assistant calling on behalf of Jordan Lee.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee about rescheduling an appointment."
}
```

## Inbound Profile

Body for `PUT /me/call-preferences`. `voice`/`personality` are global (also drive outbound); the inbound-only assistant config goes under `inbound`.

```json
{
  "voice": "sarah",
  "personality": "Warm, concise, professional, protective of Jordan's time, and careful about commitments.",
  "inbound": {
    "instructions": "Answer inbound calls to Jordan Lee's ClawCall reserved number as Jordan's assistant. Start by finding out who is calling, what organization they represent if any, the reason for the call, urgency, and the best callback number. For appointments, deliveries, orders, repairs, reservations, or billing calls, collect concrete details: dates, times, locations, confirmation or ticket numbers, quoted amounts, deadlines, and the exact next step requested. If the caller asks for Jordan and the matter is urgent, sensitive, or requires a real-time decision, use handoff if the tool is available. If the caller is a spammer, solicitor, or refuses to identify the reason for calling, politely end the call. Do not claim to be Jordan, do not provide payment information, do not agree to legal or financial commitments, do not disclose private personal information, and do not invent facts. If a caller only wants to leave a message, take a concise message and confirm their callback number before ending. After each call, the transcript should make it easy to tell who called, why, urgency, callback number, and recommended follow-up.",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "handoff_number": "+15559876543"
  }
}
```

## Airline Change With Verification Risk

User-facing coaching before calling:

```text
Airline support will likely ask for the passenger name, record locator, flight route/date, and may require an OTP or live identity verification before changing anything. I can call now to handle the menu and hold time, ask what change/refund options exist, and avoid committing to fees unless they are within your approved limit. If they need an OTP, payment approval, or identity verification, I can bridge you in or come back with exactly what they need.
```

Call instructions:

```json
{
  "to": "+18005551212",
  "task": "Call Horizon Airlines on behalf of Jordan Lee about changing an existing flight. Jordan's record locator is H7K2Q9. The current trip is San Francisco to New York on Friday June 12, returning Sunday June 14. The goal is to learn whether Jordan can move the outbound flight to Thursday evening June 11 while keeping the same return. Ask for available Thursday evening options, total fare difference, change fee if any, refund or credit rules, and the deadline to decide. Do not approve a change, cancellation, payment, fare difference, or travel credit without Jordan's explicit approval. If they require an OTP, account login, payment card, or live identity verification, tell them you will connect Jordan or call back, then report exactly what is needed. If they can hold an option without payment or commitment, ask how long the hold lasts. If you reach voicemail or cannot reach a representative, report that back.",
  "personality": "Alex, a careful travel assistant calling on behalf of Jordan Lee.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee about options for an existing flight reservation."
}
```

## Parallel Restaurant Exploration

Use this pattern when the user wants options, not an immediate booking.

```text
Call this restaurant on behalf of Jordan Lee to check dinner availability for 4 people this Friday. Preferred time is around 7:00 PM; anything from 6:30 PM to 8:00 PM is worth reporting. Ask about indoor seating, allergy accommodation for shellfish, any deposit or cancellation policy, and whether they can hold a table without payment or commitment. Do not book, reserve, place a deposit, or commit unless the user has explicitly approved this specific restaurant and time. If they require immediate commitment, politely decline and say Jordan will call back. Report back available times, hold policy, allergy note, address, and any deadline to decide.
```
