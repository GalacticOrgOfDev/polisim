"""Manual Streamlit check for Matrix animation rendering.

This test is skipped by default because it requires a running Streamlit
session to visually confirm the animation. Keep it as a reminder of the
manual check flow.
"""
import pytest

pytest.importorskip("streamlit")
pytest.importorskip("ui.animations")


@pytest.mark.skip(reason="Visual verification required in Streamlit app")
def test_matrix_animation_manual_check():
    assert True
