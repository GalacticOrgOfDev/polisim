"""
Custom Policy Builder Module
Allows users to create and modify fiscal policies with adjustable parameters.
Supports saving/loading custom policies and scenario modeling.

Architecture:
- PolicyTemplate: Base policy structure with adjustable parameters
- CustomPolicy: User-defined policy with parameters
- PolicyBuilder: Factory for creating policies from templates
- PolicyLibrary: Manages multiple policies
"""

import io
import json
import zipfile
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
from datetime import datetime


class PolicyType(Enum):
    """Types of policies that can be created."""
    HEALTHCARE = "healthcare"
    TAX_REFORM = "tax_reform"
    SPENDING_REFORM = "spending_reform"
    COMBINED = "combined"
    CUSTOM = "custom"


@dataclass
class PolicyParameter:
    """Single adjustable parameter in a policy."""
    name: str
    description: str
    value: float
    min_value: float
    max_value: float
    unit: str = ""
    category: str = "general"
    
    def validate(self) -> bool:
        """Validate parameter is within bounds."""
        return self.min_value <= self.value <= self.max_value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CustomPolicy:
    """User-defined fiscal policy with adjustable parameters."""
    
    # Metadata
    name: str
    description: str
    policy_type: PolicyType
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    author: str = "User"
    category: str = "General"  # Category for organization (e.g., "My Policies", "Healthcare Ideas")
    order: int = 0  # For ordering within categories
    
    # Parameters organized by category
    parameters: Dict[str, PolicyParameter] = field(default_factory=dict)
    
    # Projection results (optional)
    projection_results: Optional[pd.DataFrame] = None
    fiscal_impact: Optional[Dict[str, float]] = None
    structured_mechanics: Optional[Dict[str, Any]] = None  # Serialized PolicyMechanics for context-aware sims
    
    def add_parameter(
        self,
        name: str,
        description: str,
        value: float,
        min_val: float,
        max_val: float,
        unit: str = "",
        category: str = "general",
    ) -> None:
        """Add a new parameter to the policy."""
        param = PolicyParameter(
            name=name,
            description=description,
            value=value,
            min_value=min_val,
            max_value=max_val,
            unit=unit,
            category=category,
        )
        self.parameters[name] = param
    
    def update_parameter(self, name: str, value: float) -> bool:
        """Update parameter value if it exists and is valid."""
        if name not in self.parameters:
            return False
        
        param = self.parameters[name]
        if not (param.min_value <= value <= param.max_value):
            return False
        
        param.value = value
        return True
    
    def get_parameter_value(self, name: str) -> Optional[float]:
        """Get parameter value by name."""
        if name in self.parameters:
            return self.parameters[name].value
        return None
    
    def get_parameters_by_category(self, category: str) -> Dict[str, PolicyParameter]:
        """Get all parameters in a specific category."""
        return {
            name: param
            for name, param in self.parameters.items()
            if param.category == category
        }
    
    def validate_all(self) -> Tuple[bool, List[str]]:
        """Validate all parameters."""
        errors = []
        for name, param in self.parameters.items():
            if not param.validate():
                errors.append(
                    f"Parameter '{name}' value {param.value} out of range "
                    f"[{param.min_value}, {param.max_value}]"
                )
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert policy to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type.value,
            "created_date": self.created_date,
            "author": self.author,
            "category": self.category,
            "order": self.order,
            "parameters": {
                name: param.to_dict() for name, param in self.parameters.items()
            },
            "structured_mechanics": self.structured_mechanics,
        }
    
    def to_json(self) -> str:
        """Convert policy to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "CustomPolicy":
        """Create policy from dictionary."""
        policy = CustomPolicy(
            name=data["name"],
            description=data["description"],
            policy_type=PolicyType(data["policy_type"]),
            created_date=data.get("created_date", datetime.now().isoformat()),
            author=data.get("author", "User"),
            category=data.get("category", "General"),
            order=data.get("order", 0),
        )
        
        for param_name, param_data in data.get("parameters", {}).items():
            param = PolicyParameter(**param_data)
            policy.parameters[param_name] = param

        # Optional structured mechanics for context-aware simulations
        policy.structured_mechanics = data.get("structured_mechanics")
        
        return policy
    
    @staticmethod
    def from_json(json_str: str) -> "CustomPolicy":
        """Create policy from JSON string."""
        data = json.loads(json_str)
        return CustomPolicy.from_dict(data)
    
    def to_healthcare_policy(self):
        """Convert CustomPolicy to HealthcarePolicyModel for simulation.
        
        IMPORTANT: Revenue definitions must include ONLY government-dedicated healthcare revenues.
        Patient out-of-pocket costs are NOT government revenue - they represent patient burden.
        
        The simulation calculates:
        - Healthcare spending from spending_target_gdp
        - Available revenue from payroll_tax + general_revenue_pct + other_funding_sources
        - Surplus/Deficit as: revenue - spending (as % of GDP)
        
        Example:
            - Payroll tax: 4% (employer+employee health insurance taxes only)
            - General revenue: 3.5% (Medicare, Medicaid, VA funding only)  
            - Other funding: 0.5% (savings from negotiated pricing, efficiency gains)
            - Total revenue: 8% of GDP available for healthcare
            - If spending target is 9%, then deficit is -1% of GDP (unrealistic without subsidies)
        """
        from core.healthcare import HealthcarePolicyModel, HealthcareCategory, PolicyType as HealthcarePolicyType, TransitionTimeline
        from core.policy_mechanics_extractor import PolicyMechanicsExtractor
        
        # Create base healthcare policy with custom parameters
        # NOTE: All percentages represent % of GDP
        policy = HealthcarePolicyModel(
            policy_type=HealthcarePolicyType.CURRENT_US,  # Use as custom baseline
            policy_name=self.name,
            policy_version="custom",
            created_date=self.created_date,
            description=self.description,
            
            # Default values (can be overridden by parameters)
            universal_coverage=False,
            zero_out_of_pocket=False,
            opt_out_allowed=False,
            emergency_coverage=True,
            coverage_percentage=0.92,
            
            # Revenue sources (% of GDP)
            # CRITICAL: Only include government-dedicated healthcare revenues
            # Do NOT include patient out-of-pocket costs or private insurance premiums
            total_payroll_tax=self.get_parameter_value('payroll_tax') or 0.04,
            employer_contribution_pct=self.get_parameter_value('employer_contribution') or 0.10,
            employee_contribution_pct=self.get_parameter_value('employee_contribution') or 0.08,
            general_revenue_pct=self.get_parameter_value('general_revenue') or 0.035,
            
            # Spending target (% of GDP)
            healthcare_spending_target_gdp=self.get_parameter_value('healthcare_spending_target') or 0.18,
            admin_overhead_pct=self.get_parameter_value('admin_overhead') or 0.16,
        )
        
        # Set other funding sources from parameters
        # CRITICAL: Only include government-dedicated sources (savings, efficiency gains, etc.)
        # Do NOT include patient out-of-pocket or private insurance - those are not government revenue
        other_funding = {}
        
        # Only include legitimate government healthcare revenue sources
        healthcare_specific_sources = {
            'drug_pricing_negotiation',
            'administrative_savings', 
            'efficiency_gains',
            'fraud_prevention',
            'provider_consolidation_savings'
        }
        
        for source in healthcare_specific_sources:
            if self.get_parameter_value(source):
                other_funding[source] = self.get_parameter_value(source)
        
        if other_funding:
            policy.other_funding_sources = other_funding

        # Attach structured mechanics when available so the simulator can use
        # the context-aware path instead of legacy hard-coded assumptions.
        mechanics_dict = getattr(self, "structured_mechanics", None)
        if mechanics_dict:
            try:
                policy.mechanics = PolicyMechanicsExtractor.mechanics_from_dict(
                    mechanics_dict,
                    default_name=self.name,
                    default_type=self.policy_type.value
                )

                # Map key targets/flags onto the policy for legacy consumers
                if policy.mechanics.target_spending_pct_gdp:
                    policy.healthcare_spending_target_gdp = float(policy.mechanics.target_spending_pct_gdp) / 100.0
                policy.zero_out_of_pocket = bool(policy.mechanics.zero_out_of_pocket)
                policy.universal_coverage = bool(policy.mechanics.universal_coverage)

                # Build a transition timeline from milestones if provided
                if policy.mechanics.timeline_milestones:
                    milestones = {m.year: m.description or "" for m in policy.mechanics.timeline_milestones}
                    start_year = min(m.year for m in policy.mechanics.timeline_milestones)
                    target_year = policy.mechanics.target_spending_year or max(m.year for m in policy.mechanics.timeline_milestones)
                    policy.transition_timeline = TransitionTimeline(
                        start_year=start_year,
                        full_implementation_year=target_year,
                        sunset_year=None,
                        key_milestones=milestones,
                        transition_funding_source="Extracted from policy text"
                    )
            except Exception:
                # If anything goes wrong we simply fall back to legacy values
                policy.mechanics = None
        
        # Set up healthcare categories with default values
        policy.categories = {
            "hospital": HealthcareCategory(
                category_name="Hospital Inpatient/Outpatient",
                current_spending_pct=self.get_parameter_value('hospital_spending_pct') or 0.31,
                baseline_cost=250.0,
                reduction_target=self.get_parameter_value('hospital_reduction') or 0.0,
                description="Hospital services"
            ),
            "physician": HealthcareCategory(
                category_name="Physician Services",
                current_spending_pct=self.get_parameter_value('physician_spending_pct') or 0.20,
                baseline_cost=160.0,
                reduction_target=self.get_parameter_value('physician_reduction') or 0.0,
                description="Physician care"
            ),
            "pharmacy": HealthcareCategory(
                category_name="Pharmaceuticals",
                current_spending_pct=self.get_parameter_value('pharmacy_spending_pct') or 0.10,
                baseline_cost=80.0,
                reduction_target=self.get_parameter_value('pharmacy_reduction') or 0.0,
                description="Drugs"
            ),
            "administrative": HealthcareCategory(
                category_name="Administrative",
                current_spending_pct=self.get_parameter_value('admin_spending_pct') or 0.16,
                baseline_cost=128.0,
                reduction_target=self.get_parameter_value('admin_reduction') or 0.0,
                description="Insurance overhead, billing"
            ),
            "other": HealthcareCategory(
                category_name="Other",
                current_spending_pct=self.get_parameter_value('other_spending_pct') or 0.23,
                baseline_cost=184.0,
                reduction_target=0.0,
                description="Other services"
            ),
        }
        
        return policy


class PolicyTemplate:
    """Template for creating policies with pre-defined parameters."""
    
    HEALTHCARE_TEMPLATE = {
        "name": "Healthcare Reform Template",
        "description": "Template for healthcare policy reform",
        "type": PolicyType.HEALTHCARE,
        "parameters": {
            "coverage_target_pct": {
                "description": "Target population with healthcare coverage (%)",
                "value": 95.0,
                "min": 90.0,
                "max": 100.0,
                "unit": "%",
                "category": "coverage",
            },
            "out_of_pocket_max": {
                "description": "Maximum out-of-pocket cost per person ($/year)",
                "value": 8_500.0,
                "min": 0.0,
                "max": 20_000.0,
                "unit": "$",
                "category": "coverage",
            },
            "health_spending_target_gdp": {
                "description": "Target health spending as % of GDP",
                "value": 7.0,
                "min": 5.0,
                "max": 12.0,
                "unit": "%",
                "category": "spending",
            },
            "pharma_cost_reduction_pct": {
                "description": "Pharmaceutical cost reduction (%)",
                "value": 15.0,
                "min": 0.0,
                "max": 50.0,
                "unit": "%",
                "category": "costs",
            },
            "provider_payment_reform": {
                "description": "Provider payment adjustment (%)",
                "value": 0.0,
                "min": -30.0,
                "max": 20.0,
                "unit": "%",
                "category": "payments",
            },
            "innovation_investment_pct": {
                "description": "Annual investment in biomedical innovation (% of budget)",
                "value": 3.0,
                "min": 0.0,
                "max": 10.0,
                "unit": "%",
                "category": "innovation",
            },
        },
    }
    
    TAX_REFORM_TEMPLATE = {
        "name": "Tax Reform Template",
        "description": "Template for federal tax reform",
        "type": PolicyType.TAX_REFORM,
        "parameters": {
            "income_tax_rate_change": {
                "description": "Individual income tax rate change (percentage points)",
                "value": 0.0,
                "min": -10.0,
                "max": 10.0,
                "unit": "pp",
                "category": "income",
            },
            "corporate_tax_rate": {
                "description": "Corporate income tax rate (%)",
                "value": 21.0,
                "min": 15.0,
                "max": 35.0,
                "unit": "%",
                "category": "corporate",
            },
            "capital_gains_rate": {
                "description": "Long-term capital gains tax rate (%)",
                "value": 20.0,
                "min": 0.0,
                "max": 37.0,
                "unit": "%",
                "category": "investment",
            },
            "payroll_tax_increase": {
                "description": "Payroll tax rate increase (percentage points)",
                "value": 0.0,
                "min": -2.0,
                "max": 5.0,
                "unit": "pp",
                "category": "payroll",
            },
            "estate_tax_exemption": {
                "description": "Estate tax exemption ($ millions)",
                "value": 13.61,
                "min": 0.0,
                "max": 50.0,
                "unit": "$M",
                "category": "estate",
            },
            "carbon_tax_per_ton": {
                "description": "Carbon tax rate ($/ton CO2)",
                "value": 0.0,
                "min": 0.0,
                "max": 200.0,
                "unit": "$/ton",
                "category": "energy",
            },
        },
    }
    
    SPENDING_REFORM_TEMPLATE = {
        "name": "Spending Reform Template",
        "description": "Template for federal spending reform",
        "type": PolicyType.SPENDING_REFORM,
        "parameters": {
            "defense_reduction_pct": {
                "description": "Defense spending reduction (%)",
                "value": 0.0,
                "min": -10.0,
                "max": 20.0,
                "unit": "%",
                "category": "defense",
            },
            "nondefense_discretionary_reduction": {
                "description": "Non-defense discretionary reduction (%)",
                "value": 0.0,
                "min": -15.0,
                "max": 10.0,
                "unit": "%",
                "category": "discretionary",
            },
            "ss_benefit_reduction_pct": {
                "description": "Social Security benefit reduction for high earners (%)",
                "value": 0.0,
                "min": 0.0,
                "max": 50.0,
                "unit": "%",
                "category": "mandatory",
            },
            "medicare_payment_reduction": {
                "description": "Medicare provider payment reduction (%)",
                "value": 0.0,
                "min": -20.0,
                "max": 10.0,
                "unit": "%",
                "category": "healthcare",
            },
            "improper_payments_reduction": {
                "description": "Reduce improper payments (waste/fraud) by $B/year",
                "value": 0.0,
                "min": 0.0,
                "max": 100.0,
                "unit": "$B",
                "category": "efficiency",
            },
        },
    }
    
    @staticmethod
    def create_from_template(template_name: str, policy_name: str) -> CustomPolicy:
        """Create a new policy from a template."""
        templates = {
            "healthcare": PolicyTemplate.HEALTHCARE_TEMPLATE,
            "tax_reform": PolicyTemplate.TAX_REFORM_TEMPLATE,
            "spending_reform": PolicyTemplate.SPENDING_REFORM_TEMPLATE,
        }
        
        if template_name not in templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = templates[template_name]
        policy = CustomPolicy(
            name=policy_name,
            description=str(template["description"]),
            policy_type=template["type"],  # type: ignore[arg-type]
        )
        
        params = template["parameters"]
        if isinstance(params, dict):
            for param_name, param_config in params.items():
                policy.add_parameter(
                    name=param_name,
                    description=param_config["description"],
                    value=param_config["value"],
                    min_val=param_config["min"],
                    max_val=param_config["max"],
                    unit=param_config["unit"],
                    category=param_config["category"],
                )
        
        return policy


class PolicyLibrary:
    """Manages collection of policies with categorization support."""
    
    def __init__(self, library_path: str = "policies/custom_policies"):
        """Initialize policy library."""
        self.library_path = Path(library_path)
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.policies: Dict[str, CustomPolicy] = {}
        self.metadata_file = self.library_path / "_library_metadata.json"
        # Default categories with "Uploaded Policies" first for visibility
        self.metadata: Dict[str, Any] = {"categories": ["Uploaded Policies", "General", "Custom"]}
        self._load_metadata()
        self._load_all_policies()
    
    def _load_metadata(self) -> None:
        """Load library metadata (categories, etc)."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {e}")
    
    def _save_metadata(self) -> None:
        """Save library metadata to disk."""
        try:
            with open(self.metadata_file, "w") as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Error saving metadata: {e}")
    
    def _load_all_policies(self) -> None:
        """Load all policies from disk."""
        for policy_file in self.library_path.glob("*.json"):
            if policy_file.name == "_library_metadata.json":
                continue
            try:
                with open(policy_file, "r") as f:
                    data = json.load(f)
                    policy = CustomPolicy.from_dict(data)
                    self.policies[policy.name] = policy
            except Exception as e:
                print(f"Error loading policy {policy_file}: {e}")
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        categories = self.metadata.get("categories", ["General"])
        return list(categories) if categories else ["General"]
    
    def add_category(self, category_name: str) -> bool:
        """Add a new category."""
        if category_name in self.metadata.get("categories", []):
            return False
        self.metadata.setdefault("categories", []).append(category_name)
        self._save_metadata()
        return True
    
    def delete_category(self, category_name: str) -> bool:
        """Delete a category and move policies to General."""
        if category_name not in self.metadata.get("categories", []):
            return False
        
        # Reassign policies in this category to General
        for policy in self.policies.values():
            if policy.category == category_name:
                policy.category = "General"
                self.save_policy(policy)
        
        self.metadata["categories"].remove(category_name)
        self._save_metadata()
        return True
    
    def add_policy(self, policy: CustomPolicy) -> bool:
        """Add policy to library."""
        if policy.name in self.policies:
            return False  # Policy with same name exists
        
        # Ensure category exists
        if policy.category not in self.metadata.get("categories", []):
            policy.category = "General"
        
        self.policies[policy.name] = policy
        self.save_policy(policy)
        return True
    
    def save_policy(self, policy: CustomPolicy) -> bool:
        """Save policy to disk."""
        try:
            file_path = self.library_path / f"{policy.name}.json"
            with open(file_path, "w") as f:
                f.write(policy.to_json())
            return True
        except Exception as e:
            print(f"Error saving policy: {e}")
            return False
    
    def rename_policy(self, old_name: str, new_name: str) -> bool:
        """Rename a policy."""
        if old_name not in self.policies or new_name in self.policies:
            return False
        
        policy = self.policies[old_name]
        policy.name = new_name
        
        # Delete old file, save new file
        try:
            old_file = self.library_path / f"{old_name}.json"
            if old_file.exists():
                old_file.unlink()
            
            self.save_policy(policy)
            del self.policies[old_name]
            self.policies[new_name] = policy
            return True
        except Exception as e:
            print(f"Error renaming policy: {e}")
            return False
    
    def clone_policy(self, source_name: str, new_name: str) -> bool:
        """Clone an existing policy with a new name."""
        if source_name not in self.policies or new_name in self.policies:
            return False
        
        source = self.policies[source_name]
        cloned = CustomPolicy(
            name=new_name,
            description=f"Clone of: {source.description}",
            policy_type=source.policy_type,
            author=source.author,
            category=source.category,
            created_date=datetime.now().isoformat(),
        )
        
        # Copy all parameters
        for param_name, param in source.parameters.items():
            cloned.parameters[param_name] = PolicyParameter(
                name=param.name,
                description=param.description,
                value=param.value,
                min_value=param.min_value,
                max_value=param.max_value,
                unit=param.unit,
                category=param.category,
            )
        
        self.policies[new_name] = cloned
        self.save_policy(cloned)
        return True
    
    def get_policy(self, name: str) -> Optional[CustomPolicy]:
        """Get policy by name."""
        return self.policies.get(name)
    
    def list_policies(self) -> List[str]:
        """List all policy names sorted."""
        return sorted(self.policies.keys())
    
    def list_policies_by_category(self, category: str) -> List[str]:
        """List policies in a specific category."""
        return sorted([
            name for name, policy in self.policies.items()
            if policy.category == category
        ], key=lambda name: self.policies[name].order)
    
    def list_policies_by_type(self, policy_type: PolicyType) -> List[str]:
        """List policies of a specific type."""
        return sorted([
            name for name, policy in self.policies.items()
            if policy.policy_type == policy_type
        ])
    
    def reorder_policies(self, category: str, ordered_names: List[str]) -> bool:
        """Reorder policies within a category."""
        try:
            for i, name in enumerate(ordered_names):
                if name in self.policies:
                    self.policies[name].order = i
                    self.save_policy(self.policies[name])
            return True
        except Exception as e:
            print(f"Error reordering policies: {e}")
            return False
    
    def delete_policy(self, name: str) -> bool:
        """Delete policy from library."""
        if name not in self.policies:
            return False
        
        try:
            file_path = self.library_path / f"{name}.json"
            file_path.unlink()
            del self.policies[name]
            return True
        except Exception as e:
            print(f"Error deleting policy: {e}")
            return False
    
    def export_policies_dataframe(self) -> pd.DataFrame:
        """Export all policies as DataFrame."""
        rows = []
        for name, policy in self.policies.items():
            rows.append({
                "Name": name,
                "Type": policy.policy_type.value,
                "Description": policy.description,
                "Created": policy.created_date,
                "Author": policy.author,
                "Parameters": len(policy.parameters),
            })
        return pd.DataFrame(rows)


