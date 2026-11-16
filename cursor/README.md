# ClawCall for Cursor and Grok Bot

This plugin connects Cursor and Grok Bot to ClawCall's hosted MCP server at `https://api.clawcall.dev/mcp`.

## What it does

- Places real calls to US phone numbers, works phone menus, and waits on hold.
- Talks to whoever answers and reports the outcome, with the transcript and a temporary recording link when available.
- Rings the user's verified phone and connects them into the call when only they can continue (one-time codes, payments, identity checks).
- Lists call history, ends active calls, and shows plan or trial usage.
- Serves ClawCall's calling guide, which the agent reads before it places a call.

## Sign-in and permissions

The first use opens ClawCall's OAuth 2.1 sign-in. Users sign in to their ClawCall account and approve two scopes:

- `calls:read`: call status, transcripts, recordings, history, plan, and guides.
- `calls:write`: placing, steering, and ending calls, and saving call settings.

No API key, secret, environment variable, hook, or executable ships with this plugin. New accounts get 30 calls or 30 minutes free, whichever comes first, with no card.

## Network access

- `https://api.clawcall.dev/mcp`: Streamable HTTP MCP endpoint.
- `https://api.clawcall.dev/.well-known/*` and the `authorize`, `token`, `register`, and `revoke` endpoints on the same origin: OAuth discovery, dynamic client registration, and tokens.

## Support

- Docs: https://clawcall.dev/for-agents
- Privacy: https://clawcall.dev/privacy
- Email: support@clawcall.dev
