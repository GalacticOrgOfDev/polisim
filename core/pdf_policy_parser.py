"""
PDF Policy Parser Module
Extracts policy parameters from PDF documents like the United States Galactic Health Act.
Supports document upload, text extraction, and parameter parsing.

Features:
- Extract text from PDF files
- Parse policy sections and identify parameters
- Convert PDF policies into CustomPolicy objects
- Handle complex legislative language
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum

from core.validation import InputValidator, ValidationError


@dataclass
class PolicyExtraction:
    """Results from PDF policy extraction."""
    title: str
    source_file: str
    extracted_date: str
    text_content: str
    identified_parameters: Dict[str, Any]
    legislative_sections: Dict[str, str]
    fiscal_impact_estimates: Dict[str, float]
    confidence_score: float  # 0-1 indicating extraction quality


class PolicyKeywordMatcher:
    """Matches keywords in policy text to identify parameters and sections."""
    
    # Healthcare-specific keywords
    HEALTHCARE_KEYWORDS = {
        "coverage": [
            "universal", "coverage", "zero.*out.*of.*pocket", "uninsured",
            "coverage rate", "percent.*covered", "beneficiaries"
        ],
        "spending": [
            "spending", "expenditure", "billion", "trillion", "cost",
            "health.*spending.*gdp", "healthcare.*budget"
        ],
        "benefits": [
            "benefit", "opt.*out", "voucher", "supplement", "deductible",
            "copayment", "copay", "coinsurance"
        ],
        "costs": [
            "pharmaceutical", "drug", "prescription", "device",
            "price", "pricing", "cost.*reduction", "negotiat"
        ],
        "providers": [
            "provider", "hospital", "physician", "doctor", "payment",
            "reimbursement", "fee.*schedule"
        ],
        "innovation": [
            "innovation", "biomedical", "research", "development",
            "accelerate", "moonshot", "breakthrough"
        ]
    }
    
    # Tax-specific keywords
    TAX_KEYWORDS = {
        "income_tax": [
            "income.*tax", "marginal.*rate", "tax.*bracket",
            "progressive", "tax.*on.*income"
        ],
        "corporate_tax": [
            "corporate.*tax", "business.*tax", "c.*corporation",
            "corporate.*rate"
        ],
        "payroll_tax": [
            "payroll.*tax", "fica", "social.*security.*tax",
            "medicare.*tax", "employee.*contribution"
        ],
        "capital_gains": [
            "capital.*gains", "investment.*income",
            "long.*term.*gains", "short.*term.*gains"
        ],
        "wealth_tax": [
            "wealth.*tax", "net.*worth", "billionaire",
            "ultra.*high.*net.*worth"
        ],
    }
    
    # Spending-specific keywords
    SPENDING_KEYWORDS = {
        "defense": [
            "defense", "military", "pentagon", "armed.*forces",
            "defense.*spending"
        ],
        "discretionary": [
            "discretionary", "appropriations", "annual.*budget",
            "non.*defense", "discretionary.*spending"
        ],
        "mandatory": [
            "mandatory", "entitlement", "social.*security",
            "medicare", "medicaid"
        ],
    }
    
    @classmethod
    def extract_fiscal_numbers(cls, text: str) -> Dict[str, float]:
        """Extract dollar amounts and percentages from text."""
        results = {}
        
        # Pattern for billions/trillions - improved capturing groups
        large_num_pattern = r'(\$?\d+(?:\.\d+)?)\s*(billion|billion\s*dollars?|B|trillion|trillion\s*dollars?|T)(?:\s|$|[^\w])'
        for match in re.finditer(large_num_pattern, text, re.IGNORECASE):
            amount_str = match.group(1).replace('$', '')
            unit_str = match.group(2).lower()  # Get the full unit string
            unit = unit_str[0]  # Get first character (B or T)
            try:
                amount = float(amount_str)
                if unit == 't':
                    amount *= 1000  # Convert to billions
                results[match.group(0)] = amount
            except (ValueError, IndexError):
                continue
        
        # Pattern for percentages
        pct_pattern = r'(\d+(?:\.\d+)?)\s*(?:percent|%)'
        for match in re.finditer(pct_pattern, text):
            try:
                pct = float(match.group(1))
                results[match.group(0)] = pct
            except ValueError:
                continue
        
        return results
    
    @classmethod
    def extract_years(cls, text: str) -> List[int]:
        """Extract year references from text."""
        years = []
        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        for match in re.finditer(year_pattern, text):
            try:
                year = int(match.group(1))
                if 1990 <= year <= 2100:
                    years.append(year)
            except ValueError:
                continue
        return sorted(list(set(years)))
    
    @classmethod
    def extract_policy_sections(cls, text: str) -> Dict[str, str]:
        """Extract major policy sections from text."""
        sections = {}
        
        # Pattern for section headers (e.g., "Sec. 5. Coverage provisions")
        section_pattern = r'(?:Sec(?:tion)?\.?\s*(\d+)\.?\s*-?\s*([^\n]+))'
        
        lines = text.split('\n')
        current_section = None
        section_content = []
        
        for line in lines:
            match = re.match(section_pattern, line, re.IGNORECASE)
            if match:
                if current_section:
                    sections[current_section] = '\n'.join(section_content)
                current_section = f"Section {match.group(1)}: {match.group(2)}"
                section_content = []
            elif current_section:
                section_content.append(line)
        
        if current_section:
            sections[current_section] = '\n'.join(section_content)
        
        return sections
    
    @classmethod
    def match_keywords(cls, text: str, category: str = "healthcare") -> Dict[str, int]:
        """Count keyword matches by category."""
        if category == "healthcare":
            keywords = cls.HEALTHCARE_KEYWORDS
        elif category == "tax":
            keywords = cls.TAX_KEYWORDS
        elif category == "spending":
            keywords = cls.SPENDING_KEYWORDS
        else:
            return {}
        
        matches = {}
        for keyword_type, patterns in keywords.items():
            count = 0
            for pattern in patterns:
                count += len(re.findall(pattern, text, re.IGNORECASE))
            matches[keyword_type] = count
        
        return matches


class PolicyPDFProcessor:
    """Process and extract data from policy PDF files."""
    
    def __init__(self):
        """Initialize PDF processor."""
        self.upload_dir = Path("policies/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_uploaded_file(self, file_path: Path, file_content: bytes) -> bool:
        """Save uploaded PDF file."""
        try:
            destination = self.upload_dir / file_path.name
            destination.write_bytes(file_content)
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    
    def extract_text_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file.
        
        Note: This is a placeholder. In production, use:
        - pdfplumber for better text extraction
        - pypdf for PDF manipulation
        - pytesseract for OCR of scanned documents
        
        For now, assumes text-based PDFs can be read.
        """
        try:
            # Validate file size (Safety #1)
            try:
                InputValidator.validate_file_size(file_path)
            except ValidationError as e:
                return f"[PDF file size validation failed: {str(e)}]"
            
            # Try pdfplumber first
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text.append(page.extract_text() or "")
                return "\n".join(text)
            except ImportError:
                pass
            
            # Fallback: Try pypdf
            try:
                from pypdf import PdfReader
                text = []
                reader = PdfReader(file_path)
                for page in reader.pages:
                    text.append(page.extract_text() or "")
                return "\n".join(text)
            except ImportError:
                pass
            
            # If no PDF library available, return error
            return "[PDF extraction requires pdfplumber or pypdf - install with: pip install pdfplumber]"
        
        except Exception as e:
            return f"[Error extracting PDF: {str(e)}]"
    
    def analyze_policy_text(self, text: str, policy_title: str = "", policy_type: str = None) -> PolicyExtraction:
        """Analyze policy text and extract parameters.
        
        Args:
            text: The policy text to analyze
            policy_title: Title of the policy
            policy_type: Type of policy (healthcare, tax_reform, spending_reform, combined, custom)
                        If provided, extraction will focus on matching parameters for this type
        """
        from datetime import datetime
        from core.policy_mechanics_extractor import extract_policy_mechanics, mechanics_to_dict
        
        # Unified extraction across all domains (healthcare, tax, Social Security, spending)
        try:
            extraction_policy_type = policy_type if policy_type else "combined"
            mechanics = extract_policy_mechanics(text, policy_type=extraction_policy_type)
            structured = mechanics_to_dict(mechanics)
            identified_parameters = {
                "category": mechanics.policy_type,
                "confidence_score": mechanics.confidence_score,
                "structured_mechanics": structured,
                "domains_detected": {
                    "healthcare": bool(structured.get("funding_mechanisms")),
                    "tax": structured.get("tax_mechanics") is not None,
                    "social_security": structured.get("social_security_mechanics") is not None,
                    "spending": structured.get("spending_mechanics") is not None,
                },
            }

            sections = mechanics.source_sections if mechanics.source_sections else {}
            fiscal_impact = {}

            return PolicyExtraction(
                title=policy_title or mechanics.policy_name,
                source_file=str(Path.cwd()),
                extracted_date=datetime.now().isoformat(),
                text_content=text[:5000],
                identified_parameters=identified_parameters,
                legislative_sections=sections,
                fiscal_impact_estimates=fiscal_impact,
                confidence_score=mechanics.confidence_score,
            )
        except Exception as e:
            # Fall back to heuristic extraction if structured extraction fails
            print(f"Structured extraction failed, falling back to heuristic extraction: {e}")
        
        # Fallback to old extraction method
        
        # Extract fiscal numbers
        fiscal_numbers = PolicyKeywordMatcher.extract_fiscal_numbers(text)
        
        # Extract years
        years = PolicyKeywordMatcher.extract_years(text)
        
        # Extract sections
        sections = PolicyKeywordMatcher.extract_policy_sections(text)
        
        # Determine policy category based on policy_type hint or auto-detect from content
        if policy_type:
            # Use the provided policy type to guide extraction
            category = policy_type.lower() if isinstance(policy_type, str) else policy_type.value
            # Map custom types to keyword match categories
            if category == "healthcare":
                matches = PolicyKeywordMatcher.match_keywords(text, "healthcare")
            elif category in ["tax_reform", "tax"]:
                matches = PolicyKeywordMatcher.match_keywords(text, "tax")
            elif category in ["spending_reform", "spending"]:
                matches = PolicyKeywordMatcher.match_keywords(text, "spending")
            elif category in ["combined", "custom"]:
                # For combined/custom, check all categories
                healthcare_matches = PolicyKeywordMatcher.match_keywords(text, "healthcare")
                tax_matches = PolicyKeywordMatcher.match_keywords(text, "tax")
                spending_matches = PolicyKeywordMatcher.match_keywords(text, "spending")
                # Merge all matches
                matches = {**healthcare_matches, **tax_matches, **spending_matches}
            else:
                matches = {}
        else:
            # Auto-detect category from content
            healthcare_matches = PolicyKeywordMatcher.match_keywords(text, "healthcare")
            tax_matches = PolicyKeywordMatcher.match_keywords(text, "tax")
            spending_matches = PolicyKeywordMatcher.match_keywords(text, "spending")
            
            # Determine primary category
            max_healthcare = max(healthcare_matches.values()) if healthcare_matches else 0
            max_tax = max(tax_matches.values()) if tax_matches else 0
            max_spending = max(spending_matches.values()) if spending_matches else 0
            
            if max_healthcare >= max_tax and max_healthcare >= max_spending:
                category = "healthcare"
                matches = healthcare_matches
            elif max_tax >= max_spending:
                category = "tax"
                matches = tax_matches
            else:
                category = "spending"
                matches = spending_matches
        
        # Calculate confidence score based on:
        # - Number of identified sections (0-0.3)
        # - Number of fiscal figures (0-0.3)
        # - Number of keyword matches (0-0.4)
        confidence = 0.0
        confidence += min(len(sections) / 20, 0.3)
        confidence += min(len(fiscal_numbers) / 10, 0.3)
        confidence += min(sum(matches.values()) / 50, 0.4)
        
        identified_parameters = {
            "category": category,
            "keyword_matches": matches,
            "fiscal_numbers": fiscal_numbers,
            "years_mentioned": years,
            "num_sections": len(sections),
        }
        
        fiscal_impact = {}
        for num_desc, amount in list(fiscal_numbers.items())[:10]:
            fiscal_impact[num_desc] = amount
        
        return PolicyExtraction(
            title=policy_title or "Extracted Policy",
            source_file=str(Path.cwd()),
            extracted_date=datetime.now().isoformat(),
            text_content=text[:5000],  # Store first 5000 chars
            identified_parameters=identified_parameters,
            legislative_sections=sections,
            fiscal_impact_estimates=fiscal_impact,
            confidence_score=min(confidence, 1.0),
        )
    
    def create_policy_from_extraction(
        self,
        extraction: PolicyExtraction,
        policy_name: str,
        policy_type: str = None
    ) -> "CustomPolicy":
        """Create CustomPolicy from extraction results.
        
        Args:
            extraction: PolicyExtraction object from analyze_policy_text
            policy_name: Name for the new policy
            policy_type: Override policy type (healthcare, tax_reform, spending_reform, combined, custom)
        """
        from core.policy_builder import CustomPolicy, PolicyType
        
        # Map category to policy type
        category_to_type = {
            "healthcare": PolicyType.HEALTHCARE,
            "tax_reform": PolicyType.TAX_REFORM,
            "tax": PolicyType.TAX_REFORM,
            "spending_reform": PolicyType.SPENDING_REFORM,
            "spending": PolicyType.SPENDING_REFORM,
            "combined": PolicyType.COMBINED,
            "custom": PolicyType.CUSTOM,
        }
        
        # Use provided policy_type if given, otherwise infer from extraction
        if policy_type:
            category = policy_type.lower() if isinstance(policy_type, str) else policy_type.value
            mapped_type = category_to_type.get(category, PolicyType.CUSTOM)
        else:
            category = extraction.identified_parameters.get("category", "healthcare")
            mapped_type = category_to_type.get(category, PolicyType.CUSTOM)
        
        policy = CustomPolicy(
            name=policy_name,
            description=f"Extracted from: {extraction.title}",
            policy_type=mapped_type,
            author="PDF Upload",
        )

        # Preserve structured mechanics for context-aware simulation
        if "structured_mechanics" in extraction.identified_parameters:
            policy.structured_mechanics = extraction.identified_parameters["structured_mechanics"]
        
        # Add parameters based on extracted fiscal numbers
        for desc, amount in extraction.fiscal_impact_estimates.items():
            if amount > 0:
                policy.add_parameter(
                    name=desc.replace('$', '').replace(' ', '_').lower()[:30],
                    description=desc,
                    value=amount,
                    min_val=amount * 0.5,
                    max_val=amount * 1.5,
                    unit="$B" if amount > 1 else "$M",
                    category=category,
                )
        
        return policy


# Convenience function
def process_policy_pdf(file_path: Path, policy_title: str = "") -> Optional[PolicyExtraction]:
    """Process a policy PDF file."""
    processor = PolicyPDFProcessor()
    text = processor.extract_text_from_pdf(file_path)
    return processor.analyze_policy_text(text, policy_title)
