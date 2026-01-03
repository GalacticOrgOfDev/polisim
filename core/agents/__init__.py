"""Multi-Agent Swarm Intelligence Module for PoliSim.

Phase 7 Implementation: AI-native policy analysis platform with specialized
agents that collaborate, debate, and reach consensus on policy analysis.

Core Components:
- BaseAgent: Abstract agent interface for all specialized agents
- SwarmCoordinator: Orchestrates multi-agent analysis pipeline
- JudgeAgent: Final arbitration for unresolved debates

Tier 1 Agents (MVP):
- FiscalAgent: Revenue, spending, debt analysis
- EconomicAgent: Macro-economic impact analysis
- HealthcareAgent: Healthcare policy specialist
- SocialSecurityAgent: SS/retirement analysis

Tier 2 Agents (v1.1):
- EquityAgent: Distributional impact analysis
- ImplementationAgent: Practical implementation concerns

Tier 3 Agents (v2.0 - Future):
- BehavioralAgent: Behavioral economics responses
- LegalAgent: Constitutional/legal feasibility

Usage:
    from core.agents import SwarmCoordinator, FiscalAgent, AgentType
    
    # Create coordinator with agents
    coordinator = SwarmCoordinator(config)
    
    # Analyze a bill
    result = await coordinator.analyze_bill(bill)
"""

from core.agents.types import (
    AgentType,
    MessageType,
    PipelineState,
    FindingCategory,
    ImpactMagnitude,
    CritiqueType,
    CritiqueSeverity,
    VoteType,
    ConsensusLevel,
    ThoughtType,
)

from core.agents.models import (
    AgentConfig,
    AgentAnalysis,
    Finding,
    FiscalImpact,
    Assumption,
    Evidence,
    AgentMessage,
    Critique,
    Rebuttal,
    Position,
    PositionUpdate,
    Vote,
    DebateRound,
    ConsensusFinding,
    Disagreement,
    ConsensusResult,
    ConsensusReport,
    SwarmAnalysis,
    AgentThought,
)

from core.agents.base_agent import BaseAgent
from core.agents.coordinator import SwarmCoordinator
from core.agents.judge_agent import JudgeAgent

# Tier 1 Agents (MVP)
from core.agents.fiscal_agent import FiscalAgent
from core.agents.economic_agent import EconomicAgent
from core.agents.healthcare_agent import HealthcareAgent
from core.agents.social_security_agent import SocialSecurityAgent

# Agent factory
from core.agents.factory import create_agent, AgentFactory

# LLM Client
from core.agents.llm_client import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    LLMProvider,
    get_llm_client,
    configure_llm_client,
)

# Execution strategies
from core.agents.execution_strategies import (
    ExecutionStrategy,
    ExecutionStrategyType,
    ExecutionResult,
    ExecutionStats,
    ResourceBudget,
    AllAtOnceStrategy,
    StagedStrategy,
    AdaptiveStrategy,
    PriorityStrategy,
    create_execution_strategy,
)

# Debate Engine (Phase 7.1.3)
from core.agents.debate_engine import (
    DebateEngine,
    DebateConfig,
    DebateTrigger,
    DebateTriggerType,
    DebateTopic,
    DebateModerator,
    DisagreementMap,
    DisagreementPoint,
    ArgumentQuality,
    AgentDebatePerformance,
    PositionTrajectory,
)

# Consensus Engine (Phase 7.1.4)
from core.agents.consensus_engine import (
    ConsensusEngine,
    ConsensusConfig,
    AgentWeight,
    AgentHistoricalPerformance,
    VotingRound,
    DissentRecord,
    SPECIALTY_MAP,
    calculate_weighted_mean,
    calculate_weighted_confidence_band,
    get_specialty_match_score,
)

__all__ = [
    # Types & Enums
    "AgentType",
    "MessageType",
    "PipelineState",
    "FindingCategory",
    "ImpactMagnitude",
    "CritiqueType",
    "CritiqueSeverity",
    "VoteType",
    "ConsensusLevel",
    "ThoughtType",
    # Models
    "AgentConfig",
    "AgentAnalysis",
    "Finding",
    "FiscalImpact",
    "Assumption",
    "Evidence",
    "AgentMessage",
    "Critique",
    "Rebuttal",
    "Position",
    "PositionUpdate",
    "Vote",
    "DebateRound",
    "ConsensusFinding",
    "Disagreement",
    "ConsensusResult",
    "ConsensusReport",
    "SwarmAnalysis",
    "AgentThought",
    # Core Classes
    "BaseAgent",
    "SwarmCoordinator",
    "JudgeAgent",
    # Tier 1 Agents
    "FiscalAgent",
    "EconomicAgent",
    "HealthcareAgent",
    "SocialSecurityAgent",
    # Factory
    "create_agent",
    "AgentFactory",
    # LLM Client
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "LLMProvider",
    "get_llm_client",
    "configure_llm_client",
    # Execution Strategies
    "ExecutionStrategy",
    "ExecutionStrategyType",
    "ExecutionResult",
    "ExecutionStats",
    "ResourceBudget",
    "AllAtOnceStrategy",
    "StagedStrategy",
    "AdaptiveStrategy",
    "PriorityStrategy",
    "create_execution_strategy",
    # Debate Engine
    "DebateEngine",
    "DebateConfig",
    "DebateTrigger",
    "DebateTriggerType",
    "DebateTopic",
    "DebateModerator",
    "DisagreementMap",
    "DisagreementPoint",
    "ArgumentQuality",
    "AgentDebatePerformance",
    "PositionTrajectory",
    # Consensus Engine (Phase 7.1.4)
    "ConsensusEngine",
    "ConsensusConfig",
    "AgentWeight",
    "AgentHistoricalPerformance",
    "VotingRound",
    "DissentRecord",
    "SPECIALTY_MAP",
    "calculate_weighted_mean",
    "calculate_weighted_confidence_band",
    "get_specialty_match_score",
]
