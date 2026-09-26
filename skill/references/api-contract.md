# API Contract

Use `https://api.clawcall.dev` as the base URL.

## `POST /call`

```http
POST /call
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

```json
{
  "to": "+15551234567",
  "task": "Rich Call instructions...",
  "personality": "Alex, a calm, professional assistant calling on behalf of Jordan Lee.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee.",
  "voice": "jessica",
  "loop_in_user": true
}
```

Only `to` and `task` are required. `loop_in_user` is an optional boolean that enables live handoff to the authenticated account's verified phone.

| `loop_in_user` | Destination selection |
| --- | --- |
| omitted | Preserve legacy `bridge_number`; without it, loop-in is disabled. |
| false | Disable loop-in, ignoring any `bridge_number`. |
| true | Select the verified account phone, ignoring any `bridge_number`. |

Null, strings, numbers, arrays, and objects are invalid flag values. True requires a connected account. The server prefers its eligible verified primary phone, otherwise exactly one eligible verified phone. Eligible numbers follow the existing US E.164 policy. The other call participant and ClawCall-owned numbers are prohibited. A request user ID, SMS sender, or host-saved phone cannot select the account or destination.

The server resolves the phone before outbound number allocation and carrier dispatch. Active calls retain that destination through consult and reconnect. Scheduled SMS calls resolve it at dispatch; an explicitly authorized later retry resolves it again. Legacy queued payloads without the flag keep their saved behavior and authorization IDs.

The flag enables the agent's existing loop-in tool. It does not dial the user immediately, answer for them, change consent, or alter consult deadlines.

Errors: `invalid_loop_in_user` is 400; `account_phone_unavailable` is 422 for a missing account or missing/ambiguous eligible verified phone; `account_phone_lookup_unavailable` is 503 for a timeout or provider outage; `invalid_loop_in_destination` is 400 for a prohibited destination. No outbound call is placed for these failures.

Response:

```json
{
  "call_id": "ba645d75-...",
  "status": "queued",
  "api_key": "clawcall_sk_..."
}
```

Save `api_key` if present.

## Dashboard chat call-parameter format

`POST /chat` accepts optional `call_params_format: "account-loop-in-v1"`. The declaration selects response representation only, never account identity or phone authority. Absent format retains the legacy bridge-number prompt and DTO for already-open clients. Null, unknown versions, and wrong types return HTTP 400 `unsupported_call_params_format` before invoking the model.

The final SSE `done` payload acknowledges v1 in `call_params_format` and uses `call_params.loopInUser` as a boolean. The new dashboard requires this acknowledgment before showing a confirmation action. A backend that ignores the format cannot silently accept an unsupported new call through that UI. Before modern prompt activation, the upgraded backend can project legacy drafts into the acknowledged boolean representation.

Legacy clients never receive a new account-flag-only actionable draft. If a model emits a choice the legacy DTO cannot express, the server returns `call_params: null`, `status: "gathering"`, and a refresh message. Existing historical cards in already-loaded old frontend code are unchanged. The new dashboard retires superseded unconfirmed drafts and preserves the user's explicit checkbox choice during edits; confirmed historical actions remain available.


## `GET /call/{call_id}`

```http
GET /call/{call_id}
X-Api-Key: clawcall_sk_...
```

Poll every 3 seconds until `lifecycle = "finalized"`.

Lifecycle values:

- `queued`
- `dialing`
- `answered`
- `finalized`

In-flight responses omit terminal-only fields:

```json
{
  "id": "ba645d75-...",
  "direction": "outbound",
  "handling_mode": "agent",
  "task": "...",
  "voice": "jessica",
  "personality": "Alex, Jordan's assistant.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee.",
  "numbers": {
    "to": "+15551234567",
    "from": "+15550001111",
    "bridge_from": null
  },
  "lifecycle": "dialing",
  "timestamps": {
    "queued_at": "2026-05-30T17:00:00.000Z",
    "dialing_at": "2026-05-30T17:00:01.000Z",
    "answered_at": null,
    "finalized_at": null
  }
}
```

Terminal responses include outcome, transcript, and recording fields:

```json
{
  "id": "ba645d75-...",
  "direction": "outbound",
  "handling_mode": "agent",
  "task": "...",
  "voice": "jessica",
  "personality": "Alex, Jordan's assistant.",
  "greeting": "Hi, this is Alex calling on behalf of Jordan Lee.",
  "numbers": {
    "to": "+15551234567",
    "from": "+15550001111",
    "bridge_from": null
  },
  "lifecycle": "finalized",
  "outcome": "answered",
  "outcome_detail": {
    "reason": {
      "code": "answered",
      "title": "Completed",
      "message": "The call connected successfully.",
      "retryable": false
    },
    "provider_error_code": null,
    "hangup_cause": "normal_clearing",
    "sip_hangup_cause": "200",
    "hangup_source": "callee"
  },
  "talk_seconds": 214,
  "timestamps": {
    "queued_at": "2026-05-30T17:00:00.000Z",
    "dialing_at": "2026-05-30T17:00:01.000Z",
    "answered_at": "2026-05-30T17:00:08.000Z",
    "finalized_at": "2026-05-30T17:03:42.000Z"
  },
  "transcript": [
    { "role": "assistant", "text": "Hi, this is Alex calling on behalf of Jordan Lee...", "timestamp": "2026-05-30T17:00:09.000Z" }
  ],
  "recording_url": "https://...",
  "_meta": { "balance_seconds": 847 }
}
```

`outcome` is phone-network outcome, not task success.

## `POST /call/{call_id}/hangup`

```http
POST /call/{call_id}/hangup
X-Api-Key: clawcall_sk_...
```

```json
{
  "success": true,
  "call_id": "ba645d75-...",
  "status": "failed",
  "message": "Call cancelled."
}
```

Idempotent. Already-ended calls return success.

## `GET /me/call-preferences`

```http
GET /me/call-preferences
X-Api-Key: clawcall_sk_...
```

Top-level `voice`/`personality` are global (apply to outbound AND inbound); `greeting` is the preferred outbound opener. `inbound` is `null` unless the user has an active reserved number + Unlimited Reserve Plus.

```json
{
  "configured": true,
  "voice": "jessica",
  "personality": "Warm, concise, professional.",
  "greeting": "Hi, calling on behalf of Jordan Lee.",
  "inbound": {
    "enabled": true,
    "configured": true,
    "instructions": "Answer as Jordan Lee's assistant...",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "loop_in_user": true,
    "handoff_number": null,
    "active_reserved_number": {
      "id": 12,
      "phone_number": "+15551234567",
      "display": "+1 (555) 123-4567"
    }
  }
}
```

## `PUT /me/call-preferences`

```http
PUT /me/call-preferences
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

