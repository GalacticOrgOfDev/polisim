import io
import json
import zipfile
import pandas as pd

from core.policy_builder import (
    CustomPolicy,
    PolicyType,
    build_policy_comparison_table,
    build_scenario_bundle_zip,
)


def _make_policy(name: str, value: float) -> CustomPolicy:
    policy = CustomPolicy(name=name, description=name, policy_type=PolicyType.TAX_REFORM)
    policy.add_parameter("rate", "rate", value, 0.0, 20.0, unit="%")
    return policy


def test_build_scenario_bundle_zip_contains_expected_files():
    policies = [_make_policy("A", 10.0), _make_policy("B", 12.0)]
    comparison_df = build_policy_comparison_table(policies)

    bundle_bytes = build_scenario_bundle_zip(policies, comparison_df)

    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as zf:
        names = set(zf.namelist())
        assert "policies.json" in names
        assert "metadata.json" in names
        assert "comparison.csv" in names
        assert "comparison.json" in names

        policies_payload = json.loads(zf.read("policies.json"))
        assert set(policies_payload.keys()) == {"A", "B"}

        comparison_payload = json.loads(zf.read("comparison.json"))
        assert isinstance(comparison_payload, list)
        assert comparison_payload[0]["Parameter"] == "rate"


def test_build_scenario_bundle_zip_handles_empty_comparison():
    policies = [_make_policy("Solo", 5.0)]
    empty_df = pd.DataFrame()

    bundle_bytes = build_scenario_bundle_zip(policies, empty_df)

    with zipfile.ZipFile(io.BytesIO(bundle_bytes), "r") as zf:
        names = set(zf.namelist())
        assert "policies.json" in names
        assert "metadata.json" in names
        # comparison files optional when no comparison rows
        assert "comparison.csv" not in names
        assert "comparison.json" not in names
