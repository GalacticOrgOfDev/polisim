"""Healthcare Agent for the Multi-Agent Swarm system.

The Healthcare Agent specializes in analyzing:
- Coverage effects (insurance coverage changes, eligibility)
- Cost impacts (healthcare spending, premiums, out-of-pocket)
- Quality implications (care quality, access)
- Medicare/Medicaid impacts
- Healthcare delivery system changes

This is a Tier 1 (MVP) agent essential for healthcare policy analysis.
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


class HealthcareAgent(BaseAgent):
    """Specialized agent for healthcare policy analysis.
    
    The Healthcare Agent focuses on health-related implications of
    legislation, including coverage, costs, and quality of care.
    
    Key capabilities:
    - Insurance coverage modeling
    - Healthcare cost projections
    - Medicare/Medicaid impact analysis
    - Provider payment effects
    - Health outcomes estimation
    """
    
    # Topics this agent has expertise in (for weighting)
    SPECIALTY_TOPICS = {
        "healthcare": 2.0,
        "health": 2.0,
        "medicare": 2.0,
        "medicaid": 2.0,
        "insurance": 2.0,
        "coverage": 2.0,
        "hospital": 1.8,
        "physician": 1.8,
        "prescription": 1.8,
        "drug": 1.8,
        "premium": 1.8,
        "patient": 1.8,
        "provider": 1.8,
        "aca": 1.8,
        "chip": 1.8,
        "uninsured": 2.0,
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Healthcare Agent.
        
        Args:
            config: Optional agent configuration. If not provided,
                   uses default healthcare agent settings.
        """
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.HEALTHCARE,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                confidence_threshold=0.7,
                specialization_prompt=self._get_default_specialization(),
            )
        
        super().__init__(config)
    
    def _get_default_specialization(self) -> str:
        """Return default specialization prompt."""
        return """You are a healthcare policy expert specializing in health system analysis.
Your expertise includes:
- Medicare and Medicaid programs
- Health insurance markets (ACA, employer-sponsored)
- Healthcare cost drivers and projections
- Provider payment systems
- Pharmaceutical policy
- Health outcomes and quality measurement

You are familiar with CMS actuarial methods and PoliSim's healthcare models."""
    
    def _get_specialty_description(self) -> str:
        """Return description of healthcare agent specialty."""
        return "Healthcare policy: coverage, costs, Medicare/Medicaid, quality"
    
    def _get_system_prompt(self) -> str:
        """Return system prompt for healthcare analysis."""
        return f"""You are the Healthcare Agent in PoliSim's Multi-Agent Policy Analysis Swarm.

ROLE: You analyze the healthcare implications of legislation.

EXPERTISE:
- Coverage: Insurance status changes, eligibility, enrollment
- Costs: Spending (federal/state/private), premiums, out-of-pocket
- Medicare: Parts A/B/C/D, trust funds, provider payments
- Medicaid: Federal/state spending, eligibility, managed care
- Quality: Access to care, health outcomes, disparities
- Market: Insurer behavior, provider responses, drug pricing

ANALYSIS STANDARDS:
1. Quantify coverage effects (number of people affected)
2. Project costs over 10-year and long-term horizons
3. Distinguish federal vs. state vs. private spending
4. Consider behavioral responses (take-up rates, provider participation)
5. Note uncertainty in actuarial projections

OUTPUT FORMAT:
Provide structured findings with:
- Category (coverage/cost/quality/access)
- Description of the impact
- Magnitude (people affected, $ amounts)
- Affected populations (elderly, low-income, uninsured, etc.)
- Confidence level (0-1 scale)
- Key assumptions made

{self.config.specialization_prompt}"""
    
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return analysis prompt for the given context."""
        
        # Extract relevant mechanisms
        healthcare_mechanisms = context.get_mechanism("healthcare") or []
        coverage_mechanisms = context.get_mechanism("coverage") or []
        eligibility_mechanisms = context.get_mechanism("eligibility") or []
        
        # Get baseline data
        baseline_uninsured = context.get_baseline("uninsured_millions") or "N/A"
        baseline_medicare = context.get_baseline("medicare_spending_billions") or "N/A"
        baseline_medicaid = context.get_baseline("medicaid_spending_billions") or "N/A"
        
        # Include healthcare projections if available
        health_proj_summary = ""
        if context.healthcare_projections:
            health_proj_summary = f"""
