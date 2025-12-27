"""Theme and dashboard CSS behaviour tests."""
from __future__ import annotations

import re
from unittest.mock import patch

import pytest
import streamlit as st
from ui.themes import ElementStyle, ThemeConfig, apply_theme, get_theme, apply_plotly_theme


@pytest.fixture(autouse=True)
def reset_streamlit_state():
    # Provide a clean session state for each test
    with patch.object(st, "session_state", {}):
        yield


def test_theme_loading_shape():
    theme = get_theme("light")
    assert isinstance(theme, ThemeConfig)
    assert theme.id == "light"
    assert isinstance(theme.radio, ElementStyle)
    assert isinstance(theme.menu, ElementStyle)


def test_css_generation_includes_core_colors():
    css_output: list[str] = []

    def mock_markdown(content: str, unsafe_allow_html: bool = False):
        if unsafe_allow_html and "<style" in content:
            css_output.append(content)

    with patch.object(st, "markdown", side_effect=mock_markdown):
        apply_theme("light")

    assert css_output, "apply_theme should inject CSS"
    full_css = "\n".join(css_output)
    for pattern in [
        r"background-color:\s*#FFFFFF",  # radio background
        r"border-color:\s*#808080",      # radio border
        r"background-color:\s*#0078D4",  # radio active
        r"background-color:\s*#F0F2F6",  # menu background
    ]:
        assert re.search(pattern, full_css), f"Missing expected CSS fragment: {pattern}"


def test_theme_not_mutated_by_custom_colors():
    original_theme = get_theme("light")
    original_primary = original_theme.primary_color

    with patch.object(st, "markdown"):
        apply_theme("light", {"primary_color": "#FF0000"})

    current_theme = get_theme("light")
    assert current_theme.primary_color == original_primary


def test_custom_colors_flow_into_css():
    css_output: list[str] = []

    def mock_markdown(content: str, unsafe_allow_html: bool = False):
        if unsafe_allow_html and "<style" in content:
            css_output.append(content)

    custom = {
        "primary_color": "#AA0000",
        "background_color": "#101010",
        "secondary_background_color": "#202020",
        "text_color": "#BADA55",
    }

    with patch.object(st, "markdown", side_effect=mock_markdown):
        apply_theme("light", custom)

    full_css = "\n".join(css_output)
    assert "#AA0000" in full_css
    assert "#101010" in full_css
    assert "#202020" in full_css
    assert "#BADA55" in full_css


def test_dark_transparency_is_clamped():
    css_output: list[str] = []

    def mock_markdown(content: str, unsafe_allow_html: bool = False):
        if unsafe_allow_html and "<style" in content:
            css_output.append(content)

    st.session_state["settings"] = {
        "bg_opacity": 0.1,
        "content_opacity": 0.1,
        "sidebar_opacity": 0.1,
        "header_opacity": 0.1,
    }

    with patch.object(st, "markdown", side_effect=mock_markdown):
        apply_theme("dark")

    full_css = "\n".join(css_output)
    assert "rgba(14, 17, 23, 0.55)" in full_css  # main background clamped
    assert "rgba(38, 39, 48, 0.75)" in full_css  # header background clamped


def test_plotly_theme_respects_custom_colors():
    class DummyFig:
        def __init__(self):
            self.data = []
            self.layout_updates = {}

        def update_layout(self, **kwargs):
            self.layout_updates.update(kwargs)

    fig = DummyFig()
    custom = {
        "background_color": "#121212",
        "secondary_background_color": "#222222",
        "text_color": "#EEEEEE",
        "primary_color": "#FF0000",
    }

    apply_plotly_theme(fig, "light", custom)

    assert fig.layout_updates["paper_bgcolor"] == "#121212"
    assert fig.layout_updates["plot_bgcolor"] == "#222222"
    assert fig.layout_updates["font"]["color"] == "#EEEEEE"
