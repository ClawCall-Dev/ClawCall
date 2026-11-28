"""Hermes approval gate and pre_tool_call directives for mutating ClawCall tools."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Callable

try:
    from .config import MAX_GOAL_CHARS, WRITE_TOOLS
    from .phone_guard import validate_us_phone_number
except ImportError:  # pragma: no cover - direct module loading
    from config import MAX_GOAL_CHARS, WRITE_TOOLS
    from phone_guard import validate_us_phone_number


class ApprovalRequiredError(PermissionError):
    """Raised when a mutating tool is called without explicit user approval."""

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(message)
        self.code = "approval_required"
        self.tool_name = tool_name
        self.message = message


class ApprovalDeniedError(PermissionError):
    """Raised when the user or Hermes approval callback denies a mutating tool."""

    def __init__(self, tool_name: str, message: str) -> None:
        super().__init__(message)
        self.code = "approval_denied"
        self.tool_name = tool_name
        self.message = message


@dataclass(frozen=True)
class ApprovalRequest:
    """Structured approval request handed to Hermes or a host approval callback."""

    tool_name: str
    scope: str
    summary: str
    preview: dict[str, Any]
    rule_key: str


ApprovalCallback = Callable[[ApprovalRequest], bool]


def _rule_key(tool_name: str, content: str) -> str:
    """Approve-for-session remembers this exact content only, never a whole tool."""
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
    return f"clawcall:{tool_name}:{digest}"


def _handoff_contacts(params: dict[str, Any]) -> list[dict[str, Any]]:
    handoff = params.get("handoff")
    contacts = handoff.get("contacts") if isinstance(handoff, dict) else None
    if not isinstance(contacts, list):
        return []
    return [c if isinstance(c, dict) else {} for c in contacts]


def _handoff_line(params: dict[str, Any]) -> str | None:
    handoff = params.get("handoff")
    if not isinstance(handoff, dict):
        return None
    contacts = _handoff_contacts(params)
    if not contacts:
        return "Hand-off: may ring you into the call (your saved ClawCall loop-in list, or your verified phone)"
    people = ", ".join(
        f"{c.get('name') or '(no name)'} ({c.get('phone') or 'no number'})" for c in contacts
    )
    return f"Hand-off: may ring these people into the call, in order: {people}"


def _voicemail_line(params: dict[str, Any]) -> str | None:
    voicemail = params.get("voicemail")
    if not isinstance(voicemail, dict):
        return None
    if voicemail.get("kind") == "leave_message":
        return f"At voicemail, leave this message: {voicemail.get('message') or '(empty)'}"
    return "At voicemail: hang up without leaving a message"


def build_approval_message(tool_name: str, params: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if tool_name == "clawcall_place_call":
        recipient = str(params.get("recipient") or "recipient")
        to_number = str(params.get("to") or "unknown number")
        on_behalf_of = str(params.get("on_behalf_of") or "(not set)")
        goal = str(params.get("goal") or "")
        authority = params.get("authority") or {}
        allow = authority.get("allow") if isinstance(authority, dict) else []
        limits = authority.get("limits") if isinstance(authority, dict) else []
        lines = [
            f"Place a US phone call via ClawCall to {recipient} ({to_number})",
            f"On behalf of: {on_behalf_of}",
            f"Goal: {goal or '(empty)'}",
            f"Allowed commitments: {', '.join(allow) if allow else 'ask and relay only'}",
        ]
        if limits:
            lines.append(f"Limits: {', '.join(limits)}")
        from_number = params.get("from")
        if from_number:
            lines.append(f"Calling from your line: {from_number}")
        for extra in (_handoff_line(params), _voicemail_line(params)):
            if extra:
                lines.append(extra)
        return (
            "\n".join(lines),
            {
                "to": to_number,
                "recipient": recipient,
                "on_behalf_of": on_behalf_of,
                "goal": goal,
                "authority": authority,
                "from": params.get("from"),
                "handoff_contacts": [
                    {"name": c.get("name"), "phone": c.get("phone")} for c in _handoff_contacts(params)
                ],
                "voicemail": params.get("voicemail"),
            },
        )

    if tool_name == "clawcall_hangup_call":
        call_id = str(params.get("call_id") or "unknown call")
        return (
            f"Hang up active ClawCall call {call_id}.",
            {"call_id": call_id},
        )

    if tool_name == "clawcall_update_call_settings":
        changed_keys = sorted(str(k) for k in params.keys())
        details = json.dumps(params, sort_keys=True, default=str)
        return (
            f"Update ClawCall account call settings ({', '.join(changed_keys) or 'no fields'}):\n{details}",
            {"fields": changed_keys},
        )

    return (f"Execute mutating ClawCall tool {tool_name}.", {})


def normalize_allowlist(raw_numbers: Any) -> frozenset[str]:
    normalized: set[str] = set()
    if not isinstance(raw_numbers, (list, tuple, set, frozenset)):
        return frozenset()
    for item in raw_numbers:
        res = validate_us_phone_number(str(item), field_name="allowed_numbers")
        if res.valid and res.normalized:
            normalized.add(res.normalized)
    return frozenset(normalized)


def build_pre_tool_call_directive(
    tool_name: str,
    args: dict[str, Any] | None,
    *,
    require_approval: bool = True,
    allowed_numbers: Any = (),
    in_cron: bool = False,
) -> dict[str, Any] | None:
    """Return a real Hermes pre_tool_call directive: block, approve, or None (allow)."""
    if tool_name not in WRITE_TOOLS:
        return None

    safe_args = dict(args) if isinstance(args, dict) else {}
    allowlist = normalize_allowlist(allowed_numbers)

    if tool_name == "clawcall_place_call":
        validation = validate_us_phone_number(safe_args.get("to"), field_name="to")
        if not validation.valid or not validation.normalized:
            return {"action": "block", "message": f"ClawCall: {validation.error}"}
        normalized_to = validation.normalized

        if allowlist and normalized_to not in allowlist:
            return {
                "action": "block",
                "message": (
                    f"ClawCall: {normalized_to} is not in the configured allowed_numbers list."
                ),
            }

        if in_cron and normalized_to not in allowlist:
            return {
                "action": "block",
                "message": (
                    "ClawCall: a scheduled (cron) run cannot call a number outside allowed_numbers "
                    "because nobody is there to approve it."
                ),
            }

        if safe_args.get("from"):
            from_check = validate_us_phone_number(safe_args.get("from"), field_name="from")
            if not from_check.valid or not from_check.normalized:
                return {"action": "block", "message": f"ClawCall: {from_check.error}"}
            safe_args["from"] = from_check.normalized

        # Every number the call can ring passes the same checks as `to`.
        contacts = _handoff_contacts(safe_args)
        normalized_contacts: list[dict[str, Any]] = []
        for idx, contact in enumerate(contacts, start=1):
            field = f"handoff.contacts[{idx}].phone"
            check = validate_us_phone_number(contact.get("phone"), field_name=field)
            if not check.valid or not check.normalized:
                return {"action": "block", "message": f"ClawCall: {check.error}"}
            if (allowlist or in_cron) and check.normalized not in allowlist:
                reason = (
                    "a scheduled (cron) run cannot ring a hand-off number outside allowed_numbers "
                    "because nobody is there to approve it"
                    if in_cron and not allowlist
                    else "it is not in the configured allowed_numbers list"
                )
                return {
                    "action": "block",
                    "message": f"ClawCall: {field} {check.normalized} is refused: {reason}.",
                }
            normalized_contacts.append({**contact, "phone": check.normalized})
        if contacts:
            safe_args["handoff"] = {**safe_args["handoff"], "contacts": normalized_contacts}

        goal = str(safe_args.get("goal") or "").strip()
        if len(goal) > MAX_GOAL_CHARS:
            return {
                "action": "block",
                "message": (
                    f"ClawCall: the call goal is {len(goal)} characters; the limit is {MAX_GOAL_CHARS} "
                    "so the full brief fits in the approval prompt."
                ),
            }

        safe_args["to"] = normalized_to

    if in_cron and tool_name in ("clawcall_hangup_call", "clawcall_update_call_settings"):
        return {
            "action": "block",
            "message": (
                f"ClawCall: {tool_name} is refused during unattended scheduled runs because nobody can approve it."
            ),
        }

    if not require_approval:
        return None

    message, _ = build_approval_message(tool_name, safe_args)
    return {
        "action": "approve",
        "message": message,
        "rule_key": _rule_key(tool_name, message),
    }


class ApprovalGate:
    """Enforces explicit user approval before running write tools in direct invocations."""

    def __init__(
        self,
        *,
        approval_callback: ApprovalCallback | None = None,
        require_approval: bool = True,
    ) -> None:
        self._approval_callback = approval_callback
        self._require_approval = bool(require_approval)

    @property
    def require_approval(self) -> bool:
        return self._require_approval

    def requires_approval(self, tool_name: str) -> bool:
        return self._require_approval and tool_name in WRITE_TOOLS

    def check(
        self,
        tool_name: str,
        params: dict[str, Any] | None = None,
        *,
        approved: bool | None = None,
    ) -> None:
        """Verify approval for write tools; read tools pass without prompting."""
        if not self.requires_approval(tool_name):
            return

        safe_params = dict(params) if isinstance(params, dict) else {}
        summary, preview = build_approval_message(tool_name, safe_params)
        request = ApprovalRequest(
            tool_name=tool_name,
            scope="calls:write",
            summary=summary,
            preview=preview,
            rule_key=_rule_key(tool_name, summary),
        )

        if self._approval_callback is not None:
            decision = bool(self._approval_callback(request))
            if not decision:
                raise ApprovalDeniedError(
                    tool_name,
                    f"User approval was denied for '{tool_name}'. No external action was taken.",
                )
            return

        if approved is True:
            return

        raise ApprovalRequiredError(
            tool_name,
            (
                f"Tool '{tool_name}' requires explicit user approval through Hermes before execution. "
                f"Action: {summary}"
            ),
        )
