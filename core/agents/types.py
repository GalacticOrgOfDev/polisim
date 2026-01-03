"""Type definitions and enumerations for the Multi-Agent Swarm system.

This module defines all enums and type aliases used throughout the agent
infrastructure for consistent typing and behavior classification.
"""

from enum import Enum, auto
from typing import Dict, List, Any, Optional, Union, TypeVar, Callable, Awaitable


class AgentType(Enum):
    """Classification of specialized agent types."""
    
    # Tier 1 - MVP (Core agents for initial release)
    FISCAL = "fiscal"                    # Revenue, spending, debt analysis
    ECONOMIC = "economic"                # Macro-economic impact
    HEALTHCARE = "healthcare"            # Healthcare policy specialist
    SOCIAL_SECURITY = "social_security"  # SS/retirement analysis
    
    # Tier 2 - v1.1 (High value additions)
    EQUITY = "equity"                    # Distributional impact analysis
    IMPLEMENTATION = "implementation"    # Practical implementation concerns
    
    # Tier 3 - v2.0 (Future enhancements)
    BEHAVIORAL = "behavioral"            # Behavioral economics responses
    LEGAL = "legal"                      # Constitutional/legal feasibility
    
    # Special agents
    JUDGE = "judge"                      # Final arbitration agent
    COORDINATOR = "coordinator"          # Swarm orchestrator


class MessageType(Enum):
    """Types of inter-agent messages."""
    
    ANALYSIS = "analysis"        # Agent's analysis results
    CRITIQUE = "critique"        # Critique of another agent's analysis
    REBUTTAL = "rebuttal"        # Response to a critique
    PROPOSAL = "proposal"        # Proposed conclusion or recommendation
    VOTE = "vote"                # Vote on a proposal
    QUESTION = "question"        # Question to another agent
    CLARIFICATION = "clarification"  # Clarification response
    BROADCAST = "broadcast"      # Message to all agents


class PipelineState(Enum):
    """States of the analysis pipeline state machine."""
    
    INITIALIZED = "initialized"          # Pipeline created, not started
    INGESTING = "ingesting"              # Parsing bill, extracting sections
    ANALYZING = "analyzing"              # Agents analyzing independently
    CROSS_REVIEWING = "cross_reviewing"  # Agents critiquing each other
    DEBATING = "debating"                # Agents discussing disagreements
    VOTING = "voting"                    # Agents voting on proposals
    SYNTHESIZING = "synthesizing"        # Combining into unified report
    COMPLETE = "complete"                # Analysis finished
    ERROR = "error"                      # Pipeline error state


class FindingCategory(Enum):
    """Categories of policy analysis findings."""
    
    # Fiscal categories
    REVENUE = "revenue"                  # Tax revenue impacts
    SPENDING = "spending"                # Government spending impacts
    DEBT = "debt"                        # National debt implications
    DEFICIT = "deficit"                  # Deficit effects
    TRUST_FUND = "trust_fund"            # Trust fund impacts (SS, Medicare)
    
    # Healthcare categories
    COVERAGE = "coverage"                # Healthcare coverage changes
    COST = "cost"                        # Healthcare cost impacts
    QUALITY = "quality"                  # Quality of care implications
    ACCESS = "access"                    # Access to healthcare
    
    # Economic categories
    GDP = "gdp"                          # GDP impact
    EMPLOYMENT = "employment"            # Jobs and employment effects
    INFLATION = "inflation"              # Price level effects
    INTEREST_RATES = "interest_rates"    # Interest rate implications
    PRODUCTIVITY = "productivity"        # Productivity changes
    
    # Social categories
    BENEFITS = "benefits"                # Social program benefits
    ELIGIBILITY = "eligibility"          # Eligibility criteria changes
    DEMOGRAPHICS = "demographics"        # Demographic impact
    DISTRIBUTION = "distribution"        # Distributional effects
    
    # Implementation categories
    ADMINISTRATIVE = "administrative"    # Admin burden/costs
    TIMELINE = "timeline"                # Implementation timeline
    FEASIBILITY = "feasibility"          # Practical feasibility
    
    # Other
    LEGAL = "legal"                      # Legal implications
    BEHAVIORAL = "behavioral"            # Behavioral response effects
    OTHER = "other"                      # Uncategorized findings


