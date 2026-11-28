# ClawCall plugin for Hermes Agent

ClawCall gives Hermes Agent real US +1 phone calling without a Twilio, Bland, or Vapi account. It exposes nine `clawcall_*` tools over ClawCall's REST API (`https://api.clawcall.dev`, using `CLAWCALL_API_KEY` read through Hermes's `agent.secret_scope.get_secret`) or remote MCP (`https://api.clawcall.dev/mcp`, OAuth 2.1 with PKCE).

Free trial: 30 calls or 30 minutes, whichever comes first, no credit card required. Paid plans: $8.99/mo Unlimited (outbound calls), $14.99/mo Unlimited Reserve (private caller-ID number), $18.99/mo Unlimited Reserve Plus (adds inbound answering on that number). Fair use applies; no bulk or automated outreach. US +1 numbers only. 25 languages. One outbound call at a time per account. No SMS.

## Safety and privacy design

- **Hermes approval gate (`pre_tool_call`):** `clawcall_place_call`, `clawcall_hangup_call`, and `clawcall_update_call_settings` return Hermes `{"action": "approve", ...}` directives showing every detail of the call (number, recipient, goal, authority, facts it may share, questions, calling line, hand-off contacts and voicemail message) with a `rule_key` that hashes the whole request, so approve-for-session never covers a call that differs in any field, and fail closed when nobody can approve. `allowed_numbers` limits both the destination and every hand-off contact, refuses the call if any entry is not a valid US +1 number, and is required for unattended scheduled (cron) runs, which cannot dial outside it. Read tools (`clawcall_get_balance`, `clawcall_get_call`, `clawcall_get_call_transcript`, `clawcall_list_calls`, `clawcall_get_recording`, `clawcall_get_call_settings`) run without write approval.
- **Strict US +1, emergency, and premium-rate guard:** `validate_us_phone_number` runs locally before any request and accepts only valid US +1 NANP numbers (`+1XXXXXXXXXX`). It refuses international country codes (`+44`, `+91`, etc.), non-US +1 regions (Canada and Caribbean NANP area codes), invalid area/exchange codes (`+10XX`, `+11XX`), emergency or N11 service numbers (`911`, `988`, `211`-`811`, `+1911`), and premium-rate numbers (`900`, `976`).
- **Scoped secret access (Hermes Rule 11):** Secrets are read through `agent.secret_scope.get_secret` rather than bare `os.environ` or local credential files, keeping multi-profile Hermes setups isolated.
- **Zero local transcript storage:** The plugin never writes transcripts, call recordings, phone numbers, or keys to local files, caches, or logs. Captured transcript evidence is returned directly in tool output only. On ClawCall's servers, recordings are deleted after 10 minutes and transcripts after 7 days.
- **Zero external runtime dependencies:** Built purely on the Python 3 standard library (`urllib.request`, `json`, `re`, `hashlib`, `dataclasses`). No shell commands, child processes, telemetry, or self-updater.

## Third-party service disclosure

ClawCall is a third-party calling service at `https://clawcall.dev`. When enabled, call requests, destination numbers, and call settings are sent over HTTPS to `https://api.clawcall.dev` (or `https://api.clawcall.dev/mcp`). Write actions go through Hermes's approval gate, non-US/emergency/premium-rate numbers are refused before dialing, unattended cron runs fail closed outside `allowed_numbers`, and no transcripts or recordings are saved locally. ClawCall deletes recordings after 10 minutes and transcripts after 7 days, makes no HIPAA, PCI, or SOC 2 compliance claims, and identifies itself as an AI when asked on a call.

## Remote MCP instead of the plugin

To use ClawCall's hosted MCP server without installing this plugin, add it to `~/.hermes/config.yaml` with `trust: untrusted`, so Hermes asks before every call, hang-up and settings change:

```yaml
mcp_servers:
  clawcall:
    url: "https://api.clawcall.dev/mcp"
    auth: oauth
    trust: untrusted
```

Then run `hermes mcp login clawcall` once and start a new session.

## Local setup and testing

Run the full offline unit test suite (zero network calls, standard library only):

```bash
python3 -m unittest discover -s hermes/test -v
```

Validate with the official Hermes catalog admission tool before submitting a PR to `NousResearch/hermes-agent`:

```bash
hermes plugins validate hermes --install-deps
```

See [LISTING.md](./LISTING.md) for the complete Hermes Marketplace listing copy and submission steps for `NousResearch/hermes-agent/plugin-catalog/clawcall.yaml`.
