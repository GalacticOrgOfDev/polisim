"""Social Security Agent for the Multi-Agent Swarm system.

The Social Security Agent specializes in analyzing:
- OASI (Old-Age and Survivors Insurance) impacts
- DI (Disability Insurance) impacts
- Trust fund solvency effects
- Benefit changes (retirement age, COLA, formulas)
- Payroll tax changes
- Demographic effects on the system

This is a Tier 1 (MVP) agent essential for retirement policy analysis.
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


class SocialSecurityAgent(BaseAgent):
    """Specialized agent for Social Security policy analysis.
    
    The Social Security Agent focuses on retirement and disability
    insurance programs, trust fund solvency, and reform proposals.
    
    Key capabilities:
    - Trust fund (OASI, DI) projection modeling
    - Benefit formula analysis
    - Retirement age and COLA effects
    - Payroll tax impact analysis
    - 75-year actuarial projections
    """
    
    # Topics this agent has expertise in (for weighting)
    SPECIALTY_TOPICS = {
        "social security": 2.0,
        "retirement": 2.0,
        "oasi": 2.0,
        "disability": 1.8,
        "trust fund": 2.0,
        "benefit": 1.8,
        "payroll tax": 2.0,
        "cola": 1.8,
        "retirement age": 2.0,
        "pia": 1.8,
        "bend point": 1.8,
        "actuarial": 1.8,
        "solvency": 2.0,
        "ssa": 1.8,
        "retiree": 1.8,
        "survivor": 1.8,
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Social Security Agent.
        
        Args:
            config: Optional agent configuration. If not provided,
                   uses default social security agent settings.
        """
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.SOCIAL_SECURITY,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                confidence_threshold=0.7,
                specialization_prompt=self._get_default_specialization(),
            )
        
        super().__init__(config)
    
    def _get_default_specialization(self) -> str:
        """Return default specialization prompt."""
        return """You are a Social Security policy expert specializing in retirement system analysis.
Your expertise includes:
- OASDI program structure and financing
- Trust fund accounting and solvency
- Benefit formulas (PIA, bend points, replacement rates)
- Retirement age and COLA policies
- Payroll tax mechanics
- 75-year actuarial projections
- Demographic trends affecting Social Security

You are familiar with SSA Trustees Report methodologies and PoliSim's SS models."""
    
    def _get_specialty_description(self) -> str:
        """Return description of social security agent specialty."""
        return "Social Security: OASI/DI, trust funds, benefits, retirement policy"
    
    def _get_system_prompt(self) -> str:
        """Return system prompt for social security analysis."""
        return f"""You are the Social Security Agent in PoliSim's Multi-Agent Policy Analysis Swarm.

ROLE: You analyze Social Security and retirement policy implications.

EXPERTISE:
- Trust Funds: OASI, DI solvency dates, reserve ratios
- Benefits: PIA formula, bend points, replacement rates, COLA
- Financing: Payroll taxes, taxable maximum, contribution rates
- Demographics: Beneficiary ratios, life expectancy, labor force
- Reforms: Retirement age, benefit cuts, tax increases, means-testing

ANALYSIS STANDARDS:
1. Use 75-year actuarial projections as standard horizon
2. Express impacts in terms of actuarial balance (% of taxable payroll)
3. Distinguish OASI from DI effects when relevant
4. Consider distributional effects across generations and income levels
5. Reference SSA Trustees assumptions where applicable

OUTPUT FORMAT:
Provide structured findings with:
- Category (trust_fund/benefits/eligibility/revenue)
- Description of the impact
- Magnitude (years of solvency, % of taxable payroll, benefit change %)
- Affected populations (current retirees, future retirees, workers)
- Confidence level (0-1 scale)
- Key assumptions made

{self.config.specialization_prompt}"""
    
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return analysis prompt for the given context."""
        
        # Extract relevant mechanisms
        ss_mechanisms = context.get_mechanism("social_security") or []
        benefit_mechanisms = context.get_mechanism("benefit") or []
        retirement_mechanisms = context.get_mechanism("retirement") or []
        tax_mechanisms = context.get_mechanism("tax") or []
        
        # Get baseline data
        baseline_oasi_depletion = context.get_baseline("oasi_depletion_year") or "N/A"
        baseline_di_depletion = context.get_baseline("di_depletion_year") or "N/A"
        baseline_payroll_rate = context.get_baseline("payroll_tax_rate") or "12.4%"
        
        # Include SS projections if available
        ss_proj_summary = ""
        if context.ss_projections:
            ss_proj_summary = f"""
