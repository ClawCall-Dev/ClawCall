---
name: clawcall
description: Place and manage real US +1 phone calls from Hermes Agent via ClawCall with approval gating, US-only and emergency/premium-rate number guards, and zero local transcript storage. Not for SMS or non-US calls.
version: 1.0.0
homepage: https://clawcall.dev
license: MIT
metadata: {"hermes":{"plugin":"clawcall","mcp_url":"https://api.clawcall.dev/mcp","rest_base_url":"https://api.clawcall.dev","auth":"oauth-or-api-key","scopes":["calls:read","calls:write"],"approval_required_tools":["clawcall_place_call","clawcall_hangup_call","clawcall_update_call_settings"],"local_transcript_storage":false}}
---

# ClawCall for Hermes Agent

ClawCall gives Hermes Agent a real US phone line without a Twilio, Bland, or Vapi account.

## Connection

- **Hermes plugin tools:** Install from the Hermes Marketplace (`hermes plugins install clawcall`) and set `CLAWCALL_API_KEY` from `https://clawcall.dev/dashboard/keys` (read via Hermes's `agent.secret_scope.get_secret`).
- **Remote MCP (no API key):** Add `https://api.clawcall.dev/mcp` under `mcp_servers.clawcall` with `auth: oauth` and `trust: untrusted` in `~/.hermes/config.yaml` (so Hermes asks before every call, hang-up and settings change) and run `hermes mcp login clawcall` (OAuth 2.1 with PKCE and Dynamic Client Registration; scopes `calls:read` and `calls:write`).

## Tools

Read-only tools (`calls:read`, no write approval required):

- `clawcall_get_balance`: check plan status and remaining trial allowance without placing a call.
- `clawcall_get_call`: check lifecycle, phone-network outcome, and latest captured transcript lines when present.
- `clawcall_get_call_transcript`: read captured transcript evidence directly in tool output (never saved to local disk).
- `clawcall_list_calls`: list recent outbound or inbound calls.
- `clawcall_get_recording`: get a temporary playable recording URL when available (recordings expire after 10 minutes).
- `clawcall_get_call_settings`: read saved voice, warm greeting, and inbound answering settings.

Write tools (`calls:write`, routed through Hermes's `pre_tool_call` approval gate):

- `clawcall_place_call`: start one real US +1 outbound call with structured fields (`to`, `recipient`, `on_behalf_of`, `goal`, `authority`).
- `clawcall_hangup_call`: hang up an active or queued call.
- `clawcall_update_call_settings`: update voice, warm greeting, or inbound answering settings.

## Safe test without placing a call

Ask Hermes:

> Check my ClawCall plan and remaining trial allowance. Do not place a call.

## Safety and limits

- **US +1 numbers only:** non-US international numbers, Canadian/Caribbean +1 regions, emergency/N11 codes (`911`, `988`, `211`-`811`), and premium-rate numbers (`900`, `976`) are refused locally before any network call.
- **Approval gate and cron safety:** every call, hangup, and setting change triggers Hermes's approval prompt with the full brief and fails closed when unattended. Scheduled runs cannot dial numbers outside `allowed_numbers`.
- **Zero local transcript storage:** nothing is written to local disk. On ClawCall's servers, recordings are deleted after 10 minutes and transcripts after 7 days.
- **Plan and product boundaries:** Free trial is 30 calls or 30 minutes, whichever comes first, no card. Paid plans are $8.99/mo Unlimited, $14.99/mo Unlimited Reserve (private caller-ID number), and $18.99/mo Unlimited Reserve Plus (inbound answering). Fair use, no bulk or automated outreach, one call at a time, 25 languages, no SMS, no HIPAA/PCI/SOC 2 claims. Says it is an AI when asked.
