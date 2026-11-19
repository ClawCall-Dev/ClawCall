# ClawCall: phone calls for AI agents

ClawCall is a remote MCP server that lets an AI agent make real phone calls. Add one URL to ChatGPT, Claude, Cursor, Codex, Grok Build or any MCP client, sign in, and your agent can call a US number, get through the phone menu, wait on hold, talk to whoever answers, and bring back the outcome and transcript.

```text
https://api.clawcall.dev/mcp
```

- **No API key, no carrier account, no number to buy.** The connector signs in with OAuth 2.1, and calls go out from ClawCall's numbers.
- **Flat price.** Unlimited calls to US numbers for $8.99 a month, with no per-minute charges. Unlimited means fair use for one person or agent, not bulk or automated outreach. The free trial is 30 calls or 30 minutes, whichever comes first, with no credit card.
- **It makes the call itself.** A voice agent holds the conversation in any of 25 languages. You do not build or host a voice pipeline.

## Quick start

1. Add `https://api.clawcall.dev/mcp` as a custom connector (remote MCP server) in your AI client. In ChatGPT, install the [ClawCall plugin](https://chatgpt.com/plugins/plugin_asdk_app_6aaf68b30c288191859044b59f1bcb07) from the plugin directory instead.
2. Sign in to ClawCall when the consent page opens and allow call access (`calls:read`, `calls:write`).
3. Ask for a call: "Call the pharmacy at (555) 010-0000 and ask whether my prescription is ready."

Step-by-step guides for each client: [ChatGPT](https://clawcall.dev/guides/chatgpt-mcp), [Claude](https://clawcall.dev/guides/claude-mcp), [Grok Bot](https://clawcall.dev/guides/grok-bot-mcp), [OpenAI dots](https://clawcall.dev/guides/openai-dots-mcp), [OpenClaw](https://clawcall.dev/guides/openclaw-mcp), [Hermes Agent](https://clawcall.dev/guides/hermes-mcp), and [more](https://clawcall.dev/guides).

## What the agent can do

| Tool | What it does |
| --- | --- |
| `get_calling_guide` | Reads ClawCall's current guide for briefing a call |
| `place_call` | Starts a call and returns at once with a call ID |
| `place_call_and_wait` | Places one call and waits briefly (45 seconds by default) for the result |
| `place_call_and_track` | Places one call and returns its first event |
| `track_call` | Waits for the next event on a call: ringing, answered, a question from the phone agent, or ended |
| `reply_on_call` | Answers a question the phone agent asked your agent during a live call |
| `get_call` | Call status and outcome |
| `get_call_transcript` | Full turn-by-turn transcript |
| `get_recording` | Temporary recording link, when a recording was captured |
| `hangup_call` | Ends a call in progress |
| `list_calls` | Inbound and outbound call history |
| `get_balance` | Plan and trial usage |
| `get_call_settings`, `update_call_settings` | Voice, greeting, and inbound answering preferences |
| `connect_webhook` | Sends call events to your agent's webhook URL |

On a call, ClawCall:

- navigates phone menus (keypad presses) and waits on hold
- speaks any of 25 languages and follows the other side if they switch
- rings you into the call when a decision, a one-time code or a payment detail is yours to give
- leaves a voicemail when told to
- answers calls to your own reserved number and takes messages, on the Unlimited Reserve Plus plan

## How ClawCall compares

Ways to give an AI agent a phone, from each vendor's own docs and pricing pages on 2026-11-19. "Not stated" means the vendor's pages did not say.

| | Connect | Your own number or carrier | Price for US calls | Phone menus and hold | Calls to |
| --- | --- | --- | --- | --- | --- |
| **ClawCall** | Remote MCP, OAuth sign-in | Not needed | Flat $8.99/month, unlimited; free trial of 30 calls or 30 minutes | Both | US numbers only |
| [AgentPhone](https://agentphone.ai/pricing) | Remote MCP with OAuth or an API key | Buy a number, $3/month each | $0.22/min with its hosted voice agent, $0.13/min with your own; $5 starting credit | Keypad presses stated; hold not stated | Not stated (its numbers are US and Canada) |
| [Vapi](https://vapi.ai/pricing) | Remote MCP, OAuth sign-in | Outbound calls need a number imported from Twilio, Telnyx or another carrier ([docs](https://docs.vapi.ai/phone-calling.md)) | $0.05/min platform fee plus model, voice and transcription costs | Keypad presses stated; hold not stated | Depends on the number you import; international calls stated |
| [Bland](https://www.bland.ai/pricing) | Remote MCP with OAuth or an API key | Not needed; shared number, or a dedicated one on its Agent Phone Plan | $0.14/min on the Start plan, or the Agent Phone Plan: unlimited US and Canada calls for $9.99 the first month, then $19.99/month | Phone menus stated; hold not stated | US and Canada on the Agent Phone Plan; other countries from credits |
| [Twilio](https://github.com/twilio-labs/mcp) | Local MCP server with your Twilio API keys | Your own Twilio account and numbers | $0.014/min outbound for the phone line only ([pricing](https://www.twilio.com/en-us/voice/pricing/us)); the voice agent is yours to build | Not built in | International, priced by country |
| [call4me](https://call4.me/pricing) | Remote MCP, Google or X sign-in or an API key | Not needed | $0.25/min from pickup, $0.125/min on hold | Both | US, Canada, EU, UK and more |
| [OsmO](https://getosmo.app/mcp) | Remote MCP, sign-in by text message | Not needed | 3 credits per answered call, 50 free credits ([details](https://getosmo.app/ai-calls/mcp-phone-calls-for-agents)) | Both | US, UK, India, Canada, Australia |

What that means for 100 five-minute calls a month (500 minutes) at each published rate: $113 on AgentPhone's hosted agent with one number, at least $70 on Bland's Start plan or $19.99 on its Agent Phone Plan, up to $125 on call4me (its hold time bills at half rate), and $8.99 on ClawCall.

Where ClawCall is the wrong choice:

- **Calls outside the US.** ClawCall dials US +1 numbers only.
- **Many calls at once.** One outbound call at a time per account, so it is not for bulk outreach or a call center.
- **Building your own voice agent.** If you want to control the model, voice and call flow yourself, Vapi, Bland, Retell or Twilio are built for that.

## Plans

| Plan | Price | What you get |
| --- | --- | --- |
| Free trial | $0 | 30 calls or 30 minutes, whichever comes first |
| Unlimited | $8.99/month | Unlimited outbound calls to US numbers from shared ClawCall numbers |
| Unlimited Reserve | $14.99/month | Adds your own reserved US number as caller ID |
| Unlimited Reserve Plus | $18.99/month | Adds an AI that answers calls to your number |

Current details: [clawcall.dev/pricing](https://clawcall.dev/pricing).

## Plugins in this repository

The Cursor and Grok Bot plugin source is in [`cursor/`](./cursor). The Grok Build plugin source is in [`grok/`](./grok). Its official xAI marketplace submission is tracked in [xai-org/plugin-marketplace#336](https://github.com/xai-org/plugin-marketplace/pull/336).

## Agent skill

Install the ClawCall skill from ClawHub:

```bash
openclaw skills install @clawcall-dev/clawcall-dev
```

Published skill: https://clawhub.ai/clawcall-dev/skills/clawcall-dev

### Hermes Agent

Install version 2.0.1 directly from the official repository:

```bash
hermes skills install https://raw.githubusercontent.com/ClawCall-Dev/ClawCall/skill-v2.0.1/skill/SKILL.md
```

Or install the publisher-qualified ClawHub package:

```bash
hermes skills install @clawcall-dev/clawcall-dev
```

Start a new Hermes session after installation, then ask Hermes to make a call. The direct install exposes `/clawcall`; the ClawHub install exposes `/clawcall-dev`. Use `CLAWCALL_API_KEY` if you already have a key; eligible first calls can provision one. No call is placed during installation.

Hermes' Skills Hub searches ClawHub and other registries. On versions whose ClawHub search returns no results, use either install command above instead of keyword search.

Or copy the [`skill/`](./skill) directory, containing only `SKILL.md` and `LICENSE`, into your agent's skills directory. The skill fetches current calling guides and API formats from [ClawCall's public guide index](https://api.clawcall.dev/guides/v1/index.md) before new operations. These instructions change with the server without requiring another skill update. Credentials remain local and are never sent when fetching public guides.

Existing installations need the 2.0.0 migration once. Replace the old skill directory, including its bundled references, with the two-file package. Keep credentials in the host secret store or `~/.config/clawcall/key.json`. Changes to the skill's capabilities or permissions still require a new skill release.

## Legacy local stdio MCP package

The [`mcp/`](./mcp) directory contains the legacy `@clawcall/mcp` stdio package for existing local/API-key installations. New integrations should use the hosted OAuth connector above. The legacy package remains documented for compatibility but is not the distribution path submitted to the xAI marketplace.

## Examples

> "Call Dr. Rivera's office and confirm my appointment for Tuesday at 2:30."

> "Phone the restaurant at +15551234567 and make a reservation for four people Saturday at 7 PM."

> "Get me through to a real person at my insurance company."

## Links

- [ClawCall](https://clawcall.dev)
- [Documentation](https://clawcall.dev/docs)
- [For AI agents](https://clawcall.dev/for-agents)
- [Hosted MCP endpoint](https://api.clawcall.dev/mcp)
- [Published ClawHub skill](https://clawhub.ai/clawcall-dev/skills/clawcall-dev)
- [Privacy policy](https://clawcall.dev/privacy)
- [Terms of service](https://clawcall.dev/terms)

## License

The distributed [`skill/`](./skill/LICENSE) is licensed MIT-0. Other repository components retain their existing MIT licenses. ClawCall service usage is governed separately by its [terms](https://clawcall.dev/terms).

## Download History

[![Download History](https://skill-history.com/chart/clawcall-dev/clawcall-dev.svg)](https://skill-history.com/clawcall-dev/clawcall-dev)
