#!/usr/bin/env python3
"""
Example MCP Client for POLISIM
Demonstrates how to interact with the MCP server programmatically.

Usage:
    # Start server in one terminal:
    python mcp_server.py

    # In another terminal, run this client:
    python mcp_client_example.py
"""

import json
import subprocess
import sys
import time
from typing import Any, Dict, Optional


class PolisimMCPClient:
    """Simple client for interacting with POLISIM MCP server."""

    def __init__(self, server_cmd: str = "python mcp_server.py"):
        """
        Initialize client and start MCP server process.

        Args:
            server_cmd: Command to start server
        """
        self.server_cmd = server_cmd
        self.process = None
        self._start_server()

    def _start_server(self):
        """Start the MCP server process."""
        try:
            print(f"Starting MCP server: {self.server_cmd}", file=sys.stderr)
            self.process = subprocess.Popen(
                self.server_cmd.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            time.sleep(1)  # Give server time to initialize
            print("Server started successfully", file=sys.stderr)
        except Exception as e:
            print(f"Failed to start server: {e}", file=sys.stderr)
            raise

    def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send request to MCP server and receive response.

        Args:
            request: MCP request dictionary

        Returns:
            MCP response dictionary
        """
        try:
            # Send request
            request_json = json.dumps(request)
            self.process.stdin.write(request_json + "\n")
            self.process.stdin.flush()

            # Read response
            response_line = self.process.stdout.readline()
            if not response_line:
                raise RuntimeError("Server closed connection")

            response = json.loads(response_line)
            return response

        except Exception as e:
            print(f"Error communicating with server: {e}", file=sys.stderr)
            raise

    def list_tools(self) -> Dict[str, Any]:
        """List available tools."""
        request = {"type": "list_tools"}
        return self._send_request(request)

    def run_simulation(
        self,
        policy_name: str,
        years: int = 22,
        iterations: int = 10000,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a simulation.

        Args:
            policy_name: Name of policy to simulate
            years: Number of years
            iterations: Number of Monte Carlo iterations
            parameters: Optional parameter overrides

        Returns:
            Simulation results
        """
        request = {
            "type": "call_tool",
            "name": "run_simulation",
            "input": {
                "policy_name": policy_name,
                "years": years,
                "iterations": iterations,
            },
        }
        if parameters:
            request["input"]["parameters"] = parameters

        return self._send_request(request)

    def compare_scenarios(
        self,
        baseline_policy: str,
        alternative_policy: str,
        years: int = 22,
    ) -> Dict[str, Any]:
        """
        Compare two scenarios.

        Args:
            baseline_policy: Baseline policy name
            alternative_policy: Alternative policy name
            years: Number of years

        Returns:
            Comparison results
        """
        request = {
            "type": "call_tool",
            "name": "compare_scenarios",
            "input": {
                "baseline_policy": baseline_policy,
                "alternative_policy": alternative_policy,
                "years": years,
            },
        }
        return self._send_request(request)

    def sensitivity_analysis(
        self,
        policy_name: str,
        parameters: Optional[list] = None,
        variance_percent: float = 20.0,
    ) -> Dict[str, Any]:
        """
        Run sensitivity analysis.

        Args:
            policy_name: Policy name
            parameters: Parameters to analyze
            variance_percent: Variance percentage

        Returns:
            Sensitivity analysis results
        """
        request = {
            "type": "call_tool",
            "name": "sensitivity_analysis",
            "input": {
                "policy_name": policy_name,
                "variance_percent": variance_percent,
            },
        }
        if parameters:
            request["input"]["parameters"] = parameters

        return self._send_request(request)

    def get_policy_catalog(self, filter_keyword: Optional[str] = None) -> Dict[str, Any]:
        """Get available policies."""
        request = {
            "type": "call_tool",
            "name": "get_policy_catalog",
            "input": {},
        }
        if filter_keyword:
            request["input"]["filter"] = filter_keyword

        return self._send_request(request)

    def close(self):
        """Close server connection."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)


def main():
    """Run example client interactions."""
    client = PolisimMCPClient()

    try:
        print("\n" + "=" * 70)
        print("POLISIM MCP CLIENT EXAMPLE")
        print("=" * 70)

        # 1. List available tools
        print("\n1. Listing available tools...")
        tools_response = client.list_tools()
        tools = tools_response.get("tools", [])
        print(f"   Found {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool['name']}: {tool['description']}")

        # 2. Get policy catalog
        print("\n2. Retrieving policy catalog...")
        catalog_response = client.get_policy_catalog()
        if catalog_response["result"]["status"] == "success":
            policies = catalog_response["result"]["results"]["policies"]
            print(f"   Available policies: {policies}")
        else:
            print(f"   Error: {catalog_response['result']['message']}")

        # 3. Run simulation (example policy - will adapt if not found)
        print("\n3. Running simulation...")
        policy_name = "United_States_Galactic_Health_Act"
        sim_response = client.run_simulation(
            policy_name=policy_name, years=22, iterations=10000
        )

        if sim_response["result"]["status"] == "success":
            results = sim_response["result"]["results"]
            print(f"   Policy: {results['policy_name']}")
            print(f"   Years: {results['years']}")
            print(f"   Iterations: {results['iterations']}")
            print(f"   Mean debt (2050): ${results['mean_debt_2050']:,.0f}B")
            print(f"   Std Dev: ${results['std_debt_2050']:,.0f}B")
            print(f"   Percentiles:")
            for pct, value in results["percentiles"].items():
                print(f"      {pct}: ${value:,.0f}B")
        else:
            print(f"   Error: {sim_response['result']['message']}")

        # 4. Run sensitivity analysis
        print("\n4. Running sensitivity analysis...")
        sensitivity_response = client.sensitivity_analysis(
            policy_name=policy_name,
            variance_percent=20.0,
        )

        if sensitivity_response["result"]["status"] == "success":
            print("   Sensitivity analysis complete")
        else:
            print(f"   Error: {sensitivity_response['result']['message']}")

        print("\n" + "=" * 70)
        print("Example completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
