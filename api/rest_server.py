"""
REST API Server for PoliSim
Provides HTTP endpoints for policy analysis and fiscal projections.

Features:
- Policy simulation endpoints
- Real data access
- Report generation
- Monte Carlo analysis
- Scenario comparison
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from flask import Flask, request, jsonify, send_file
    from flask_cors import CORS
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False

from core.policy_builder import CustomPolicy, PolicyLibrary
from core.monte_carlo_scenarios import MonteCarloPolicySimulator, PolicySensitivityAnalyzer, StressTestAnalyzer
from core.policy_enhancements import PolicyRecommendationEngine, PolicyImpactCalculator, InteractiveScenarioExplorer, FiscalGoal
from core.data_loader import load_real_data
from core.report_generator import ComprehensiveReportBuilder, ReportMetadata
import pandas as pd


class APIError(Exception):
    """Custom API error."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


def create_api_app() -> "Flask":
    """Create and configure Flask application."""
    if not HAS_FLASK:
        raise ImportError("Flask and flask-cors required. Install with: pip install flask flask-cors")
    
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    # Error handler
    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify({
            "error": error.message,
            "status": "error"
        })
        response.status_code = error.status_code
        return response
    
    # Health check
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "healthy",
            "version": "1.0",
            "timestamp": datetime.now().isoformat()
        })
    
    # Policy endpoints
    @app.route('/api/policies', methods=['GET'])
    def list_policies():
        """List available policy templates."""
        try:
            library = PolicyLibrary()
            templates = [
                {"name": t.name, "type": t.policy_type, "parameters": len(t.parameters)}
                for t in library.templates.values()
            ]
            return jsonify({
                "status": "success",
                "count": len(templates),
                "policies": templates
            })
        except Exception as e:
            raise APIError(f"Failed to list policies: {str(e)}")
    
    @app.route('/api/policies/<policy_type>', methods=['GET'])
    def get_policy_template(policy_type):
        """Get policy template details."""
        try:
            library = PolicyLibrary()
            if policy_type not in library.templates:
                raise APIError(f"Policy type {policy_type} not found", 404)
            
            template = library.templates[policy_type]
            return jsonify({
                "status": "success",
                "name": template.name,
                "type": template.policy_type,
                "description": template.description,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.parameter_type,
                        "default": p.default_value,
                        "unit": p.unit,
                    }
                    for p in template.parameters.values()
                ]
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Failed to get policy template: {str(e)}")
    
    # Simulation endpoints
    @app.route('/api/simulate/policy', methods=['POST'])
    def simulate_policy():
        """Run policy simulation."""
        try:
            data = request.get_json()
            
            # Validate input
            if not data or 'revenue_change_pct' not in data:
                raise APIError("Missing required parameters: revenue_change_pct, spending_change_pct")
            
            revenue_change = data.get('revenue_change_pct', 0)
            spending_change = data.get('spending_change_pct', 0)
            years = data.get('years', 10)
            iterations = data.get('iterations', 5000)
            
            # Run simulation
            simulator = MonteCarloPolicySimulator()
            result = simulator.simulate_policy(
                policy_name=data.get('policy_name', 'Custom Policy'),
                revenue_change_pct=revenue_change,
                spending_change_pct=spending_change,
                years=years,
                iterations=iterations,
            )
            
            return jsonify({
                "status": "success",
                "policy_name": result.policy_name,
                "iterations": result.iterations,
                "mean_deficit": float(result.mean_deficit),
                "median_deficit": float(result.median_deficit),
                "std_dev": float(result.std_dev_deficit),
                "p10_deficit": float(result.p10_deficit),
                "p90_deficit": float(result.p90_deficit),
                "probability_balanced": float(result.probability_balanced),
                "confidence_bounds": [float(result.p10_deficit), float(result.p90_deficit)],
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Simulation failed: {str(e)}")
    
    # Sensitivity analysis
    @app.route('/api/analyze/sensitivity', methods=['POST'])
    def sensitivity_analysis():
        """Run sensitivity analysis."""
        try:
            data = request.get_json()
            
            base_revenue = data.get('base_revenue', 5980)
            base_spending = data.get('base_spending', 6911)
            parameter_ranges = data.get('parameter_ranges', {
                'Revenue': (-10, 20),
                'Spending': (-30, 10),
            })
            
            analyzer = PolicySensitivityAnalyzer()
            result_df = analyzer.tornado_analysis(
                base_revenue=base_revenue,
                base_spending=base_spending,
                parameter_ranges=parameter_ranges,
            )
            
            return jsonify({
                "status": "success",
                "analysis": "sensitivity",
                "parameters": result_df.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Sensitivity analysis failed: {str(e)}")
    
    # Stress testing
    @app.route('/api/analyze/stress', methods=['POST'])
    def stress_test():
        """Run stress test analysis."""
        try:
            data = request.get_json()
            
            policy_params = {
                'revenue_change_pct': data.get('revenue_change_pct', 0),
                'spending_change_pct': data.get('spending_change_pct', 0),
            }
            
            analyzer = StressTestAnalyzer()
            result_df = analyzer.run_stress_test(policy_params)
            
            return jsonify({
                "status": "success",
                "analysis": "stress_test",
                "scenarios": result_df.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Stress test failed: {str(e)}")
    
    # Recommendation endpoint
    @app.route('/api/recommend/policies', methods=['POST'])
    def recommend_policies():
        """Get policy recommendations."""
        try:
            data = request.get_json()
            
            fiscal_goal = data.get('fiscal_goal', 'minimize_deficit')
            limit = data.get('limit', 5)
            
            # Map string to enum
            goal_map = {
                'minimize_deficit': FiscalGoal.MINIMIZE_DEFICIT,
                'maximize_revenue': FiscalGoal.MAXIMIZE_REVENUE,
                'balance_budget': FiscalGoal.BALANCE_BUDGET,
                'sustainable_debt': FiscalGoal.SUSTAINABLE_DEBT,
                'growth_focused': FiscalGoal.GROWTH_FOCUSED,
                'equity_focused': FiscalGoal.EQUITY_FOCUSED,
            }
            
            goal = goal_map.get(fiscal_goal.lower(), FiscalGoal.MINIMIZE_DEFICIT)
            
            engine = PolicyRecommendationEngine()
            recommendations = engine.recommend_policies(goal=goal, limit=limit)
            
            return jsonify({
                "status": "success",
                "fiscal_goal": fiscal_goal,
                "recommendations": [
                    {
                        "policy": rec.policy_name,
                        "overall_score": float(rec.overall_score),
                        "fiscal_impact": float(rec.fiscal_impact),
                        "sustainability": float(rec.sustainability_score),
                        "feasibility": float(rec.feasibility_score),
                        "equity": float(rec.equity_score),
                        "growth": float(rec.growth_impact),
                    }
                    for rec in recommendations
                ]
            })
        except Exception as e:
            raise APIError(f"Recommendation failed: {str(e)}")
    
    # Impact calculation
    @app.route('/api/calculate/impact', methods=['POST'])
    def calculate_impact():
        """Calculate fiscal impact of policy."""
        try:
            data = request.get_json()
            
            revenue_change = data.get('revenue_change_pct', 0)
            spending_change = data.get('spending_change_pct', 0)
            years = data.get('years', 10)
            
            calculator = PolicyImpactCalculator()
            impact_df = calculator.calculate_impact(
                policy_name=data.get('policy_name', 'Policy'),
                revenue_change_pct=revenue_change,
                spending_change_pct=spending_change,
                years=years,
            )
            
            return jsonify({
                "status": "success",
                "policy": data.get('policy_name', 'Policy'),
                "projections": impact_df.to_dict(orient='records'),
                "total_deficit": float(impact_df['Deficit'].sum()),
                "avg_deficit": float(impact_df['Deficit'].mean()),
            })
        except Exception as e:
            raise APIError(f"Impact calculation failed: {str(e)}")
    
    # Data endpoints
    @app.route('/api/data/baseline', methods=['GET'])
    def get_baseline_data():
        """Get baseline fiscal data."""
        try:
            data = load_real_data()
            return jsonify({
                "status": "success",
                "revenue": float(data['revenue']),
                "spending": float(data['spending']),
                "deficit": float(data['deficit']),
                "gdp": float(data['gdp']),
                "deficit_pct_gdp": float(data['deficit_pct_gdp']),
            })
        except Exception as e:
            raise APIError(f"Failed to load baseline data: {str(e)}")
    
    @app.route('/api/data/historical', methods=['GET'])
    def get_historical_data():
        """Get historical fiscal data."""
        try:
            # Return sample historical data
            historical = pd.DataFrame({
                'Year': list(range(2015, 2025)),
                'Revenue': [3300, 3450, 3600, 3750, 3900, 3980, 4100, 4200, 4300, 4400],
                'Spending': [3800, 3950, 4100, 4250, 4400, 4550, 4700, 4850, 5000, 5150],
            })
            historical['Deficit'] = historical['Spending'] - historical['Revenue']
            
            return jsonify({
                "status": "success",
                "historical": historical.to_dict(orient='records'),
            })
        except Exception as e:
            raise APIError(f"Failed to load historical data: {str(e)}")
    
    # Report generation endpoint
    @app.route('/api/report/generate', methods=['POST'])
    def generate_report():
        """Generate fiscal policy report."""
        try:
            data = request.get_json()
            
            metadata = ReportMetadata(
                title=data.get('title', 'Fiscal Policy Report'),
                author=data.get('author', 'PoliSim API'),
                description=data.get('description', ''),
            )
            
            builder = ComprehensiveReportBuilder(metadata)
            builder.add_executive_summary(data.get('summary', 'Report generated via API.'))
            
            # Generate JSON (always available)
            report_dir = Path('reports/api_generated')
            report_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_path = report_dir / f"report_{timestamp}.json"
            
            builder.generate_json(str(json_path))
            
            return jsonify({
                "status": "success",
                "report": str(json_path),
                "format": "json",
                "timestamp": timestamp,
            })
        except Exception as e:
            raise APIError(f"Report generation failed: {str(e)}")
    
    # Scenario comparison
    @app.route('/api/scenarios/compare', methods=['POST'])
    def compare_scenarios():
        """Compare multiple policy scenarios."""
        try:
            data = request.get_json()
            scenarios = data.get('scenarios', [])
            
            if not scenarios:
                raise APIError("No scenarios provided")
            
            explorer = InteractiveScenarioExplorer()
            comparison = explorer.create_scenario_list(
                scenarios=[s.get('name', f'Scenario {i}') for i, s in enumerate(scenarios)]
            )
            
            results = []
            for scenario in scenarios:
                calc = PolicyImpactCalculator()
                impact = calc.calculate_impact(
                    policy_name=scenario.get('name', 'Scenario'),
                    revenue_change_pct=scenario.get('revenue_change_pct', 0),
                    spending_change_pct=scenario.get('spending_change_pct', 0),
                    years=scenario.get('years', 10),
                )
                
                results.append({
                    "scenario": scenario.get('name'),
                    "10_year_deficit": float(impact['Deficit'].sum()),
                    "avg_deficit": float(impact['Deficit'].mean()),
                    "final_year_deficit": float(impact['Deficit'].iloc[-1]),
                })
            
            return jsonify({
                "status": "success",
                "scenario_count": len(results),
                "scenarios": results,
            })
        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Scenario comparison failed: {str(e)}")
    
    return app


def run_api_server(host: str = '127.0.0.1', port: int = 5000, debug: bool = False):
    """Run the REST API server."""
    try:
        app = create_api_app()
        print(f"Starting PoliSim REST API on {host}:{port}")
        print(f"API Documentation: http://{host}:{port}/api/health")
        app.run(host=host, port=port, debug=debug)
    except ImportError as e:
        print(f"Error: {e}")
        print("Install Flask with: pip install flask flask-cors")


if __name__ == "__main__":
    run_api_server(debug=True)
