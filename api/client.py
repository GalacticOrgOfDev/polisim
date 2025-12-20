"""
PoliSim REST API Client
Simple Python client for interacting with the PoliSim REST API.
"""

from typing import Dict, List, Optional, Any
import requests
import json


class PoliSimAPIClient:
    """Client for PoliSim REST API."""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """Initialize API client."""
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = f"{self.base_url}/api/{endpoint}"
        response = self.session.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._make_request('GET', 'health')
    
    # Policy endpoints
    def list_policies(self) -> List[Dict[str, Any]]:
        """List available policy templates."""
        result = self._make_request('GET', 'policies')
        return result.get('policies', [])
    
    def get_policy_template(self, policy_type: str) -> Dict[str, Any]:
        """Get policy template details."""
        return self._make_request('GET', f'policies/{policy_type}')
    
    # Simulation endpoints
    def simulate_policy(
        self,
        revenue_change_pct: float,
        spending_change_pct: float,
        policy_name: str = "Custom Policy",
        years: int = 10,
        iterations: int = 5000,
    ) -> Dict[str, Any]:
        """Run policy simulation."""
        payload = {
            'policy_name': policy_name,
            'revenue_change_pct': revenue_change_pct,
            'spending_change_pct': spending_change_pct,
            'years': years,
            'iterations': iterations,
        }
        return self._make_request('POST', 'simulate/policy', json=payload)
    
    # Analysis endpoints
    def analyze_sensitivity(
        self,
        base_revenue: float = 5980,
        base_spending: float = 6911,
        parameter_ranges: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Run sensitivity analysis."""
        if parameter_ranges is None:
            parameter_ranges = {
                'Revenue': (-10, 20),
                'Spending': (-30, 10),
            }
        
        payload = {
            'base_revenue': base_revenue,
            'base_spending': base_spending,
            'parameter_ranges': parameter_ranges,
        }
        return self._make_request('POST', 'analyze/sensitivity', json=payload)
    
    def stress_test(
        self,
        revenue_change_pct: float = 0,
        spending_change_pct: float = 0,
    ) -> Dict[str, Any]:
        """Run stress test analysis."""
        payload = {
            'revenue_change_pct': revenue_change_pct,
            'spending_change_pct': spending_change_pct,
        }
        return self._make_request('POST', 'analyze/stress', json=payload)
    
    # Recommendation endpoint
    def recommend_policies(
        self,
        fiscal_goal: str = "minimize_deficit",
        limit: int = 5,
    ) -> Dict[str, Any]:
        """Get policy recommendations."""
        payload = {
            'fiscal_goal': fiscal_goal,
            'limit': limit,
        }
        return self._make_request('POST', 'recommend/policies', json=payload)
    
    # Impact calculation
    def calculate_impact(
        self,
        revenue_change_pct: float,
        spending_change_pct: float,
        policy_name: str = "Policy",
        years: int = 10,
    ) -> Dict[str, Any]:
        """Calculate fiscal impact of policy."""
        payload = {
            'policy_name': policy_name,
            'revenue_change_pct': revenue_change_pct,
            'spending_change_pct': spending_change_pct,
            'years': years,
        }
        return self._make_request('POST', 'calculate/impact', json=payload)
    
    # Data endpoints
    def get_baseline_data(self) -> Dict[str, Any]:
        """Get baseline fiscal data."""
        return self._make_request('GET', 'data/baseline')
    
    def get_historical_data(self) -> Dict[str, Any]:
        """Get historical fiscal data."""
        return self._make_request('GET', 'data/historical')
    
    # Report generation
    def generate_report(
        self,
        title: str = "Fiscal Policy Report",
        author: str = "PoliSim",
        description: str = "",
        summary: str = "",
    ) -> Dict[str, Any]:
        """Generate fiscal policy report."""
        payload = {
            'title': title,
            'author': author,
            'description': description,
            'summary': summary or "Report generated via API.",
        }
        return self._make_request('POST', 'report/generate', json=payload)
    
    # Scenario comparison
    def compare_scenarios(self, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compare multiple policy scenarios."""
        payload = {'scenarios': scenarios}
        return self._make_request('POST', 'scenarios/compare', json=payload)


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = PoliSimAPIClient("http://localhost:5000")
    
    # Check health
    print("API Health:", client.health_check())
    
    # List policies
    print("\nAvailable Policies:", client.list_policies())
    
    # Simulate policy
    print("\nPolicy Simulation:")
    result = client.simulate_policy(
        revenue_change_pct=5,
        spending_change_pct=-3,
        policy_name="Test Policy"
    )
    print(f"Mean Deficit: ${result['mean_deficit']:,.0f}B")
    print(f"Confidence Bounds: ${result['p10_deficit']:,.0f}B - ${result['p90_deficit']:,.0f}B")
    
    # Get recommendations
    print("\nPolicy Recommendations:")
    recommendations = client.recommend_policies(fiscal_goal="minimize_deficit")
    for rec in recommendations['recommendations'][:3]:
        print(f"  {rec['policy']}: Score {rec['overall_score']:.1f}")
    
    # Compare scenarios
    print("\nScenario Comparison:")
    scenarios = [
        {"name": "Status Quo", "revenue_change_pct": 0, "spending_change_pct": 0},
        {"name": "Tax Reform", "revenue_change_pct": 5, "spending_change_pct": 0},
        {"name": "Spending Cut", "revenue_change_pct": 0, "spending_change_pct": -3},
    ]
    comparison = client.compare_scenarios(scenarios)
    for scenario in comparison['scenarios']:
        print(f"  {scenario['scenario']}: 10-year deficit ${scenario['10_year_deficit']:,.0f}B")
