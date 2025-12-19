#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for POLISIM
Enables AI agents to interact with the economic simulation engine as a tool.

Usage:
    python mcp_server.py
"""

import json
import sys
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
from utils.logging_config import setup_logging


class PolisimMCPServer:
    """MCP Server wrapper for POLISIM economic simulation engine."""

    def __init__(self):
        """Initialize the MCP server and load configuration."""
        self.logger = setup_logging("mcp_server")
        self.config = ConfigManager()
        self.logger.info("POLISIM MCP Server initialized")

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
