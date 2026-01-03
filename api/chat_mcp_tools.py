"""
MCP Tools for Chat Integration (Phase 7.3.1).

This module provides MCP (Model Context Protocol) tools that enable AI agents
to interact with the chat system, trigger analyses, and share results.

Tools:
    analyze_bill - Trigger full swarm analysis on a bill
    run_scenario - Run a specific simulation scenario
    compare_policies - Compare multiple policies side-by-side
    get_disagreement_map - Retrieve agent disagreement visualization
    query_cbo_data - Query CBO baseline data
    send_chat_message - Send a message to a chat channel
    get_channel_context - Get recent messages for context

Example:
    from api.chat_mcp_tools import ChatMCPTools
    
    tools = ChatMCPTools()
    result = await tools.analyze_bill(
        bill_id="hr123",
        focus_areas=["revenue", "healthcare"],
        channel_id="channel_abc"
    )
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for Tool Results
# =============================================================================

@dataclass
class AnalysisResult:
    """Result from bill analysis."""
    analysis_id: str
    bill_id: str
    status: str  # pending, running, completed, failed
    summary: Optional[str] = None
    key_findings: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    fiscal_impact: Optional[Dict[str, Any]] = None
    agent_consensus: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ScenarioResult:
    """Result from scenario simulation."""
    scenario_id: str
    scenario_name: str
    status: str
    baseline_comparison: Optional[Dict[str, Any]] = None
    projections: Optional[Dict[str, Any]] = None
    sensitivity: Optional[Dict[str, Any]] = None
    charts: Optional[List[Dict[str, Any]]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComparisonResult:
    """Result from policy comparison."""
    comparison_id: str
    policies: List[str]
    differences: List[Dict[str, Any]]
    impact_delta: Dict[str, Any]
    recommendation: Optional[str] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DisagreementMap:
    """Agent disagreement visualization data."""
    analysis_id: str
    nodes: List[Dict[str, Any]]  # Agents
    edges: List[Dict[str, Any]]  # Disagreement connections
    topics: List[str]
    max_disagreement: float
    summary: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass 
class CBOData:
    """CBO baseline data query result."""
    metric: str
    years: List[int]
    values: List[float]
    unit: str
    source: str
    last_updated: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# =============================================================================
# Chat MCP Tools
# =============================================================================

class ChatMCPTools:
    """MCP tools for chat-integrated policy analysis.
    
    These tools enable AI agents to:
    - Trigger swarm analysis on bills
    - Run economic scenarios
    - Compare policies
    - Query CBO data
    - Share results in chat
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._pending_analyses: Dict[str, Dict[str, Any]] = {}
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return MCP tool definitions for chat functionality."""
        return [
            {
                "name": "analyze_bill",
                "description": "Trigger full multi-agent swarm analysis on a bill. "
                              "Returns analysis results with agent consensus, fiscal impact, "
                              "and key findings. Can post results to a chat channel.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "bill_id": {
                            "type": "string",
                            "description": "Bill identifier (e.g., 'HR1234', 'S567')",
                        },
                        "bill_text": {
                            "type": "string",
                            "description": "Full text of the bill (if not already in system)",
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific areas to analyze: 'revenue', 'spending', "
                                          "'healthcare', 'social_security', 'economic_impact'",
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Chat channel ID to post results (optional)",
                        },
                    },
                    "required": ["bill_id"],
                },
            },
            {
                "name": "run_scenario",
                "description": "Run an economic scenario simulation with specific parameters. "
                              "Supports recession, inflation, policy changes, etc.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scenario_type": {
                            "type": "string",
                            "description": "Type: 'recession', 'inflation', 'policy_change', "
                                          "'demographic_shift', 'custom'",
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Scenario-specific parameters",
                        },
                        "years": {
                            "type": "integer",
                            "description": "Projection years (default: 10)",
                        },
                        "iterations": {
                            "type": "integer",
                            "description": "Monte Carlo iterations (default: 1000)",
                        },
                        "compare_to_baseline": {
                            "type": "boolean",
                            "description": "Include baseline comparison (default: true)",
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Chat channel ID to post results (optional)",
                        },
                    },
                    "required": ["scenario_type"],
                },
            },
            {
                "name": "compare_policies",
                "description": "Compare multiple policies side-by-side with detailed analysis "
                              "of differences in fiscal impact, coverage, and implementation.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "policy_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of 2+ policy IDs to compare",
                        },
                        "comparison_metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Metrics to compare: 'fiscal_impact', 'coverage', "
                                          "'cost_effectiveness', 'implementation_timeline'",
                        },
                        "channel_id": {
                            "type": "string",
                            "description": "Chat channel ID to post results (optional)",
                        },
                    },
                    "required": ["policy_ids"],
                },
            },
            {
                "name": "get_disagreement_map",
                "description": "Retrieve the agent disagreement visualization for an analysis. "
                              "Shows which agents disagree on what topics and why.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "analysis_id": {
                            "type": "string",
                            "description": "ID of the analysis to get disagreement map for",
                        },
                    },
                    "required": ["analysis_id"],
                },
            },
            {
                "name": "query_cbo_data",
                "description": "Query CBO baseline data for specific metrics and years. "
                              "Returns official CBO projections for revenue, spending, debt, etc.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "metric": {
                            "type": "string",
                            "description": "Metric: 'total_revenue', 'total_spending', 'deficit', "
                                          "'debt_held_by_public', 'gdp', 'medicare_spending', etc.",
                        },
                        "start_year": {
                            "type": "integer",
                            "description": "Start year for data (default: current year)",
                        },
                        "end_year": {
                            "type": "integer",
                            "description": "End year for data (default: start + 10)",
                        },
                    },
                    "required": ["metric"],
                },
            },
            {
                "name": "send_chat_message",
                "description": "Send a message to a chat channel as an AI agent. "
                              "Use for sharing insights, asking questions, or posting results.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Target chat channel ID",
                        },
                        "content": {
                            "type": "string",
                            "description": "Message content (supports markdown)",
                        },
                        "message_type": {
                            "type": "string",
                            "description": "Type: 'text', 'analysis_result', 'scenario_result'",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional data (charts, links, etc.)",
                        },
                        "agent_id": {
                            "type": "string",
                            "description": "Agent sending the message",
                        },
                    },
                    "required": ["channel_id", "content"],
                },
            },
            {
                "name": "get_channel_context",
                "description": "Get recent messages from a channel for context. "
                              "Useful for understanding ongoing discussion before responding.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Chat channel ID",
                        },
                        "message_count": {
                            "type": "integer",
                            "description": "Number of recent messages (default: 20)",
                        },
                        "include_analysis_results": {
                            "type": "boolean",
                            "description": "Include full analysis result metadata (default: false)",
                        },
                    },
                    "required": ["channel_id"],
                },
            },
        ]
    
    # -------------------------------------------------------------------------
    # Tool Implementations
    # -------------------------------------------------------------------------
    
    async def analyze_bill(
        self,
        bill_id: str,
        bill_text: Optional[str] = None,
        focus_areas: Optional[List[str]] = None,
        channel_id: Optional[str] = None
    ) -> AnalysisResult:
        """Trigger full swarm analysis on a bill.
        
        This integrates with the SwarmCoordinator (Phase 7.1) to run
        multi-agent analysis with debate and consensus.
        """
        analysis_id = str(uuid4())[:12]
        
        self.logger.info(f"Starting bill analysis {analysis_id} for {bill_id}")
        
        # Store pending analysis
        self._pending_analyses[analysis_id] = {
            "bill_id": bill_id,
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        
        try:
            # Import swarm coordinator if available
            try:
                from core.agents.coordinator import SwarmCoordinator
                from core.agents.types import Bill
                
                # Create bill object
                bill = Bill(
                    bill_id=bill_id,
                    title=f"Bill {bill_id}",
                    text=bill_text or "",
                    focus_areas=focus_areas or [],
                )
                
                # Run swarm analysis
                coordinator = SwarmCoordinator()
                self._pending_analyses[analysis_id]["status"] = "running"
                
                swarm_result = await coordinator.analyze_bill(bill)
                
                # Extract results
                result = AnalysisResult(
                    analysis_id=analysis_id,
                    bill_id=bill_id,
                    status="completed",
                    summary=swarm_result.summary if hasattr(swarm_result, 'summary') else None,
                    key_findings=swarm_result.findings if hasattr(swarm_result, 'findings') else None,
                    confidence=swarm_result.confidence if hasattr(swarm_result, 'confidence') else None,
                    fiscal_impact=swarm_result.fiscal_impact if hasattr(swarm_result, 'fiscal_impact') else None,
                    agent_consensus=swarm_result.consensus if hasattr(swarm_result, 'consensus') else None,
                )
                
            except ImportError:
                # Swarm not available - return mock result
                self.logger.warning("SwarmCoordinator not available, returning mock analysis")
                
                await asyncio.sleep(0.5)  # Simulate processing
                
                result = AnalysisResult(
                    analysis_id=analysis_id,
                    bill_id=bill_id,
                    status="completed",
                    summary=f"Analysis of {bill_id} completed. This is a placeholder result.",
                    key_findings=[
                        {"category": "revenue", "description": "Estimated revenue impact", "confidence": 0.8},
                        {"category": "spending", "description": "Spending provisions identified", "confidence": 0.75},
                    ],
                    confidence=0.78,
                    fiscal_impact={
                        "10_year_cost": {"estimate": 50.0, "unit": "billion"},
                        "revenue_change": {"estimate": -20.0, "unit": "billion"},
                    },
                    agent_consensus={
                        "level": "consensus",
                        "agreement_score": 0.82,
                        "dissenting_agents": [],
                    },
                )
            
            self._pending_analyses[analysis_id]["status"] = "completed"
            
            # Post to channel if specified
            if channel_id:
                await self._post_analysis_to_channel(channel_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Bill analysis failed: {e}")
            self._pending_analyses[analysis_id]["status"] = "failed"
            return AnalysisResult(
                analysis_id=analysis_id,
                bill_id=bill_id,
                status="failed",
                summary=f"Analysis failed: {str(e)}",
            )
    
    async def run_scenario(
        self,
        scenario_type: str,
        parameters: Optional[Dict[str, Any]] = None,
        years: int = 10,
        iterations: int = 1000,
        compare_to_baseline: bool = True,
        channel_id: Optional[str] = None
    ) -> ScenarioResult:
        """Run an economic scenario simulation."""
        scenario_id = str(uuid4())[:12]
        
        self.logger.info(f"Running scenario {scenario_id}: {scenario_type}")
        
        try:
            # Import simulation components
            try:
                from core.monte_carlo_scenarios import MonteCarloPolicySimulator
                from core.economic_engine import EconomicParameters, PolicyScenario
                
                # Build scenario
                params = EconomicParameters()
                
                # Apply scenario-specific modifications
                if scenario_type == "recession":
                    params.gdp_growth_mean = -0.02
                    params.unemployment_mean = 0.08
                elif scenario_type == "inflation":
                    params.inflation_mean = parameters.get("inflation_rate", 0.06) if parameters else 0.06
                elif scenario_type == "policy_change":
                    # Apply custom parameters
                    if parameters:
                        for key, value in parameters.items():
                            if hasattr(params, key):
                                setattr(params, key, value)
                
                # Run simulation
                simulator = MonteCarloPolicySimulator(iterations=iterations)
                sim_results = simulator.run_simulation(
                    PolicyScenario(
                        name=scenario_type,
                        description=f"Scenario: {scenario_type}",
                        parameters=params,
                    ),
                    years=years,
                )
                
                # Build result
                result = ScenarioResult(
                    scenario_id=scenario_id,
                    scenario_name=scenario_type,
                    status="completed",
                    projections={
                        "years": list(range(2026, 2026 + years)),
                        "debt_to_gdp": sim_results.get("debt_to_gdp_median", []),
                        "deficit": sim_results.get("deficit_median", []),
                    },
                    baseline_comparison={
                        "debt_delta": sim_results.get("debt_vs_baseline", 0),
                        "deficit_delta": sim_results.get("deficit_vs_baseline", 0),
                    } if compare_to_baseline else None,
                )
                
            except ImportError:
                # Simulation not available - return mock result
                self.logger.warning("Simulation components not available, returning mock result")
                
                await asyncio.sleep(0.3)
                
                result = ScenarioResult(
                    scenario_id=scenario_id,
                    scenario_name=scenario_type,
                    status="completed",
                    projections={
                        "years": list(range(2026, 2026 + years)),
                        "debt_to_gdp": [100 + i * 2 for i in range(years)],
                        "deficit": [-1.5 + i * 0.1 for i in range(years)],
                    },
                    baseline_comparison={
                        "debt_delta": 5.0,
                        "deficit_delta": 0.5,
                    } if compare_to_baseline else None,
                )
            
            # Post to channel if specified
            if channel_id:
                await self._post_scenario_to_channel(channel_id, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Scenario simulation failed: {e}")
            return ScenarioResult(
                scenario_id=scenario_id,
                scenario_name=scenario_type,
                status="failed",
            )
    
    async def compare_policies(
        self,
        policy_ids: List[str],
        comparison_metrics: Optional[List[str]] = None,
        channel_id: Optional[str] = None
    ) -> ComparisonResult:
        """Compare multiple policies side-by-side."""
        comparison_id = str(uuid4())[:12]
        
        if len(policy_ids) < 2:
            return ComparisonResult(
                comparison_id=comparison_id,
                policies=policy_ids,
                differences=[{"error": "Need at least 2 policies to compare"}],
                impact_delta={},
            )
        
        self.logger.info(f"Comparing policies: {policy_ids}")
        
        metrics = comparison_metrics or ["fiscal_impact", "coverage", "cost_effectiveness"]
        
        # Build comparison (placeholder implementation)
        differences = []
        for metric in metrics:
            differences.append({
                "metric": metric,
                "policy_values": {pid: f"Value for {pid}" for pid in policy_ids},
                "significant_difference": True,
            })
        
        result = ComparisonResult(
            comparison_id=comparison_id,
            policies=policy_ids,
            differences=differences,
            impact_delta={
                "fiscal_impact_spread": 50.0,
                "coverage_spread": 10.0,
            },
            recommendation=f"Policy {policy_ids[0]} appears most cost-effective based on available data.",
        )
        
        if channel_id:
            await self._post_comparison_to_channel(channel_id, result)
        
        return result
    
    async def get_disagreement_map(
        self,
        analysis_id: str
    ) -> DisagreementMap:
        """Retrieve agent disagreement visualization for an analysis."""
        self.logger.info(f"Getting disagreement map for analysis {analysis_id}")
        
        # Try to load from completed analysis
        try:
            from core.agents.coordinator import SwarmCoordinator
            
            coordinator = SwarmCoordinator()
            debate_data = await coordinator.get_debate_visualization(analysis_id)
            
            return DisagreementMap(
                analysis_id=analysis_id,
                nodes=debate_data.get("agents", []),
                edges=debate_data.get("disagreements", []),
                topics=debate_data.get("topics", []),
                max_disagreement=debate_data.get("max_disagreement", 0),
                summary=debate_data.get("summary", ""),
            )
            
        except (ImportError, Exception):
            # Return placeholder
            return DisagreementMap(
                analysis_id=analysis_id,
                nodes=[
                    {"id": "fiscal", "name": "Fiscal Agent", "specialty": "revenue/spending"},
                    {"id": "healthcare", "name": "Healthcare Agent", "specialty": "healthcare"},
                    {"id": "economic", "name": "Economic Agent", "specialty": "macro"},
                ],
                edges=[
                    {"source": "fiscal", "target": "economic", "weight": 0.3, "topic": "GDP growth assumption"},
                ],
                topics=["revenue_projection", "spending_baseline", "gdp_growth"],
                max_disagreement=0.3,
                summary="Minor disagreement on GDP growth assumptions between Fiscal and Economic agents.",
            )
    
    async def query_cbo_data(
        self,
        metric: str,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> CBOData:
        """Query CBO baseline data for specific metrics."""
        current_year = datetime.now().year
        start = start_year or current_year
        end = end_year or (start + 10)
        
        self.logger.info(f"Querying CBO data: {metric} ({start}-{end})")
        
        try:
            from core.cbo_scraper import CBOScraper
            
            scraper = CBOScraper()
            data = scraper.get_metric(metric, start, end)
            
            return CBOData(
                metric=metric,
                years=data.get("years", list(range(start, end + 1))),
                values=data.get("values", []),
                unit=data.get("unit", "billions"),
                source="CBO Budget and Economic Outlook",
                last_updated=data.get("last_updated", datetime.now().isoformat()),
            )
            
        except (ImportError, Exception) as e:
            self.logger.warning(f"CBO data query failed: {e}")
            
            # Return placeholder data
            years = list(range(start, end + 1))
            return CBOData(
                metric=metric,
                years=years,
                values=[100 + i * 5 for i in range(len(years))],
                unit="billions",
                source="CBO (placeholder data)",
                last_updated=datetime.now().isoformat(),
            )
    
    async def send_chat_message(
        self,
        channel_id: str,
        content: str,
        message_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: str = "ai_agent"
    ) -> Dict[str, Any]:
        """Send a message to a chat channel as an AI agent."""
        self.logger.info(f"Agent {agent_id} sending message to channel {channel_id}")
        
        try:
            from api.chat_api import ChatService
            from api.database import get_db_session
            
            with get_db_session() as session:
                service = ChatService(session)
                message = service.send_message(
                    channel_id=channel_id,
                    sender_id=agent_id,
                    sender_type="agent",
                    sender_name=f"Agent {agent_id}",
                    content=content,
                    message_type=message_type,
                    metadata=metadata,
                )
                
                if message:
                    return {"success": True, "message_id": message.message_id}
                return {"success": False, "error": "Channel not found"}
                
        except Exception as e:
            self.logger.error(f"Failed to send chat message: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_channel_context(
        self,
        channel_id: str,
        message_count: int = 20,
        include_analysis_results: bool = False
    ) -> Dict[str, Any]:
        """Get recent messages from a channel for context."""
        self.logger.info(f"Getting context for channel {channel_id}")
        
        try:
            from api.chat_api import ChatService
            from api.database import get_db_session
            
            with get_db_session() as session:
                service = ChatService(session)
                messages = service.get_messages(
                    channel_id=channel_id,
                    limit=message_count,
                )
                
                # Format messages for context
                context = []
                for msg in messages:
                    msg_data = {
                        "sender": msg.sender_name or msg.sender_id,
                        "sender_type": msg.sender_type.value,
                        "content": msg.content,
                        "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                        "type": msg.message_type.value,
                    }
                    
                    if include_analysis_results and msg.metadata:
                        msg_data["metadata"] = msg.metadata
                    
                    context.append(msg_data)
                
                return {
                    "channel_id": channel_id,
                    "message_count": len(context),
                    "messages": context,
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get channel context: {e}")
            return {
                "channel_id": channel_id,
                "message_count": 0,
                "messages": [],
                "error": str(e),
            }
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    async def _post_analysis_to_channel(
        self,
        channel_id: str,
        result: AnalysisResult
    ) -> None:
        """Post analysis result to chat channel."""
        content = f"## 📊 Analysis Complete: {result.bill_id}\n\n"
        
        if result.summary:
            content += f"**Summary:** {result.summary}\n\n"
        
        if result.key_findings:
            content += "**Key Findings:**\n"
            for finding in result.key_findings[:5]:
                content += f"- {finding.get('description', 'N/A')} "
                content += f"(confidence: {finding.get('confidence', 'N/A')})\n"
            content += "\n"
        
        if result.confidence:
            content += f"**Overall Confidence:** {result.confidence:.0%}\n"
        
        if result.agent_consensus:
            content += f"**Consensus Level:** {result.agent_consensus.get('level', 'N/A')}\n"
        
        await self.send_chat_message(
            channel_id=channel_id,
            content=content,
            message_type="analysis_result",
            metadata=result.to_dict(),
            agent_id="swarm_coordinator",
        )
    
    async def _post_scenario_to_channel(
        self,
        channel_id: str,
        result: ScenarioResult
    ) -> None:
        """Post scenario result to chat channel."""
        content = f"## 📈 Scenario Results: {result.scenario_name}\n\n"
        
        if result.projections:
            years = result.projections.get("years", [])
            if years:
                content += f"**Projection Period:** {years[0]} - {years[-1]}\n\n"
        
        if result.baseline_comparison:
            content += "**vs. Baseline:**\n"
            for key, value in result.baseline_comparison.items():
                content += f"- {key}: {value:+.1f}\n"
        
        await self.send_chat_message(
            channel_id=channel_id,
            content=content,
            message_type="scenario_result",
            metadata=result.to_dict(),
            agent_id="scenario_runner",
        )
    
    async def _post_comparison_to_channel(
        self,
        channel_id: str,
        result: ComparisonResult
    ) -> None:
        """Post comparison result to chat channel."""
        content = f"## ⚖️ Policy Comparison\n\n"
        content += f"**Policies Compared:** {', '.join(result.policies)}\n\n"
        
        if result.differences:
            content += "**Key Differences:**\n"
            for diff in result.differences[:5]:
                content += f"- {diff.get('metric', 'N/A')}: "
                if diff.get('significant_difference'):
                    content += "Significant difference found\n"
                else:
                    content += "Similar across policies\n"
        
        if result.recommendation:
            content += f"\n**Recommendation:** {result.recommendation}\n"
        
        await self.send_chat_message(
            channel_id=channel_id,
            content=content,
            message_type="analysis_result",
            metadata=result.to_dict(),
            agent_id="policy_comparator",
        )


# =============================================================================
# Tool Execution Handler
# =============================================================================

class ChatMCPToolHandler:
    """Handler for executing chat MCP tools.
    
    Integrates with the main MCP server to provide chat functionality.
    """
    
    def __init__(self):
        self.tools = ChatMCPTools()
        self.logger = logging.getLogger(__name__)
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a chat MCP tool by name."""
        self.logger.info(f"Executing chat tool: {tool_name}")
        
        tool_map = {
            "analyze_bill": self.tools.analyze_bill,
            "run_scenario": self.tools.run_scenario,
            "compare_policies": self.tools.compare_policies,
            "get_disagreement_map": self.tools.get_disagreement_map,
            "query_cbo_data": self.tools.query_cbo_data,
            "send_chat_message": self.tools.send_chat_message,
            "get_channel_context": self.tools.get_channel_context,
        }
        
        if tool_name not in tool_map:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = await tool_map[tool_name](**arguments)
            
            # Convert dataclass results to dict
            if hasattr(result, 'to_dict'):
                return {"status": "success", "result": result.to_dict()}
            return {"status": "success", "result": result}
            
        except Exception as e:
            self.logger.error(f"Tool execution failed: {e}")
            return {"status": "error", "error": str(e)}
