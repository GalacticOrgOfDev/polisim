"""Consensus Engine for Multi-Agent Policy Analysis.

This module implements a sophisticated consensus-building system where AI agents
vote on proposals, with weighted aggregation based on agent specialty, historical
accuracy, and current analysis confidence.

Key Features:
- Weighted voting system with multiple support levels
- Agent weighting based on specialty match and historical performance
- Consensus level detection (strong consensus, consensus, majority, divided)
- Dissent tracking with minority view capture
- Comprehensive consensus report generation

Phase 7.1.4 Implementation - January 2026
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Awaitable, Dict, List, Optional, Set, Tuple
from uuid import uuid4
import statistics

from core.agents.types import (
    AgentType,
    FindingCategory,
    ImpactMagnitude,
    VoteType,
    ConsensusLevel,
    AnalysisEventType,
    VOTE_WEIGHTS,
    CONSENSUS_THRESHOLDS,
)
from core.agents.models import (
    AgentAnalysis,
    Finding,
    Evidence,
    Vote,
    Proposal,
    ConsensusFinding,
    Disagreement,
    MinorityView,
    Uncertainty,
    ConsensusResult,
    ConsensusReport,
    ConfidenceBand,
    AnalysisEvent,
    Position,
)


logger = logging.getLogger(__name__)


# =============================================================================
# Consensus Configuration
# =============================================================================

@dataclass
class ConsensusConfig:
    """Configuration for consensus behavior."""
    
    # Consensus thresholds
    strong_consensus_threshold: float = 0.90  # >90% weighted agreement
    consensus_threshold: float = 0.75         # 75-90% agreement
    majority_threshold: float = 0.60          # 60-75% agreement
    divided_threshold: float = 0.40           # 40-60% - genuine disagreement
    
    # Voting settings
    require_unanimous_on_critical: bool = False
    minimum_votes_required: int = 2
    allow_abstentions: bool = True
    
    # Agent weighting
    specialty_weight_multiplier: float = 1.5  # Specialists get 50% more weight
    historical_accuracy_weight: float = 0.3   # How much history affects weight
    confidence_weight_factor: float = 0.5     # How much confidence affects weight
    debate_performance_weight: float = 0.2    # Debate quality contribution
    
    # Report generation
    include_minority_views: bool = True
    include_dissent_reasoning: bool = True
    max_uncertainties_in_report: int = 10
    
    # Performance
    voting_timeout_seconds: float = 30.0


# =============================================================================
# Agent Weight Calculation
# =============================================================================

@dataclass
class AgentWeight:
    """Calculated weight for an agent on a specific topic."""
    
    agent_id: str
    base_weight: float = 1.0
    specialty_bonus: float = 0.0
    historical_accuracy_factor: float = 1.0
    confidence_factor: float = 1.0
    debate_performance_factor: float = 1.0
    final_weight: float = 1.0
    
    # Explanation
    calculation_breakdown: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentHistoricalPerformance:
    """Track historical performance of an agent."""
    
    agent_id: str
    total_analyses: int = 0
    accurate_predictions: int = 0
    accuracy_rate: float = 0.5  # Default neutral
    topics_specialized: List[str] = field(default_factory=list)
    average_confidence_calibration: float = 1.0  # 1.0 = well calibrated


# =============================================================================
# Voting Structures
# =============================================================================

@dataclass
class VotingRound:
    """A single round of voting on proposals."""
    
    round_id: str = field(default_factory=lambda: str(uuid4())[:8])
    proposals: List[Proposal] = field(default_factory=list)
    votes: List[Vote] = field(default_factory=list)
    agent_weights: Dict[str, AgentWeight] = field(default_factory=dict)
    results: Dict[str, ConsensusResult] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DissentRecord:
    """Record of dissent on a proposal."""
    
    dissent_id: str = field(default_factory=lambda: str(uuid4())[:8])
    proposal_id: str = ""
    dissenting_agents: List[str] = field(default_factory=list)
    dissent_reasons: Dict[str, str] = field(default_factory=dict)
    dissent_strength: float = 0.0  # Weighted strength of dissent
    conditions_for_support: Dict[str, List[str]] = field(default_factory=dict)


# =============================================================================
# Topic-Agent Specialty Mapping
# =============================================================================

# Map finding categories to specialized agent types
SPECIALTY_MAP: Dict[FindingCategory, List[AgentType]] = {
    # Fiscal categories -> Fiscal Agent
    FindingCategory.REVENUE: [AgentType.FISCAL],
    FindingCategory.SPENDING: [AgentType.FISCAL],
    FindingCategory.DEBT: [AgentType.FISCAL],
    FindingCategory.DEFICIT: [AgentType.FISCAL],
    FindingCategory.TRUST_FUND: [AgentType.FISCAL, AgentType.SOCIAL_SECURITY],
    
    # Healthcare categories -> Healthcare Agent
    FindingCategory.COVERAGE: [AgentType.HEALTHCARE],
    FindingCategory.COST: [AgentType.HEALTHCARE, AgentType.FISCAL],
    FindingCategory.QUALITY: [AgentType.HEALTHCARE],
    FindingCategory.ACCESS: [AgentType.HEALTHCARE],
    
    # Economic categories -> Economic Agent
    FindingCategory.GDP: [AgentType.ECONOMIC],
    FindingCategory.EMPLOYMENT: [AgentType.ECONOMIC],
    FindingCategory.INFLATION: [AgentType.ECONOMIC],
    FindingCategory.INTEREST_RATES: [AgentType.ECONOMIC, AgentType.FISCAL],
    FindingCategory.PRODUCTIVITY: [AgentType.ECONOMIC],
    
    # Social categories -> Social Security Agent
    FindingCategory.BENEFITS: [AgentType.SOCIAL_SECURITY],
    FindingCategory.ELIGIBILITY: [AgentType.SOCIAL_SECURITY, AgentType.HEALTHCARE],
    FindingCategory.DEMOGRAPHICS: [AgentType.SOCIAL_SECURITY, AgentType.ECONOMIC],
    FindingCategory.DISTRIBUTION: [AgentType.EQUITY],
    
    # Implementation categories
    FindingCategory.ADMINISTRATIVE: [AgentType.IMPLEMENTATION],
    FindingCategory.TIMELINE: [AgentType.IMPLEMENTATION],
    FindingCategory.FEASIBILITY: [AgentType.IMPLEMENTATION],
    
    # Other
    FindingCategory.LEGAL: [AgentType.LEGAL],
    FindingCategory.BEHAVIORAL: [AgentType.BEHAVIORAL],
    FindingCategory.OTHER: [],
}


# =============================================================================
# Consensus Engine Core
# =============================================================================

class ConsensusEngine:
    """Engine for building consensus among agents through weighted voting.
    
    The ConsensusEngine handles:
    - Creating proposals from agent findings
    - Calculating agent weights for specific topics
    - Running weighted voting rounds
    - Detecting consensus levels
    - Tracking and preserving dissent
    - Generating comprehensive reports
    
    Example:
        engine = ConsensusEngine(config)
        report = await engine.build_consensus(
            analyses=agent_analyses,
            debate_results=debate_timeline,
            context=analysis_context
        )
    """
    
    def __init__(
        self,
        config: Optional[ConsensusConfig] = None,
        historical_performance: Optional[Dict[str, AgentHistoricalPerformance]] = None,
    ):
        """Initialize the consensus engine.
        
        Args:
            config: Consensus configuration. Uses defaults if not provided.
            historical_performance: Historical performance data for agents.
        """
        self.config = config or ConsensusConfig()
        self.historical_performance = historical_performance or {}
        
        # Runtime state
        self._event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None
        self._voting_rounds: List[VotingRound] = []
        
        logger.info("ConsensusEngine initialized")
    
    # =========================================================================
    # Main Entry Point
    # =========================================================================
    
    async def build_consensus(
        self,
        analyses: List[AgentAnalysis],
        debate_results: Optional[Any] = None,  # DebateTimeline
        context: Optional[Any] = None,  # AnalysisContext
        event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None,
    ) -> ConsensusReport:
        """Build comprehensive consensus from agent analyses.
        
        This is the main entry point. It:
        1. Creates proposals from agent findings
        2. Calculates agent weights
        3. Runs voting on each proposal
        4. Determines consensus levels
        5. Tracks dissent
        6. Generates final report
        
        Args:
            analyses: All agent analyses
            debate_results: Optional debate timeline for context
            context: Analysis context
            event_callback: Optional callback for streaming events
        
        Returns:
            ConsensusReport with findings, disagreements, and recommendations
        """
        self._event_callback = event_callback
        analysis_id = analyses[0].analysis_id if analyses else str(uuid4())
        bill_id = analyses[0].bill_id if analyses else ""
        
        logger.info(f"Building consensus from {len(analyses)} agent analyses")
        
        await self._emit_event(
            AnalysisEventType.STAGE_CHANGED,
            {"stage": "consensus_building", "agent_count": len(analyses)}
        )
        
        # Step 1: Extract proposals from findings
        proposals = self._create_proposals_from_findings(analyses)
        logger.info(f"Created {len(proposals)} proposals from agent findings")
        
        # Step 2: Calculate agent weights
        agent_weights = self._calculate_all_agent_weights(
            analyses, debate_results
        )
        
        # Step 3: Generate votes for each proposal
        votes = self._generate_votes_from_analyses(analyses, proposals)
        
        # Step 4: Run voting round
        voting_round = await self._run_voting_round(
            proposals, votes, agent_weights
        )
        self._voting_rounds.append(voting_round)
        
        # Step 5: Categorize results into consensus/disagreements
        consensus_findings = []
        disagreements = []
        minority_views = []
        
        for proposal_id, result in voting_round.results.items():
            proposal = next((p for p in proposals if p.proposal_id == proposal_id), None)
            if not proposal:
                continue
            
            if result.consensus_level in [ConsensusLevel.STRONG_CONSENSUS, ConsensusLevel.CONSENSUS]:
                consensus_findings.append(self._result_to_consensus_finding(
                    proposal, result, voting_round.votes
                ))
            elif result.consensus_level == ConsensusLevel.MAJORITY:
                # Include as consensus but track minority
                consensus_findings.append(self._result_to_consensus_finding(
                    proposal, result, voting_round.votes
                ))
                minority = self._extract_minority_view(proposal, result, voting_round.votes)
                if minority:
                    minority_views.append(minority)
            else:
                # Divided or no consensus - record disagreement
                disagreements.append(self._result_to_disagreement(
                    proposal, result, voting_round.votes
                ))
        
        # Step 6: Extract uncertainties
        uncertainties = self._extract_uncertainties(analyses)
        
        # Step 7: Generate report
        report = self._generate_consensus_report(
            analysis_id=analysis_id,
            bill_id=bill_id,
            analyses=analyses,
            consensus_findings=consensus_findings,
            disagreements=disagreements,
            minority_views=minority_views,
            uncertainties=uncertainties,
            voting_round=voting_round,
        )
        
        await self._emit_event(
            AnalysisEventType.CONSENSUS_REACHED,
            {
                "consensus_count": len(consensus_findings),
                "disagreement_count": len(disagreements),
                "overall_level": report.confidence_level.value,
            }
        )
        
        logger.info(
            f"Consensus complete: {len(consensus_findings)} agreed, "
            f"{len(disagreements)} disagreements, "
            f"level={report.confidence_level.value}"
        )
        
        return report
    
    # =========================================================================
    # Proposal Creation
    # =========================================================================
    
    def _create_proposals_from_findings(
        self,
        analyses: List[AgentAnalysis],
    ) -> List[Proposal]:
        """Create proposals from agent findings.
        
        Groups similar findings and creates votable proposals.
        
        Args:
            analyses: All agent analyses
        
        Returns:
            List of proposals to vote on
        """
        # Group findings by category
        findings_by_category: Dict[FindingCategory, List[Tuple[Finding, str]]] = {}
        
        for analysis in analyses:
            for finding in analysis.findings:
                category = finding.category
                if category not in findings_by_category:
                    findings_by_category[category] = []
                findings_by_category[category].append((finding, analysis.agent_id))
        
        proposals = []
        
        for category, findings_list in findings_by_category.items():
            # Create a proposal for each unique finding description
            seen_descriptions: Set[str] = set()
            
            for finding, agent_id in findings_list:
                # Normalize description for comparison
                desc_key = finding.description[:100].lower().strip()
                
                if desc_key not in seen_descriptions:
                    seen_descriptions.add(desc_key)
                    
                    proposal = Proposal(
                        proposer_id=agent_id,
                        topic=category.value,
                        description=finding.description,
                        supporting_findings=[finding.finding_id],
                        confidence=finding.confidence,
                    )
                    proposals.append(proposal)
        
        return proposals
    
    # =========================================================================
    # Agent Weight Calculation
    # =========================================================================
    
    def _calculate_all_agent_weights(
        self,
        analyses: List[AgentAnalysis],
        debate_results: Optional[Any] = None,
    ) -> Dict[str, Dict[str, AgentWeight]]:
        """Calculate weights for all agents across all topics.
        
        Args:
            analyses: All agent analyses
            debate_results: Optional debate timeline
        
        Returns:
            Nested dict: {topic: {agent_id: AgentWeight}}
        """
        weights: Dict[str, Dict[str, AgentWeight]] = {}
        
        # Get all topics (finding categories)
        topics = set()
        for analysis in analyses:
            for finding in analysis.findings:
                topics.add(finding.category.value)
        
        # Calculate weights per topic per agent
        for topic in topics:
            weights[topic] = {}
            
            for analysis in analyses:
                weight = self._calculate_agent_weight(
                    agent_id=analysis.agent_id,
                    agent_type=analysis.agent_type,
                    topic=topic,
                    analysis_confidence=analysis.overall_confidence,
                    debate_results=debate_results,
                )
                weights[topic][analysis.agent_id] = weight
        
        return weights
    
    def _calculate_agent_weight(
        self,
        agent_id: str,
        agent_type: AgentType,
        topic: str,
        analysis_confidence: float,
        debate_results: Optional[Any] = None,
    ) -> AgentWeight:
        """Calculate weight for a single agent on a specific topic.
        
        Weight is calculated as:
        final_weight = base_weight 
                      * (1 + specialty_bonus)
                      * historical_accuracy_factor
                      * confidence_factor
                      * debate_performance_factor
        
        Args:
            agent_id: The agent's ID
            agent_type: The agent's type
            topic: The topic being voted on
            analysis_confidence: Agent's confidence in their analysis
            debate_results: Optional debate results for performance
        
        Returns:
            AgentWeight with detailed breakdown
        """
        weight = AgentWeight(agent_id=agent_id)
        
        # 1. Base weight (all agents start equal)
        weight.base_weight = 1.0
        weight.calculation_breakdown["base"] = 1.0
        
        # 2. Specialty bonus
        try:
            category = FindingCategory(topic)
            specialized_types = SPECIALTY_MAP.get(category, [])
            
            if agent_type in specialized_types:
                weight.specialty_bonus = self.config.specialty_weight_multiplier - 1.0
                weight.calculation_breakdown["specialty_bonus"] = weight.specialty_bonus
        except ValueError:
            # Unknown category, no specialty bonus
            pass
        
        # 3. Historical accuracy factor
        historical = self.historical_performance.get(agent_id)
        if historical and historical.total_analyses > 0:
            # Scale accuracy to weight factor (0.5 to 1.5 range)
            accuracy_factor = 0.5 + historical.accuracy_rate
            weight.historical_accuracy_factor = accuracy_factor
            weight.calculation_breakdown["historical_accuracy"] = accuracy_factor
        else:
            weight.historical_accuracy_factor = 1.0
            weight.calculation_breakdown["historical_accuracy"] = 1.0
        
        # 4. Confidence factor
        # Scale confidence to factor: conf 0.5 -> factor 0.75, conf 1.0 -> factor 1.0
        confidence_factor = (
            1.0 - (1.0 - analysis_confidence) * self.config.confidence_weight_factor
        )
        weight.confidence_factor = max(0.5, min(1.5, confidence_factor))
        weight.calculation_breakdown["confidence"] = weight.confidence_factor
        
        # 5. Debate performance factor (if available)
        if debate_results:
            debate_factor = self._extract_debate_performance(agent_id, debate_results)
            weight.debate_performance_factor = debate_factor
            weight.calculation_breakdown["debate_performance"] = debate_factor
        else:
            weight.debate_performance_factor = 1.0
        
        # Calculate final weight
        weight.final_weight = (
            weight.base_weight
            * (1.0 + weight.specialty_bonus)
            * weight.historical_accuracy_factor
            * weight.confidence_factor
            * weight.debate_performance_factor
        )
        
        return weight
    
    def _extract_debate_performance(
        self,
        agent_id: str,
        debate_results: Any,  # DebateTimeline
    ) -> float:
        """Extract debate performance factor from debate results.
        
        Args:
            agent_id: The agent's ID
            debate_results: Debate timeline
        
        Returns:
            Performance factor (0.8 to 1.2)
        """
        # Default to neutral if no debate data
        if not debate_results or not hasattr(debate_results, 'rounds'):
            return 1.0
        
        # Count position changes (adaptability is valued)
        position_changes = 0
        total_rounds = len(debate_results.rounds)
        
        for round_data in debate_results.rounds:
            if hasattr(round_data, 'position_updates'):
                if agent_id in round_data.position_updates:
                    position_changes += 1
        
        # Moderate position changes are good (shows reasoning)
        # Too many or too few are less ideal
        if total_rounds == 0:
            return 1.0
        
        change_rate = position_changes / total_rounds
        
        if 0.2 <= change_rate <= 0.5:
            return 1.1  # Good adaptability
        elif change_rate > 0.5:
            return 0.9  # Too changeable
        else:
            return 1.0  # Stable but not rigid
    
    # =========================================================================
    # Vote Generation
    # =========================================================================
    
    def _generate_votes_from_analyses(
        self,
        analyses: List[AgentAnalysis],
        proposals: List[Proposal],
    ) -> List[Vote]:
        """Generate votes from agent analyses.
        
        Each agent votes on each proposal based on their findings.
        
        Args:
            analyses: All agent analyses
            proposals: Proposals to vote on
        
        Returns:
            List of votes
        """
        votes = []
        
        for proposal in proposals:
            for analysis in analyses:
                vote = self._generate_vote(analysis, proposal)
                votes.append(vote)
        
        return votes
    
    def _generate_vote(
        self,
        analysis: AgentAnalysis,
        proposal: Proposal,
    ) -> Vote:
        """Generate a single vote from an agent's analysis.
        
        Args:
            analysis: Agent's analysis
            proposal: Proposal to vote on
        
        Returns:
            Vote
        """
        # Check if agent has a finding matching this proposal
        matching_finding = None
        for finding in analysis.findings:
            if finding.category.value == proposal.topic:
                # Check if descriptions are similar
                if self._descriptions_similar(
                    finding.description, proposal.description
                ):
                    matching_finding = finding
                    break
        
        if matching_finding:
            # Agent agrees with the proposal
            if matching_finding.confidence >= 0.8:
                support = VoteType.STRONGLY_SUPPORT
            else:
                support = VoteType.SUPPORT
            
            reasoning = f"Finding aligns with proposal: {matching_finding.description[:100]}"
            confidence = matching_finding.confidence
            conditions = []
            
        else:
            # Check if agent is a specialist for this topic
            try:
                category = FindingCategory(proposal.topic)
                specialists = SPECIALTY_MAP.get(category, [])
                is_specialist = analysis.agent_type in specialists
            except ValueError:
                is_specialist = False
            
            if is_specialist:
                # Agent is specialist but didn't find this - may oppose
                support = VoteType.NEUTRAL
                reasoning = "No direct finding on this topic"
                confidence = 0.5
                conditions = ["Need more data"]
            else:
                # Non-specialist without direct finding
                support = VoteType.NEUTRAL
                reasoning = "Outside primary expertise"
                confidence = 0.5
                conditions = []
        
        return Vote(
            voter_id=analysis.agent_id,
            proposal_id=proposal.proposal_id,
            support=support,
            confidence=confidence,
            reasoning=reasoning,
            conditions=conditions,
        )
    
    def _descriptions_similar(self, desc1: str, desc2: str) -> bool:
        """Check if two descriptions are similar enough.
        
        Simple heuristic: check for significant word overlap.
        
        Args:
            desc1: First description
            desc2: Second description
        
        Returns:
            True if similar
        """
        # Normalize
        words1 = set(desc1.lower().split())
        words2 = set(desc2.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'will', 'be', 'to', 'of', 'and', 'in', 'for', 'on', 'with'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return False
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return (intersection / union) > 0.3 if union > 0 else False
    
    # =========================================================================
    # Voting Round Execution
    # =========================================================================
    
    async def _run_voting_round(
        self,
        proposals: List[Proposal],
        votes: List[Vote],
        agent_weights: Dict[str, Dict[str, AgentWeight]],
    ) -> VotingRound:
        """Run a complete voting round on proposals.
        
        Args:
            proposals: Proposals to vote on
            votes: All votes
            agent_weights: Calculated agent weights
        
        Returns:
            VotingRound with results
        """
        voting_round = VotingRound(
            proposals=proposals,
            votes=votes,
        )
        
        # Flatten agent weights for the round
        all_weights: Dict[str, AgentWeight] = {}
        for topic_weights in agent_weights.values():
            all_weights.update(topic_weights)
        voting_round.agent_weights = all_weights
        
        # Calculate result for each proposal
        for proposal in proposals:
            proposal_votes = [v for v in votes if v.proposal_id == proposal.proposal_id]
            
            # Get topic-specific weights
            topic_weights = agent_weights.get(proposal.topic, {})
            
            result = self._calculate_consensus_result(
                proposal, proposal_votes, topic_weights
            )
            voting_round.results[proposal.proposal_id] = result
        
        return voting_round
    
    def _calculate_consensus_result(
        self,
        proposal: Proposal,
        votes: List[Vote],
        weights: Dict[str, AgentWeight],
    ) -> ConsensusResult:
        """Calculate consensus result for a proposal.
        
        Args:
            proposal: The proposal
            votes: Votes on this proposal
            weights: Agent weights for this topic
        
        Returns:
            ConsensusResult with level and details
        """
        if len(votes) < self.config.minimum_votes_required:
            return ConsensusResult(
                proposal_id=proposal.proposal_id,
                consensus_level=ConsensusLevel.NO_CONSENSUS,
                weighted_support=0.0,
                votes=votes,
                passed=False,
            )
        
        # Calculate weighted support
        total_weighted_support = 0.0
        total_weight = 0.0
        conditions_required = []
        
        for vote in votes:
            if vote.support == VoteType.ABSTAIN:
                continue
            
            # Get agent weight
            agent_weight = weights.get(vote.voter_id)
            weight = agent_weight.final_weight if agent_weight else 1.0
            
            # Get vote weight
            vote_weight = VOTE_WEIGHTS.get(vote.support, 0.0)
            
            # Weighted contribution
            weighted_vote = weight * vote_weight * vote.confidence
            total_weighted_support += weighted_vote
            total_weight += weight
            
            # Collect conditions
            conditions_required.extend(vote.conditions)
        
        # Normalize to 0-1 scale
        # Vote weights range from -2 to +2, so normalize
        if total_weight > 0:
            # Shift from [-2, 2] to [0, 1]
            raw_support = total_weighted_support / total_weight
            normalized_support = (raw_support + 2) / 4  # Maps -2..2 to 0..1
        else:
            normalized_support = 0.5
        
        # Determine consensus level
        consensus_level = self._determine_consensus_level(normalized_support)
        
        # Determine if proposal passed
        passed = consensus_level in [
            ConsensusLevel.STRONG_CONSENSUS,
            ConsensusLevel.CONSENSUS,
            ConsensusLevel.MAJORITY,
        ]
        
        return ConsensusResult(
            proposal_id=proposal.proposal_id,
            consensus_level=consensus_level,
            weighted_support=normalized_support,
            votes=votes,
            passed=passed,
            conditions_required=list(set(conditions_required)),
        )
    
    def _determine_consensus_level(self, support: float) -> ConsensusLevel:
        """Determine consensus level from normalized support score.
        
        Args:
            support: Normalized support score (0-1)
        
        Returns:
            ConsensusLevel
        """
        if support >= self.config.strong_consensus_threshold:
            return ConsensusLevel.STRONG_CONSENSUS
        elif support >= self.config.consensus_threshold:
            return ConsensusLevel.CONSENSUS
        elif support >= self.config.majority_threshold:
            return ConsensusLevel.MAJORITY
        elif support >= self.config.divided_threshold:
            return ConsensusLevel.DIVIDED
        else:
            return ConsensusLevel.MINORITY
    
    # =========================================================================
    # Result Conversion
    # =========================================================================
    
    def _result_to_consensus_finding(
        self,
        proposal: Proposal,
        result: ConsensusResult,
        votes: List[Vote],
    ) -> ConsensusFinding:
        """Convert a successful result to a ConsensusFinding.
        
        Args:
            proposal: The proposal
            result: Voting result
            votes: All votes
        
        Returns:
            ConsensusFinding
        """
        proposal_votes = [v for v in votes if v.proposal_id == proposal.proposal_id]
        
        # Identify supporting and dissenting agents
        supporting = []
        dissenting = []
        dissent_reasons = {}
        
        for vote in proposal_votes:
            if vote.support in [VoteType.STRONGLY_SUPPORT, VoteType.SUPPORT]:
                supporting.append(vote.voter_id)
            elif vote.support in [VoteType.OPPOSE, VoteType.STRONGLY_OPPOSE]:
                dissenting.append(vote.voter_id)
                dissent_reasons[vote.voter_id] = vote.reasoning
        
        return ConsensusFinding(
            description=proposal.description,
            category=FindingCategory(proposal.topic) if proposal.topic in [c.value for c in FindingCategory] else FindingCategory.OTHER,
            consensus_level=result.consensus_level,
            weighted_confidence=result.weighted_support,
            supporting_agents=supporting,
            dissenting_agents=dissenting,
            dissent_reasons=dissent_reasons,
        )
    
    def _result_to_disagreement(
        self,
        proposal: Proposal,
        result: ConsensusResult,
        votes: List[Vote],
    ) -> Disagreement:
        """Convert a failed consensus result to a Disagreement.
        
        Args:
            proposal: The proposal
            result: Voting result
            votes: All votes
        
        Returns:
            Disagreement
        """
        proposal_votes = [v for v in votes if v.proposal_id == proposal.proposal_id]
        
        # Extract positions
        positions = {}
        for vote in proposal_votes:
            positions[vote.voter_id] = f"{vote.support.value}: {vote.reasoning}"
        
        return Disagreement(
            topic=proposal.topic,
            agents_involved=[v.voter_id for v in proposal_votes],
            positions=positions,
            reason=f"Consensus level: {result.consensus_level.value}, support: {result.weighted_support:.2f}",
            severity="major" if result.consensus_level == ConsensusLevel.DIVIDED else "moderate",
            resolution_attempted=True,
            resolution_method="vote",
        )
    
    def _extract_minority_view(
        self,
        proposal: Proposal,
        result: ConsensusResult,
        votes: List[Vote],
    ) -> Optional[MinorityView]:
        """Extract minority view from a majority consensus.
        
        Args:
            proposal: The proposal
            result: Voting result
            votes: All votes
        
        Returns:
            MinorityView or None
        """
        proposal_votes = [v for v in votes if v.proposal_id == proposal.proposal_id]
        
        # Find dissenting votes
        dissenting_votes = [
            v for v in proposal_votes
            if v.support in [VoteType.OPPOSE, VoteType.STRONGLY_OPPOSE]
        ]
        
        if not dissenting_votes:
            return None
        
        return MinorityView(
            agents=[v.voter_id for v in dissenting_votes],
            position=f"Dissent on: {proposal.description[:100]}",
            reasoning="; ".join(v.reasoning for v in dissenting_votes),
            evidence=[],  # Could extract from original findings
        )
    
    # =========================================================================
    # Uncertainty Extraction
    # =========================================================================
    
    def _extract_uncertainties(
        self,
        analyses: List[AgentAnalysis],
    ) -> List[Uncertainty]:
        """Extract key uncertainties from analyses.
        
        Args:
            analyses: All agent analyses
        
        Returns:
            List of uncertainties
        """
        uncertainties = []
        seen_areas = set()
        
        for analysis in analyses:
            for area in analysis.uncertainty_areas:
                if area.lower() not in seen_areas:
                    seen_areas.add(area.lower())
                    uncertainties.append(Uncertainty(
                        description=area,
                        impact_if_wrong="Analysis conclusions may vary significantly",
                        sensitivity="medium",
                    ))
        
        # Limit to configured max
        return uncertainties[:self.config.max_uncertainties_in_report]
    
    # =========================================================================
    # Report Generation
    # =========================================================================
    
    def _generate_consensus_report(
        self,
        analysis_id: str,
        bill_id: str,
        analyses: List[AgentAnalysis],
        consensus_findings: List[ConsensusFinding],
        disagreements: List[Disagreement],
        minority_views: List[MinorityView],
        uncertainties: List[Uncertainty],
        voting_round: VotingRound,
    ) -> ConsensusReport:
        """Generate the final consensus report.
        
        Args:
            analysis_id: The analysis ID
            bill_id: The bill ID
            analyses: All agent analyses
            consensus_findings: Agreed findings
            disagreements: Unresolved disagreements
            minority_views: Minority positions
            uncertainties: Key uncertainties
            voting_round: The voting round data
        
        Returns:
            Comprehensive ConsensusReport
        """
        # Calculate overall confidence level
        if consensus_findings:
            avg_confidence = sum(
                f.weighted_confidence for f in consensus_findings
            ) / len(consensus_findings)
            
            if avg_confidence >= 0.9:
                overall_level = ConsensusLevel.STRONG_CONSENSUS
            elif avg_confidence >= 0.75:
                overall_level = ConsensusLevel.CONSENSUS
            elif avg_confidence >= 0.6:
                overall_level = ConsensusLevel.MAJORITY
            else:
                overall_level = ConsensusLevel.DIVIDED
        else:
            overall_level = ConsensusLevel.NO_CONSENSUS
            avg_confidence = 0.0
        
        # Generate executive summary
        bill_summary = self._generate_bill_summary(analyses)
        
        # Generate primary recommendation
        primary_recommendation = self._generate_primary_recommendation(
            consensus_findings, disagreements
        )
        
        # Generate caveats
        caveats = self._generate_caveats(
            disagreements, minority_views, uncertainties
        )
        
        # Identify areas needing more research
        further_research = self._identify_research_needs(
            disagreements, uncertainties
        )
        
        return ConsensusReport(
            analysis_id=analysis_id,
            bill_id=bill_id,
            bill_summary=bill_summary,
            agreed_findings=consensus_findings,
            confidence_level=overall_level,
            unresolved_disputes=disagreements,
            minority_views=minority_views if self.config.include_minority_views else [],
            key_uncertainties=uncertainties,
            scenario_sensitivity={},  # Would be populated by sensitivity analysis
            primary_recommendation=primary_recommendation,
            caveats=caveats,
            further_research_needed=further_research,
            participating_agents=[a.agent_id for a in analyses],
        )
    
    def _generate_bill_summary(
        self,
        analyses: List[AgentAnalysis],
    ) -> str:
        """Generate a summary of the bill from agent analyses.
        
        Args:
            analyses: All agent analyses
        
        Returns:
            Summary string
        """
        # Combine executive summaries
        summaries = [a.executive_summary for a in analyses if a.executive_summary]
        
        if not summaries:
            return "Multi-agent analysis complete. See individual findings for details."
        
        # Use the highest confidence agent's summary as primary
        best_analysis = max(analyses, key=lambda a: a.overall_confidence)
        
        return best_analysis.executive_summary
    
    def _generate_primary_recommendation(
        self,
        consensus_findings: List[ConsensusFinding],
        disagreements: List[Disagreement],
    ) -> str:
        """Generate the primary recommendation.
        
        Args:
            consensus_findings: Agreed findings
            disagreements: Disagreements
        
        Returns:
            Recommendation string
        """
        if not consensus_findings:
            return "Insufficient consensus to make a clear recommendation. Further analysis recommended."
        
        # Count by consensus level
        strong = sum(1 for f in consensus_findings if f.consensus_level == ConsensusLevel.STRONG_CONSENSUS)
        consensus = sum(1 for f in consensus_findings if f.consensus_level == ConsensusLevel.CONSENSUS)
        
        if strong > len(consensus_findings) / 2:
            qualifier = "with high confidence"
        elif consensus + strong > len(consensus_findings) / 2:
            qualifier = "with moderate confidence"
        else:
            qualifier = "with reservations"
        
        return (
            f"Based on {len(consensus_findings)} agreed findings {qualifier}, "
            f"the analysis identifies significant fiscal and policy impacts. "
            f"Note: {len(disagreements)} areas remain in dispute."
        )
    
    def _generate_caveats(
        self,
        disagreements: List[Disagreement],
        minority_views: List[MinorityView],
        uncertainties: List[Uncertainty],
    ) -> List[str]:
        """Generate caveats for the report.
        
        Args:
            disagreements: Unresolved disagreements
            minority_views: Minority positions
            uncertainties: Key uncertainties
        
        Returns:
            List of caveat strings
        """
        caveats = []
        
        if disagreements:
            caveats.append(
                f"Analysis includes {len(disagreements)} unresolved disagreements "
                "that may affect conclusions."
            )
        
        if minority_views:
            caveats.append(
                f"{len(minority_views)} minority view(s) documented. "
                "Alternative interpretations exist."
            )
        
        if uncertainties:
            high_sensitivity = [u for u in uncertainties if u.sensitivity == "high"]
            if high_sensitivity:
                caveats.append(
                    f"{len(high_sensitivity)} high-sensitivity uncertainties identified "
                    "that could significantly affect projections."
                )
        
        if not caveats:
            caveats.append("Analysis reflects strong multi-agent consensus with minimal reservations.")
        
        return caveats
    
    def _identify_research_needs(
        self,
        disagreements: List[Disagreement],
        uncertainties: List[Uncertainty],
    ) -> List[str]:
        """Identify areas needing further research.
        
        Args:
            disagreements: Unresolved disagreements
            uncertainties: Key uncertainties
        
        Returns:
            List of research needs
        """
        needs = []
        
        # From disagreements
        for disagreement in disagreements[:3]:  # Top 3
            needs.append(f"Resolve dispute on {disagreement.topic}")
        
        # From uncertainties
        for uncertainty in uncertainties:
            if uncertainty.data_needed_to_resolve:
                for data_need in uncertainty.data_needed_to_resolve[:2]:
                    if data_need not in needs:
                        needs.append(data_need)
        
        return needs[:5]  # Limit to 5
    
    # =========================================================================
    # Event Emission
    # =========================================================================
    
    async def _emit_event(
        self,
        event_type: AnalysisEventType,
        data: Dict[str, Any],
    ) -> None:
        """Emit an analysis event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if self._event_callback:
            event = AnalysisEvent(
                event_type=event_type,
                data=data,
            )
            try:
                await self._event_callback(event)
            except Exception as e:
                logger.warning(f"Failed to emit event: {e}")


