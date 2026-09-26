# Errors And Limits

Always preserve returned URLs exactly. They are personalized.

## Calling Errors

| Code | What to do |
| --- | --- |
| `invalid_phone` (400) | Ask for a valid US `+1XXXXXXXXXX` number. |
| `unsupported_destination` (400) | Explain that ClawCall currently supports US phone numbers only; ask for a US number. |
| `missing_fields` (400) | Add both `to` and rich `task` Call instructions. |
| `auth_required` (401) | Send the returned sign-up/auth URL or ask for an API key. |
| `invalid_api_key` (401) | Remove/replace the saved key, or make an unauthenticated first call to get a new proto key. |
| `quota_exceeded` (429) | Send `action.url`; if `sign_in_url` is present and the user already has an account, send that instead. |
| `trial_exhausted` (402) | Send `action.url`; if `sign_in_url` is present and the user already has an account, send that instead. |
| `plan_required` (402) | Send `action.url` for plan selection. |
| `balance_depleted` (429) | Send `action.url` for plan selection. |
| `number_pool_exhausted` (503) | Wait 15 seconds and retry once silently; if it repeats, tell the user lines are busy. |
| `reserved_number_busy` (409) | Tell the user their reserved number is already handling a call; retry after it completes. |
| `dial_failed` (502) | Retry once after a few seconds. |

## Inbound Setup Errors

| Code | What to do |
| --- | --- |
| `auth_required` (401) | Explain inbound setup requires an account-linked key; use the account-link flow if a saved key exists. |
| `reserved_number_required` (402) | Tell the user they need Unlimited Reserve Plus with an active reserved number before inbound can be configured. Send `action.url` if present. |
| `inbound_plan_required` (403) | Tell the user Unlimited Reserve Plus is required for inbound calls. |
| `invalid_preferences` (400) | Fix the global `voice` (must be `jessica`, `sarah`, `chris`, or `eric`). |
| `invalid_profile` (400) | Fix missing/invalid inbound `instructions` or `greeting`. |
| `invalid_handoff_number` (400) | Ask for an external reachable handoff number that is not a ClawCall number. |

## Loop-in errors

These errors apply to outbound call setup and inbound profile saves.

| Code | What to do |
| --- | --- |
| `invalid_loop_in_user` (400) | Send true or false, not null or a string. |
| `invalid_warm_greeting` (400) | Send true for a private greeting and join question, or false to connect on callback answer. Null and strings are invalid. |
| `account_phone_unavailable` (422) | Connect the account or correct its verified primary phone. Never substitute a number from chat. |
| `account_phone_lookup_unavailable` (503) | Explain the temporary lookup failure. The user can try again shortly; no outbound call was placed. Do not ask them to reverify. |
| `invalid_loop_in_destination` (400) | Explain that the account phone cannot be the other participant or a ClawCall-owned number. |

## Outcomes

For terminal calls, prefer the server-provided `outcome_detail.reason.message` and use `outcome_detail.reason.retryable` to decide whether to offer a retry. The table below is fallback guidance for older servers.

| Outcome | Tell the user | Next step |
| --- | --- | --- |
| `answered` | Summarize task result from transcript. | Offer transcript/recording or follow-up. |
| `no_answer` | "No one picked up." | Ask before retrying unless the user preauthorized retries. |
| `busy` | "The line was busy." | Offer to retry in a moment. |
| `rejected` | "The call was declined." | Suggest retry, live handoff, or direct call if screening unknown numbers. |
| `invalid_number` | "That number does not seem valid." | Ask to verify; do not retry blindly. |
| `unreachable` | "That number appears unreachable or out of service." | Ask to verify; do not retry blindly. |
| `network_error` | Do not bother the user on first occurrence. | Retry once silently; if it repeats, explain. |
| `cancelled` | "The call was cancelled." | No action unless user wants a new call. |
| `system_error` | "The call system hit an error." | Retry once if appropriate. |
| `failed` | Explain what the response/transcript reveals. | Retry only if it looks transient. |

## Trial And Balance

New users get trial access for 30 calls and 30 minutes, whichever lasts later. A trial call counts only after it finalizes with at least 5 seconds of talk time.

Do not check balance before every call. Place the call and handle returned errors.

Balance can be returned in `_meta.balance_seconds` on some terminal call responses and by:

```http
GET /balance
X-Api-Key: clawcall_sk_...
```

Balance-aware responses can include:

- `X-ClawCall-Balance-Seconds`
- `X-ClawCall-Balance-Minutes`
- `X-ClawCall-Tier`

An entitled plan in the account balance means unlimited calling. Where second counters are exposed, Unlimited balance responses and completed-call metadata report `unlimited: true` and `balance_seconds: null`, with the current `plan` and no low-balance warning. Never treat a null balance as zero.

Trial responses include `trial.allowed`, `trial.remainingCalls`, and `trial.remainingSeconds`. Calls can remain available when seconds reach zero because the trial ends only when both allowances are exhausted. Use `trial.allowed` to interpret availability.

For metered balances, mention a returned low-balance warning briefly.
