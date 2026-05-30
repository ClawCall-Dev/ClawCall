# Errors And Limits

Always preserve returned URLs exactly. They are personalized.

## Calling Errors

| Code | What to do |
| --- | --- |
| `invalid_phone` (400) | Ask for a valid US `+1XXXXXXXXXX` number. |
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

## Outcomes

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

New users get trial access for 10 calls and 10 minutes, whichever lasts later. A trial call counts only after it finalizes with at least 5 seconds of talk time.

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

When balance drops below 120 seconds, mention it briefly.