Global fields upsert for any authed user. Include `inbound` (requires Reserve Plus + active reserved number) to set the inbound assistant. If preserving existing global fields while changing only `inbound`, first `GET /me/call-preferences` and echo current top-level values.

The supplied inbound block replaces the prior profile. Omitted `inbound` leaves it unchanged; `inbound: null` clears it. Within a replacement block, omitted `loop_in_user` restores legacy mode using the supplied `handoff_number`, or no destination if that is absent. True and false take precedence over the legacy field and clear it in storage. The server never stores the resolved account phone in preferences. Legacy rows omit the flag on read; new rows return the saved boolean.

`inbound.passthrough_numbers` accepts up to 100 US E.164 caller numbers. A supplied array replaces the list, `[]` clears it, and omission preserves it even when other inbound fields are replaced. Read current preferences and preserve the required `instructions` and `greeting`, existing loop-in or legacy handoff settings, and global settings when changing only this list. Saving a nonempty list validates the verified account destination. Matched calls bypass the assistant, recording, and transcription; history reports `handling_mode: "passthrough"`.

Saving true validates the owning account phone. Each future inbound call resolves it again using the reserved-number owner, not the original caller. Lookup failure on arrival disables loop-in for that call while preserving the existing assistant or voicemail flow. Active calls retain their initial destination. The same resolved destination supplies existing inbound terminal notifications.

Hosted MCP `update_call_settings` is a partial update, unlike REST PUT. Omitted inbound fields preserve their current values, including a saved loop-in flag; `inbound: null` clears the profile. SMS `update_inbound_profile` also preserves omitted inbound fields. Neither accepts null for the flag.

```json
{
  "voice": "sarah",
  "personality": "Warm, concise, professional.",
  "inbound": {
    "instructions": "Rich inbound profile instructions...",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "loop_in_user": true
  }
}
```

## `DELETE /me/call-preferences`

Resets the **global** voice/personality/greeting. The inbound block is cleared via `PUT { "inbound": null }`.

```http
DELETE /me/call-preferences
X-Api-Key: clawcall_sk_...
```

## `GET /me/calls?direction=inbound`

```http
GET /me/calls?direction=inbound&since=<ISO_TIMESTAMP>&limit=25
X-Api-Key: clawcall_sk_...
```

Response envelope:

```json
{
  "calls": [
    {
      "id": "ba645d75-...",
      "direction": "inbound",
      "handling_mode": "agent",
      "task": "Answer inbound calls to Jordan Lee's ClawCall reserved number...",
      "voice": "sarah",
      "personality": "Warm, concise, professional...",
      "greeting": "Hi, this is Jordan's assistant. How can I help?",
      "numbers": {
        "from": "+15559870000",
        "to": "+15551234567",
        "bridge_from": null
      },
      "lifecycle": "finalized",
      "outcome": "answered",
      "talk_seconds": 95,
      "transcript": [],
      "recording_url": null,
      "recording_available_until": null,
      "recording_expired": false
    }
  ],
  "recordingWindowMinutes": 10
}
```


## Subscription and trial balances

`GET /balance`, completed-call `_meta`, and balance response headers use the same entitlements as `GET /me` and call admission. Active and trialing subscriptions, and past-due subscriptions within the existing grace period, have unlimited calling.

For an Unlimited subscription, `GET /balance` returns:

```json
{
  "tier": "paid",
  "unlimited": true,
  "balance_seconds": null,
  "balance_minutes": null,
  "low_balance": false,
  "plan": {
    "id": "unlimited",
    "status": "active",
    "cancelAtPeriodEnd": false,
    "currentPeriodEnd": "2026-10-12T03:38:42.000Z",
    "grandfatheredUntil": null,
    "grandfathered": false
  }
}
```

Completed-call `_meta` contains `balance_seconds: null`, `unlimited: true`, and the same `plan`, without a warning or purchase action. The `X-ClawCall-Balance-Seconds` and `X-ClawCall-Balance-Minutes` headers contain the literal `unlimited` on call-start, completed-call, and balance responses. The tier remains `paid`. Clients must accept nullable JSON counters and the nonnumeric header value; do not coerce either to zero.

Legacy prepaid balances remain numeric. Signed-in trial users are reported as `tier: "free"`, using account usage rather than the request IP. Trial balance responses and completed-call metadata include `trial`, matching `GET /me`. A trial can have zero remaining seconds and still allow calls when `remainingCalls` is positive. Exhausted or ended trials report `trial.allowed: false`; completed-call warnings use `trial_exhausted`.

MCP `get_balance` keeps the `plan` / `legacy` / `trial` account view. MCP `get_call` and `place_call_and_wait` preserve Unlimited and trial metadata, while omitting purchase actions.