class ImpactMagnitude(Enum):
    """Magnitude classification for policy impacts."""
    
    NEGLIGIBLE = "negligible"      # <0.1% change
    LOW = "low"                    # 0.1-1% change
    MEDIUM = "medium"              # 1-5% change
    HIGH = "high"                  # 5-15% change
    TRANSFORMATIVE = "transformative"  # >15% change or structural shift


class CritiqueType(Enum):
    """Types of critiques in agent debates."""
    
    METHODOLOGY = "methodology"    # Issues with analytical approach
    ASSUMPTION = "assumption"      # Problems with underlying assumptions
    EVIDENCE = "evidence"          # Insufficient or contradictory evidence
    LOGIC = "logic"                # Logical errors or gaps
    SCOPE = "scope"                # Missing considerations
    MAGNITUDE = "magnitude"        # Disagreement on impact size
    TIMING = "timing"              # Disagreement on timeline/phasing
    UNCERTAINTY = "uncertainty"    # Inadequate uncertainty quantification


class CritiqueSeverity(Enum):
    """Severity levels for critiques."""
    
    MINOR = "minor"        # Small issue, doesn't change conclusions
    MODERATE = "moderate"  # Notable issue, may affect conclusions
    MAJOR = "major"        # Significant issue, likely affects conclusions
    CRITICAL = "critical"  # Fundamental flaw, invalidates analysis


class VoteType(Enum):
    """Types of votes on proposals."""
    
    STRONGLY_SUPPORT = "strongly_support"  # Weight: 2.0
    SUPPORT = "support"                    # Weight: 1.0
    NEUTRAL = "neutral"                    # Weight: 0.0
    OPPOSE = "oppose"                      # Weight: -1.0
    STRONGLY_OPPOSE = "strongly_oppose"    # Weight: -2.0
    ABSTAIN = "abstain"                    # No weight, does not count


class ConsensusLevel(Enum):
    """Levels of consensus among agents."""
    
    STRONG_CONSENSUS = "strong_consensus"  # >90% weighted agreement
    CONSENSUS = "consensus"                # 75-90% agreement
    MAJORITY = "majority"                  # 60-75% agreement
    DIVIDED = "divided"                    # 40-60% - genuine disagreement
    MINORITY = "minority"                  # <40% - contrarian view
    NO_CONSENSUS = "no_consensus"          # Unable to reach agreement


class ThoughtType(Enum):
    """Types of agent thoughts during analysis (for streaming)."""
    
    OBSERVATION = "observation"      # Noticing something in the bill
    HYPOTHESIS = "hypothesis"        # Forming a hypothesis
    CALCULATION = "calculation"      # Performing calculations
    CONCLUSION = "conclusion"        # Reaching a conclusion
    QUESTION = "question"            # Identifying questions/uncertainties
    REFERENCE = "reference"          # Citing data or sources
    COMPARISON = "comparison"        # Comparing to other policies


class AnalysisEventType(Enum):
    """Event types for live analysis streaming."""
    
    PIPELINE_STARTED = "pipeline_started"
    STAGE_CHANGED = "stage_changed"
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_FINDING = "agent_finding"
    AGENT_COMPLETED = "agent_completed"
    DEBATE_STARTED = "debate_started"
    DEBATE_TURN = "debate_turn"
    DEBATE_CONVERGENCE = "debate_convergence"
    CONSENSUS_REACHED = "consensus_reached"
    ANALYSIS_COMPLETE = "analysis_complete"
    ERROR = "error"


# Type aliases for common patterns
AgentId = str
BillId = str
AnalysisId = str
ProposalId = str
MessageId = str

# Callback type for event streaming
EventCallback = Callable[["AnalysisEvent"], Awaitable[None]]

# Weight mapping for votes
VOTE_WEIGHTS: Dict[VoteType, float] = {
    VoteType.STRONGLY_SUPPORT: 2.0,
    VoteType.SUPPORT: 1.0,
    VoteType.NEUTRAL: 0.0,
    VoteType.OPPOSE: -1.0,
    VoteType.STRONGLY_OPPOSE: -2.0,
    VoteType.ABSTAIN: 0.0,  # Does not count
}

# Consensus thresholds
CONSENSUS_THRESHOLDS = {
    ConsensusLevel.STRONG_CONSENSUS: 0.90,
    ConsensusLevel.CONSENSUS: 0.75,
    ConsensusLevel.MAJORITY: 0.60,
    ConsensusLevel.DIVIDED: 0.40,
    ConsensusLevel.MINORITY: 0.0,
}
