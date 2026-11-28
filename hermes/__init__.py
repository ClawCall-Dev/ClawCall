"""Hermes Agent marketplace plugin for ClawCall.

Exposes 9 approval-gated ``clawcall_*`` tools over ClawCall's REST API
(https://api.clawcall.dev) or remote MCP server (https://api.clawcall.dev/mcp),
a ``pre_tool_call`` hook that blocks non-US/emergency/premium-rate numbers and
routes write actions through Hermes's native approval prompt (failing closed on
unattended cron runs), and the bundled ``clawcall`` skill. Stores no transcripts
or recordings on local disk.
"""

from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Any, Callable

try:
    from .approval import (
        AllowlistError,
        ApprovalDeniedError,
        ApprovalGate,
        ApprovalRequest,
        ApprovalRequiredError,
        build_pre_tool_call_directive,
    )
    from .client import ClawCallClient, ClawCallClientError
    from .config import (
        ALL_TOOLS,
        CONFIG_DEFAULTS,
        ClawCallConfig,
        DEFAULT_MCP_URL,
        DEFAULT_REST_BASE_URL,
        OAUTH_ACCESS_TOKEN_ENV,
        PLUGIN_NAME,
        PLUGIN_VERSION,
        READ_TOOLS,
        REST_API_KEY_ENV,
        SecretReader,
        WRITE_TOOLS,
        build_mcp_config,
        build_rest_config,
        read_hermes_secret,
    )
    from .phone_guard import PhoneValidationError, assert_us_phone_number, validate_us_phone_number
    from .schemas import TOOL_METADATA, TOOL_SCHEMAS
    from .tools import ClawCallPlugin
except ImportError:  # pragma: no cover - direct module loading by Hermes plugin loader
    from approval import (
        AllowlistError,
        ApprovalDeniedError,
        ApprovalGate,
        ApprovalRequest,
        ApprovalRequiredError,
        build_pre_tool_call_directive,
    )
    from client import ClawCallClient, ClawCallClientError
    from config import (
        ALL_TOOLS,
        CONFIG_DEFAULTS,
        ClawCallConfig,
        DEFAULT_MCP_URL,
        DEFAULT_REST_BASE_URL,
        OAUTH_ACCESS_TOKEN_ENV,
        PLUGIN_NAME,
        PLUGIN_VERSION,
        READ_TOOLS,
        REST_API_KEY_ENV,
        SecretReader,
        WRITE_TOOLS,
        build_mcp_config,
        build_rest_config,
        read_hermes_secret,
    )
    from phone_guard import PhoneValidationError, assert_us_phone_number, validate_us_phone_number
    from schemas import TOOL_METADATA, TOOL_SCHEMAS
    from tools import ClawCallPlugin

__all__ = [
    "ALL_TOOLS",
    "AllowlistError",
    "ApprovalDeniedError",
    "ApprovalGate",
    "ApprovalRequest",
    "ApprovalRequiredError",
    "ClawCallClient",
    "ClawCallClientError",
    "ClawCallConfig",
    "ClawCallPlugin",
    "DEFAULT_MCP_URL",
    "DEFAULT_REST_BASE_URL",
    "PLUGIN_NAME",
    "PLUGIN_VERSION",
    "PhoneValidationError",
    "READ_TOOLS",
    "TOOL_METADATA",
    "TOOL_SCHEMAS",
    "WRITE_TOOLS",
    "assert_us_phone_number",
    "build_mcp_config",
    "build_pre_tool_call_directive",
    "build_rest_config",
    "read_hermes_secret",
    "register",
    "validate_us_phone_number",
]


def _resolve_context_approval_callback(ctx: Any):
    for attr in ("approval_callback", "request_approval"):
        candidate = getattr(ctx, attr, None)
        if callable(candidate):
            return candidate
    return None


def _resolve_get_config(ctx: Any) -> Callable[[str, Any], Any]:
    candidate = getattr(ctx, "get_config", None)
    if callable(candidate):
        return candidate
    return lambda key, default=None: default


def _is_in_cron(ctx: Any) -> bool:
    lookup = getattr(ctx, "current_cron_execution", None)
    if not callable(lookup):
        return False
    try:
        return lookup() is not None
    except Exception:
        # Unknown execution context means unattended: fail closed.
        return True


