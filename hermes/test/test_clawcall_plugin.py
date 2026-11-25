"""Offline unit tests for the ClawCall Hermes Agent marketplace plugin."""

from __future__ import annotations

import builtins
import json
from pathlib import Path
import re
import sys
import tempfile
import types
import unittest
from unittest import mock

PLUGIN_DIR = Path(__file__).resolve().parents[1]
if str(PLUGIN_DIR.parent) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR.parent))

import importlib.util  # noqa: E402


def _load_plugin_package():
    spec = importlib.util.spec_from_file_location(
        "hermes_clawcall",
        PLUGIN_DIR / "__init__.py",
        submodule_search_locations=[str(PLUGIN_DIR)],
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["hermes_clawcall"] = module
    spec.loader.exec_module(module)
    return module


hc = _load_plugin_package()
from hermes_clawcall.client import HttpRequest, HttpResponse  # noqa: E402


def _sample_call_payload(to: str = "+14155550199") -> dict:
    return {
        "to": to,
        "recipient": "Main Street Dental",
        "on_behalf_of": "Alex Rivera",
        "goal": "Confirm the dental cleaning appointment tomorrow at 2:00 PM.",
        "authority": {"allow": []},
        "questions": ["Is the appointment confirmed?"],
    }


def _fake_transport_factory(responses: list[HttpResponse] | None = None):
    recorded: list[tuple[HttpRequest, float]] = []
    queue = list(responses or [])

    def _transport(req: HttpRequest, timeout_seconds: float) -> HttpResponse:
        recorded.append((req, timeout_seconds))
        if queue:
            return queue.pop(0)
        return HttpResponse(
            status=200,
            headers={"content-type": "application/json"},
            body=json.dumps({"ok": True}).encode("utf-8"),
        )

    return _transport, recorded


class TestPhoneGuard(unittest.TestCase):
    def test_valid_us_numbers_pass_and_normalize(self) -> None:
        for raw, expected in [
            ("+14155550123", "+14155550123"),
            ("+1 (212) 555-0144", "+12125550144"),
            ("+1-650-555-0198", "+16505550198"),
            ("+1 310.555.0182", "+13105550182"),
        ]:
            result = hc.validate_us_phone_number(raw)
            self.assertTrue(result.valid, f"Expected {raw} to be valid: {result.error}")
            self.assertEqual(result.normalized, expected)

    def test_international_numbers_refused_with_us_scope_message(self) -> None:
        for raw in ["+442079460958", "+919876543210", "+33142685300", "+61293744000", "011442079460958"]:
            result = hc.validate_us_phone_number(raw)
            self.assertFalse(result.valid, f"Expected international number {raw} to fail")
            self.assertEqual(result.code, "unsupported_destination")
            self.assertIn("US +1", result.error or "")

    def test_non_us_nanp_area_codes_refused(self) -> None:
        for raw in ["+14165550123", "+16045550199", "+15145550111", "+12425550122", "+18765550101"]:
            result = hc.validate_us_phone_number(raw)
            self.assertFalse(result.valid, f"Expected non-US NANP {raw} to fail")
            self.assertEqual(result.code, "unsupported_destination")
            self.assertIn("US +1", result.error or "")

    def test_emergency_and_n11_numbers_refused(self) -> None:
        for raw in ["911", "988", "411", "311", "211", "511", "611", "711", "811", "+1911", "+1988", "112", "999", "000", "+19115550123", "+14159110123"]:
            result = hc.validate_us_phone_number(raw)
            self.assertFalse(result.valid, f"Expected emergency/N11 {raw} to fail")
            self.assertEqual(result.code, "emergency_number_blocked")

    def test_premium_rate_numbers_refused(self) -> None:
        for raw in ["+19005550123", "+19765550123", "+14159760123"]:
            result = hc.validate_us_phone_number(raw)
            self.assertFalse(result.valid, f"Expected premium-rate {raw} to fail")
            self.assertEqual(result.code, "premium_number_blocked")

    def test_invalid_area_codes_and_formats_refused(self) -> None:
        for raw in ["+10125550123", "+11235550123", "+14150550123", "+14151550123", "4155550123", "+141555501", "", "   "]:
            result = hc.validate_us_phone_number(raw)
            self.assertFalse(result.valid, f"Expected invalid number {raw!r} to fail")

    def test_handoff_contact_numbers_are_also_guarded(self) -> None:
        transport, recorded = _fake_transport_factory()
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        payload = _sample_call_payload()
        payload["handoff"] = {"contacts": [{"name": "UK Office", "phone": "+442079460958"}]}
        with self.assertRaises(hc.PhoneValidationError):
            plugin.place_call(payload, approved=True)
        self.assertEqual(recorded, [])


class TestApprovalGateAndPreToolCall(unittest.TestCase):
    def test_write_tools_blocked_without_approval_and_no_network_request_sent(self) -> None:
        transport, recorded = _fake_transport_factory()
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        with self.assertRaises(hc.ApprovalRequiredError):
            plugin.place_call(_sample_call_payload())
        with self.assertRaises(hc.ApprovalRequiredError):
            plugin.hangup_call("call_123")
        with self.assertRaises(hc.ApprovalRequiredError):
            plugin.update_call_settings({"voice": "sarah"})
        self.assertEqual(recorded, [])

    def test_write_tools_blocked_when_callback_denies(self) -> None:
        transport, recorded = _fake_transport_factory()
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        seen_requests: list[hc.ApprovalRequest] = []

        def _deny(req: hc.ApprovalRequest) -> bool:
            seen_requests.append(req)
            return False

        plugin = hc.ClawCallPlugin(config=cfg, approval_callback=_deny, http_transport=transport)
        with self.assertRaises(hc.ApprovalDeniedError):
            plugin.place_call(_sample_call_payload())
        self.assertEqual(len(seen_requests), 1)
        self.assertEqual(seen_requests[0].tool_name, "clawcall_place_call")
        self.assertTrue(seen_requests[0].rule_key.startswith("clawcall:clawcall_place_call:"))
        self.assertEqual(recorded, [])

    def test_write_tools_succeed_when_approved_by_flag_or_callback(self) -> None:
        transport, recorded = _fake_transport_factory(
            [
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"call_id": "call_1"}).encode()),
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"status": "ended"}).encode()),
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"ok": True}).encode()),
            ]
        )
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, approval_callback=lambda _req: True, http_transport=transport)

        self.assertEqual(plugin.place_call(_sample_call_payload())["call_id"], "call_1")
        self.assertEqual(plugin.hangup_call("call_1")["status"], "ended")
        self.assertTrue(plugin.update_call_settings({"voice": "eric"})["ok"])
        self.assertEqual(len(recorded), 3)

    def test_read_tools_work_without_write_approval(self) -> None:
        transport, recorded = _fake_transport_factory(
            [
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"plan": "unlimited"}).encode()),
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"id": "c1", "outcome": "answered"}).encode()),
            ]
        )
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        self.assertEqual(plugin.get_balance()["plan"], "unlimited")
        self.assertEqual(plugin.get_call("c1")["outcome"], "answered")
        self.assertEqual(len(recorded), 2)

    def test_pre_tool_call_returns_real_hermes_directives_and_fails_closed_in_cron(self) -> None:
        # Read tool returns None (allow without approval).
        self.assertIsNone(hc.build_pre_tool_call_directive("clawcall_get_balance", {}))

        # Write tool returns real Hermes {"action": "approve", "message": ..., "rule_key": ...}.
        directive = hc.build_pre_tool_call_directive("clawcall_place_call", _sample_call_payload())
        assert directive is not None
        self.assertEqual(directive["action"], "approve")
        self.assertIn("+14155550199", directive["message"])
        self.assertIn("Main Street Dental", directive["message"])
        self.assertTrue(directive["rule_key"].startswith("clawcall:clawcall_place_call:"))

        # Invalid/emergency/non-US number returns {"action": "block", ...}.
        blocked_intl = hc.build_pre_tool_call_directive("clawcall_place_call", _sample_call_payload("+442079460958"))
        assert blocked_intl is not None
        self.assertEqual(blocked_intl["action"], "block")

        blocked_911 = hc.build_pre_tool_call_directive("clawcall_place_call", _sample_call_payload("911"))
        assert blocked_911 is not None
        self.assertEqual(blocked_911["action"], "block")

        # Unattended cron run fails closed unless number is in allowed_numbers.
        blocked_cron = hc.build_pre_tool_call_directive(
            "clawcall_place_call", _sample_call_payload("+14155550199"), in_cron=True, allowed_numbers=[]
        )
        assert blocked_cron is not None
        self.assertEqual(blocked_cron["action"], "block")
        self.assertIn("scheduled", blocked_cron["message"])

        # Allowed number inside cron run passes block check (when require_approval=False).
        allowed_cron = hc.build_pre_tool_call_directive(
            "clawcall_place_call",
            _sample_call_payload("+14155550199"),
            require_approval=False,
            in_cron=True,
            allowed_numbers=["+14155550199"],
        )
        self.assertIsNone(allowed_cron)


