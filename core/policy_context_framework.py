"""
Policy Context Extraction Framework
Provides a principled, extensible approach to understanding legislation
by identifying semantic concepts rather than keyword matching.

Core principles:
1. Policies are structured by **intent domains** (funding, coverage, implementation, governance)
2. Each domain has **extractable concepts** with multiple linguistic expressions
3. Extraction is **recursive** — concepts build on other concepts
4. Results are **structured data** that can drive simulations without assumptions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
import re


class ConceptType(Enum):
    """Semantic concept categories across healthcare policies."""
    # Coverage concepts
    COVERAGE_SCOPE = "coverage_scope"  # Who is covered
    COST_SHARING = "cost_sharing"  # Out-of-pocket requirements
    SERVICE_SCOPE = "service_scope"  # What services are included
    
    # Funding concepts
    REVENUE_SOURCE = "revenue_source"  # How funding is generated
    REVENUE_AMOUNT = "revenue_amount"  # Quantified funding
    COST_CONTROL = "cost_control"  # Spending targets/constraints
    
    # Implementation concepts
    TIMELINE = "timeline"  # When things happen
    PHASE_IN = "phase_in"  # Gradual rollout
    TRANSITION = "transition"  # From old to new system
    
    # Governance concepts
    OVERSIGHT = "oversight"  # Who makes decisions
    ACCOUNTABILITY = "accountability"  # How performance is measured
    SAFEGUARD = "safeguard"  # Circuit breakers, protections
    
    # System concepts
    INTERACTION = "interaction"  # How different parts connect
    EXCEPTION = "exception"  # Special cases, opt-outs


@dataclass
class ConceptExpression:
    """A single linguistic expression of a concept."""
    pattern: str  # Regex or exact phrase
    context_clues: List[str] = field(default_factory=list)  # Words nearby that strengthen match
    confidence_boost: float = 0.0  # Confidence multiplier (0-1)
    is_regex: bool = True


@dataclass
class ExtractedConcept:
    """A successfully extracted concept from text."""
    concept_type: ConceptType
    concept_name: str
    value: str  # The actual extracted content
    source_text: str  # Original legislative language
    confidence: float  # 0-1 score
    section: Optional[str] = None  # Which section of the bill
    relationships: Dict[str, List[str]] = field(default_factory=dict)  # Links to other concepts
    qualifiers: List[str] = field(default_factory=list)  # Conditions, exceptions, etc.


@dataclass
class ConceptTaxonomy:
    """Organized set of concepts that define a policy domain."""
    domain_name: str
    description: str
    concepts: Dict[str, List[ConceptExpression]] = field(default_factory=dict)
    required_concepts: Set[str] = field(default_factory=set)  # Must find at least these
    scoring_weights: Dict[str, float] = field(default_factory=dict)  # Importance multipliers


class PolicyContextExtractor:
    """
    Main context extraction engine.
    
    Workflow:
    1. Load taxonomies for recognized policy domains
    2. Scan policy text for semantic concepts
    3. Extract structured concepts with confidence scores
    4. Build dependency graph (concept X depends on concept Y)
    5. Validate completeness and flag gaps
    6. Serialize to PolicyMechanics
    """
    
    def __init__(self):
        self.taxonomies: Dict[str, ConceptTaxonomy] = {}
        self._register_standard_taxonomies()
    
    def _register_standard_taxonomies(self):
        """Register default taxonomies for common policy types."""
        self.register_taxonomy(self._build_single_payer_taxonomy())
        self.register_taxonomy(self._build_universal_coverage_taxonomy())
        self.register_taxonomy(self._build_multi_payer_taxonomy())
    
    def register_taxonomy(self, taxonomy: ConceptTaxonomy):
        """Register a new policy domain taxonomy."""
        self.taxonomies[taxonomy.domain_name] = taxonomy
    
    def _build_single_payer_taxonomy(self) -> ConceptTaxonomy:
        """Taxonomy for single-payer systems (M4A, USGHA, etc.)."""
        return ConceptTaxonomy(
            domain_name="single_payer",
            description="Universal healthcare via single government payer",
            concepts={
                "universal_coverage": [
                    ConceptExpression(
                        pattern=r"all\s+(?:residents|citizens|individuals|persons)",
                        context_clues=["covered", "eligible", "qualify"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"universal\s+(?:health\s+)?coverage",
                        context_clues=[],
                        confidence_boost=0.3,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"single-?payer",
                        context_clues=["system", "healthcare", "program"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                ],
                "zero_cost_sharing": [
                    ConceptExpression(
                        pattern=r"no\s+(?:copayment|copay|coinsurance|deductible)s?",
                        context_clues=["zero", "free", "no cost"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"zero[- ]out[- ]of[- ]pocket",
                        context_clues=[],
                        confidence_boost=0.3,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"eliminate[d]?\s+(?:out[- ]of[- ]pocket|patient\s+cost)",
                        context_clues=[],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                ],
                "payroll_tax_funding": [
                    ConceptExpression(
                        pattern=r"payroll\s+(?:tax|contribution|assessment)",
                        context_clues=["employer", "employee", "wage", "salary"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"(\d+(?:\.\d+)?)\s*%\s+(?:of\s+)?(?:payroll|wage|earnings)",
                        context_clues=["tax", "fund", "financing"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"employer\s+and\s+employee\s+contribution",
                        context_clues=["payroll", "withhold", "assessment"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "income_tax_funding": [
                    ConceptExpression(
                        pattern=r"(?:general\s+)?(?:income\s+)?tax(?:es)?",
                        context_clues=["fund", "finance", "pay for", "revenue"],
                        confidence_boost=0.15,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"progressive\s+(?:income\s+)?tax",
                        context_clues=[],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "existing_spending_redirect": [
                    ConceptExpression(
                        pattern=r"(?:redirect|reallocate|consolidate|transfer)[^.]*?(?:Medicare|Medicaid|VA|CHIP|federal\s+health)",
                        context_clues=["existing", "current", "program"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"eliminate\s+(?:redundant\s+)?(?:private\s+)?insurance\s+premium",
                        context_clues=["redirect", "savings"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "administrative_savings": [
                    ConceptExpression(
                        pattern=r"(?:reduce|eliminate)\s+(?:administrative|billing|insurance)\s+overhead",
                        context_clues=["efficiency", "savings", "cost"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"administrative\s+(?:efficiency|savings|reduction)",
                        context_clues=["percent", "%", "billion"],
                        confidence_boost=0.15,
                        is_regex=True
                    ),
                ],
                "transaction_tax_funding": [
                    ConceptExpression(
                        pattern=r"financial\s+transaction\s+tax",
                        context_clues=["FTT", "trade", "stock", "revenue"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"(?:FTT|transaction\s+fee)",
                        context_clues=["financial", "trading", "fund"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "excise_tax_funding": [
                    ConceptExpression(
                        pattern=r"excise\s+tax",
                        context_clues=["luxury", "unhealthy", "reallocate", "revenue"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"(?:luxury\s+goods|unhealthy\s+products)\s+tax",
                        context_clues=["excise", "revenue"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "tariff_funding": [
                    ConceptExpression(
                        pattern=r"import\s+tariff",
                        context_clues=["allocation", "revenue", "percent"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"tariff\s+revenue",
                        context_clues=["import", "allocation", "healthcare"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "premium_conversion": [
                    ConceptExpression(
                        pattern=r"(?:employer|employee)[^.]{0,100}premium[^.]{0,100}(?:convert|redirect|replace)",
                        context_clues=["payroll", "contribution", "health insurance"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"health\s+insurance\s+premium[^.]{0,100}(?:payroll|contribution)",
                        context_clues=["convert", "replace", "redirect"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "program_consolidation": [
                    ConceptExpression(
                        pattern=r"(?:SNAP|WIC|school\s+lunch|nutrition)[^.]{0,100}(?:consolidat|transfer|integrat)",
                        context_clues=["program", "social", "health"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"consolidat(?:e|ion)[^.]{0,100}(?:federal|social|nutrition)",
                        context_clues=["program", "SNAP", "WIC"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "pharmaceutical_savings": [
                    ConceptExpression(
                        pattern=r"(?:drug|pharmaceutical)\s+(?:pricing|negotiation)",
                        context_clues=["savings", "most-favored-nation", "reform"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"most[- ]favored[- ]nation",
                        context_clues=["drug", "pharmaceutical", "pricing"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "reinsurance_mechanism": [
                    ConceptExpression(
                        pattern=r"reinsurance\s+pool",
                        context_clues=["transitional", "high-cost", "claims"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                ],
                "dsh_gme_funding": [
                    ConceptExpression(
                        pattern=r"(?:disproportionate\s+share\s+hospital|DSH)",
                        context_clues=["fund", "follow", "patients", "provider"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"(?:graduate\s+medical\s+education|GME)",
                        context_clues=["fund", "follow", "patients", "training"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "inflation_adjustment": [
                    ConceptExpression(
                        pattern=r"(?:health\s+)?inflation\s+escalator",
                        context_clues=["automatic", "CPI", "medical", "adjustment"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"(?:medical\s+care|CPI[- ]U)\s+component",
                        context_clues=["exceed", "inflation", "automatic"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "eitc_rebate": [
                    ConceptExpression(
                        pattern=r"(?:Earned\s+Income\s+Tax\s+Credit|EITC)",
                        context_clues=["expansion", "rebate", "low earner", "low income"],
                        confidence_boost=0.25,
                        is_regex=True
                    ),
                    ConceptExpression(
                        pattern=r"low\s+earner[s]?\s+(?:rebate|credit|exemption)",
                        context_clues=["EITC", "income", "payroll"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
            },
            required_concepts={"universal_coverage", "zero_cost_sharing"},
            scoring_weights={
                "universal_coverage": 0.15,
                "zero_cost_sharing": 0.15,
                "payroll_tax_funding": 0.08,
                "income_tax_funding": 0.08,
                "existing_spending_redirect": 0.08,
                "administrative_savings": 0.04,
                "transaction_tax_funding": 0.04,
                "excise_tax_funding": 0.04,
                "tariff_funding": 0.04,
                "premium_conversion": 0.04,
                "program_consolidation": 0.04,
                "pharmaceutical_savings": 0.04,
                "reinsurance_mechanism": 0.04,
                "dsh_gme_funding": 0.04,
                "inflation_adjustment": 0.04,
                "eitc_rebate": 0.04,
            }
        )
    
    def _build_universal_coverage_taxonomy(self) -> ConceptTaxonomy:
        """Taxonomy for policies targeting universal coverage (not necessarily single-payer)."""
        return ConceptTaxonomy(
            domain_name="universal_coverage",
            description="Policies that aim for universal or near-universal coverage",
            concepts={
                "coverage_mandate": [
                    ConceptExpression(
                        pattern=r"individual\s+mandate|mandate(?:d)?\s+(?:health\s+)?insurance",
                        context_clues=["penalty", "requirement", "all"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "expanded_eligibility": [
                    ConceptExpression(
                        pattern=r"(?:expand|increase)\s+(?:eligibility|enrollment|coverage)",
                        context_clues=["percent", "million", "population"],
                        confidence_boost=0.15,
                        is_regex=True
                    ),
                ],
            },
            required_concepts=set(),
            scoring_weights={}
        )
    
    def _build_multi_payer_taxonomy(self) -> ConceptTaxonomy:
        """Taxonomy for multi-payer / regulated private insurance systems."""
        return ConceptTaxonomy(
            domain_name="multi_payer",
            description="Policies that maintain multiple payers with regulation",
            concepts={
                "insurance_regulation": [
                    ConceptExpression(
                        pattern=r"(?:regulate|regulated|regulation)\s+(?:private\s+)?insurance",
                        context_clues=["coverage", "rates", "benefits"],
                        confidence_boost=0.2,
                        is_regex=True
                    ),
                ],
                "price_controls": [
                    ConceptExpression(
                        pattern=r"(?:price|rate)\s+(?:control|regulation|cap|limit)",
                        context_clues=["drug", "prescription", "provider"],
                        confidence_boost=0.15,
                        is_regex=True
                    ),
                ],
            },
            required_concepts=set(),
            scoring_weights={}
        )
    
    def extract_from_text(self, text: str, policy_name: str = "Unknown Policy") -> Dict[str, List[ExtractedConcept]]:
        """
        Extract all semantic concepts from policy text.
        
        Returns:
            Dict mapping concept types to extracted concepts
        """
        extracted: Dict[str, List[ExtractedConcept]] = {}
        
        # Section identification (heuristic)
        sections = self._identify_sections(text)
        
        # For each taxonomy, extract concepts
        for taxonomy_name, taxonomy in self.taxonomies.items():
            for concept_name, expressions in taxonomy.concepts.items():
                for expr in expressions:
                    matches = self._find_concept_matches(
                        text=text,
                        pattern=expr.pattern,
                        is_regex=expr.is_regex,
                        context_clues=expr.context_clues,
                        confidence_boost=expr.confidence_boost
                    )
                    
                    for match in matches:
                        concept = ExtractedConcept(
                            concept_type=ConceptType.REVENUE_SOURCE,
                            concept_name=concept_name,
                            value=match["value"],
                            source_text=match["source_text"],
                            confidence=match["confidence"],
                            section=match.get("section"),
                        )
                        
                        key = f"{taxonomy_name}/{concept_name}"
                        if key not in extracted:
                            extracted[key] = []
                        extracted[key].append(concept)
        
        return extracted
    
    def _identify_sections(self, text: str) -> Dict[str, Tuple[int, int]]:
        """Identify major sections in legislative text (Section 1, Section 2, etc.)."""
        sections = {}
        pattern = r'(?:^|\n)\*\*?(?:Section|Sec\.?)\s+(\d+)[.\s]+([^\n]*)'
        
        for match in re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE):
            section_num = match.group(1)
            section_title = match.group(2)
            start = match.start()
            sections[f"Section {section_num}"] = (start, len(text))
        
        return sections
    
    def _find_concept_matches(
        self,
        text: str,
        pattern: str,
        is_regex: bool,
        context_clues: List[str],
        confidence_boost: float
    ) -> List[Dict]:
        """Find matches of a concept expression in text."""
        matches = []
        
        if is_regex:
            for match in re.finditer(pattern, text, re.IGNORECASE | re.DOTALL):
                source_text = text[max(0, match.start() - 100):min(len(text), match.end() + 100)]
                
                # Check for context clues nearby
                context_match_count = sum(
                    1 for clue in context_clues
                    if re.search(clue, source_text, re.IGNORECASE)
                )
                confidence = min(0.5 + confidence_boost + (context_match_count * 0.1), 1.0)
                
                matches.append({
                    "value": match.group(0),
                    "source_text": source_text.strip(),
                    "confidence": confidence,
                    "section": None,
                })
        else:
            # Exact phrase matching
            if pattern.lower() in text.lower():
                idx = text.lower().find(pattern.lower())
                source_text = text[max(0, idx - 100):min(len(text), idx + len(pattern) + 100)]
                context_match_count = sum(
                    1 for clue in context_clues
                    if re.search(clue, source_text, re.IGNORECASE)
                )
                confidence = min(0.6 + confidence_boost + (context_match_count * 0.1), 1.0)
                
                matches.append({
                    "value": pattern,
                    "source_text": source_text.strip(),
                    "confidence": confidence,
                    "section": None,
                })
        
        return matches
    
    def assess_policy_type(self, text: str) -> Tuple[str, float]:
        """
        Assess which policy domain/taxonomy this text best matches.
        
        Returns:
            (best_matching_domain, confidence_score)
        """
        scores: Dict[str, float] = {}
        
        for taxonomy_name, taxonomy in self.taxonomies.items():
            total_score = 0.0
            concepts_found = 0
            
            for concept_name, expressions in taxonomy.concepts.items():
                for expr in expressions:
                    if expr.is_regex:
                        if re.search(expr.pattern, text, re.IGNORECASE | re.DOTALL):
                            weight = taxonomy.scoring_weights.get(concept_name, 0.1)
                            total_score += weight
                            concepts_found += 1
                    else:
                        if expr.pattern.lower() in text.lower():
                            weight = taxonomy.scoring_weights.get(concept_name, 0.1)
                            total_score += weight
                            concepts_found += 1
            
            # Bonus for finding required concepts
            required_found = 0
            for req_concept in taxonomy.required_concepts:
                if req_concept in taxonomy.concepts:
                    for expr in taxonomy.concepts[req_concept]:
                        if expr.is_regex:
                            if re.search(expr.pattern, text, re.IGNORECASE):
                                required_found += 1
                                break
                        else:
                            if expr.pattern.lower() in text.lower():
                                required_found += 1
                                break
            
            required_boost = (required_found / len(taxonomy.required_concepts)) if taxonomy.required_concepts else 0.0
            scores[taxonomy_name] = total_score + (required_boost * 0.3)
        
        if not scores:
            return ("unknown", 0.0)
        
        best_domain = max(scores, key=scores.get)
        return (best_domain, min(scores[best_domain], 1.0))


def create_context_aware_extractor() -> PolicyContextExtractor:
    """Factory function to create a configured extractor."""
    return PolicyContextExtractor()
