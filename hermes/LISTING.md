# ClawCall (Hermes Agent Marketplace listing)

Updated 2026-11-26. Facts checked against `clawcall.dev/pricing`, `clawcall.dev/facts`, and `NousResearch/hermes-agent/plugin-catalog/README.md`.

## Marketplace card summary

**Name:** `clawcall`  
**Title:** `ClawCall`  
**Category:** `voice`  
**Version:** `"1.0.0"`  
**Requires Hermes:** `">=0.23.0"`

## What ClawCall does

Hermes Agent has no built-in phone line. The ClawCall plugin connects Hermes to ClawCall (`https://api.clawcall.dev` and remote MCP `https://api.clawcall.dev/mcp`) so Hermes can place real US +1 phone calls on your behalf, navigate phone menus, wait on hold, leave voicemail when instructed, ring you in when a decision is yours, and report back with the phone-network outcome and captured transcript evidence when present.

Key facts:

- **Countries:** US +1 numbers only (does not call Canada or other countries).
- **Languages:** 25 languages supported (`ar, bn, de, en, es, fr, he, hi, id, it, ja, kn, ko, mr, ms, nl, pl, pt, ta, te, th, tl, tr, vi, zh`).
- **Pricing:** Free trial of 30 calls or 30 minutes, whichever comes first, with no credit card required. Paid flat monthly plans are $8.99/mo for Unlimited (outbound calls from ClawCall's shared caller ID), $14.99/mo for Unlimited Reserve (adds a private caller-ID number; $149.90/yr), and $18.99/mo for Unlimited Reserve Plus (adds inbound answering on that reserved number; $189.90/yr).
- **Fair use and limits:** Fair use applies; no bulk or automated outreach. One outbound call at a time per account. No SMS.
- **No carrier setup:** You do not need your own Twilio, Bland, or Vapi account.

## Full third-party service and safety disclosure

ClawCall is a third-party telephony service operated at `https://clawcall.dev`. Installing and authorizing this plugin sends destination phone numbers, call instructions, and call settings over HTTPS only to `api.clawcall.dev` (`https://api.clawcall.dev` with `CLAWCALL_API_KEY`, or `https://api.clawcall.dev/mcp` via OAuth 2.1 with PKCE). Secrets are read through Hermes's `agent.secret_scope.get_secret` rather than bare `os.environ` or credential files. `clawcall_place_call`, `clawcall_hangup_call`, and `clawcall_update_call_settings` go through Hermes's approval gate via a `pre_tool_call` hook showing the full destination, recipient, goal, and authority with a per-content `rule_key`, failing closed when nobody can approve. Unattended cron runs refuse numbers outside `allowed_numbers`. Non-US, emergency/N11 (`911`, `988`, `211`-`811`), and premium-rate (`900`, `976`) numbers are refused locally before any network request. This plugin stores no transcripts, recordings, or phone logs locally on disk; captured transcript evidence is returned directly in tool output when present. On ClawCall's servers, recordings are deleted after 10 minutes and transcripts after 7 days. ClawCall makes no HIPAA, PCI, or SOC 2 compliance claims, and its voice agent says it is an AI when asked. Zero third-party Python dependencies; no shell commands, child processes, telemetry, or self-updater.

## Capabilities

- **Read tools (`calls:read`, no write approval required):** `clawcall_get_balance`, `clawcall_get_call`, `clawcall_get_call_transcript`, `clawcall_list_calls`, `clawcall_get_recording`, `clawcall_get_call_settings`
- **Write tools (`calls:write`, approval-gated via `pre_tool_call`):** `clawcall_place_call`, `clawcall_hangup_call`, `clawcall_update_call_settings`
- **Hook:** `pre_tool_call`
- **Bundled skill:** `skills/clawcall/SKILL.md` (registered via `ctx.register_skill`)

## Publishing steps for `NousResearch/hermes-agent`

1. **Publish `plugins/hermes-clawcall` to a public repository** (`https://github.com/ClawCall-Dev/ClawCall` or a dedicated `https://github.com/ClawCall-Dev/clawcall-for-hermes`) and record the exact 40-character commit SHA (`git rev-parse HEAD`).
2. **Validate locally against the exact catalog CI check:**
   ```bash
   hermes plugins validate /path/to/plugin --install-deps
   ```
3. **Open a PR to `NousResearch/hermes-agent`:**
   - Copy `plugin-catalog-entry.yaml` to `plugin-catalog/clawcall.yaml`.
   - Set `repo`, `subdir` (if monorepo, or omit/empty if standalone repo), and `sha` (exact 40-character lowercase hex SHA).
   - Keep `tier: community` (maintainers set `verified` during review if applicable).
   - Include the disclosure paragraph above in the PR description.
4. **Verify after merge:** Confirm `https://hermes-agent.nousresearch.com/marketplace/clawcall` renders and test `hermes plugins install clawcall`.
