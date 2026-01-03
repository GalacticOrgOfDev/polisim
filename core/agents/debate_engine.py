"""Debate Loop Engine for Multi-Agent Policy Analysis.

This module implements a sophisticated debate system where AI agents discuss
disagreements, challenge each other's findings, and work toward consensus.
The debate follows research-backed protocols (ICLR 2025 MAD Analysis) with
tight rounds (max 3-5) and judge arbitration for stalemates.

Key Features:
- Structured debate protocol with triggers and termination conditions
- Critique and rebuttal system with evidence-based arguments
- Convergence algorithm with weighted position tracking
- Debate visualization data for UI transparency
- Judge agent arbitration for unresolved disputes
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Awaitable, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from core.agents.types import (
    AgentType,
    CritiqueType,
    CritiqueSeverity,
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
    Critique,
    Rebuttal,
    Position,
    PositionUpdate,
    DebateRound,
    DebateTimeline,
    TurningPoint,
    Vote,
    Proposal,
    AnalysisEvent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Debate Configuration
# =============================================================================

@dataclass
class DebateConfig:
    """Configuration for debate behavior."""
    
    # Round limits (research shows diminishing returns beyond 3 rounds)
    max_rounds: int = 3
    hard_cap_rounds: int = 5
    
    # Convergence thresholds
    convergence_threshold: float = 0.8  # Early exit when consensus achieved
    stalemate_rounds: int = 2  # No position changes in N rounds = stalemate
    judge_invocation_threshold: float = 0.6  # Below this after round 3, invoke judge
    
    # Debate triggers
    confidence_divergence_threshold: float = 0.3  # Agents differ by >0.3
    magnitude_divergence_threshold: float = 0.2  # >20% difference in estimates
    
    # Timing
    round_timeout_seconds: float = 60.0
    critique_timeout_seconds: float = 30.0
    rebuttal_timeout_seconds: float = 30.0
    
    # Moderation
    max_critiques_per_agent_per_round: int = 3
    require_evidence_for_critique: bool = True
    track_argument_quality: bool = True


# =============================================================================
# Debate Trigger System
# =============================================================================

class DebateTriggerType(Enum):
    """Types of conditions that trigger debate."""
    
    CONFIDENCE_DIVERGENCE = "confidence_divergence"
    CONTRADICTORY_FINDINGS = "contradictory_findings"
    ASSUMPTION_DISPUTE = "assumption_dispute"
    MAGNITUDE_DISAGREEMENT = "magnitude_disagreement"
    CRITICAL_CRITIQUE = "critical_critique"
    METHODOLOGY_CONFLICT = "methodology_conflict"


@dataclass
class DebateTrigger:
    """A specific trigger that initiated debate."""
    
    trigger_id: str = field(default_factory=lambda: str(uuid4())[:8])
    trigger_type: DebateTriggerType = DebateTriggerType.CONFIDENCE_DIVERGENCE
    topic: str = ""
    agents_involved: List[str] = field(default_factory=list)
    severity: str = "moderate"  # minor, moderate, major, critical
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebateTopic:
    """A topic to be debated with its context."""
    
    topic_id: str = field(default_factory=lambda: str(uuid4())[:8])
    title: str = ""
    description: str = ""
    triggers: List[DebateTrigger] = field(default_factory=list)
    priority: int = 1  # 1=highest, 3=lowest
    related_findings: List[str] = field(default_factory=list)
    category: str = ""
    

# =============================================================================
# Debate Argument Quality Tracking
# =============================================================================

@dataclass
class ArgumentQuality:
    """Quality assessment of an argument in debate."""
    
    argument_id: str = field(default_factory=lambda: str(uuid4())[:8])
    agent_id: str = ""
    argument_type: str = ""  # critique, rebuttal, position
    evidence_quality: float = 0.5  # 0-1 scale
    logical_coherence: float = 0.5
    relevance: float = 0.5
    novelty: float = 0.5  # New information vs. repetition
    overall_quality: float = 0.5
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentDebatePerformance:
    """Track agent performance throughout debate."""
    
    agent_id: str = ""
    arguments_made: int = 0
    arguments_quality_avg: float = 0.0
    position_changes: int = 0
    critiques_received: int = 0
    critiques_acknowledged: int = 0
    evidence_citations: int = 0
    influence_score: float = 0.0  # How much they influenced others


# =============================================================================
# Disagreement Map for Visualization
# =============================================================================

@dataclass
class DisagreementPoint:
    """A specific point of disagreement between agents."""
    
    point_id: str = field(default_factory=lambda: str(uuid4())[:8])
    topic: str = ""
    agent_positions: Dict[str, str] = field(default_factory=dict)
    agent_confidences: Dict[str, float] = field(default_factory=dict)
    magnitude_of_disagreement: float = 0.0  # 0-1 scale
    key_arguments: Dict[str, List[str]] = field(default_factory=dict)
    resolution_status: str = "unresolved"  # unresolved, partially_resolved, resolved


@dataclass
class DisagreementMap:
    """Complete map of disagreements for visualization."""
    
    map_id: str = field(default_factory=lambda: str(uuid4())[:8])
    analysis_id: str = ""
    total_disagreements: int = 0
    resolved_count: int = 0
    points: List[DisagreementPoint] = field(default_factory=list)
    agent_pairs_most_disagreement: List[Tuple[str, str, float]] = field(default_factory=list)
    topic_disagreement_scores: Dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# Extended Position Tracking
# =============================================================================

@dataclass
class PositionTrajectory:
    """Track how an agent's position evolved over debate."""
    
    agent_id: str = ""
    initial_position: Optional[Position] = None
    position_history: List[Position] = field(default_factory=list)
    confidence_history: List[float] = field(default_factory=list)
    change_reasons: List[str] = field(default_factory=list)
    total_change_magnitude: float = 0.0


# =============================================================================
# Debate Engine Core
# =============================================================================