@dataclass
class ScenarioBundle:
    """Named grouping of policies for scenario comparisons."""
    name: str
    policy_names: List[str]
    description: str = ""
    author: str = "User"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScenarioBundle":
        return ScenarioBundle(
            name=data["name"],
            policy_names=data.get("policy_names", []),
            description=data.get("description", ""),
            author=data.get("author", "User"),
            created_date=data.get("created_date", datetime.now().isoformat()),
        )


class ScenarioBundleLibrary:
    """Manage saved scenario bundles on disk."""

    def __init__(self, bundle_path: str = "policies/scenario_bundles.json"):
        self.bundle_path = Path(bundle_path)
        self.bundle_path.parent.mkdir(parents=True, exist_ok=True)
        self.bundles: Dict[str, ScenarioBundle] = {}
        self._load()

    def _load(self) -> None:
        if self.bundle_path.exists():
            try:
                with open(self.bundle_path, "r") as f:
                    raw = json.load(f)
                for item in raw:
                    bundle = ScenarioBundle.from_dict(item)
                    self.bundles[bundle.name] = bundle
            except Exception as exc:
                print(f"Error loading scenario bundles: {exc}")

    def _persist(self) -> None:
        try:
            serialized = [bundle.to_dict() for bundle in self.bundles.values()]
            with open(self.bundle_path, "w") as f:
                json.dump(serialized, f, indent=2)
        except Exception as exc:
            print(f"Error saving scenario bundles: {exc}")

    def list_bundles(self) -> List[str]:
        return sorted(self.bundles.keys())

    def get_bundle(self, name: str) -> Optional[ScenarioBundle]:
        return self.bundles.get(name)

    def save_bundle(self, bundle: ScenarioBundle) -> None:
        self.bundles[bundle.name] = bundle
        self._persist()

    def delete_bundle(self, name: str) -> bool:
        if name not in self.bundles:
            return False
        del self.bundles[name]
        self._persist()
        return True


