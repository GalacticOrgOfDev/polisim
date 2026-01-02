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
class TaxMechanics:
    """Extracted tax reform mechanics."""
    wealth_tax_rate: Optional[float] = None
    wealth_tax_threshold: Optional[float] = None
    wealth_tax_tiers: Dict[str, float] = field(default_factory=dict)  # e.g., {"tier_1": 0.02, "threshold_1": 50_000_000}
    
    consumption_tax_rate: Optional[float] = None
    consumption_tax_exemptions: List[str] = field(default_factory=list)
    consumption_tax_rebate: Optional[float] = None
    
    carbon_tax_per_ton: Optional[float] = None
    carbon_tax_annual_increase: Optional[float] = None
    carbon_revenue_allocation: Dict[str, float] = field(default_factory=dict)
    
    financial_transaction_tax_rate: Optional[float] = None
    
    income_tax_changes: Dict[str, Any] = field(default_factory=dict)  # bracket changes, rate changes
    corporate_tax_rate: Optional[float] = None
    payroll_tax_rate: Optional[float] = None
    
    tax_revenue_billions: Optional[float] = None
    estimated_tax_revenue_growth: Optional[float] = None


@dataclass
class SocialSecurityMechanics:
    """Extracted social security reform mechanics."""
    payroll_tax_rate: Optional[float] = None
    payroll_tax_cap_change: Optional[str] = None  # e.g., "remove_cap", "increase_cap"
    payroll_tax_cap_increase: Optional[float] = None
    
    full_retirement_age: Optional[int] = None
    full_retirement_age_change: Optional[int] = None
    
    benefit_formula_changes: Dict[str, Any] = field(default_factory=dict)
    cola_adjustments: Optional[str] = None
    
    means_testing_threshold: Optional[float] = None
    means_testing_enabled: bool = False
    
    early_claiming_reduction: Optional[float] = None
    delayed_claiming_credit: Optional[float] = None
    
    demographic_assumptions: Dict[str, float] = field(default_factory=dict)
    
    trust_fund_solvency_year: Optional[int] = None
    estimated_year_deficit: Optional[float] = None


@dataclass
class SpendingMechanics:
    """Extracted discretionary spending reform mechanics."""
    defense_spending_change: Optional[float] = None  # percentage change (e.g., 0.05 = +5%)
    defense_spending_cap: Optional[float] = None  # absolute cap in billions
    
    nondefense_discretionary_change: Optional[float] = None
    nondefense_categories: Dict[str, float] = field(default_factory=dict)  # e.g., {"education": 0.05, "infrastructure": 0.10}
    
    infrastructure_spending: Optional[float] = None
    education_spending: Optional[float] = None
    research_spending: Optional[float] = None
    medicaid_expansion: bool = False
    medicaid_block_grant: bool = False
    medicaid_per_capita_cap: bool = False
    medicaid_fmap_change: Optional[float] = None  # percentage point change
    medicaid_waivers: bool = False
    national_health_fund: bool = False
    medicare_transfer: bool = False
    social_security_health_transfer: bool = False
    payroll_to_health_fund: bool = False
    
    spending_growth_rate: Optional[float] = None
    inflation_adjustment: Optional[float] = None
    
    budget_caps_enabled: bool = False
    budget_cap_levels: Dict[str, float] = field(default_factory=dict)


