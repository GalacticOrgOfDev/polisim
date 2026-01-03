"""Data models for the Multi-Agent Swarm system.

This module defines all dataclasses and Pydantic models used for agent
communication, analysis results, debates, and consensus building.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from core.agents.types import (
    AgentType,
    MessageType,
    FindingCategory,
    ImpactMagnitude,
    CritiqueType,
    CritiqueSeverity,
    VoteType,
    ConsensusLevel,
    ThoughtType,
    AnalysisEventType,
)


# =============================================================================
# Configuration Models
# =============================================================================

class AgentConfig(BaseModel):
    """Configuration for an individual agent."""
    
    agent_type: AgentType
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3
    max_tokens: int = 4096
    specialization_prompt: str = ""
    confidence_threshold: float = 0.7
    timeout_seconds: float = 60.0
    retry_attempts: int = 3
    
    # Agent-specific settings
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class SwarmConfig(BaseModel):
    """Configuration for the swarm coordinator."""
    
    # Agent configurations
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    
    # Execution settings
    max_parallel_agents: int = 8
    global_timeout_seconds: float = 300.0
    token_budget_per_analysis: int = 100000
    
    # Debate settings
    max_debate_rounds: int = 3
    convergence_threshold: float = 0.8
    debate_timeout_seconds: float = 180.0
    
    # Consensus settings
    consensus_threshold: float = 0.75
    require_unanimous_on_critical: bool = False
    
    # Streaming settings
    enable_streaming: bool = True
    thought_batch_window_ms: int = 100


# =============================================================================
# Core Analysis Models
# =============================================================================

@dataclass
class FiscalImpact:
    """Quantified fiscal impact of a policy."""
    
    amount_billions: float  # In billions USD
    time_period: str  # e.g., "annual", "10-year", "75-year"
    confidence_low: float  # P10 estimate
    confidence_mid: float  # P50 estimate
    confidence_high: float  # P90 estimate
    is_revenue: bool  # True for revenue, False for spending
    is_recurring: bool = True
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    notes: Optional[str] = None


@dataclass
class Assumption:
    """An assumption used in analysis."""
    
    assumption_id: str = field(default_factory=lambda: str(uuid4())[:8])
    category: str = ""
    description: str = ""
    value: Any = None
    source: Optional[str] = None
    confidence: float = 0.8
    alternatives: List[str] = field(default_factory=list)


@dataclass
class Evidence:
    """Supporting evidence for a finding."""
    
    evidence_id: str = field(default_factory=lambda: str(uuid4())[:8])
    source: str = ""  # e.g., "CBO 2025 Baseline", "SSA Trustees Report"
    description: str = ""
    data_point: Optional[Any] = None
    url: Optional[str] = None
    date: Optional[str] = None
    reliability: float = 0.9  # 0-1 scale


@dataclass
class Finding:
    """A single finding from agent analysis."""
    
    finding_id: str = field(default_factory=lambda: str(uuid4())[:8])
    category: FindingCategory = FindingCategory.OTHER
    description: str = ""
    impact_magnitude: ImpactMagnitude = ImpactMagnitude.MEDIUM
    confidence: float = 0.7
    time_horizon: str = "10-year"
    affected_populations: List[str] = field(default_factory=list)
    fiscal_impact: Optional[FiscalImpact] = None
    supporting_evidence: List[Evidence] = field(default_factory=list)
    assumptions_used: List[str] = field(default_factory=list)
    uncertainty_factors: List[str] = field(default_factory=list)


@dataclass
class AgentAnalysis:
    """Complete analysis output from a single agent."""
    
    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    agent_id: str = ""
    agent_type: AgentType = AgentType.FISCAL
    bill_id: str = ""
    
    # Analysis results
    findings: List[Finding] = field(default_factory=list)
    assumptions_used: List[Assumption] = field(default_factory=list)
    overall_confidence: float = 0.7
    uncertainty_areas: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    model_used: str = ""
    tokens_used: int = 0
    execution_time_seconds: float = 0.0
    
    # Summary
    executive_summary: str = ""
    key_takeaways: List[str] = field(default_factory=list)


# =============================================================================
# Communication Models
# =============================================================================

@dataclass
class AgentMessage:
    """Message exchanged between agents."""
    
    message_id: str = field(default_factory=lambda: str(uuid4()))
    sender: str = ""
    recipients: List[str] = field(default_factory=list)  # Empty = broadcast
    message_type: MessageType = MessageType.BROADCAST
    content: Dict[str, Any] = field(default_factory=dict)
    in_reply_to: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentThought:
    """Intermediate thought during analysis (for streaming)."""
    
    thought_id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    thought_type: ThoughtType = ThoughtType.OBSERVATION
    content: str = ""
    confidence: Optional[float] = None
    related_section: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# Debate Models
# =============================================================================

@dataclass
class Position:
    """An agent's position on a topic."""
    
    position_id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    topic: str = ""
    stance: str = ""  # The position statement
    confidence: float = 0.7
    key_arguments: List[str] = field(default_factory=list)
    supporting_evidence: List[str] = field(default_factory=list)
    acknowledged_weaknesses: List[str] = field(default_factory=list)


