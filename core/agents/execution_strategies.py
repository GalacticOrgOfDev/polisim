"""Execution strategies for agent orchestration.

This module provides different strategies for executing agents in the
swarm, allowing flexible control over parallelism, ordering, and
resource allocation.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Awaitable, Dict, List, Optional, Set
from enum import Enum

from core.agents.types import AgentType, AnalysisEventType
from core.agents.models import AgentAnalysis, AgentConfig, AnalysisEvent
from core.agents.base_agent import BaseAgent, AnalysisContext


logger = logging.getLogger(__name__)


class ExecutionStrategyType(Enum):
    """Types of execution strategies."""
    
    ALL_AT_ONCE = "all_at_once"      # Launch all agents simultaneously
    STAGED = "staged"                 # Run in dependency order
    ADAPTIVE = "adaptive"             # Add agents based on initial findings
    ROUND_ROBIN = "round_robin"       # Execute one at a time in rotation
    PRIORITY = "priority"             # Execute by priority order


@dataclass
class ExecutionResult:
    """Result of agent execution."""
    
    agent_id: str
    agent_type: AgentType
    analysis: Optional[AgentAnalysis] = None
    success: bool = True
    error: Optional[str] = None
    execution_time_seconds: float = 0.0
    retries: int = 0


@dataclass
class ExecutionStats:
    """Statistics about execution."""
    
    total_agents: int = 0
    successful: int = 0
    failed: int = 0
    timed_out: int = 0
    total_time_seconds: float = 0.0
    total_tokens: int = 0
    results: List[ExecutionResult] = field(default_factory=list)


@dataclass
class ResourceBudget:
    """Resource budget for execution."""
    
    max_concurrent: int = 8
    max_tokens_total: int = 100000
    max_tokens_per_agent: int = 20000
    timeout_per_agent_seconds: float = 60.0
    timeout_total_seconds: float = 300.0
    
    # Tracking
    tokens_used: int = 0
    agents_active: int = 0
    
    def can_start_agent(self) -> bool:
        """Check if we can start another agent."""
        return (
            self.agents_active < self.max_concurrent and
            self.tokens_used < self.max_tokens_total
        )
    
    def register_agent_start(self) -> None:
        """Register that an agent has started."""
        self.agents_active += 1
    
    def register_agent_complete(self, tokens: int) -> None:
        """Register that an agent has completed."""
        self.agents_active -= 1
        self.tokens_used += tokens


class ExecutionStrategy(ABC):
    """Abstract base class for execution strategies.
    
    Execution strategies control how agents are scheduled and run,
    allowing for different parallelism models and resource management.
    """
    
    def __init__(
        self,
        budget: Optional[ResourceBudget] = None,
        event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None,
    ):
        self.budget = budget or ResourceBudget()
        self.event_callback = event_callback
    
    @abstractmethod
    async def execute(
        self,
        agents: Dict[str, BaseAgent],
        context: AnalysisContext,
    ) -> ExecutionStats:
        """Execute agents according to the strategy.
        
        Args:
            agents: Dictionary of agent_id -> agent
            context: Analysis context
        
        Returns:
            ExecutionStats with results
        """
        pass
    
    async def _execute_single_agent(
        self,
        agent: BaseAgent,
        context: AnalysisContext,
    ) -> ExecutionResult:
        """Execute a single agent with error handling.
        
        Args:
            agent: The agent to execute
            context: Analysis context
        
        Returns:
            ExecutionResult
        """
        start_time = datetime.now()
        result = ExecutionResult(
            agent_id=agent.agent_id,
            agent_type=agent.agent_type,
        )
        
        try:
            self.budget.register_agent_start()
            
            if self.event_callback:
                await self.event_callback(AnalysisEvent(
                    event_type=AnalysisEventType.AGENT_STARTED,
                    analysis_id=context.bill_id,
                    agent_id=agent.agent_id,
                    data={"agent_type": agent.agent_type.value},
                ))
            
            # Execute with timeout
            analysis = await asyncio.wait_for(
                agent.analyze(context, self.event_callback),
                timeout=self.budget.timeout_per_agent_seconds,
            )
            
            result.analysis = analysis
            result.success = True
            
            if self.event_callback:
                await self.event_callback(AnalysisEvent(
                    event_type=AnalysisEventType.AGENT_COMPLETED,
                    analysis_id=context.bill_id,
                    agent_id=agent.agent_id,
                    data={
                        "findings_count": len(analysis.findings),
                        "confidence": analysis.overall_confidence,
                    },
                ))
            
        except asyncio.TimeoutError:
            logger.warning(f"Agent {agent.agent_id} timed out")
            result.success = False
            result.error = "Timeout"
            
        except Exception as e:
            logger.error(f"Agent {agent.agent_id} failed: {e}")
            result.success = False
            result.error = str(e)
            
        finally:
            elapsed = (datetime.now() - start_time).total_seconds()
            result.execution_time_seconds = elapsed
            
            tokens = result.analysis.tokens_used if result.analysis else 0
            self.budget.register_agent_complete(tokens)
        
        return result


class AllAtOnceStrategy(ExecutionStrategy):
    """Execute all agents simultaneously.
    
    This is the most parallel approach - all agents start at once.
    Best for independent analyses where agents don't need each other's results.
    """
    
    async def execute(
        self,
        agents: Dict[str, BaseAgent],
        context: AnalysisContext,
    ) -> ExecutionStats:
        """Execute all agents in parallel."""
        logger.info(f"Executing {len(agents)} agents with all-at-once strategy")
        
        start_time = datetime.now()
        stats = ExecutionStats(total_agents=len(agents))
        
        # Create tasks for all agents
        tasks = [
            self._execute_single_agent(agent, context)
            for agent in agents.values()
        ]
        
        # Execute all with global timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.budget.timeout_total_seconds,
            )
        except asyncio.TimeoutError:
            logger.error("Global timeout reached")
            results = []
        
        # Process results
        for result in results:
            if isinstance(result, ExecutionResult):
                stats.results.append(result)
                if result.success:
                    stats.successful += 1
                elif result.error == "Timeout":
                    stats.timed_out += 1
                else:
                    stats.failed += 1
                stats.total_tokens += (
                    result.analysis.tokens_used if result.analysis else 0
                )
        
        stats.total_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"All-at-once execution complete: {stats.successful}/{stats.total_agents} "
            f"successful in {stats.total_time_seconds:.1f}s"
        )
        
        return stats


class StagedStrategy(ExecutionStrategy):
    """Execute agents in dependency order.
    
    Agents are grouped into stages based on their dependencies.
    Each stage completes before the next begins.
    
    Example stages:
    1. Fiscal agent (provides baseline numbers)
    2. Economic agent (needs fiscal context)
    3. Healthcare, Social Security (can use economic projections)
    """
    
    # Define stage ordering
    STAGES = [
        [AgentType.FISCAL],                    # Stage 1: Core fiscal first
        [AgentType.ECONOMIC],                  # Stage 2: Economic needs fiscal
        [AgentType.HEALTHCARE, AgentType.SOCIAL_SECURITY],  # Stage 3: Domain experts
        [AgentType.EQUITY, AgentType.IMPLEMENTATION],       # Stage 4: Secondary analysis
    ]
    
    async def execute(
        self,
        agents: Dict[str, BaseAgent],
        context: AnalysisContext,
    ) -> ExecutionStats:
        """Execute agents in staged order."""
        logger.info(f"Executing {len(agents)} agents with staged strategy")
        
        start_time = datetime.now()
        stats = ExecutionStats(total_agents=len(agents))
        
        # Group agents by stage
        staged_agents: List[List[BaseAgent]] = []
        remaining = set(agents.keys())
        
        for stage_types in self.STAGES:
            stage = []
            for agent_id, agent in agents.items():
                if agent_id in remaining and agent.agent_type in stage_types:
                    stage.append(agent)
                    remaining.discard(agent_id)
            if stage:
                staged_agents.append(stage)
        
        # Add any remaining agents to final stage
        if remaining:
            staged_agents.append([agents[aid] for aid in remaining])
        
        # Execute stage by stage
        accumulated_analyses: Dict[str, AgentAnalysis] = {}
        
        for stage_num, stage in enumerate(staged_agents, 1):
            logger.info(f"Executing stage {stage_num} with {len(stage)} agents")
            
            # Enrich context with previous stage results
            enriched_context = self._enrich_context(context, accumulated_analyses)
            
            # Execute stage in parallel
            tasks = [
                self._execute_single_agent(agent, enriched_context)
                for agent in stage
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, ExecutionResult):
                    stats.results.append(result)
                    if result.success:
                        stats.successful += 1
                        if result.analysis:
                            accumulated_analyses[result.agent_id] = result.analysis
                    elif result.error == "Timeout":
                        stats.timed_out += 1
                    else:
                        stats.failed += 1
                    stats.total_tokens += (
                        result.analysis.tokens_used if result.analysis else 0
                    )
        
        stats.total_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Staged execution complete: {stats.successful}/{stats.total_agents} "
            f"successful in {stats.total_time_seconds:.1f}s"
        )
        
        return stats
    
    def _enrich_context(
        self,
        context: AnalysisContext,
        previous_analyses: Dict[str, AgentAnalysis],
    ) -> AnalysisContext:
        """Enrich context with previous stage results.
        
        This allows later-stage agents to build on earlier analyses.
        """
        # For now, add analyses to additional_context
        # In future, could parse findings into structured data
        enriched_additional = dict(context.additional_context)
        
        for agent_id, analysis in previous_analyses.items():
            enriched_additional[f"prior_{agent_id}"] = {
                "executive_summary": analysis.executive_summary,
                "key_takeaways": analysis.key_takeaways,
                "overall_confidence": analysis.overall_confidence,
            }
        
        return AnalysisContext(
            bill_id=context.bill_id,
            bill_text=context.bill_text,
            bill_sections=context.bill_sections,
            extracted_mechanisms=context.extracted_mechanisms,
            baseline_data=context.baseline_data,
            scenario=context.scenario,
            projection_years=context.projection_years,
            additional_context=enriched_additional,
        )


class AdaptiveStrategy(ExecutionStrategy):
    """Adaptively add agents based on initial findings.
    
    Starts with core agents, then adds specialized agents
    based on what the initial analysis reveals.
    
    Example:
    - Start with Fiscal + Economic
    - If healthcare provisions found → add Healthcare agent
    - If SS provisions found → add Social Security agent
    """
    
    # Keywords that trigger additional agents
    TRIGGER_KEYWORDS = {
        AgentType.HEALTHCARE: [
            "medicare", "medicaid", "healthcare", "health insurance",
            "coverage", "hospital", "medical", "aca", "affordable care",
        ],
        AgentType.SOCIAL_SECURITY: [
            "social security", "oasdi", "oasi", "retirement", "benefits",
            "trust fund", "payroll tax", "ssa", "cola",
        ],
        AgentType.EQUITY: [
            "distributional", "income distribution", "poverty", "inequality",
            "progressive", "regressive", "low-income", "high-income",
        ],
    }
    
    async def execute(
        self,
        agents: Dict[str, BaseAgent],
        context: AnalysisContext,
    ) -> ExecutionStats:
        """Execute with adaptive agent selection."""
        logger.info(f"Executing with adaptive strategy")
        
        start_time = datetime.now()
        stats = ExecutionStats(total_agents=0)
        
        # Phase 1: Always run fiscal and economic
        core_types = {AgentType.FISCAL, AgentType.ECONOMIC}
        core_agents = {
            aid: agent for aid, agent in agents.items()
            if agent.agent_type in core_types
        }
        
        stats.total_agents = len(core_agents)
        
        # Execute core agents
        tasks = [
            self._execute_single_agent(agent, context)
            for agent in core_agents.values()
        ]
        
        core_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        accumulated_findings = []
        for result in core_results:
            if isinstance(result, ExecutionResult):
                stats.results.append(result)
                if result.success:
                    stats.successful += 1
                    if result.analysis:
                        accumulated_findings.extend(result.analysis.findings)
                else:
                    stats.failed += 1
        
        # Phase 2: Determine additional agents needed
        additional_agents = self._determine_additional_agents(
            context.bill_text,
            accumulated_findings,
            agents,
            core_agents,
        )
        
        if additional_agents:
            logger.info(f"Adaptive: adding {len(additional_agents)} specialized agents")
            stats.total_agents += len(additional_agents)
            
            tasks = [
                self._execute_single_agent(agent, context)
                for agent in additional_agents.values()
            ]
            
            additional_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in additional_results:
                if isinstance(result, ExecutionResult):
                    stats.results.append(result)
                    if result.success:
                        stats.successful += 1
                    else:
                        stats.failed += 1
        
        stats.total_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Adaptive execution complete: {stats.successful}/{stats.total_agents} "
            f"successful in {stats.total_time_seconds:.1f}s"
        )
        
        return stats
    
    def _determine_additional_agents(
        self,
        bill_text: str,
        findings: List,
        all_agents: Dict[str, BaseAgent],
        already_used: Dict[str, BaseAgent],
    ) -> Dict[str, BaseAgent]:
        """Determine which additional agents to invoke."""
        additional = {}
        bill_text_lower = bill_text.lower()
        
        for agent_type, keywords in self.TRIGGER_KEYWORDS.items():
            # Check if we already have this agent type
            if any(a.agent_type == agent_type for a in already_used.values()):
                continue
            
            # Check if keywords are present in bill text
            if any(kw in bill_text_lower for kw in keywords):
                # Find an agent of this type
                for aid, agent in all_agents.items():
                    if agent.agent_type == agent_type and aid not in already_used:
                        additional[aid] = agent
                        logger.info(f"Adaptive: adding {agent_type.value} agent based on keyword match")
                        break
        
        return additional


class PriorityStrategy(ExecutionStrategy):
    """Execute agents in priority order.
    
    Agents are executed one at a time based on priority,
    allowing earlier agents to potentially inform later ones.
    """
    
    # Priority order (lower = higher priority)
    PRIORITIES = {
        AgentType.FISCAL: 1,
        AgentType.ECONOMIC: 2,
        AgentType.HEALTHCARE: 3,
        AgentType.SOCIAL_SECURITY: 3,
        AgentType.EQUITY: 4,
        AgentType.IMPLEMENTATION: 5,
    }
    
    async def execute(
        self,
        agents: Dict[str, BaseAgent],
        context: AnalysisContext,
    ) -> ExecutionStats:
        """Execute agents in priority order."""
        logger.info(f"Executing {len(agents)} agents with priority strategy")
        
        start_time = datetime.now()
        stats = ExecutionStats(total_agents=len(agents))
        
        # Sort by priority
        sorted_agents = sorted(
            agents.values(),
            key=lambda a: self.PRIORITIES.get(a.agent_type, 99),
        )
        
        # Execute sequentially
        for agent in sorted_agents:
            result = await self._execute_single_agent(agent, context)
            stats.results.append(result)
            
            if result.success:
                stats.successful += 1
            elif result.error == "Timeout":
                stats.timed_out += 1
            else:
                stats.failed += 1
            
            stats.total_tokens += (
                result.analysis.tokens_used if result.analysis else 0
            )
        
        stats.total_time_seconds = (datetime.now() - start_time).total_seconds()
        
        logger.info(
            f"Priority execution complete: {stats.successful}/{stats.total_agents} "
            f"successful in {stats.total_time_seconds:.1f}s"
        )
        
        return stats


def create_execution_strategy(
    strategy_type: ExecutionStrategyType,
    budget: Optional[ResourceBudget] = None,
    event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None,
) -> ExecutionStrategy:
    """Factory function to create execution strategies.
    
    Args:
        strategy_type: Type of strategy to create
        budget: Resource budget
        event_callback: Optional event callback
    
    Returns:
        ExecutionStrategy instance
    """
    strategies = {
        ExecutionStrategyType.ALL_AT_ONCE: AllAtOnceStrategy,
        ExecutionStrategyType.STAGED: StagedStrategy,
        ExecutionStrategyType.ADAPTIVE: AdaptiveStrategy,
        ExecutionStrategyType.PRIORITY: PriorityStrategy,
    }
    
    strategy_class = strategies.get(strategy_type, AllAtOnceStrategy)
    return strategy_class(budget=budget, event_callback=event_callback)
