import json
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import streamlit as st
import pytest

from ui.auth import StreamlitAuth
from ui.dashboard import (
    initialize_settings,
    save_settings,
    reset_settings,
    DEFAULT_SETTINGS,
)


@pytest.fixture(autouse=True)
def _reset_session_state():
    st.session_state.clear()
    yield
    st.session_state.clear()


def test_dev_mode_is_authenticated():
    StreamlitAuth.initialize()
    st.session_state[StreamlitAuth.SESSION_AUTH_MODE] = "development"

    assert StreamlitAuth.is_authenticated() is True


def test_production_requires_token():
    StreamlitAuth.initialize()
    st.session_state[StreamlitAuth.SESSION_AUTH_MODE] = "production"

    assert StreamlitAuth.is_authenticated() is False


def test_expired_token_triggers_logout(monkeypatch):
    StreamlitAuth.initialize()
    st.session_state[StreamlitAuth.SESSION_AUTH_MODE] = "production"
    st.session_state[StreamlitAuth.SESSION_TOKEN] = "expired-token"
    st.session_state[StreamlitAuth.SESSION_USER] = {"username": "alice"}
    st.session_state[StreamlitAuth.SESSION_LOGIN_TIME] = datetime.now() - timedelta(hours=25)

    logout_calls = {}

    def fake_logout(reason=None):
        logout_calls["reason"] = reason
        st.session_state.update({
            StreamlitAuth.SESSION_TOKEN: None,
            StreamlitAuth.SESSION_USER: None,
            StreamlitAuth.SESSION_LOGIN_TIME: None,
            StreamlitAuth.SESSION_AUTH_NOTICE: reason,
        })

    monkeypatch.setattr(StreamlitAuth, "logout", fake_logout)

    assert StreamlitAuth.is_authenticated() is False
    assert st.session_state[StreamlitAuth.SESSION_TOKEN] is None
    assert st.session_state[StreamlitAuth.SESSION_USER] is None
    assert "expired" in logout_calls.get("reason", "").lower()
    assert "expired" in st.session_state[StreamlitAuth.SESSION_AUTH_NOTICE].lower()


def test_get_auth_header_returns_bearer():
    StreamlitAuth.initialize()
    st.session_state[StreamlitAuth.SESSION_TOKEN] = "abc123"

    assert StreamlitAuth.get_auth_header() == {"Authorization": "Bearer abc123"}


def test_initialize_settings_prefers_api_over_defaults(monkeypatch):
    # Force authenticated state so dashboard pulls from API
    monkeypatch.setattr(StreamlitAuth, "is_authenticated", lambda: True)

    def fake_get(url, headers=None, timeout=5):
        return SimpleNamespace(
            status_code=200,
            json=lambda: {"preferences": {"theme": "dark", "animation_enabled": True}},
        )

    monkeypatch.setattr("requests.get", fake_get)

    initialize_settings()

    assert st.session_state.settings["theme"] == "dark"
    assert st.session_state.settings["animation_enabled"] is True


def test_save_settings_writes_local_and_api(monkeypatch, tmp_path):
    st.session_state.settings = {"theme": "matrix", "animation_enabled": True}

    # Ensure authentication path is used
    monkeypatch.setattr(StreamlitAuth, "is_authenticated", lambda: True)
    monkeypatch.setattr(StreamlitAuth, "get_auth_header", lambda: {"Authorization": "Bearer test"})

    # Redirect Path.home() to temporary directory to avoid touching real filesystem
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    def fake_put(url, headers=None, json=None, timeout=5):
        return SimpleNamespace(status_code=200, json=lambda: {"ok": True})

    monkeypatch.setattr("requests.put", fake_put)

    success, message = save_settings()

    settings_file = tmp_path / ".polisim" / "settings.json"

    assert success is True
    assert settings_file.exists()
    on_disk = json.loads(settings_file.read_text())
    assert on_disk["theme"] == "matrix"
    assert "failed" not in message.lower()


def test_reset_settings_resets_session_local_and_api(monkeypatch, tmp_path):
    st.session_state.settings = {"theme": "matrix", "animation_enabled": True}

    monkeypatch.setattr(StreamlitAuth, "is_authenticated", lambda: True)
    monkeypatch.setattr(StreamlitAuth, "get_auth_header", lambda: {"Authorization": "Bearer test"})
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    api_called = {"post": False}

    def fake_post(url, headers=None, timeout=5):
        api_called["post"] = True
        assert "preferences/reset" in url
        return SimpleNamespace(status_code=200)

    monkeypatch.setattr("requests.post", fake_post)

    success, message = reset_settings()

    settings_file = tmp_path / ".polisim" / "settings.json"

    assert success is True
    assert settings_file.exists()
    on_disk = json.loads(settings_file.read_text())
    assert on_disk["theme"] == DEFAULT_SETTINGS["theme"]
    assert api_called["post"] is True
    assert "failed" not in message.lower()


def test_logout_sets_notice_and_clears_session(monkeypatch):
    StreamlitAuth.initialize()
    st.session_state.update({
        StreamlitAuth.SESSION_TOKEN: "abc",
        StreamlitAuth.SESSION_USER: {"username": "sam"},
        StreamlitAuth.SESSION_LOGIN_TIME: datetime.now(),
    })

    monkeypatch.setattr(st, "rerun", lambda: None)

    StreamlitAuth.logout(reason="Manual logout")

    assert st.session_state[StreamlitAuth.SESSION_TOKEN] is None
    assert st.session_state[StreamlitAuth.SESSION_USER] is None
    assert st.session_state[StreamlitAuth.SESSION_AUTH_NOTICE] == "Manual logout"
