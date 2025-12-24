"""
Policy Mechanics Builder
Translates extracted concepts into structured PolicyMechanics.

This layer sits between the raw concept extraction and the final simulation-ready format.
It handles:
1. Concept composition (combining related concepts)
2. Quantitative inference (extracting % values, dollar amounts, timeline dates)
3. Confidence aggregation (combining concept-level confidence into domain-level)
4. Dependency validation (ensuring required concepts are present)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import re
import json
from datetime import datetime, timedelta

from core.policy_context_framework import (
    ExtractedConcept, ConceptType, PolicyContextExtractor, create_context_aware_extractor
)


@dataclass
class ExtractedQuantity:
    """Quantitative information extracted from text."""
    value: float
    unit: str  # %, $B (billion), years, months, etc.
    confidence: float
    context: str  # Brief context (e.g., "payroll tax rate")


@dataclass
class ConceptComposite:
    """Related concepts grouped by semantic meaning."""
    theme: str  # e.g., "funding", "coverage", "timeline"
    constituent_concepts: List[ExtractedConcept]
    derived_value: Optional[Any] = None
    confidence: float = 0.0
    
    def __post_init__(self):
        if not self.confidence:
            self.confidence = sum(c.confidence for c in self.constituent_concepts) / max(1, len(self.constituent_concepts))


class QuantityExtractor:
    """Extract and normalize quantities from legislative text."""
    
    @staticmethod
    def extract_percentage(text: str, context_type: str = None) -> List[ExtractedQuantity]:
        """
        Find percentage values in text with optional context filtering.
        
        Args:
            text: The text to search
            context_type: Optional filter for percentage type:
                - 'tax_rate': 1-25% range, near tax/payroll/income keywords
                - 'gdp': 0-30% range, near GDP/gross domestic product
                - 'efficacy': 0-100% range, near effective/probability/evidence
                - None: Extract all percentages 0-100%
        
        Returns:
            List of ExtractedQuantity objects with confidence based on context match
        """
        quantities = []
        pattern = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
        
        # Context keywords for different percentage types
        context_keywords = {
            'tax_rate': ['tax', 'payroll', 'income', 'rate', 'levy', 'contribution', 'premium'],
            'gdp': ['gdp', 'gross domestic product', 'economy', 'economic output'],
            'efficacy': ['effective', 'probability', 'evidence', 'success', 'outcome', 'result']
        }
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            
            # Get surrounding context (200 chars on each side)
            context_start = max(0, match.start() - 200)
            context_end = min(len(text), match.end() + 200)
            context = text[context_start:context_end]
            
            # Base confidence
            confidence = 0.7
            
            # Apply context type filtering
            if context_type:
                # Check if any context keywords appear near the percentage
                keywords = context_keywords.get(context_type, [])
                context_lower = context.lower()
                keyword_found = any(kw in context_lower for kw in keywords)
                
                if not keyword_found:
                    continue  # Skip percentages that don't match context type
                
                # Boost confidence if keyword is very close (within 50 chars)
                close_context = text[max(0, match.start() - 50):match.end() + 50].lower()
                if any(kw in close_context for kw in keywords):
                    confidence = 0.9
                else:
                    confidence = 0.75
            
            # Range validation based on context type
            valid_range = True
            if context_type == 'tax_rate' and not (1 <= value <= 50):
                valid_range = False  # Tax rates typically 1-50%
            elif context_type == 'gdp' and not (0 <= value <= 50):
                valid_range = False  # GDP percentages typically 0-50%
            elif context_type == 'efficacy' and not (0 <= value <= 100):
                valid_range = False  # Efficacy can be 0-100%
            elif not context_type and not (0 <= value <= 100):
                valid_range = False  # General sanity check
            
            if not valid_range:
                continue
            
            # Get compact context (40 chars each side for display)
            display_context = text[max(0, match.start() - 40):match.end() + 40].strip()
            
            quantities.append(ExtractedQuantity(
                value=value,
                unit="%",
                confidence=confidence,
                context=display_context
            ))
        
        return quantities
    
    @staticmethod
    def extract_currency(text: str) -> List[ExtractedQuantity]:
        """Find currency amounts (billions/trillions)."""
        quantities = []
        pattern = r'\$\s*(\d+(?:\.\d+)?)\s*(?:billion|trillion|B|T|bn|tr)'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = float(match.group(1))
            unit_match = re.search(r'(billion|trillion|B|T|bn|tr)', match.group(0), re.IGNORECASE)
            unit = unit_match.group(0).lower() if unit_match else "B"
            
            context = text[max(0, match.start() - 40):match.end() + 40]
            quantities.append(ExtractedQuantity(
                value=value,
                unit=unit,
                confidence=0.85,
                context=context.strip()
            ))
        
        return quantities
    
    @staticmethod
    def extract_timeline(text: str) -> List[ExtractedQuantity]:
        """Find timeline indicators (years, dates, phases)."""
        quantities = []
        pattern = r'(\d+)\s*(?:year|month|quarter|week)s?'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = int(match.group(1))
            unit = re.search(r'(year|month|quarter|week)', match.group(0), re.IGNORECASE).group(1).lower()
            
            context = text[max(0, match.start() - 40):match.end() + 40]
            quantities.append(ExtractedQuantity(
                value=value,
                unit=unit,
                confidence=0.8,
                context=context.strip()
            ))
        
        return quantities
    
    @staticmethod
    def extract_dates(text: str) -> List[ExtractedQuantity]:
        """Find specific dates."""
        quantities = []
        # Common date patterns
        patterns = [
            r'(?:on|by)\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+(?:,?\s+\d{4})?',
            r'(?:on|by)\s+\d+/\d+/\d{4}',
            r'(?:on|by)\s+\d{4}(?:-\d{2}){2}',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context = text[max(0, match.start() - 40):match.end() + 40]
                quantities.append(ExtractedQuantity(
                    value=0,  # Placeholder; actual date parsing needed
                    unit="date",
                    confidence=0.7,
                    context=context.strip()
                ))
        
        return quantities


class PolicyMechanicsBuilder:
    """Build structured mechanics from extracted concepts."""
    
    def __init__(self):
        self.extractor = create_context_aware_extractor()
        self.quantity_extractor = QuantityExtractor()
    
    def build_from_text(self, text: str, policy_name: str = "Unknown Policy") -> Dict[str, Any]:
        """
        Complete workflow: extract concepts → compose → build mechanics.
        
        Returns:
            Dictionary representation of PolicyMechanics with full traceability
        """
        # Step 1: Assess policy type
        policy_type, type_confidence = self.extractor.assess_policy_type(text)
        
        # Step 2: Extract all concepts
        extracted_concepts = self.extractor.extract_from_text(text, policy_name)
        
        # Step 3: Extract quantities
        percentages = self.quantity_extractor.extract_percentage(text)
        currencies = self.quantity_extractor.extract_currency(text)
        timelines = self.quantity_extractor.extract_timeline(text)
        
        # Step 4: Build composites from related concepts
        composites = self._build_composites(extracted_concepts, percentages, currencies, timelines)
        
        # Step 5: Construct mechanics dict
        mechanics = {
            "policy_name": policy_name,
            "policy_type": policy_type,
            "type_confidence": type_confidence,
            "extracted_at": datetime.now().isoformat(),
            
            # Concepts and composites
            "concepts": {k: [
                {
                    "concept_name": c.concept_name,
                    "value": c.value,
                    "confidence": c.confidence,
                    "source_text": c.source_text[:200],  # Truncate for readability
                    "section": c.section,
                }
                for c in v
            ] for k, v in extracted_concepts.items()},
            
            "composites": [
                {
                    "theme": comp.theme,
                    "constituent_count": len(comp.constituent_concepts),
                    "derived_value": comp.derived_value,
                    "confidence": comp.confidence,
                }
                for comp in composites
            ],
            
            # Quantities
            "quantities": {
                "percentages": [
                    {"value": q.value, "unit": q.unit, "confidence": q.confidence, "context": q.context[:100]}
                    for q in percentages
                ],
                "currencies": [
                    {"value": q.value, "unit": q.unit, "confidence": q.confidence, "context": q.context[:100]}
                    for q in currencies
                ],
                "timelines": [
                    {"value": q.value, "unit": q.unit, "confidence": q.confidence, "context": q.context[:100]}
                    for q in timelines
                ],
            },
            
            # Assessment
            "assessment": self._assess_completeness(extracted_concepts, policy_type),
        }
        
        return mechanics
    
    def _build_composites(
        self,
        concepts: Dict[str, List[ExtractedConcept]],
        percentages: List[ExtractedQuantity],
        currencies: List[ExtractedQuantity],
        timelines: List[ExtractedQuantity],
    ) -> List[ConceptComposite]:
        """Group related concepts into themes."""
        composites = []
        
        # Funding theme
        funding_concepts = [
            c for key, clist in concepts.items()
            for c in clist
            if "funding" in key.lower() or "revenue" in key.lower() or "tax" in key.lower()
        ]
        if funding_concepts:
            composites.append(ConceptComposite(
                theme="funding",
                constituent_concepts=funding_concepts,
                derived_value={
                    "total_mechanisms": len(funding_concepts),
                    "percentages_found": len(percentages),
                    "currencies_found": len(currencies),
                }
            ))
        
        # Coverage theme
        coverage_concepts = [
            c for key, clist in concepts.items()
            for c in clist
            if "coverage" in key.lower() or "cost" in key.lower()
        ]
        if coverage_concepts:
            composites.append(ConceptComposite(
                theme="coverage",
                constituent_concepts=coverage_concepts,
            ))
        
        # Implementation theme
        timeline_concepts = [
            c for key, clist in concepts.items()
            for c in clist
            if "timeline" in key.lower() or "phase" in key.lower()
        ]
        implementation_items = timeline_concepts + timelines  # Type mismatch but conceptually similar
        if implementation_items:
            composites.append(ConceptComposite(
                theme="implementation",
                constituent_concepts=timeline_concepts,
                derived_value={
                    "timeline_indicators": len(timelines),
                }
            ))
        
        return composites
    
    def _assess_completeness(self, concepts: Dict[str, List[ExtractedConcept]], policy_type: str) -> Dict[str, Any]:
        """Check if key concepts for this policy type are present."""
        assessment = {
            "policy_type": policy_type,
            "concepts_found": len(concepts),
            "gaps": [],
            "strengths": [],
            "overall_confidence": 0.0,
        }
        
        # Check for expected concepts by policy type
        expected_concepts = {
            "single_payer": [
                "single_payer/universal_coverage",
                "single_payer/zero_cost_sharing",
                "single_payer/payroll_tax_funding",
            ],
            "universal_coverage": [
                "universal_coverage/coverage_mandate",
            ],
            "multi_payer": [
                "multi_payer/insurance_regulation",
            ],
        }
        
        if policy_type in expected_concepts:
            for expected in expected_concepts[policy_type]:
                if expected in concepts and concepts[expected]:
                    assessment["strengths"].append(expected)
                else:
                    assessment["gaps"].append(expected)
        
        # Overall confidence
        total_concepts = sum(len(v) for v in concepts.values())
        expected_count = len(expected_concepts.get(policy_type, []))
        found_count = len(assessment["strengths"])
        
        if expected_count > 0:
            assessment["overall_confidence"] = min(found_count / expected_count, 1.0)
        elif total_concepts > 0:
            assessment["overall_confidence"] = min(total_concepts / 8.0, 1.0)  # Heuristic
        
        return assessment


def extract_policy_context(text: str, policy_name: str = "Unknown Policy") -> Dict[str, Any]:
    """Convenience function to extract context from policy text."""
    builder = PolicyMechanicsBuilder()
    return builder.build_from_text(text, policy_name)
