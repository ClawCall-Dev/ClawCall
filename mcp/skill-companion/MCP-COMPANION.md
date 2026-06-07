# ClawCall MCP Companion

This note accompanies the ClawCall skill (`skill/SKILL.md`). It explains the
`clawcall-mcp` server — a stdio MCP wrapper over the same public ClawCall REST
contract the skill documents — and, critically, how the MCP server and the skill
**share one identity** so that running both does not fork your account, key, or
call history.

Copy this file into `skill/references/` if you want it to travel with the skill.

> All workflow assertions below mirror the centralized prose in the MCP package
> (`src/config/metadata.ts`: `WORKFLOW`, `GREETING_CAVEAT`, `GATE_CAVEAT`,
> `CAMPAIGN_NOTE`). The tool descriptions are the single source of truth — this
> note must not diverge from them.

---

## 1. Install / register

Add the server to your MCP client config. The `env` block is **optional** — the
server self-provisions a proto-key on the first call if no key is supplied.

```json
{ "mcpServers": { "clawcall": { "command": "npx", "args": ["-y", "clawcall-mcp"], "env": { "CLAWCALL_API_KEY": "optional", "CLAWCALL_BASE_URL": "https://api.clawcall.dev" } } } }
```

Claude Code one-liner:

```
claude mcp add clawcall -- npx -y clawcall-mcp
```

`CLAWCALL_BASE_URL` defaults to `https://api.clawcall.dev`. `CLAWCALL_API_KEY`
is an operator/CI override only — see §2.

---

## 2. Identity-sharing contract (load-bearing)

The MCP server reads and writes the **same** credential file the skill uses:

```
~/.config/clawcall/key.json   →   { "api_key": "clawcall_sk_...", "user_phone_number": "+1..." }
```

(Honors `XDG_CONFIG_HOME` when set.) Because both the skill-agent and the
MCP-agent resolve their key from this one file, they operate as **one
identity** — the same proto-key, the same trial quota, the same call history,
the same balance. Running the skill and the MCP server together does **not**
fork identity.

Custody rules the MCP server follows:

- On the first unauthenticated `place_call`, the auto-issued proto-key is
  captured **on receipt** (from both the JSON `api_key` field and the
  `X-ClawCall-Api-Key` response header) and persisted — merging to preserve an
  existing `user_phone_number` — **before** any poll loop runs, so a killed
  handler never loses the single-surfaced secret.
- `CLAWCALL_API_KEY` in `env` **shadows** the file (operator override). When set,
  the file is not consulted for reads.
- The key is **never** a tool-call argument (it would leak into conversation
  history and logs). The only way to set a key via a tool is the non-echoing
  `set_api_key`.
- A genuine `401 invalid_api_key` envelope clears the saved `api_key` (preserving
  `user_phone_number`) so the next call re-provisions. Network/5xx errors never
  delete the key.

---

## 3. The load-bearing workflow (run it once, internalize it)

```
place_call  →  poll get_call every 3s until lifecycle === "finalized"
            →  outcome is the PHONE-NETWORK result, NOT task success
            →  read the transcript (get_call_transcript)
            →  judge the transcript against the task
```

`outcome` (`answered` / `no_answer` / `busy` / `rejected` / ...) tells you only
what the phone network did. An `answered` call can still fail the task. You
**must** read the transcript and decide whether the goal was met, then report
back or call again.

`get_call` is intentionally context-cheap (it returns a short transcript tail,
not the full array) so you can poll it every 3 seconds. Pull the full turn-by-turn
transcript with `get_call_transcript` once the call is finalized.

---

## 4. Granularity: which tool to reach for

- **Single foreground call, want the result in one shot:**
  `place_call_and_wait`. It internally polls `get_call` at 3s until finalized,
  with a hard cap (~180s, ceiling 240s). On cap it **degrades to the
  non-blocking contract** — returns `{ still_running: true, call_id, ... }` and
  tells you to keep polling `get_call` with that id. It is named (not a `wait`
  flag) so the timeout tradeoff is visible when you pick the tool.

- **Campaigns — 3–4 parallel, interchangeable, info-only calls** (quotes,
  availability, inventory, policy comparison): use `place_call` to fan out, then
  `get_call` to poll each. **Never** use the blocking `place_call_and_wait` for
  campaigns. Only parallelize calls that gather information — never calls that
  book, buy, cancel, or commit, unless the user gave explicit safe boundaries and
  duplicate commitments are impossible.

---

## 5. Two hard caveats (verbatim, do not soften)

- **`greeting` does NOT set the agent's first spoken line.** The `greeting`
  parameter is outbound-opener context only. The agent's actual opening line is
  hardcoded server-side to a recording disclosure. Do not promise a user that
  `greeting` controls what the agent says first.

- **402 is PERMANENT gating, not retryable.** `trial_exhausted`,
  `plan_required`, and `reserved_number_required` (all HTTP 402) are permanent
  gates — do **not** retry them as if transient. Surface the
  `action.url` / `action.sign_in_url` from the error envelope **verbatim**
  (they are personalized and embed the proto-key) so the human can act.

---

## 6. Trial limits — never hardcode

Do **not** hardcode trial limits in prose, prompts, or logic. Read them from the
live `quota` object in the `trial_exhausted` error envelope:

```
{ "error": { "code": "trial_exhausted",
             "quota": { "used_seconds", "remaining_seconds", "limit_seconds", "tier" },
             "action": { "url", "sign_in_url" } } }
```

The server's trial constants have changed before — any remembered number drifts
out of date. Always quote the live `quota` fields, never a hardcoded limit.

---

## 7. Account linking

`get_account_link_url` builds the browser sign-in link **client-side** from the
**saved** key — it never mints a new key:

```
https://clawcall.dev/sign-in?token=<saved_key>
```

(See `SKILL.md:71`.) Opening that URL and signing up/in attaches this agent's
key, calls, balance, and history to a ClawCall account. The server's
`sign_in_url` inside quota-exhaustion error envelopes is a **separate** surface —
do not confuse it with the linking flow.

---

## 8. v1 scope

v1 of `clawcall-mcp` is **outbound-only**. The inbound / reserved-number /
call-preferences cluster (`/me/call-preferences`, reserved-number provisioning,
inbound-history polling) is deferred to v2. Use the skill directly for those
flows until v2 ships.
