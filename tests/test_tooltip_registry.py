"""Unit tests for tooltip registry helper functions."""

import pytest

from ui.tooltip_registry import TOOLTIPS, get_tooltip, add_tooltip_icon


def test_get_tooltip_returns_registered_value():
    key = "healthcare_spending_target"
    assert key in TOOLTIPS
    result = get_tooltip(key)
    assert isinstance(result, str)
    assert "percentage of GDP" in result


def test_get_tooltip_returns_fallback_for_unknown_key():
    fallback = "custom fallback"
    assert get_tooltip("unknown_key", fallback) == fallback
    assert get_tooltip("unknown_key") == ""


def test_add_tooltip_icon_appends_marker_when_available():
    label = "Test Label"
    key = "deficit"
    marked = add_tooltip_icon(label, key)
    assert marked.endswith("(i)")
    assert label in marked


def test_add_tooltip_icon_no_marker_when_missing():
    label = "Plain Label"
    marked = add_tooltip_icon(label, "missing_key")
    assert marked == label


@pytest.mark.parametrize(
    "key",
    [
        "healthcare_policy_builtin",
        "healthcare_projection_years",
        "healthcare_base_gdp",
        "healthcare_initial_debt",
        "revenue_economic_scenario",
        "medicare_projection_years",
        "medicaid_projection_years",
        "combined_projection_years",
        "discretionary_projection_years",
        "combined_revenue_scenario",
    ],
)
def test_registry_has_expected_tooltip_keys(key):
    assert key in TOOLTIPS
    assert TOOLTIPS[key]