@dataclass
class PolicyMechanics:
    """Complete extracted policy mechanics - unified extraction for all domains."""
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
    
    # Tax reform mechanics (extracted for all policies)
    tax_mechanics: Optional[TaxMechanics] = None
    
    # Social Security mechanics (extracted for all policies)
    social_security_mechanics: Optional[SocialSecurityMechanics] = None
    
    # Spending reform mechanics (extracted for all policies)
    spending_mechanics: Optional[SpendingMechanics] = None
    
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
        """Generic healthcare extraction path without USGHA assumptions.
        
        Enhanced to extract all mechanics categories:
        - Funding mechanisms (payroll, premiums, taxes, etc.)
        - Tax mechanics (payroll tax cap, FTT, excise, tariffs, EITC)
        - Social Security mechanics (grandfathering, integration, FICA offset)
        - Spending mechanics (health fund, program consolidation, circuit breakers)
        """
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
        mechanics.zero_out_of_pocket = bool(re.search(r'no\s+(?:deductibles?|copay(?:ment)?s?|premiums?)|zero[- ]out[- ]of[- ]pocket', text, re.IGNORECASE))
        mechanics.universal_coverage = bool(re.search(r'(all\s+residents|universal\s+coverage|single[- ]payer|all\s+(?:qualified\s+)?individuals)', text, re.IGNORECASE))

        spending_target = PolicyMechanicsExtractor._extract_spending_target(text)
        if spending_target:
            mechanics.target_spending_pct_gdp = spending_target.get("target_pct", None)
            mechanics.target_spending_year = spending_target.get("target_year", None)

        # ==========================================================================
        # ENHANCED: Extract domain-specific mechanics (tax, SS, spending)
        # ==========================================================================
        # Tax mechanics extraction
        mechanics.tax_mechanics = PolicyMechanicsExtractor._extract_tax_mechanics(text)
        
        # Social Security mechanics extraction
        mechanics.social_security_mechanics = PolicyMechanicsExtractor._extract_social_security_mechanics(text)
        
        # Spending mechanics extraction (includes Medicaid, health fund, circuit breakers)
        mechanics.spending_mechanics = PolicyMechanicsExtractor._extract_spending_mechanics(text)

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
            except (ValueError, TypeError) as e:
                # Skip invalid milestone entries (bad type conversion or missing required field)
                import logging
                logging.getLogger(__name__).debug(f"Skipping invalid timeline milestone: {e}")
                continue

        # Policy targets and flags
        mechanics.target_spending_pct_gdp = data.get("target_spending_pct_gdp")
        mechanics.target_spending_year = data.get("target_spending_year")
        mechanics.zero_out_of_pocket = bool(data.get("zero_out_of_pocket", False))
        mechanics.universal_coverage = bool(data.get("universal_coverage", False))
        
        # Domain-specific mechanics
        tax_data = data.get("tax_mechanics") or None
        if tax_data:
            mechanics.tax_mechanics = TaxMechanics(
                wealth_tax_rate=tax_data.get("wealth_tax_rate"),
                wealth_tax_threshold=tax_data.get("wealth_tax_threshold"),
                wealth_tax_tiers=tax_data.get("wealth_tax_tiers", {}),
                consumption_tax_rate=tax_data.get("consumption_tax_rate"),
                consumption_tax_exemptions=tax_data.get("consumption_tax_exemptions", []),
                consumption_tax_rebate=tax_data.get("consumption_tax_rebate"),
                carbon_tax_per_ton=tax_data.get("carbon_tax_per_ton"),
                carbon_tax_annual_increase=tax_data.get("carbon_tax_annual_increase"),
                carbon_revenue_allocation=tax_data.get("carbon_revenue_allocation", {}),
                financial_transaction_tax_rate=tax_data.get("financial_transaction_tax_rate"),
                income_tax_changes=tax_data.get("income_tax_changes", {}),
                corporate_tax_rate=tax_data.get("corporate_tax_rate"),
                payroll_tax_rate=tax_data.get("payroll_tax_rate"),
                tax_revenue_billions=tax_data.get("tax_revenue_billions"),
                estimated_tax_revenue_growth=tax_data.get("estimated_tax_revenue_growth")
            )
        
        ss_data = data.get("social_security_mechanics") or None
        if ss_data:
            mechanics.social_security_mechanics = SocialSecurityMechanics(
                payroll_tax_rate=ss_data.get("payroll_tax_rate"),
                payroll_tax_cap_change=ss_data.get("payroll_tax_cap_change"),
                payroll_tax_cap_increase=ss_data.get("payroll_tax_cap_increase"),
                full_retirement_age=ss_data.get("full_retirement_age"),
                full_retirement_age_change=ss_data.get("full_retirement_age_change"),
                benefit_formula_changes=ss_data.get("benefit_formula_changes", {}),
                cola_adjustments=ss_data.get("cola_adjustments"),
                means_testing_threshold=ss_data.get("means_testing_threshold"),
                means_testing_enabled=bool(ss_data.get("means_testing_enabled", False)),
                early_claiming_reduction=ss_data.get("early_claiming_reduction"),
                delayed_claiming_credit=ss_data.get("delayed_claiming_credit"),
                demographic_assumptions=ss_data.get("demographic_assumptions", {}),
                trust_fund_solvency_year=ss_data.get("trust_fund_solvency_year"),
                estimated_year_deficit=ss_data.get("estimated_year_deficit")
            )
        
        spending_data = data.get("spending_mechanics") or None
        if spending_data:
            mechanics.spending_mechanics = SpendingMechanics(
                defense_spending_change=spending_data.get("defense_spending_change"),
                defense_spending_cap=spending_data.get("defense_spending_cap"),
                nondefense_discretionary_change=spending_data.get("nondefense_discretionary_change"),
                nondefense_categories=spending_data.get("nondefense_categories", {}),
                infrastructure_spending=spending_data.get("infrastructure_spending"),
                education_spending=spending_data.get("education_spending"),
                research_spending=spending_data.get("research_spending"),
                medicaid_expansion=bool(spending_data.get("medicaid_expansion", False)),
                medicaid_block_grant=bool(spending_data.get("medicaid_block_grant", False)),
                medicaid_per_capita_cap=bool(spending_data.get("medicaid_per_capita_cap", False)),
                medicaid_fmap_change=spending_data.get("medicaid_fmap_change"),
                medicaid_waivers=bool(spending_data.get("medicaid_waivers", False)),
                national_health_fund=bool(spending_data.get("national_health_fund", False)),
                medicare_transfer=bool(spending_data.get("medicare_transfer", False)),
                social_security_health_transfer=bool(spending_data.get("social_security_health_transfer", False)),
                payroll_to_health_fund=bool(spending_data.get("payroll_to_health_fund", False)),
                spending_growth_rate=spending_data.get("spending_growth_rate"),
                inflation_adjustment=spending_data.get("inflation_adjustment"),
                budget_caps_enabled=bool(spending_data.get("budget_caps_enabled", False)),
                budget_cap_levels=spending_data.get("budget_cap_levels", {})
            )

        # Optional metadata
        mechanics.source_sections = data.get("source_sections", {}) or {}
        mechanics.confidence_score = float(data.get("confidence_score", 0.0)) if data.get("confidence_score") is not None else 0.0

        return mechanics
    
    @staticmethod
    def _extract_funding_section_6(text: str) -> List[FundingMechanism]:
        """Extract funding mechanisms from Section 6."""
        mechanisms: List[FundingMechanism] = []
        
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
        """Generic funding extraction without USGHA defaults.
        
        Enhanced to detect USGHA-style funding patterns:
        - 15% combined payroll tax cap with allocation breakdown
        - Medicare/Medicaid/SS/CHIP program consolidation into health fund
        - Dollar-for-dollar offset against existing payroll taxes (3101/3111)
        - Health fund allocation percentages (45% health, 27.5% federal, 27.5% state)
        """
        mechanisms: List[FundingMechanism] = []

        # ==========================================================================
        # ENHANCED PAYROLL TAX DETECTION (USGHA-style)
        # ==========================================================================
        # Pattern 1: "payroll tax rate...capped at X percent" - most reliable
        payroll_cap_match = re.search(
            r'(?:total\s+)?(?:combined\s+)?payroll\s+(?:tax|contribution)\s+rate[^.]{0,100}?(?:cap(?:ped)?|shall\s+(?:be|not)\s+exceed)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent',
            text,
            re.IGNORECASE
        )
        
        # Pattern 2: "capped at X percent" preceding or following payroll mention
        if not payroll_cap_match:
            payroll_cap_match = re.search(
                r'(?:cap(?:ped)?|maximum|limit(?:ed)?)[^.]{0,150}?(?:payroll|combined)[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent',
                text,
                re.IGNORECASE
            )
        if not payroll_cap_match:
            payroll_cap_match = re.search(
                r'(?:payroll|combined)[^.]{0,150}?(?:cap(?:ped)?|maximum|limit(?:ed)?)[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent',
                text,
                re.IGNORECASE
            )
        
        # Pattern 3: Look for specific USGHA language "shall be capped at 15 percent"
        if not payroll_cap_match:
            payroll_cap_match = re.search(
                r'shall\s+be\s+capped\s+at\s+(\d+(?:\.\d+)?)\s*percent',
                text,
                re.IGNORECASE
            )
        
        # Extract allocation breakdown if present (e.g., "Of this 15 percent, 45 percent shall be dedicated...")
        health_fund_allocation = None
        federal_allocation = None
        state_allocation = None
        allocation_match = re.search(
            r'(?:of\s+this|from\s+this)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent\s+(?:shall\s+be\s+)?(?:dedicated|allocated)[^.]{0,100}?(?:health|national\s+health|trust\s+fund)',
            text,
            re.IGNORECASE
        )
        if allocation_match:
            health_fund_allocation = float(allocation_match.group(2)) / 100
        
        # Look for federal/state allocation breakdown
        alloc_breakdown = re.search(
            r'(\d+(?:\.\d+)?)\s*percent\s+(?:allocated\s+)?to\s+(?:previous\s+)?federal\s+(?:tax\s+)?allocations?\s+and\s+(\d+(?:\.\d+)?)\s*percent\s+to\s+(?:previous\s+)?state',
            text,
            re.IGNORECASE
        )
        if alloc_breakdown:
            federal_allocation = float(alloc_breakdown.group(1)) / 100
            state_allocation = float(alloc_breakdown.group(2)) / 100
        
        if payroll_cap_match:
            rate = float(payroll_cap_match.group(1))
            if 5 <= rate <= 25:  # Validate plausible payroll tax range
                # Convert payroll rate to GDP estimate
                # Wages are ~53% of GDP, so 15% payroll ≈ 15% * 53% ≈ 7.95% GDP
                estimated_gdp_pct = rate * 0.53
                
                # Build detailed description
                desc_parts = [f"{rate}% combined payroll tax cap (~{estimated_gdp_pct:.1f}% GDP)"]
                if health_fund_allocation:
                    desc_parts.append(f"{health_fund_allocation*100:.1f}% to health fund")
                if federal_allocation:
                    desc_parts.append(f"{federal_allocation*100:.1f}% to federal allocations")
                if state_allocation:
                    desc_parts.append(f"{state_allocation*100:.1f}% to state allocations")
                
                # Create funding mechanism with allocation metadata
                fm = FundingMechanism(
                    source_type="payroll_tax",
                    percentage_rate=rate,
                    percentage_gdp=estimated_gdp_pct,
                    description=" | ".join(desc_parts)
                )
                
                # Store allocation details in conditions for downstream use
                if health_fund_allocation:
                    fm.conditions.append(f"health_fund_allocation:{health_fund_allocation}")
                if federal_allocation:
                    fm.conditions.append(f"federal_allocation:{federal_allocation}")
                if state_allocation:
                    fm.conditions.append(f"state_allocation:{state_allocation}")
                
                mechanisms.append(fm)
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
        
        # ==========================================================================
        # DOLLAR-FOR-DOLLAR OFFSET DETECTION (sections 3101/3111)
        # ==========================================================================
        offset_match = re.search(
            r'(?:reduced|offset)\s+(?:dollar[- ]for[- ]dollar|one[- ]for[- ]one)[^.]{0,100}?(?:section[s]?\s+)?(?:3101|3111|existing\s+(?:payroll|social\s+security))',
            text,
            re.IGNORECASE
        )
        if offset_match:
            mechanisms.append(FundingMechanism(
                source_type="payroll_offset",
                description="Dollar-for-dollar offset against existing Social Security/Medicare payroll taxes (3101/3111)",
                conditions=["revenue_neutral", "offset_existing_payroll"]
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

        # National health fund / unified trust for Medicare-Medicaid-social security payroll redirection
        if re.search(r'national\s+health\s+fund', text, re.IGNORECASE):
            mechanisms.append(FundingMechanism(
                source_type="national_health_fund",
                description="National Health Fund (consolidated Medicare/Medicaid/payroll financing)"
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
    def _extract_tax_mechanics(text: str) -> TaxMechanics:
        """Extract tax reform mechanics from policy text.
        
        Enhanced to detect USGHA-style tax mechanics:
        - Payroll tax cap (e.g., 15% combined cap with allocations)
        - Financial transaction tax (1% on trades over $10M)
        - Excise tax reallocation (1% of existing excise taxes)
        - Import tariff allocation (12% of tariffs to health fund)
        - Automatic tax reductions on surplus triggers
        - EITC expansion for low earners
        """
        mechanics = TaxMechanics()
        
        # ==========================================================================
        # ENHANCED: USGHA-style Payroll Tax Cap Detection
        # ==========================================================================
        # Pattern 1: "combined payroll tax rate...capped at X percent"
        payroll_cap_patterns = [
            r'(?:total\s+)?(?:combined\s+)?payroll\s+(?:tax|contribution)\s+rate[^.]{0,100}?(?:capped|shall\s+(?:be|not)\s+exceed)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent',
            r'payroll\s+(?:tax|contribution)[^.]{0,50}?cap(?:ped)?\s+at\s+(\d+(?:\.\d+)?)\s*%',
            r'cap\s+(?:the\s+)?(?:combined\s+)?payroll\s+(?:tax|contribution)[^.]{0,50}?(\d+(?:\.\d+)?)\s*%',
        ]
        for pattern in payroll_cap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mechanics.payroll_tax_rate = float(match.group(1)) / 100
                break
        
        # Pattern 2: Allocation breakdown "Of this X percent, Y percent shall be dedicated..."
        allocation_pattern = re.search(
            r'(?:of\s+this|from\s+this)[^.]{0,30}?(\d+(?:\.\d+)?)\s*percent[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent[^.]{0,100}?(?:dedicated|allocated)[^.]{0,100}(?:health|national\s+health|trust\s+fund)',
            text,
            re.IGNORECASE
        )
        if allocation_pattern:
            # Store in income_tax_changes as allocation metadata
            mechanics.income_tax_changes['payroll_cap_rate'] = float(allocation_pattern.group(1)) / 100
            mechanics.income_tax_changes['health_fund_allocation'] = float(allocation_pattern.group(2)) / 100
        
        # Pattern 3: Federal/state allocation split "27.5 percent...federal...27.5 percent...state"
        fed_state_pattern = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?(?:federal|previous\s+federal)[^.]{0,80}?(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?(?:state|previous\s+state)',
            text,
            re.IGNORECASE
        )
        if fed_state_pattern:
            mechanics.income_tax_changes['federal_allocation'] = float(fed_state_pattern.group(1)) / 100
            mechanics.income_tax_changes['state_allocation'] = float(fed_state_pattern.group(2)) / 100
        
        # ==========================================================================
        # ENHANCED: Financial Transaction Tax (USGHA: 1% on trades >$10M)
        # ==========================================================================
        ftt_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*financial\s+transaction\s+tax',
            r'financial\s+transaction\s+tax[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:tax|reallocation)[^.]{0,50}?trades?\s+(?:exceeding|over|above)',
            r'transaction\s+tax[^.]{0,80}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
        ]
        for pattern in ftt_patterns:
            ftt_match = re.search(pattern, text, re.IGNORECASE)
            if ftt_match:
                mechanics.financial_transaction_tax_rate = float(ftt_match.group(1)) / 100
                break
        
        # FTT threshold detection (e.g., "$10 million")
        ftt_threshold = re.search(
            r'(?:transaction\s+tax|trades?)[^.]{0,80}?(?:exceeding|over|above)\s*\$?\s*(\d+(?:,\d{3})*)\s*(?:million|m)',
            text,
            re.IGNORECASE
        )
        if ftt_threshold:
            threshold_str = ftt_threshold.group(1).replace(',', '')
            mechanics.income_tax_changes['ftt_threshold'] = float(threshold_str) * 1_000_000
        
        # ==========================================================================
        # ENHANCED: Excise Tax Reallocation (USGHA: "1% of existing excise taxes")
        # ==========================================================================
        excise_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)[^.]{0,50}?(?:of\s+)?(?:existing\s+)?excise\s+tax(?:es)?',
            r'excise\s+tax(?:es)?[^.]{0,100}?(?:reallocat|redirect|transfer)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
            r'(?:reallocat|redirect)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)[^.]{0,50}?excise',
        ]
        for pattern in excise_patterns:
            excise_match = re.search(pattern, text, re.IGNORECASE)
            if excise_match:
                rate = float(excise_match.group(1)) / 100
                mechanics.income_tax_changes['excise_tax_reallocation'] = rate
                break
        
        # ==========================================================================
        # ENHANCED: Import Tariff Allocation (USGHA: "12 percent of import tariffs")
        # ==========================================================================
        tariff_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*(?:of\s+)?import\s+tariff',
            r'import\s+tariff[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
            r'tariff[^.]{0,50}?(?:allocat|redirect|transfer)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
        ]
        for pattern in tariff_patterns:
            tariff_match = re.search(pattern, text, re.IGNORECASE)
            if tariff_match:
                rate = float(tariff_match.group(1)) / 100
                mechanics.income_tax_changes['import_tariff_allocation'] = rate
                break
        
        # ==========================================================================
        # ENHANCED: Automatic Tax Reductions on Surplus (USGHA Circuit Breaker)
        # ==========================================================================
        surplus_tax_cut = re.search(
            r'surplus(?:es)?[^.]{0,100}?(?:trigger|automatic)[^.]{0,100}?tax\s+(?:reduction|cut)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|percentage)',
            text,
            re.IGNORECASE
        )
        if surplus_tax_cut:
            mechanics.income_tax_changes['surplus_tax_reduction'] = float(surplus_tax_cut.group(1)) / 100
        
        # Pattern: "1 percentage point cut to top marginal income tax rate per surplus"
        marginal_cut = re.search(
            r'(\d+(?:\.\d+)?)\s*percentage\s+point\s+cut[^.]{0,50}?(?:top\s+)?(?:marginal\s+)?income\s+tax',
            text,
            re.IGNORECASE
        )
        if marginal_cut:
            mechanics.income_tax_changes['marginal_cut_per_surplus'] = float(marginal_cut.group(1)) / 100
        
        # ==========================================================================
        # ENHANCED: EITC Expansion (USGHA: "50 percent rebates to low earners via EITC")
        # ==========================================================================
        eitc_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s*rebate[^.]{0,50}?(?:low\s+earner|eitc|earned\s+income)',
            r'eitc[^.]{0,50}?(?:expan|rebate|credit)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
            r'earned\s+income\s+(?:tax\s+)?credit[^.]{0,80}?(?:expan|increas)',
        ]
        for pattern in eitc_patterns:
            eitc_match = re.search(pattern, text, re.IGNORECASE)
            if eitc_match:
                if eitc_match.groups():
                    mechanics.income_tax_changes['eitc_rebate_rate'] = float(eitc_match.group(1)) / 100
                mechanics.income_tax_changes['eitc_expansion'] = True
                break
        
        # ==========================================================================
        # ENHANCED: Dollar-for-Dollar Offset Detection
        # ==========================================================================
        if re.search(r'dollar[- ]for[- ]dollar', text, re.IGNORECASE):
            mechanics.income_tax_changes['dollar_for_dollar_offset'] = True
        
        # Sections 3101/3111 offset (Social Security/Medicare taxes)
        if re.search(r'section[s]?\s+3101\s*(?:and|&|/)\s*3111', text, re.IGNORECASE):
            mechanics.income_tax_changes['replaces_fica'] = True
        
        # ==========================================================================
        # STANDARD: Wealth tax extraction
        # ==========================================================================
        wealth_rate = re.search(r'wealth\s+tax[^.]*?(\d+(?:\.\d+)?)\s*%', text, re.IGNORECASE)
        if wealth_rate:
            mechanics.wealth_tax_rate = float(wealth_rate.group(1)) / 100
        
        wealth_threshold = re.search(
            r'wealth\s+(?:tax|value).*?(?:threshold|exemption|above)\s*(?:of)?\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|m|b)?',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if wealth_threshold:
            threshold_str = wealth_threshold.group(1).replace(',', '')
            try:
                threshold_val = float(threshold_str)
                # Convert to dollars if not already
                if 'm' in wealth_threshold.group(0).lower() or (threshold_val < 1000 and 'billion' not in wealth_threshold.group(0).lower()):
                    threshold_val *= 1_000_000
                elif 'b' in wealth_threshold.group(0).lower() or 'billion' in wealth_threshold.group(0).lower():
                    threshold_val *= 1_000_000_000
                mechanics.wealth_tax_threshold = threshold_val
            except ValueError:
                pass
        
        # Extract wealth tax tiers
        tier_matches = re.findall(
            r'tier\s*(\d+)[^.]*?(\d+(?:\.\d+)?)\s*%(?:[^.]*?(?:on|above|threshold))?',
            text,
            re.IGNORECASE
        )
        for tier_num, rate in tier_matches:
            mechanics.wealth_tax_tiers[f"tier_{tier_num}_rate"] = float(rate) / 100
        
        # Consumption tax extraction
        consumption_rate = re.search(
            r'(?:consumption|vat|sales)\s+tax[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if consumption_rate:
            mechanics.consumption_tax_rate = float(consumption_rate.group(1)) / 100
        
        # Consumption tax exemptions
        exemptions = re.findall(
            r'exempt(?:ion)?[^.]*?(?:food|medicine|housing|medical|prescription)',
            text,
            re.IGNORECASE
        )
        if exemptions:
            if re.search(r'(?:food|groceries)', text, re.IGNORECASE):
                mechanics.consumption_tax_exemptions.append("food")
            if re.search(r'(?:medicine|prescription|drug)', text, re.IGNORECASE):
                mechanics.consumption_tax_exemptions.append("medicine")
            if re.search(r'(?:housing|rent|mortgage)', text, re.IGNORECASE):
                mechanics.consumption_tax_exemptions.append("housing")
        
        # Consumption tax rebate
        rebate = re.search(
            r'rebate[^.]*?\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:per|annual)',
            text,
            re.IGNORECASE
        )
        if rebate:
            mechanics.consumption_tax_rebate = float(rebate.group(1).replace(',', ''))
        
        # Carbon tax extraction
        carbon_rate = re.search(
            r'carbon\s+(?:tax|price)[^.]*?\$?\s*(\d+(?:\.\d+)?)\s*(?:per|/)\s*(?:ton|tonne)',
            text,
            re.IGNORECASE
        )
        if carbon_rate:
            mechanics.carbon_tax_per_ton = float(carbon_rate.group(1))
        
        carbon_increase = re.search(
            r'(?:increase|escalate)[^.]*?\$?\s*(\d+(?:\.\d+)?)\s*(?:per|annually)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if carbon_increase:
            mechanics.carbon_tax_annual_increase = float(carbon_increase.group(1))
        
        # Carbon revenue allocation
        dividend_match = re.search(r'(?:dividend|rebate)[^.]*?(\d+)\s*%', text, re.IGNORECASE)
        if dividend_match:
            mechanics.carbon_revenue_allocation['dividend'] = float(dividend_match.group(1)) / 100
        
        transition_match = re.search(
            r'(?:transition|affected)\s+(?:industries|workers|communities)[^.]*?(\d+)\s*%',
            text,
            re.IGNORECASE
        )
        if transition_match:
            mechanics.carbon_revenue_allocation['transition_assistance'] = float(transition_match.group(1)) / 100
        
        # Financial transaction tax
        ftt_rate = re.search(
            r'(?:financial\s+transaction|tobin)\s+tax[^.]*?(\d+(?:\.\d+)?)\s*(?:%|basis\s+point)',
            text,
            re.IGNORECASE
        )
        if ftt_rate:
            rate_str = ftt_rate.group(1)
            if 'basis' in ftt_rate.group(0).lower():
                mechanics.financial_transaction_tax_rate = float(rate_str) / 10000  # basis points to decimal
            else:
                mechanics.financial_transaction_tax_rate = float(rate_str) / 100
        
        # Income tax changes
        income_rate = re.search(
            r'(?:income|marginal)\s+tax\s+rate[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if income_rate:
            mechanics.income_tax_changes['top_rate'] = float(income_rate.group(1)) / 100
        
        # Corporate tax rate
        corporate_rate = re.search(
            r'corporate\s+(?:income\s+)?tax\s+rate[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if corporate_rate:
            mechanics.corporate_tax_rate = float(corporate_rate.group(1)) / 100
        
        # Payroll tax rate
        payroll_rate = re.search(
            r'payroll\s+tax[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if payroll_rate:
            mechanics.payroll_tax_rate = float(payroll_rate.group(1)) / 100
        
        # Total tax revenue
        revenue = re.search(
            r'(?:raise|generate|estimated)\s+(?:revenue|revenues|funds)[^.]*?\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:billion|trillion)',
            text,
            re.IGNORECASE
        )
        if revenue:
            amount_str = revenue.group(1).replace(',', '')
            amount = float(amount_str)
            if 'trillion' in revenue.group(0).lower():
                amount *= 1000
            mechanics.tax_revenue_billions = amount
        
        return mechanics
    
    @staticmethod
    def _extract_social_security_mechanics(text: str) -> SocialSecurityMechanics:
        """Extract Social Security reform mechanics from policy text.
        
        Enhanced to detect USGHA-style Social Security integration:
        - Grandfathered existing accounts with benefits payable under current law
        - Integration with National Health and Longevity Trust Fund
        - Payroll contribution allocation to SS purposes
        - Fiscal bridge fund for transition overlap
        - Dollar-for-dollar offset against sections 3101/3111
        """
        mechanics = SocialSecurityMechanics()
        
        # ==========================================================================
        # ENHANCED: USGHA-style Social Security Grandfathering
        # ==========================================================================
        # Pattern 1: "Existing Social Security accounts are grandfathered"
        grandfathering_patterns = [
            r'(?:existing\s+)?social\s+security\s+(?:accounts?|benefits?)[^.]{0,50}?grandfathered',
            r'grandfathered[^.]{0,50}?social\s+security',
            r'social\s+security[^.]{0,80}?(?:payable\s+(?:as|under)\s+)?current\s+law',
            r'(?:preserve|maintain|protect)[^.]{0,50}?(?:existing\s+)?social\s+security\s+(?:benefits?|accounts?)',
        ]
        for pattern in grandfathering_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                mechanics.benefit_formula_changes['grandfathered'] = True
                mechanics.benefit_formula_changes['current_law_preserved'] = True
                break
        
        # ==========================================================================
        # ENHANCED: Integration with National Health Trust Fund (USGHA-style)
        # ==========================================================================
        # Pattern 1: "funding shall derive from the National Health and Longevity Trust Fund"
        health_fund_integration_patterns = [
            r'funding\s+shall\s+derive\s+from[^.]{0,50}?(?:National\s+Health|Trust\s+Fund)',
            r'social\s+security[^.]{0,100}?(?:National\s+Health|Trust\s+Fund)',
            r'(?:National\s+Health|Trust\s+Fund)[^.]{0,100}?social\s+security',
            r'integrat(?:e|ed|ion)\s+(?:of\s+)?social\s+security',
        ]
        for pattern in health_fund_integration_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                mechanics.benefit_formula_changes['health_fund_integration'] = True
                break
        
        # Pattern 2: "45 percent...dedicated to...integrated Social Security purposes"
        ss_allocation = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,150}?(?:dedicated|allocated)[^.]{0,100}?(?:integrat(?:e|ed))?\s*social\s+security\s+purposes',
            text,
            re.IGNORECASE
        )
        if ss_allocation:
            mechanics.benefit_formula_changes['health_fund_integration'] = True
            mechanics.benefit_formula_changes['integrated_allocation_pct'] = float(ss_allocation.group(1)) / 100
        
        # ==========================================================================
        # ENHANCED: Fiscal Bridge Fund (USGHA transition mechanism)
        # ==========================================================================
        # Pattern: "fiscal bridge fund equivalent to 0.1 percent"
        bridge_fund_patterns = [
            r'fiscal\s+bridge\s+fund[^.]{0,80}?(\d+(?:\.\d+)?)\s*percent',
            r'bridge\s+fund[^.]{0,80}?(?:transition|overlap|payroll\s+shift)',
            r'(?:transition|overlap)[^.]{0,50}?bridge\s+fund',
        ]
        for pattern in bridge_fund_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mechanics.benefit_formula_changes['fiscal_bridge_fund'] = True
                if match.groups():
                    mechanics.benefit_formula_changes['bridge_fund_pct'] = float(match.group(1)) / 100
                break
        
        # ==========================================================================
        # ENHANCED: Dollar-for-Dollar Offset (sections 3101/3111)
        # ==========================================================================
        # Pattern: "reduced dollar-for-dollar by existing sections 3101/3111 taxes"
        offset_patterns = [
            r'dollar[- ]for[- ]dollar[^.]{0,80}?section[s]?\s+3101',
            r'section[s]?\s+3101\s*(?:and|&|/)\s*3111[^.]{0,80}?(?:offset|replace|reduce)',
            r'(?:offset|replace|reduce)[^.]{0,80}?section[s]?\s+3101\s*(?:and|&|/)\s*3111',
            r'fully\s+replace\s+(?:and\s+)?offset[^.]{0,80}?(?:3101|social\s+security)',
        ]
        for pattern in offset_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                mechanics.payroll_tax_cap_change = "integrated_offset"
                mechanics.benefit_formula_changes['fica_offset'] = True
                break
        
        # ==========================================================================
        # ENHANCED: Payroll Tax Cap Detection (USGHA-style: capped at 15%)
        # ==========================================================================
        payroll_cap_patterns = [
            r'(?:total\s+)?(?:combined\s+)?payroll\s+(?:tax|contribution)\s+rate[^.]{0,100}?(?:capped|shall\s+(?:be|not)\s+exceed)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent',
            r'payroll\s+(?:tax|contribution)[^.]{0,50}?cap(?:ped)?\s+at\s+(\d+(?:\.\d+)?)\s*%',
        ]
        for pattern in payroll_cap_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                mechanics.payroll_tax_rate = float(match.group(1)) / 100
                mechanics.payroll_tax_cap_change = "capped"
                break
        
        # Fallback: Standard payroll tax rate detection
        if not mechanics.payroll_tax_rate:
            payroll_tax = re.search(
                r'payroll\s+tax[^.]*?(\d+(?:\.\d+)?)\s*%',
                text,
                re.IGNORECASE
            )
            if payroll_tax:
                mechanics.payroll_tax_rate = float(payroll_tax.group(1)) / 100
        
        # ==========================================================================
        # ENHANCED: Payroll Tax Allocation Breakdown (45%/27.5%/27.5%)
        # ==========================================================================
        allocation_breakdown = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,100}?(?:health|trust\s+fund)[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?federal[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?state',
            text,
            re.IGNORECASE
        )
        if allocation_breakdown:
            mechanics.benefit_formula_changes['health_allocation_pct'] = float(allocation_breakdown.group(1)) / 100
            mechanics.benefit_formula_changes['federal_allocation_pct'] = float(allocation_breakdown.group(2)) / 100
            mechanics.benefit_formula_changes['state_allocation_pct'] = float(allocation_breakdown.group(3)) / 100
        
        # ==========================================================================
        # ENHANCED: Surplus Dividends to SS
        # ==========================================================================
        surplus_dividend = re.search(
            r'surplus\s+dividend[^.]{0,100}?(?:social\s+security|allocated)',
            text,
            re.IGNORECASE
        )
        if surplus_dividend:
            mechanics.benefit_formula_changes['surplus_dividends'] = True
        
        # ==========================================================================
        # STANDARD: Payroll tax cap changes (traditional)
        # ==========================================================================
        if not mechanics.payroll_tax_cap_change:
            if re.search(r'(?:remove|eliminate|raise)\s+(?:the\s+)?payroll\s+tax\s+cap', text, re.IGNORECASE):
                mechanics.payroll_tax_cap_change = "remove_cap"
            elif re.search(r'raise.*payroll\s+(?:tax\s+)?cap', text, re.IGNORECASE):
                mechanics.payroll_tax_cap_change = "increase_cap"
                cap_increase = re.search(
                    r'cap.*?\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*k',
                    text,
                    re.IGNORECASE
                )
                if cap_increase:
                    mechanics.payroll_tax_cap_increase = float(cap_increase.group(1).replace(',', '')) * 1000
        
        # ==========================================================================
        # STANDARD: Full Retirement Age changes
        # ==========================================================================
        fra = re.search(
            r'(?:full\s+retirement\s+age|fra)[^.]*?(?:raise|increase)\s+to\s+(\d+)',
            text,
            re.IGNORECASE
        )
        if fra:
            mechanics.full_retirement_age = int(fra.group(1))
        
        fra_change = re.search(
            r'(?:increase|raise)\s+(?:the\s+)?(?:full\s+retirement\s+age|fra)\s+by\s+(\d+)',
            text,
            re.IGNORECASE
        )
        if fra_change:
            mechanics.full_retirement_age_change = int(fra_change.group(1))
        
        # ==========================================================================
        # STANDARD: Benefit formula changes
        # ==========================================================================
        if re.search(r'adjust\s+(?:benefit\s+)?formula', text, re.IGNORECASE):
            mechanics.benefit_formula_changes['adjusted'] = True
        
        # ==========================================================================
        # STANDARD: COLA adjustments
        # ==========================================================================
        if re.search(r'chained\s+cpi', text, re.IGNORECASE):
            mechanics.cola_adjustments = "chained_cpi"
        elif re.search(r'cola|cost[- ]of[- ]living', text, re.IGNORECASE):
            mechanics.cola_adjustments = "maintained"
        
        # ==========================================================================
        # STANDARD: Means testing
        # ==========================================================================
        if re.search(r'means\s+test', text, re.IGNORECASE):
            mechanics.means_testing_enabled = True
            threshold = re.search(
                r'means\s+test[^.]*?\$?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*k',
                text,
                re.IGNORECASE
            )
            if threshold:
                mechanics.means_testing_threshold = float(threshold.group(1).replace(',', '')) * 1000
        
        # ==========================================================================
        # STANDARD: Early/delayed claiming adjustments
        # ==========================================================================
        early = re.search(
            r'(?:early|age\s+62)\s+claiming[^.]*?(\d+)\s*%',
            text,
            re.IGNORECASE
        )
        if early:
            mechanics.early_claiming_reduction = float(early.group(1)) / 100
        
        delayed = re.search(
            r'(?:delay|age\s+70)\s+claiming[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if delayed:
            mechanics.delayed_claiming_credit = float(delayed.group(1)) / 100
        
        # ==========================================================================
        # STANDARD: Trust fund solvency
        # ==========================================================================
        solvency = re.search(
            r'solvency[^.]*?(\d{4})',
            text,
            re.IGNORECASE
        )
        if solvency:
            mechanics.trust_fund_solvency_year = int(solvency.group(1))
        
        return mechanics
    
    @staticmethod
    def _extract_spending_mechanics(text: str) -> SpendingMechanics:
        """Extract discretionary spending reform mechanics from policy text.
        
        Enhanced to detect USGHA-style program consolidation:
        - National Health Fund / National Health and Longevity Trust Fund
        - Medicare/Medicaid/CHIP/VA/ACA redirection into unified fund
        - Social Security health integration (payroll tax allocation)
        - Program consolidation (SNAP, WIC, school lunch into health fund)
        """
        mechanics = SpendingMechanics()
        
        # Defense spending changes - look for percentage changes
        defense_pct = re.search(
            r'defense.*?([+-]?\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if defense_pct:
            mechanics.defense_spending_change = float(defense_pct.group(1)) / 100
        
        # Infrastructure spending - more flexible pattern
        infra_patterns = [
            r'infrastructure[^$]*?\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t)',
            r'\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t).*?infrastructure',
        ]
        for pattern in infra_patterns:
            infrastructure = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if infrastructure:
                amount_str = infrastructure.group(1).replace(',', '')
                amount = float(amount_str)
                if 'trillion' in infrastructure.group(0).lower() or 't' in infrastructure.group(0)[-1].lower():
                    amount *= 1000
                mechanics.infrastructure_spending = amount
                break
        
        # Education spending - more flexible pattern
        edu_patterns = [
            r'(?:education|schools?|k[-]?12)[^$]*?\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t)',
            r'\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t).*?(?:education|schools?)',
        ]
        for pattern in edu_patterns:
            education = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if education:
                amount_str = education.group(1).replace(',', '')
                amount = float(amount_str)
                if 'trillion' in education.group(0).lower() or 't' in education.group(0)[-1].lower():
                    amount *= 1000
                mechanics.education_spending = amount
                break
        
        # Research spending
        research_patterns = [
            r'(?:research|science|r[&\-]d)[^$]*?\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t)',
            r'\$\s*(\d+(?:,\d{3})*)\s*(?:billion|b|trillion|t).*?(?:research|science)',
        ]
        for pattern in research_patterns:
            research = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if research:
                amount_str = research.group(1).replace(',', '')
                amount = float(amount_str)
                if 'trillion' in research.group(0).lower() or 't' in research.group(0)[-1].lower():
                    amount *= 1000
                mechanics.research_spending = amount
                break

        # ==========================================================================
        # ENHANCED: National Health Fund / Trust Fund Detection (USGHA-style)
        # ==========================================================================
        # Detect "National Health and Longevity Trust Fund" or "National Health Fund"
        health_fund_patterns = [
            r'national\s+health\s+(?:and\s+longevity\s+)?trust\s+fund',
            r'national\s+health\s+fund',
            r'unified\s+(?:health|healthcare)\s+fund',
            r'single[- ]payer\s+(?:trust\s+)?fund',
            r'health\s+trust\s+fund',
        ]
        for pattern in health_fund_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                mechanics.national_health_fund = True
                break

        # ==========================================================================
        # ENHANCED: Medicare/Medicaid/CHIP/VA/ACA Redirection Detection
        # ==========================================================================
        # Pattern 1: Explicit "Redirection of existing federal health expenditures (Medicare, Medicaid, CHIP, VA, ACA..."
        federal_programs_redirect = re.search(
            r'(?:redirect(?:ion)?|consolidat(?:e|ion)|transfer)[^.]{0,50}(?:of\s+)?(?:existing\s+)?federal\s+health\s+(?:expenditure|spending|program)[^.]{0,150}?\(?\s*(?:Medicare|Medicaid)',
            text,
            re.IGNORECASE
        )
        if federal_programs_redirect:
            mechanics.medicare_transfer = True
            mechanics.medicaid_expansion = True  # Medicaid integrated into new fund
        
        # Pattern 2: "Medicare, Medicaid, CHIP, VA, ACA" listed together (common USGHA pattern)
        programs_list = re.search(
            r'Medicare,?\s*Medicaid,?\s*(?:CHIP|Children.{1,30}Health)',
            text,
            re.IGNORECASE
        )
        if programs_list and re.search(r'(?:redirect|transfer|consolidat|fold)', text, re.IGNORECASE):
            mechanics.medicare_transfer = True
            mechanics.medicaid_expansion = True
        
        # Pattern 3: Individual program transfers
        if re.search(r'medicare[^.]{0,120}(?:transfer(?:red)?|redirect(?:ed)?|consolidat(?:e|ed)|fold(?:ed)?|integrat(?:e|ed))[^.]{0,80}(?:health\s+fund|trust\s+fund|single\s+fund|unified)', text, re.IGNORECASE | re.DOTALL):
            mechanics.medicare_transfer = True
        if re.search(r'medicaid[^.]{0,120}(?:transfer(?:red)?|redirect(?:ed)?|consolidat(?:e|ed)|fold(?:ed)?|integrat(?:e|ed))[^.]{0,80}(?:health\s+fund|trust\s+fund|single\s+fund|unified)', text, re.IGNORECASE | re.DOTALL):
            mechanics.medicaid_expansion = True  # Medicaid integrated

        # ==========================================================================
        # ENHANCED: Social Security Health Integration Detection (USGHA-style)
        # ==========================================================================
        # Pattern 1: "integrated Social Security purposes" - key USGHA language
        ss_integration = re.search(
            r'integrat(?:e|ed|ion)\s+(?:of\s+)?social\s+security|social\s+security[^.]{0,50}integrat(?:e|ed|ion)',
            text,
            re.IGNORECASE
        )
        if ss_integration:
            mechanics.social_security_health_transfer = True
        
        # Pattern 2: "dedicated to...health...and...Social Security purposes"
        ss_health_dedication = re.search(
            r'dedicated\s+to[^.]{0,100}(?:health|national\s+health)[^.]{0,100}(?:and[^.]{0,50})?social\s+security\s+purposes',
            text,
            re.IGNORECASE
        )
        if ss_health_dedication:
            mechanics.social_security_health_transfer = True
            mechanics.payroll_to_health_fund = True
        
        # Pattern 3: "replace...sections 3101 and 3111 (Social Security and Medicare)"
        ss_replacement = re.search(
            r'(?:replace|offset|substitute)[^.]{0,100}section[s]?\s+3101\s+(?:and|&)\s+3111[^.]{0,50}(?:Social\s+Security|Medicare)',
            text,
            re.IGNORECASE
        )
        if ss_replacement:
            mechanics.social_security_health_transfer = True
            mechanics.payroll_to_health_fund = True
        
        # Pattern 4: "fold in" or "absorb" Social Security health component
        ss_fold = re.search(
            r'social\s+security[^.]{0,80}(?:fold(?:ed)?|absorb(?:ed)?|integrat(?:e|ed)|merge(?:d)?)[^.]{0,50}(?:health|medical|healthcare)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if ss_fold:
            mechanics.social_security_health_transfer = True

        # ==========================================================================
        # ENHANCED: Payroll Tax to Health Fund Redirection
        # ==========================================================================
        # Pattern 1: "X percent shall be dedicated to the National Health...Trust Fund"
        payroll_health_dedication = re.search(
            r'(\d+(?:\.\d+)?)\s*percent\s+(?:shall\s+be\s+)?(?:dedicated|allocated|directed)\s+to\s+(?:the\s+)?(?:National\s+Health|Health\s+(?:and\s+Longevity\s+)?Trust\s+Fund)',
            text,
            re.IGNORECASE
        )
        if payroll_health_dedication:
            mechanics.payroll_to_health_fund = True
        
        # Pattern 2: Payroll contribution converted/replaced/redirected
        payroll_redirect = re.search(
            r'payroll\s+(?:tax|contribution)[^.]{0,150}(?:convert(?:ed)?|redirect(?:ed)?|replace(?:d)?|transfer(?:red)?)[^.]{0,100}(?:health|trust\s+fund|national)',
            text,
            re.IGNORECASE | re.DOTALL
        )
        if payroll_redirect:
            mechanics.payroll_to_health_fund = True

        # ==========================================================================
        # STANDARD: Medicaid provisions (non-USGHA)
        # ==========================================================================
        if re.search(r'medicaid[^.]{0,60}(?:expansion|eligible|enrollment|coverage)', text, re.IGNORECASE | re.DOTALL):
            if not mechanics.medicaid_expansion:  # Don't override USGHA detection
                mechanics.medicaid_expansion = True
        if re.search(r'medicaid[^.]{0,60}(?:block\s+grant|blockgrant)', text, re.IGNORECASE | re.DOTALL):
            mechanics.medicaid_block_grant = True
        if re.search(r'medicaid[^.]{0,80}(per\s+capita\s+cap)', text, re.IGNORECASE | re.DOTALL):
            mechanics.medicaid_per_capita_cap = True
        fmap = re.search(r'(?:fmap|federal\s+match(?:ing)?\s+rate)[^.]{0,80}(\d+(?:\.\d+)?)\s*percent', text, re.IGNORECASE | re.DOTALL)
        if fmap:
            mechanics.medicaid_fmap_change = float(fmap.group(1))
        if re.search(r'(?:1115|waiver)[^.]{0,120}medicaid', text, re.IGNORECASE | re.DOTALL):
            mechanics.medicaid_waivers = True

        # ==========================================================================
        # STANDARD: Spending growth rate and inflation adjustment
        # ==========================================================================
        growth = re.search(
            r'(?:growth|increase|annual)\s+rate[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if growth:
            mechanics.spending_growth_rate = float(growth.group(1)) / 100
        
        inflation = re.search(
            r'(?:inflation|cpi)[^.]*?adjust[^.]*?(\d+(?:\.\d+)?)\s*%',
            text,
            re.IGNORECASE
        )
        if inflation:
            mechanics.inflation_adjustment = float(inflation.group(1)) / 100
        
        # Budget caps
        if re.search(r'(?:budget|spending)\s+cap', text, re.IGNORECASE):
            mechanics.budget_caps_enabled = True
            
            # Look for cap amount
            cap_patterns = [
                r'cap[^$]*?\$\s*(\d+(?:\.\d+)?)\s*(?:trillion|t)',
                r'(?:trillion|t)\s*budget.*?cap',
            ]
            for pattern in cap_patterns:
                cap_search = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if cap_search and '1' not in str(cap_search.group(0)):  # Avoid matching "trillion" without amount
                    try:
                        amount_str = cap_search.group(1).replace(',', '')
                        amount = float(amount_str) * 1000  # Convert trillion to billions
                        mechanics.budget_cap_levels['total'] = amount
                        break
                    except (IndexError, ValueError):
                        continue

        # ==========================================================================
        # ENHANCED: USGHA Surplus Allocation Detection (Section 11)
        # ==========================================================================
        # Pattern: "X percent to contingency reserves / debt reduction / infrastructure"
        surplus_allocations = {}
        
        # Contingency reserves
        contingency = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?contingency\s+(?:reserve|fund)',
            text,
            re.IGNORECASE
        )
        if contingency:
            surplus_allocations['contingency_pct'] = float(contingency.group(1))
        
        # Debt reduction
        debt = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?(?:national\s+)?debt\s+(?:reduction|paydown)',
            text,
            re.IGNORECASE
        )
        if debt:
            surplus_allocations['debt_reduction_pct'] = float(debt.group(1))
        
        # Infrastructure/education/research
        infra_alloc = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?infrastructure[^.]{0,50}(?:education|research)?',
            text,
            re.IGNORECASE
        )
        if infra_alloc:
            surplus_allocations['infrastructure_pct'] = float(infra_alloc.group(1))
        
        # Universal health dividends / tax credits
        dividend = re.search(
            r'(\d+(?:\.\d+)?)\s*percent[^.]{0,80}?(?:universal\s+health\s+)?dividend|direct[^.]{0,50}?tax\s+credit',
            text,
            re.IGNORECASE
        )
        if dividend:
            surplus_allocations['dividend_pct'] = float(dividend.group(1)) if dividend.groups() else 10.0
        
        if surplus_allocations:
            mechanics.budget_cap_levels['surplus_allocations'] = surplus_allocations  # type: ignore[assignment]

        # ==========================================================================
        # ENHANCED: USGHA Fiscal Circuit Breaker Detection (Section 6(d))
        # ==========================================================================
        # Pattern: "If expenditures exceed X percent of GDP, tax rates freeze"
        circuit_breaker = re.search(
            r'(?:if\s+)?expenditure[s]?\s+exceed[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent\s+of\s+(?:gross\s+domestic\s+product|gdp)',
            text,
            re.IGNORECASE
        )
        if circuit_breaker:
            mechanics.budget_caps_enabled = True
            mechanics.budget_cap_levels['gdp_cap_pct'] = float(circuit_breaker.group(1))
        
        # Surplus trigger tax reduction
        surplus_trigger = re.search(
            r'surplus(?:es)?[^.]{0,80}?trigger[^.]{0,80}?(?:automatic\s+)?tax\s+(?:reduction|cut)',
            text,
            re.IGNORECASE
        )
        if surplus_trigger:
            mechanics.budget_cap_levels['surplus_tax_trigger'] = True

        # ==========================================================================
        # ENHANCED: USGHA Administrative Overhead Cap
        # ==========================================================================
        admin_cap = re.search(
            r'(?:maximum|not\s+exceed)[^.]{0,50}?(\\d+(?:\\.\\d+)?)\\s*percent\\s*administrative\\s+(?:overhead|cost)',
            text,
            re.IGNORECASE
        )
        if admin_cap:
            mechanics.budget_cap_levels['admin_overhead_cap_pct'] = float(admin_cap.group(1))
        
        # Alternative pattern: "2.5 percent administrative overhead"
        admin_cap_alt = re.search(
            r'(\d+(?:\.\d+)?)\s*percent\s+administrative\s+(?:overhead|cost)',
            text,
            re.IGNORECASE
        )
        if admin_cap_alt:
            mechanics.budget_cap_levels['admin_overhead_cap_pct'] = float(admin_cap_alt.group(1))

        # ==========================================================================
        # ENHANCED: USGHA Program Consolidation Detection
        # ==========================================================================
        # SNAP/WIC/school lunch consolidation
        nutrition_consolidation = re.search(
            r'(?:SNAP|Supplemental\s+Nutrition|WIC|school\s+lunch)[^.]{0,150}?(?:transfer|consolidat|integrat)',
            text,
            re.IGNORECASE
        )
        if nutrition_consolidation:
            mechanics.budget_cap_levels['nutrition_consolidated'] = True
        
        # VA health consolidation
        va_consolidation = re.search(
            r'(?:VA|veteran)[^.]{0,100}?(?:transfer|consolidat|redirect|integrat)[^.]{0,100}?(?:health|trust\s+fund|GDOH)',
            text,
            re.IGNORECASE
        )
        if va_consolidation:
            mechanics.budget_cap_levels['va_consolidated'] = True

        # ==========================================================================
        # ENHANCED: USGHA Spending Targets Detection (Section 13)
        # ==========================================================================
        # Pattern: "Health spending below X percent of GDP by YYYY"
        spending_target = re.search(
            r'(?:health\s+)?spending\s+(?:below|under|at)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent\s+(?:of\s+)?(?:gross\s+domestic\s+product|gdp)[^.]{0,50}?by\s+(\d{4})',
            text,
            re.IGNORECASE
        )
        if spending_target:
            mechanics.spending_growth_rate = float(spending_target.group(1)) / 100
            mechanics.budget_cap_levels['target_spending_pct_gdp'] = float(spending_target.group(1))
            mechanics.budget_cap_levels['target_year'] = int(spending_target.group(2))
        
        # Pattern: "average below 7 percent"
        avg_target = re.search(
            r'average\s+(?:below|under)\s+(\d+(?:\.\d+)?)\s*percent',
            text,
            re.IGNORECASE
        )
        if avg_target:
            mechanics.budget_cap_levels['avg_spending_target_pct'] = float(avg_target.group(1))

        # ==========================================================================
        # ENHANCED: USGHA Provider Payment Reforms (Section 10)
        # ==========================================================================
        # Global budgets
        global_budget = re.search(
            r'global\s+budget[^.]{0,100}?(\d+(?:\.\d+)?)\s*percent\s+(?:savings\s+)?retention',
            text,
            re.IGNORECASE
        )
        if global_budget:
            mechanics.budget_cap_levels['global_budget_savings_retention'] = float(global_budget.group(1))
        
        # Outcome-based pay multiplier
        outcome_pay = re.search(
            r'outcome[- ]based\s+pay[^.]{0,80}?(\d+(?:\.\d+)?)\s*x\s+multiplier',
            text,
            re.IGNORECASE
        )
        if outcome_pay:
            mechanics.budget_cap_levels['outcome_pay_multiplier'] = float(outcome_pay.group(1))

        # ==========================================================================
        # ENHANCED: USGHA Health Equity Fund (Section 16)
        # ==========================================================================
        equity_fund = re.search(
            r'health\s+equity[^.]{0,80}?(?:fund|investment)[^.]{0,50}?(\d+(?:\.\d+)?)\s*(?:percent|%)',
            text,
            re.IGNORECASE
        )
        if equity_fund:
            mechanics.budget_cap_levels['health_equity_fund_pct'] = float(equity_fund.group(1))
        
        return mechanics
    
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


def extract_policy_mechanics(text: str, policy_type: str = "combined") -> PolicyMechanics:
    """
    Main entry point for extracting policy mechanics - UNIFIED EXTRACTION.
    
    When policy_type="combined" (default), extracts mechanics for ALL domains:
    - Healthcare
    - Tax reform
    - Social Security
    - Spending reform
    
    Each module can then access the mechanics it needs from the returned object.
    
    Args:
        text: Full policy text
        policy_type: Type of policy (healthcare, tax_reform, spending_reform, combined)
    
    Returns:
        PolicyMechanics object with structured extraction for all applicable domains
    """
    # Detect policy types from content when "combined" specified
    detected_types = set()
    if policy_type == "combined":
        # Force extraction across all domains for combined policies to avoid missing mechanics
        detected_types.update(["healthcare", "tax", "social_security", "spending"])
    else:
        # Single type specified
        if policy_type == "healthcare":
            detected_types.add("healthcare")
        elif policy_type == "tax_reform":
            detected_types.add("tax")
        elif policy_type == "spending_reform":
            detected_types.add("spending")
        elif policy_type == "social_security":
            detected_types.add("social_security")
    
    # Create base mechanics object
    policy_type_str = "combined" if len(detected_types) > 1 else list(detected_types)[0] if detected_types else "healthcare"
    mechanics = PolicyMechanics(
        policy_name="Extracted Policy",
        policy_type=policy_type_str
    )
    
    # Extract healthcare mechanics if detected
    if "healthcare" in detected_types:
        try:
            healthcare_mechanics = extract_with_context_awareness(text)
            mechanics.policy_name = healthcare_mechanics.policy_name
            mechanics.target_spending_pct_gdp = healthcare_mechanics.target_spending_pct_gdp
            mechanics.target_spending_year = healthcare_mechanics.target_spending_year
            mechanics.zero_out_of_pocket = healthcare_mechanics.zero_out_of_pocket
            mechanics.universal_coverage = healthcare_mechanics.universal_coverage
            mechanics.funding_mechanisms = healthcare_mechanics.funding_mechanisms
            mechanics.surplus_allocation = healthcare_mechanics.surplus_allocation
            mechanics.circuit_breakers = healthcare_mechanics.circuit_breakers
            mechanics.innovation_fund = healthcare_mechanics.innovation_fund
            mechanics.timeline_milestones = healthcare_mechanics.timeline_milestones
            mechanics.source_sections.update(healthcare_mechanics.source_sections)
        except Exception as e:
            print(f"Healthcare extraction failed: {e}")
    
    # Extract tax mechanics if detected
    if "tax" in detected_types:
        try:
            mechanics.tax_mechanics = PolicyMechanicsExtractor._extract_tax_mechanics(text)
        except Exception as e:
            print(f"Tax extraction failed: {e}")
    
    # Extract social security mechanics if detected
    if "social_security" in detected_types:
        try:
            mechanics.social_security_mechanics = PolicyMechanicsExtractor._extract_social_security_mechanics(text)
        except Exception as e:
            print(f"Social Security extraction failed: {e}")
    
    # Extract spending mechanics if detected
    if "spending" in detected_types:
        try:
            mechanics.spending_mechanics = PolicyMechanicsExtractor._extract_spending_mechanics(text)
        except Exception as e:
            print(f"Spending extraction failed: {e}")
    
    # Calculate overall confidence
    mechanics.confidence_score = PolicyMechanicsExtractor._calculate_confidence(mechanics)
    
    return mechanics


def mechanics_to_dict(mechanics: PolicyMechanics) -> Dict[str, Any]:
    """Serialize PolicyMechanics to a plain dictionary for storage."""

    def funding_to_dict(f: FundingMechanism) -> Dict[str, Any]:
        return {
            "source_type": f.source_type,
            "percentage_gdp": f.percentage_gdp,
            "percentage_rate": f.percentage_rate,
            "description": f.description,
            "phase_in_start": f.phase_in_start,
            "phase_in_end": f.phase_in_end,
            "conditions": f.conditions,
            "estimated_amount": f.estimated_amount,
        }

    def circuit_to_dict(c: CircuitBreaker) -> Dict[str, Any]:
        return {
            "trigger_type": c.trigger_type,
            "threshold_value": c.threshold_value,
            "threshold_unit": c.threshold_unit,
            "action": c.action,
            "description": c.description,
        }

    def innovation_to_dict(i: InnovationFundRules) -> Optional[Dict[str, Any]]:
        if not i:
            return None
        return {
            "funding_min_pct": i.funding_min_pct,
            "funding_max_pct": i.funding_max_pct,
            "funding_base": i.funding_base,
            "prize_min_dollars": i.prize_min_dollars,
            "prize_max_dollars": i.prize_max_dollars,
            "annual_cap_pct": i.annual_cap_pct,
            "annual_cap_base": i.annual_cap_base,
            "eligible_categories": i.eligible_categories,
        }

    def surplus_to_dict(s: SurplusAllocation) -> Optional[Dict[str, Any]]:
        if not s:
            return None
        return {
            "contingency_reserve_pct": s.contingency_reserve_pct,
            "debt_reduction_pct": s.debt_reduction_pct,
            "infrastructure_pct": s.infrastructure_pct,
            "dividends_pct": s.dividends_pct,
            "other_allocations": s.other_allocations,
            "trigger_conditions": s.trigger_conditions,
        }

    def timeline_to_dict(t: TimelineMilestone) -> Dict[str, Any]:
        return {
            "year": t.year,
            "description": t.description,
            "metric_type": t.metric_type,
            "target_value": t.target_value,
        }

    def tax_to_dict(t: TaxMechanics) -> Optional[Dict[str, Any]]:
        if not t:
            return None
        return {
            "wealth_tax_rate": t.wealth_tax_rate,
            "wealth_tax_threshold": t.wealth_tax_threshold,
            "wealth_tax_tiers": t.wealth_tax_tiers,
            "consumption_tax_rate": t.consumption_tax_rate,
            "consumption_tax_exemptions": t.consumption_tax_exemptions,
            "consumption_tax_rebate": t.consumption_tax_rebate,
            "carbon_tax_per_ton": t.carbon_tax_per_ton,
            "carbon_tax_annual_increase": t.carbon_tax_annual_increase,
            "carbon_revenue_allocation": t.carbon_revenue_allocation,
            "financial_transaction_tax_rate": t.financial_transaction_tax_rate,
            "income_tax_changes": t.income_tax_changes,
            "corporate_tax_rate": t.corporate_tax_rate,
            "payroll_tax_rate": t.payroll_tax_rate,
            "tax_revenue_billions": t.tax_revenue_billions,
            "estimated_tax_revenue_growth": t.estimated_tax_revenue_growth,
        }

    def ss_to_dict(s: SocialSecurityMechanics) -> Optional[Dict[str, Any]]:
        if not s:
            return None
        return {
            "payroll_tax_rate": s.payroll_tax_rate,
            "payroll_tax_cap_change": s.payroll_tax_cap_change,
            "payroll_tax_cap_increase": s.payroll_tax_cap_increase,
            "full_retirement_age": s.full_retirement_age,
            "full_retirement_age_change": s.full_retirement_age_change,
            "benefit_formula_changes": s.benefit_formula_changes,
            "cola_adjustments": s.cola_adjustments,
            "means_testing_threshold": s.means_testing_threshold,
            "means_testing_enabled": s.means_testing_enabled,
            "early_claiming_reduction": s.early_claiming_reduction,
            "delayed_claiming_credit": s.delayed_claiming_credit,
            "demographic_assumptions": s.demographic_assumptions,
            "trust_fund_solvency_year": s.trust_fund_solvency_year,
            "estimated_year_deficit": s.estimated_year_deficit,
        }

    def spending_to_dict(s: SpendingMechanics) -> Optional[Dict[str, Any]]:
        if not s:
            return None
        return {
            "defense_spending_change": s.defense_spending_change,
            "defense_spending_cap": s.defense_spending_cap,
            "nondefense_discretionary_change": s.nondefense_discretionary_change,
            "nondefense_categories": s.nondefense_categories,
            "infrastructure_spending": s.infrastructure_spending,
            "education_spending": s.education_spending,
            "research_spending": s.research_spending,
            "medicaid_expansion": s.medicaid_expansion,
            "medicaid_block_grant": s.medicaid_block_grant,
            "medicaid_per_capita_cap": s.medicaid_per_capita_cap,
            "medicaid_fmap_change": s.medicaid_fmap_change,
            "medicaid_waivers": s.medicaid_waivers,
            "national_health_fund": s.national_health_fund,
            "medicare_transfer": s.medicare_transfer,
            "social_security_health_transfer": s.social_security_health_transfer,
            "payroll_to_health_fund": s.payroll_to_health_fund,
            "spending_growth_rate": s.spending_growth_rate,
            "inflation_adjustment": s.inflation_adjustment,
            "budget_caps_enabled": s.budget_caps_enabled,
            "budget_cap_levels": s.budget_cap_levels,
        }

    return {
        "policy_name": mechanics.policy_name,
        "policy_type": mechanics.policy_type,
        "funding_mechanisms": [funding_to_dict(f) for f in mechanics.funding_mechanisms],
        "surplus_allocation": surplus_to_dict(mechanics.surplus_allocation) if mechanics.surplus_allocation else None,
        "circuit_breakers": [circuit_to_dict(c) for c in mechanics.circuit_breakers],
        "innovation_fund": innovation_to_dict(mechanics.innovation_fund) if mechanics.innovation_fund else None,
        "timeline_milestones": [timeline_to_dict(t) for t in mechanics.timeline_milestones],
        "target_spending_pct_gdp": mechanics.target_spending_pct_gdp,
        "target_spending_year": mechanics.target_spending_year,
        "zero_out_of_pocket": mechanics.zero_out_of_pocket,
        "universal_coverage": mechanics.universal_coverage,
        "tax_mechanics": tax_to_dict(mechanics.tax_mechanics) if mechanics.tax_mechanics else None,
        "social_security_mechanics": ss_to_dict(mechanics.social_security_mechanics) if mechanics.social_security_mechanics else None,
        "spending_mechanics": spending_to_dict(mechanics.spending_mechanics) if mechanics.spending_mechanics else None,
        "source_sections": mechanics.source_sections,
        "confidence_score": mechanics.confidence_score,
        "unfunded": mechanics.unfunded,
    }


def _detect_healthcare_content(text: str) -> bool:
    """Detect if text contains healthcare policy content."""
    healthcare_keywords = [
        r'health\s+(?:care|insurance|coverage)',
        r'medicare|medicaid|oasi|disability|aca|affordable\s+care',
        r'premiums?|deductible|copay|out[- ]of[- ]pocket',
        r'coverage|enrollment|beneficiar(?:y|ies)',
        r'drug\s+(?:pricing|costs?)|pharmaceutical',
    ]
    return sum(1 for kw in healthcare_keywords if re.search(kw, text, re.IGNORECASE)) >= 2


def _detect_tax_content(text: str) -> bool:
    """Detect if text contains tax reform policy content."""
    tax_keywords = [
        r'wealth\s+tax|net\s+worth\s+tax',
        r'consumption\s+tax|vat|sales\s+tax',
        r'carbon\s+(?:tax|pricing|emissions)',
        r'financial\s+transaction\s+tax|tobin\s+tax',
        r'tax\s+(?:rate|bracket|increase|reform)',
        r'revenue|tax\s+burden|marginal\s+rate',
    ]
    return sum(1 for kw in tax_keywords if re.search(kw, text, re.IGNORECASE)) >= 2


def _detect_social_security_content(text: str) -> bool:
    """Detect if text contains Social Security reform content."""
    ss_keywords = [
        r'social\s+security|social\s+insurance',
        r'payroll\s+tax|oasdi|fica',
        r'full\s+retirement\s+age|early\s+claiming|delayed\s+claiming',
        r'benefit\s+formula|primary\s+insurance\s+amount|pia',
        r'trust\s+fund|solvency|retirement\s+benefits?',
    ]
    return sum(1 for kw in ss_keywords if re.search(kw, text, re.IGNORECASE)) >= 2


def _detect_spending_content(text: str) -> bool:
    """Detect if text contains spending reform policy content."""
    spending_keywords = [
        r'defense|military|pentagon',
        r'discretionary\s+(?:spending|budget)|infrastructure|roads|bridges|transit',
        r'(?:education|schools?|k[-]?12|research|science)',
        r'(?:budget|spending)\s+cap|appropriation',
        r'medicaid|chip|fmap|per\s+capita\s+cap|block\s+grant',
    ]
    return sum(1 for kw in spending_keywords if re.search(kw, text, re.IGNORECASE)) >= 2


def calculate_total_funding_gdp(mechanics: PolicyMechanics) -> float:
    """
    Calculate total funding as percentage of GDP from extracted funding mechanisms.
    
    This aggregates all funding sources to provide a total revenue estimate
    for policy projections.
    
    Args:
        mechanics: PolicyMechanics object with funding_mechanisms
        
    Returns:
        Total funding as percentage of GDP (e.g., 0.12 = 12% GDP)
    """
    total_gdp_pct = 0.0
    
    for fm in mechanics.funding_mechanisms:
        if fm.percentage_gdp is not None:
            total_gdp_pct += fm.percentage_gdp
    
    return total_gdp_pct / 100.0 if total_gdp_pct > 1 else total_gdp_pct


def calculate_fiscal_balance(
    mechanics: PolicyMechanics,
    gdp_billions: float = 28000.0
) -> Dict[str, float]:
    """
    Calculate projected fiscal balance from policy mechanics.
    
    Computes revenue, spending, and balance based on extracted policy parameters.
    
    Args:
        mechanics: PolicyMechanics object with funding and spending targets
        gdp_billions: GDP in billions (default ~$28T for 2026)
        
    Returns:
        Dictionary with revenue, spending, and balance estimates
    """
    # Calculate total revenue from funding mechanisms
    total_funding_pct = calculate_total_funding_gdp(mechanics)
    revenue_billions = gdp_billions * total_funding_pct
    
    # Calculate spending target
    spending_pct = 0.18  # Default current US healthcare ~18% GDP
    if mechanics.target_spending_pct_gdp is not None:
        spending_pct = mechanics.target_spending_pct_gdp
        if spending_pct > 1:
            spending_pct = spending_pct / 100.0
    
    spending_billions = gdp_billions * spending_pct
    
    # Calculate balance
    balance_billions = revenue_billions - spending_billions
    balance_pct = (revenue_billions - spending_billions) / gdp_billions
    
    return {
        "revenue_pct_gdp": total_funding_pct,
        "revenue_billions": revenue_billions,
        "spending_pct_gdp": spending_pct,
        "spending_billions": spending_billions,
        "balance_billions": balance_billions,
        "balance_pct_gdp": balance_pct,
        "sustainable": balance_billions >= 0
    }


def get_projection_adjustments(mechanics_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate projection adjustment parameters from serialized policy mechanics.
    
    This function takes the structured mechanics dictionary (as stored in policy templates)
    and returns adjustment factors for the projection models.
    
    Args:
        mechanics_dict: Serialized policy mechanics dictionary
        
    Returns:
        Dictionary with model-specific adjustment parameters
    """
    adjustments: Dict[str, Dict[str, Any]] = {
        "revenue": {},
        "healthcare": {},
        "social_security": {},
        "discretionary": {},
        "medicaid": {},
    }
    
    # Revenue adjustments from funding mechanisms
    funding_mechs = mechanics_dict.get("funding_mechanisms", [])
    total_funding_gdp = sum(
        fm.get("percentage_gdp", 0) or 0 
        for fm in funding_mechs
    )
    if total_funding_gdp > 1:
        total_funding_gdp = total_funding_gdp / 100.0
    adjustments["revenue"]["total_funding_pct_gdp"] = total_funding_gdp
    
    # Check for specific funding types
    for fm in funding_mechs:
        source_type = fm.get("source_type", "")
        if source_type == "payroll_tax" and fm.get("percentage_rate"):
            adjustments["revenue"]["payroll_tax_rate"] = fm["percentage_rate"] / 100.0
        elif source_type == "converted_premiums":
            adjustments["revenue"]["premium_conversion_pct_gdp"] = fm.get("percentage_gdp", 0)
        elif source_type == "redirected_federal":
            adjustments["revenue"]["federal_redirect_pct_gdp"] = fm.get("percentage_gdp", 0)
    
    # Healthcare adjustments
    target_spending = mechanics_dict.get("target_spending_pct_gdp")
    if target_spending is not None:
        if target_spending > 1:
            target_spending = target_spending / 100.0
        adjustments["healthcare"]["target_spending_pct_gdp"] = target_spending
    adjustments["healthcare"]["target_year"] = mechanics_dict.get("target_spending_year")
    adjustments["healthcare"]["universal_coverage"] = mechanics_dict.get("universal_coverage", False)
    adjustments["healthcare"]["zero_out_of_pocket"] = mechanics_dict.get("zero_out_of_pocket", False)
    
    # Social Security adjustments
    ss_mech = mechanics_dict.get("social_security_mechanics") or {}
    if ss_mech:
        adjustments["social_security"] = {
            "payroll_tax_rate": ss_mech.get("payroll_tax_rate"),
            "cap_change": ss_mech.get("payroll_tax_cap_change"),
            "cap_increase": ss_mech.get("payroll_tax_cap_increase"),
            "fra": ss_mech.get("full_retirement_age"),
            "fra_change": ss_mech.get("full_retirement_age_change"),
            "cola_adjustment": ss_mech.get("cola_adjustments"),
        }
    
    # Discretionary adjustments
    spend_mech = mechanics_dict.get("spending_mechanics") or {}
    if spend_mech:
        adjustments["discretionary"] = {
            "defense_change": spend_mech.get("defense_spending_change"),
            "nondefense_change": spend_mech.get("nondefense_discretionary_change"),
            "budget_caps": spend_mech.get("budget_caps_enabled"),
            "infrastructure": spend_mech.get("infrastructure_spending"),
            "education": spend_mech.get("education_spending"),
        }
        
        # Medicaid-specific adjustments
        adjustments["medicaid"] = {
            "expansion": spend_mech.get("medicaid_expansion"),
            "block_grant": spend_mech.get("medicaid_block_grant"),
            "per_capita_cap": spend_mech.get("medicaid_per_capita_cap"),
            "fmap_change": spend_mech.get("medicaid_fmap_change"),
            "waivers": spend_mech.get("medicaid_waivers"),
            "national_health_fund": spend_mech.get("national_health_fund"),
            "medicare_transfer": spend_mech.get("medicare_transfer"),
        }
    
    return adjustments


# =============================================================================
# MCP-READY EXTRACTION HOOKS
# =============================================================================
# These functions are designed to be callable by future MCP (Model Context Protocol)
# tools for AI-assisted policy extraction. They return structured data suitable
# for integration with language models and automated policy analysis systems.
#
# Usage pattern for MCP integration:
#   1. MCP tool calls mcp_extract_policy_text(pdf_path) to get text
#   2. MCP tool calls mcp_analyze_policy_type(text) to determine policy type
#   3. MCP tool calls mcp_extract_all_mechanics(text) for full extraction
#   4. AI agent reviews and enriches extracted mechanics
#   5. MCP tool calls mcp_validate_extraction(mechanics) for quality check
# =============================================================================


def mcp_analyze_policy_type(text: str) -> Dict[str, Any]:
    """
    MCP-ready function to analyze policy text and determine content types.
    
    Returns a structured analysis of what policy domains are present in the text,
    useful for routing to appropriate extraction methods.
    
    Args:
        text: Raw policy text to analyze
        
    Returns:
        Dictionary with:
        - primary_type: Most likely policy type (healthcare, tax, social_security, spending, combined)
        - detected_domains: List of all detected policy domains
        - confidence: Confidence score (0.0-1.0)
        - key_indicators: List of key phrases that triggered detection
    """
    domains = []
    indicators = []
    
    # Check for healthcare content
    if _detect_healthcare_content(text):
        domains.append("healthcare")
        indicators.extend([
            match.group(0) for match in re.finditer(
                r'(?:health\s+care|medicare|medicaid|coverage|premium)',
                text[:5000],
                re.IGNORECASE
            )
        ][:3])
    
    # Check for tax reform content
    if _detect_tax_content(text):
        domains.append("tax_reform")
        indicators.extend([
            match.group(0) for match in re.finditer(
                r'(?:wealth\s+tax|carbon\s+tax|payroll\s+tax|income\s+tax)',
                text[:5000],
                re.IGNORECASE
            )
        ][:3])
    
    # Check for Social Security content
    if _detect_social_security_content(text):
        domains.append("social_security")
        indicators.extend([
            match.group(0) for match in re.finditer(
                r'(?:social\s+security|retirement|payroll|trust\s+fund)',
                text[:5000],
                re.IGNORECASE
            )
        ][:3])
    
    # Check for spending reform content
    if _detect_spending_content(text):
        domains.append("spending_reform")
        indicators.extend([
            match.group(0) for match in re.finditer(
                r'(?:defense|infrastructure|medicaid|discretionary)',
                text[:5000],
                re.IGNORECASE
            )
        ][:3])
    
    # Determine primary type
    if len(domains) >= 3:
        primary_type = "combined"
    elif len(domains) == 0:
        primary_type = "unknown"
    else:
        primary_type = domains[0]
    
    # Calculate confidence
    confidence = min(1.0, len(domains) * 0.25 + len(indicators) * 0.05)
    
    return {
        "primary_type": primary_type,
        "detected_domains": domains,
        "confidence": confidence,
        "key_indicators": list(set(indicators))[:10],
        "text_length": len(text),
        "is_comprehensive": len(domains) >= 2
    }


def mcp_extract_all_mechanics(
    text: str,
    policy_name: str = "Extracted Policy"
) -> Dict[str, Any]:
    """
    MCP-ready function to extract all policy mechanics from text.
    
    This is the main entry point for MCP-based extraction. It performs
    comprehensive extraction across all policy domains and returns
    structured data suitable for AI agent review and enrichment.
    
    Args:
        text: Raw policy text to extract from
        policy_name: Name to assign to extracted policy
        
    Returns:
        Dictionary with:
        - mechanics: Full serialized PolicyMechanics
        - extraction_metadata: Information about extraction quality
        - ai_enrichment_hints: Suggestions for AI agent review
    """
    # Analyze content type first
    analysis = mcp_analyze_policy_type(text)
    
    # Extract using context-aware extractor
    mechanics = extract_with_context_awareness(text, policy_name)
    
    # Serialize to dictionary
    mechanics_dict = mechanics_to_dict(mechanics)
    
    # Generate AI enrichment hints based on what was/wasn't extracted
    hints = []
    
    # Check for incomplete payroll tax extraction
    funding_mechs = mechanics_dict.get("funding_mechanisms", [])
    has_payroll = any(fm.get("source_type") == "payroll_tax" for fm in funding_mechs)
    if not has_payroll and "payroll" in text.lower():
        hints.append("Payroll tax mentioned but not extracted - verify rate and allocation")
    
    # Check for incomplete program consolidation
    spend_mech = mechanics_dict.get("spending_mechanics") or {}
    if spend_mech.get("national_health_fund") and not spend_mech.get("medicare_transfer"):
        hints.append("Health fund detected but Medicare transfer not confirmed - verify program consolidation")
    
    # Check for missing spending target
    if mechanics_dict.get("target_spending_pct_gdp") is None and "percent of gdp" in text.lower():
        hints.append("GDP percentage mentioned but spending target not extracted - verify target value")
    
    # Check for low confidence areas
    if mechanics_dict.get("confidence_score", 0) < 0.5:
        hints.append("Low extraction confidence - manual review recommended")
    
    return {
        "mechanics": mechanics_dict,
        "extraction_metadata": {
            "policy_analysis": analysis,
            "extraction_method": "unified",
            "confidence_score": mechanics_dict.get("confidence_score", 0),
            "funding_mechanisms_count": len(funding_mechs),
            "has_healthcare": "healthcare" in analysis.get("detected_domains", []),
            "has_tax": "tax_reform" in analysis.get("detected_domains", []),
            "has_social_security": "social_security" in analysis.get("detected_domains", []),
            "has_spending": "spending_reform" in analysis.get("detected_domains", []),
        },
        "ai_enrichment_hints": hints,
        "extraction_version": "2.0-mcp-ready"
    }


def mcp_extract_usgha_specific(text: str) -> Dict[str, Any]:
    """
    MCP-ready function to extract USGHA-specific policy mechanics.
    
    Optimized for United States Galactic Health Act patterns including:
    - 15% combined payroll tax cap with 45%/27.5%/27.5% allocation
    - National Health and Longevity Trust Fund
    - Medicare/Medicaid/CHIP/VA/ACA program consolidation
    - Social Security health integration
    - Dollar-for-dollar offset (sections 3101/3111)
    
    Args:
        text: USGHA policy text
        
    Returns:
        Dictionary with USGHA-specific extracted fields
    """
    result: Dict[str, Any] = {
        "is_usgha_pattern": False,
        "payroll_tax": {},
        "health_fund": {},
        "program_consolidation": {},
        "social_security_integration": {},
        "spending_targets": {},
    }
    
    # Check for USGHA signature patterns
    usgha_signatures = [
        r'galactic\s+(?:health|department)',
        r'national\s+health\s+and\s+longevity\s+trust\s+fund',
        r'multiplanetary',
        r'longevity\s+moonshot',
    ]
    usgha_matches = sum(1 for sig in usgha_signatures if re.search(sig, text, re.IGNORECASE))
    result["is_usgha_pattern"] = usgha_matches >= 2
    
    # Extract payroll tax details
    payroll_cap = re.search(
        r'(?:total\s+)?(?:combined\s+)?payroll\s+(?:tax|contribution)\s+rate[^.]{0,100}?(?:capped|shall\s+(?:be|not)\s+exceed)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent',
        text,
        re.IGNORECASE
    )
    if payroll_cap:
        result["payroll_tax"]["cap_rate"] = float(payroll_cap.group(1))
    
    # Extract allocation breakdown
    allocation = re.search(
        r'(?:of\s+this|from\s+this)[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent[^.]{0,100}?(?:health|national\s+health|trust\s+fund)',
        text,
        re.IGNORECASE
    )
    if allocation:
        result["payroll_tax"]["health_fund_allocation_pct"] = float(allocation.group(2))
    
    # Federal/state allocation
    fed_state = re.search(
        r'(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?federal[^.]{0,50}?(\d+(?:\.\d+)?)\s*percent[^.]{0,50}?state',
        text,
        re.IGNORECASE
    )
    if fed_state:
        result["payroll_tax"]["federal_allocation_pct"] = float(fed_state.group(1))
        result["payroll_tax"]["state_allocation_pct"] = float(fed_state.group(2))
    
    # Dollar-for-dollar offset
    if re.search(r'dollar[- ]for[- ]dollar|section[s]?\s+3101\s+(?:and|&)\s+3111', text, re.IGNORECASE):
        result["payroll_tax"]["offset_existing_taxes"] = True
    
    # Health fund detection
    if re.search(r'national\s+health\s+(?:and\s+longevity\s+)?trust\s+fund', text, re.IGNORECASE):
        result["health_fund"]["name"] = "National Health and Longevity Trust Fund"
        result["health_fund"]["exists"] = True
    
    # Program consolidation
    programs = []
    if re.search(r'medicare', text, re.IGNORECASE):
        programs.append("Medicare")
    if re.search(r'medicaid', text, re.IGNORECASE):
        programs.append("Medicaid")
    if re.search(r'chip|children.{1,30}health', text, re.IGNORECASE):
        programs.append("CHIP")
    if re.search(r'\bva\b|veteran', text, re.IGNORECASE):
        programs.append("VA")
    if re.search(r'\baca\b|affordable\s+care', text, re.IGNORECASE):
        programs.append("ACA")
    
    result["program_consolidation"]["programs"] = programs
    result["program_consolidation"]["is_consolidated"] = len(programs) >= 3
    
    # Social Security integration
    ss_patterns = [
        (r'integrat(?:e|ed|ion)\s+(?:of\s+)?social\s+security', "integration"),
        (r'social\s+security\s+purposes', "purpose_allocation"),
        (r'(?:replace|offset)[^.]{0,100}section[s]?\s+3101', "tax_replacement"),
        (r'grandfathered.*social\s+security|social\s+security.*grandfathered', "grandfathering"),
    ]
    ss_integration_types = []
    for pattern, int_type in ss_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            ss_integration_types.append(int_type)
    
    result["social_security_integration"]["integration_types"] = ss_integration_types
    result["social_security_integration"]["is_integrated"] = len(ss_integration_types) > 0
    
    # Spending targets
    spending_target = PolicyMechanicsExtractor._extract_spending_target(text)
    if spending_target:
        result["spending_targets"] = spending_target
    
    return result


def mcp_validate_extraction(mechanics_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    MCP-ready function to validate extracted policy mechanics.
    
    Performs quality checks on extracted mechanics and returns
    validation results with suggestions for improvement.
    
    Args:
        mechanics_dict: Serialized PolicyMechanics dictionary
        
    Returns:
        Dictionary with:
        - is_valid: Overall validity (True/False)
        - quality_score: Quality score (0.0-1.0)
        - issues: List of validation issues
        - suggestions: List of improvement suggestions
    """
    issues = []
    suggestions = []
    quality_points = 0
    max_points = 10
    
    # Check policy name
    if mechanics_dict.get("policy_name"):
        quality_points += 1
    else:
        issues.append("Missing policy name")
    
    # Check funding mechanisms
    funding = mechanics_dict.get("funding_mechanisms", [])
    if len(funding) > 0:
        quality_points += 2
        # Check for GDP percentages
        has_gdp = any(fm.get("percentage_gdp") for fm in funding)
        if has_gdp:
            quality_points += 1
        else:
            suggestions.append("Add GDP percentage estimates to funding mechanisms")
    else:
        issues.append("No funding mechanisms extracted")
        suggestions.append("Review Section 6 or funding-related sections for revenue sources")
    
    # Check spending targets
    if mechanics_dict.get("target_spending_pct_gdp") is not None:
        quality_points += 1
    else:
        suggestions.append("Look for GDP percentage spending targets")
    
    # Check coverage flags
    if mechanics_dict.get("zero_out_of_pocket") or mechanics_dict.get("universal_coverage"):
        quality_points += 1
    
    # Check domain-specific mechanics
    if mechanics_dict.get("tax_mechanics"):
        quality_points += 1
    if mechanics_dict.get("social_security_mechanics"):
        quality_points += 1
    if mechanics_dict.get("spending_mechanics"):
        spending = mechanics_dict.get("spending_mechanics", {})
        if spending.get("national_health_fund") or spending.get("medicare_transfer"):
            quality_points += 1
        if spending.get("medicaid_expansion"):
            quality_points += 1
    
    # Calculate quality score
    quality_score = quality_points / max_points
    
    # Determine validity
    is_valid = len(issues) == 0 and quality_score >= 0.3
    
    return {
        "is_valid": is_valid,
        "quality_score": quality_score,
        "quality_points": quality_points,
        "max_points": max_points,
        "issues": issues,
        "suggestions": suggestions,
        "validation_version": "1.0"
    }


def mcp_get_extraction_schema() -> Dict[str, Any]:
    """
    MCP-ready function to get the extraction schema.
    
    Returns the complete schema of extractable policy mechanics,
    useful for AI agents to understand what fields are available.
    
    Returns:
        Dictionary describing all extractable fields and their types
    """
    return {
        "funding_mechanism_types": [
            "payroll_tax", "redirected_federal", "converted_premiums",
            "efficiency_gains", "transaction_tax", "excise_reallocation",
            "import_tariffs", "reinsurance_pool", "national_health_fund",
            "pharmaceutical_savings", "program_consolidation", "dsh_gme_funds",
            "inflation_escalator", "eitc_expansion", "payroll_offset"
        ],
        "tax_mechanics_fields": [
            "wealth_tax_rate", "wealth_tax_threshold", "wealth_tax_tiers",
            "consumption_tax_rate", "consumption_tax_exemptions", "consumption_tax_rebate",
            "carbon_tax_per_ton", "carbon_tax_annual_increase", "carbon_revenue_allocation",
            "financial_transaction_tax_rate", "income_tax_changes",
            "corporate_tax_rate", "payroll_tax_rate"
        ],
        "social_security_fields": [
            "payroll_tax_rate", "payroll_tax_cap_change", "payroll_tax_cap_increase",
            "full_retirement_age", "full_retirement_age_change",
            "benefit_formula_changes", "cola_adjustments",
            "means_testing_threshold", "means_testing_enabled",
            "early_claiming_reduction", "delayed_claiming_credit"
        ],
        "spending_mechanics_fields": [
            "defense_spending_change", "nondefense_discretionary_change",
            "infrastructure_spending", "education_spending", "research_spending",
            "medicaid_expansion", "medicaid_block_grant", "medicaid_per_capita_cap",
            "national_health_fund", "medicare_transfer",
            "social_security_health_transfer", "payroll_to_health_fund"
        ],
        "circuit_breaker_types": [
            "spending_cap", "surplus_trigger", "deficit_trigger"
        ],
        "timeline_metric_types": [
            "coverage_start", "full_implementation", "spending_target", "surplus_target"
        ],
        "schema_version": "2.0"
    }
