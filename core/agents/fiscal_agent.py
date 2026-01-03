"""Fiscal Agent for the Multi-Agent Swarm system.

The Fiscal Agent specializes in analyzing:
- Revenue impacts (tax changes, new revenue sources)
- Spending changes (new programs, funding changes)
- Debt implications (deficit changes, debt trajectory)
- Trust fund effects (Social Security, Medicare trust funds)

This is a Tier 1 (MVP) agent essential for core policy analysis.
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


class FiscalAgent(BaseAgent):
    """Specialized agent for fiscal impact analysis.
    
    The Fiscal Agent focuses on the budgetary implications of legislation,
    including revenue, spending, debt, and trust fund impacts.
    
    Key capabilities:
    - 10-year budget window analysis
    - Revenue scoring (static and dynamic)
    - Spending projections
    - Debt trajectory modeling
    - Trust fund solvency analysis
    """
    
    # Topics this agent has expertise in (for weighting)
    SPECIALTY_TOPICS = {
        "revenue": 2.0,
        "tax": 2.0,
        "spending": 2.0,
        "budget": 2.0,
        "debt": 2.0,
        "deficit": 2.0,
        "trust fund": 1.8,
        "fiscal": 2.0,
        "appropriation": 1.8,
        "funding": 1.8,
        "cost": 1.5,
    }
    
    def __init__(self, config: Optional[AgentConfig] = None):
        """Initialize the Fiscal Agent.
        
        Args:
            config: Optional agent configuration. If not provided,
                   uses default fiscal agent settings.
        """
        if config is None:
            config = AgentConfig(
                agent_type=AgentType.FISCAL,
                model="claude-sonnet-4-20250514",
                temperature=0.3,
                confidence_threshold=0.7,
                specialization_prompt=self._get_default_specialization(),
            )
        
        super().__init__(config)
    
    def _get_default_specialization(self) -> str:
        """Return default specialization prompt."""
        return """You are a fiscal policy expert specializing in federal budget analysis.
Your expertise includes:
- CBO scoring methodologies
- Tax revenue estimation
- Federal spending programs
- Debt dynamics and interest costs
- Trust fund accounting (Social Security, Medicare)

You approach analysis systematically, always citing baseline data and 
quantifying uncertainty ranges. You are familiar with PoliSim's fiscal
models and can interpret their outputs."""
    
    def _get_specialty_description(self) -> str:
        """Return description of fiscal agent specialty."""
        return "Federal budget analysis: revenue, spending, debt, and trust funds"
    
    def _get_system_prompt(self) -> str:
        """Return system prompt for fiscal analysis."""
        return f"""You are the Fiscal Agent in PoliSim's Multi-Agent Policy Analysis Swarm.

ROLE: You analyze the fiscal (budgetary) implications of legislation.

EXPERTISE:
- Federal revenue: income taxes, payroll taxes, corporate taxes, excise taxes
- Federal spending: mandatory programs, discretionary spending, interest
- National debt: deficit projections, debt-to-GDP ratios, interest costs
- Trust funds: Social Security (OASI, DI), Medicare (HI, SMI)

ANALYSIS STANDARDS:
1. Use 10-year budget window as primary timeframe
2. Distinguish static vs. dynamic scoring assumptions
3. Quantify uncertainty with P10/P50/P90 confidence bands
4. Cite CBO, SSA, or other official baselines
5. Flag any revenue/spending estimates outside normal ranges

OUTPUT FORMAT:
Provide structured findings with:
- Category (revenue/spending/debt/trust_fund)
- Description of the impact
- Magnitude (billions USD, with confidence range)
- Time horizon (when impacts occur)
- Confidence level (0-1 scale)
- Key assumptions made
- Supporting evidence

