"""
Policy Mechanics Extractor
Extracts detailed policy implementation mechanics from legislative text.
Focuses on healthcare reform with structured extraction of:
- Funding mechanisms (revenue sources, tax rates, consolidation)
- Surplus allocation rules
- Circuit breakers and safeguards
- Innovation fund rules
- Timeline and milestones
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


@dataclass
class FundingMechanism:
    """Extracted funding mechanism details."""
    source_type: str  # payroll_tax, redirected_federal, converted_premiums, efficiency_gains, transaction_tax, excise_reallocation, import_tariffs, reinsurance_pool
    percentage_gdp: Optional[float] = None
    percentage_rate: Optional[float] = None  # e.g., 15% payroll tax rate
    description: str = ""
    phase_in_start: Optional[int] = None
    phase_in_end: Optional[int] = None
    conditions: List[str] = field(default_factory=list)
    estimated_amount: Optional[float] = None  # billions if available


@dataclass
class SurplusAllocation:
    """Extracted surplus allocation rules."""
    contingency_reserve_pct: float = 0.0
    debt_reduction_pct: float = 0.0
    infrastructure_pct: float = 0.0
    dividends_pct: float = 0.0
    other_allocations: Dict[str, float] = field(default_factory=dict)
    trigger_conditions: List[str] = field(default_factory=list)


@dataclass
class CircuitBreaker:
    """Extracted circuit breaker / fiscal safeguard."""
    trigger_type: str  # spending_cap, surplus_trigger, deficit_trigger
    threshold_value: float
    threshold_unit: str  # percent_gdp, percent_baseline, absolute_dollars
    action: str  # freeze_taxes, cut_taxes, increase_funding
    description: str = ""


@dataclass
class InnovationFundRules:
    """Extracted innovation fund rules."""
    funding_min_pct: float = 0.0
    funding_max_pct: float = 0.0
    funding_base: str = ""  # e.g., "savings vs baseline"
    prize_min_dollars: float = 0.0
    prize_max_dollars: float = 0.0
    annual_cap_pct: float = 0.0
    annual_cap_base: str = ""  # e.g., "surpluses"
    eligible_categories: List[str] = field(default_factory=list)


@dataclass
class TimelineMilestone:
    """Extracted timeline milestone."""
    year: int
    description: str
    metric_type: str = ""  # enrollment, spending_target, coverage_rate
    target_value: Optional[float] = None


@dataclass
class PolicyMechanics:
    """Complete extracted policy mechanics."""
    policy_name: str
    policy_type: str  # healthcare, tax_reform, spending_reform, combined
    
    # Core mechanics
    funding_mechanisms: List[FundingMechanism] = field(default_factory=list)
    surplus_allocation: Optional[SurplusAllocation] = None
    circuit_breakers: List[CircuitBreaker] = field(default_factory=list)
    innovation_fund: Optional[InnovationFundRules] = None
    timeline_milestones: List[TimelineMilestone] = field(default_factory=list)
    
    # Healthcare-specific
    target_spending_pct_gdp: Optional[float] = None
    target_spending_year: Optional[int] = None
    zero_out_of_pocket: bool = False
    universal_coverage: bool = False
    
    # Extracted text sections for reference
    source_sections: Dict[str, str] = field(default_factory=dict)
    confidence_score: float = 0.0
    unfunded: bool = False  # flag when no revenue identified


class PolicyMechanicsExtractor:
    """Extract structured policy mechanics from legislative text."""

    @staticmethod
    def _extract_section(text: str, section_number: int) -> Optional[str]:
        """Return the raw text of a numbered section if present."""
        pattern = rf'\*\*?(?:Section|Sec\.?)\s*{section_number}[.\s]+[^\n]*\n(.*?)(?=\*\*?(?:Section|Sec\.?)\s*{section_number + 1}|\Z)'
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None
    
    @staticmethod
    def extract_usgha_mechanics(text: str) -> PolicyMechanics:
        """
        Extract USGHA-specific mechanics from policy text.
        Optimized for United States Galactic Health Act structure.
        """
        mechanics = PolicyMechanics(
            policy_name="United States Galactic Health Act",
            policy_type="healthcare"
        )
        
        # Extract funding mechanisms (Section 6)
        mechanics.funding_mechanisms = PolicyMechanicsExtractor._extract_funding_section_6(text)

        # Keep raw sections for traceability
        mechanics.source_sections["funding"] = PolicyMechanicsExtractor._extract_section(text, 6) or ""
        
        # Extract surplus allocation (Section 11)
        mechanics.surplus_allocation = PolicyMechanicsExtractor._extract_surplus_section_11(text)
        mechanics.source_sections["surplus_allocation"] = PolicyMechanicsExtractor._extract_section(text, 11) or ""
        
        # Extract circuit breakers (Section 6d)
        mechanics.circuit_breakers = PolicyMechanicsExtractor._extract_circuit_breakers(text)
        mechanics.source_sections["circuit_breakers"] = PolicyMechanicsExtractor._extract_section(text, 6) or ""
        
        # Extract innovation fund (Section 9)
        mechanics.innovation_fund = PolicyMechanicsExtractor._extract_innovation_fund(text)
        mechanics.source_sections["innovation_fund"] = PolicyMechanicsExtractor._extract_section(text, 9) or ""
        
        # Extract timeline milestones
        mechanics.timeline_milestones = PolicyMechanicsExtractor._extract_timeline(text)
        mechanics.source_sections["timeline"] = "\n".join(m.description for m in mechanics.timeline_milestones)
        
        # Mark unfunded if no revenue sources found
        mechanics.unfunded = len(mechanics.funding_mechanisms) == 0

        # Extract spending targets
        spending_target = PolicyMechanicsExtractor._extract_spending_target(text)
        if spending_target:
            mechanics.target_spending_pct_gdp = spending_target.get('target_pct', None)
            mechanics.target_spending_year = spending_target.get('target_year', None)
        
        # Extract coverage provisions
        mechanics.zero_out_of_pocket = bool(re.search(r'zero[- ]out[- ]of[- ]pocket', text, re.IGNORECASE))
        mechanics.universal_coverage = bool(re.search(r'universal\s+coverage', text, re.IGNORECASE))
        
        # Calculate confidence
        mechanics.confidence_score = PolicyMechanicsExtractor._calculate_confidence(mechanics)
        
        return mechanics

    @staticmethod
    def extract_generic_healthcare_mechanics(text: str, policy_name: str = "Extracted Healthcare Policy") -> PolicyMechanics:
        """Generic healthcare extraction path without USGHA assumptions."""
        mechanics = PolicyMechanics(policy_name=policy_name, policy_type="healthcare")

        mechanics.funding_mechanisms = PolicyMechanicsExtractor._extract_generic_funding(text)
        mechanics.source_sections["funding"] = PolicyMechanicsExtractor._extract_section(text, 6) or ""

        mechanics.surplus_allocation = PolicyMechanicsExtractor._extract_surplus_section_11(text) or \
            PolicyMechanicsExtractor._extract_surplus_generic(text)
        mechanics.source_sections["surplus_allocation"] = PolicyMechanicsExtractor._extract_section(text, 11) or ""

        mechanics.circuit_breakers = PolicyMechanicsExtractor._extract_circuit_breakers(text)
        mechanics.innovation_fund = PolicyMechanicsExtractor._extract_innovation_fund(text)
        mechanics.timeline_milestones = PolicyMechanicsExtractor._extract_timeline(text)

        # Coverage flags for single-payer style bills (e.g., no premiums/copays, all residents)
        mechanics.zero_out_of_pocket = bool(re.search(r'no\s+(?:deductibles?|copay(?:ment)?s?|premiums?)', text, re.IGNORECASE))
        mechanics.universal_coverage = bool(re.search(r'(all\s+residents|universal\s+coverage|single[- ]payer)', text, re.IGNORECASE))

        spending_target = PolicyMechanicsExtractor._extract_spending_target(text)
        if spending_target:
            mechanics.target_spending_pct_gdp = spending_target.get("target_pct", None)
            mechanics.target_spending_year = spending_target.get("target_year", None)

        mechanics.confidence_score = PolicyMechanicsExtractor._calculate_confidence(mechanics)
        return mechanics

    @staticmethod
    def mechanics_from_dict(data: Dict[str, Any], default_name: str = "Uploaded Policy",
                            default_type: str = "healthcare") -> PolicyMechanics:
        """Rehydrate PolicyMechanics from a serialized dictionary."""
        mechanics = PolicyMechanics(
            policy_name=data.get("policy_name", default_name),
            policy_type=data.get("policy_type", default_type)
        )

        # Core mechanics
        for fm in data.get("funding_mechanisms", []) or []:
            mechanics.funding_mechanisms.append(FundingMechanism(
                source_type=fm.get("source_type", ""),
                percentage_gdp=fm.get("percentage_gdp", None),
                percentage_rate=fm.get("percentage_rate", None),
                description=fm.get("description", ""),
                phase_in_start=fm.get("phase_in_start", None),
                phase_in_end=fm.get("phase_in_end", None),
                conditions=fm.get("conditions", []) or []
            ))

        alloc = data.get("surplus_allocation") or None
        if alloc:
            mechanics.surplus_allocation = SurplusAllocation(
                contingency_reserve_pct=alloc.get("contingency_reserve_pct", 0.0),
                debt_reduction_pct=alloc.get("debt_reduction_pct", 0.0),
                infrastructure_pct=alloc.get("infrastructure_pct", 0.0),
                dividends_pct=alloc.get("dividends_pct", 0.0),
                other_allocations=alloc.get("other_allocations", {}) or {},
                trigger_conditions=alloc.get("trigger_conditions", []) or []
            )

        for cb in data.get("circuit_breakers", []) or []:
            mechanics.circuit_breakers.append(CircuitBreaker(
                trigger_type=cb.get("trigger_type", ""),
                threshold_value=cb.get("threshold_value", 0.0),
                threshold_unit=cb.get("threshold_unit", ""),
                action=cb.get("action", ""),
                description=cb.get("description", "")
            ))

        innovation = data.get("innovation_fund") or None
        if innovation:
            mechanics.innovation_fund = InnovationFundRules(
                funding_min_pct=innovation.get("funding_min_pct", 0.0),
                funding_max_pct=innovation.get("funding_max_pct", 0.0),
                funding_base=innovation.get("funding_base", ""),
                prize_min_dollars=innovation.get("prize_min_dollars", 0.0),
                prize_max_dollars=innovation.get("prize_max_dollars", 0.0),
                annual_cap_pct=innovation.get("annual_cap_pct", 0.0),
                annual_cap_base=innovation.get("annual_cap_base", ""),
                eligible_categories=innovation.get("eligible_categories", []) or []
            )

        for mile in data.get("timeline_milestones", []) or []:
            try:
                mechanics.timeline_milestones.append(TimelineMilestone(
                    year=int(mile.get("year")),
                    description=mile.get("description", ""),
                    metric_type=mile.get("metric_type", ""),
                    target_value=mile.get("target_value")
                ))
            except Exception:
                continue

        # Policy targets and flags
        mechanics.target_spending_pct_gdp = data.get("target_spending_pct_gdp")
        mechanics.target_spending_year = data.get("target_spending_year")
        mechanics.zero_out_of_pocket = bool(data.get("zero_out_of_pocket", False))
        mechanics.universal_coverage = bool(data.get("universal_coverage", False))

        # Optional metadata
        mechanics.source_sections = data.get("source_sections", {}) or {}
        mechanics.confidence_score = float(data.get("confidence_score", 0.0)) if data.get("confidence_score") is not None else 0.0

        return mechanics
    
    @staticmethod
    def _extract_funding_section_6(text: str) -> List[FundingMechanism]:
        """Extract funding mechanisms from Section 6."""
        mechanisms = []
        
        # Find Section 6 text (handles both **Section 6. and Section 6.)
        section_match = re.search(
            r'\*\*?(?:Section|Sec\.?)\s*6[.\s]+[^\n]*(?:Funding|funding)[^\n*]*\*?\*?[^\n]*\n(.*?)(?=\*\*?(?:Section|Sec\.?)\s*7|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not section_match:
            return mechanisms
        
        section_text = section_match.group(1)
        
        # Extract payroll tax
        payroll_match = re.search(
            r'payroll\s+(?:tax|contribution)[^.]*?(\d+(?:\.\d+)?)\s*percent',
            section_text,
            re.IGNORECASE
        )
        if payroll_match:
            mechanisms.append(FundingMechanism(
                source_type="payroll_tax",
                percentage_rate=float(payroll_match.group(1)),
                description=f"{payroll_match.group(1)}% combined payroll tax"
            ))
        
        # Extract phase-in timeline
        phase_match = re.search(
            r'phased\s+in\s+over\s+(\d+)\s+years',
            section_text,
            re.IGNORECASE
        )
        if phase_match and mechanisms:
            mechanisms[-1].phase_in_start = 2027  # USGHA starts 2027
            mechanisms[-1].phase_in_end = 2027 + int(phase_match.group(1))
        
        # Extract redirected federal healthcare (Medicare/Medicaid/VA/ACA/CHIP consolidation)
        # Look for mentions throughout the document
        federal_patterns = [
            r'(?:redirect|consolidat)[^.]*?(?:Medicare|Medicaid|federal\s+health)[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            r'existing\s+federal\s+health\s+spending[^.]*?(\d+(?:\.\d+)?)\s*percent',
        ]
        
        for pattern in federal_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                mechanisms.append(FundingMechanism(
                    source_type="redirected_federal",
                    percentage_gdp=float(match.group(1)),
                    description=f"Redirected federal healthcare ({match.group(1)}% GDP)"
                ))
                break

        # Extract converted premiums (employer + employee) when explicit
        premium_match = re.search(
            r'(?:converted|redirected|reallocated)[^.]*?premiums[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if premium_match:
            mechanisms.append(FundingMechanism(
                source_type="converted_premiums",
                percentage_gdp=float(premium_match.group(1)),
                description=f"Converted employer + employee premiums ({premium_match.group(1)}% GDP)"
            ))

        # Financial transaction tax reallocation (e.g., 1% on large trades)
        ftt_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:financial\s+transaction\s+tax|FTT)',
            text,
            re.IGNORECASE
        )
        if ftt_match:
            mechanisms.append(FundingMechanism(
                source_type="transaction_tax",
                percentage_rate=float(ftt_match.group(1)),
                description=f"Financial transaction tax reallocation ({ftt_match.group(1)}% on large trades)"
            ))

        # Excise tax reallocation
        excise_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:excise\s+tax|luxury\s+goods|unhealthy\s+products)',
            text,
            re.IGNORECASE
        )
        if excise_match:
            mechanisms.append(FundingMechanism(
                source_type="excise_reallocation",
                percentage_rate=float(excise_match.group(1)),
                description=f"Reallocated excise taxes ({excise_match.group(1)}% of existing excises)"
            ))

        # Import tariffs share
        tariff_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:import\s+tariffs|tariff\s+revenues)',
            text,
            re.IGNORECASE
        )
        if tariff_match:
            mechanisms.append(FundingMechanism(
                source_type="import_tariffs",
                percentage_rate=float(tariff_match.group(1)),
                description=f"Portion of import tariffs ({tariff_match.group(1)}%)"
            ))

        # Transitional reinsurance pool funding mention
        if re.search(r'reinsurance\s+pool', text, re.IGNORECASE):
            mechanisms.append(FundingMechanism(
                source_type="reinsurance_pool",
                description="Temporary high-cost transitional reinsurance pool"
            ))

        # Extract efficiency gains only when quantified
        efficiency_match = re.search(
            r'(?:efficiency|administrative|drug\s+pricing|savings)[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if efficiency_match:
            mechanisms.append(FundingMechanism(
                source_type="efficiency_gains",
                percentage_gdp=float(efficiency_match.group(1)),
                description=f"Efficiency and savings ({efficiency_match.group(1)}% GDP)"
            ))
        
        return mechanisms
    
    @staticmethod
    def _extract_surplus_section_11(text: str) -> Optional[SurplusAllocation]:
        """Extract surplus allocation from Section 11."""
        # Find Section 11 text (handles **Section 11. format)
        section_match = re.search(
            r'\*\*?(?:Section|Sec\.?)\s*11[.\s]+[^\n]*(?:Surplus|surplus)[^\n*]*\*?\*?[^\n]*\n(.*?)(?=\*\*?(?:Section|Sec\.?)\s*12|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not section_match:
            return None
        
        section_text = section_match.group(1)
        
        allocation = SurplusAllocation()
        
        # Look for percentage allocations
        # Pattern: (1) X percent to Y
        allocations_pattern = r'\((\d+)\)\s*(\d+(?:\.\d+)?)\s*percent\s+to\s+([^\n.]+)'
        
        for match in re.finditer(allocations_pattern, section_text, re.IGNORECASE):
            pct = float(match.group(2))
            if pct > 100:
                continue
            destination = match.group(3).lower()
            
            if 'contingency' in destination or 'reserve' in destination:
                allocation.contingency_reserve_pct = pct
            elif 'debt' in destination:
                allocation.debt_reduction_pct = pct
            elif 'infrastructure' in destination or 'education' in destination or 'research' in destination:
                allocation.infrastructure_pct = pct
            elif 'dividend' in destination or 'taxpayer' in destination or 'rebate' in destination:
                allocation.dividends_pct = pct
            else:
                allocation.other_allocations[destination.strip()] = pct
        
        # Only return if we found meaningful allocations
        total_pct = (allocation.contingency_reserve_pct + 
                    allocation.debt_reduction_pct + 
                    allocation.infrastructure_pct + 
                    allocation.dividends_pct)
        
        return allocation if total_pct > 0 else None

    @staticmethod
    def _extract_surplus_generic(text: str) -> Optional[SurplusAllocation]:
        """Extract surplus allocation rules from any part of the text."""
        allocation = SurplusAllocation()

        for match in re.finditer(r'(?:reserve|contingency)[^.]*?(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE):
            pct = float(match.group(1))
            if pct <= 100:
                allocation.contingency_reserve_pct = max(allocation.contingency_reserve_pct, pct)
        for match in re.finditer(r'debt[^.]*?(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE):
            pct = float(match.group(1))
            if pct <= 100:
                allocation.debt_reduction_pct = max(allocation.debt_reduction_pct, pct)
        for match in re.finditer(r'(\d+(?:\.\d+)?)\s*percent[^.]*?(infrastructure|education|research)', text, re.IGNORECASE):
            pct = float(match.group(1))
            if pct <= 100:
                allocation.infrastructure_pct = max(allocation.infrastructure_pct, pct)
        for match in re.finditer(r'(dividend|rebate|taxpayer)[^.]*?(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE):
            pct = float(match.group(2))
            if pct <= 100:
                allocation.dividends_pct = max(allocation.dividends_pct, pct)

        total_pct = (
            allocation.contingency_reserve_pct +
            allocation.debt_reduction_pct +
            allocation.infrastructure_pct +
            allocation.dividends_pct
        )
        return allocation if total_pct > 0 else None
    
    @staticmethod
    def _extract_circuit_breakers(text: str) -> List[CircuitBreaker]:
        """Extract fiscal circuit breakers."""
        breakers = []
        
        # Find Section 6(d) specifically or any mention of circuit breakers
        circuit_patterns = [
            r'\(d\)\s+Fiscal\s+Circuit\s+Breakers[.\s—:]+([^\n]+(?:\n[^\n(]+)*)',  # Section 6(d)
            r'(?:fiscal\s+circuit\s+breaker|safeguard)[s]?[:\s]+(.*?)(?=\n\n|\Z)'  # Generic
        ]
        
        for pattern in circuit_patterns:
            for match in re.finditer(pattern, text, re.DOTALL | re.IGNORECASE):
                breaker_text = match.group(1)
                
                # Look for spending cap triggers
                cap_match = re.search(
                    r'expenditures?\s+exceed[s]?\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP)',
                    breaker_text,
                    re.IGNORECASE
                )
                if cap_match:
                    breakers.append(CircuitBreaker(
                        trigger_type="spending_cap",
                        threshold_value=float(cap_match.group(1)),
                        threshold_unit="percent_gdp",
                        action="freeze_taxes",
                        description=f"If spending exceeds {cap_match.group(1)}% GDP, freeze tax rates"
                    ))
                
                # Look for surplus triggers (GDP percentage)
                surplus_match = re.search(
                    r'surplus[es]?\s+(?:exceed|trigger)[s]?\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP)',
                    breaker_text,
                    re.IGNORECASE
                )
                if surplus_match:
                    breakers.append(CircuitBreaker(
                        trigger_type="surplus_trigger",
                        threshold_value=float(surplus_match.group(1)),
                        threshold_unit="percent_gdp",
                        action="cut_taxes",
                        description=f"If surplus exceeds {surplus_match.group(1)}% GDP, automatic tax cuts"
                    ))
                
                # Look for dollar-based surplus triggers (e.g., explicit $X billion triggers)
                dollar_surplus_match = re.search(
                    r'(?:every|for\s+each|per)\s+\$?(\d+(?:\.\d+)?)\s*(?:billion|B)[^.]*?surplus[es]?[^.]*?(\d+(?:\.\d+)?)\s*percent[^.]*?(?:tax|rate)\s+(?:reduction|cut)',
                    breaker_text,
                    re.IGNORECASE
                )
                if dollar_surplus_match:
                    breakers.append(CircuitBreaker(
                        trigger_type="surplus_trigger",
                        threshold_value=float(dollar_surplus_match.group(1)),
                        threshold_unit="billion_dollars",
                        action=f"Automatic {dollar_surplus_match.group(2)}% tax reduction",
                        description=f"For every ${dollar_surplus_match.group(1)}B in surpluses, reduce taxes by {dollar_surplus_match.group(2)}%"
                    ))
        
        return breakers
    
    @staticmethod
    def _extract_innovation_fund(text: str) -> Optional[InnovationFundRules]:
        """Extract innovation fund rules from Section 9."""
        # Find Section 9 text (handles **Section 9. format)
        section_match = re.search(
            r'\*\*?(?:Section|Sec\.?)\s*9[.\s]+[^\n]*(?:Innovation|innovation)[^\n*]*\*?\*?[^\n]*\n(.*?)(?=\*\*?(?:Section|Sec\.?)\s*10|\Z)',
            text,
            re.DOTALL | re.IGNORECASE
        )
        
        if not section_match:
            return None
        
        section_text = section_match.group(1)
        
        fund = InnovationFundRules()
        
        # Extract funding percentage range
        funding_range = re.search(
            r'not\s+less\s+than\s+(\d+(?:\.\d+)?)\s*percent\s+and\s+not\s+more\s+than\s+(\d+(?:\.\d+)?)\s*percent',
            section_text,
            re.IGNORECASE
        )
        if funding_range:
            fund.funding_min_pct = float(funding_range.group(1))
            fund.funding_max_pct = float(funding_range.group(2))
        
        # Extract what it's a percentage of
        if 'reduction in' in section_text.lower() or 'savings' in section_text.lower():
            fund.funding_base = "savings_vs_baseline"
        
        # Extract prize ranges
        prize_pattern = r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion)'
        prize_amounts = []
        for match in re.finditer(prize_pattern, section_text, re.IGNORECASE):
            amount_str = match.group(1).replace(',', '')
            amount = float(amount_str)
            if 'billion' in match.group(0).lower():
                amount *= 1000  # Convert to millions
            prize_amounts.append(amount)
        
        if prize_amounts:
            fund.prize_min_dollars = min(prize_amounts) * 1_000_000  # Convert millions to dollars
            fund.prize_max_dollars = max(prize_amounts) * 1_000_000
        
        # Extract annual cap - handle variations like "capped at", "capped art" (PDF OCR error)
        cap_match = re.search(
            r'(?:annual[ly]?\s+)?(?:capped|cap)[s]?\s+(?:at|art)\s+(\d+(?:\.\d+)?)\s*(?:%|percent)',
            section_text,
            re.IGNORECASE
        )
        if cap_match:
            fund.annual_cap_pct = float(cap_match.group(1))
            if 'surplus' in section_text.lower():
                fund.annual_cap_base = "surpluses"
        
        # Extract eligible categories
        if 'longevity' in section_text.lower():
            fund.eligible_categories.append('longevity')
        if 'radiation' in section_text.lower():
            fund.eligible_categories.append('radiation_countermeasures')
        if 'healthspan' in section_text.lower():
            fund.eligible_categories.append('healthspan_extension')
        
        return fund if fund.funding_max_pct > 0 else None
    
    @staticmethod
    def _extract_timeline(text: str) -> List[TimelineMilestone]:
        """Extract timeline milestones."""
        milestones = []
        
        # Pattern: beginning/by/on [date/year]
        date_patterns = [
            r'beginning\s+(?:January\s+\d+,\s+)?(\d{4})',
            r'by\s+(?:January\s+\d+,\s+)?(\d{4})',
            r'on\s+(?:January\s+\d+,\s+)?(\d{4})',
            r'(?:fiscal\s+year\s+)?(\d{4})',
        ]
        
        # Look for specific milestones
        milestone_patterns = {
            'coverage_start': r'coverage[^.]*?beginning[^.]*?(\d{4})',
            'full_implementation': r'full\s+(?:national\s+)?implementation[^.]*?(\d{4})',
            'spending_target': r'(?:below|under)\s+(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:gross\s+domestic\s+product|GDP)[^.]*?by\s+(\d{4})',
            'surplus_target': r'surplus[es]?[^.]*?by\s+(\d{4})',
        }
        
        for milestone_type, pattern in milestone_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if milestone_type == 'spending_target':
                    milestones.append(TimelineMilestone(
                        year=int(match.group(2)),
                        description=f"Achieve {match.group(1)}% GDP spending target",
                        metric_type="spending_pct_gdp",
                        target_value=float(match.group(1))
                    ))
                else:
                    year = int(match.group(1))
                    milestones.append(TimelineMilestone(
                        year=year,
                        description=milestone_type.replace('_', ' ').title(),
                        metric_type=milestone_type
                    ))
        
        return sorted(milestones, key=lambda m: m.year)

    @staticmethod
    def _extract_generic_funding(text: str) -> List[FundingMechanism]:
        """Generic funding extraction without USGHA defaults."""
        mechanisms: List[FundingMechanism] = []

        # Payroll tax - prioritize cap/maximum keywords and validate rate range
        # Try two patterns: "cap...payroll...X%" and "payroll...capped at X%"
        payroll_cap_match = re.search(
            r'(?:cap(?:ped)?|maximum|limit(?:ed)?)[^.]{0,150}?(?:payroll|combined)[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent',
            text,
            re.IGNORECASE
        )
        if not payroll_cap_match:
            # Try reverse order: payroll...capped...X%
            payroll_cap_match = re.search(
                r'(?:payroll|combined)[^.]{0,150}?(?:cap(?:ped)?|maximum|limit(?:ed)?)[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent',
                text,
                re.IGNORECASE
            )
        
        if payroll_cap_match:
            rate = float(payroll_cap_match.group(1))
            if 5 <= rate <= 25:  # Validate plausible payroll tax range
                # Convert payroll rate to GDP estimate
                # Wages are ~53% of GDP, so 15% payroll ≈ 15% * 53% ≈ 7.95% GDP
                estimated_gdp_pct = rate * 0.53
                mechanisms.append(FundingMechanism(
                    source_type="payroll_tax",
                    percentage_rate=rate,
                    percentage_gdp=estimated_gdp_pct,
                    description=f"{rate}% combined payroll tax (~{estimated_gdp_pct:.1f}% GDP)"
                ))
        else:
            # Fallback: generic payroll pattern with validation
            payroll_match = re.search(
                r'payroll\s+(?:tax|contribution)[^.]*?(\d+(?:\.\d+)?)\s*percent',
                text,
                re.IGNORECASE
            )
            if payroll_match:
                rate = float(payroll_match.group(1))
                if 5 <= rate <= 25:  # Only accept plausible rates
                    # Convert payroll rate to GDP estimate
                    estimated_gdp_pct = rate * 0.53
                    mechanisms.append(FundingMechanism(
                        source_type="payroll_tax",
                        percentage_rate=rate,
                        percentage_gdp=estimated_gdp_pct,
                        description=f"{rate}% payroll tax (~{estimated_gdp_pct:.1f}% GDP)"
                    ))

        federal_match = re.search(
            r'(?:federal\s+health|Medicare|Medicaid)[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if federal_match:
            mechanisms.append(FundingMechanism(
                source_type="redirected_federal",
                percentage_gdp=float(federal_match.group(1)),
                description=f"Redirected federal health spending ({federal_match.group(1)}% GDP)"
            ))

        premium_match = re.search(
            r'(?:converted|redirected)[^.]*?premium[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if premium_match:
            mechanisms.append(FundingMechanism(
                source_type="converted_premiums",
                percentage_gdp=float(premium_match.group(1)),
                description=f"Converted premiums ({premium_match.group(1)}% GDP)"
            ))

        efficiency_match = re.search(
            r'(?:efficienc|savings|drug\s+pricing|administrative)[^.]*?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:GDP|gross\s+domestic\s+product)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if efficiency_match:
            mechanisms.append(FundingMechanism(
                source_type="efficiency_gains",
                percentage_gdp=float(efficiency_match.group(1)),
                description=f"Efficiency gains ({efficiency_match.group(1)}% GDP)"
            ))

        ftt_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:financial\s+transaction\s+tax|FTT)',
            text,
            re.IGNORECASE
        )
        if ftt_match:
            mechanisms.append(FundingMechanism(
                source_type="transaction_tax",
                percentage_rate=float(ftt_match.group(1)),
                description=f"Financial transaction tax ({ftt_match.group(1)}%)"
            ))

        excise_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:excise\s+tax|luxury\s+goods|unhealthy\s+products)',
            text,
            re.IGNORECASE
        )
        if excise_match:
            mechanisms.append(FundingMechanism(
                source_type="excise_reallocation",
                percentage_rate=float(excise_match.group(1)),
                description=f"Excise tax reallocation ({excise_match.group(1)}%)"
            ))

        tariff_match = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]*?(?:import\s+tariffs|tariff\s+revenues)',
            text,
            re.IGNORECASE
        )
        if tariff_match:
            mechanisms.append(FundingMechanism(
                source_type="import_tariffs",
                percentage_rate=float(tariff_match.group(1)),
                description=f"Import tariff allocation ({tariff_match.group(1)}%)"
            ))

        if re.search(r'reinsurance\s+pool', text, re.IGNORECASE):
            mechanisms.append(FundingMechanism(
                source_type="reinsurance_pool",
                description="Transitional reinsurance pool"
            ))

        # Premium conversion (employer/employee premiums → payroll contributions)
        premium_conversion_match = re.search(
            r'(?:employer|employee)[^.]{0,100}(?:premium|health\s+insurance)[^.]{0,100}(?:convert(?:ed)?|redirect(?:ed)?|replace(?:d)?)[^.]{0,50}(?:payroll|contribution)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if premium_conversion_match:
            mechanisms.append(FundingMechanism(
                source_type="converted_premiums",
                description="Employer/employee premiums converted to payroll contributions"
            ))

        # Federal program consolidation (Medicare, Medicaid, CHIP, VA, ACA)
        federal_consolidation_match = re.search(
            r'(?:redirect(?:ion)?|consolidat(?:e|ion)|transfer)[^.]{0,150}(?:Medicare|Medicaid|CHIP|VA|ACA|federal\s+health)[^.]{0,150}(?:expenditure|spending|program|budget)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if federal_consolidation_match:
            mechanisms.append(FundingMechanism(
                source_type="redirected_federal",
                description="Redirected federal health program spending (Medicare, Medicaid, CHIP, VA, ACA)"
            ))

        # Pharmaceutical/drug pricing savings
        pharma_savings_match = re.search(
            r'(?:drug|pharmaceutical|medicine)[^.]{0,100}(?:pricing|negotiat(?:e|ion)|savings|most[- ]favored[- ]nation)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if pharma_savings_match:
            mechanisms.append(FundingMechanism(
                source_type="pharmaceutical_savings",
                description="Pharmaceutical pricing reforms and savings"
            ))

        # Nutrition/social program consolidation (SNAP, WIC, school lunch)
        nutrition_consolidation_match = re.search(
            r'(?:SNAP|WIC|school\s+lunch|nutrition)[^.]{0,150}(?:consolida(?:te|tion)|transfer|integrat(?:e|ion))',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if nutrition_consolidation_match:
            mechanisms.append(FundingMechanism(
                source_type="program_consolidation",
                description="Nutrition and social program consolidation"
            ))

        # Disproportionate share hospital (DSH) and graduate medical education (GME) funds
        dsh_gme_match = re.search(
            r'(?:disproportionate\s+share\s+hospital|DSH|graduate\s+medical\s+education|GME)[^.]{0,100}(?:fund|follow|transfer)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if dsh_gme_match:
            mechanisms.append(FundingMechanism(
                source_type="dsh_gme_funds",
                description="Disproportionate share hospital (DSH) and graduate medical education (GME) funds"
            ))

        # Health inflation escalator (automatic payroll increase if medical CPI exceeds threshold)
        inflation_escalator_match = re.search(
            r'(?:health\s+inflation\s+escalator|medical\s+care\s+component|CPI[- ]U)[^.]{0,200}(?:exceed|greater|above)[^.]{0,50}(\d+(?:\.\d+)?)\s*percent',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if inflation_escalator_match:
            mechanisms.append(FundingMechanism(
                source_type="inflation_escalator",
                description=f"Health inflation escalator (automatic adjustment if medical CPI exceeds {inflation_escalator_match.group(1)}%)"
            ))

        # Earned Income Tax Credit (EITC) expansion for low earners
        eitc_match = re.search(
            r'(?:Earned\s+Income\s+Tax\s+Credit|EITC)[^.]{0,100}(?:expansion|rebate|low\s+earner)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if eitc_match:
            mechanisms.append(FundingMechanism(
                source_type="eitc_expansion",
                description="Earned Income Tax Credit expansion for low earners"
            ))

        # Post-processing: Add GDP percentage estimates for major revenue sources without explicit GDP values
        for mech in mechanisms:
            if mech.percentage_gdp is None or mech.percentage_gdp == 0:
                if mech.source_type == "redirected_federal":
                    # Medicare + Medicaid + CHIP + VA + ACA ≈ 3.5% GDP
                    mech.percentage_gdp = 3.5
                    if "%" not in mech.description:
                        mech.description += " (~3.5% GDP)"
                
                elif mech.source_type == "converted_premiums":
                    # Private health insurance premiums ≈ 5.5% GDP
                    mech.percentage_gdp = 5.5
                    if "%" not in mech.description:
                        mech.description += " (~5.5% GDP)"
                
                elif mech.source_type == "efficiency_gains":
                    # Administrative savings typically 3-5% GDP
                    mech.percentage_gdp = 3.0
                    if "%" not in mech.description:
                        mech.description += " (~3% GDP)"
                
                elif mech.source_type in ["financial_transaction_tax", "transaction_tax"] and mech.percentage_rate:
                    # FTT revenue depends on trading volume; 0.1-1% FTT ≈ 0.3-1.5% GDP
                    if mech.percentage_rate < 0.2:
                        mech.percentage_gdp = 0.3
                    elif mech.percentage_rate < 0.5:
                        mech.percentage_gdp = 0.6
                    else:
                        mech.percentage_gdp = 1.0
                    if "GDP" not in mech.description:
                        mech.description += f" (~{mech.percentage_gdp}% GDP)"
                
                elif mech.source_type in ["excise_reallocation", "excise_tax"]:
                    # Excise taxes ~0.5% GDP
                    mech.percentage_gdp = 0.5
                    if "GDP" not in mech.description:
                        mech.description += " (~0.5% GDP)"
                
                elif mech.source_type in ["import_tariffs", "tariff_revenue"]:
                    # Import tariffs ~2% GDP, allocating 12% of that
                    mech.percentage_gdp = 0.24
                    if "GDP" not in mech.description:
                        mech.description += " (~0.24% GDP)"
                
                elif mech.source_type == "program_consolidation":
                    # SNAP + WIC + school lunch ≈ 0.5% GDP
                    mech.percentage_gdp = 0.5
                    if "GDP" not in mech.description:
                        mech.description += " (~0.5% GDP)"
                
                elif mech.source_type == "drug_pricing_savings" or mech.source_type == "pharmaceutical_savings":
                    # Drug pricing savings ≈ 1-2% GDP
                    mech.percentage_gdp = 1.5
                    if "GDP" not in mech.description:
                        mech.description += " (~1.5% GDP)"
                
                elif mech.source_type == "reinsurance_pool":
                    # Reinsurance pool ≈ 0.2% GDP
                    mech.percentage_gdp = 0.2
                    if "GDP" not in mech.description:
                        mech.description += " (~0.2% GDP)"
                
                elif mech.source_type == "dsh_gme_funds":
                    # DSH + GME ≈ 0.3% GDP
                    mech.percentage_gdp = 0.3
                    if "GDP" not in mech.description:
                        mech.description += " (~0.3% GDP)"

        return mechanisms
    
    @staticmethod
    def _extract_spending_target(text: str) -> Optional[Dict[str, Any]]:
        """Extract spending target percentage and year."""
        # Pattern: below X percent of GDP by/within YEAR/YEARS
        # Prioritize "average below" which indicates final target vs interim milestones
        # Handle OCR errors like "arverage" and random single letters between words
        patterns = [
            r'a\w*verage\s+health\s+spending\s+below\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP).*?by\s*[^\d]*(\d{4})',
            r'average\s+below\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP).*?by\s+(\d{4})',
            r'below\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP).*?(?:by|within)\s+(\d{4})',
            r'below\s+(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|GDP).*?(?:within)\s+(\d+)\s+years?'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                target_pct = float(match.group(1))
                
                if len(match.groups()) >= 2:
                    try:
                        year_or_duration = int(match.group(2))
                        if year_or_duration > 100:  # Absolute year
                            target_year = year_or_duration
                        else:  # Relative years
                            target_year = 2025 + year_or_duration
                    except ValueError:
                        target_year = None
                else:
                    target_year = None
                
                return {
                    'target_pct': target_pct,
                    'target_year': target_year
                }
        
        return None
    
    @staticmethod
    def _calculate_confidence(mechanics: PolicyMechanics) -> float:
        """Calculate confidence score for extracted mechanics."""
        score = 0.0
        
        # Funding mechanisms (0-0.35) - increased weight for comprehensive extraction
        if mechanics.funding_mechanisms:
            # Bonus for having 3+ mechanisms (comprehensive funding model)
            base_score = min(len(mechanics.funding_mechanisms) * 0.08, 0.30)
            if len(mechanics.funding_mechanisms) >= 3:
                base_score += 0.05
            score += base_score
        
        # Surplus allocation (0-0.25)
        if mechanics.surplus_allocation:
            allocation = mechanics.surplus_allocation
            total_pct = (allocation.contingency_reserve_pct + 
                        allocation.debt_reduction_pct + 
                        allocation.infrastructure_pct + 
                        allocation.dividends_pct)
            score += min(total_pct / 100 * 0.25, 0.25)
        
        # Circuit breakers (0-0.2) - bonus for having both types
        if mechanics.circuit_breakers:
            base_score = min(len(mechanics.circuit_breakers) * 0.08, 0.15)
            if len(mechanics.circuit_breakers) >= 2:
                base_score += 0.05
            score += base_score
        
        # Innovation fund (0-0.1)
        if mechanics.innovation_fund and mechanics.innovation_fund.funding_max_pct > 0:
            score += 0.10
        
        # Timeline (0-0.1)
        if mechanics.timeline_milestones:
            score += min(len(mechanics.timeline_milestones) * 0.015, 0.10)

        # Coverage flags (0-0.05)
        if mechanics.universal_coverage:
            score += 0.03
        if mechanics.zero_out_of_pocket:
            score += 0.02

        # Penalize unfunded policies to surface warnings
        if mechanics.unfunded:
            score = min(score, 0.35)
        
        return min(score, 1.0)


def extract_with_context_awareness(text: str, policy_name: str = "Extracted Policy") -> PolicyMechanics:
    """
    Enhanced extraction using context-aware framework.
    
    This function combines semantic concept analysis with structured extraction
    to improve accuracy across diverse bill formats (M4A, ACA, USGHA, hybrid, etc.).
    
    Strategy:
    1. Use context framework to identify funding mechanisms conceptually
    2. Extract percentages from framework findings with semantic matching
    3. Skip obviously-wrong percentages (e.g., 0.1% for payroll tax when framework expects 15%)
    4. Merge findings: framework concepts + contextually-matched percentages
    
    Args:
        text: Policy text to extract
        policy_name: Name of policy
        
    Returns:
        PolicyMechanics with framework-enhanced extraction
    """
    try:
        from core.policy_mechanics_builder import extract_policy_context
    except ImportError:
        return PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text, policy_name)
    
    # Get context-aware extraction
    context_result = extract_policy_context(text, policy_name)
    policy_type = context_result.get("policy_type", "unknown")
    
    # Get baseline standard extraction
    mechanics = PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text, policy_name)
    
    # Set flags based on detected policy type
    if policy_type == "single_payer":
        mechanics.universal_coverage = True
        mechanics.zero_out_of_pocket = True
    
    # KEEP the standard extraction's funding mechanisms - they have GDP percentages!
    # Just boost confidence if framework found matching concepts
    found_concepts = context_result.get("concepts", {})
    
    # Boost confidence based on framework findings
    # High confidence if policy type detected + multiple funding mechanisms found
    if policy_type == "single_payer" and len(mechanics.funding_mechanisms) > 0:
        # Framework found a single-payer with funding mechanisms = high confidence
        confidence_base = 0.65  # Base for single-payer detection
        confidence_boost = min(len(mechanics.funding_mechanisms) * 0.02, 0.25)  # Up to +0.25
        mechanics.confidence_score = min(confidence_base + confidence_boost, 0.95)
    
    return mechanics


def extract_policy_mechanics(text: str, policy_type: str = "healthcare") -> PolicyMechanics:
    """
    Main entry point for extracting policy mechanics.
    
    Uses context-aware framework for healthcare policies to improve accuracy
    across diverse bill formats (M4A, ACA, hybrid, etc.).
    
    Args:
        text: Full policy text
        policy_type: Type of policy (healthcare, tax_reform, spending_reform)
    
    Returns:
        PolicyMechanics object with structured extraction
    """
    if policy_type == "healthcare":
        # Try context-aware extraction for healthcare
        try:
            return extract_with_context_awareness(text)
        except Exception as e:
            print(f"Context-aware extraction failed, falling back: {e}")
            # Fall back to standard extraction
            if "galactic health" in text.lower() or "usgha" in text.lower():
                return PolicyMechanicsExtractor.extract_usgha_mechanics(text)
            return PolicyMechanicsExtractor.extract_generic_healthcare_mechanics(text)
    
    # Generic extraction fallback for non-healthcare
    mechanics = PolicyMechanics(
        policy_name="Extracted Policy",
        policy_type=policy_type
    )
    
    # Add generic extraction logic here if needed
    
    return mechanics
