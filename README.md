# ClawCall

Make real AI-powered phone calls from any AI agent. ClawCall dials US phone numbers, handles the conversation, and returns the outcome, transcript, and recording when available.

**30 calls and 30 minutes free, whichever lasts later. No credit card required.**

## Hosted MCP connector (recommended)

ClawCall's official remote MCP server is available at:

```text
https://api.clawcall.dev/mcp
```

Add that URL as a custom connector in Grok Build, ChatGPT, Claude, Codex, or another remote MCP client. The connector uses OAuth 2.1: sign in to ClawCall and approve read/write call access when prompted. No API key is copied into the AI host.

The hosted connector can:

- place outbound calls to US phone numbers
- navigate phone menus and hold queues
- bridge the user into a live call
- poll call status and retrieve transcripts and temporary recording URLs
- list inbound and outbound call history
- end active calls and inspect plan or trial usage
- serve ClawCall's calling guide before a call is placed
- configure inbound answering and passthrough callers that ring the verified
  account phone directly with the original caller ID, without recording or transcription

The Grok Build plugin source is in [`grok/`](./grok). Its official xAI marketplace submission is tracked in [xai-org/plugin-marketplace#336](https://github.com/xai-org/plugin-marketplace/pull/336).

## Agent skill

Install the ClawCall skill from ClawHub:

```bash
openclaw skills install @clawcall-dev/clawcall-dev
```

Published skill: https://clawhub.ai/clawcall-dev/skills/clawcall-dev

Or copy the [`skill/`](./skill) directory, containing only `SKILL.md` and `LICENSE`, into your agent's skills directory. The skill fetches current calling guides and API formats from [ClawCall's public guide index](https://api.clawcall.dev/guides/v1/index.md) before new operations. These instructions change with the server without requiring another skill update. Credentials remain local and are never sent when fetching public guides.

Existing installations need the 2.0.0 migration once. Replace the old skill directory, including its bundled references, with the two-file package. Keep credentials in the host secret store or `~/.config/clawcall/key.json`. Changes to the skill's capabilities or permissions still require a new skill release.

## Legacy local stdio MCP package

The [`mcp/`](./mcp) directory contains the legacy `@clawcall/mcp` stdio package for existing local/API-key installations. New integrations should use the hosted OAuth connector above. The legacy package remains documented for compatibility but is not the distribution path submitted to the xAI marketplace.

## What it does

- Calls US phone numbers over real phone lines
- Handles appointments, reservations, order checks, callbacks, office follow-ups, phone menus, and hold queues
- Leaves voicemail or takes messages when instructed
- Returns call outcomes, transcripts, and recordings
- Supports live handoff when identity verification, negotiation, or a real-time decision requires the user
- Supports reusable voice, personality, greeting, and inbound reserved-number answering preferences through the product and REST surfaces

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
