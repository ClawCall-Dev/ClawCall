"""Configuration builders, secret resolution, and constants for the ClawCall Hermes plugin."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

PLUGIN_NAME = "clawcall"
PLUGIN_VERSION = "1.0.0"

WEBSITE_URL = "https://clawcall.dev"
DEFAULT_MCP_URL = "https://api.clawcall.dev/mcp"
DEFAULT_REST_BASE_URL = "https://api.clawcall.dev"
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_GOAL_CHARS = 2000

MCP_TRANSPORT = "streamable-http"
MCP_AUTH_MODE = "oauth"
MCP_SCOPES: tuple[str, ...] = ("calls:read", "calls:write")

REST_API_KEY_ENV = "CLAWCALL_API_KEY"
OAUTH_ACCESS_TOKEN_ENV = "CLAWCALL_ACCESS_TOKEN"

# Canonical Hermes tool names (prefixed to avoid collisions) mapped to ClawCall MCP tool names.
TOOL_TO_MCP_NAME: dict[str, str] = {
    "clawcall_get_balance": "get_balance",
    "clawcall_place_call": "place_call",
    "clawcall_get_call": "get_call",
    "clawcall_get_call_transcript": "get_call_transcript",
    "clawcall_list_calls": "list_calls",
    "clawcall_get_recording": "get_recording",
    "clawcall_hangup_call": "hangup_call",
    "clawcall_get_call_settings": "get_call_settings",
    "clawcall_update_call_settings": "update_call_settings",
}

READ_TOOLS: frozenset[str] = frozenset(
    {
        "clawcall_get_balance",
        "clawcall_get_call",
        "clawcall_get_call_transcript",
        "clawcall_list_calls",
        "clawcall_get_recording",
        "clawcall_get_call_settings",
    }
)

WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "clawcall_place_call",
        "clawcall_hangup_call",
        "clawcall_update_call_settings",
    }
)

ALL_TOOLS: tuple[str, ...] = (
    "clawcall_get_balance",
    "clawcall_place_call",
    "clawcall_get_call",
    "clawcall_get_call_transcript",
    "clawcall_list_calls",
    "clawcall_get_recording",
    "clawcall_hangup_call",
    "clawcall_get_call_settings",
    "clawcall_update_call_settings",
)

SUPPORTED_VOICES: tuple[str, ...] = ("eric", "jessica", "sarah", "chris")

SUPPORTED_LANGUAGES: tuple[str, ...] = (
    "ar",
    "bn",
    "de",
    "en",
    "es",
    "fr",
    "he",
    "hi",
    "id",
    "it",
    "ja",
    "kn",
    "ko",
    "mr",
    "ms",
    "nl",
    "pl",
    "pt",
    "ta",
    "te",
    "th",
    "tl",
    "tr",
    "vi",
    "zh",
)

REST_ENDPOINTS: dict[str, dict[str, str]] = {
    "clawcall_get_balance": {"method": "GET", "path": "/balance"},
    "clawcall_place_call": {"method": "POST", "path": "/call"},
    "clawcall_get_call": {"method": "GET", "path": "/call/{call_id}"},
    "clawcall_get_call_transcript": {"method": "GET", "path": "/call/{call_id}"},
    "clawcall_list_calls": {"method": "GET", "path": "/me/calls"},
    "clawcall_get_recording": {"method": "GET", "path": "/call/{call_id}/recording"},
    "clawcall_hangup_call": {"method": "POST", "path": "/call/{call_id}/hangup"},
    "clawcall_get_call_settings": {"method": "GET", "path": "/me/call-preferences"},
    "clawcall_update_call_settings": {"method": "PUT", "path": "/me/call-preferences"},
}

CONFIG_DEFAULTS: dict[str, Any] = {
    "require_approval": True,
    "allowed_numbers": [],
    "transport": "rest",
    "timeout_seconds": 30,
}

SecretReader = Callable[[str], str]


def read_hermes_secret(name: str) -> str:
    """Read a declared secret strictly through Hermes's active profile secret scope.

    Never reads process environment variables directly or local credential files,
    preserving multi-profile isolation per Hermes catalog admission rule 11.
    """
    try:
        from agent.secret_scope import get_secret  # type: ignore[import-not-found]
    except ImportError:
        return ""
    try:
        return (get_secret(name) or "").strip()
    except Exception:
        # Unscoped read under multiplexing: treat as unset rather than borrowing another profile's key.
        return ""


def _validate_https_url(url: str, label: str) -> str:
    cleaned = url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{label} must be an https:// URL.")
    return cleaned


def build_mcp_config(
    *,
    url: str = DEFAULT_MCP_URL,
    enabled: bool = True,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return the Hermes config.yaml mcp_servers.clawcall configuration object."""
    normalized_url = _validate_https_url(url, "mcp_url")
    return {
        "name": PLUGIN_NAME,
        "url": normalized_url,
        "transport": MCP_TRANSPORT,
        "auth": MCP_AUTH_MODE,
        # Hermes asks before every write-capable tool on an untrusted server.
        "trust": "untrusted",
        "scopes": list(MCP_SCOPES),
        "enabled": bool(enabled),
        "timeout": float(timeout_seconds),
        "approval_required_tools": sorted(WRITE_TOOLS),
        "local_transcript_storage": False,
    }