class TestSecretScopeRule11(unittest.TestCase):
    def test_read_hermes_secret_uses_agent_secret_scope_and_not_os_environ(self) -> None:
        fake_agent_pkg = types.ModuleType("agent")
        fake_secret_scope = types.ModuleType("agent.secret_scope")
        seen_names: list[str] = []

        def _fake_get_secret(name: str) -> str:
            seen_names.append(name)
            return "clawcall_sk_from_scope" if name == "CLAWCALL_API_KEY" else ""

        fake_secret_scope.get_secret = _fake_get_secret  # type: ignore[attr-defined]
        fake_agent_pkg.secret_scope = fake_secret_scope  # type: ignore[attr-defined]

        with mock.patch.dict(
            sys.modules,
            {"agent": fake_agent_pkg, "agent.secret_scope": fake_secret_scope},
        ):
            with mock.patch.dict("os.environ", {"CLAWCALL_API_KEY": "clawcall_sk_wrong_env"}):
                cfg = hc.ClawCallConfig.from_hermes()

        self.assertEqual(cfg.api_key, "clawcall_sk_from_scope")
        self.assertIn("CLAWCALL_API_KEY", seen_names)


class TestConfigAndTransports(unittest.TestCase):
    def test_mcp_and_rest_config_objects_match_canonical_endpoints(self) -> None:
        mcp_cfg = hc.build_mcp_config()
        self.assertEqual(mcp_cfg["url"], "https://api.clawcall.dev/mcp")
        self.assertEqual(mcp_cfg["transport"], "streamable-http")
        self.assertEqual(mcp_cfg["auth"], "oauth")
        self.assertEqual(mcp_cfg["scopes"], ["calls:read", "calls:write"])
        self.assertFalse(mcp_cfg["local_transcript_storage"])

        rest_cfg = hc.build_rest_config()
        self.assertEqual(rest_cfg["base_url"], "https://api.clawcall.dev")
        self.assertEqual(rest_cfg["auth_header"], "X-Api-Key")
        self.assertEqual(rest_cfg["api_key_env"], "CLAWCALL_API_KEY")
        self.assertFalse(rest_cfg["local_transcript_storage"])

    def test_mcp_transport_maps_prefixed_tool_to_canonical_mcp_name(self) -> None:
        sse_body = (
            "event: message\n"
            'data: {"jsonrpc":"2.0","id":1,"result":{"structuredContent":{"plan":"unlimited","unlimited":true}}}\n\n'
        ).encode("utf-8")
        transport, recorded = _fake_transport_factory(
            [HttpResponse(200, {"content-type": "text/event-stream"}, sse_body)]
        )
        cfg = hc.ClawCallConfig(transport="mcp", access_token="oauth_tok_123")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        result = plugin.get_balance()
        self.assertTrue(result["unlimited"])
        self.assertEqual(recorded[0][0].url, "https://api.clawcall.dev/mcp")
        body_json = json.loads((recorded[0][0].body or b"{}").decode("utf-8"))
        self.assertEqual(body_json["params"]["name"], "get_balance")

    def test_rest_transport_hits_canonical_rest_base_url(self) -> None:
        transport, recorded = _fake_transport_factory(
            [HttpResponse(200, {"content-type": "application/json"}, json.dumps({"calls": []}).encode())]
        )
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        result = plugin.list_calls(direction="outbound", limit=5)
        self.assertEqual(result, {"calls": []})
        self.assertEqual(recorded[0][0].url, "https://api.clawcall.dev/me/calls?direction=outbound&limit=5")
        self.assertEqual(recorded[0][0].headers["X-Api-Key"], "clawcall_sk_test")


