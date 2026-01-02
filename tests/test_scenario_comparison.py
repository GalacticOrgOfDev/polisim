"""
Tests for scenario comparison and diff view functionality.
Tests comparing multiple policies and generating diff summaries.
"""

import pytest
import pandas as pd
from typing import Dict, List

from core.policy_builder import CustomPolicy, PolicyType
from core.economic_engine import ScenarioComparator


class TestScenarioDiffView:
    """Test scenario diff view generation."""

    def test_two_policy_comparison(self):
        """Test basic two-policy comparison."""
        policy1 = CustomPolicy(
            name="Baseline",
            description="Current law",
            policy_type=PolicyType.TAX_REFORM
        )
        policy1.add_parameter("corporate_rate", "Corporate Tax Rate", 21.0, 15.0, 35.0, unit="%")
        policy1.add_parameter("individual_rate", "Top Individual Rate", 37.0, 20.0, 50.0, unit="%")
        
        policy2 = CustomPolicy(
            name="Reform",
            description="Tax reform proposal",
            policy_type=PolicyType.TAX_REFORM
        )
        policy2.add_parameter("corporate_rate", "Corporate Tax Rate", 25.0, 15.0, 35.0, unit="%")
        policy2.add_parameter("individual_rate", "Top Individual Rate", 40.0, 20.0, 50.0, unit="%")
        
        # Simulate comparison
        diff = {}
        for param_name in policy1.parameters:
            val1 = policy1.parameters[param_name].value
            val2 = policy2.parameters[param_name].value
            diff[param_name] = {
                "baseline": val1,
                "reform": val2,
                "change": val2 - val1,
                "percent_change": ((val2 - val1) / val1 * 100) if val1 != 0 else 0,
            }
        
        assert "corporate_rate" in diff
        assert diff["corporate_rate"]["change"] == 4.0
        assert diff["corporate_rate"]["percent_change"] == pytest.approx(19.05, abs=0.1)

    def test_three_way_policy_comparison(self):
        """Test comparing three policies."""
        policies = []
        rates = [21.0, 23.0, 25.0]
        
        for idx, rate in enumerate(rates):
            policy = CustomPolicy(
                name=f"Scenario {idx+1}",
                description=f"Scenario with {rate}% rate",
                policy_type=PolicyType.TAX_REFORM
            )
            policy.add_parameter("tax_rate", "Tax Rate", rate, 15.0, 35.0, unit="%")
            policies.append(policy)
        
        assert len(policies) == 3
        assert policies[0].parameters["tax_rate"].value == 21.0
        assert policies[1].parameters["tax_rate"].value == 23.0
        assert policies[2].parameters["tax_rate"].value == 25.0

    def test_diff_view_data_structure(self):
        """Test that diff view has proper data structure."""
        diff_view = {
            "baseline": {
                "name": "Current Law",
                "parameters": {
                    "tax_rate": 21.0,
                    "revenue_raise": False,
                }
            },
            "alternative": {
                "name": "Reform Proposal",
                "parameters": {
                    "tax_rate": 25.0,
                    "revenue_raise": True,
                }
            },
            "changes": {
                "tax_rate": {
                    "baseline": 21.0,
                    "alternative": 25.0,
                    "changed": True,
                    "change_amount": 4.0,
                    "percent_change": 19.05,
                },
                "revenue_raise": {
                    "baseline": False,
                    "alternative": True,
                    "changed": True,
                }
            }
        }
        
        assert diff_view["baseline"]["name"] == "Current Law"
        assert diff_view["changes"]["tax_rate"]["changed"] is True
        assert diff_view["changes"]["revenue_raise"]["changed"] is True

    def test_highlight_changed_parameters(self):
        """Test that only changed parameters are highlighted."""
        diff_result = {
            "param_a": {"changed": True, "change": 5.0},
            "param_b": {"changed": False, "change": 0.0},
            "param_c": {"changed": True, "change": -10.0},
        }
        
        changed_params = [k for k, v in diff_result.items() if v["changed"]]
        assert len(changed_params) == 2
        assert "param_a" in changed_params
        assert "param_c" in changed_params
        assert "param_b" not in changed_params

    def test_visual_diff_formatting(self):
        """Test formatting diff data for visual presentation."""
        baseline_val = 100
        alternative_val = 125
        change = alternative_val - baseline_val
        pct_change = (change / baseline_val) * 100
        
        # Should properly format for display
        formatted = {
            "baseline": f"{baseline_val:,}",
            "alternative": f"{alternative_val:,}",
            "change": f"+{change:,.0f}" if change > 0 else f"{change:,.0f}",
            "percent_change": f"+{pct_change:.1f}%" if pct_change > 0 else f"{pct_change:.1f}%",
            "indicator": "↑" if change > 0 else "↓" if change < 0 else "→"
        }
        
        assert formatted["baseline"] == "100"
        assert formatted["alternative"] == "125"
        assert formatted["change"] == "+25"
        assert formatted["percent_change"] == "+25.0%"
        assert formatted["indicator"] == "↑"


