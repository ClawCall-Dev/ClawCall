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
at `https://api.clawcall.dev/mcp` (OAuth 2.1). The server owns the request format
and workflows, so read its guide instead of relying on this file for field details.

## Before every call

1. Call `get_calling_guide` with `topic: "outbound"` and `call_format: "structured"`.
   Read topic `examples` too when the request is unusual.
2. The phone agent knows only what the request contains. Put every detail the
   goal depends on into `facts` and `questions`.
3. Confirm consequential goals and limits with the user before placing a call that
   can book, buy, cancel, pay, or otherwise commit.

## Place and follow a call

- `place_call` takes `to` (US E.164, `+1` and 10 digits), `recipient`,
  `on_behalf_of`, `goal`, and `authority`. An empty `authority.allow` means ask
  and relay only; boundaries go in `authority.limits`.
- Include `handoff` on most calls, listing in `handoff.when` what only the user
  can handle (one-time codes, payments, identity checks). The agent then rings
  the account's loop-in contacts or verified phone.
- `place_call` returns a `call_id`. Call `track_call` until the event is `ended`,
  then read `get_call_transcript` before saying whether the goal succeeded.
  `place_call_and_track` places the call and returns its first event.
- With `delegation: "poll"`, the phone agent can ask you questions during the
  call; answer each `request` event by calling `track_call` with `reply`.
- `outcome` is the phone network result, not task success.
- Do not run parallel calls that can book, buy, cancel, or commit.

## Settings

- Read `get_call_settings` before `update_call_settings`, and read it again after
  to verify. Change voice or personality and inbound settings in separate calls.
- Top-level `warm_greeting` (default true) briefs the user privately before a
  loop-in connects them; false connects on answer. It does not enable loop-in and
  does not stop recording or transcription.
- Inbound settings need Unlimited Reserve Plus with a reserved number; read guide
  topic `inbound` first. `inbound.passthrough_numbers` replaces the whole list.

## Guides

`get_calling_guide` topics: `outbound`, `examples`, `errors`, `profile`,
`inbound`, `privacy`, `webhooks`.

## Notes

- Hosted MCP uses OAuth. Never ask for or invent an API key.
- Preserve any `action.url` in errors verbatim.
- US numbers only.
