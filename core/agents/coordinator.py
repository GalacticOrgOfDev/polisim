"""Swarm Coordinator for orchestrating multi-agent analysis.

The SwarmCoordinator is the central orchestrator that manages the full
analysis pipeline: ingestion, parallel analysis, cross-review, debate,
voting, and synthesis.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Awaitable, Dict, List, Optional
from uuid import uuid4

from core.agents.types import (
    AgentType,
    PipelineState,
    AnalysisEventType,
    ConsensusLevel,
    CritiqueSeverity,
    CONSENSUS_THRESHOLDS,
)
from core.agents.models import (
    SwarmConfig,
    AgentConfig,
    AgentAnalysis,
    Finding,
    ConsensusFinding,
    Disagreement,
    ConfidenceBand,
    SwarmAnalysis,
    AnalysisMetadata,
    ConsensusReport,
    ConsensusResult,
    DebateRound,
    DebateTimeline,
    TurningPoint,
    Position,
    Critique,
    Vote,
    Proposal,
    AnalysisEvent,
    Evidence,
)
from core.agents.base_agent import BaseAgent, AnalysisContext
from core.agents.factory import AgentFactory, create_agent
from core.agents.judge_agent import JudgeAgent
from core.agents.debate_engine import DebateEngine, DebateConfig, DisagreementMap


logger = logging.getLogger(__name__)


class SwarmCoordinator:
    """Orchestrator for multi-agent policy analysis.
    
    The SwarmCoordinator manages the complete analysis pipeline:
    
    1. **Ingestion**: Parse bill, extract sections and mechanisms
    2. **Parallel Analysis**: Each agent analyzes independently
    3. **Cross-Review**: Agents critique each other's findings
    4. **Debate**: Agents discuss disagreements (max 3 rounds)
    5. **Consensus**: Weighted voting on conclusions
    6. **Synthesis**: Combine into unified report
    
    Example:
        coordinator = SwarmCoordinator()
        result = await coordinator.analyze_bill(bill_context)
    """
    
    def __init__(
        self,
        config: Optional[SwarmConfig] = None,
        agents: Optional[Dict[str, BaseAgent]] = None,
    ):
        """Initialize the coordinator.
        
        Args:
            config: Swarm configuration. Uses defaults if not provided.
            agents: Pre-created agents. If not provided, creates Tier 1 agents.
        """
        self.config = config or SwarmConfig()
        self.agents: Dict[str, BaseAgent] = agents or {}
        self.judge: Optional[JudgeAgent] = None
        
        # Initialize debate engine with config
        debate_config = DebateConfig(
            max_rounds=self.config.max_debate_rounds,
            convergence_threshold=self.config.convergence_threshold,
        )
        self.debate_engine = DebateEngine(config=debate_config)
        
        # Pipeline state
        self.state = PipelineState.INITIALIZED
        self._current_analysis_id: Optional[str] = None
        self._event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None
        
        # Create default agents if none provided
        if not self.agents:
            self._create_default_agents()
        
        logger.info(
            f"SwarmCoordinator initialized with {len(self.agents)} agents"
        )
    
    def _create_default_agents(self) -> None:
        """Create the default Tier 1 agents."""
        factory = AgentFactory()
        self.agents = factory.create_tier1_agents()
        self.judge = JudgeAgent()
        
        # Attach judge to debate engine
        self.debate_engine.judge = self.judge
    
    async def analyze_bill(
        self,
        context: AnalysisContext,
        event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None,
    ) -> SwarmAnalysis:
        """Orchestrate full bill analysis pipeline.
        
        This is the main entry point for swarm analysis. It runs through
        all pipeline stages and produces a comprehensive SwarmAnalysis.
        
        Args:
            context: Analysis context with bill text and data
            event_callback: Optional callback for streaming events
        
        Returns:
            SwarmAnalysis with agent analyses, debate, and consensus
        """
        self._event_callback = event_callback
        self._current_analysis_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Starting swarm analysis for bill {context.bill_id}")
        
        # Initialize result
        result = SwarmAnalysis(
            analysis_id=self._current_analysis_id,
            bill_id=context.bill_id,
        )
        result.metadata.timestamp_start = start_time
        
        try:
            # Stage 1: Ingestion (already done via context)
            await self._emit_event(
                AnalysisEventType.PIPELINE_STARTED,
                {"bill_id": context.bill_id, "agents": list(self.agents.keys())}
            )
            self.state = PipelineState.INGESTING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "ingesting"})
            
            # Stage 2: Parallel Analysis
            self.state = PipelineState.ANALYZING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "analyzing"})
            
            agent_analyses = await self._execute_parallel_analysis(context)
            result.agent_analyses = {a.agent_id: a for a in agent_analyses}
            result.metadata.agents_participated = len(agent_analyses)
            
            # Stage 3: Cross-Review
            self.state = PipelineState.CROSS_REVIEWING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "cross_reviewing"})
            
            all_critiques = await self._execute_cross_review(agent_analyses, context)
            
            # Stage 4: Debate (if disagreements exist)
            self.state = PipelineState.DEBATING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "debating"})
            
            debate_timeline = await self._run_debate(
                agent_analyses, all_critiques, context
            )
            result.debate_timeline = debate_timeline
            result.metadata.debate_rounds_conducted = len(debate_timeline.rounds) if debate_timeline else 0
            
            # Stage 5: Consensus
            self.state = PipelineState.VOTING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "voting"})
            
            consensus_findings, disagreements = await self._build_consensus(
                agent_analyses, debate_timeline, context
            )
            result.consensus_findings = consensus_findings
            result.disagreements = disagreements
            
            # Calculate confidence bands
            result.confidence_bands = self._calculate_confidence_bands(
                agent_analyses, consensus_findings
            )
            
            # Stage 6: Synthesis
            self.state = PipelineState.SYNTHESIZING
            await self._emit_event(AnalysisEventType.STAGE_CHANGED, {"stage": "synthesizing"})
            
            result.consensus_report = self._synthesize_report(
                result, context
            )
            
            self.state = PipelineState.COMPLETE
            await self._emit_event(
                AnalysisEventType.ANALYSIS_COMPLETE,
                {"analysis_id": self._current_analysis_id}
            )
            
        except Exception as e:
            self.state = PipelineState.ERROR
            logger.error(f"Pipeline error: {e}")
            await self._emit_event(AnalysisEventType.ERROR, {"error": str(e)})
            raise
        
        finally:
            result.metadata.timestamp_end = datetime.now()
            result.metadata.total_execution_time_seconds = (
                result.metadata.timestamp_end - start_time
            ).total_seconds()
            result.metadata.total_tokens_used = sum(
                a.tokens_used for a in result.agent_analyses.values()
            )
        
        logger.info(
            f"Swarm analysis complete: {len(result.consensus_findings)} consensus findings, "
            f"{len(result.disagreements)} disagreements, "
            f"{result.metadata.total_execution_time_seconds:.1f}s total"
        )
        
        return result
    
    async def _execute_parallel_analysis(
        self,
        context: AnalysisContext,
    ) -> List[AgentAnalysis]:
        """Run all agents in parallel with timeout handling.
        
        Args:
            context: Analysis context
        
        Returns:
            List of completed agent analyses
        """
        logger.info(f"Starting parallel analysis with {len(self.agents)} agents")
        
        async def analyze_with_agent(agent: BaseAgent) -> Optional[AgentAnalysis]:
            """Run single agent analysis with error handling."""
            try:
                await self._emit_event(
                    AnalysisEventType.AGENT_STARTED,
                    {"agent_id": agent.agent_id, "agent_type": agent.agent_type.value}
                )
                
                analysis = await asyncio.wait_for(
                    agent.analyze(context, self._event_callback),
                    timeout=self.config.global_timeout_seconds / len(self.agents)
                )
                
                await self._emit_event(
                    AnalysisEventType.AGENT_COMPLETED,
                    {
                        "agent_id": agent.agent_id,
                        "findings_count": len(analysis.findings),
                        "confidence": analysis.overall_confidence,
                    }
                )
                
                return analysis
                
            except asyncio.TimeoutError:
                logger.warning(f"Agent {agent.agent_id} timed out")
                return None
            except Exception as e:
                logger.error(f"Agent {agent.agent_id} failed: {e}")
                return None
        
        # Run all agents in parallel
        tasks = [
            analyze_with_agent(agent)
            for agent in self.agents.values()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        analyses = [
            r for r in results
            if isinstance(r, AgentAnalysis)
        ]
        
        logger.info(f"Parallel analysis complete: {len(analyses)} agents succeeded")
        
        return analyses
    
    async def _execute_cross_review(
        self,
        analyses: List[AgentAnalysis],
        context: AnalysisContext,
    ) -> Dict[str, List[Critique]]:
        """Have each agent critique other agents' analyses.
        
        Args:
            analyses: All agent analyses
            context: Analysis context
        
        Returns:
            Dictionary of target_agent_id -> list of critiques
        """
        logger.info("Starting cross-review phase")
        
        all_critiques: Dict[str, List[Critique]] = {a.agent_id: [] for a in analyses}
        
        # Each agent critiques each other agent
        for critic_analysis in analyses:
            critic = self.agents.get(critic_analysis.agent_id)
            if not critic:
                continue
            
            for target_analysis in analyses:
                if target_analysis.agent_id == critic_analysis.agent_id:
                    continue  # Don't self-critique
                
                try:
                    critiques = await critic.critique(target_analysis, context)
                    all_critiques[target_analysis.agent_id].extend(critiques)
                except Exception as e:
                    logger.warning(
                        f"Critique failed: {critic_analysis.agent_id} -> "
                        f"{target_analysis.agent_id}: {e}"
                    )
        
        total_critiques = sum(len(c) for c in all_critiques.values())
        logger.info(f"Cross-review complete: {total_critiques} critiques generated")
        
        return all_critiques
    
    async def _run_debate(
        self,
        analyses: List[AgentAnalysis],
        critiques: Dict[str, List[Critique]],
        context: AnalysisContext,
    ) -> Optional[DebateTimeline]:
        """Run debate rounds to resolve disagreements.
        
        Uses the DebateEngine for structured debate protocol with:
        - Debate trigger detection
        - Critique/rebuttal exchanges
        - Convergence tracking
        - Judge arbitration when needed
        
        Args:
            analyses: All agent analyses
            critiques: Critiques from cross-review
            context: Analysis context
        
        Returns:
            DebateTimeline or None if no debate needed
        """
        logger.info("Starting debate phase with DebateEngine")
        
        # Run debate through the engine
        timeline = await self.debate_engine.run_debate(
            analyses=analyses,
            critiques=critiques,
            agents=self.agents,
            context=context,
            event_callback=self._event_callback,
        )
        
        if timeline:
            logger.info(
                f"Debate complete: {len(timeline.rounds)} rounds, "
                f"convergence: {timeline.final_convergence:.2f}"
            )
        
        return timeline
    
    async def _run_debate_round(
        self,
        round_num: int,
        topic: str,
        analyses: List[AgentAnalysis],
        critiques: Dict[str, List[Critique]],
        context: AnalysisContext,
    ) -> DebateRound:
        """Run a single round of debate.
        
        Args:
            round_num: The round number
            topic: The debate topic
            analyses: All agent analyses
            critiques: All critiques
            context: Analysis context
        
        Returns:
            DebateRound with positions, critiques, and convergence
        """
        round_result = DebateRound(
            round_number=round_num,
            topic=topic,
            participants=[a.agent_id for a in analyses],
        )
        
        # Get opening positions
        for analysis in analyses:
            position = Position(
                agent_id=analysis.agent_id,
                topic=topic,
                stance=analysis.executive_summary,
                confidence=analysis.overall_confidence,
                key_arguments=analysis.key_takeaways,
            )
            round_result.opening_positions[analysis.agent_id] = position
        
        # Critiques from this round
        for agent_id, agent_critiques in critiques.items():
            for critique in agent_critiques:
                round_result.critiques.append(critique)
        
        # Calculate convergence score
        round_result.convergence_score = self._calculate_convergence(
            list(round_result.opening_positions.values())
        )
        
        round_result.timestamp_end = datetime.now()
        
        return round_result
    
    def _identify_debate_topics(
        self,
        analyses: List[AgentAnalysis],
        critiques: Dict[str, List[Critique]],
    ) -> List[str]:
        """Identify topics that warrant debate.
        
        Args:
            analyses: All agent analyses
            critiques: All critiques
        
        Returns:
            List of topic strings to debate
        """
        topics = []
        
        # Look for major critiques
        for agent_id, agent_critiques in critiques.items():
            for critique in agent_critiques:
                if critique.severity in [CritiqueSeverity.MAJOR, CritiqueSeverity.CRITICAL]:
                    topic = f"{critique.critique_type.value}: {critique.argument[:100]}"
                    if topic not in topics:
                        topics.append(topic)
        
        # Look for confidence divergence
        confidences = [a.overall_confidence for a in analyses]
        if confidences:
            divergence = max(confidences) - min(confidences)
            if divergence > 0.3:
                topics.append(f"Confidence divergence: {divergence:.2f}")
        
        return topics[:3]  # Limit to top 3 topics
    
    def _calculate_convergence(self, positions: List[Position]) -> float:
        """Calculate convergence score from positions.
        
        Args:
            positions: List of agent positions
        
        Returns:
            Convergence score 0.0 to 1.0
        """
        if not positions or len(positions) < 2:
            return 1.0
        
        # Use confidence variance as proxy for convergence
        confidences = [p.confidence for p in positions]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        
        # Convert variance to convergence (lower variance = higher convergence)
        # Variance of 0.25 (max for 0-1 range) maps to 0, variance of 0 maps to 1
        convergence = max(0.0, 1.0 - variance * 4)
        
        return convergence
    
    def _gather_evidence(
        self, analyses: List[AgentAnalysis]
    ) -> Dict[str, List[Evidence]]:
        """Gather evidence from all analyses.
        
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
    
    def _get_current_positions(
        self,
        analyses: List[AgentAnalysis],
        topic: str,
    ) -> Dict[str, Position]:
        """Get current positions from analyses.
        
        Args:
            analyses: All agent analyses
            topic: The topic being debated
        
        Returns:
            Dictionary of agent_id -> Position
        """
        positions = {}
        
        for analysis in analyses:
            positions[analysis.agent_id] = Position(
                agent_id=analysis.agent_id,
                topic=topic,
                stance=analysis.executive_summary,
                confidence=analysis.overall_confidence,
                key_arguments=analysis.key_takeaways,
            )
        
        return positions
    
    async def _build_consensus(
        self,
        analyses: List[AgentAnalysis],
        debate_timeline: Optional[DebateTimeline],
        context: AnalysisContext,
    ) -> tuple:
        """Build consensus from agent analyses and debate.
        
        Args:
            analyses: All agent analyses
            debate_timeline: Results of debate
            context: Analysis context
        
        Returns:
            Tuple of (consensus_findings, disagreements)
        """
        logger.info("Building consensus from agent findings")
        
        # Collect all findings
        all_findings: Dict[str, List[tuple]] = {}  # category -> [(finding, agent, confidence)]
        
        for analysis in analyses:
            for finding in analysis.findings:
                category = finding.category.value
                if category not in all_findings:
                    all_findings[category] = []
                all_findings[category].append((
                    finding,
                    analysis.agent_id,
                    finding.confidence * analysis.overall_confidence
                ))
        
        consensus_findings = []
        disagreements = []
        
        # Process each category
        for category, findings_list in all_findings.items():
            if len(findings_list) == 1:
                # Single finding - automatic consensus
                finding, agent, conf = findings_list[0]
                consensus_findings.append(ConsensusFinding(
                    description=finding.description,
                    category=finding.category,
                    consensus_level=ConsensusLevel.CONSENSUS,
                    weighted_confidence=conf,
                    supporting_agents=[agent],
                ))
            else:
                # Multiple findings - assess agreement
                consensus, disagreement = self._assess_agreement(
                    category, findings_list
                )
                if consensus:
                    consensus_findings.append(consensus)
                if disagreement:
                    disagreements.append(disagreement)
        
        logger.info(
            f"Consensus built: {len(consensus_findings)} agreed, "
            f"{len(disagreements)} disagreements"
        )
        
        return consensus_findings, disagreements
    
    def _assess_agreement(
        self,
        category: str,
        findings_list: List[tuple],
    ) -> tuple:
        """Assess agreement among findings in a category.
        
        Args:
            category: The finding category
            findings_list: List of (finding, agent_id, weighted_confidence)
        
        Returns:
            Tuple of (ConsensusFinding or None, Disagreement or None)
        """
        from core.agents.types import FindingCategory
        
        # Simple heuristic: if confidences are similar, there's consensus
        confidences = [f[2] for f in findings_list]
        mean_conf = sum(confidences) / len(confidences)
        variance = sum((c - mean_conf) ** 2 for c in confidences) / len(confidences)
        
        agents = [f[1] for f in findings_list]
        
        if variance < 0.04:  # Low variance = consensus
            # Pick the highest confidence finding
            best = max(findings_list, key=lambda x: x[2])
            return (
                ConsensusFinding(
                    description=best[0].description,
                    category=FindingCategory(category),
                    consensus_level=ConsensusLevel.CONSENSUS if mean_conf > 0.7 else ConsensusLevel.MAJORITY,
                    weighted_confidence=mean_conf,
                    supporting_agents=agents,
                ),
                None
            )
        else:
            # High variance = disagreement
            return (
                None,
                Disagreement(
                    topic=category,
                    agents_involved=agents,
                    positions={f[1]: f[0].description[:200] for f in findings_list},
                    reason=f"Confidence variance: {variance:.2f}",
                    severity="moderate" if variance < 0.1 else "major",
                )
            )
    
    def _calculate_confidence_bands(
        self,
        analyses: List[AgentAnalysis],
        consensus_findings: List[ConsensusFinding],
    ) -> Dict[str, ConfidenceBand]:
        """Calculate confidence bands for key metrics.
        
        Args:
            analyses: All agent analyses
            consensus_findings: Consensus findings
        
        Returns:
            Dictionary of metric_name -> ConfidenceBand
        """
        bands = {}
        
        # Calculate bands for fiscal impact
        fiscal_impacts = []
        for analysis in analyses:
            for finding in analysis.findings:
                if finding.fiscal_impact:
                    fiscal_impacts.append(finding.fiscal_impact)
        
        if fiscal_impacts:
            amounts = [fi.amount_billions for fi in fiscal_impacts]
            amounts.sort()
            n = len(amounts)
            
            bands["fiscal_impact"] = ConfidenceBand(
                metric_name="Total Fiscal Impact",
                p10=amounts[int(n * 0.1)] if n > 0 else 0,
                p50=amounts[int(n * 0.5)] if n > 0 else 0,
                p90=amounts[int(n * 0.9)] if n > 0 else 0,
                unit="billions USD",
            )
        
        return bands
    
    def _synthesize_report(
        self,
        result: SwarmAnalysis,
        context: AnalysisContext,
    ) -> ConsensusReport:
        """Synthesize the final consensus report.
        
        Args:
            result: Current swarm analysis result
            context: Analysis context
        
        Returns:
            ConsensusReport
        """
        # Determine overall consensus level
        if result.consensus_findings:
            avg_confidence = sum(
                f.weighted_confidence for f in result.consensus_findings
            ) / len(result.consensus_findings)
        else:
            avg_confidence = 0.5
        
        if avg_confidence >= 0.9:
            consensus_level = ConsensusLevel.STRONG_CONSENSUS
        elif avg_confidence >= 0.75:
            consensus_level = ConsensusLevel.CONSENSUS
        elif avg_confidence >= 0.6:
            consensus_level = ConsensusLevel.MAJORITY
        else:
            consensus_level = ConsensusLevel.DIVIDED
        
        # Generate recommendations
        primary_recommendation = self._generate_primary_recommendation(
            result.consensus_findings, result.disagreements
        )
        
        caveats = self._generate_caveats(result.disagreements)
        
        further_research = self._generate_research_needs(
            result.disagreements, result.consensus_findings
        )
        
        return ConsensusReport(
            analysis_id=result.analysis_id,
            bill_id=context.bill_id,
            bill_summary=context.bill_text[:500],
            agreed_findings=result.consensus_findings,
            confidence_level=consensus_level,
            unresolved_disputes=result.disagreements,
            minority_views=[],
            key_uncertainties=[],
            primary_recommendation=primary_recommendation,
            caveats=caveats,
            further_research_needed=further_research,
            participating_agents=list(result.agent_analyses.keys()),
        )
    
    def _generate_primary_recommendation(
        self,
        consensus_findings: List[ConsensusFinding],
        disagreements: List[Disagreement],
    ) -> str:
        """Generate the primary recommendation."""
        if not consensus_findings:
            return "Insufficient consensus for recommendation. Additional analysis needed."
        
        high_confidence = [f for f in consensus_findings if f.weighted_confidence > 0.7]
        
        if len(high_confidence) > len(consensus_findings) / 2:
            return (
                f"Strong analytical support found for {len(high_confidence)} key findings. "
                f"Policy appears well-analyzed with manageable uncertainty."
            )
        else:
            return (
                f"Moderate consensus achieved on {len(consensus_findings)} findings. "
                f"Consider addressing {len(disagreements)} areas of disagreement."
            )
    
    def _generate_caveats(self, disagreements: List[Disagreement]) -> List[str]:
        """Generate caveats based on disagreements."""
        caveats = []
        
        major = [d for d in disagreements if d.severity == "major"]
        if major:
            caveats.append(
                f"Major disagreements exist on {len(major)} topics; "
                "findings in these areas should be treated with caution"
            )
        
        if len(disagreements) > 3:
            caveats.append(
                "Multiple areas of expert disagreement suggest high policy uncertainty"
            )
        
        return caveats
    
    def _generate_research_needs(
        self,
        disagreements: List[Disagreement],
        consensus_findings: List[ConsensusFinding],
    ) -> List[str]:
        """Generate list of further research needs."""
        needs = []
        
        for disagreement in disagreements[:3]:
            needs.append(f"Resolve {disagreement.topic}: {disagreement.reason}")
        
        low_confidence = [
            f for f in consensus_findings 
            if f.weighted_confidence < 0.6
        ]
        if low_confidence:
            needs.append(
                f"Strengthen evidence for {len(low_confidence)} low-confidence findings"
            )
        
        return needs
    
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
        if self._event_callback is None:
            return
        
        event = AnalysisEvent(
            event_type=event_type,
            analysis_id=self._current_analysis_id or "",
            data=data,
        )
        
        await self._event_callback(event)
    
    def get_disagreement_map(
        self,
        analyses: List[AgentAnalysis],
        debate_timeline: Optional[DebateTimeline] = None,
    ) -> DisagreementMap:
        """Generate a disagreement map for visualization.
        
        This provides visualization data showing which agents disagree,
        on what topics, and by how much.
        
        Args:
            analyses: All agent analyses
            debate_timeline: Optional debate timeline
        
        Returns:
            DisagreementMap with visualization data
        """
        return self.debate_engine.generate_disagreement_map(
            analyses=analyses,
            timeline=debate_timeline,
        )
    
    def get_debate_performance(self) -> Dict[str, Any]:
        """Get performance metrics for agents during debate.
        
        Returns:
            Dictionary of agent_id -> performance metrics
        """
        return self.debate_engine.get_agent_performance()
