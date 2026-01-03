"""Economic Agent for the Multi-Agent Swarm system.

The Economic Agent specializes in analyzing:
- GDP impacts (growth effects, productivity changes)
- Employment effects (job creation/loss, labor market)
- Inflation impacts (price level effects)
- Interest rate implications
- Behavioral responses to policy changes

This is a Tier 1 (MVP) agent essential for macro-economic analysis.
"""

import json
import logging
import re
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
)
from core.agents.models import (
    AgentConfig,
    AgentAnalysis,
    Finding,
    FiscalImpact,
    Assumption,
    Evidence,
    Critique,
    Vote,
    Proposal,
)


logger = logging.getLogger(__name__)


class EconomicAgent(BaseAgent):
    """Specialized agent for macroeconomic impact analysis.
    
    The Economic Agent focuses on broader economic implications beyond
    direct fiscal effects, including growth, employment, and prices.
    
    Key capabilities:
    - GDP growth impact estimation
    - Employment/labor market analysis
    - Inflation and price level effects
    - Dynamic scoring considerations
    - Economic feedback loops
    """
    
    # Topics this agent has expertise in (for weighting)
    SPECIALTY_TOPICS = {
        "gdp": 2.0,
        "growth": 2.0,
        "employment": 2.0,
        "jobs": 2.0,
        "labor": 1.8,
        "inflation": 2.0,
        "prices": 1.8,
        "wages": 1.8,
        "productivity": 2.0,
        "economic": 2.0,
        "recession": 1.8,
        "interest rate": 1.8,
        "investment": 1.8,
        "trade": 1.5,
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Economic Agent.
        
        Args:
            config: Optional agent configuration. If not provided,
                   uses default economic agent settings.
        """
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.ECONOMIC,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                confidence_threshold=0.7,
                specialization_prompt=self._get_default_specialization(),
            )
        
        super().__init__(config)
    
    def _get_default_specialization(self) -> str:
        """Return default specialization prompt."""
        return """You are a macroeconomic policy expert specializing in economic impact analysis.
Your expertise includes:
- GDP and growth modeling
- Labor economics and employment effects
- Price dynamics and inflation
- Monetary policy transmission
- Dynamic scoring methodologies
- Behavioral economics responses

You approach analysis with attention to both short-term and long-term effects,
and carefully model economic feedback loops."""
    
    def _get_specialty_description(self) -> str:
        """Return description of economic agent specialty."""
        return "Macroeconomic analysis: GDP, employment, inflation, growth dynamics"
    
    def _get_system_prompt(self) -> str:
        """Return system prompt for economic analysis."""
        return f"""You are the Economic Agent in PoliSim's Multi-Agent Policy Analysis Swarm.

ROLE: You analyze the macroeconomic implications of legislation.

EXPERTISE:
- GDP impacts: growth effects, investment responses, productivity
- Employment: job creation/destruction, wage effects, labor supply
- Prices: inflation/deflation pressures, sector-specific price changes
- Interest rates: crowding out, monetary policy interactions
- Dynamic effects: behavioral responses, second-order impacts

ANALYSIS STANDARDS:
1. Distinguish short-run (<3 years) vs. long-run (>3 years) effects
2. Consider both demand-side and supply-side channels
3. Quantify with point estimates and uncertainty ranges
4. Account for economic cycle timing (recession vs. expansion)
5. Note key assumptions about behavioral elasticities

OUTPUT FORMAT:
Provide structured findings with:
- Category (gdp/employment/inflation/interest_rates/productivity)
- Description of the impact
- Magnitude (%, basis points, or jobs, with confidence range)
- Time horizon (short-run, medium-run, long-run)
- Confidence level (0-1 scale)
- Key assumptions made
- Economic mechanisms/channels

{self.config.specialization_prompt}"""
    
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return analysis prompt for the given context."""
        
        # Extract relevant mechanisms
        economic_mechanisms = context.get_mechanism("economic") or []
        tax_mechanisms = context.get_mechanism("tax") or []
        spending_mechanisms = context.get_mechanism("spending") or []
        
        # Get baseline data
        baseline_gdp = context.get_baseline("gdp_billions") or "N/A"
        baseline_unemployment = context.get_baseline("unemployment_rate") or "N/A"
        baseline_inflation = context.get_baseline("inflation_rate") or "N/A"
        
        # Include economic projections if available
        econ_proj_summary = ""
        if context.economic_projections:
            econ_proj_summary = f"""
PRE-COMPUTED ECONOMIC PROJECTIONS (from PoliSim models):
{json.dumps(context.economic_projections, indent=2, default=str)[:2000]}
"""
        
        return f"""Analyze the macroeconomic implications of the following legislation.

BILL ID: {context.bill_id}
SCENARIO: {context.scenario}
PROJECTION YEARS: {context.projection_years}

BILL TEXT:
{context.bill_text[:8000]}

EXTRACTED MECHANISMS:
Economic Mechanisms: {json.dumps(economic_mechanisms, indent=2, default=str)[:1500]}
Tax Mechanisms: {json.dumps(tax_mechanisms, indent=2, default=str)[:1500]}
Spending Mechanisms: {json.dumps(spending_mechanisms, indent=2, default=str)[:1500]}

BASELINE ECONOMIC DATA:
- GDP: ${baseline_gdp}B
- Unemployment Rate: {baseline_unemployment}%
- Inflation Rate: {baseline_inflation}%
{econ_proj_summary}

INSTRUCTIONS:
1. Assess GDP growth impacts (short-run and long-run)
2. Estimate employment effects (job creation/loss, wages)
3. Evaluate inflation implications
4. Consider investment and productivity effects
5. Identify behavioral responses and feedback loops
6. Quantify uncertainty and note key assumptions

Provide your analysis in structured JSON format with findings array."""
    
    def _get_critique_prompt(self, analysis: AgentAnalysis) -> str:
        """Return critique prompt for another agent's analysis."""
        
        findings_summary = "\n".join([
            f"- {f.category.value}: {f.description} "
            f"(confidence: {f.confidence}, magnitude: {f.impact_magnitude.value})"
            for f in analysis.findings[:10]
        ])
        
        return f"""Review the following analysis from a {analysis.agent_type.value} agent 
and provide critiques from an economic perspective.

AGENT: {analysis.agent_id}
TYPE: {analysis.agent_type.value}
OVERALL CONFIDENCE: {analysis.overall_confidence}

FINDINGS:
{findings_summary}

ASSUMPTIONS USED:
{json.dumps([a.__dict__ for a in analysis.assumptions_used[:5]], indent=2, default=str)}

YOUR TASK:
1. Identify any economic implications the agent may have missed
2. Challenge assumptions about behavioral responses
3. Point out any growth/employment estimates that seem unrealistic
4. Note if dynamic economic effects are properly considered
5. Suggest refinements to improve economic accuracy

Provide critiques in structured JSON format."""
    
    async def _parse_analysis_response(
        self,
        response: str,
        context: AnalysisContext
    ) -> AgentAnalysis:
        """Parse LLM response into structured AgentAnalysis."""
        
        analysis = AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            model_used=self.config.model,
        )
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                for f_data in data.get("findings", []):
                    finding = self._parse_finding(f_data)
                    if finding:
                        analysis.findings.append(finding)
                
                for a_data in data.get("assumptions", []):
                    assumption = Assumption(
                        category=a_data.get("category", "economic"),
                        description=a_data.get("description", ""),
                        value=a_data.get("value"),
                        source=a_data.get("source"),
                        confidence=float(a_data.get("confidence", 0.8)),
                    )
                    analysis.assumptions_used.append(assumption)
                
                analysis.executive_summary = data.get("executive_summary", "")
                analysis.key_takeaways = data.get("key_takeaways", [])
                analysis.uncertainty_areas = data.get("uncertainty_areas", [])
                analysis.overall_confidence = float(data.get("overall_confidence", 0.7))
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            analysis.findings.append(Finding(
                category=FindingCategory.GDP,
                description=response[:500],
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.5,
            ))
            analysis.overall_confidence = 0.5
        
        return analysis
    
    def _parse_finding(self, f_data: Dict[str, Any]) -> Optional[Finding]:
        """Parse a finding dictionary into a Finding object."""
        try:
            category_str = f_data.get("category", "gdp").lower()
            category_map = {
                "gdp": FindingCategory.GDP,
                "growth": FindingCategory.GDP,
                "employment": FindingCategory.EMPLOYMENT,
                "jobs": FindingCategory.EMPLOYMENT,
                "labor": FindingCategory.EMPLOYMENT,
                "inflation": FindingCategory.INFLATION,
                "prices": FindingCategory.INFLATION,
                "interest": FindingCategory.INTEREST_RATES,
                "interest_rates": FindingCategory.INTEREST_RATES,
                "productivity": FindingCategory.PRODUCTIVITY,
            }
            category = category_map.get(category_str, FindingCategory.GDP)
            
            magnitude_str = f_data.get("impact_magnitude", "medium").lower()
            magnitude_map = {
                "negligible": ImpactMagnitude.NEGLIGIBLE,
                "low": ImpactMagnitude.LOW,
                "medium": ImpactMagnitude.MEDIUM,
                "high": ImpactMagnitude.HIGH,
                "transformative": ImpactMagnitude.TRANSFORMATIVE,
            }
            magnitude = magnitude_map.get(magnitude_str, ImpactMagnitude.MEDIUM)
            
            return Finding(
                category=category,
                description=f_data.get("description", ""),
                impact_magnitude=magnitude,
                confidence=float(f_data.get("confidence", 0.7)),
                time_horizon=f_data.get("time_horizon", "10-year"),
                affected_populations=f_data.get("affected_populations", []),
                assumptions_used=f_data.get("assumptions_used", []),
                uncertainty_factors=f_data.get("uncertainty_factors", []),
            )
        
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse finding: {e}")
            return None
    
    async def _parse_critique_response(
        self,
        response: str,
        target_analysis: AgentAnalysis
    ) -> List[Critique]:
        """Parse LLM response into structured Critiques."""
        
        critiques = []
        
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                
                for c_data in data:
                    critique_type_map = {
                        "methodology": CritiqueType.METHODOLOGY,
                        "assumption": CritiqueType.ASSUMPTION,
                        "evidence": CritiqueType.EVIDENCE,
                        "logic": CritiqueType.LOGIC,
                    }
                    
                    severity_map = {
                        "minor": CritiqueSeverity.MINOR,
                        "moderate": CritiqueSeverity.MODERATE,
                        "major": CritiqueSeverity.MAJOR,
                        "critical": CritiqueSeverity.CRITICAL,
                    }
                    
                    critique = Critique(
                        critic_id=self.agent_id,
                        target_id=target_analysis.agent_id,
                        target_finding_id=c_data.get("target_finding_id"),
                        critique_type=critique_type_map.get(
                            c_data.get("critique_type", "methodology").lower(),
                            CritiqueType.METHODOLOGY
                        ),
                        severity=severity_map.get(
                            c_data.get("severity", "moderate").lower(),
                            CritiqueSeverity.MODERATE
                        ),
                        argument=c_data.get("argument", ""),
                        suggested_revision=c_data.get("suggested_revision"),
                    )
                    critiques.append(critique)
        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse critique response: {e}")
        
        return critiques
    
    # =========================================================================
    # Public API Implementation
    # =========================================================================
    
    async def analyze(
        self,
        context: AnalysisContext,
        event_callback: Optional[Callable[[Any], Awaitable[None]]] = None
    ) -> AgentAnalysis:
        """Analyze a bill for economic impacts.
        
        Args:
            context: Analysis context with bill text and data
            event_callback: Optional callback for streaming thoughts
        
        Returns:
            AgentAnalysis with economic findings
        """
        self._event_callback = event_callback
        self._current_analysis_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Economic Agent {self.agent_id} starting analysis of {context.bill_id}")
        
        await self.emit_thought(
            ThoughtType.OBSERVATION,
            f"Beginning economic analysis of bill {context.bill_id}",
        )
        
        analysis = await self._perform_analysis(context)
        analysis.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        await self.emit_thought(
            ThoughtType.CONCLUSION,
            f"Analysis complete. Found {len(analysis.findings)} economic findings.",
            confidence=analysis.overall_confidence,
        )
        
        logger.info(
            f"Economic Agent completed analysis: {len(analysis.findings)} findings, "
            f"confidence {analysis.overall_confidence:.2f}"
        )
        
        return analysis
    
    async def _perform_analysis(self, context: AnalysisContext) -> AgentAnalysis:
        """Perform the actual economic analysis."""
        
        analysis = AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            model_used=self.config.model,
        )
        
        # Analyze tax mechanisms for economic effects
        tax_mechanisms = context.get_mechanism("tax") or []
        for tm in tax_mechanisms:
            await self.emit_thought(
                ThoughtType.HYPOTHESIS,
                f"Assessing economic effects of: {tm.get('name', 'tax provision')}",
            )
            
            # Estimate GDP effect from tax changes
            amount = tm.get("amount", 0)
            gdp_multiplier = self._estimate_gdp_multiplier(tm)
            
            if gdp_multiplier != 0:
                analysis.findings.append(Finding(
                    category=FindingCategory.GDP,
                    description=f"GDP effect from {tm.get('name', 'tax provision')}: "
                               f"Tax change affects growth through {self._get_channel(tm)}",
                    impact_magnitude=self._estimate_gdp_magnitude(amount, gdp_multiplier),
                    confidence=0.65,
                    time_horizon="5-year",
                    assumptions_used=["Standard tax multiplier assumptions"],
                ))
        
        # Analyze spending mechanisms for economic effects
        spending_mechanisms = context.get_mechanism("spending") or []
        for sm in spending_mechanisms:
            await self.emit_thought(
                ThoughtType.CALCULATION,
                f"Calculating employment effects of: {sm.get('name', 'spending program')}",
            )
            
            # Estimate employment effect
            jobs_estimate = self._estimate_jobs_created(sm)
            if jobs_estimate:
                analysis.findings.append(Finding(
                    category=FindingCategory.EMPLOYMENT,
                    description=f"Employment effect from {sm.get('name', 'spending')}: "
                               f"Estimated {jobs_estimate:,} jobs affected",
                    impact_magnitude=self._estimate_jobs_magnitude(jobs_estimate),
                    confidence=0.60,
                    time_horizon="3-year",
                    affected_populations=["Labor force"],
                ))
        
        # Use pre-computed economic projections if available
        if context.economic_projections:
            await self.emit_thought(
                ThoughtType.REFERENCE,
                "Incorporating PoliSim economic projection results",
            )
            
            gdp_change = context.economic_projections.get("gdp_change_percent")
            if gdp_change:
                analysis.findings.append(Finding(
                    category=FindingCategory.GDP,
                    description=f"Overall GDP impact: {gdp_change:+.2f}% change from baseline",
                    impact_magnitude=self._percent_to_magnitude(gdp_change),
                    confidence=0.75,
                    time_horizon="10-year",
                ))
        
        # Standard economic assumptions
        analysis.assumptions_used = [
            Assumption(
                category="economic",
                description="Rational expectations and efficient markets",
                confidence=0.70,
            ),
            Assumption(
                category="labor",
                description="Unemployment at natural rate baseline",
                source="CBO Economic Outlook",
                confidence=0.75,
            ),
            Assumption(
                category="behavioral",
                description="Standard labor supply elasticities",
                value="0.1-0.4 range",
                confidence=0.65,
            ),
        ]
        
        # Calculate overall confidence
        if analysis.findings:
            analysis.overall_confidence = sum(f.confidence for f in analysis.findings) / len(analysis.findings)
        else:
            analysis.overall_confidence = 0.5
        
        analysis.executive_summary = self._generate_executive_summary(analysis)
        analysis.key_takeaways = self._generate_key_takeaways(analysis)
        
        return analysis
    
    def _estimate_gdp_multiplier(self, mechanism: Dict) -> float:
        """Estimate GDP multiplier for a tax mechanism."""
        mech_type = mechanism.get("type", "").lower()
        
        # Standard multiplier estimates
        if "investment" in mech_type or "capital" in mech_type:
            return 0.8  # Higher multiplier for investment incentives
        elif "consumption" in mech_type or "income" in mech_type:
            return 0.5  # Moderate multiplier for income taxes
        elif "corporate" in mech_type:
            return 0.3  # Lower short-run multiplier for corporate
        
        return 0.4  # Default moderate multiplier
    
    def _estimate_gdp_magnitude(self, amount: Any, multiplier: float) -> ImpactMagnitude:
        """Estimate GDP impact magnitude."""
        try:
            amt = abs(float(amount) if amount else 0)
            gdp_effect = amt * multiplier / 25000  # Rough % of GDP (assuming ~$25T GDP)
            
            if gdp_effect < 0.01:
                return ImpactMagnitude.NEGLIGIBLE
            elif gdp_effect < 0.1:
                return ImpactMagnitude.LOW
            elif gdp_effect < 0.5:
                return ImpactMagnitude.MEDIUM
            elif gdp_effect < 1.0:
                return ImpactMagnitude.HIGH
            else:
                return ImpactMagnitude.TRANSFORMATIVE
        except (TypeError, ValueError):
            return ImpactMagnitude.MEDIUM
    
    def _get_channel(self, mechanism: Dict) -> str:
        """Get the economic channel for a mechanism."""
        mech_type = mechanism.get("type", "").lower()
        
        if "investment" in mech_type:
            return "investment incentives"
        elif "consumption" in mech_type:
            return "household spending"
        elif "labor" in mech_type:
            return "labor supply effects"
        
        return "aggregate demand"
    
    def _estimate_jobs_created(self, mechanism: Dict) -> Optional[int]:
        """Estimate jobs created/affected by a spending mechanism."""
        try:
            amount = float(mechanism.get("amount", 0))
            if amount == 0:
                return None
            
            # Rough estimate: $100K per job (varies by sector)
            cost_per_job = mechanism.get("cost_per_job", 100000)
            jobs = int(amount * 1e9 / cost_per_job)
            
            return jobs if jobs > 100 else None
        except (TypeError, ValueError):
            return None
    
    def _estimate_jobs_magnitude(self, jobs: int) -> ImpactMagnitude:
        """Estimate impact magnitude from job numbers."""
        if jobs < 10000:
            return ImpactMagnitude.NEGLIGIBLE
        elif jobs < 100000:
            return ImpactMagnitude.LOW
        elif jobs < 500000:
            return ImpactMagnitude.MEDIUM
        elif jobs < 2000000:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _percent_to_magnitude(self, percent: float) -> ImpactMagnitude:
        """Convert percentage change to impact magnitude."""
        abs_pct = abs(percent)
        
        if abs_pct < 0.1:
            return ImpactMagnitude.NEGLIGIBLE
        elif abs_pct < 0.5:
            return ImpactMagnitude.LOW
        elif abs_pct < 1.0:
            return ImpactMagnitude.MEDIUM
        elif abs_pct < 3.0:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _generate_executive_summary(self, analysis: AgentAnalysis) -> str:
        """Generate executive summary."""
        gdp_findings = [f for f in analysis.findings if f.category == FindingCategory.GDP]
        employment_findings = [f for f in analysis.findings if f.category == FindingCategory.EMPLOYMENT]
        
        return (
            f"Economic Analysis Summary: Identified {len(gdp_findings)} GDP impacts "
            f"and {len(employment_findings)} employment effects. "
            f"Overall economic confidence: {analysis.overall_confidence:.0%}"
        )
    
    def _generate_key_takeaways(self, analysis: AgentAnalysis) -> List[str]:
        """Generate key takeaways."""
        takeaways = []
        
        high_impact = [
            f for f in analysis.findings 
            if f.impact_magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.TRANSFORMATIVE]
        ]
        
        if high_impact:
            takeaways.append(f"Identified {len(high_impact)} significant economic effects")
        
        return takeaways
    
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Critique another agent's analysis from an economic perspective."""
        critiques = []
        
        # Check for missing economic considerations
        has_economic = any(
            f.category in [FindingCategory.GDP, FindingCategory.EMPLOYMENT,
                          FindingCategory.INFLATION, FindingCategory.PRODUCTIVITY]
            for f in other_analysis.findings
        )
        
        if not has_economic and other_analysis.agent_type != AgentType.ECONOMIC:
            critiques.append(Critique(
                critic_id=self.agent_id,
                target_id=other_analysis.agent_id,
                critique_type=CritiqueType.SCOPE,
                severity=CritiqueSeverity.MODERATE,
                argument="Analysis does not consider macroeconomic feedback effects",
                suggested_revision="Include GDP, employment, and inflation implications",
            ))
        
        # Check for unrealistic behavioral assumptions
        for assumption in other_analysis.assumptions_used:
            if "elasticity" in assumption.description.lower():
                try:
                    if assumption.value and float(assumption.value) > 1.0:
                        critiques.append(Critique(
                            critic_id=self.agent_id,
                            target_id=other_analysis.agent_id,
                            critique_type=CritiqueType.ASSUMPTION,
                            severity=CritiqueSeverity.MODERATE,
                            argument=f"Elasticity assumption ({assumption.value}) exceeds typical empirical estimates",
                            suggested_revision="Consider using elasticities in 0.1-0.5 range",
                        ))
                except (TypeError, ValueError):
                    pass
        
        return critiques
    
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Vote on proposals from an economic perspective."""
        votes = []
        
        for proposal in proposals:
            vote_type = VoteType.NEUTRAL
            confidence = 0.6
            reasoning = "Neutral pending economic impact assessment"
            
            desc_lower = proposal.description.lower()
            
            if "growth" in desc_lower and "increase" in desc_lower:
                vote_type = VoteType.SUPPORT
                confidence = 0.70
                reasoning = "Proposal supports economic growth"
            
            elif "job" in desc_lower and ("creat" in desc_lower or "employ" in desc_lower):
                vote_type = VoteType.SUPPORT
                confidence = 0.70
                reasoning = "Proposal has positive employment effects"
            
            elif "recession" in desc_lower or "contraction" in desc_lower:
                vote_type = VoteType.OPPOSE
                confidence = 0.65
                reasoning = "Proposal may have contractionary effects"
            
            votes.append(Vote(
                voter_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                support=vote_type,
                confidence=confidence,
                reasoning=reasoning,
            ))
        
        return votes
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Get economic agent's weight for a topic."""
        topic_lower = topic.lower()
        
        for keyword, weight in self.SPECIALTY_TOPICS.items():
            if keyword in topic_lower:
                return weight
        
        return 1.0
