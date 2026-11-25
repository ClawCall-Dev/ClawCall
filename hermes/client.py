"""Zero-dependency HTTP client for ClawCall remote MCP and REST API.

This module never writes transcripts, call recordings, phone numbers, or keys to disk.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

try:
    from .config import ClawCallConfig, PLUGIN_NAME, PLUGIN_VERSION, TOOL_TO_MCP_NAME
except ImportError:  # pragma: no cover - direct module loading
    from config import ClawCallConfig, PLUGIN_NAME, PLUGIN_VERSION, TOOL_TO_MCP_NAME


class ClawCallClientError(RuntimeError):
    """Raised when ClawCall returns an API, MCP, or transport error."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "client_error",
        status_code: int | None = None,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.details = details


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: bytes | None = None
    follow_redirects: bool = True


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: dict[str, str]
    body: bytes


HttpTransport = Callable[[HttpRequest, float], HttpResponse]


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def _default_http_transport(req: HttpRequest, timeout_seconds: float) -> HttpResponse:
    urllib_req = Request(
        req.url,
        data=req.body,
        headers=req.headers,
        method=req.method,
    )
    opener = build_opener() if req.follow_redirects else build_opener(_NoRedirectHandler())
    try:
        with opener.open(urllib_req, timeout=timeout_seconds) as resp:
            headers = {k.lower(): v for k, v in resp.headers.items()}
            return HttpResponse(status=resp.status, headers=headers, body=resp.read())
    except HTTPError as err:
        headers = {k.lower(): v for k, v in err.headers.items()} if err.headers else {}
        body = err.read() if err.fp is not None else b""
        return HttpResponse(status=err.code, headers=headers, body=body)
    except URLError as err:
        raise ClawCallClientError(
            f"Network request to ClawCall failed: {err.reason}",
            code="network_error",
        ) from err


def _parse_json_or_sse(raw_body: bytes, content_type: str) -> Any:
    text = raw_body.decode("utf-8", errors="replace").strip()
    if not text:
        return {}
    if "text/event-stream" in content_type.lower():
        data_lines: list[str] = []
        for line in text.splitlines():
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload and payload != "[DONE]":
                    data_lines.append(payload)
        if not data_lines:
            return {}
        return json.loads(data_lines[-1])
    return json.loads(text)


def _extract_error(payload: Any, status_code: int) -> tuple[str, str]:
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            code = str(err.get("code") or f"http_{status_code}")
            message = str(err.get("message") or f"ClawCall request failed with HTTP {status_code}.")
            return code, message
        if isinstance(err, str):
            return f"http_{status_code}", err
        if "message" in payload:
            return str(payload.get("code") or f"http_{status_code}"), str(payload["message"])
    return f"http_{status_code}", f"ClawCall request failed with HTTP {status_code}."