def build_policy_comparison_table(policies: List[CustomPolicy]) -> pd.DataFrame:
    """Create a comparison table of parameter values across policies."""
    if not policies:
        return pd.DataFrame()

    all_param_names: set[str] = set()
    for policy in policies:
        all_param_names.update(policy.parameters.keys())

    baseline_name = policies[0].name
    rows: List[Dict[str, Any]] = []

    for param_name in sorted(all_param_names):
        row: Dict[str, Any] = {"Parameter": param_name}
        baseline_value = None

        for idx, policy in enumerate(policies):
            param = policy.parameters.get(param_name)
            value = param.value if param is not None else None
            row[policy.name] = value
            if idx == 0:
                baseline_value = value
            elif baseline_value is not None and value is not None:
                row[f"{policy.name} Δ vs {baseline_name}"] = value - baseline_value
            else:
                row[f"{policy.name} Δ vs {baseline_name}"] = None

        rows.append(row)

    return pd.DataFrame(rows)


def build_scenario_bundle_zip(policies: List[CustomPolicy], comparison_df: pd.DataFrame) -> bytes:
    """Create an in-memory zip containing policies and comparison artifacts."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Policies JSON
        policies_payload = {policy.name: policy.to_dict() for policy in policies}
        zf.writestr("policies.json", json.dumps(policies_payload, indent=2))

        # Comparison table
        if not comparison_df.empty:
            zf.writestr("comparison.csv", comparison_df.to_csv(index=False))
            zf.writestr("comparison.json", comparison_df.to_json(orient="records", indent=2))

        # Metadata
        meta = {
            "generated_at": datetime.now().isoformat(),
            "policy_count": len(policies),
            "comparison_rows": int(len(comparison_df)) if comparison_df is not None else 0,
            "policy_names": [p.name for p in policies],
        }
        zf.writestr("metadata.json", json.dumps(meta, indent=2))

    buffer.seek(0)
    return buffer.read()


__all__ = [
    "PolicyType",
    "PolicyParameter",
    "CustomPolicy",
    "PolicyTemplate",
    "PolicyLibrary",
    "ScenarioBundle",
    "ScenarioBundleLibrary",
    "build_policy_comparison_table",
    "build_scenario_bundle_zip",
]
