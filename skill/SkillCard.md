# Skill Card

## Description

ClawCall lets an AI agent place real US phone calls — a voice agent dials, navigates phone trees, handles hold time, optionally bridges the user into a live call, and returns the transcript, outcome, and recording link. The skill also helps configure reusable voice/personality preferences and inbound reserved-number answering profiles.

This skill is ready for commercial and non-commercial use.

## Owner

ClawCall (https://clawcall.dev) — support@clawcall.dev

## License/Terms of Use

Proprietary — governed by the ClawCall Terms of Service at https://clawcall.dev/terms. API usage is metered and billed per the user's ClawCall account.

## Use Case

End users delegating routine phone work to an AI coding agent or assistant: calling businesses to book, confirm, reschedule, cancel, or check order/appointment status; handling phone menus and hold time; comparing options across vendors; receiving live handoff to a real person; configuring reusable ClawCall voice/personality preferences; or configuring an inbound reserved number to answer incoming calls.

## Deployment Geography for Use

US only. The skill validates `+1` E.164 numbers and refuses to dial international destinations. Callers and reserved numbers must be US-based.

## Known Risks and Mitigations

Risk: The voice agent may commit to a booking, cancellation, payment, or other binding action on the user's behalf based only on what's in the call instructions.
Mitigation: Call instructions must explicitly state decision boundaries and what not to agree to. For sensitive or negotiable calls, the skill offers live handoff via `bridge_number` so the user joins before any commitment.

Risk: A phone agent could be asked to provide private user information (DOB, account numbers, OTPs, payment details) it does not have or should not disclose.
Mitigation: The skill instructs agents to anticipate verification points up front, to refuse to fabricate identity details, and to bridge the user in for live verification rather than guess.

Risk: Outbound calls reach the wrong business, location, or department when a public lookup is ambiguous.
Mitigation: The skill requires the agent to confirm the number when there are multiple plausible locations, conflicting listings, or low-confidence lookups, and to surface the number called in the post-call report.

Risk: Calls placed outside the recipient's business hours waste the user's trial/minute budget and may annoy recipients.
Mitigation: The skill instructs agents to check local hours and ask the user before dialing outside ~8 AM–6 PM local or on weekends.

Risk: The voice agent could misrepresent itself as a human, or place a recorded call without disclosing the recording.
Mitigation: The voice agent's system prompt hard-bakes two behaviors: it admits to being an AI when asked, and it states upfront that the call is being recorded.

## References

- Agent Skill source: [`SKILL.md`](SKILL.md)
- API contract: [`references/api-contract.md`](references/api-contract.md)
- Examples: [`references/examples.md`](references/examples.md)
- Errors and limits: [`references/errors-and-limits.md`](references/errors-and-limits.md)
- Inbound reserved numbers: [`references/inbound-reserved-numbers.md`](references/inbound-reserved-numbers.md)
- Pressure-test evals: [`evals/pressure-scenarios.md`](evals/pressure-scenarios.md)
- Product site: https://clawcall.dev
- Agent Skills open specification: https://agentskills.io/specification

## Skill Output

Output type(s): API calls (HTTPS to `https://api.clawcall.dev`), file writes (API key persisted to `~/.config/clawcall/key.json`), and structured call results returned to the agent.

Output format: JSON over HTTPS. Terminal call responses include `lifecycle`, `outcome`, `talk_seconds`, `transcript` (JSON array of turns), and `recording_url` when available.

Output parameters: `call_id` (UUID), `lifecycle` ∈ {`queued`, `dialing`, `answered`, `finalized`}, `outcome` (10-value phone-network enum — see the API contract reference).

Other properties: Calls are billed against the user's ClawCall balance or trial allotment (10 calls / 10 minutes, whichever lasts later). Recordings are retained per the ClawCall Terms of Service. The agent should treat saved API keys as credentials.

## Skill Version

1.0.0 — published at https://github.com/ClawCall-Dev/ClawCall. No detached signature is currently published.

## Ethical Considerations

The skill places real phone calls that reach real people. The voice agent's system prompt enforces two upfront disclosures: it announces that the call is being recorded, and it admits to being an AI when directly asked. Agents using ClawCall should additionally:
- Not place calls that harass, deceive, or spam recipients.
- Not use the skill to evade identity verification, impersonate the user beyond the scope they've authorized, or commit to anything the user has not approved.
- Respect Do-Not-Call lists, robocall laws, and recipient consent for recorded calls under applicable state laws.

Users remain accountable for the calls placed on their behalf and should review post-call transcripts before relying on stated commitments.
