"""Judge Agent for final arbitration in Multi-Agent debates.

The Judge Agent is a special agent that arbitrates when standard debate
fails to reach consensus. It reviews the entire debate history, weighs
evidence from all sides, and makes final determinations.
"""

import json
import logging
from datetime import datetime
from typing import Any, Callable, Awaitable, Dict, List, Optional
from uuid import uuid4

from core.agents.base_agent import BaseAgent, AnalysisContext
from core.agents.types import (
    AgentType,
    FindingCategory,
    ImpactMagnitude,
    CritiqueType,
    CritiqueSeverity,
    VoteType,
    ThoughtType,
    ConsensusLevel,
)
from core.agents.models import (
    AgentConfig,
    AgentAnalysis,
    Finding,
    Assumption,
    Critique,
    Vote,
    Proposal,
    DebateRound,
    Position,
    Evidence,
    ConsensusFinding,
)


logger = logging.getLogger(__name__)


class Arbitration:
    """Result of judge arbitration."""
    
    def __init__(
        self,
        topic: str,
        final_position: str,
        confidence: float,
        reasoning: str,
        evidence_cited: List[str],
        dissent_acknowledged: List[str],
        recommendations: List[str],
    ):
        self.arbitration_id = str(uuid4())[:8]
        self.topic = topic
        self.final_position = final_position
        self.confidence = confidence
        self.reasoning = reasoning
        self.evidence_cited = evidence_cited
        self.dissent_acknowledged = dissent_acknowledged
        self.recommendations = recommendations
        self.timestamp = datetime.now()


