# @clawcall/mcp

MCP server wrapping the ClawCall REST API for AI-powered US phone calls.

ClawCall places real outbound phone calls in the US (+1 only). This package is a stdio
MCP server that exposes the ClawCall REST contract as tools any MCP host (Claude Code,
Claude Desktop, Cursor, Windsurf) can call. It is a stateless client over the public API
at `https://api.clawcall.dev` — it imports nothing from the ClawCall server.

## Install / register

Add the server to your MCP client config:

```json
{ "mcpServers": { "clawcall": { "command": "npx", "args": ["-y", "@clawcall/mcp"], "env": { "CLAWCALL_API_KEY": "optional", "CLAWCALL_BASE_URL": "https://api.clawcall.dev" } } } }
```

Or, for Claude Code, the one-liner:

```
claude mcp add clawcall -- npx -y @clawcall/mcp
```

The `env` block is **optional**. The ClawCall server self-provisions an API key on the
first call: an anonymous `place_call` auto-issues a proto-key, which this server captures
and persists. You do not need to set `CLAWCALL_API_KEY` to get started.

## Identity sharing

This MCP server reads and writes the **same** `~/.config/clawcall/key.json` file
(`{ "api_key": "...", "user_phone_number": "..." }`) that the ClawCall agent skill uses.
Running both the skill and this MCP server does **not** fork your identity — they share one
key, one trial quota, one call history, and one balance.

If `CLAWCALL_API_KEY` is set in the environment, it **shadows** the file (an operator /
CI override). The saved file is otherwise the source of truth, and the proto-key issued on
your first call is persisted there automatically (preserving any saved `user_phone_number`).

## The workflow

A call runs for several minutes. The load-bearing loop is:

1. `place_call` — returns a `call_id` immediately. Does **not** block.
2. Poll `get_call` every **3 seconds** until `lifecycle === "finalized"`.
3. `outcome` is the **phone-network result** (answered / no_answer / busy / …), **NOT**
   task success. An answered call can still fail the task.
4. Read the transcript with `get_call_transcript` and judge it against the task you set.

## Choosing a tool

- **`place_call_and_wait`** is the single-foreground-call shortcut: it places the call and
  internally polls until finalized or a hard cap (~180 s, ceiling 240 s). On the cap it
  degrades to the non-blocking contract — it returns `{ still_running: true, call_id, … }`
  and you continue with `get_call`. Use it when you want one call's result in one shot.
- **Campaigns** — 3–4 parallel, interchangeable, info-gathering-only calls (quotes,
  availability, inventory, policy comparison) — use `place_call` + `get_call` fan-out.
  **Never** use the blocking tool for campaigns. Never parallelize calls that
  book / buy / cancel / commit.

## Caveats

- **`greeting` does NOT set the agent's first spoken line.** It is outbound-opener context
  only. The agent's actual opening line is a hardcoded recording disclosure on the server.
- **402 errors are PERMANENT gating, not retryable.** `trial_exhausted`, `plan_required`,
  and `reserved_number_required` mean a human must act. Forward the returned `action.url` /
  `sign_in_url` **verbatim** (they are personalized and embed your proto-key). Do not retry.

Trial limits are read from the live `quota` object in the error envelope — they are
**never** hardcoded in this package, so the displayed numbers always match the server.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `CLAWCALL_BASE_URL` | `https://api.clawcall.dev` | ClawCall REST API base URL. |
| `CLAWCALL_FRONTEND_URL` | `https://clawcall.dev` | Frontend base used to build sign-in / account-link URLs. |
| `CLAWCALL_API_KEY` | (unset) | Optional operator override. Shadows the saved key file. |
| `CLAWCALL_WAIT_DEFAULT` | `180` | Default cap (seconds) for `place_call_and_wait`. |
| `CLAWCALL_WAIT_CEILING` | `240` | Maximum allowed cap (seconds) for `place_call_and_wait`. |

## More

- [`skill-companion/MCP-COMPANION.md`](./skill-companion/MCP-COMPANION.md) — companion note
  for the ClawCall skill describing how the two share identity and workflow.
- [`../skill/SKILL.md`](../skill/SKILL.md) — the ClawCall agent skill (the procedural
  layer; this MCP server is the connectivity layer over the same REST API).