PRE-COMPUTED SOCIAL SECURITY PROJECTIONS (from PoliSim models):
{json.dumps(context.ss_projections, indent=2, default=str)[:2000]}
"""
        
        return f"""Analyze the Social Security implications of the following legislation.

BILL ID: {context.bill_id}
SCENARIO: {context.scenario}
PROJECTION YEARS: {context.projection_years}

BILL TEXT:
{context.bill_text[:8000]}

EXTRACTED MECHANISMS:
Social Security Mechanisms: {json.dumps(ss_mechanisms, indent=2, default=str)[:1500]}
Benefit Mechanisms: {json.dumps(benefit_mechanisms, indent=2, default=str)[:1500]}
Retirement Mechanisms: {json.dumps(retirement_mechanisms, indent=2, default=str)[:1500]}
Tax Mechanisms (payroll): {json.dumps(tax_mechanisms, indent=2, default=str)[:1500]}

BASELINE SOCIAL SECURITY DATA:
- OASI Trust Fund Depletion Year: {baseline_oasi_depletion}
- DI Trust Fund Depletion Year: {baseline_di_depletion}
- Combined Payroll Tax Rate: {baseline_payroll_rate}
{ss_proj_summary}

INSTRUCTIONS:
1. Assess trust fund solvency impacts (OASI and DI separately if relevant)
2. Analyze benefit changes (amounts, eligibility, formulas)
3. Evaluate payroll tax or other financing changes
4. Consider generational and distributional effects
5. Project 75-year actuarial impact when possible
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
and provide critiques from a Social Security perspective.

AGENT: {analysis.agent_id}
TYPE: {analysis.agent_type.value}
OVERALL CONFIDENCE: {analysis.overall_confidence}

FINDINGS:
{findings_summary}

