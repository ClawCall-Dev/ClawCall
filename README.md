# ClawCall

Make real AI-powered phone calls from any AI agent. ClawCall dials the number, has the conversation, and brings back a full transcript.

**10 free minutes or 10 calls. No setup. No API keys to configure.**

## Install From ClawHub

```bash
openclaw skills install clawcall-dev
```

Published skill: https://clawhub.ai/clawcall-dev/clawcall-dev

Or manually, download the skill zip from ClawHub and add `SKILL.md` to your agent's skills directory.

## MCP Server

Prefer the Model Context Protocol? [`mcp/`](./mcp) is a stdio MCP server that exposes the
same ClawCall REST API as tools for any MCP host (Claude Code, Claude Desktop, Cursor,
Windsurf). It shares one identity and balance with the skill.

```bash
claude mcp add clawcall -- npx -y @clawcall/mcp
```

See [`mcp/README.md`](./mcp/README.md) for client config and the call workflow. The skill is
the procedural layer; the MCP server is the connectivity layer — both wrap the public API at
`https://api.clawcall.dev`.

## What users learn on install

When the skill is installed or first introduced, the agent should explain:

- ClawCall makes real outbound phone calls in the US and Canada
- The AI can handle appointments, reservations, order checks, callbacks, office follow-ups, voicemail/messages, phone menus, and hold queues
- The user can be patched in live when a call needs identity verification, negotiation, or a real-time decision
- Users can configure reusable voice, personality, greeting, and inbound reserved-number answering preferences
- Completed calls return the outcome first, with transcript details and a temporary recording URL available
- The first call auto-creates a low-privilege API key, and new users get 10 free minutes or 10 calls, whichever comes first

## What it does

- Calls US and Canada phone numbers over real phone lines
- AI agent handles the full conversation based on your task briefing
- Leaves voicemail or takes messages when the task asks for it
- Returns a complete transcript and recording
- Live handoff: the AI navigates phone trees and hold queues, then connects you in to speak directly
- Reusable voice/personality profile setup for outbound and inbound answering
- Automatic retry and callback when a call needs more information

## Examples

> "Call Dr. Rivera's office and confirm my appointment for Tuesday at 2:30"

> "Phone the restaurant at +15551234567 and make a reservation for 4 people Saturday at 7 PM"

> "Get me through to a real person at my insurance company - here's the number"

## Links

- [Published ClawHub Skill](https://clawhub.ai/clawcall-dev/clawcall-dev)
- [ClawCall Dashboard](https://clawcall.dev)
- [API Documentation](https://api.clawcall.dev)

## License

MIT