@dataclass
class PositionUpdate:
    """A change in an agent's position during debate."""
    
    agent_id: str = ""
    original_position_id: str = ""
    new_stance: str = ""
    new_confidence: float = 0.7
    reason_for_change: str = ""
    influenced_by: List[str] = field(default_factory=list)  # Message IDs
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Critique:
    """A critique of another agent's analysis or position."""
    
    critique_id: str = field(default_factory=lambda: str(uuid4())[:8])
    critic_id: str = ""
    target_id: str = ""
    target_finding_id: Optional[str] = None
    critique_type: CritiqueType = CritiqueType.METHODOLOGY
    severity: CritiqueSeverity = CritiqueSeverity.MODERATE
    argument: str = ""
    suggested_revision: Optional[str] = None
    supporting_evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Rebuttal:
    """Response to a critique."""
    
    rebuttal_id: str = field(default_factory=lambda: str(uuid4())[:8])
    critique_id: str = ""
    rebutter_id: str = ""
    argument: str = ""
    position_change: Optional[PositionUpdate] = None
    acknowledgment: bool = False  # Does rebutter acknowledge valid points?
    remaining_disagreement: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebateRound:
    """A single round of debate between agents."""
    
    round_id: str = field(default_factory=lambda: str(uuid4())[:8])
    round_number: int = 1
    topic: str = ""
    participants: List[str] = field(default_factory=list)
    opening_positions: Dict[str, Position] = field(default_factory=dict)
    critiques: List[Critique] = field(default_factory=list)
    rebuttals: List[Rebuttal] = field(default_factory=list)
    position_updates: Dict[str, PositionUpdate] = field(default_factory=dict)
    convergence_score: float = 0.0  # 0.0 = total disagreement, 1.0 = consensus
    timestamp_start: datetime = field(default_factory=datetime.now)
    timestamp_end: Optional[datetime] = None


@dataclass
class TurningPoint:
    """A significant moment in debate that changed positions."""
    
    round_number: int = 0
    agent_id: str = ""
    description: str = ""
    position_before: str = ""
    position_after: str = ""
    catalyst: str = ""  # What caused the change
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebateTimeline:
    """Complete timeline of a debate."""
    
    debate_id: str = field(default_factory=lambda: str(uuid4()))
    topic: str = ""
    rounds: List[DebateRound] = field(default_factory=list)
    position_trajectory: Dict[str, List[Position]] = field(default_factory=dict)
    key_turning_points: List[TurningPoint] = field(default_factory=list)
    final_convergence: float = 0.0
    judge_involved: bool = False


# =============================================================================
# Voting & Consensus Models
# =============================================================================

@dataclass
class Vote:
    """An agent's vote on a proposal."""
    
    vote_id: str = field(default_factory=lambda: str(uuid4())[:8])
    voter_id: str = ""
    proposal_id: str = ""
    support: VoteType = VoteType.NEUTRAL
    confidence: float = 0.7
    reasoning: str = ""
    conditions: List[str] = field(default_factory=list)  # "I support if X"
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Proposal:
    """A proposal to be voted on."""
    
    proposal_id: str = field(default_factory=lambda: str(uuid4())[:8])
    proposer_id: str = ""
    topic: str = ""
    description: str = ""
    supporting_findings: List[str] = field(default_factory=list)
    confidence: float = 0.7
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConsensusFinding:
    """A finding that agents have reached consensus on."""
    
    finding_id: str = field(default_factory=lambda: str(uuid4())[:8])
    description: str = ""
    category: FindingCategory = FindingCategory.OTHER
    consensus_level: ConsensusLevel = ConsensusLevel.CONSENSUS
    weighted_confidence: float = 0.7
    supporting_agents: List[str] = field(default_factory=list)
    dissenting_agents: List[str] = field(default_factory=list)
    dissent_reasons: Dict[str, str] = field(default_factory=dict)