YOUR TASK:
1. Identify any Social Security implications the agent may have missed
2. Challenge assumptions about demographic or behavioral responses
3. Point out any trust fund or benefit estimates that seem unrealistic
4. Note if generational equity issues are properly considered
5. Suggest refinements to improve Social Security accuracy

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
                        category=a_data.get("category", "social_security"),
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
                category=FindingCategory.TRUST_FUND,
                description=response[:500],
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.5,
            ))
            analysis.overall_confidence = 0.5
        
        return analysis
    
    def _parse_finding(self, f_data: Dict[str, Any]) -> Optional[Finding]:
        """Parse a finding dictionary into a Finding object."""
        try:
            category_str = f_data.get("category", "trust_fund").lower()
            category_map = {
                "trust_fund": FindingCategory.TRUST_FUND,
                "trust fund": FindingCategory.TRUST_FUND,
                "oasi": FindingCategory.TRUST_FUND,
                "di": FindingCategory.TRUST_FUND,
                "benefit": FindingCategory.BENEFITS,
                "benefits": FindingCategory.BENEFITS,
                "eligibility": FindingCategory.ELIGIBILITY,
                "retirement": FindingCategory.ELIGIBILITY,
                "revenue": FindingCategory.REVENUE,
                "payroll": FindingCategory.REVENUE,
                "tax": FindingCategory.REVENUE,
                "distribution": FindingCategory.DISTRIBUTION,
            }
            category = category_map.get(category_str, FindingCategory.TRUST_FUND)
            
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
                time_horizon=f_data.get("time_horizon", "75-year"),
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
        """Analyze a bill for Social Security impacts.
        
        Args:
            context: Analysis context with bill text and data
            event_callback: Optional callback for streaming thoughts
        
        Returns:
            AgentAnalysis with Social Security findings
        """
        self._event_callback = event_callback
        self._current_analysis_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Social Security Agent {self.agent_id} starting analysis of {context.bill_id}")
        
        await self.emit_thought(
            ThoughtType.OBSERVATION,
            f"Beginning Social Security analysis of bill {context.bill_id}",
        )
        
        analysis = await self._perform_analysis(context)
        analysis.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        await self.emit_thought(
            ThoughtType.CONCLUSION,
            f"Analysis complete. Found {len(analysis.findings)} Social Security findings.",
            confidence=analysis.overall_confidence,
        )
        
        logger.info(
            f"Social Security Agent completed analysis: {len(analysis.findings)} findings, "
            f"confidence {analysis.overall_confidence:.2f}"
        )
        
        return analysis
    
    async def _perform_analysis(self, context: AnalysisContext) -> AgentAnalysis:
        """Perform the actual Social Security analysis."""
        
        analysis = AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            model_used=self.config.model,
        )
        
        # Analyze Social Security mechanisms
        ss_mechanisms = context.get_mechanism("social_security") or []
        for ssm in ss_mechanisms:
            await self.emit_thought(
                ThoughtType.OBSERVATION,
                f"Analyzing Social Security provision: {ssm.get('name', 'Unknown')}",
            )
            
            # Determine impact type
            category = self._determine_category(ssm)
            
            analysis.findings.append(Finding(
                category=category,
                description=f"{ssm.get('name', 'SS provision')}: {ssm.get('description', '')}",
                impact_magnitude=self._estimate_magnitude(ssm),
                confidence=0.70,
                time_horizon="75-year",
                affected_populations=ssm.get("affected_populations", 
                    ["Current retirees", "Future retirees", "Workers"]),
            ))
        
        # Analyze benefit mechanisms
        benefit_mechanisms = context.get_mechanism("benefit") or []
        for bm in benefit_mechanisms:
            # Check if it's SS-related
            if self._is_ss_related(bm):
                await self.emit_thought(
                    ThoughtType.CALCULATION,
                    f"Calculating benefit impact: {bm.get('name', 'benefit change')}",
                )
                
                analysis.findings.append(Finding(
                    category=FindingCategory.BENEFITS,
                    description=f"Benefit change: {bm.get('description', 'Unknown')}",
                    impact_magnitude=self._estimate_benefit_magnitude(bm),
                    confidence=0.70,
                    time_horizon="75-year",
                    affected_populations=bm.get("affected_populations", ["Beneficiaries"]),
                ))
        
        # Analyze payroll tax changes
        tax_mechanisms = context.get_mechanism("tax") or []
        for tm in tax_mechanisms:
            if self._is_payroll_related(tm):
                await self.emit_thought(
                    ThoughtType.CALCULATION,
                    f"Analyzing payroll tax impact: {tm.get('name', 'tax change')}",
                )
                
                solvency_impact = self._estimate_solvency_impact(tm)
                
                analysis.findings.append(Finding(
                    category=FindingCategory.TRUST_FUND,
                    description=f"Payroll tax change affects trust fund: {tm.get('description', '')}. "
                               f"Estimated solvency impact: {solvency_impact:+d} years",
                    impact_magnitude=self._years_to_magnitude(solvency_impact),
                    confidence=0.65,
                    time_horizon="75-year",
                ))
        
        # Use pre-computed SS projections if available
        if context.ss_projections:
            await self.emit_thought(
                ThoughtType.REFERENCE,
                "Incorporating PoliSim Social Security projection results",
            )
            
            oasi_change = context.ss_projections.get("oasi_depletion_year_change")
            if oasi_change:
                analysis.findings.append(Finding(
                    category=FindingCategory.TRUST_FUND,
                    description=f"OASI Trust Fund depletion date: {oasi_change:+d} years from baseline",
                    impact_magnitude=self._years_to_magnitude(oasi_change),
                    confidence=0.75,
                    time_horizon="75-year",
                    affected_populations=["All Social Security beneficiaries"],
                ))
            
            actuarial_balance = context.ss_projections.get("actuarial_balance_change")
            if actuarial_balance:
                analysis.findings.append(Finding(
                    category=FindingCategory.TRUST_FUND,
                    description=f"75-year actuarial balance change: {actuarial_balance:+.2f}% of taxable payroll",
                    impact_magnitude=self._actuarial_to_magnitude(actuarial_balance),
                    confidence=0.75,
                    time_horizon="75-year",
                ))
        
        # Standard SS assumptions
        analysis.assumptions_used = [
            Assumption(
                category="demographic",
                description="Intermediate demographic assumptions from SSA Trustees",
                source="SSA Trustees Report",
                confidence=0.75,
            ),
            Assumption(
                category="economic",
                description="Intermediate economic assumptions (productivity, real wage growth)",
                source="SSA Trustees Report",
                confidence=0.70,
            ),
            Assumption(
                category="behavioral",
                description="Retirement claiming behavior follows historical patterns",
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
        
        if "trust" in mech_type or "solvency" in mech_type or "fund" in mech_type:
            return FindingCategory.TRUST_FUND
        elif "benefit" in mech_type or "pia" in mech_type or "cola" in mech_type:
            return FindingCategory.BENEFITS
        elif "eligibility" in mech_type or "retirement age" in mech_type:
            return FindingCategory.ELIGIBILITY
        elif "tax" in mech_type or "payroll" in mech_type:
            return FindingCategory.REVENUE
        
        return FindingCategory.TRUST_FUND
    
    def _is_ss_related(self, mechanism: Dict) -> bool:
        """Check if a mechanism is Social Security related."""
        keywords = ["social security", "oasi", "retirement", "survivor", "disability",
                   "payroll", "fica", "benefit", "cola", "pia"]
        
        text = (mechanism.get("name", "") + " " + mechanism.get("description", "")).lower()
        return any(kw in text for kw in keywords)
    
    def _is_payroll_related(self, mechanism: Dict) -> bool:
        """Check if a tax mechanism is payroll tax related."""
        keywords = ["payroll", "fica", "social security tax", "oasdi"]
        
        text = (mechanism.get("name", "") + " " + mechanism.get("description", "")).lower()
        return any(kw in text for kw in keywords)
    
    def _estimate_magnitude(self, mechanism: Dict) -> ImpactMagnitude:
        """Estimate impact magnitude from a mechanism."""
        # Check for solvency impact
        solvency_years = mechanism.get("solvency_impact_years", 0)
        if solvency_years:
            return self._years_to_magnitude(solvency_years)
        
        # Check for benefit change percentage
        benefit_change = mechanism.get("benefit_change_percent", 0)
        if benefit_change:
            return self._percent_to_magnitude(benefit_change)
        
        return ImpactMagnitude.MEDIUM
    
    def _estimate_benefit_magnitude(self, mechanism: Dict) -> ImpactMagnitude:
        """Estimate magnitude from benefit change."""
        try:
            change = float(mechanism.get("change_percent", 0))
            return self._percent_to_magnitude(change)
        except (TypeError, ValueError):
            return ImpactMagnitude.MEDIUM
    
    def _estimate_solvency_impact(self, mechanism: Dict) -> int:
        """Estimate solvency impact in years from a tax change."""
        try:
            # Rough rule: 0.1% payroll tax ≈ 1 year solvency
            rate_change = float(mechanism.get("rate_change", 0))
            return int(rate_change * 10)
        except (TypeError, ValueError):
            return 0
    
    def _years_to_magnitude(self, years: int) -> ImpactMagnitude:
        """Convert years of solvency change to magnitude."""
        abs_years = abs(years)
        if abs_years < 1:
            return ImpactMagnitude.NEGLIGIBLE
        elif abs_years < 3:
            return ImpactMagnitude.LOW
        elif abs_years < 8:
            return ImpactMagnitude.MEDIUM
        elif abs_years < 15:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _percent_to_magnitude(self, percent: float) -> ImpactMagnitude:
        """Convert percentage change to magnitude."""
        abs_pct = abs(percent)
        if abs_pct < 1:
            return ImpactMagnitude.NEGLIGIBLE
        elif abs_pct < 5:
            return ImpactMagnitude.LOW
        elif abs_pct < 15:
            return ImpactMagnitude.MEDIUM
        elif abs_pct < 30:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _actuarial_to_magnitude(self, balance: float) -> ImpactMagnitude:
        """Convert actuarial balance change to magnitude."""
        abs_bal = abs(balance)
        if abs_bal < 0.1:
            return ImpactMagnitude.NEGLIGIBLE
        elif abs_bal < 0.3:
            return ImpactMagnitude.LOW
        elif abs_bal < 0.8:
            return ImpactMagnitude.MEDIUM
        elif abs_bal < 1.5:
            return ImpactMagnitude.HIGH
        else:
            return ImpactMagnitude.TRANSFORMATIVE
    
    def _generate_executive_summary(self, analysis: AgentAnalysis) -> str:
        """Generate executive summary."""
        trust_findings = [f for f in analysis.findings if f.category == FindingCategory.TRUST_FUND]
        benefit_findings = [f for f in analysis.findings if f.category == FindingCategory.BENEFITS]
        
        return (
            f"Social Security Analysis Summary: Identified {len(trust_findings)} trust fund impacts "
            f"and {len(benefit_findings)} benefit-related findings. "
            f"Overall SS confidence: {analysis.overall_confidence:.0%}"
        )
    
    def _generate_key_takeaways(self, analysis: AgentAnalysis) -> List[str]:
        """Generate key takeaways."""
        takeaways = []
        
        high_impact = [
            f for f in analysis.findings 
            if f.impact_magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.TRANSFORMATIVE]
        ]
        
        if high_impact:
            takeaways.append(f"Identified {len(high_impact)} significant Social Security effects")
        
        trust_fund = [f for f in analysis.findings if f.category == FindingCategory.TRUST_FUND]
        if trust_fund:
            takeaways.append("Policy affects OASI/DI trust fund solvency")
        
        return takeaways
    
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Critique another agent's analysis from a Social Security perspective."""
        critiques = []
        
        # Check for missing SS considerations
        has_ss = any(
            f.category in [FindingCategory.TRUST_FUND, FindingCategory.BENEFITS]
            and "social security" in f.description.lower()
            for f in other_analysis.findings
        )
        
        if not has_ss and other_analysis.agent_type != AgentType.SOCIAL_SECURITY:
            # Check if bill text suggests SS content
            bill_text_lower = context.bill_text.lower()
            ss_keywords = ["social security", "retirement", "oasi", "payroll tax", "fica"]
            
            if any(kw in bill_text_lower for kw in ss_keywords):
                critiques.append(Critique(
                    critic_id=self.agent_id,
                    target_id=other_analysis.agent_id,
                    critique_type=CritiqueType.SCOPE,
                    severity=CritiqueSeverity.MODERATE,
                    argument="Bill contains Social Security provisions not addressed in analysis",
                    suggested_revision="Include trust fund, benefit, and payroll tax implications",
                ))
        
        # Check for inadequate time horizon
        for finding in other_analysis.findings:
            if finding.category in [FindingCategory.TRUST_FUND, FindingCategory.BENEFITS]:
                if "75-year" not in finding.time_horizon.lower() and "long-term" not in finding.time_horizon.lower():
                    critiques.append(Critique(
                        critic_id=self.agent_id,
                        target_id=other_analysis.agent_id,
                        target_finding_id=finding.finding_id,
                        critique_type=CritiqueType.METHODOLOGY,
                        severity=CritiqueSeverity.MINOR,
                        argument="Social Security analysis should use 75-year actuarial horizon",
                        suggested_revision="Extend projection to standard 75-year window",
                    ))
        
        return critiques
    
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Vote on proposals from a Social Security perspective."""
        votes = []
        
        for proposal in proposals:
            vote_type = VoteType.NEUTRAL
            confidence = 0.6
            reasoning = "Neutral pending Social Security impact assessment"
            
            desc_lower = proposal.description.lower()
            
            if "solvency" in desc_lower and ("extend" in desc_lower or "improve" in desc_lower):
                vote_type = VoteType.SUPPORT
                confidence = 0.75
                reasoning = "Proposal improves trust fund solvency"
            
            elif "cut" in desc_lower and "benefit" in desc_lower:
                vote_type = VoteType.OPPOSE
                confidence = 0.65
                reasoning = "Proposal reduces Social Security benefits"
            
            elif "strengthen" in desc_lower and "social security" in desc_lower:
                vote_type = VoteType.SUPPORT
                confidence = 0.70
                reasoning = "Proposal strengthens Social Security system"
            
            votes.append(Vote(
                voter_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                support=vote_type,
                confidence=confidence,
                reasoning=reasoning,
            ))
        
        return votes
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Get Social Security agent's weight for a topic."""
        topic_lower = topic.lower()
        
        for keyword, weight in self.SPECIALTY_TOPICS.items():
            if keyword in topic_lower:
                return weight
        
        return 1.0
