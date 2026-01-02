"""
Tests for scenario diff viewer component.
"""

import pytest
from ui.scenario_diff_viewer import ScenarioDiffViewer, ScenarioDiff


class TestScenarioDiffViewer:
    """Test suite for ScenarioDiffViewer."""
    
    @pytest.fixture
    def viewer(self):
        """Create a test viewer instance."""
        return ScenarioDiffViewer()
    
    @pytest.fixture
    def sample_scenarios(self, viewer):
        """Add sample scenarios to viewer."""
        viewer.add_scenario("Status Quo", {
            "Revenue Impact (%)": 0,
            "Spending Impact (%)": 0,
            "Deficit Change (B)": 0,
            "GDP Growth (%)": 2.5,
        })
        
        viewer.add_scenario("Tax Reform", {
            "Revenue Impact (%)": 5,
            "Spending Impact (%)": 0,
            "Deficit Change (B)": -150,
            "GDP Growth (%)": 2.3,
        })
        
        viewer.add_scenario("Spending Cut", {
            "Revenue Impact (%)": 0,
            "Spending Impact (%)": -3,
            "Deficit Change (B)": -200,
            "GDP Growth (%)": 2.6,
        })
        
        return viewer
    
    def test_add_scenario(self, viewer):
        """Test adding scenarios."""
        viewer.add_scenario("Test Scenario", {"param": 100})
        assert "Test Scenario" in viewer.scenarios
        assert viewer.scenarios["Test Scenario"]["param"] == 100
    
    def test_calculate_diff_exists(self, sample_scenarios):
        """Test calculating diff between existing scenarios."""
        diff = sample_scenarios.calculate_diff("Status Quo", "Tax Reform")
        
        assert diff.scenario_1_name == "Status Quo"
        assert diff.scenario_2_name == "Tax Reform"
        assert "Revenue Impact (%)" in diff.changes
        assert diff.changes["Revenue Impact (%)"] == (0, 5)
    
    def test_calculate_diff_nonexistent(self, sample_scenarios):
        """Test that nonexistent scenarios raise error."""
        with pytest.raises(ValueError):
            sample_scenarios.calculate_diff("Status Quo", "Nonexistent")
    
    def test_deltas_calculation(self, sample_scenarios):
        """Test that deltas are calculated correctly."""
        diff = sample_scenarios.calculate_diff("Status Quo", "Tax Reform")
        
        assert diff.deltas["Revenue Impact (%)"] == 5.0
        assert diff.deltas["Spending Impact (%)"] == 0.0
        assert diff.deltas["Deficit Change (B)"] == -150.0
        assert abs(diff.deltas["GDP Growth (%)"] - (-0.2)) < 1e-9  # Handle floating-point precision
    
    def test_render_diff_table(self, sample_scenarios):
        """Test rendering diff as DataFrame."""
        diff = sample_scenarios.calculate_diff("Status Quo", "Tax Reform")
        df = sample_scenarios.render_diff_table(diff)
        
        assert "Parameter" in df.columns
        assert "Status Quo" in df.columns
        assert "Tax Reform" in df.columns
        assert "Change" in df.columns
        assert len(df) == 4  # 4 parameters
    
    def test_multiple_scenarios_comparison(self, sample_scenarios):
        """Test that multiple scenarios can be compared."""
        scenarios = list(sample_scenarios.scenarios.keys())
        assert len(scenarios) == 3
        
        # Create multiple diffs
        diff1 = sample_scenarios.calculate_diff(scenarios[0], scenarios[1])
        diff2 = sample_scenarios.calculate_diff(scenarios[0], scenarios[2])
        
        assert diff1.scenario_1_name == scenarios[0]
        assert diff2.scenario_2_name == scenarios[2]
    
    def test_zero_delta_for_same_scenario(self, sample_scenarios):
        """Test that comparing identical values gives zero delta."""
        viewer = ScenarioDiffViewer()
        viewer.add_scenario("A", {"param": 100})
        viewer.add_scenario("B", {"param": 100})
        
        diff = viewer.calculate_diff("A", "B")
        assert diff.deltas["param"] == 0.0
    
    def test_negative_delta(self, sample_scenarios):
        """Test negative delta calculation."""
        diff = sample_scenarios.calculate_diff("Spending Cut", "Status Quo")
        
        assert diff.deltas["Spending Impact (%)"] == 3.0  # 0 - (-3)
        assert diff.deltas["Deficit Change (B)"] == 200.0  # 0 - (-200)
    
    def test_percentage_change_calculation(self, sample_scenarios):
        """Test percentage change is calculated correctly."""
        df = sample_scenarios.render_diff_table(
            sample_scenarios.calculate_diff("Status Quo", "Tax Reform")
        )
        
        # Check that at least one percentage change is present
        assert "Pct Change" in df.columns
        assert any("%" in str(val) for val in df["Pct Change"] if val != "N/A")


class TestScenarioDiffType:
    """Test ScenarioDiff dataclass."""
    
    def test_scenario_diff_creation(self):
        """Test creating a ScenarioDiff object."""
        changes = {"param1": (100, 150), "param2": (50, 50)}
        deltas = {"param1": 50, "param2": 0}
        
        diff = ScenarioDiff(
            scenario_1_name="Scenario A",
            scenario_2_name="Scenario B",
            changes=changes,
            deltas=deltas,
        )
        
        assert diff.scenario_1_name == "Scenario A"
        assert diff.scenario_2_name == "Scenario B"
        assert len(diff.changes) == 2
        assert len(diff.deltas) == 2
    
    def test_scenario_diff_access(self):
        """Test accessing ScenarioDiff properties."""
        diff = ScenarioDiff(
            scenario_1_name="A",
            scenario_2_name="B",
            changes={"x": (1, 2)},
            deltas={"x": 1},
        )
        
        assert "x" in diff.changes
        assert diff.changes["x"] == (1, 2)
        assert diff.deltas["x"] == 1