@dataclass
class Disagreement:
    """A tracked disagreement between agents."""
    
    disagreement_id: str = field(default_factory=lambda: str(uuid4())[:8])
    topic: str = ""
    agents_involved: List[str] = field(default_factory=list)
    positions: Dict[str, str] = field(default_factory=dict)
    reason: str = ""
    severity: str = "moderate"  # minor, moderate, major
    resolution_attempted: bool = False
    resolution_method: Optional[str] = None  # debate, vote, judge


@dataclass
class MinorityView:
    """A minority position held by dissenting agents."""
    
    view_id: str = field(default_factory=lambda: str(uuid4())[:8])
    agents: List[str] = field(default_factory=list)
    position: str = ""
    reasoning: str = ""
    evidence: List[str] = field(default_factory=list)


@dataclass
class Uncertainty:
    """A key uncertainty affecting analysis."""
    
    uncertainty_id: str = field(default_factory=lambda: str(uuid4())[:8])
    description: str = ""
    impact_if_wrong: str = ""
    sensitivity: str = "medium"  # low, medium, high
    data_needed_to_resolve: List[str] = field(default_factory=list)


@dataclass
class ConsensusResult:
    """Result of a consensus vote."""
    
    proposal_id: str = ""
    consensus_level: ConsensusLevel = ConsensusLevel.NO_CONSENSUS
    weighted_support: float = 0.0
    votes: List[Vote] = field(default_factory=list)
    passed: bool = False
    conditions_required: List[str] = field(default_factory=list)


@dataclass
class ConsensusReport:
    """Final consensus report from the swarm."""
    
    report_id: str = field(default_factory=lambda: str(uuid4()))
    analysis_id: str = ""
    bill_id: str = ""
    bill_summary: str = ""
    
    # Consensus findings
    agreed_findings: List[ConsensusFinding] = field(default_factory=list)
    confidence_level: ConsensusLevel = ConsensusLevel.CONSENSUS
    
    # Disagreements
    unresolved_disputes: List[Disagreement] = field(default_factory=list)
    minority_views: List[MinorityView] = field(default_factory=list)
    
    # Uncertainty
    key_uncertainties: List[Uncertainty] = field(default_factory=list)
    scenario_sensitivity: Dict[str, Any] = field(default_factory=dict)
    
    # Recommendations
    primary_recommendation: str = ""
    caveats: List[str] = field(default_factory=list)
    further_research_needed: List[str] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    participating_agents: List[str] = field(default_factory=list)


# =============================================================================
# Swarm Analysis Result
# =============================================================================

@dataclass
class AnalysisMetadata:
    """Metadata about the analysis process."""
    
    total_execution_time_seconds: float = 0.0
    total_tokens_used: int = 0
    agents_participated: int = 0
    debate_rounds_conducted: int = 0
    consensus_attempts: int = 0
    model_versions: Dict[str, str] = field(default_factory=dict)
    timestamp_start: datetime = field(default_factory=datetime.now)
    timestamp_end: Optional[datetime] = None


@dataclass
class ConfidenceBand:
    """Confidence band for a metric."""
    
    metric_name: str = ""
    p10: float = 0.0
    p50: float = 0.0
    p90: float = 0.0
    unit: str = ""


@dataclass
class SwarmAnalysis:
    """Complete swarm analysis result."""
    
    analysis_id: str = field(default_factory=lambda: str(uuid4()))
    bill_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Individual agent analyses
    agent_analyses: Dict[str, AgentAnalysis] = field(default_factory=dict)
    
    # Debate results
    debate_timeline: Optional[DebateTimeline] = None
    
    # Consensus
    consensus_findings: List[ConsensusFinding] = field(default_factory=list)
    disagreements: List[Disagreement] = field(default_factory=list)
    confidence_bands: Dict[str, ConfidenceBand] = field(default_factory=dict)
    
    # Final report
    consensus_report: Optional[ConsensusReport] = None
    
    # Metadata
    metadata: AnalysisMetadata = field(default_factory=AnalysisMetadata)


# =============================================================================
# Streaming Event Models
# =============================================================================

@dataclass
class AnalysisEvent:
    """Event for live analysis streaming."""
    
    event_id: str = field(default_factory=lambda: str(uuid4())[:8])
    event_type: AnalysisEventType = AnalysisEventType.PIPELINE_STARTED
    analysis_id: str = ""
    agent_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