class DebateEngine:
    """Engine for running structured debates between agents.
    
    The DebateEngine orchestrates multi-round debates following research-backed
    protocols. It:
    - Identifies debate topics from agent disagreements
    - Moderates critique and rebuttal exchanges
    - Tracks position changes and convergence
    - Invokes judge arbitration when needed
    - Generates visualization data
    
    Example:
        engine = DebateEngine(config)
        timeline = await engine.run_debate(
            analyses=agent_analyses,
            critiques=initial_critiques,
            agents=agent_dict,
            context=analysis_context
        )
    """
    
    def __init__(
        self,
        config: Optional[DebateConfig] = None,
        judge: Optional[Any] = None,  # JudgeAgent, typed as Any to avoid circular import
    ):
        """Initialize the debate engine.
        
        Args:
            config: Debate configuration. Uses defaults if not provided.
            judge: Optional JudgeAgent for arbitration.
        """
        self.config = config or DebateConfig()
        self.judge = judge
        
        # Runtime state
        self._current_debate_id: Optional[str] = None
        self._event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None
        self._agent_performance: Dict[str, AgentDebatePerformance] = {}
        
        logger.info("DebateEngine initialized")
    
    # =========================================================================
    # Main Entry Point
    # =========================================================================
    
    async def run_debate(
        self,
        analyses: List[AgentAnalysis],
        critiques: Dict[str, List[Critique]],
        agents: Dict[str, Any],  # BaseAgent
        context: Any,  # AnalysisContext
        event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None,
    ) -> Optional[DebateTimeline]:
        """Run the complete debate process.
        
        This is the main entry point for the debate engine. It identifies
        topics, runs rounds, tracks convergence, and returns a complete timeline.
        
        Args:
            analyses: All agent analyses
            critiques: Initial critiques from cross-review
            agents: Dictionary of agent instances
            context: Analysis context
            event_callback: Optional callback for streaming events
        
        Returns:
            DebateTimeline or None if no debate needed
        """
        self._event_callback = event_callback
        self._current_debate_id = str(uuid4())
        
        # Initialize agent performance tracking
        self._init_agent_performance(analyses)
        
        # Step 1: Identify debate topics
        topics = self._identify_debate_topics(analyses, critiques)
        
        if not topics:
            logger.info("No significant disagreements requiring debate")
            return None
        
        logger.info(f"Starting debate on {len(topics)} topics")
        await self._emit_event(
            AnalysisEventType.DEBATE_STARTED,
            {"topics": [t.title for t in topics], "agent_count": len(analyses)}
        )
        
        # Step 2: Initialize timeline
        primary_topic = topics[0]
        timeline = DebateTimeline(
            debate_id=self._current_debate_id,
            topic=primary_topic.title,
        )
        
        # Initialize position trajectories
        position_trajectories: Dict[str, PositionTrajectory] = {}
        for analysis in analyses:
            initial_pos = self._create_position_from_analysis(analysis, primary_topic.title)
            position_trajectories[analysis.agent_id] = PositionTrajectory(
                agent_id=analysis.agent_id,
                initial_position=initial_pos,
                position_history=[initial_pos],
                confidence_history=[initial_pos.confidence],
            )
            timeline.position_trajectory[analysis.agent_id] = [initial_pos]
        
        # Step 3: Run debate rounds
        current_positions = {
            a.agent_id: self._create_position_from_analysis(a, primary_topic.title)
            for a in analyses
        }
        current_critiques = critiques
        
        for round_num in range(1, self.config.max_rounds + 1):
            logger.info(f"Starting debate round {round_num}")
            
            # Run the round
            round_result = await self._run_debate_round(
                round_num=round_num,
                topic=primary_topic,
                analyses=analyses,
                current_positions=current_positions,
                critiques=current_critiques,
                agents=agents,
                context=context,
            )
            
            timeline.rounds.append(round_result)
            
            # Update position trajectories
            for agent_id, pos_update in round_result.position_updates.items():
                if agent_id in position_trajectories:
                    new_pos = Position(
                        agent_id=agent_id,
                        topic=primary_topic.title,
                        stance=pos_update.new_stance,
                        confidence=pos_update.new_confidence,
                    )
                    position_trajectories[agent_id].position_history.append(new_pos)
                    position_trajectories[agent_id].confidence_history.append(pos_update.new_confidence)
                    position_trajectories[agent_id].change_reasons.append(pos_update.reason_for_change)
                    current_positions[agent_id] = new_pos
                    timeline.position_trajectory[agent_id].append(new_pos)
            
            # Emit convergence event
            await self._emit_event(
                AnalysisEventType.DEBATE_CONVERGENCE,
                {
                    "round": round_num,
                    "convergence": round_result.convergence_score,
                    "position_changes": len(round_result.position_updates),
                }
            )
            
            # Check termination conditions
            termination_reason = self._check_termination(timeline, round_num)
            if termination_reason:
                logger.info(f"Debate terminated: {termination_reason}")
                break
        
        # Step 4: Calculate final convergence
        timeline.final_convergence = timeline.rounds[-1].convergence_score if timeline.rounds else 0.0
        
        # Step 5: Identify turning points
        timeline.key_turning_points = self._identify_turning_points(
            timeline, position_trajectories
        )
        
        # Step 6: Invoke judge if needed
        if self._should_invoke_judge(timeline):
            logger.info("Invoking Judge Agent for arbitration")
            timeline.judge_involved = True
            
            if self.judge:
                evidence = self._gather_evidence_for_judge(analyses)
                arbitration = await self.judge.arbitrate(
                    debate_history=timeline.rounds,
                    positions=current_positions,
                    evidence=evidence,
                    context=context,
                )
                
                # Record arbitration as turning point
                timeline.key_turning_points.append(TurningPoint(
                    round_number=len(timeline.rounds),
                    agent_id="judge",
                    description=f"Judge arbitration: {arbitration.final_position}",
                    position_before="Multiple conflicting positions",
                    position_after=arbitration.final_position,
                    catalyst=f"Low convergence ({timeline.final_convergence:.2f}) after {len(timeline.rounds)} rounds",
                ))
        
        logger.info(
            f"Debate complete: {len(timeline.rounds)} rounds, "
            f"final convergence: {timeline.final_convergence:.2f}, "
            f"judge involved: {timeline.judge_involved}"
        )
        
        return timeline
    
    # =========================================================================
    # Topic Identification
    # =========================================================================
    
    def _identify_debate_topics(
        self,
        analyses: List[AgentAnalysis],
        critiques: Dict[str, List[Critique]],
    ) -> List[DebateTopic]:
        """Identify topics that warrant debate.
        
        Triggers debate for:
        - Confidence divergence > threshold
        - Contradictory findings
        - Assumption disputes
        - Magnitude disagreements
        - Critical critiques
        
        Args:
            analyses: All agent analyses
            critiques: All critiques
        
        Returns:
            List of DebateTopic sorted by priority
        """
        topics: List[DebateTopic] = []
        triggers_by_topic: Dict[str, List[DebateTrigger]] = {}
        
        # Check for critical/major critiques
        for target_id, agent_critiques in critiques.items():
            for critique in agent_critiques:
                if critique.severity in [CritiqueSeverity.CRITICAL, CritiqueSeverity.MAJOR]:
                    topic_key = f"critique_{critique.critique_type.value}"
                    
                    trigger = DebateTrigger(
                        trigger_type=DebateTriggerType.CRITICAL_CRITIQUE,
                        topic=critique.argument[:100],
                        agents_involved=[critique.critic_id, target_id],
                        severity="critical" if critique.severity == CritiqueSeverity.CRITICAL else "major",
                        description=critique.argument,
                        evidence={"critique_id": critique.critique_id},
                    )
                    
                    if topic_key not in triggers_by_topic:
                        triggers_by_topic[topic_key] = []
                    triggers_by_topic[topic_key].append(trigger)
        
        # Check for confidence divergence
        confidences = {a.agent_id: a.overall_confidence for a in analyses}
        if confidences:
            max_conf = max(confidences.values())
            min_conf = min(confidences.values())
            divergence = max_conf - min_conf
            
            if divergence > self.config.confidence_divergence_threshold:
                trigger = DebateTrigger(
                    trigger_type=DebateTriggerType.CONFIDENCE_DIVERGENCE,
                    topic="Overall analysis confidence",
                    agents_involved=list(confidences.keys()),
                    severity="major" if divergence > 0.4 else "moderate",
                    description=f"Confidence divergence of {divergence:.2f} detected",
                    evidence={
                        "max_confidence": max_conf,
                        "min_confidence": min_conf,
                        "divergence": divergence,
                        "agent_confidences": confidences,
                    },
                )
                
                topic_key = "confidence_divergence"
                if topic_key not in triggers_by_topic:
                    triggers_by_topic[topic_key] = []
                triggers_by_topic[topic_key].append(trigger)
        
        # Check for contradictory findings by category
        findings_by_category: Dict[str, List[Tuple[Finding, str]]] = {}
        for analysis in analyses:
            for finding in analysis.findings:
                cat = finding.category.value
                if cat not in findings_by_category:
                    findings_by_category[cat] = []
                findings_by_category[cat].append((finding, analysis.agent_id))
        
        for category, findings_list in findings_by_category.items():
            if len(findings_list) >= 2:
                # Check for magnitude disagreement
                magnitudes = [f[0].confidence for f in findings_list]
                if magnitudes:
                    max_mag = max(magnitudes)
                    min_mag = min(magnitudes)
                    
                    if (max_mag - min_mag) > self.config.magnitude_divergence_threshold:
                        trigger = DebateTrigger(
                            trigger_type=DebateTriggerType.MAGNITUDE_DISAGREEMENT,
                            topic=f"{category} impact assessment",
                            agents_involved=[f[1] for f in findings_list],
                            severity="moderate",
                            description=f"Magnitude disagreement in {category}: {min_mag:.2f} vs {max_mag:.2f}",
                            evidence={
                                "category": category,
                                "magnitudes": {f[1]: f[0].confidence for f in findings_list},
                            },
                        )
                        
                        topic_key = f"magnitude_{category}"
                        if topic_key not in triggers_by_topic:
                            triggers_by_topic[topic_key] = []
                        triggers_by_topic[topic_key].append(trigger)
        
        # Check for assumption disputes
        assumptions_by_category: Dict[str, Dict[str, List[str]]] = {}
        for analysis in analyses:
            for assumption in analysis.assumptions_used:
                cat = assumption.category
                if cat not in assumptions_by_category:
                    assumptions_by_category[cat] = {}
                if analysis.agent_id not in assumptions_by_category[cat]:
                    assumptions_by_category[cat][analysis.agent_id] = []
                assumptions_by_category[cat][analysis.agent_id].append(assumption.description)
        
        for cat, agent_assumptions in assumptions_by_category.items():
            if len(agent_assumptions) >= 2:
                # Different agents have different assumptions in same category
                all_descriptions = []
                for agent_id, descriptions in agent_assumptions.items():
                    all_descriptions.extend(descriptions)
                
                unique_assumptions = set(all_descriptions)
                if len(unique_assumptions) > len(agent_assumptions):
                    trigger = DebateTrigger(
                        trigger_type=DebateTriggerType.ASSUMPTION_DISPUTE,
                        topic=f"Assumptions for {cat}",
                        agents_involved=list(agent_assumptions.keys()),
                        severity="moderate",
                        description=f"Different assumptions used for {cat}",
                        evidence={"assumptions": agent_assumptions},
                    )
                    
                    topic_key = f"assumption_{cat}"
                    if topic_key not in triggers_by_topic:
                        triggers_by_topic[topic_key] = []
                    triggers_by_topic[topic_key].append(trigger)
        
        # Convert triggers to topics with priority
        for topic_key, triggers in triggers_by_topic.items():
            # Determine priority based on trigger severity
            has_critical = any(t.severity == "critical" for t in triggers)
            has_major = any(t.severity == "major" for t in triggers)
            
            if has_critical:
                priority = 1
            elif has_major:
                priority = 2
            else:
                priority = 3
            
            topic = DebateTopic(
                title=triggers[0].topic if triggers else topic_key,
                description=triggers[0].description if triggers else "",
                triggers=triggers,
                priority=priority,
                category=topic_key.split("_")[0] if "_" in topic_key else topic_key,
            )
            topics.append(topic)
        
        # Sort by priority (lowest number = highest priority)
        topics.sort(key=lambda t: t.priority)
        
        # Limit to top 3 topics
        return topics[:3]
    
    # =========================================================================
    # Debate Round Execution
    # =========================================================================
    
    async def _run_debate_round(
        self,
        round_num: int,
        topic: DebateTopic,
        analyses: List[AgentAnalysis],
        current_positions: Dict[str, Position],
        critiques: Dict[str, List[Critique]],
        agents: Dict[str, Any],
        context: Any,
    ) -> DebateRound:
        """Run a single round of debate.
        
        A debate round consists of:
        1. Opening positions (from current state)
        2. Critiques (agents challenge each other)
        3. Rebuttals (agents defend or acknowledge)
        4. Position updates (agents may change stance)
        5. Convergence calculation
        
        Args:
            round_num: Current round number
            topic: The debate topic
            analyses: Original analyses
            current_positions: Current positions by agent
            critiques: Current critiques
            agents: Agent instances
            context: Analysis context
        
        Returns:
            DebateRound with all exchanges and convergence
        """
        round_result = DebateRound(
            round_number=round_num,
            topic=topic.title,
            participants=list(current_positions.keys()),
            opening_positions=dict(current_positions),
            timestamp_start=datetime.now(),
        )
        
        # Phase 1: Generate new critiques for this round
        round_critiques = await self._generate_round_critiques(
            round_num=round_num,
            topic=topic,
            positions=current_positions,
            agents=agents,
            context=context,
        )
        round_result.critiques.extend(round_critiques)
        
        # Phase 2: Generate rebuttals
        rebuttals = await self._generate_rebuttals(
            critiques=round_critiques,
            positions=current_positions,
            agents=agents,
            context=context,
        )
        round_result.rebuttals.extend(rebuttals)
        
        # Phase 3: Determine position updates
        position_updates = await self._determine_position_updates(
            round_num=round_num,
            critiques=round_critiques,
            rebuttals=rebuttals,
            current_positions=current_positions,
            agents=agents,
            context=context,
        )
        round_result.position_updates = position_updates
        
        # Phase 4: Calculate convergence
        updated_positions = dict(current_positions)
        for agent_id, update in position_updates.items():
            updated_positions[agent_id] = Position(
                agent_id=agent_id,
                topic=topic.title,
                stance=update.new_stance,
                confidence=update.new_confidence,
            )
        
        round_result.convergence_score = self._calculate_convergence(
            list(updated_positions.values())
        )
        
        round_result.timestamp_end = datetime.now()
        
        # Update agent performance metrics
        self._update_performance_metrics(round_result)
        
        return round_result
    
    async def _generate_round_critiques(
        self,
        round_num: int,
        topic: DebateTopic,
        positions: Dict[str, Position],
        agents: Dict[str, Any],
        context: Any,
    ) -> List[Critique]:
        """Generate critiques for this debate round.
        
        Args:
            round_num: Current round number
            topic: The debate topic
            positions: Current positions
            agents: Agent instances
            context: Analysis context
        
        Returns:
            List of critiques for this round
        """
        critiques = []
        
        agent_ids = list(positions.keys())
        
        # Each agent critiques others (limited by config)
        for critic_id in agent_ids:
            critic_agent = agents.get(critic_id)
            if not critic_agent:
                continue
            
            critique_count = 0
            for target_id in agent_ids:
                if target_id == critic_id:
                    continue
                
                if critique_count >= self.config.max_critiques_per_agent_per_round:
                    break
                
                target_position = positions.get(target_id)
                if not target_position:
                    continue
                
                try:
                    # Generate critique using agent's critique method
                    # Create a minimal AgentAnalysis to pass to critique
                    mock_analysis = AgentAnalysis(
                        agent_id=target_id,
                        executive_summary=target_position.stance,
                        overall_confidence=target_position.confidence,
                        key_takeaways=target_position.key_arguments,
                    )
                    
                    agent_critiques = await asyncio.wait_for(
                        critic_agent.critique(mock_analysis, context),
                        timeout=self.config.critique_timeout_seconds,
                    )
                    
                    # Filter to relevant critiques (topic-related)
                    for critique in agent_critiques[:self.config.max_critiques_per_agent_per_round - critique_count]:
                        critiques.append(critique)
                        critique_count += 1
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Critique timed out: {critic_id} -> {target_id}")
                except Exception as e:
                    logger.warning(f"Critique failed: {critic_id} -> {target_id}: {e}")
        
        return critiques
    
    async def _generate_rebuttals(
        self,
        critiques: List[Critique],
        positions: Dict[str, Position],
        agents: Dict[str, Any],
        context: Any,
    ) -> List[Rebuttal]:
        """Generate rebuttals to critiques.
        
        Args:
            critiques: Critiques to respond to
            positions: Current positions
            agents: Agent instances
            context: Analysis context
        
        Returns:
            List of rebuttals
        """
        rebuttals = []
        
        # Group critiques by target
        critiques_by_target: Dict[str, List[Critique]] = {}
        for critique in critiques:
            if critique.target_id not in critiques_by_target:
                critiques_by_target[critique.target_id] = []
            critiques_by_target[critique.target_id].append(critique)
        
        # Each targeted agent responds
        for target_id, target_critiques in critiques_by_target.items():
            agent = agents.get(target_id)
            if not agent:
                continue
            
            for critique in target_critiques:
                try:
                    # Use agent's respond_to_critique method
                    mock_analysis = AgentAnalysis(
                        agent_id=target_id,
                        executive_summary=positions.get(target_id, Position()).stance,
                    )
                    
                    response = await asyncio.wait_for(
                        agent.respond_to_critique(critique, mock_analysis, context),
                        timeout=self.config.rebuttal_timeout_seconds,
                    )
                    
                    # Check if response acknowledges the critique
                    acknowledgment = any(
                        word in response.lower() 
                        for word in ["valid", "agree", "correct", "acknowledged", "fair point"]
                    )
                    
                    rebuttal = Rebuttal(
                        critique_id=critique.critique_id,
                        rebutter_id=target_id,
                        argument=response,
                        acknowledgment=acknowledgment,
                    )
                    rebuttals.append(rebuttal)
                    
                except asyncio.TimeoutError:
                    logger.warning(f"Rebuttal timed out: {target_id}")
                except Exception as e:
                    logger.warning(f"Rebuttal failed: {target_id}: {e}")
        
        return rebuttals
    
    async def _determine_position_updates(
        self,
        round_num: int,
        critiques: List[Critique],
        rebuttals: List[Rebuttal],
        current_positions: Dict[str, Position],
        agents: Dict[str, Any],
        context: Any,
    ) -> Dict[str, PositionUpdate]:
        """Determine which agents update their positions.
        
        Position updates occur when:
        - Agent acknowledges valid critique
        - Agent's rebuttal indicates changed understanding
        - Strong evidence presented in critique
        
        Args:
            round_num: Current round
            critiques: This round's critiques
            rebuttals: This round's rebuttals
            current_positions: Current positions
            agents: Agent instances
            context: Analysis context
        
        Returns:
            Dictionary of agent_id -> PositionUpdate
        """
        updates: Dict[str, PositionUpdate] = {}
        
        # Track critiques and rebuttals by target
        rebuttals_by_target: Dict[str, List[Rebuttal]] = {}
        for rebuttal in rebuttals:
            if rebuttal.rebutter_id not in rebuttals_by_target:
                rebuttals_by_target[rebuttal.rebutter_id] = []
            rebuttals_by_target[rebuttal.rebutter_id].append(rebuttal)
        
        critiques_by_target: Dict[str, List[Critique]] = {}
        for critique in critiques:
            if critique.target_id not in critiques_by_target:
                critiques_by_target[critique.target_id] = []
            critiques_by_target[critique.target_id].append(critique)
        
        # Check each agent for position changes
        for agent_id, position in current_positions.items():
            agent = agents.get(agent_id)
            if not agent:
                continue
            
            agent_rebuttals = rebuttals_by_target.get(agent_id, [])
            agent_critiques = critiques_by_target.get(agent_id, [])
            
            # Calculate pressure to change based on:
            # - Number of acknowledged critiques
            # - Severity of critiques
            # - Quality of evidence in critiques
            
            acknowledged_count = sum(1 for r in agent_rebuttals if r.acknowledgment)
            critical_critiques = sum(
                1 for c in agent_critiques 
                if c.severity in [CritiqueSeverity.CRITICAL, CritiqueSeverity.MAJOR]
            )
            
            # Determine if position should change
            should_update = False
            confidence_change = 0.0
            reason = ""
            
            if acknowledged_count > 0:
                should_update = True
                confidence_change = -0.05 * acknowledged_count  # Reduce confidence
                reason = f"Acknowledged {acknowledged_count} valid critique(s)"
            
            if critical_critiques > 0:
                should_update = True
                confidence_change -= 0.1 * critical_critiques
                reason = f"Received {critical_critiques} critical/major critique(s)"
            
            if should_update:
                new_confidence = max(0.1, min(1.0, position.confidence + confidence_change))
                
                # Use agent's update_position method if available
                try:
                    # Extract evidence from critiques
                    evidence = [
                        Evidence(description=c.argument, source=c.critic_id)
                        for c in agent_critiques
                    ]
                    
                    updated = await agent.update_position(
                        position, evidence, agent_critiques
                    )
                    
                    # Only record if position actually changed
                    if (updated.stance != position.stance or 
                        abs(updated.confidence - position.confidence) > 0.01):
                        updates[agent_id] = PositionUpdate(
                            agent_id=agent_id,
                            original_position_id=position.position_id,
                            new_stance=updated.stance,
                            new_confidence=updated.confidence,
                            reason_for_change=reason,
                            influenced_by=[c.critique_id for c in agent_critiques],
                        )
                except Exception as e:
                    # Fall back to simple confidence adjustment
                    if abs(confidence_change) > 0.01:
                        updates[agent_id] = PositionUpdate(
                            agent_id=agent_id,
                            original_position_id=position.position_id,
                            new_stance=position.stance,  # Keep same stance
                            new_confidence=new_confidence,
                            reason_for_change=reason,
                            influenced_by=[c.critique_id for c in agent_critiques],
                        )
        
        return updates
    
    # =========================================================================
    # Convergence Calculation
    # =========================================================================
    
    def _calculate_convergence(self, positions: List[Position]) -> float:
        """Calculate convergence score from positions.
        
        Uses multiple metrics:
        - Confidence variance (lower = more convergence)
        - Stance similarity (using simple string comparison)
        - Argument overlap
        
        Args:
            positions: List of current positions
        
        Returns:
            Convergence score 0.0 to 1.0
        """
        if not positions or len(positions) < 2:
            return 1.0
        
        # Component 1: Confidence variance (weight: 0.4)
        confidences = [p.confidence for p in positions]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        # Variance of 0.25 (max for 0-1 range) maps to 0, variance of 0 maps to 1
        confidence_convergence = max(0.0, 1.0 - variance * 4)
        
        # Component 2: Stance similarity (weight: 0.4)
        # Simple approach: compare key arguments overlap
        all_arguments: Set[str] = set()
        agent_arguments: Dict[str, Set[str]] = {}
        
        for pos in positions:
            args = set(arg.lower().strip() for arg in pos.key_arguments)
            agent_arguments[pos.agent_id] = args
            all_arguments.update(args)
        
        if all_arguments:
            # Calculate Jaccard-like similarity across all agents
            shared_count: float = 0.0
            total_pairs = 0
            agent_ids = list(agent_arguments.keys())
            
            for i, aid1 in enumerate(agent_ids):
                for aid2 in agent_ids[i+1:]:
                    args1 = agent_arguments[aid1]
                    args2 = agent_arguments[aid2]
                    if args1 or args2:
                        intersection = len(args1 & args2)
                        union = len(args1 | args2)
                        if union > 0:
                            shared_count += intersection / union
                        total_pairs += 1
            
            stance_convergence = shared_count / total_pairs if total_pairs > 0 else 0.5
        else:
            stance_convergence = 0.5
        
        # Component 3: Acknowledged weaknesses alignment (weight: 0.2)
        all_weaknesses: Set[str] = set()
        for pos in positions:
            all_weaknesses.update(w.lower().strip() for w in pos.acknowledged_weaknesses)
        
        if all_weaknesses:
            weakness_convergence = min(1.0, len(all_weaknesses) / (len(positions) * 2))
        else:
            weakness_convergence = 0.5
        
        # Weighted average
        total_convergence = (
            0.4 * confidence_convergence +
            0.4 * stance_convergence +
            0.2 * weakness_convergence
        )
        
        return round(total_convergence, 3)
    
    def calculate_weighted_convergence(
        self,
        positions: Dict[str, Position],
        weights: Dict[str, float],
    ) -> float:
        """Calculate convergence with agent weights.
        
        Weights based on:
        - Agent specialty match to topic
        - Historical accuracy
        - Debate performance
        
        Args:
            positions: Positions by agent ID
            weights: Weight per agent ID
        
        Returns:
            Weighted convergence score
        """
        if not positions or len(positions) < 2:
            return 1.0
        
        # Normalize weights
        total_weight = sum(weights.get(aid, 1.0) for aid in positions.keys())
        normalized = {
            aid: weights.get(aid, 1.0) / total_weight 
            for aid in positions.keys()
        }
        
        # Weighted mean confidence
        weighted_conf = sum(
            positions[aid].confidence * normalized[aid]
            for aid in positions.keys()
        )
        
        # Weighted variance
        weighted_variance = sum(
            normalized[aid] * (positions[aid].confidence - weighted_conf) ** 2
            for aid in positions.keys()
        )
        
        # Convert to convergence
        convergence = max(0.0, 1.0 - weighted_variance * 4)
        
        return round(convergence, 3)
    
    # =========================================================================
    # Termination Conditions
    # =========================================================================
    
    def _check_termination(
        self,
        timeline: DebateTimeline,
        current_round: int,
    ) -> Optional[str]:
        """Check if debate should terminate.
        
        Termination conditions:
        - Max rounds reached
        - Convergence threshold met
        - Stalemate (no changes in N rounds)
        
        Args:
            timeline: Current debate timeline
            current_round: Current round number
        
        Returns:
            Termination reason or None
        """
        # Check convergence threshold
        if timeline.rounds:
            last_convergence = timeline.rounds[-1].convergence_score
            if last_convergence >= self.config.convergence_threshold:
                return f"Convergence threshold reached ({last_convergence:.2f})"
        
        # Check max rounds
        if current_round >= self.config.max_rounds:
            return f"Max rounds ({self.config.max_rounds}) reached"
        
        # Check for stalemate
        if len(timeline.rounds) >= self.config.stalemate_rounds:
            recent_rounds = timeline.rounds[-self.config.stalemate_rounds:]
            no_changes = all(
                len(r.position_updates) == 0 for r in recent_rounds
            )
            if no_changes:
                return f"Stalemate detected (no changes in {self.config.stalemate_rounds} rounds)"
        
        return None
    
    def _should_invoke_judge(self, timeline: DebateTimeline) -> bool:
        """Determine if judge should be invoked.
        
        Judge is invoked when:
        - Completed 3+ rounds
        - Convergence still below threshold
        
        Args:
            timeline: Debate timeline
        
        Returns:
            True if judge should arbitrate
        """
        if len(timeline.rounds) < 3:
            return False
        
        return timeline.final_convergence < self.config.judge_invocation_threshold
    
    # =========================================================================
    # Turning Points & Visualization
    # =========================================================================
    
    def _identify_turning_points(
        self,
        timeline: DebateTimeline,
        trajectories: Dict[str, PositionTrajectory],
    ) -> List[TurningPoint]:
        """Identify significant turning points in debate.
        
        Turning points are moments where:
        - Agent significantly changed position
        - Convergence notably improved
        - Key evidence changed the discussion
        
        Args:
            timeline: Debate timeline
            trajectories: Position trajectories by agent
        
        Returns:
            List of turning points
        """
        turning_points = []
        
        for round_result in timeline.rounds:
            # Check for significant position changes
            for agent_id, update in round_result.position_updates.items():
                trajectory = trajectories.get(agent_id)
                if not trajectory or not trajectory.position_history:
                    continue
                
                # Get previous position
                prev_positions = trajectory.position_history[:-1] if len(trajectory.position_history) > 1 else []
                if not prev_positions:
                    continue
                
                prev_pos = prev_positions[-1]
                confidence_change = abs(update.new_confidence - prev_pos.confidence)
                
                # Significant change threshold
                if confidence_change > 0.15 or update.new_stance != prev_pos.stance:
                    turning_points.append(TurningPoint(
                        round_number=round_result.round_number,
                        agent_id=agent_id,
                        description=update.reason_for_change,
                        position_before=prev_pos.stance[:100] if prev_pos.stance else "",
                        position_after=update.new_stance[:100] if update.new_stance else "",
                        catalyst=f"Influenced by: {', '.join(update.influenced_by[:3])}",
                    ))
            
            # Check for convergence jumps
            if round_result.round_number > 1:
                prev_round = timeline.rounds[round_result.round_number - 2]
                convergence_jump = round_result.convergence_score - prev_round.convergence_score
                
                if convergence_jump > 0.15:
                    turning_points.append(TurningPoint(
                        round_number=round_result.round_number,
                        description=f"Convergence improved by {convergence_jump:.2f}",
                        catalyst=f"Round {round_result.round_number} debate",
                    ))
        
        return turning_points
    
    def generate_disagreement_map(
        self,
        analyses: List[AgentAnalysis],
        timeline: Optional[DebateTimeline],
    ) -> DisagreementMap:
        """Generate a map of disagreements for visualization.
        
        Args:
            analyses: All agent analyses
            timeline: Debate timeline (if available)
        
        Returns:
            DisagreementMap with visualization data
        """
        disagreement_map = DisagreementMap(
            analysis_id=self._current_debate_id or "",
        )
        
        # Build disagreement points from analyses
        findings_by_category: Dict[str, List[Tuple[Finding, str, float]]] = {}
        
        for analysis in analyses:
            for finding in analysis.findings:
                cat = finding.category.value
                if cat not in findings_by_category:
                    findings_by_category[cat] = []
                findings_by_category[cat].append((
                    finding, analysis.agent_id, analysis.overall_confidence
                ))
        
        # Create disagreement points for categories with multiple findings
        for category, findings_list in findings_by_category.items():
            if len(findings_list) < 2:
                continue
            
            confidences = [f[2] for f in findings_list]
            disagreement_mag = max(confidences) - min(confidences)
            
            if disagreement_mag > 0.1:  # Only track meaningful disagreements
                point = DisagreementPoint(
                    topic=category,
                    agent_positions={f[1]: f[0].description[:100] for f in findings_list},
                    agent_confidences={f[1]: f[2] for f in findings_list},
                    magnitude_of_disagreement=disagreement_mag,
                    key_arguments={f[1]: [f[0].description] for f in findings_list},
                )
                
                # Check if resolved through debate
                if timeline and timeline.final_convergence >= 0.8:
                    point.resolution_status = "resolved"
                elif timeline and timeline.final_convergence >= 0.6:
                    point.resolution_status = "partially_resolved"
                
                disagreement_map.points.append(point)
                disagreement_map.topic_disagreement_scores[category] = disagreement_mag
        
        disagreement_map.total_disagreements = len(disagreement_map.points)
        disagreement_map.resolved_count = sum(
            1 for p in disagreement_map.points 
            if p.resolution_status == "resolved"
        )
        
        # Find agent pairs with most disagreement
        agent_pair_disagreement: Dict[Tuple[str, str], float] = {}
        for point in disagreement_map.points:
            agents = list(point.agent_confidences.keys())
            for i, a1 in enumerate(agents):
                for a2 in agents[i+1:]:
                    pair = (min(a1, a2), max(a1, a2))
                    conf_diff = abs(
                        point.agent_confidences.get(a1, 0) -
                        point.agent_confidences.get(a2, 0)
                    )
                    if pair not in agent_pair_disagreement:
                        agent_pair_disagreement[pair] = 0
                    agent_pair_disagreement[pair] += conf_diff
        
        sorted_pairs = sorted(
            agent_pair_disagreement.items(),
            key=lambda x: x[1],
            reverse=True
        )
        disagreement_map.agent_pairs_most_disagreement = [
            (p[0][0], p[0][1], p[1]) for p in sorted_pairs[:5]
        ]
        
        return disagreement_map
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _create_position_from_analysis(
        self,
        analysis: AgentAnalysis,
        topic: str,
    ) -> Position:
        """Create a Position from an AgentAnalysis.
        
        Args:
            analysis: The agent's analysis
            topic: The debate topic
        
        Returns:
            Position object
        """
        return Position(
            agent_id=analysis.agent_id,
            topic=topic,
            stance=analysis.executive_summary,
            confidence=analysis.overall_confidence,
            key_arguments=analysis.key_takeaways,
            supporting_evidence=[
                ev.description for f in analysis.findings 
                for ev in f.supporting_evidence
            ][:5],
            acknowledged_weaknesses=analysis.uncertainty_areas[:3],
        )
    
    def _init_agent_performance(self, analyses: List[AgentAnalysis]) -> None:
        """Initialize performance tracking for agents.
        
        Args:
            analyses: All agent analyses
        """
        self._agent_performance = {
            a.agent_id: AgentDebatePerformance(agent_id=a.agent_id)
            for a in analyses
        }
    
    def _update_performance_metrics(self, round_result: DebateRound) -> None:
        """Update agent performance metrics from round result.
        
        Args:
            round_result: Completed debate round
        """
        # Update critique counts
        critiques_given: Dict[str, int] = {}
        critiques_received: Dict[str, int] = {}
        
        for critique in round_result.critiques:
            critiques_given[critique.critic_id] = critiques_given.get(critique.critic_id, 0) + 1
            critiques_received[critique.target_id] = critiques_received.get(critique.target_id, 0) + 1
        
        for agent_id in self._agent_performance:
            perf = self._agent_performance[agent_id]
            perf.arguments_made += critiques_given.get(agent_id, 0)
            perf.critiques_received += critiques_received.get(agent_id, 0)
        
        # Update position change counts
        for agent_id in round_result.position_updates:
            if agent_id in self._agent_performance:
                self._agent_performance[agent_id].position_changes += 1
        
        # Update acknowledgment counts from rebuttals
        for rebuttal in round_result.rebuttals:
            if rebuttal.acknowledgment and rebuttal.rebutter_id in self._agent_performance:
                self._agent_performance[rebuttal.rebutter_id].critiques_acknowledged += 1
    
    def _gather_evidence_for_judge(
        self,
        analyses: List[AgentAnalysis],
    ) -> Dict[str, List[Evidence]]:
        """Gather evidence from analyses for judge review.
        
        Args:
            analyses: All agent analyses
        
        Returns:
            Dictionary of agent_id -> evidence list
        """
        evidence = {}
        
        for analysis in analyses:
            agent_evidence = []
            for finding in analysis.findings:
                for ev in finding.supporting_evidence:
                    agent_evidence.append(ev)
            evidence[analysis.agent_id] = agent_evidence
        
        return evidence
    
    async def _emit_event(
        self,
        event_type: AnalysisEventType,
        data: Dict[str, Any],
    ) -> None:
        """Emit a debate event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if self._event_callback is None:
            return
        
        event = AnalysisEvent(
            event_type=event_type,
            analysis_id=self._current_debate_id or "",
            data=data,
        )
        
        await self._event_callback(event)
    
    def get_agent_performance(self) -> Dict[str, AgentDebatePerformance]:
        """Get performance metrics for all agents.
        
        Returns:
            Dictionary of agent_id -> performance metrics
        """
        return dict(self._agent_performance)


# =============================================================================
# Debate Moderator (Optional Advanced Feature)
# =============================================================================

class DebateModerator:
    """Moderator for managing debate flow and quality.
    
    The moderator:
    - Identifies most contentious topics
    - Balances speaking turns
    - Prevents circular arguments
    - Tracks argument quality
    - Decides when to invoke judge
    
    This is an optional enhancement over the basic DebateEngine.
    """
    
    def __init__(self, config: Optional[DebateConfig] = None):
        self.config = config or DebateConfig()
        self._argument_history: List[str] = []
        self._turn_counts: Dict[str, int] = {}
        self._argument_quality_scores: Dict[str, List[ArgumentQuality]] = {}
    
    def rank_contentious_topics(
        self,
        topics: List[DebateTopic],
    ) -> List[DebateTopic]:
        """Rank topics by contentiousness for debate priority.
        
        Args:
            topics: List of debate topics
        
        Returns:
            Topics sorted by contentiousness (highest first)
        """
        def contentiousness_score(topic: DebateTopic) -> float:
            score = 0.0
            
            # More triggers = more contentious
            score += len(topic.triggers) * 0.2
            
            # Critical triggers add more
            for trigger in topic.triggers:
                if trigger.severity == "critical":
                    score += 0.5
                elif trigger.severity == "major":
                    score += 0.3
                elif trigger.severity == "moderate":
                    score += 0.1
            
            # More agents involved = more contentious
            all_agents = set()
            for trigger in topic.triggers:
                all_agents.update(trigger.agents_involved)
            score += len(all_agents) * 0.1
            
            return score
        
        return sorted(topics, key=contentiousness_score, reverse=True)
    
    def balance_turns(
        self,
        agents: List[str],
        current_speaker: str,
    ) -> str:
        """Select next speaker to balance participation.
        
        Args:
            agents: List of agent IDs
            current_speaker: Current speaker ID
        
        Returns:
            Next speaker ID
        """
        # Initialize turn counts if needed
        for agent in agents:
            if agent not in self._turn_counts:
                self._turn_counts[agent] = 0
        
        self._turn_counts[current_speaker] += 1
        
        # Select agent with fewest turns
        other_agents = [a for a in agents if a != current_speaker]
        if not other_agents:
            return current_speaker
        
        return min(other_agents, key=lambda a: self._turn_counts.get(a, 0))
    
    def is_circular_argument(
        self,
        argument: str,
        similarity_threshold: float = 0.8,
    ) -> bool:
        """Check if argument is circular (repeating previous points).
        
        Args:
            argument: The argument text
            similarity_threshold: Threshold for considering circular
        
        Returns:
            True if argument appears circular
        """
        argument_lower = argument.lower().strip()
        
        for prev_arg in self._argument_history[-10:]:  # Check last 10 arguments
            # Simple similarity check (could be enhanced with embeddings)
            words_new = set(argument_lower.split())
            words_prev = set(prev_arg.lower().split())
            
            if words_new and words_prev:
                intersection = len(words_new & words_prev)
                union = len(words_new | words_prev)
                similarity = intersection / union if union > 0 else 0
                
                if similarity > similarity_threshold:
                    return True
        
        self._argument_history.append(argument_lower)
        return False
    
    def assess_argument_quality(
        self,
        agent_id: str,
        argument: str,
        has_evidence: bool,
        is_novel: bool,
    ) -> ArgumentQuality:
        """Assess the quality of an argument.
        
        Args:
            agent_id: ID of arguing agent
            argument: The argument text
            has_evidence: Whether evidence was provided
            is_novel: Whether argument is novel (not circular)
        
        Returns:
            ArgumentQuality assessment
        """
        quality = ArgumentQuality(
            agent_id=agent_id,
            argument_type="general",
            evidence_quality=0.8 if has_evidence else 0.3,
            logical_coherence=0.7,  # Would need NLP to assess properly
            relevance=0.8,
            novelty=0.8 if is_novel else 0.2,
        )
        
        # Calculate overall quality
        quality.overall_quality = (
            0.3 * quality.evidence_quality +
            0.3 * quality.logical_coherence +
            0.2 * quality.relevance +
            0.2 * quality.novelty
        )
        
        # Track for agent
        if agent_id not in self._argument_quality_scores:
            self._argument_quality_scores[agent_id] = []
        self._argument_quality_scores[agent_id].append(quality)
        
        return quality
    
    def get_agent_quality_average(self, agent_id: str) -> float:
        """Get average argument quality for an agent.
        
        Args:
            agent_id: Agent ID
        
        Returns:
            Average quality score
        """
        scores = self._argument_quality_scores.get(agent_id, [])
        if not scores:
            return 0.5
        return sum(q.overall_quality for q in scores) / len(scores)