class TestZeroLocalTranscriptStorage(unittest.TestCase):
    def test_simulated_call_and_transcript_writes_zero_files_to_disk(self) -> None:
        transcript_payload = {
            "id": "call_abc",
            "lifecycle": "finalized",
            "outcome": "answered",
            "transcript": [
                {"speaker": "business", "text": "Main Street Dental, how can I help?"},
                {"speaker": "ai", "text": "Hi, calling to confirm Alex Rivera's appointment."},
            ],
        }
        transport, _ = _fake_transport_factory(
            [
                HttpResponse(200, {"content-type": "application/json"}, json.dumps({"call_id": "call_abc"}).encode()),
                HttpResponse(200, {"content-type": "application/json"}, json.dumps(transcript_payload).encode()),
            ]
        )
        cfg = hc.ClawCallConfig(transport="rest", api_key="clawcall_sk_test")
        plugin = hc.ClawCallPlugin(config=cfg, http_transport=transport)

        write_opens: list[tuple[str, str]] = []
        real_open = builtins.open

        def _spy_open(file, mode="r", *args, **kwargs):
            if any(flag in str(mode) for flag in ("w", "a", "x", "+")):
                write_opens.append((str(file), str(mode)))
            return real_open(file, mode, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmpdir:
            with mock.patch("builtins.open", side_effect=_spy_open):
                call_res = plugin.place_call(_sample_call_payload(), approved=True)
                transcript_res = plugin.get_call_transcript(call_res["call_id"])

            self.assertEqual(len(transcript_res["transcript"]), 2)
            self.assertEqual(write_opens, [])
            self.assertEqual(list(Path(tmpdir).rglob("*")), [])


class TestHermesCatalogAdmissionContract(unittest.TestCase):
    def test_recording_probe_matches_plugin_yaml_and_catalog_entry_exactly(self) -> None:
        """Simulates Hermes's `hermes plugins validate` capability probe and manifest checks."""
        import yaml

        manifest = yaml.safe_load((PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8"))
        catalog_path = PLUGIN_DIR / "plugin-catalog-entry.yaml"
        catalog = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) if catalog_path.is_file() else None

        # Check required plugin.yaml fields and Hermes flat config_schema contract.
        for key in ("name", "version", "description"):
            self.assertTrue(manifest.get(key), f"plugin.yaml missing {key}")
        self.assertEqual(manifest["manifest_version"], 2)
        self.assertEqual(manifest["api_version"], 1)

        allowed_config_types = {"str", "string", "int", "integer", "float", "number", "bool", "boolean", "list", "dict", "secret"}
        for cfg_key, cfg_spec in manifest["config_schema"].items():
            self.assertIsInstance(cfg_spec, dict, f"config_schema.{cfg_key} must be a mapping")
            self.assertIn(str(cfg_spec["type"]).lower(), allowed_config_types)

        for env_entry in manifest["requires_env"]:
            self.assertRegex(env_entry["name"], r"^[A-Z][A-Z0-9_]*$")

        # Simulate Hermes RecordingContext probe.
        registered_tools: list[str] = []
        registered_hooks: dict[str, object] = {}
        registered_skills: list[tuple[str, Path]] = []

        class _RecordingCtx:
            def get_config(self, key: str, default=None):
                return default

            def current_cron_execution(self):
                return None

            def register_tool(self, *, name, toolset, schema, handler, check_fn=None, emoji=None):
                registered_tools.append(name)

            def register_hook(self, event_name, fn):
                registered_hooks[event_name] = fn

            def register_skill(self, name, path):
                registered_skills.append((name, Path(path)))

        ctx = _RecordingCtx()
        hc.register(ctx, secret_reader=lambda _k: "clawcall_sk_test")

        # Rule 6: declared capabilities must match actual registrations 1:1.
        self.assertEqual(set(registered_tools), set(manifest["provides_tools"]))
        self.assertEqual(set(registered_hooks.keys()), set(manifest["provides_hooks"]))
        self.assertEqual(len(registered_skills), 1)
        self.assertEqual(registered_skills[0][0], "clawcall")
        self.assertTrue(registered_skills[0][1].is_file())

        # Catalog entry matches plugin.yaml and Hermes catalog_entry_fields rules when present.
        if catalog is not None:
            self.assertEqual(catalog["name"], manifest["name"])
            self.assertEqual(catalog["version"], manifest["version"])
            self.assertEqual(catalog["requires_hermes"], manifest["requires_hermes"])
            self.assertEqual(catalog["tier"], "community")
            self.assertEqual(catalog["capabilities"]["provides_tools"], manifest["provides_tools"])
            self.assertEqual(catalog["capabilities"]["provides_hooks"], manifest["provides_hooks"])
            self.assertEqual(catalog["capabilities"]["provides_middleware"], [])
            self.assertEqual(catalog["capabilities"]["requires_env"], ["CLAWCALL_API_KEY"])
            self.assertRegex(catalog["repo"], r"^https://\S+$")
            self.assertRegex(catalog["subdir"], r"^[A-Za-z0-9._/-]+$")
            self.assertNotIn("..", catalog["subdir"])
            self.assertIn("Disclosure:", catalog["description"])

        # Hook behaves per real Hermes contract.
        hook = registered_hooks["pre_tool_call"]
        self.assertEqual(hook("clawcall_place_call", _sample_call_payload())["action"], "approve")
        self.assertEqual(hook("clawcall_place_call", _sample_call_payload("911"))["action"], "block")
        self.assertIsNone(hook("clawcall_get_balance", {}))

    def test_no_em_dashes_and_no_bare_os_environ_in_plugin_code(self) -> None:
        for path in [
            PLUGIN_DIR / "plugin.yaml",
            PLUGIN_DIR / "plugin-catalog-entry.yaml",
            PLUGIN_DIR / "LISTING.md",
            PLUGIN_DIR / "README.md",
            PLUGIN_DIR / "skills" / "clawcall" / "SKILL.md",
        ]:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\u2014", text, f"Found em dash in {path.name}")

        for py_path in PLUGIN_DIR.glob("*.py"):
            source = py_path.read_text(encoding="utf-8")
            self.assertIsNone(
                re.search(r"\bos\.environ\b", source),
                f"Found bare os.environ read in {py_path.name}; use agent.secret_scope.get_secret instead (Rule 11)",
            )


if __name__ == "__main__":
    unittest.main()