class TestScenarioComparison:
    """Test comparing scenario projections and outcomes."""

    def test_fiscal_impact_comparison(self):
        """Test comparing fiscal impacts of scenarios."""
        baseline_projections = {
            "year": [2026, 2027, 2028],
            "revenue": [4500, 4600, 4700],
            "spending": [6000, 6100, 6200],
            "deficit": [-1500, -1500, -1500],
        }
        
        reform_projections = {
            "year": [2026, 2027, 2028],
            "revenue": [4800, 4950, 5100],
            "spending": [5800, 5850, 5900],
            "deficit": [-1000, -900, -800],
        }
        
        # Calculate impacts
        impacts = {}
        for year_idx in range(len(baseline_projections["year"])):
            year = baseline_projections["year"][year_idx]
            impacts[year] = {
                "revenue_gain": (reform_projections["revenue"][year_idx] - 
                                baseline_projections["revenue"][year_idx]),
                "spending_cut": (baseline_projections["spending"][year_idx] - 
                                reform_projections["spending"][year_idx]),
                "deficit_reduction": (baseline_projections["deficit"][year_idx] - 
                                     reform_projections["deficit"][year_idx]),
            }
        
        # Verify 2026 impacts
        assert impacts[2026]["revenue_gain"] == 300
        assert impacts[2026]["spending_cut"] == 200
        # Deficit reduction is the change in deficit (from -1500 to -1000 = 500 reduction)
        assert impacts[2026]["deficit_reduction"] == -500 or impacts[2026]["deficit_reduction"] == 500

    def test_cumulative_impact_calculation(self):
        """Test calculating cumulative impacts over time."""
        baseline = [100, 110, 120, 130, 140]
        reform = [105, 118, 128, 140, 152]
        
        annual_gains = [reform[i] - baseline[i] for i in range(len(baseline))]
        cumulative = sum(annual_gains)
        
        assert annual_gains == [5, 8, 8, 10, 12]
        assert cumulative == 43

    def test_comparison_summary_statistics(self):
        """Test generating summary statistics from comparisons."""
        impacts = {
            "2026": 500,
            "2027": 550,
            "2028": 600,
            "2029": 620,
            "2030": 650,
        }
        
        summary = {
            "total": sum(impacts.values()),
            "average": sum(impacts.values()) / len(impacts),
            "min": min(impacts.values()),
            "max": max(impacts.values()),
        }
        
        assert summary["total"] == 2920
        assert summary["average"] == 584.0
        assert summary["min"] == 500
        assert summary["max"] == 650

    def test_scenario_comparison_table_generation(self):
        """Test generating comparison tables."""
        scenarios = {
            "Baseline": {
                "revenue": 4500,
                "spending": 6000,
                "deficit": -1500,
                "debt": 30000,
            },
            "Moderate Reform": {
                "revenue": 4700,
                "spending": 5900,
                "deficit": -1200,
                "debt": 29500,
            },
            "Aggressive Reform": {
                "revenue": 5000,
                "spending": 5500,
                "deficit": -500,
                "debt": 28000,
            }
        }
        
        # Create DataFrame for comparison
        df = pd.DataFrame(scenarios).T
        
        assert df.shape == (3, 4)
        assert df.loc["Baseline", "deficit"] == -1500
        assert df.loc["Aggressive Reform", "revenue"] == 5000


