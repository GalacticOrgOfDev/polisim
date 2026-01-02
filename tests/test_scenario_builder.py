import pandas as pd

from core.policy_builder import (
    CustomPolicy,
    PolicyType,
    ScenarioBundle,
    ScenarioBundleLibrary,
    build_policy_comparison_table,
)


def test_scenario_bundle_library_round_trip(tmp_path):
    bundle_path = tmp_path / "bundles.json"
    lib = ScenarioBundleLibrary(bundle_path=bundle_path)

    bundle = ScenarioBundle(name="demo", policy_names=["A", "B"], description="test")
    lib.save_bundle(bundle)

    # Persisted bundle is readable in a new instance
    reloaded = ScenarioBundleLibrary(bundle_path=bundle_path)
    assert "demo" in reloaded.list_bundles()

    loaded_bundle = reloaded.get_bundle("demo")
    assert loaded_bundle is not None
    assert loaded_bundle.policy_names == ["A", "B"]

    # Delete removes entry
    assert reloaded.delete_bundle("demo")
    assert "demo" not in reloaded.list_bundles()


def test_build_policy_comparison_table_computes_deltas():
    p1 = CustomPolicy(name="Policy A", description="baseline", policy_type=PolicyType.TAX_REFORM)
    p1.add_parameter("rate", "rate", 10.0, 0.0, 20.0, unit="%")

    p2 = CustomPolicy(name="Policy B", description="variant", policy_type=PolicyType.TAX_REFORM)
    p2.add_parameter("rate", "rate", 12.5, 0.0, 20.0, unit="%")

    df = build_policy_comparison_table([p1, p2])
    assert not df.empty

    delta_col = "Policy B Δ vs Policy A"
    assert delta_col in df.columns

    # Single parameter row should reflect the delta
    delta_value = df.loc[df["Parameter"] == "rate", delta_col].iloc[0]
    assert delta_value == 2.5
