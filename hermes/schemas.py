"""Tool JSON schemas and Hermes metadata for the ClawCall plugin."""

from __future__ import annotations

from typing import Any

try:
    from .config import SUPPORTED_LANGUAGES, SUPPORTED_VOICES, WRITE_TOOLS
except ImportError:  # pragma: no cover - direct module loading
    from config import SUPPORTED_LANGUAGES, SUPPORTED_VOICES, WRITE_TOOLS

TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    "clawcall_get_balance": {
        "name": "clawcall_get_balance",
        "description": "Read the connected ClawCall account's plan status and remaining trial allowance without placing a call.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_place_call": {
        "name": "clawcall_place_call",
        "description": (
            "Place one real outbound US +1 phone call via ClawCall. Requires explicit user approval through "
            "Hermes before execution. Refuses non-US, emergency/N11, and premium-rate numbers. Stores no transcripts locally."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "US +1 E.164 phone number to call (for example +14155550123). Non-US, emergency, and premium-rate numbers are refused.",
                },
                "recipient": {
                    "type": "string",
                    "description": "Business, department, location, or person expected to answer.",
                },
                "on_behalf_of": {
                    "type": "string",
                    "description": "Person or organization the assistant represents.",
                },
                "goal": {
                    "type": "string",
                    "description": "Outcome wanted from the call with all context needed (up to 2000 characters).",
                },
                "authority": {
                    "type": "object",
                    "description": "Commitments allowed and boundaries. Empty allow list means ask and relay only.",
                    "properties": {
                        "allow": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "limits": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["allow"],
                    "additionalProperties": False,
                },
                "facts": {
                    "type": "array",
                    "description": "Labeled reference details the recipient may ask for.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["label", "value"],
                        "additionalProperties": False,
                    },
                },
                "questions": {
                    "type": "array",
                    "description": "Questions to ask the recipient.",
                    "items": {"type": "string"},
                },
                "handoff": {
                    "type": "object",
                    "description": "Optional loop-in settings for ringing the user or named contacts.",
                    "properties": {
                        "when": {
                            "type": "string",
                            "description": "When to ring the user or contacts in, in plain words.",
                        },
                        "warm_greeting": {"type": "boolean"},
                        "contacts": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "phone": {"type": "string"},
                                    "ring_seconds": {"type": "integer"},
                                    "warm_greeting": {"type": "boolean"},
                                },
                                "required": ["name", "phone"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "additionalProperties": False,
                },
                "voicemail": {
                    "type": "object",
                    "description": "Voicemail handling: kind 'end' or 'leave_message' with message text.",
                    "properties": {
                        "kind": {"type": "string", "enum": ["end", "leave_message"]},
                        "message": {"type": "string"},
                    },
                    "required": ["kind"],
                    "additionalProperties": False,
                },
                "assistant_name": {
                    "type": "string",
                    "description": "Optional plain assistant name such as Jordan.",
                },
                "voice": {
                    "type": "string",
                    "enum": list(SUPPORTED_VOICES),
                    "description": "Optional audio voice.",
                },
                "language": {
                    "type": "string",
                    "enum": list(SUPPORTED_LANGUAGES),
                    "description": "Optional ISO language code (25 supported languages).",
                },
                "from": {
                    "type": "string",
                    "description": "Optional US +1 caller ID line belonging to the account.",
                },
                "delegation": {
                    "type": "boolean",
                    "description": "Optional: true enables live delegation lookups during the call (default false).",
                },
            },
            "required": ["to", "recipient", "on_behalf_of", "goal", "authority"],
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": True,
        "x-clawcall-scope": "calls:write",
    },
    "clawcall_get_call": {
        "name": "clawcall_get_call",
        "description": "Read a call's lifecycle, network outcome, talk time, and latest captured transcript lines when present.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The call ID returned by clawcall_place_call.",
                },
            },
            "required": ["call_id"],
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_get_call_transcript": {
        "name": "clawcall_get_call_transcript",
        "description": "Return captured transcript evidence for a call directly in tool output without writing files to disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The call ID returned by clawcall_place_call.",
                },
            },
            "required": ["call_id"],
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_list_calls": {
        "name": "clawcall_list_calls",
        "description": "Read recent outbound or inbound call history for the connected ClawCall account.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["outbound", "inbound"],
                    "description": "Optional call direction filter.",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "description": "Maximum number of calls to return.",
                },
                "since": {
                    "type": "string",
                    "description": "Optional ISO-8601 timestamp filter.",
                },
                "phone": {
                    "type": "string",
                    "description": "Optional US +1 E.164 phone filter.",
                },
            },
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_get_recording": {
        "name": "clawcall_get_recording",
        "description": "Return a temporary playable recording URL when available (ClawCall deletes recordings after 10 minutes; nothing is saved locally).",
        "parameters": {
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The call ID returned by clawcall_place_call.",
                },
            },
            "required": ["call_id"],
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_hangup_call": {
        "name": "clawcall_hangup_call",
        "description": "Hang up a queued or live ClawCall phone call. Requires explicit user approval through Hermes.",
        "parameters": {
            "type": "object",
            "properties": {
                "call_id": {
                    "type": "string",
                    "description": "The call ID of the active or queued call to stop.",
                },
            },
            "required": ["call_id"],
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": True,
        "x-clawcall-scope": "calls:write",
    },
    "clawcall_get_call_settings": {
        "name": "clawcall_get_call_settings",
        "description": "Read saved voice, loop-in greeting preference, reserved number status, and inbound assistant settings.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": False,
        "x-clawcall-scope": "calls:read",
    },
    "clawcall_update_call_settings": {
        "name": "clawcall_update_call_settings",
        "description": "Update ClawCall voice, warm greeting, or inbound answering settings. Requires explicit user approval through Hermes.",
        "parameters": {
            "type": "object",
            "properties": {
                "voice": {
                    "type": ["string", "null"],
                    "enum": [*SUPPORTED_VOICES, None],
                },
                "personality": {"type": ["string", "null"]},
                "greeting": {"type": ["string", "null"]},
                "warm_greeting": {"type": "boolean"},
                "inbound": {
                    "type": ["object", "null"],
                    "properties": {
                        "instructions": {"type": "string"},
                        "greeting": {"type": "string"},
                        "loop_in_user": {"type": "boolean"},
                        "handoff_number": {"type": ["string", "null"]},
                        "knowledge_base": {"type": ["string", "null"]},
                        "default_language": {
                            "type": ["string", "null"],
                            "enum": [*SUPPORTED_LANGUAGES, None],
                        },
                        "passthrough_numbers": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "additionalProperties": False,
                },
            },
            "additionalProperties": False,
        },
        "x-hermes-requires-approval": True,
        "x-clawcall-scope": "calls:write",
    },
}

TOOL_METADATA: dict[str, dict[str, Any]] = {
    name: {
        "name": name,
        "toolset": "clawcall",
        "requires_approval": name in WRITE_TOOLS,
        "scope": "calls:write" if name in WRITE_TOOLS else "calls:read",
        "read_only": name not in WRITE_TOOLS,
        "stores_transcript_locally": False,
    }
    for name in TOOL_SCHEMAS
}