# =============================================================================
# Utility Functions
# =============================================================================

def calculate_weighted_mean(
    values: List[float],
    weights: List[float],
) -> float:
    """Calculate weighted mean of values.
    
    Args:
        values: List of values
        weights: Corresponding weights
    
    Returns:
        Weighted mean
    """
    if not values or not weights:
        return 0.0
    
    if len(values) != len(weights):
        raise ValueError("Values and weights must have same length")
    
    total_weight = sum(weights)
    if total_weight == 0:
        return sum(values) / len(values)  # Fall back to unweighted
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def calculate_weighted_confidence_band(
    estimates: List[float],
    confidences: List[float],
    weights: List[float],
) -> ConfidenceBand:
    """Calculate confidence band from weighted estimates.
    
    Args:
        estimates: Point estimates from agents
        confidences: Confidence levels
        weights: Agent weights
    
    Returns:
        ConfidenceBand with P10, P50, P90
    """
    if not estimates:
        return ConfidenceBand(
            metric_name="unknown",
            p10=0.0,
            p50=0.0,
            p90=0.0,
        )
    
    # Weight estimates by confidence and agent weight
    weighted_estimates = []
    total_weight = 0.0
    
    for est, conf, weight in zip(estimates, confidences, weights):
        combined_weight = conf * weight
        weighted_estimates.append((est, combined_weight))
        total_weight += combined_weight
    
    # Sort by estimate
    weighted_estimates.sort(key=lambda x: x[0])
    
    # Find percentiles
    cumulative = 0.0
    p10 = weighted_estimates[0][0]
    p50 = weighted_estimates[len(weighted_estimates) // 2][0]
    p90 = weighted_estimates[-1][0]
    
    for est, weight in weighted_estimates:
        cumulative += weight
        pct = cumulative / total_weight if total_weight > 0 else 0
        
        if pct >= 0.1 and p10 == weighted_estimates[0][0]:
            p10 = est
        if pct >= 0.5 and p50 == weighted_estimates[len(weighted_estimates) // 2][0]:
            p50 = est
        if pct >= 0.9 and p90 == weighted_estimates[-1][0]:
            p90 = est
    
    return ConfidenceBand(
        metric_name="weighted_estimate",
        p10=p10,
        p50=p50,
        p90=p90,
    )


def get_specialty_match_score(
    agent_type: AgentType,
    category: FindingCategory,
) -> float:
    """Get specialty match score for an agent on a category.
    
    Args:
        agent_type: The agent type
        category: The finding category
    
    Returns:
        Score 0.0 to 1.0
    """
    specialists = SPECIALTY_MAP.get(category, [])
    
    if agent_type in specialists:
        # Primary specialist
        if specialists.index(agent_type) == 0:
            return 1.0
        else:
            return 0.8  # Secondary specialist
    
    return 0.5  # Non-specialist
