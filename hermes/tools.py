"""Safe tool wrappers for the ClawCall Hermes Agent plugin.

All mutating operations enforce the Hermes approval gate. All destination and
loop-in numbers pass the strict US +1, emergency, and premium-rate guard before
any network call is issued. No transcripts, recordings, or phone numbers are ever
written to local disk.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

try:
    from .approval import ApprovalCallback, ApprovalGate, normalize_allowlist
    from .client import ClawCallClient, HttpTransport
    from .config import (
        ALL_TOOLS,
        ClawCallConfig,
        MAX_GOAL_CHARS,
        SUPPORTED_LANGUAGES,
        SUPPORTED_VOICES,
    )
    from .phone_guard import PhoneValidationError, assert_us_phone_number
    from .schemas import TOOL_METADATA, TOOL_SCHEMAS
except ImportError:  # pragma: no cover - direct module loading
    from approval import ApprovalCallback, ApprovalGate, normalize_allowlist
    from client import ClawCallClient, HttpTransport
    from config import (
        ALL_TOOLS,
        ClawCallConfig,
        MAX_GOAL_CHARS,
        SUPPORTED_LANGUAGES,
        SUPPORTED_VOICES,
    )
    from phone_guard import PhoneValidationError, assert_us_phone_number
    from schemas import TOOL_METADATA, TOOL_SCHEMAS


def _require_non_empty_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _validate_place_call_payload(
    raw_params: dict[str, Any],
    *,
    allowed_numbers: tuple[str, ...] = (),
) -> dict[str, Any]:
    if not isinstance(raw_params, dict):
        raise ValueError("clawcall_place_call parameters must be a JSON object.")

    params = deepcopy(raw_params)

    # Validate destination number before anything else.
    params["to"] = assert_us_phone_number(params.get("to"), field_name="to")

    allowlist = normalize_allowlist(allowed_numbers)  # raises AllowlistError on a bad entry
    if allowlist and params["to"] not in allowlist:
        raise PhoneValidationError(
            "number_not_allowed",
            f"to: {params['to']} is not in the configured allowed_numbers list.",
        )

    if "from" in params and params["from"] is not None:
        params["from"] = assert_us_phone_number(params["from"], field_name="from")

    if "task" in params:
        raise ValueError(
            "Use structured call fields (to, recipient, on_behalf_of, goal, authority) instead of legacy task."
        )

    params["recipient"] = _require_non_empty_string(params.get("recipient"), "recipient")
    params["on_behalf_of"] = _require_non_empty_string(params.get("on_behalf_of"), "on_behalf_of")
    params["goal"] = _require_non_empty_string(params.get("goal"), "goal")
    if len(params["goal"]) > MAX_GOAL_CHARS:
        raise ValueError(
            f"goal is {len(params['goal'])} characters; the limit is {MAX_GOAL_CHARS} characters."
        )

    authority = params.get("authority")
    if not isinstance(authority, dict) or not isinstance(authority.get("allow"), list):
        raise ValueError("authority.allow is required and must be a list of strings (use [] for ask and relay only).")
    if not all(isinstance(item, str) and item.strip() for item in authority["allow"]):
        raise ValueError("authority.allow entries must be non-empty strings.")
    if "limits" in authority:
        if not isinstance(authority["limits"], list) or not authority["limits"]:
            raise ValueError("authority.limits must be a non-empty list of strings when supplied.")
        if not all(isinstance(item, str) and item.strip() for item in authority["limits"]):
            raise ValueError("authority.limits entries must be non-empty strings.")

    if "voice" in params and params["voice"] is not None:
        if params["voice"] not in SUPPORTED_VOICES:
            raise ValueError(f"voice must be one of: {', '.join(SUPPORTED_VOICES)}.")

    if "language" in params and params["language"] is not None:
        if params["language"] not in SUPPORTED_LANGUAGES:
            raise ValueError(f"language must be one of: {', '.join(SUPPORTED_LANGUAGES)}.")

    handoff = params.get("handoff")
    if handoff is not None:
        if not isinstance(handoff, dict):
            raise ValueError("handoff must be an object.")
        if "when" in handoff and handoff["when"] is not None:
            handoff["when"] = _require_non_empty_string(handoff["when"], "handoff.when")
        contacts = handoff.get("contacts")
        if contacts is not None:
            if not isinstance(contacts, list) or not (1 <= len(contacts) <= 10):
                raise ValueError("handoff.contacts must contain between 1 and 10 contacts.")
            for idx, contact in enumerate(contacts, start=1):
                if not isinstance(contact, dict):
                    raise ValueError(f"handoff.contacts[{idx}] must be an object.")
                _require_non_empty_string(contact.get("name"), f"handoff.contacts[{idx}].name")
                contact["phone"] = assert_us_phone_number(
                    contact.get("phone"),
                    field_name=f"handoff.contacts[{idx}].phone",
                )
                if allowlist and contact["phone"] not in allowlist:
                    raise PhoneValidationError(
                        "number_not_allowed",
                        f"handoff.contacts[{idx}].phone: {contact['phone']} is not in the configured "
                        "allowed_numbers list.",
                    )

    voicemail = params.get("voicemail")
    if voicemail is not None:
        if not isinstance(voicemail, dict):
            raise ValueError("voicemail must be an object.")
        kind = voicemail.get("kind")
        if kind not in ("end", "leave_message"):
            raise ValueError("voicemail.kind must be 'end' or 'leave_message'.")
        if kind == "leave_message":
            voicemail["message"] = _require_non_empty_string(voicemail.get("message"), "voicemail.message")
        elif "message" in voicemail:
            raise ValueError("voicemail.message is only allowed with kind 'leave_message'.")

    if "delegation" in params and params["delegation"] is not None:
        if not isinstance(params["delegation"], bool):
            raise ValueError("delegation must be true or false.")

    return params


def _validate_update_settings_payload(raw_params: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw_params, dict):
        raise ValueError("clawcall_update_call_settings parameters must be a JSON object.")

    params = deepcopy(raw_params)

    if "voice" in params and params["voice"] is not None and params["voice"] != "":
        if params["voice"] not in SUPPORTED_VOICES:
            raise ValueError(f"voice must be one of: {', '.join(SUPPORTED_VOICES)}.")

    inbound = params.get("inbound")
    if isinstance(inbound, dict):
        if "handoff_number" in inbound and inbound["handoff_number"] is not None:
            inbound["handoff_number"] = assert_us_phone_number(
                inbound["handoff_number"],
                field_name="inbound.handoff_number",
            )
        if "passthrough_numbers" in inbound and inbound["passthrough_numbers"] is not None:
            if not isinstance(inbound["passthrough_numbers"], list):
                raise ValueError("inbound.passthrough_numbers must be a list of US +1 numbers.")
            inbound["passthrough_numbers"] = [
                assert_us_phone_number(num, field_name=f"inbound.passthrough_numbers[{idx}]")
                for idx, num in enumerate(inbound["passthrough_numbers"], start=1)
            ]
        if "default_language" in inbound and inbound["default_language"] is not None:
            if inbound["default_language"] not in SUPPORTED_LANGUAGES:
                raise ValueError(f"inbound.default_language must be one of: {', '.join(SUPPORTED_LANGUAGES)}.")

    return params


class ClawCallPlugin:
    """High-level wrapper exposing all 9 ClawCall tools with safety guards."""

    def __init__(
        self,
        *,
        config: ClawCallConfig | None = None,
        approval_callback: ApprovalCallback | None = None,
        http_transport: HttpTransport | None = None,
    ) -> None:
        self.config = config or ClawCallConfig.from_hermes()
        self.approval_gate = ApprovalGate(
            approval_callback=approval_callback,
            require_approval=self.config.require_approval,
        )
        self.client = ClawCallClient(self.config, http_transport=http_transport)

    def get_tool_schemas(self) -> dict[str, dict[str, Any]]:
        return deepcopy(TOOL_SCHEMAS)

    def get_tool_metadata(self) -> dict[str, dict[str, Any]]:
        return deepcopy(TOOL_METADATA)

    def get_balance(self) -> Any:
        return self.invoke("clawcall_get_balance", {})

    def place_call(self, payload: dict[str, Any], *, approved: bool | None = None) -> Any:
        return self.invoke("clawcall_place_call", payload, approved=approved)

    def get_call(self, call_id: str) -> Any:
        return self.invoke("clawcall_get_call", {"call_id": call_id})

    def get_call_transcript(self, call_id: str) -> Any:
        return self.invoke("clawcall_get_call_transcript", {"call_id": call_id})

    def list_calls(
        self,
        *,
        direction: str | None = None,
        limit: int | None = None,
        since: str | None = None,
        phone: str | None = None,
    ) -> Any:
        params: dict[str, Any] = {}
        if direction is not None:
            params["direction"] = direction
        if limit is not None:
            params["limit"] = limit
        if since is not None:
            params["since"] = since
        if phone is not None:
            params["phone"] = phone
        return self.invoke("clawcall_list_calls", params)

    def get_recording(self, call_id: str) -> Any:
        return self.invoke("clawcall_get_recording", {"call_id": call_id})

    def hangup_call(self, call_id: str, *, approved: bool | None = None) -> Any:
        return self.invoke("clawcall_hangup_call", {"call_id": call_id}, approved=approved)

    def get_call_settings(self) -> Any:
        return self.invoke("clawcall_get_call_settings", {})

    def update_call_settings(self, payload: dict[str, Any], *, approved: bool | None = None) -> Any:
        return self.invoke("clawcall_update_call_settings", payload, approved=approved)

    def invoke(
        self,
        tool_name: str,
        params: dict[str, Any] | None = None,
        *,
        approved: bool | None = None,
    ) -> Any:
        if tool_name not in ALL_TOOLS:
            raise ValueError(f"Unsupported ClawCall tool: {tool_name}")

        raw = dict(params or {})
        validated = self._validate_inputs(tool_name, raw)

        # Enforce Hermes approval gate for write operations before any network request.
        self.approval_gate.check(tool_name, validated, approved=approved)

        # Execute over configured transport, keeping everything in memory.
        return self.client.execute_tool(tool_name, validated)

    def _validate_inputs(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        if tool_name in ("clawcall_get_balance", "clawcall_get_call_settings"):
            return {}

        if tool_name == "clawcall_place_call":
            return _validate_place_call_payload(
                params,
                allowed_numbers=self.config.allowed_numbers,
            )

        if tool_name in (
            "clawcall_get_call",
            "clawcall_get_call_transcript",
            "clawcall_get_recording",
            "clawcall_hangup_call",
        ):
            call_id = _require_non_empty_string(params.get("call_id"), "call_id")
            return {"call_id": call_id}

        if tool_name == "clawcall_list_calls":
            cleaned: dict[str, Any] = {}
            if "direction" in params and params["direction"] is not None:
                if params["direction"] not in ("outbound", "inbound"):
                    raise ValueError("direction must be 'outbound' or 'inbound'.")
                cleaned["direction"] = params["direction"]
            if "limit" in params and params["limit"] is not None:
                if not isinstance(params["limit"], int) or params["limit"] < 1:
                    raise ValueError("limit must be a positive integer.")
                cleaned["limit"] = params["limit"]
            if "since" in params and params["since"] is not None:
                cleaned["since"] = _require_non_empty_string(params["since"], "since")
            if "phone" in params and params["phone"] is not None:
                cleaned["phone"] = assert_us_phone_number(params["phone"], field_name="phone")
            return cleaned

        if tool_name == "clawcall_update_call_settings":
            return _validate_update_settings_payload(params)

        raise ValueError(f"Unsupported ClawCall tool: {tool_name}")