PRE-COMPUTED HEALTHCARE PROJECTIONS (from PoliSim models):
{json.dumps(context.healthcare_projections, indent=2, default=str)[:2000]}
"""
        
        return f"""Analyze the healthcare implications of the following legislation.

BILL ID: {context.bill_id}
SCENARIO: {context.scenario}
PROJECTION YEARS: {context.projection_years}

BILL TEXT:
{context.bill_text[:8000]}

EXTRACTED MECHANISMS:
Healthcare Mechanisms: {json.dumps(healthcare_mechanisms, indent=2, default=str)[:1500]}
Coverage Mechanisms: {json.dumps(coverage_mechanisms, indent=2, default=str)[:1500]}
Eligibility Mechanisms: {json.dumps(eligibility_mechanisms, indent=2, default=str)[:1500]}

BASELINE HEALTHCARE DATA:
- Uninsured Population: {baseline_uninsured}M
- Medicare Spending: ${baseline_medicare}B
- Medicaid Spending: ${baseline_medicaid}B
{health_proj_summary}

INSTRUCTIONS:
1. Assess coverage changes (who gains/loses coverage)
2. Project federal healthcare spending effects
3. Estimate impacts on Medicare and Medicaid specifically
4. Evaluate effects on premiums and out-of-pocket costs
5. Consider quality and access implications
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
and provide critiques from a healthcare perspective.

AGENT: {analysis.agent_id}
TYPE: {analysis.agent_type.value}
OVERALL CONFIDENCE: {analysis.overall_confidence}

FINDINGS:
{findings_summary}