class ClawCallClient:
    """In-memory ClawCall API client supporting remote MCP and REST fallback."""

    def __init__(
        self,
        config: ClawCallConfig,
        *,
        http_transport: HttpTransport | None = None,
    ) -> None:
        self._config = config
        self._transport = http_transport or _default_http_transport
        self._rpc_id = 0

    @property
    def config(self) -> ClawCallConfig:
        return self._config

    def _base_headers(self) -> dict[str, str]:
        return {
            "User-Agent": f"hermes-plugin-{PLUGIN_NAME}/{PLUGIN_VERSION}",
        }

    def _auth_headers(self, *, mode: str) -> dict[str, str]:
        if mode == "mcp":
            if self._config.access_token:
                return {"Authorization": f"Bearer {self._config.access_token}"}
            if self._config.api_key:
                return {"X-Api-Key": self._config.api_key}
            raise ClawCallClientError(
                (
                    "ClawCall MCP authentication is not configured. Run `hermes mcp login clawcall` "
                    "for OAuth 2.1 with PKCE, or set CLAWCALL_API_KEY for REST fallback."
                ),
                code="auth_required",
                status_code=401,
            )

        if self._config.api_key:
            return {"X-Api-Key": self._config.api_key}
        if self._config.access_token:
            return {"Authorization": f"Bearer {self._config.access_token}"}
        raise ClawCallClientError(
            (
                "CLAWCALL_API_KEY is required for ClawCall REST API calls, or use "
                "OAuth 2.1 with PKCE via remote MCP at https://api.clawcall.dev/mcp."
            ),
            code="auth_required",
            status_code=401,
        )

    def call_mcp_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke a tool on ClawCall's Streamable HTTP remote MCP endpoint."""
        self._rpc_id += 1
        rpc_payload = {
            "jsonrpc": "2.0",
            "id": self._rpc_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {},
            },
        }
        headers = {
            **self._base_headers(),
            **self._auth_headers(mode="mcp"),
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        resp = self._transport(
            HttpRequest(
                method="POST",
                url=self._config.mcp_url,
                headers=headers,
                body=json.dumps(rpc_payload).encode("utf-8"),
            ),
            self._config.timeout_seconds,
        )
        content_type = resp.headers.get("content-type", "application/json")
        try:
            parsed = _parse_json_or_sse(resp.body, content_type)
        except json.JSONDecodeError as err:
            raise ClawCallClientError(
                f"ClawCall MCP returned non-JSON response (HTTP {resp.status}).",
                code="invalid_response",
                status_code=resp.status,
            ) from err

        if resp.status >= 400:
            code, message = _extract_error(parsed, resp.status)
            raise ClawCallClientError(message, code=code, status_code=resp.status, details=parsed)

        if isinstance(parsed, dict) and "error" in parsed and parsed["error"]:
            code, message = _extract_error(parsed, resp.status)
            raise ClawCallClientError(message, code=code, status_code=resp.status, details=parsed["error"])

        result = parsed.get("result") if isinstance(parsed, dict) else parsed
        if isinstance(result, dict):
            if result.get("isError"):
                message = "ClawCall MCP tool returned an error."
                content = result.get("content")
                if isinstance(content, list) and content and isinstance(content[0], dict):
                    message = str(content[0].get("text") or message)
                raise ClawCallClientError(message, code="mcp_tool_error", status_code=resp.status, details=result)
            if "structuredContent" in result and result["structuredContent"] is not None:
                return result["structuredContent"]
            content = result.get("content")
            if isinstance(content, list) and len(content) == 1 and isinstance(content[0], dict):
                text = content[0].get("text")
                if isinstance(text, str):
                    try:
                        return json.loads(text)
                    except json.JSONDecodeError:
                        return {"text": text}
        return result

    def rest_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        follow_redirects: bool = True,
    ) -> HttpResponse:
        """Send an authenticated request to ClawCall's REST API."""
        url = f"{self._config.rest_base_url.rstrip('/')}{path}"
        if params:
            filtered = {k: v for k, v in params.items() if v is not None}
            if filtered:
                url = f"{url}?{urlencode(filtered)}"

        headers = {
            **self._base_headers(),
            **self._auth_headers(mode="rest"),
            "Accept": "application/json",
        }
        body_bytes: bytes | None = None
        if json_body is not None:
            headers["Content-Type"] = "application/json"
            body_bytes = json.dumps(json_body).encode("utf-8")

        return self._transport(
            HttpRequest(
                method=method,
                url=url,
                headers=headers,
                body=body_bytes,
                follow_redirects=follow_redirects,
            ),
            self._config.timeout_seconds,
        )

    def rest_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        resp = self.rest_request(method, path, params=params, json_body=json_body)
        try:
            parsed = json.loads(resp.body.decode("utf-8")) if resp.body else {}
        except json.JSONDecodeError as err:
            raise ClawCallClientError(
                f"ClawCall REST API returned non-JSON response (HTTP {resp.status}).",
                code="invalid_response",
                status_code=resp.status,
            ) from err

        if resp.status >= 400:
            code, message = _extract_error(parsed, resp.status)
            raise ClawCallClientError(message, code=code, status_code=resp.status, details=parsed)

        return parsed

    def execute_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Dispatch a tool over the configured transport (REST or remote MCP)."""
        args = dict(arguments or {})
        if self._config.transport == "mcp":
            mcp_name = TOOL_TO_MCP_NAME.get(tool_name, tool_name)
            return self.call_mcp_tool(mcp_name, args)
        return self._execute_rest_tool(tool_name, args)

    def _execute_rest_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        if tool_name == "clawcall_get_balance":
            return self.rest_json("GET", "/balance")

        if tool_name == "clawcall_place_call":
            return self.rest_json("POST", "/call", json_body=args)

        if tool_name == "clawcall_get_call":
            call_id = args["call_id"]
            return self.rest_json("GET", f"/call/{call_id}")

        if tool_name == "clawcall_get_call_transcript":
            call_id = args["call_id"]
            call_data = self.rest_json("GET", f"/call/{call_id}")
            return {
                "call_id": call_data.get("id", call_id),
                "lifecycle": call_data.get("lifecycle"),
                "outcome": call_data.get("outcome"),
                "transcript": call_data.get("transcript") or [],
            }

        if tool_name == "clawcall_list_calls":
            query = {
                "direction": args.get("direction"),
                "limit": args.get("limit"),
                "since": args.get("since"),
                "phone": args.get("phone"),
            }
            return self.rest_json("GET", "/me/calls", params=query)

        if tool_name == "clawcall_get_recording":
            call_id = args["call_id"]
            resp = self.rest_request(
                "GET",
                f"/call/{call_id}/recording",
                follow_redirects=False,
            )
            if resp.status in (301, 302, 303, 307, 308):
                location = resp.headers.get("location")
                if not location:
                    raise ClawCallClientError(
                        "Recording redirect did not include a Location URL.",
                        code="recording_not_available",
                        status_code=resp.status,
                    )
                return {
                    "call_id": call_id,
                    "recording_url": location,
                    "retention_minutes": 10,
                }
            if resp.status >= 400:
                parsed = json.loads(resp.body.decode("utf-8")) if resp.body else {}
                code, message = _extract_error(parsed, resp.status)
                raise ClawCallClientError(message, code=code, status_code=resp.status, details=parsed)
            return json.loads(resp.body.decode("utf-8")) if resp.body else {}

        if tool_name == "clawcall_hangup_call":
            call_id = args["call_id"]
            return self.rest_json("POST", f"/call/{call_id}/hangup")

        if tool_name == "clawcall_get_call_settings":
            return self.rest_json("GET", "/me/call-preferences")

        if tool_name == "clawcall_update_call_settings":
            return self.rest_json("PUT", "/me/call-preferences", json_body=args)

        raise ClawCallClientError(f"Unknown ClawCall tool: {tool_name}", code="unknown_tool")
