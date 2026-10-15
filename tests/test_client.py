"""Python client matches the TypeScript harness: keys, redaction, retries."""

import json

import httpx

from jev_lab.client import DEFAULT_MODEL, TypeSafeError, load_api_key, system_one

FIXTURE_KEY = "apikey_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _isolate(monkeypatch, key_file: str = "/tmp/jev-test-no-key-file") -> None:
    monkeypatch.delenv("TYPESAFE_OFFLINE", raising=False)
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    monkeypatch.delenv("JEV_API_KEY", raising=False)
    monkeypatch.delenv("TYPESAFE_MODEL", raising=False)
    monkeypatch.setenv("TYPESAFE_KEY_FILE", key_file)


def test_default_model_is_pinned():
    assert DEFAULT_MODEL == "jev-1.13.0"


def test_offline_env_ignores_key(monkeypatch):
    monkeypatch.setenv("TYPESAFE_OFFLINE", "1")
    monkeypatch.setenv("TYPESAFE_API_KEY", "present-but-offline")
    assert load_api_key() == ""


def test_env_key_prefers_typesafe_over_jev(monkeypatch):
    _isolate(monkeypatch)
    monkeypatch.setenv("JEV_API_KEY", "from-jev")
    monkeypatch.setenv("TYPESAFE_API_KEY", "from-typesafe")
    assert load_api_key() == "from-typesafe"


def test_jev_env_key_when_typesafe_unset(monkeypatch):
    _isolate(monkeypatch)
    monkeypatch.setenv("JEV_API_KEY", "from-jev")
    assert load_api_key() == "from-jev"


def test_key_file_skips_comments(monkeypatch, tmp_path):
    key_file = tmp_path / "api_key"
    key_file.write_text("# comment\n\n  from-file  \nignored\n", encoding="utf-8")
    _isolate(monkeypatch, str(key_file))
    assert load_api_key() == "from-file"


def test_system_one_redacts_state_and_pins_model(monkeypatch):
    monkeypatch.delenv("TYPESAFE_MODEL", raising=False)
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.content.decode()
        seen["auth"] = request.headers["Authorization"]
        return httpx.Response(
            200,
            json={"model": "jev-1.13.0", "answers": {"ok": {"type": "noul", "noul": 1}}},
        )

    result = system_one(
        {"note": f"leak {FIXTURE_KEY}", "api_key": "super-secret-key-value"},
        {"ok": {"type": "noul", "instructions": "ok?"}},
        api_key="test-key-value",
        transport=httpx.MockTransport(handler),
        sleep=lambda _seconds: None,
    )
    body = seen["body"]
    assert FIXTURE_KEY not in body
    assert "apikey_" not in body
    assert "super-secret-key-value" not in body
    assert "test-key-value" not in body
    assert "[REDACTED]" in body
    assert json.loads(body)["model"] == "jev-1.13.0"
    assert seen["auth"] == "Bearer test-key-value"
    assert result["answers"]["ok"]["noul"] == 1


def test_system_one_retries_429_then_succeeds():
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "slow"}, headers={"retry-after": "0"})
        return httpx.Response(200, json={"model": "jev-1.13.0", "answers": {"x": {"type": "noul", "noul": 1}}})

    result = system_one(
        "hi",
        {"x": {"type": "noul", "instructions": "yes?"}},
        api_key="test-key-value",
        transport=httpx.MockTransport(handler),
        retries=2,
        sleep=lambda _seconds: None,
    )
    assert calls["n"] == 2
    assert result["answers"]["x"]["noul"] == 1


def test_system_one_error_does_not_echo_the_key():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": f"rejected {FIXTURE_KEY}"})

    try:
        system_one(
            "hi",
            {"x": {"type": "noul", "instructions": "yes?"}},
            api_key="test-key-value",
            transport=httpx.MockTransport(handler),
            sleep=lambda _seconds: None,
        )
    except TypeSafeError as exc:
        assert exc.status_code == 401
        assert FIXTURE_KEY not in exc.body
        assert "apikey_" not in str(exc)
        assert "[REDACTED]" in exc.body
    else:
        raise AssertionError("expected TypeSafeError")