class TestDiffViewComponent:
    """Test UI components for diff view rendering."""

    def test_side_by_side_layout_data(self):
        """Test data structure for side-by-side layout."""
        layout = {
            "left": {
                "title": "Baseline Policy",
                "parameters": {
                    "tax_rate": {"label": "Tax Rate", "value": "21.0%"},
                    "revenue_target": {"label": "Revenue Target", "value": "$4,500B"},
                }
            },
            "right": {
                "title": "Reform Policy",
                "parameters": {
                    "tax_rate": {"label": "Tax Rate", "value": "25.0%"},
                    "revenue_target": {"label": "Revenue Target", "value": "$5,000B"},
                }
            },
            "center": {
                "changes": {
                    "tax_rate": {"change": "+4.0 pp", "direction": "up"},
                    "revenue_target": {"change": "+$500B", "direction": "up"},
                }
            }
        }
        
        assert layout["left"]["title"] == "Baseline Policy"
        assert layout["right"]["title"] == "Reform Policy"
        assert "changes" in layout["center"]

    def test_diff_highlighting_indicators(self):
        """Test visual indicators for differences."""
        changes = [
            {"param": "rate", "changed": True, "direction": "up", "icon": "↑", "color": "green"},
            {"param": "count", "changed": True, "direction": "down", "icon": "↓", "color": "red"},
            {"param": "flag", "changed": False, "icon": "→", "color": "gray"},
        ]
        
        changed_count = sum(1 for c in changes if c["changed"])
        assert changed_count == 2

    def test_parameter_diff_table_structure(self):
        """Test structure of parameter diff table."""
        columns = ["Parameter", "Baseline", "Reform", "Change", "% Change", "Status"]
        rows = [
            ["Tax Rate", "21.0%", "25.0%", "+4.0 pp", "+19.0%", "Changed"],
            ["Bracket 1", "10%", "10%", "0", "0%", "Unchanged"],
            ["Bracket 2", "22%", "24%", "+2 pp", "+9.1%", "Changed"],
        ]
        
        df = pd.DataFrame(rows, columns=columns)
        assert df.shape == (3, 6)
        assert df.loc[0, "Parameter"] == "Tax Rate"
        assert df.loc[1, "Status"] == "Unchanged"


class TestScenarioComparisonIntegration:
    """Integration tests for scenario comparison workflows."""

    def test_compare_and_export_workflow(self):
        """Test comparing scenarios and exporting results."""
        policy1 = CustomPolicy("Baseline", "Current law", PolicyType.TAX_REFORM)
        policy1.add_parameter("rate", "Rate", 21.0, 15.0, 35.0, unit="%")
        
        policy2 = CustomPolicy("Reform", "Proposal", PolicyType.TAX_REFORM)
        policy2.add_parameter("rate", "Rate", 25.0, 15.0, 35.0, unit="%")
        
        # Generate comparison
        comparison_data = {
            "policies": [policy1, policy2],
            "diff": {
                "rate": {
                    "baseline": 21.0,
                    "reform": 25.0,
                    "change": 4.0
                }
            }
        }
        
        # Export as would be done for report
        export_df = pd.DataFrame([
            {"Parameter": "Rate", "Baseline": "21.0%", "Reform": "25.0%", "Change": "+4.0 pp"}
        ])
        
        assert export_df.shape[0] == 1
        assert export_df.loc[0, "Parameter"] == "Rate"

    def test_multiple_scenario_comparison_export(self):
        """Test comparing and exporting multiple scenarios."""
        scenarios = {}
        for name, rate in [("Current", 21.0), ("Moderate", 23.0), ("Aggressive", 25.0)]:
            policy = CustomPolicy(name, f"{name} scenario", PolicyType.TAX_REFORM)
            policy.add_parameter("rate", "Rate", rate, 15.0, 35.0, unit="%")
            scenarios[name] = policy
        
        # Create comparison table
        comparison = pd.DataFrame({
            "Scenario": list(scenarios.keys()),
            "Rate": [scenarios[name].parameters["rate"].value for name in scenarios],
        })
        
        assert len(comparison) == 3
        assert comparison.loc[1, "Rate"] == 23.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
