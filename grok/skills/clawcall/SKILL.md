---
name: clawcall
description: >-
  Use when the user wants Grok to place a US phone call, call a business, handle
  hold or phone menus, confirm/reschedule/cancel/book/follow up, reach a real
  person, leave voicemail, connect the user into a live call, or configure inbound
  answering and passthrough via ClawCall.
homepage: https://clawcall.dev
---

# ClawCall

ClawCall places real US phone calls for the signed-in user through the hosted MCP
at `https://api.clawcall.dev/mcp` (OAuth 2.1).

## Before every call

1. Call `get_calling_guide` with topic `outbound` (required every time).
2. When writing Call instructions (`task`), also read topic `examples`.
3. Confirm consequential goals and decision boundaries with the user before
   placing a call that can book, buy, cancel, pay, or otherwise commit.

## Place a call

- Use `place_call` with US E.164 `to` (`+1` + 10 digits) and complete `task`
  Call instructions (who you represent, goal, known facts, questions,
  alternatives, what not to promise, voicemail behavior, what to report).
- Returns `call_id` immediately. Poll `get_call` until `lifecycle` is
  `finalized`, then `get_call_transcript` before reporting whether the user's
  goal succeeded.
- `outcome` is the phone network result, not task success.
- Use `loop_in_user: true` for live handoff to the signed-in account's verified
  phone, and put the handoff trigger in `task`. `bridge_number` is legacy.
- Do not run parallel calls that can book, buy, cancel, or commit.

## Guides

`get_calling_guide` topics: `outbound`, `examples`, `errors`, `profile`,
`inbound`, `privacy`.

## Inbound settings

- Read guide topic `inbound` and `get_call_settings` before updating settings.
- Use `update_call_settings` with an inbound-only patch. Change global voice or
  personality in a separate call. Read settings again to verify the result.
- `inbound.passthrough_numbers` lists callers who ring the verified account phone
  directly with their original caller ID, without the assistant, recording, or
  conversation transcript. It works independently of loop-in.
- The list supports up to 100 unique US E.164 numbers. Read the saved list before
  adding or removing entries and send the complete desired list. Omission
  preserves it; `[]` clears it.

## Notes

- Hosted MCP uses OAuth — never ask for or invent an API key.
- Preserve any `action.url` on errors verbatim.
- US numbers only.