class JudgeAgent(BaseAgent):
    """Special agent for final arbitration of unresolved debates.
    
    The Judge Agent is invoked only when standard debate fails to converge
    (convergence < 0.6 after round 3). It reviews the entire debate history,
    considers all positions and evidence, and makes a final determination.
    
    Key capabilities:
    - Comprehensive debate review
    - Evidence weighing across all agents
    - Fair treatment of minority positions
    - Final determination with confidence
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Judge Agent.
        
        Args:
            config: Optional agent configuration.
        """
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.JUDGE,
                model="claude-sonnet-4-20250514",
                temperature=0.2,  # Lower temperature for more consistent judgments
                confidence_threshold=0.6,
                specialization_prompt=self._get_default_specialization(),
            )
        
        super().__init__(config)
    
    def _get_default_specialization(self) -> str:
        """Return default specialization prompt."""
        return """You are an impartial arbiter with expertise across fiscal, economic, 
healthcare, and social policy domains. Your role is to make fair, evidence-based 
determinations when expert agents cannot reach consensus through debate.

You value:
- Rigorous evidence over speculation
- Acknowledging genuine uncertainty
- Fair representation of minority views
- Clear reasoning for your determinations"""
    
    def _get_specialty_description(self) -> str:
        """Return description of judge agent specialty."""
        return "Impartial arbitration: resolving expert disagreements with evidence-based judgments"
    
    def _get_system_prompt(self) -> str:
        """Return system prompt for judge arbitration."""
        return f"""You are the Judge Agent in PoliSim's Multi-Agent Policy Analysis Swarm.

ROLE: You arbitrate when expert agents cannot reach consensus through debate.

RESPONSIBILITIES:
1. Review the complete debate history fairly
2. Weigh evidence presented by all parties
3. Identify the strongest arguments on each side
4. Acknowledge legitimate uncertainty
5. Make a final determination with clear reasoning
6. Document dissenting views fairly

ARBITRATION STANDARDS:
- Base decisions on evidence quality, not agent count
- Give appropriate weight to domain expertise
- Distinguish methodological disagreements from factual disputes
- Acknowledge when uncertainty prevents definitive conclusions
- Provide actionable recommendations

OUTPUT FORMAT:
Provide arbitration with:
- Final position on the disputed topic
- Confidence level (0-1 scale)
- Key evidence supporting the determination
- Acknowledged dissent and its merits
- Recommendations for further analysis if needed

{self.config.specialization_prompt}"""
    
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return analysis prompt - Judge typically uses arbitrate() instead."""
        return "Judge Agent performs arbitration, not standard analysis."
    
    def _get_critique_prompt(self, analysis: AgentAnalysis) -> str:
        """Return critique prompt - Judge doesn't critique, it arbitrates."""
        return "Judge Agent arbitrates, does not critique."
    
    async def _parse_analysis_response(
        self,
        response: str,
        context: AnalysisContext
    ) -> AgentAnalysis:
        """Parse response - Judge typically uses arbitrate() instead."""
        return AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
        )
    
    async def _parse_critique_response(
        self,
        response: str,
        target_analysis: AgentAnalysis
    ) -> List[Critique]:
        """Parse critique response - Judge doesn't critique."""
        return []
    
    # =========================================================================
    # Judge-Specific Methods
    # =========================================================================
    
    async def arbitrate(
        self,
        debate_history: List[DebateRound],
        positions: Dict[str, Position],
        evidence: Dict[str, List[Evidence]],
        context: Optional[AnalysisContext] = None,
    ) -> Arbitration:
        """Arbitrate an unresolved debate.
        
        This is the primary method for the Judge Agent. It reviews the complete
        debate history, all positions, and evidence to make a final determination.
        
        Args:
            debate_history: List of all debate rounds
            positions: Current positions by agent ID
            evidence: Evidence presented by each agent
            context: Optional analysis context for reference
        
        Returns:
            Arbitration result with final position and reasoning
        """
        logger.info(f"Judge Agent {self.agent_id} beginning arbitration")
        
        if not debate_history:
            return Arbitration(
                topic="Unknown",
                final_position="Insufficient debate history for arbitration",
                confidence=0.3,
                reasoning="No debate rounds provided",
                evidence_cited=[],
                dissent_acknowledged=[],
                recommendations=["Conduct debate before requesting arbitration"],
            )
        
        # Get the topic from the last debate round
        topic = debate_history[-1].topic if debate_history else "Unknown topic"
        
        # Analyze the debate
        position_analysis = self._analyze_positions(positions)
        evidence_quality = self._assess_evidence_quality(evidence)
        convergence_trend = self._analyze_convergence_trend(debate_history)
        key_disagreements = self._identify_key_disagreements(debate_history)
        
        # Determine final position based on analysis
        final_position, confidence, reasoning = self._determine_final_position(
            position_analysis,
            evidence_quality,
            convergence_trend,
            key_disagreements,
        )
        
        # Identify evidence to cite
        evidence_cited = self._select_key_evidence(evidence, evidence_quality)
        
        # Acknowledge dissent fairly
        dissent_acknowledged = self._acknowledge_dissent(
            positions, final_position, key_disagreements
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            confidence, key_disagreements, evidence_quality
        )
        
        arbitration = Arbitration(
            topic=topic,
            final_position=final_position,
            confidence=confidence,
            reasoning=reasoning,
            evidence_cited=evidence_cited,
            dissent_acknowledged=dissent_acknowledged,
            recommendations=recommendations,
        )
        
        logger.info(
            f"Judge arbitration complete: confidence {confidence:.2f}, "
            f"{len(dissent_acknowledged)} dissenting views acknowledged"
        )
        
        return arbitration
    
    def _analyze_positions(self, positions: Dict[str, Position]) -> Dict[str, Any]:
        """Analyze the distribution and strength of positions."""
        if not positions:
            return {"count": 0, "unique_stances": 0, "average_confidence": 0}
        
        stances = [p.stance for p in positions.values()]
        confidences = [p.confidence for p in positions.values()]
        
        # Group similar stances
        unique_stances = len(set(stances))
        
        return {
            "count": len(positions),
            "unique_stances": unique_stances,
            "average_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "positions": positions,
            "majority_stance": max(set(stances), key=stances.count) if stances else None,
        }
    
    def _assess_evidence_quality(
        self, evidence: Dict[str, List[Evidence]]
    ) -> Dict[str, float]:
        """Assess the quality of evidence from each agent."""
        quality_scores = {}
        
        for agent_id, agent_evidence in evidence.items():
            if not agent_evidence:
                quality_scores[agent_id] = 0.0
                continue
            
            # Average reliability of evidence
            avg_reliability = sum(e.reliability for e in agent_evidence) / len(agent_evidence)
            
            # Bonus for citing official sources
            official_sources = sum(
                1 for e in agent_evidence 
                if any(s in e.source.lower() for s in ["cbo", "ssa", "cms", "bls", "treasury"])
            )
            source_bonus = min(0.2, official_sources * 0.05)
            
            quality_scores[agent_id] = min(1.0, avg_reliability + source_bonus)
        
        return quality_scores
    
    def _analyze_convergence_trend(
        self, debate_history: List[DebateRound]
    ) -> Dict[str, Any]:
        """Analyze how convergence changed over debate rounds."""
        if not debate_history:
            return {"trend": "none", "final_convergence": 0}
        
        convergences = [round.convergence_score for round in debate_history]
        
        # Determine trend
        if len(convergences) < 2:
            trend = "insufficient_data"
        elif convergences[-1] > convergences[0]:
            trend = "improving"
        elif convergences[-1] < convergences[0]:
            trend = "degrading"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "final_convergence": convergences[-1] if convergences else 0,
            "convergence_history": convergences,
        }
    
    def _identify_key_disagreements(
        self, debate_history: List[DebateRound]
    ) -> List[Dict[str, Any]]:
        """Identify the key points of disagreement from debate."""
        disagreements = []
        
        for round in debate_history:
            # Look at critiques for major disagreements
            for critique in round.critiques:
                if critique.severity in [CritiqueSeverity.MAJOR, CritiqueSeverity.CRITICAL]:
                    disagreements.append({
                        "critic": critique.critic_id,
                        "target": critique.target_id,
                        "type": critique.critique_type.value,
                        "argument": critique.argument,
                        "severity": critique.severity.value,
                    })
        
        return disagreements
    
    def _determine_final_position(
        self,
        position_analysis: Dict[str, Any],
        evidence_quality: Dict[str, float],
        convergence_trend: Dict[str, Any],
        key_disagreements: List[Dict[str, Any]],
    ) -> tuple:
        """Determine the final position based on all analysis."""
        
        positions = position_analysis.get("positions", {})
        
        if not positions:
            return (
                "Unable to determine position due to insufficient data",
                0.3,
                "No positions provided for arbitration"
            )
        
        # Weight positions by evidence quality
        weighted_positions = []
        for agent_id, position in positions.items():
            evidence_weight = evidence_quality.get(agent_id, 0.5)
            weighted_positions.append({
                "agent": agent_id,
                "stance": position.stance,
                "weight": position.confidence * evidence_weight,
                "arguments": position.key_arguments,
            })
        
        # Sort by weight
        weighted_positions.sort(key=lambda x: x["weight"], reverse=True)
        
        # Take the highest-weighted position
        if weighted_positions:
            best = weighted_positions[0]
            
            # Confidence based on weight difference and convergence
            confidence = min(0.9, best["weight"])
            if len(weighted_positions) > 1:
                weight_gap = best["weight"] - weighted_positions[1]["weight"]
                confidence = min(confidence, 0.5 + weight_gap)
            
            # Adjust for convergence trend
            if convergence_trend["trend"] == "improving":
                confidence = min(0.95, confidence + 0.1)
            elif convergence_trend["trend"] == "degrading":
                confidence = max(0.3, confidence - 0.1)
            
            reasoning = (
                f"Position supported by strongest evidence (weight: {best['weight']:.2f}). "
                f"Convergence trend: {convergence_trend['trend']}. "
                f"Key arguments: {'; '.join(best['arguments'][:3]) if best['arguments'] else 'None specified'}"
            )
            
            return (best["stance"], confidence, reasoning)
        
        return (
            "No clear position determinable",
            0.3,
            "Unable to weigh competing positions"
        )
    
    def _select_key_evidence(
        self,
        evidence: Dict[str, List[Evidence]],
        quality_scores: Dict[str, float],
    ) -> List[str]:
        """Select key evidence to cite in arbitration."""
        all_evidence = []
        
        for agent_id, agent_evidence in evidence.items():
            quality = quality_scores.get(agent_id, 0.5)
            for ev in agent_evidence:
                all_evidence.append({
                    "description": ev.description,
                    "source": ev.source,
                    "combined_score": ev.reliability * quality,
                })
        
        # Sort by combined score and take top evidence
        all_evidence.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return [
            f"{e['description']} ({e['source']})"
            for e in all_evidence[:5]
        ]
    
    def _acknowledge_dissent(
        self,
        positions: Dict[str, Position],
        final_position: str,
        key_disagreements: List[Dict[str, Any]],
    ) -> List[str]:
        """Fairly acknowledge dissenting views."""
        dissents = []
        
        for agent_id, position in positions.items():
            # If position differs from final
            if position.stance.lower() != final_position.lower():
                dissent_note = f"{agent_id}: {position.stance}"
                if position.key_arguments:
                    dissent_note += f" (argues: {position.key_arguments[0]})"
                dissents.append(dissent_note)
        
        return dissents[:5]  # Limit to top 5 dissents
    
    def _generate_recommendations(
        self,
        confidence: float,
        key_disagreements: List[Dict[str, Any]],
        evidence_quality: Dict[str, float],
    ) -> List[str]:
        """Generate recommendations based on arbitration."""
        recommendations = []
        
        if confidence < 0.6:
            recommendations.append(
                "Low confidence suggests further research is needed before policy implementation"
            )
        
        if key_disagreements:
            recommendations.append(
                f"Address {len(key_disagreements)} major disagreements through additional analysis"
            )
        
        low_quality_agents = [
            agent for agent, quality in evidence_quality.items() 
            if quality < 0.5
        ]
        if low_quality_agents:
            recommendations.append(
                "Strengthen evidence base with additional official data sources"
            )
        
        if not recommendations:
            recommendations.append("Arbitration reached with reasonable confidence")
        
        return recommendations
    
    def arbitration_to_consensus_finding(
        self,
        arbitration: Arbitration,
        category: FindingCategory = FindingCategory.OTHER,
    ) -> ConsensusFinding:
        """Convert an Arbitration to a ConsensusFinding for the report."""
        
        # Determine consensus level from confidence
        if arbitration.confidence >= 0.8:
            level = ConsensusLevel.STRONG_CONSENSUS
        elif arbitration.confidence >= 0.6:
            level = ConsensusLevel.CONSENSUS
        elif arbitration.confidence >= 0.5:
            level = ConsensusLevel.MAJORITY
        else:
            level = ConsensusLevel.DIVIDED
        
        return ConsensusFinding(
            description=arbitration.final_position,
            category=category,
            consensus_level=level,
            weighted_confidence=arbitration.confidence,
            dissenting_agents=[d.split(":")[0] for d in arbitration.dissent_acknowledged],
            dissent_reasons={
                d.split(":")[0]: d.split(":")[-1].strip() 
                for d in arbitration.dissent_acknowledged
            },
        )
    
    # =========================================================================
    # BaseAgent Interface Implementation
    # =========================================================================
    
    async def analyze(
        self,
        context: AnalysisContext,
        event_callback: Optional[Callable[[Any], Awaitable[None]]] = None
    ) -> AgentAnalysis:
        """Judge Agent doesn't perform standard analysis.
        
        Use arbitrate() method instead for resolving debates.
        """
        logger.warning("Judge Agent should use arbitrate() method, not analyze()")
        return AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            executive_summary="Judge Agent does not perform standard analysis. Use arbitrate() for debate resolution.",
            overall_confidence=0.0,
        )
    
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Judge Agent doesn't critique - it arbitrates.
        
        Use arbitrate() method instead.
        """
        logger.warning("Judge Agent should use arbitrate() method, not critique()")
        return []
    
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Judge Agent can vote but typically arbitrates instead."""
        votes = []
        
        for proposal in proposals:
            # Judge votes neutrally, as arbitration is its primary role
            votes.append(Vote(
                voter_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                support=VoteType.NEUTRAL,
                confidence=0.5,
                reasoning="Judge Agent typically arbitrates rather than votes",
            ))
        
        return votes
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Judge has equal weight across all topics."""
        return 1.0