YOUR TASK:
1. Identify any healthcare implications the agent may have missed
2. Challenge assumptions about coverage take-up or provider behavior
3. Point out any healthcare cost estimates that seem unrealistic
4. Note if effects on vulnerable populations are properly considered
5. Suggest refinements to improve healthcare accuracy

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
                        category=a_data.get("category", "healthcare"),
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
                category=FindingCategory.COVERAGE,
                description=response[:500],
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.5,
            ))
            analysis.overall_confidence = 0.5
        
        return analysis
    
    def _parse_finding(self, f_data: Dict[str, Any]) -> Optional[Finding]:
        """Parse a finding dictionary into a Finding object."""
        try:
            category_str = f_data.get("category", "coverage").lower()
            category_map = {
                "coverage": FindingCategory.COVERAGE,
                "insurance": FindingCategory.COVERAGE,
                "cost": FindingCategory.COST,
                "spending": FindingCategory.COST,
                "quality": FindingCategory.QUALITY,
                "access": FindingCategory.ACCESS,
                "trust_fund": FindingCategory.TRUST_FUND,
                "medicare": FindingCategory.TRUST_FUND,
                "eligibility": FindingCategory.ELIGIBILITY,
            }
            category = category_map.get(category_str, FindingCategory.COVERAGE)
            
            magnitude_str = f_data.get("impact_magnitude", "medium").lower()
            magnitude_map = {
                "negligible": ImpactMagnitude.NEGLIGIBLE,
                "low": ImpactMagnitude.LOW,
                "medium": ImpactMagnitude.MEDIUM,
                "high": ImpactMagnitude.HIGH,
                "transformative": ImpactMagnitude.TRANSFORMATIVE,
            }
            magnitude = magnitude_map.get(magnitude_str, ImpactMagnitude.MEDIUM)
            
            # Parse fiscal impact if present
            fiscal_impact = None
            if "fiscal_impact" in f_data:
                fi = f_data["fiscal_impact"]
                fiscal_impact = FiscalImpact(
                    amount_billions=float(fi.get("amount_billions", 0)),
                    time_period=fi.get("time_period", "10-year"),
                    confidence_low=float(fi.get("confidence_low", 0)),
                    confidence_mid=float(fi.get("confidence_mid", 0)),
                    confidence_high=float(fi.get("confidence_high", 0)),
                    is_revenue=fi.get("is_revenue", False),
                )
            
            return Finding(
                category=category,
                description=f_data.get("description", ""),
                impact_magnitude=magnitude,
                confidence=float(f_data.get("confidence", 0.7)),
                time_horizon=f_data.get("time_horizon", "10-year"),
                affected_populations=f_data.get("affected_populations", []),
                fiscal_impact=fiscal_impact,
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
                    critique = Critique(
                        critic_id=self.agent_id,
                        target_id=target_analysis.agent_id,
                        target_finding_id=c_data.get("target_finding_id"),
                        critique_type=CritiqueType(c_data.get("critique_type", "methodology")),
                        severity=CritiqueSeverity(c_data.get("severity", "moderate")),
                        argument=c_data.get("argument", ""),
                        suggested_revision=c_data.get("suggested_revision"),
                    )
                    critiques.append(critique)
        
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
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
        """Analyze a bill for healthcare impacts.
        
        Args:
            context: Analysis context with bill text and data
            event_callback: Optional callback for streaming thoughts
        
        Returns:
            AgentAnalysis with healthcare findings
        """
        self._event_callback = event_callback
        self._current_analysis_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Healthcare Agent {self.agent_id} starting analysis of {context.bill_id}")
        
        await self.emit_thought(
            ThoughtType.OBSERVATION,
            f"Beginning healthcare analysis of bill {context.bill_id}",
        )
        
        analysis = await self._perform_analysis(context)
        analysis.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        await self.emit_thought(
            ThoughtType.CONCLUSION,
            f"Analysis complete. Found {len(analysis.findings)} healthcare findings.",
            confidence=analysis.overall_confidence,
        )
        
        logger.info(
            f"Healthcare Agent completed analysis: {len(analysis.findings)} findings, "
            f"confidence {analysis.overall_confidence:.2f}"
        )
        
        return analysis
    
    async def _perform_analysis(self, context: AnalysisContext) -> AgentAnalysis:
        """Perform the actual healthcare analysis."""
        
        analysis = AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            model_used=self.config.model,
        )
        
        # Analyze healthcare mechanisms
        healthcare_mechanisms = context.get_mechanism("healthcare") or []
        for hm in healthcare_mechanisms:
            await self.emit_thought(
                ThoughtType.OBSERVATION,
                f"Analyzing healthcare provision: {hm.get('name', 'Unknown')}",
            )
            
            # Determine category from mechanism
            category = self._determine_category(hm)
            
            analysis.findings.append(Finding(
                category=category,
                description=f"{hm.get('name', 'Healthcare provision')}: {hm.get('description', '')}",
                impact_magnitude=self._estimate_magnitude(hm),
                confidence=0.70,
                time_horizon=hm.get("time_horizon", "10-year"),
                affected_populations=hm.get("affected_populations", ["Healthcare beneficiaries"]),
                fiscal_impact=self._create_fiscal_impact(hm),
            ))
        
        # Analyze coverage mechanisms
        coverage_mechanisms = context.get_mechanism("coverage") or []
        for cm in coverage_mechanisms:
            await self.emit_thought(
                ThoughtType.CALCULATION,
                f"Estimating coverage impact: {cm.get('name', 'coverage change')}",
            )
            
            coverage_change = cm.get("coverage_change_millions", 0)
            
            analysis.findings.append(Finding(
                category=FindingCategory.COVERAGE,
                description=f"Coverage change: {cm.get('description', 'Unknown')}. "
                           f"Affects approximately {coverage_change}M people.",
                impact_magnitude=self._estimate_coverage_magnitude(coverage_change),
                confidence=0.65,
                time_horizon=cm.get("time_horizon", "5-year"),
                affected_populations=cm.get("affected_populations", ["Uninsured", "Underinsured"]),
            ))
        
        # Analyze eligibility mechanisms
        eligibility_mechanisms = context.get_mechanism("eligibility") or []
        for em in eligibility_mechanisms:
            analysis.findings.append(Finding(
                category=FindingCategory.ELIGIBILITY,
                description=f"Eligibility change: {em.get('description', 'Unknown')}",
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.70,
                time_horizon=em.get("time_horizon", "immediate"),
                affected_populations=em.get("affected_populations", []),
            ))
        
        # Use pre-computed healthcare projections if available
        if context.healthcare_projections:
            await self.emit_thought(
                ThoughtType.REFERENCE,
                "Incorporating PoliSim healthcare projection results",
            )
            
            # Medicare trust fund finding
            hi_change = context.healthcare_projections.get("hi_trust_fund_years_change")
            if hi_change:
                analysis.findings.append(Finding(
                    category=FindingCategory.TRUST_FUND,
                    description=f"Medicare HI Trust Fund solvency: {hi_change:+d} years",
                    impact_magnitude=self._estimate_trust_fund_magnitude(hi_change),
                    confidence=0.75,
                    time_horizon="long-term",
                ))
        
        # Standard healthcare assumptions
        analysis.assumptions_used = [
            Assumption(
                category="coverage",
                description="Standard take-up rate assumptions for new coverage",
                value="70-85% eligible enrollment",
                source="CBO coverage modeling",
                confidence=0.70,
            ),
            Assumption(
                category="cost",
                description="Healthcare cost growth follows current trends",
                source="CMS National Health Expenditure projections",
                confidence=0.75,
            ),
            Assumption(
                category="behavior",
                description="Provider participation rates maintained",
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
    
    def _determine_category(self, mechanism: Dict) -> FindingCategory:
        """Determine the appropriate category for a mechanism."""
        mech_type = mechanism.get("type", "").lower()
        description = mechanism.get("description", "").lower()
        
        if "coverage" in mech_type or "insurance" in mech_type:
            return FindingCategory.COVERAGE
        elif "cost" in mech_type or "spending" in mech_type or "payment" in mech_type:
            return FindingCategory.COST
        elif "quality" in mech_type or "outcome" in mech_type:
            return FindingCategory.QUALITY
        elif "access" in mech_type or "provider" in mech_type:
            return FindingCategory.ACCESS
        elif "eligibility" in mech_type:
            return FindingCategory.ELIGIBILITY
        elif "medicare" in description or "trust fund" in description:
            return FindingCategory.TRUST_FUND
        
        return FindingCategory.COVERAGE
    
    def _estimate_magnitude(self, mechanism: Dict) -> ImpactMagnitude:
        """Estimate impact magnitude from a mechanism."""
        # Check for coverage impact
        coverage = mechanism.get("coverage_change_millions", 0)
        if coverage:
            return self._estimate_coverage_magnitude(coverage)
        
        # Check for spending impact
        amount = mechanism.get("amount", 0)
        if amount:
            try:
                amt = abs(float(amount))
                if amt < 5:
                    return ImpactMagnitude.LOW
                elif amt < 50:
                    return ImpactMagnitude.MEDIUM
                elif amt < 200:
                    return ImpactMagnitude.HIGH
                else:
                    return ImpactMagnitude.TRANSFORMATIVE
            except (TypeError, ValueError):
                pass
        
        return ImpactMagnitude.MEDIUM
    
    def _estimate_coverage_magnitude(self, coverage_millions: Any) -> ImpactMagnitude:
        """Estimate magnitude from coverage change."""
        try:
            cov = abs(float(coverage_millions))
            if cov < 0.5:
                return ImpactMagnitude.NEGLIGIBLE
            elif cov < 2:
                return ImpactMagnitude.LOW
            elif cov < 10:
                return ImpactMagnitude.MEDIUM
            elif cov < 30:
                return ImpactMagnitude.HIGH
            else:
                return ImpactMagnitude.TRANSFORMATIVE
        except (TypeError, ValueError):
            return ImpactMagnitude.MEDIUM
    
    def _estimate_trust_fund_magnitude(self, years_change: int) -> ImpactMagnitude:
        """Estimate magnitude from trust fund solvency change."""
        abs_years = abs(years_change)
        if abs_years < 1:
            return ImpactMagnitude.NEGLIGIBLE
        elif abs_years < 3:
            return ImpactMagnitude.LOW
        elif abs_years < 7:
            return ImpactMagnitude.MEDIUM
        elif abs_years < 15:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _create_fiscal_impact(self, mechanism: Dict) -> Optional[FiscalImpact]:
        """Create a FiscalImpact from a mechanism."""
        amount = mechanism.get("amount")
        if amount is None:
            return None
        
        try:
            amt = float(amount)
            return FiscalImpact(
                amount_billions=amt,
                time_period=mechanism.get("time_period", "10-year"),
                confidence_low=amt * 0.75,
                confidence_mid=amt,
                confidence_high=amt * 1.35,  # Healthcare has higher uncertainty
                is_revenue=mechanism.get("is_revenue", False),
            )
        except (TypeError, ValueError):
            return None
    
    def _generate_executive_summary(self, analysis: AgentAnalysis) -> str:
        """Generate executive summary."""
        coverage_findings = [f for f in analysis.findings if f.category == FindingCategory.COVERAGE]
        cost_findings = [f for f in analysis.findings if f.category == FindingCategory.COST]
        
        return (
            f"Healthcare Analysis Summary: Identified {len(coverage_findings)} coverage impacts "
            f"and {len(cost_findings)} cost-related findings. "
            f"Overall healthcare confidence: {analysis.overall_confidence:.0%}"
        )
    
    def _generate_key_takeaways(self, analysis: AgentAnalysis) -> List[str]:
        """Generate key takeaways."""
        takeaways = []
        
        high_impact = [
            f for f in analysis.findings 
            if f.impact_magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.TRANSFORMATIVE]
        ]
        
        if high_impact:
            takeaways.append(f"Identified {len(high_impact)} significant healthcare effects")
        
        trust_fund = [f for f in analysis.findings if f.category == FindingCategory.TRUST_FUND]
        if trust_fund:
            takeaways.append("Policy affects Medicare/Medicaid trust fund solvency")
        
        return takeaways
    
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Critique another agent's analysis from a healthcare perspective."""
        critiques = []
        
        # Check for missing healthcare considerations
        has_healthcare = any(
            f.category in [FindingCategory.COVERAGE, FindingCategory.COST,
                          FindingCategory.QUALITY, FindingCategory.ACCESS]
            for f in other_analysis.findings
        )
        
        if not has_healthcare and other_analysis.agent_type != AgentType.HEALTHCARE:
            # Check if bill text suggests healthcare content
            bill_text_lower = context.bill_text.lower()
            healthcare_keywords = ["medicare", "medicaid", "health", "hospital", "physician", "insurance"]
            
            if any(kw in bill_text_lower for kw in healthcare_keywords):
                critiques.append(Critique(
                    critic_id=self.agent_id,
                    target_id=other_analysis.agent_id,
                    critique_type=CritiqueType.SCOPE,
                    severity=CritiqueSeverity.MODERATE,
                    argument="Bill contains healthcare provisions not addressed in analysis",
                    suggested_revision="Include coverage, cost, and quality implications",
                ))
        
        # Check for missing affected populations
        for finding in other_analysis.findings:
            if finding.category in [FindingCategory.COVERAGE, FindingCategory.ELIGIBILITY]:
                if not finding.affected_populations:
                    critiques.append(Critique(
                        critic_id=self.agent_id,
                        target_id=other_analysis.agent_id,
                        target_finding_id=finding.finding_id,
                        critique_type=CritiqueType.SCOPE,
                        severity=CritiqueSeverity.MINOR,
                        argument="Finding does not specify affected populations",
                        suggested_revision="Identify specific populations (elderly, low-income, etc.)",
                    ))
        
        return critiques
    
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Vote on proposals from a healthcare perspective."""
        votes = []
        
        for proposal in proposals:
            vote_type = VoteType.NEUTRAL
            confidence = 0.6
            reasoning = "Neutral pending healthcare impact assessment"
            
            desc_lower = proposal.description.lower()
            
            if "coverage" in desc_lower and "expand" in desc_lower:
                vote_type = VoteType.SUPPORT
                confidence = 0.75
                reasoning = "Proposal expands healthcare coverage"
            
            elif "reduce" in desc_lower and ("medicare" in desc_lower or "medicaid" in desc_lower):
                vote_type = VoteType.OPPOSE
                confidence = 0.70
                reasoning = "Proposal may reduce healthcare benefits"
            
            elif "quality" in desc_lower and "improve" in desc_lower:
                vote_type = VoteType.SUPPORT
                confidence = 0.70
                reasoning = "Proposal improves healthcare quality"
            
            votes.append(Vote(
                voter_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                support=vote_type,
                confidence=confidence,
                reasoning=reasoning,
            ))
        
        return votes
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Get healthcare agent's weight for a topic."""
        topic_lower = topic.lower()
        
        for keyword, weight in self.SPECIALTY_TOPICS.items():
            if keyword in topic_lower:
                return weight
        
        return 1.0