def _build_hermes_handler(
    *,
    ctx: Any,
    tool_name: str,
    explicit_config: ClawCallConfig | None,
    secret_reader: SecretReader,
    http_transport: Any,
    hook_registered: bool,
):
    approval_callback = _resolve_context_approval_callback(ctx)
    get_config = _resolve_get_config(ctx)

    def _handler(args: dict[str, Any] | None = None, **kwargs: Any) -> str:
        # Build per-call config from active Hermes profile secret scope (Rule 11).
        runtime_config = explicit_config or ClawCallConfig.from_hermes(
            get_config=get_config,
            secret_reader=secret_reader,
        )
        # Re-apply every block rule here (destination, hand-off numbers, allowlist, cron) so they
        # hold even when the pre_tool_call hook did not run: a host without register_hook, or a
        # hook that raised and was skipped.
        blocked = build_pre_tool_call_directive(
            tool_name,
            args if isinstance(args, dict) else {},
            require_approval=False,
            allowed_numbers=runtime_config.allowed_numbers,
            in_cron=_is_in_cron(ctx),
        )
        if blocked is not None:
            return json.dumps(
                {
                    "ok": False,
                    "tool": tool_name,
                    "error": {"code": "blocked", "message": blocked.get("message", "ClawCall: refused.")},
                }
            )

        # Hermes's pre_tool_call prompt is the approval. Treat a write as approved only when that
        # hook is registered; otherwise the approval gate asks for an explicit flag or callback.
        approved = kwargs.get("approved")
        if approved is None and "user_approved" in kwargs:
            approved = kwargs.get("user_approved")
        if approved is None and approval_callback is None and hook_registered:
            approved = True

        plugin = ClawCallPlugin(
            config=runtime_config,
            approval_callback=approval_callback,
            http_transport=http_transport,
        )
        try:
            result = plugin.invoke(tool_name, args or {}, approved=approved)
            return json.dumps({"ok": True, "tool": tool_name, "result": result})
        except (PhoneValidationError, AllowlistError, ApprovalRequiredError, ApprovalDeniedError, ClawCallClientError) as err:
            return json.dumps(
                {
                    "ok": False,
                    "tool": tool_name,
                    "error": {
                        "code": getattr(err, "code", "clawcall_error"),
                        "message": str(err),
                    },
                }
            )
        except ValueError as err:
            return json.dumps(
                {
                    "ok": False,
                    "tool": tool_name,
                    "error": {
                        "code": "invalid_request",
                        "message": str(err),
                    },
                }
            )

    _handler.__name__ = f"handle_{tool_name}"
    return _handler


def register(
    ctx: Any,
    *,
    config: ClawCallConfig | None = None,
    secret_reader: SecretReader = read_hermes_secret,
    http_transport: Any = None,
) -> ClawCallPlugin:
    """Hermes Agent plugin entry point. Registers all 9 clawcall_* tools, pre_tool_call hook, and skill."""
    get_config = _resolve_get_config(ctx)
    approval_callback = _resolve_context_approval_callback(ctx)
    initial_config = config or ClawCallConfig.from_hermes(
        get_config=get_config,
        secret_reader=secret_reader,
    )
    plugin = ClawCallPlugin(
        config=initial_config,
        approval_callback=approval_callback,
        http_transport=http_transport,
    )

    def _has_credentials() -> bool:
        if config is not None:
            return bool(config.api_key or config.access_token)
        return bool(secret_reader(REST_API_KEY_ENV) or secret_reader(OAUTH_ACCESS_TOKEN_ENV))

    register_tool_fn = ctx.register_tool
    try:
        sig = inspect.signature(register_tool_fn)
        accepted_kwargs = set(sig.parameters.keys())
        accepts_var_kwargs = any(
            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
        )
    except (TypeError, ValueError):
        accepted_kwargs = set()
        accepts_var_kwargs = True

    register_hook_fn = getattr(ctx, "register_hook", None)
    hook_registered = callable(register_hook_fn)

    for tool_name in ALL_TOOLS:
        schema = TOOL_SCHEMAS[tool_name]
        handler = _build_hermes_handler(
            ctx=ctx,
            tool_name=tool_name,
            explicit_config=config,
            secret_reader=secret_reader,
            http_transport=http_transport,
            hook_registered=hook_registered,
        )

        call_kwargs: dict[str, Any] = {
            "name": tool_name,
            "toolset": PLUGIN_NAME,
            "schema": schema,
            "handler": handler,
        }
        if accepts_var_kwargs or "check_fn" in accepted_kwargs:
            call_kwargs["check_fn"] = _has_credentials
        if accepts_var_kwargs or "emoji" in accepted_kwargs:
            call_kwargs["emoji"] = "\U0001f4de"

        register_tool_fn(**call_kwargs)

    if hook_registered:
        def _pre_tool_call(
            tool_name: str = "",
            args: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> dict[str, Any] | None:
            resolved_name = tool_name or str(kwargs.get("name") or "")
            resolved_args = args if args is not None else kwargs.get("arguments") or kwargs.get("params")
            raw_require = get_config("require_approval", CONFIG_DEFAULTS["require_approval"])
            require_approval = bool(
                initial_config.require_approval if config is not None else (True if raw_require is None else raw_require)
            )
            allowed_numbers = (
                initial_config.allowed_numbers
                if config is not None
                else get_config("allowed_numbers", CONFIG_DEFAULTS["allowed_numbers"])
            )
            return build_pre_tool_call_directive(
                resolved_name,
                resolved_args if isinstance(resolved_args, dict) else {},
                require_approval=require_approval,
                allowed_numbers=allowed_numbers,
                in_cron=_is_in_cron(ctx),
            )

        register_hook_fn("pre_tool_call", _pre_tool_call)

    register_skill_fn = getattr(ctx, "register_skill", None)
    if callable(register_skill_fn):
        skill_path = Path(__file__).parent / "skills" / "clawcall" / "SKILL.md"
        if skill_path.is_file():
            register_skill_fn(PLUGIN_NAME, skill_path)

    return plugin
