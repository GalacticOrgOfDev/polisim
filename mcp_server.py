#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for POLISIM
Enables AI agents to interact with the economic simulation engine as a tool.

Usage:
    python mcp_server.py
"""

import json
import sys
import numpy as np
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from core.config import ConfigManager
from core.economic_engine import (
    EconomicParameters,
    PolicyScenario,
    MonteCarloEngine,
    EconomicModel,
    SensitivityAnalyzer,
    ScenarioComparator,
)
from core.social_security import (
    SocialSecurityModel,
    DemographicAssumptions,
    BenefitFormula,
    TrustFundAssumptions,
    SocialSecurityReforms,
)
from core.revenue_modeling import (
    FederalRevenueModel,
    IndividualIncomeTaxAssumptions,
    PayrollTaxAssumptions,
    CorporateIncomeTaxAssumptions,
    TaxReforms,
)
from utils.logging_config import setup_logging


class PolisimMCPServer:
    """MCP Server wrapper for POLISIM economic simulation engine.
    
    Supports healthcare (Phase 1), social security and revenue modeling (Phase 2),
    and combined fiscal analysis.
    """

    def __init__(self):
        """Initialize the MCP server and load configuration."""
        self.logger = setup_logging("mcp_server")
        self.config = ConfigManager()
        self.ss_model = SocialSecurityModel()
        self.revenue_model = FederalRevenueModel()
        self.logger.info("POLISIM MCP Server initialized with Phase 1 + Phase 2 modules")

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return list of available tools for AI agents."""
        return [
            {
                "name": "run_simulation",
                "description": "Run Monte Carlo economic simulation with policy parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_name": {
                            "type": "string",
                            "description": "Name of the policy scenario",
                        },
                        "years": {
                            "type": "integer",
                            "description": "Number of years to simulate (default: 22)",
                        },
                        "iterations": {
                            "type": "integer",
                            "description": "Number of Monte Carlo iterations (default: 10000)",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Override economic parameters as JSON",
                        },
                    },
                    "required": ["policy_name"],
                },
            },
            {
                "name": "compare_scenarios",
                "description": "Compare two policy scenarios side-by-side",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "baseline_policy": {
                            "type": "string",
                            "description": "Name of baseline policy",
                        },
                        "alternative_policy": {
                            "type": "string",
                            "description": "Name of alternative policy",
                        },
                        "years": {
                            "type": "integer",
                            "description": "Number of years to simulate",
                        },
                    },
                    "required": ["baseline_policy", "alternative_policy"],
                },
            },
            {
                "name": "sensitivity_analysis",
                "description": "Perform sensitivity analysis on key economic parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_name": {
                            "type": "string",
                            "description": "Policy scenario name",
                        },
                        "parameters": {
                            "type": "array",
                            "description": "Parameters to vary (e.g., ['inflation_rate', 'population_growth'])",
                            "items": {"type": "string"},
                        },
                        "variance_percent": {
                            "type": "number",
                            "description": "Percentage to vary parameters (default: 20)",
                        },
                    },
                    "required": ["policy_name"],
                },
            },
            {
                "name": "get_policy_catalog",
                "description": "Retrieve available policy scenarios from catalog",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filter": {
                            "type": "string",
                            "description": "Optional filter keyword",
                        }
                    },
                },
            },
            {
                "name": "get_config_parameters",
                "description": "Retrieve current configuration parameters",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "section": {
                            "type": "string",
                            "description": "Config section (e.g., 'economic', 'simulation')",
                        }
                    },
                },
            },
            {
                "name": "project_social_security",
                "description": "Project Social Security trust funds (OASI/DI) with Monte Carlo uncertainty",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "years": {
                            "type": "integer",
                            "description": "Number of years to project (default: 30)",
                        },
                        "iterations": {
                            "type": "integer",
                            "description": "Monte Carlo iterations (default: 10000)",
                        },
                    },
                },
            },
            {
                "name": "social_security_reform",
                "description": "Model impact of Social Security policy reforms",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reform_type": {
                            "type": "string",
                            "description": "Reform type: 'raise_tax', 'raise_fra', 'reduce_benefits', or 'combined'",
                        },
                        "years": {
                            "type": "integer",
                            "description": "Projection years (default: 30)",
                        },
                    },
                    "required": ["reform_type"],
                },
            },
            {
                "name": "project_federal_revenues",
                "description": "Project federal revenues across all sources (income tax, payroll, corporate, etc.)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "years": {
                            "type": "integer",
                            "description": "Number of years to project (default: 10)",
                        },
                        "iterations": {
                            "type": "integer",
                            "description": "Monte Carlo iterations (default: 10000)",
                        },
                        "gdp_growth": {
                            "type": "number",
                            "description": "Assumed annual GDP growth rate (default: 0.025)",
                        },
                        "wage_growth": {
                            "type": "number",
                            "description": "Assumed annual wage growth rate (default: 0.03)",
                        },
                    },
                },
            },
            {
                "name": "tax_reform_analysis",
                "description": "Analyze impact of federal tax policy reforms",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "reform_type": {
                            "type": "string",
                            "description": "Reform type: 'top_rate', 'corporate_rate', 'payroll_tax', or 'remove_cap'",
                        },
                        "magnitude": {
                            "type": "number",
                            "description": "Reform magnitude (e.g., 0.05 for 5% increase, 0.28 for new rate)",
                        },
                    },
                    "required": ["reform_type"],
                },
            },
        ]

    def run_simulation(
        self,
        policy_name: str,
        years: int = 22,
        iterations: int = 10000,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo economic simulation.

        Args:
            policy_name: Name of policy scenario
            years: Number of years to simulate
            iterations: Number of Monte Carlo iterations
            parameters: Override economic parameters

        Returns:
            Simulation results with statistics
        """
        try:
            self.logger.info(f"Running simulation for policy: {policy_name}")

            # Load or create economic parameters
            if parameters:
                params = EconomicParameters(**parameters)
            else:
                params = EconomicParameters()

            # Create policy scenario
            policy = PolicyScenario(
                name=policy_name,
                description=f"Simulation run for {policy_name}",
                parameters=params,
            )

            # Run Monte Carlo engine
            engine = MonteCarloEngine(iterations=iterations)
            results = engine.run(policy, years=years)

            # Aggregate statistics
            stats = {
                "policy_name": policy_name,
                "years": years,
                "iterations": iterations,
                "mean_debt_2050": float(results["debt_2050"].mean()),
                "std_debt_2050": float(results["debt_2050"].std()),
                "min_debt_2050": float(results["debt_2050"].min()),
                "max_debt_2050": float(results["debt_2050"].max()),
                "percentiles": {
                    "p10": float(results["debt_2050"].quantile(0.1)),
                    "p25": float(results["debt_2050"].quantile(0.25)),
                    "p50": float(results["debt_2050"].quantile(0.50)),
                    "p75": float(results["debt_2050"].quantile(0.75)),
                    "p90": float(results["debt_2050"].quantile(0.90)),
                },
            }

            self.logger.info(f"Simulation complete. Mean debt 2050: ${stats['mean_debt_2050']:,.0f}B")
            return {"status": "success", "results": stats}

        except Exception as e:
            self.logger.error(f"Simulation failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def compare_scenarios(
        self,
        baseline_policy: str,
        alternative_policy: str,
        years: int = 22,
    ) -> Dict[str, Any]:
        """
        Compare two policy scenarios.

        Args:
            baseline_policy: Baseline scenario name
            alternative_policy: Alternative scenario name
            years: Number of years to simulate

        Returns:
            Comparison results and statistics
        """
        try:
            self.logger.info(
                f"Comparing {baseline_policy} vs {alternative_policy}"
            )

            baseline_params = EconomicParameters()
            baseline = PolicyScenario(
                name=baseline_policy,
                description=f"Baseline: {baseline_policy}",
                parameters=baseline_params,
            )

            alternative_params = EconomicParameters()
            alternative = PolicyScenario(
                name=alternative_policy,
                description=f"Alternative: {alternative_policy}",
                parameters=alternative_params,
            )

            # Run comparisons
            comparator = ScenarioComparator()
            comparison = comparator.compare(baseline, alternative, years=years)

            self.logger.info(f"Comparison complete")
            return {"status": "success", "results": comparison}

        except Exception as e:
            self.logger.error(f"Comparison failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def sensitivity_analysis(
        self,
        policy_name: str,
        parameters: Optional[List[str]] = None,
        variance_percent: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on policy parameters.

        Args:
            policy_name: Policy scenario name
            parameters: Parameters to analyze
            variance_percent: Percentage variance to apply

        Returns:
            Sensitivity analysis results
        """
        try:
            self.logger.info(f"Running sensitivity analysis for {policy_name}")

            params = EconomicParameters()
            policy = PolicyScenario(
                name=policy_name,
                description=f"Sensitivity analysis for {policy_name}",
                parameters=params,
            )

            analyzer = SensitivityAnalyzer()
            sensitivity = analyzer.analyze(
                policy, parameters=parameters, variance_percent=variance_percent
            )

            self.logger.info("Sensitivity analysis complete")
            return {"status": "success", "results": sensitivity}

        except Exception as e:
            self.logger.error(f"Sensitivity analysis failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_policy_catalog(self, filter_keyword: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve available policy scenarios.

        Args:
            filter_keyword: Optional filter keyword

        Returns:
            List of available policies
        """
        try:
            self.logger.info("Retrieving policy catalog")

            policies_config = self.config.get_parameter("policies", {})
            policies = list(policies_config.keys())

            if filter_keyword:
                policies = [p for p in policies if filter_keyword.lower() in p.lower()]

            return {
                "status": "success",
                "count": len(policies),
                "policies": policies,
            }

        except Exception as e:
            self.logger.error(f"Failed to retrieve policy catalog: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_config_parameters(self, section: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve configuration parameters.

        Args:
            section: Optional section filter

        Returns:
            Configuration parameters
        """
        try:
            self.logger.info(f"Retrieving config parameters (section: {section})")

            if section:
                params = self.config.get_parameter(section, {})
            else:
                params = self.config.config

            return {"status": "success", "parameters": params}

        except Exception as e:
            self.logger.error(f"Failed to retrieve parameters: {str(e)}")
            return {"status": "error", "message": str(e)}

    def project_social_security(
        self, years: int = 30, iterations: int = 10000
    ) -> Dict[str, Any]:
        """
        Project Social Security trust funds with Monte Carlo uncertainty.

        Args:
            years: Number of years to project
            iterations: Number of Monte Carlo iterations

        Returns:
            Trust fund projections and solvency analysis
        """
        try:
            self.logger.info(f"Projecting Social Security for {years} years ({iterations} iterations)")

            projections = self.ss_model.project_trust_funds(years=years, iterations=iterations)
            solvency = self.ss_model.estimate_solvency_dates(projections)

            summary = {
                "years_projected": years,
                "iterations": iterations,
                "oasi_depletion_year": float(solvency.get("OASI_depletion_year", np.nan)),
                "di_solvency_through": float(solvency.get("DI_solvency_through_year", np.nan)),
                "oasi_depletion_p10": float(solvency.get("OASI_depletion_p10", np.nan)),
                "oasi_depletion_p90": float(solvency.get("OASI_depletion_p90", np.nan)),
            }

            # Convert projections to serializable format
            results_data = {k: v.tolist() if hasattr(v, 'tolist') else float(v) 
                          for k, v in projections.iloc[-1].items()}

            self.logger.info("Social Security projection complete")
            return {
                "status": "success",
                "summary": summary,
                "latest_year": results_data,
            }

        except Exception as e:
            self.logger.error(f"Social Security projection failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def social_security_reform(
        self, reform_type: str, years: int = 30
    ) -> Dict[str, Any]:
        """
        Model impact of Social Security policy reforms.

        Args:
            reform_type: Type of reform ('raise_tax', 'raise_fra', 'reduce_benefits', 'combined')
            years: Number of years to project

        Returns:
            Reform impact analysis
        """
        try:
            self.logger.info(f"Analyzing Social Security reform: {reform_type}")

            reforms_map = {
                "raise_tax": SocialSecurityReforms.raise_payroll_tax_rate,
                "raise_fra": SocialSecurityReforms.raise_full_retirement_age,
                "reduce_benefits": SocialSecurityReforms.reduce_benefits,
                "combined": SocialSecurityReforms.combined_reform,
            }

            if reform_type not in reforms_map:
                return {
                    "status": "error",
                    "message": f"Unknown reform type: {reform_type}. Must be one of {list(reforms_map.keys())}",
                }

            reform_func = reforms_map[reform_type]
            if reform_type == "combined":
                reforms = reform_func()
            elif reform_type == "reduce_benefits":
                reforms = reform_func(reduction_percent=0.15)
            elif reform_type == "raise_fra":
                reforms = reform_func(new_fra=70)
            else:  # raise_tax
                reforms = reform_func(new_rate=0.145)

            # Project with reform
            baseline = self.ss_model.project_trust_funds(years=years, iterations=5000)
            baseline_solvency = self.ss_model.estimate_solvency_dates(baseline)
            baseline_depletion = baseline_solvency.get("OASI_depletion_year")
            
            reformed = self.ss_model.apply_policy_reform(reforms["reforms"], baseline)
            reformed_solvency = self.ss_model.estimate_solvency_dates(reformed)
            reformed_depletion = reformed_solvency.get("OASI_depletion_year")

            # Handle NaN values
            baseline_depl_val = float(baseline_depletion) if not np.isnan(baseline_depletion) else -1
            reformed_depl_val = float(reformed_depletion) if not np.isnan(reformed_depletion) else -1

            self.logger.info(f"Reform analysis complete for {reform_type}")
            return {
                "status": "success",
                "reform_type": reform_type,
                "reform_details": reforms["description"],
                "baseline_depletion": baseline_depl_val,
                "reformed_depletion": reformed_depl_val,
                "years_extended": float(reformed_depl_val - baseline_depl_val) if (baseline_depl_val > 0 and reformed_depl_val > 0) else 0,
            }

        except Exception as e:
            self.logger.error(f"Social Security reform analysis failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def project_federal_revenues(
        self,
        years: int = 10,
        iterations: int = 10000,
        gdp_growth: float = 0.025,
        wage_growth: float = 0.03,
    ) -> Dict[str, Any]:
        """
        Project federal revenues across all sources.

        Args:
            years: Number of years to project
            iterations: Number of Monte Carlo iterations
            gdp_growth: Annual GDP growth rate
            wage_growth: Annual wage growth rate

        Returns:
            Revenue projections by source
        """
        try:
            self.logger.info(
                f"Projecting federal revenues for {years} years "
                f"(GDP: {gdp_growth:.1%}, Wages: {wage_growth:.1%})"
            )

            # Convert scalars to arrays for the model
            gdp_growth_array = np.full(years, gdp_growth)
            wage_growth_array = np.full(years, wage_growth)

            revenues = self.revenue_model.project_all_revenues(
                years=years,
                gdp_growth=gdp_growth_array,
                wage_growth=wage_growth_array,
                iterations=iterations,
            )

            # Summary statistics by grouping mean across iterations
            latest_data = revenues[revenues['year'] == revenues['year'].max()]
            
            summary = {
                "year": int(latest_data['year'].iloc[0]),
                "total_revenue": float(latest_data["total_revenues"].mean()),
                "individual_income_tax": float(latest_data["individual_income_tax"].mean()),
                "payroll_taxes": float((latest_data["social_security_tax"].mean() + latest_data["medicare_tax"].mean())),
                "corporate_income_tax": float(latest_data["corporate_income_tax"].mean()),
                "excise_taxes": float(latest_data["excise_taxes"].mean()),
                "other_revenues": float(latest_data["other_revenues"].mean()),
            }

            # 10-year growth
            first_year_total = revenues[revenues['year'] == revenues['year'].min()]["total_revenues"].mean()
            last_year_total = revenues[revenues['year'] == revenues['year'].max()]["total_revenues"].mean()
            growth_rate = (last_year_total / first_year_total) ** (1 / years) - 1

            self.logger.info("Federal revenue projection complete")
            return {
                "status": "success",
                "projection_years": years,
                "iterations": iterations,
                "assumptions": {
                    "gdp_growth_annual": gdp_growth,
                    "wage_growth_annual": wage_growth,
                },
                "latest_year_summary": summary,
                "ten_year_growth_rate": float(growth_rate),
            }

        except Exception as e:
            self.logger.error(f"Federal revenue projection failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def tax_reform_analysis(
        self, reform_type: str, magnitude: float = 0.05
    ) -> Dict[str, Any]:
        """
        Analyze impact of federal tax policy reforms.

        Args:
            reform_type: Type of reform ('top_rate', 'corporate_rate', 'payroll_tax', 'remove_cap')
            magnitude: Reform magnitude (rate increase or new rate)

        Returns:
            Tax reform impact analysis
        """
        try:
            self.logger.info(f"Analyzing tax reform: {reform_type} (magnitude: {magnitude})")

            reforms_map = {
                "top_rate": TaxReforms.increase_individual_income_tax_rate,
                "corporate_rate": TaxReforms.increase_corporate_income_tax_rate,
                "payroll_tax": TaxReforms.increase_payroll_tax_rate,
                "remove_cap": TaxReforms.remove_social_security_wage_cap,
            }

            if reform_type not in reforms_map:
                return {
                    "status": "error",
                    "message": f"Unknown reform type: {reform_type}. Must be one of {list(reforms_map.keys())}",
                }

            reform_func = reforms_map[reform_type]
            if reform_type == "remove_cap":
                reforms = reform_func()
            else:
                reforms = reform_func(new_rate=magnitude)

            # Project revenues with reform - use arrays
            gdp_growth_array = np.full(10, 0.025)
            wage_growth_array = np.full(10, 0.03)

            baseline = self.revenue_model.project_all_revenues(
                years=10, gdp_growth=gdp_growth_array, wage_growth=wage_growth_array, iterations=5000
            )
            reformed = self.revenue_model.apply_tax_reform(reforms["reforms"], baseline)

            baseline_total = baseline["total_revenues"].sum()
            reformed_total = reformed["total_revenues"].sum()
            revenue_impact = reformed_total - baseline_total

            self.logger.info(f"Tax reform analysis complete for {reform_type}")
            return {
                "status": "success",
                "reform_type": reform_type,
                "reform_details": reforms["description"],
                "baseline_10yr_revenue": float(baseline_total),
                "reformed_10yr_revenue": float(reformed_total),
                "revenue_impact": float(revenue_impact),
                "percent_change": float(revenue_impact / baseline_total * 100),
            }

        except Exception as e:
            self.logger.error(f"Tax reform analysis failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def call_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with input parameters.

        Args:
            tool_name: Name of the tool to call
            tool_input: Input parameters for the tool

        Returns:
            Tool execution results
        """
        self.logger.info(f"Calling tool: {tool_name}")

        if tool_name == "run_simulation":
            return self.run_simulation(**tool_input)
        elif tool_name == "compare_scenarios":
            return self.compare_scenarios(**tool_input)
        elif tool_name == "sensitivity_analysis":
            return self.sensitivity_analysis(**tool_input)
        elif tool_name == "get_policy_catalog":
            return self.get_policy_catalog(**tool_input)
        elif tool_name == "get_config_parameters":
            return self.get_config_parameters(**tool_input)
        elif tool_name == "project_social_security":
            return self.project_social_security(**tool_input)
        elif tool_name == "social_security_reform":
            return self.social_security_reform(**tool_input)
        elif tool_name == "project_federal_revenues":
            return self.project_federal_revenues(**tool_input)
        elif tool_name == "tax_reform_analysis":
            return self.tax_reform_analysis(**tool_input)
        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP request from AI agent.

        Args:
            request: MCP request dictionary

        Returns:
            MCP response
        """
        request_type = request.get("type")

        if request_type == "list_tools":
            return {"type": "list_tools_response", "tools": self.list_tools()}

        elif request_type == "call_tool":
            tool_name = request.get("name")
            tool_input = request.get("input", {})
            result = self.call_tool(tool_name, tool_input)
            return {
                "type": "call_tool_response",
                "name": tool_name,
                "result": result,
            }

        else:
            return {
                "type": "error",
                "message": f"Unknown request type: {request_type}",
            }


def main():
    """Run MCP server in interactive mode or process stdin."""
    server = PolisimMCPServer()

    print("POLISIM MCP Server initialized", file=sys.stderr)
    print(f"Available tools: {len(server.list_tools())}", file=sys.stderr)

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                response = server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError as e:
                error_response = {
                    "type": "error",
                    "message": f"Invalid JSON: {str(e)}",
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    "type": "error",
                    "message": f"Server error: {str(e)}",
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("MCP Server stopped", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()