def build_rest_config(
    *,
    base_url: str = DEFAULT_REST_BASE_URL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Return the ClawCall REST API configuration object."""
    normalized_base = _validate_https_url(base_url, "rest_base_url")
    return {
        "name": PLUGIN_NAME,
        "base_url": normalized_base,
        "auth_header": "X-Api-Key",
        "api_key_env": REST_API_KEY_ENV,
        "timeout": float(timeout_seconds),
        "endpoints": {name: dict(spec) for name, spec in REST_ENDPOINTS.items()},
        "approval_required_tools": sorted(WRITE_TOOLS),
        "local_transcript_storage": False,
    }


@dataclass(frozen=True)
class ClawCallConfig:
    """Runtime settings for the ClawCall Hermes plugin."""

    transport: str = "rest"
    mcp_url: str = DEFAULT_MCP_URL
    rest_base_url: str = DEFAULT_REST_BASE_URL
    api_key: str | None = None
    access_token: str | None = None
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    require_approval: bool = True
    allowed_numbers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.transport not in ("mcp", "rest"):
            raise ValueError("transport must be 'mcp' or 'rest'.")
        _validate_https_url(self.mcp_url, "mcp_url")
        _validate_https_url(self.rest_base_url, "rest_base_url")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero.")

    @classmethod
    def from_hermes(
        cls,
        *,
        get_config: Callable[[str, Any], Any] | None = None,
        secret_reader: SecretReader = read_hermes_secret,
        transport: str | None = None,
        require_approval: bool | None = None,
    ) -> "ClawCallConfig":
        """Build configuration from Hermes plugin settings and scoped secrets without touching disk."""
        cfg = get_config or (lambda key, default=None: default)
        api_key = secret_reader(REST_API_KEY_ENV).strip() or None
        access_token = secret_reader(OAUTH_ACCESS_TOKEN_ENV).strip() or None

        raw_transport = transport if transport is not None else cfg("transport", CONFIG_DEFAULTS["transport"])
        selected_transport = str(raw_transport or "rest").strip().lower()
        if selected_transport not in ("mcp", "rest"):
            selected_transport = "mcp" if access_token and not api_key else "rest"
        if transport is None and selected_transport == "rest" and not api_key and access_token:
            selected_transport = "mcp"

        raw_approval = (
            require_approval
            if require_approval is not None
            else cfg("require_approval", CONFIG_DEFAULTS["require_approval"])
        )
        raw_timeout = cfg("timeout_seconds", CONFIG_DEFAULTS["timeout_seconds"])
        try:
            timeout_val = float(raw_timeout)
            if timeout_val <= 0:
                timeout_val = DEFAULT_TIMEOUT_SECONDS
        except (TypeError, ValueError):
            timeout_val = DEFAULT_TIMEOUT_SECONDS

        raw_allowed = cfg("allowed_numbers", CONFIG_DEFAULTS["allowed_numbers"])
        # Keep every entry, valid or not: the allowlist check refuses a list with a bad entry
        # rather than silently dropping it (an emptied list would mean "no restriction").
        if raw_allowed is None:
            raw_items: list[Any] = []
        elif isinstance(raw_allowed, (list, tuple)):
            raw_items = list(raw_allowed)
        else:
            raw_items = [raw_allowed]
        allowed = tuple(str(item).strip() for item in raw_items)

        return cls(
            transport=selected_transport,
            mcp_url=DEFAULT_MCP_URL,
            rest_base_url=DEFAULT_REST_BASE_URL,
            api_key=api_key,
            access_token=access_token,
            timeout_seconds=timeout_val,
            require_approval=bool(True if raw_approval is None else raw_approval),
            allowed_numbers=allowed,
        )

    def to_mcp_config(self) -> dict[str, Any]:
        return build_mcp_config(
            url=self.mcp_url,
            timeout_seconds=self.timeout_seconds,
        )

    def to_rest_config(self) -> dict[str, Any]:
        return build_rest_config(
            base_url=self.rest_base_url,
            timeout_seconds=self.timeout_seconds,
        )
