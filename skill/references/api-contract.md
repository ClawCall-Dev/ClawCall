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
  "bridge_number": "+15559876543"
}
```

Only `to` and `task` are required. `bridge_number` is only for live handoff.

Response:

```json
{
  "call_id": "ba645d75-...",
  "status": "queued",
  "api_key": "clawcall_sk_..."
}
```

Save `api_key` if present.

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

## `GET /me/inbound-call-profile`

```http
GET /me/inbound-call-profile
X-Api-Key: clawcall_sk_...
```

```json
{
  "inbound_enabled": true,
  "active_reserved_number": {
    "id": 12,
    "phone_number": "+15551234567",
    "display": "+1 (555) 123-4567"
  },
  "configured": true,
  "profile": {
    "instructions": "Answer as Jordan Lee's assistant...",
    "voice": "jessica",
    "personality": "Warm, concise, professional.",
    "greeting": "Hi, this is Jordan's assistant. How can I help?",
    "handoff_number": "+15559876543"
  }
}
```

## `PUT /me/inbound-call-profile`

```http
PUT /me/inbound-call-profile
Content-Type: application/json
X-Api-Key: clawcall_sk_...
```

```json
{
  "instructions": "Rich inbound profile instructions...",
  "voice": "sarah",
  "personality": "Warm, concise, professional.",
  "greeting": "Hi, this is Jordan's assistant. How can I help?",
  "handoff_number": "+15559876543"
}
```

## `DELETE /me/inbound-call-profile`

```http
DELETE /me/inbound-call-profile
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
