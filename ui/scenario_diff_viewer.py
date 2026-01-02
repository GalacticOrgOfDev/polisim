"""
Scenario Diff Viewer Component - Display differences between policy scenarios.

This module provides a Streamlit component for visualizing differences between
multiple policy scenarios with color-coded highlighting and delta calculations.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import streamlit as st
import pandas as pd
import json


@dataclass
class ScenarioDiff:
    """Represents the difference between two scenarios."""
    scenario_1_name: str
    scenario_2_name: str
    changes: Dict[str, Tuple[Any, Any]]  # param_name -> (old_value, new_value)
    deltas: Dict[str, float]  # param_name -> delta value


class ScenarioDiffViewer:
    """Component for viewing differences between policy scenarios."""
    
    def __init__(self):
        """Initialize the diff viewer."""
        self.scenarios: Dict[str, Dict[str, Any]] = {}
    
    def add_scenario(self, name: str, parameters: Dict[str, Any]) -> None:
        """Add a scenario to the viewer.
        
        Args:
            name: Scenario name (e.g., "Status Quo", "Tax Reform")
            parameters: Dict of parameter_name -> value
        """
        self.scenarios[name] = parameters
    
    def calculate_diff(self, scenario_1: str, scenario_2: str) -> ScenarioDiff:
        """Calculate differences between two scenarios.
        
        Args:
            scenario_1: Name of first scenario (baseline)
            scenario_2: Name of second scenario (comparison)
        
        Returns:
            ScenarioDiff object with changes and deltas
        """
        if scenario_1 not in self.scenarios or scenario_2 not in self.scenarios:
            raise ValueError(f"Scenarios '{scenario_1}' and/or '{scenario_2}' not found")
        
        params_1 = self.scenarios[scenario_1]
        params_2 = self.scenarios[scenario_2]
        
        changes = {}
        deltas = {}
        
        # Get all unique parameters
        all_params = set(params_1.keys()) | set(params_2.keys())
        
        for param in sorted(all_params):
            val_1 = params_1.get(param, 0)
            val_2 = params_2.get(param, 0)
            
            changes[param] = (val_1, val_2)
            
            # Calculate delta (handles numeric comparisons)
            try:
                delta = float(val_2) - float(val_1)
                deltas[param] = delta
            except (TypeError, ValueError):
                deltas[param] = 0.0
        
        return ScenarioDiff(
            scenario_1_name=scenario_1,
            scenario_2_name=scenario_2,
            changes=changes,
            deltas=deltas,
        )
    
    def render_diff_table(self, diff: ScenarioDiff, show_delta: bool = True) -> pd.DataFrame:
        """Render diff as a Pandas DataFrame.
        
        Args:
            diff: ScenarioDiff object
            show_delta: Whether to show delta column
        
        Returns:
            DataFrame with comparison
        """
        rows = []
        
        for param, (val_1, val_2) in diff.changes.items():
            delta = diff.deltas.get(param, 0)
            
            row = {
                "Parameter": param,
                diff.scenario_1_name: val_1,
                diff.scenario_2_name: val_2,
            }
            
            if show_delta:
                row["Change"] = f"{delta:+.2f}" if isinstance(delta, float) else delta
                row["Pct Change"] = f"{(delta / float(val_1) * 100):+.1f}%" if val_1 != 0 else "N/A"
            
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def render_streamlit_diff(
        self,
        diff: ScenarioDiff,
        show_delta: bool = True,
        highlight_threshold: float = 0.0,
    ) -> None:
        """Render diff comparison in Streamlit.
        
        Args:
            diff: ScenarioDiff object
            show_delta: Whether to show delta column
            highlight_threshold: Minimum change to highlight (for numeric values)
        """
        st.subheader(f"Scenario Comparison: {diff.scenario_1_name} vs {diff.scenario_2_name}")
        
        # Create comparison DataFrame
        comparison_df = self.render_diff_table(diff, show_delta)
        
        # Display as table with formatting
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )
        
        # Show summary statistics
        col1, col2, col3 = st.columns(3)
        
        # Count parameters changed
        num_changes = sum(1 for v1, v2 in diff.changes.values() if v1 != v2)
        with col1:
            st.metric("Parameters Changed", num_changes)
        
        # Sum of absolute deltas
        total_delta = sum(abs(d) for d in diff.deltas.values())
        with col2:
            st.metric("Total Absolute Change", f"{total_delta:.2f}")
        
        # Count of increases vs decreases
        increases = sum(1 for d in diff.deltas.values() if d > 0)
        with col3:
            st.metric("Increases", increases, f"Decreases: {num_changes - increases}")
        
        # Show details in expander
        with st.expander("📊 Detailed Comparison"):
            # Parameters with largest changes
            sorted_deltas = sorted(
                diff.deltas.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            st.write("**Largest Changes:**")
            for param, delta in sorted_deltas[:5]:
                val_1, val_2 = diff.changes[param]
                change_pct = (delta / float(val_1) * 100) if val_1 != 0 else 0
                
                if delta > 0:
                    st.success(f"🔼 {param}: {val_1} → {val_2} (+{delta:.2f}, +{change_pct:.1f}%)")
                elif delta < 0:
                    st.error(f"🔽 {param}: {val_1} → {val_2} ({delta:.2f}, {change_pct:.1f}%)")
    
    def render_streamlit_multi_comparison(
        self,
        scenarios: List[str],
    ) -> None:
        """Render comparison of 3+ scenarios.
        
        Args:
            scenarios: List of scenario names to compare
        """
        if len(scenarios) < 2:
            st.warning("Please select at least 2 scenarios to compare")
            return
        
        st.subheader(f"Multi-Scenario Comparison: {len(scenarios)} scenarios")
        
        # Build comparison table with all scenarios
        all_params = set()
        for scenario_name in scenarios:
            if scenario_name in self.scenarios:
                all_params.update(self.scenarios[scenario_name].keys())
        
        rows = []
        for param in sorted(all_params):
            row = {"Parameter": param}
            for scenario_name in scenarios:
                if scenario_name in self.scenarios:
                    row[scenario_name] = self.scenarios[scenario_name].get(param, "—")
                else:
                    row[scenario_name] = "—"
            rows.append(row)
        
        comparison_df = pd.DataFrame(rows)
        
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True,
        )
        
        # Show which scenarios are most different
        if len(scenarios) >= 2:
            st.write("**Scenario Diversity:**")
            for i in range(len(scenarios)):
                for j in range(i + 1, len(scenarios)):
                    diff = self.calculate_diff(scenarios[i], scenarios[j])
                    num_changes = sum(1 for v1, v2 in diff.changes.values() if v1 != v2)
                    if num_changes > 0:
                        st.info(f"📊 {scenarios[i]} vs {scenarios[j]}: {num_changes} parameters differ")


def demo():
    """Demo the diff viewer component."""
    st.title("Scenario Diff Viewer Demo")
    
    viewer = ScenarioDiffViewer()
    
    # Add example scenarios
    viewer.add_scenario("Status Quo", {
        "Revenue Impact (%)": 0,
        "Spending Impact (%)": 0,
        "Deficit Change (B)": 0,
        "GDP Growth (%)": 2.5,
        "Tax Rate (%)": 24.0,
    })
    
    viewer.add_scenario("Tax Reform", {
        "Revenue Impact (%)": 5,
        "Spending Impact (%)": 0,
        "Deficit Change (B)": -150,
        "GDP Growth (%)": 2.3,
        "Tax Rate (%)": 25.2,
    })
    
    viewer.add_scenario("Spending Cut", {
        "Revenue Impact (%)": 0,
        "Spending Impact (%)": -3,
        "Deficit Change (B)": -200,
        "GDP Growth (%)": 2.6,
        "Tax Rate (%)": 24.0,
    })
    
    # Render comparison
    col1, col2 = st.columns(2)
    with col1:
        scenario_1 = st.selectbox("First Scenario:", list(viewer.scenarios.keys()))
    with col2:
        scenario_2 = st.selectbox("Second Scenario:", list(viewer.scenarios.keys()), index=1)
    
    if scenario_1 != scenario_2:
        diff = viewer.calculate_diff(scenario_1, scenario_2)
        viewer.render_streamlit_diff(diff)
    else:
        st.warning("Please select different scenarios")


if __name__ == "__main__":
    demo()