{self.config.specialization_prompt}"""
    
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return analysis prompt for the given context."""
        
        # Extract relevant mechanisms
        funding_mechanisms = context.get_mechanism("funding") or []
        tax_mechanisms = context.get_mechanism("tax") or []
        spending_mechanisms = context.get_mechanism("spending") or []
        
        # Get baseline data
        baseline_revenue = context.get_baseline("total_revenue_billions") or "N/A"
        baseline_spending = context.get_baseline("total_spending_billions") or "N/A"
        baseline_debt = context.get_baseline("debt_held_by_public_billions") or "N/A"
        
        # Include fiscal projections if available
        fiscal_proj_summary = ""
        if context.fiscal_projections:
            fiscal_proj_summary = f"""
PRE-COMPUTED FISCAL PROJECTIONS (from PoliSim models):
{json.dumps(context.fiscal_projections, indent=2, default=str)[:2000]}
"""
        
        return f"""Analyze the fiscal implications of the following legislation.

BILL ID: {context.bill_id}
SCENARIO: {context.scenario}
PROJECTION YEARS: {context.projection_years}

BILL TEXT:
{context.bill_text[:8000]}

EXTRACTED MECHANISMS:
Funding Mechanisms: {json.dumps(funding_mechanisms, indent=2, default=str)[:2000]}
Tax Mechanisms: {json.dumps(tax_mechanisms, indent=2, default=str)[:2000]}
Spending Mechanisms: {json.dumps(spending_mechanisms, indent=2, default=str)[:2000]}

BASELINE DATA (Current Law):
- Total Federal Revenue: ${baseline_revenue}B
- Total Federal Spending: ${baseline_spending}B
- Debt Held by Public: ${baseline_debt}B
{fiscal_proj_summary}

INSTRUCTIONS:
1. Identify all revenue impacts (taxes, fees, other receipts)
2. Identify all spending impacts (new programs, funding changes)
3. Calculate net deficit impact by year
4. Assess debt trajectory implications
5. Evaluate trust fund impacts if applicable
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
and provide critiques from a fiscal perspective.

AGENT: {analysis.agent_id}
TYPE: {analysis.agent_type.value}
OVERALL CONFIDENCE: {analysis.overall_confidence}

FINDINGS:
{findings_summary}

ASSUMPTIONS USED:
{json.dumps([a.__dict__ for a in analysis.assumptions_used[:5]], indent=2, default=str)}

YOUR TASK:
1. Identify any fiscal implications the agent may have missed
2. Challenge assumptions that affect fiscal estimates
3. Point out any revenue/spending estimates that seem unrealistic
4. Note methodology concerns from a fiscal standpoint
5. Suggest refinements to improve fiscal accuracy

Provide critiques in structured JSON format with critique_type, severity, 
argument, and suggested_revision for each."""
    
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
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                
                # Parse findings
                for f_data in data.get("findings", []):
                    finding = self._parse_finding(f_data)
                    if finding:
                        analysis.findings.append(finding)
                
                # Parse assumptions
                for a_data in data.get("assumptions", []):
                    assumption = Assumption(
                        category=a_data.get("category", "general"),
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
            # Create a single finding from the raw response
            analysis.findings.append(Finding(
                category=FindingCategory.OTHER,
                description=response[:500],
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.5,
            ))
            analysis.overall_confidence = 0.5
        
        return analysis
    
    def _parse_finding(self, f_data: Dict[str, Any]) -> Optional[Finding]:
        """Parse a finding dictionary into a Finding object."""
        try:
            # Map category string to enum
            category_str = f_data.get("category", "other").lower()
            category_map = {
                "revenue": FindingCategory.REVENUE,
                "spending": FindingCategory.SPENDING,
                "debt": FindingCategory.DEBT,
                "deficit": FindingCategory.DEFICIT,
                "trust_fund": FindingCategory.TRUST_FUND,
                "trust fund": FindingCategory.TRUST_FUND,
            }
            category = category_map.get(category_str, FindingCategory.OTHER)
            
            # Map magnitude string to enum
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
                    is_recurring=fi.get("is_recurring", True),
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
                    critique_type_str = c_data.get("critique_type", "methodology").lower()
                    critique_type_map = {
                        "methodology": CritiqueType.METHODOLOGY,
                        "assumption": CritiqueType.ASSUMPTION,
                        "evidence": CritiqueType.EVIDENCE,
                        "logic": CritiqueType.LOGIC,
                        "scope": CritiqueType.SCOPE,
                        "magnitude": CritiqueType.MAGNITUDE,
                        "timing": CritiqueType.TIMING,
                        "uncertainty": CritiqueType.UNCERTAINTY,
                    }
                    
                    severity_str = c_data.get("severity", "moderate").lower()
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
                        critique_type=critique_type_map.get(critique_type_str, CritiqueType.METHODOLOGY),
                        severity=severity_map.get(severity_str, CritiqueSeverity.MODERATE),
                        argument=c_data.get("argument", ""),
                        suggested_revision=c_data.get("suggested_revision"),
                        supporting_evidence=c_data.get("supporting_evidence", []),
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
        """Analyze a bill for fiscal impacts.
        
        Args:
            context: Analysis context with bill text and data
            event_callback: Optional callback for streaming thoughts
        
        Returns:
            AgentAnalysis with fiscal findings
        """
        self._event_callback = event_callback
        self._current_analysis_id = str(uuid4())
        start_time = datetime.now()
        
        logger.info(f"Fiscal Agent {self.agent_id} starting analysis of {context.bill_id}")
        
        # Emit initial thought
        await self.emit_thought(
            ThoughtType.OBSERVATION,
            f"Beginning fiscal analysis of bill {context.bill_id}",
        )
        
        # Try LLM-based analysis first, fall back to rule-based
        try:
            analysis = await self._perform_llm_analysis(context)
        except Exception as e:
            logger.warning(f"LLM analysis failed, using rule-based: {e}")
            analysis = await self._perform_rule_based_analysis(context)
        
        # Record execution time
        analysis.execution_time_seconds = (datetime.now() - start_time).total_seconds()
        
        await self.emit_thought(
            ThoughtType.CONCLUSION,
            f"Analysis complete. Found {len(analysis.findings)} fiscal findings.",
            confidence=analysis.overall_confidence,
        )
        
        logger.info(
            f"Fiscal Agent completed analysis: {len(analysis.findings)} findings, "
            f"confidence {analysis.overall_confidence:.2f}"
        )
        
        return analysis
    
    async def _perform_llm_analysis(self, context: AnalysisContext) -> AgentAnalysis:
        """Perform LLM-based fiscal analysis.
        
        Calls Claude to perform deeper analysis of the bill text.
        """
        await self.emit_thought(
            ThoughtType.REASONING,
            "Using AI-powered analysis for comprehensive fiscal assessment",
        )
        
        # Call LLM
        response = await self.call_llm_for_analysis(context)
        
        # Parse response
        analysis = await self._parse_analysis_response(response, context)
        
        return analysis
    
    async def _perform_rule_based_analysis(self, context: AnalysisContext) -> AgentAnalysis:
        """Perform rule-based fiscal analysis.
        
        Falls back to extracted mechanisms when LLM is unavailable.
        """
        analysis = AgentAnalysis(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            bill_id=context.bill_id,
            model_used=self.config.model,
        )
        
        # Analyze funding mechanisms
        funding_mechanisms = context.get_mechanism("funding") or []
        for fm in funding_mechanisms:
            await self.emit_thought(
                ThoughtType.OBSERVATION,
                f"Identified funding mechanism: {fm.get('name', 'Unknown')}",
            )
            
            finding = Finding(
                category=FindingCategory.SPENDING,
                description=f"Funding mechanism: {fm.get('description', fm.get('name', 'Unknown'))}",
                impact_magnitude=self._estimate_magnitude(fm.get("amount")),
                confidence=0.75,
                time_horizon=fm.get("time_horizon", "10-year"),
                fiscal_impact=self._create_fiscal_impact(fm, is_revenue=False),
            )
            analysis.findings.append(finding)
        
        # Analyze tax mechanisms
        tax_mechanisms = context.get_mechanism("tax") or []
        for tm in tax_mechanisms:
            await self.emit_thought(
                ThoughtType.CALCULATION,
                f"Calculating revenue impact of tax provision: {tm.get('name', 'Unknown')}",
            )
            
            finding = Finding(
                category=FindingCategory.REVENUE,
                description=f"Tax provision: {tm.get('description', tm.get('name', 'Unknown'))}",
                impact_magnitude=self._estimate_magnitude(tm.get("amount")),
                confidence=0.70,
                time_horizon=tm.get("time_horizon", "10-year"),
                fiscal_impact=self._create_fiscal_impact(tm, is_revenue=True),
            )
            analysis.findings.append(finding)
        
        # Analyze spending mechanisms
        spending_mechanisms = context.get_mechanism("spending") or []
        for sm in spending_mechanisms:
            finding = Finding(
                category=FindingCategory.SPENDING,
                description=f"Spending provision: {sm.get('description', sm.get('name', 'Unknown'))}",
                impact_magnitude=self._estimate_magnitude(sm.get("amount")),
                confidence=0.75,
                time_horizon=sm.get("time_horizon", "10-year"),
                fiscal_impact=self._create_fiscal_impact(sm, is_revenue=False),
            )
            analysis.findings.append(finding)
        
        # Use pre-computed fiscal projections if available
        if context.fiscal_projections:
            await self.emit_thought(
                ThoughtType.REFERENCE,
                "Incorporating PoliSim fiscal projection results",
            )
            
            # Add debt trajectory finding
            debt_change = context.fiscal_projections.get("debt_change_10yr")
            if debt_change:
                analysis.findings.append(Finding(
                    category=FindingCategory.DEBT,
                    description=f"10-year debt trajectory change: ${debt_change}B",
                    impact_magnitude=self._estimate_magnitude(debt_change),
                    confidence=0.80,
                    time_horizon="10-year",
                ))
        
        # Calculate overall confidence
        if analysis.findings:
            analysis.overall_confidence = sum(f.confidence for f in analysis.findings) / len(analysis.findings)
        else:
            analysis.overall_confidence = 0.5
        
        # Add standard assumptions
        analysis.assumptions_used = [
            Assumption(
                category="economic",
                description="GDP growth follows CBO baseline projections",
                source="CBO Economic Outlook",
                confidence=0.75,
            ),
            Assumption(
                category="fiscal",
                description="Current law baseline for revenue projections",
                source="CBO Budget Baseline",
                confidence=0.85,
            ),
        ]
        
        analysis.executive_summary = self._generate_executive_summary(analysis)
        analysis.key_takeaways = self._generate_key_takeaways(analysis)
        
        return analysis
    
    def _estimate_magnitude(self, amount: Any) -> ImpactMagnitude:
        """Estimate impact magnitude from an amount."""
        try:
            amt = float(amount) if amount else 0
            abs_amt = abs(amt)
            
            if abs_amt < 1:  # < $1B
                return ImpactMagnitude.NEGLIGIBLE
            elif abs_amt < 10:  # $1B - $10B
                return ImpactMagnitude.LOW
            elif abs_amt < 100:  # $10B - $100B
                return ImpactMagnitude.MEDIUM
            elif abs_amt < 500:  # $100B - $500B
                return ImpactMagnitude.HIGH
            else:  # > $500B
                return ImpactMagnitude.TRANSFORMATIVE
        except (TypeError, ValueError):
            return ImpactMagnitude.MEDIUM
    
    def _create_fiscal_impact(self, mechanism: Dict, is_revenue: bool) -> Optional[FiscalImpact]:
        """Create a FiscalImpact from a mechanism dictionary."""
        amount = mechanism.get("amount")
        if amount is None:
            return None
        
        try:
            amt = float(amount)
            # Apply uncertainty bands (±20% for P10/P90)
            return FiscalImpact(
                amount_billions=amt,
                time_period=mechanism.get("time_period", "10-year"),
                confidence_low=amt * 0.8,
                confidence_mid=amt,
                confidence_high=amt * 1.2,
                is_revenue=is_revenue,
                is_recurring=mechanism.get("is_recurring", True),
            )
        except (TypeError, ValueError):
            return None
    
    def _generate_executive_summary(self, analysis: AgentAnalysis) -> str:
        """Generate executive summary from analysis."""
        revenue_findings = [f for f in analysis.findings if f.category == FindingCategory.REVENUE]
        spending_findings = [f for f in analysis.findings if f.category == FindingCategory.SPENDING]
        
        total_revenue = sum(
            f.fiscal_impact.amount_billions 
            for f in revenue_findings 
            if f.fiscal_impact
        )
        total_spending = sum(
            f.fiscal_impact.amount_billions 
            for f in spending_findings 
            if f.fiscal_impact
        )
        
        return (
            f"Fiscal Analysis Summary: Identified {len(revenue_findings)} revenue provisions "
            f"(~${total_revenue:.1f}B) and {len(spending_findings)} spending provisions "
            f"(~${total_spending:.1f}B). Net fiscal impact: ${total_revenue - total_spending:.1f}B."
        )
    
    def _generate_key_takeaways(self, analysis: AgentAnalysis) -> List[str]:
        """Generate key takeaways from analysis."""
        takeaways = []
        
        high_impact = [
            f for f in analysis.findings 
            if f.impact_magnitude in [ImpactMagnitude.HIGH, ImpactMagnitude.TRANSFORMATIVE]
        ]
        
        if high_impact:
            takeaways.append(
                f"Identified {len(high_impact)} high-impact fiscal provisions"
            )
        
        low_confidence = [f for f in analysis.findings if f.confidence < 0.6]
        if low_confidence:
            takeaways.append(
                f"{len(low_confidence)} findings have elevated uncertainty"
            )
        
        return takeaways
    
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Critique another agent's analysis from a fiscal perspective.
        
        Args:
            other_analysis: Analysis to critique
            context: Original analysis context
        
        Returns:
            List of critiques
        """
        critiques = []
        
        # Check for missing fiscal considerations
        has_fiscal = any(
            f.category in [FindingCategory.REVENUE, FindingCategory.SPENDING, 
                          FindingCategory.DEBT, FindingCategory.DEFICIT]
            for f in other_analysis.findings
        )
        
        if not has_fiscal and other_analysis.agent_type != AgentType.FISCAL:
            critiques.append(Critique(
                critic_id=self.agent_id,
                target_id=other_analysis.agent_id,
                critique_type=CritiqueType.SCOPE,
                severity=CritiqueSeverity.MODERATE,
                argument="Analysis does not consider fiscal implications of the policy",
                suggested_revision="Include analysis of revenue/spending impacts",
            ))
        
        # Check for unrealistic magnitude estimates
        for finding in other_analysis.findings:
            if finding.fiscal_impact:
                amt = finding.fiscal_impact.amount_billions
                if amt > 1000:  # >$1T is unusual
                    critiques.append(Critique(
                        critic_id=self.agent_id,
                        target_id=other_analysis.agent_id,
                        target_finding_id=finding.finding_id,
                        critique_type=CritiqueType.MAGNITUDE,
                        severity=CritiqueSeverity.MAJOR,
                        argument=f"Fiscal estimate of ${amt}B exceeds typical policy impacts",
                        suggested_revision="Review methodology and validate against CBO baselines",
                    ))
        
        return critiques
    
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Vote on proposals from a fiscal perspective.
        
        Args:
            proposals: List of proposals to vote on
            context: Analysis context
        
        Returns:
            List of votes
        """
        votes = []
        
        for proposal in proposals:
            # Determine support based on fiscal soundness
            vote_type = VoteType.NEUTRAL
            confidence = 0.6
            reasoning = "Neutral pending detailed fiscal analysis"
            
            # Simple heuristics for MVP
            desc_lower = proposal.description.lower()
            
            if "deficit neutral" in desc_lower or "pay-as-you-go" in desc_lower:
                vote_type = VoteType.SUPPORT
                confidence = 0.75
                reasoning = "Proposal maintains fiscal discipline"
            
            elif "increase debt" in desc_lower or "unfunded" in desc_lower:
                vote_type = VoteType.OPPOSE
                confidence = 0.70
                reasoning = "Proposal increases long-term fiscal burden"
            
            votes.append(Vote(
                voter_id=self.agent_id,
                proposal_id=proposal.proposal_id,
                support=vote_type,
                confidence=confidence,
                reasoning=reasoning,
            ))
        
        return votes
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Get fiscal agent's weight for a topic.
        
        Returns higher weight for fiscal topics.
        """
        topic_lower = topic.lower()
        
        for keyword, weight in self.SPECIALTY_TOPICS.items():
            if keyword in topic_lower:
                return weight
        
        return 1.0  # Default weight
