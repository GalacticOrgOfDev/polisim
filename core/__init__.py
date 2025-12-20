"""Core economic and simulation modules.

This module provides the main API for polisim:
- Healthcare policy models and comparisons (Phase 1)
- Social Security projections (Phase 2)
- Federal revenue modeling (Phase 2)
- Economic simulation and Monte Carlo engine
- Metrics and analysis tools
- Scenario management

Usage:
    from core import get_policy_by_type, PolicyType
    from core.economic_engine import MonteCarloEngine, PolicyScenario
    from core.social_security import SocialSecurityModel
    from core.revenue_modeling import FederalRevenueModel
    
    # Load policy
    policy = get_policy_by_type(PolicyType.USGHA)
    
    # Run simulation
    engine = MonteCarloEngine()
    result = engine.run_simulation(scenario, iterations=100000)
"""

import logging

from core.economics import calculate_revenues_and_outs
from core.simulation import simulate_years
from core.simulation import simulate_healthcare_years
from core.metrics import compute_policy_metrics, calculate_cbo_summary

from core.healthcare import (
    HealthcarePolicyModel,
    HealthcarePolicyFactory,
    PolicyType,
    get_policy_by_type,
    list_available_policies,
)

from core.economic_engine import (
    MonteCarloEngine,
    EconomicModel,
    PolicyScenario,
    SimulationResult,
    EconomicParameters,
    RevenueLine,
    SpendingCategory,
    SensitivityAnalyzer,
    ScenarioComparator,
)

# Phase 2: Social Security & Revenue modules
from core.social_security import (
    SocialSecurityModel,
    DemographicAssumptions,
    BenefitFormula,
    TrustFundAssumptions,
    SocialSecurityReforms,
)

from core.revenue_modeling import (
    FederalRevenueModel,
    IndividualIncomeTaxAssumptions,
    PayrollTaxAssumptions,
    CorporateIncomeTaxAssumptions,
    TaxReforms,
)

# Phase 3.1: Medicare & Medicaid modules
from core.medicare_medicaid import (
    MedicareModel,
    MedicaidModel,
    MedicareAssumptions,
    MedicaidAssumptions,
)

# Phase 3.2: Discretionary & Interest & Combined modules
from core.discretionary_spending import (
    DiscretionarySpendingModel,
    DiscretionaryAssumptions,
)

from core.interest_spending import (
    InterestOnDebtModel,
    DebtAssumptions,
)

from core.combined_outlook import (
    CombinedFiscalOutlookModel,
)

# Phase 4: Real Data & Policy Builder modules
from core.data_loader import (
    RealDataLoader,
    load_real_data,
    CBOHistoricalData,
    SSAHistoricalData,
    MedicareHistoricalData,
    MedicaidHistoricalData,
    PopulationProjections,
)

from core.policy_builder import (
    CustomPolicy,
    PolicyParameter,
    PolicyTemplate,
    PolicyLibrary,
    PolicyType as BuilderPolicyType,
)

from core.pdf_policy_parser import (
    PolicyPDFProcessor,
    PolicyKeywordMatcher,
    PolicyExtraction,
    process_policy_pdf,
)

# Phase 4b: Policy Enhancements
from core.policy_enhancements import (
    PolicyRecommendationEngine,
    PolicyImpactCalculator,
    InteractiveScenarioExplorer,
    PolicyComparator,
    PolicyScore,
    FiscalGoal,
)

# Phase 4c: Monte Carlo Scenarios
from core.monte_carlo_scenarios import (
    MonteCarloPolicySimulator,
    PolicySensitivityAnalyzer,
    StressTestAnalyzer,
    MonteCarloResult,
)

# Phase 4b: Report Generation
from core.report_generator import (
    PDFReportGenerator,
    ExcelReportGenerator,
    ComprehensiveReportBuilder,
    ReportSection,
    ReportMetadata,
)

# Configure module-level logging
_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())

__all__ = [
    # Economics
    'calculate_revenues_and_outs',
    'simulate_years',
    'simulate_healthcare_years',
    'compute_policy_metrics',
    'calculate_cbo_summary',
    
    # Healthcare policies
    'HealthcarePolicyModel',
    'HealthcarePolicyFactory',
    'PolicyType',
    'get_policy_by_type',
    'list_available_policies',
    
    # Economic engine
    'MonteCarloEngine',
    'EconomicModel',
    'PolicyScenario',
    'SimulationResult',
    'EconomicParameters',
    'RevenueLine',
    'SpendingCategory',
    'SensitivityAnalyzer',
    'ScenarioComparator',
    
    # Phase 2: Social Security & Revenue
    'SocialSecurityModel',
    'DemographicAssumptions',
    'BenefitFormula',
    'TrustFundAssumptions',
    'SocialSecurityReforms',
    'FederalRevenueModel',
    'IndividualIncomeTaxAssumptions',
    'PayrollTaxAssumptions',
    'CorporateIncomeTaxAssumptions',
    'TaxReforms',
    
    # Phase 3.1: Medicare & Medicaid
    'MedicareModel',
    'MedicaidModel',
    'MedicareAssumptions',
    'MedicaidAssumptions',
    
    # Phase 3.2: Discretionary & Interest & Combined
    'DiscretionarySpendingModel',
    'DiscretionaryAssumptions',
    'InterestOnDebtModel',
    'DebtAssumptions',
    'CombinedFiscalOutlookModel',
    
    # Phase 4: Real Data & Policy Builder
    'RealDataLoader',
    'load_real_data',
    'CBOHistoricalData',
    'SSAHistoricalData',
    'MedicareHistoricalData',
    'MedicaidHistoricalData',
    'PopulationProjections',
    'CustomPolicy',
    'PolicyParameter',
    'PolicyTemplate',
    'PolicyLibrary',
    'PolicyPDFProcessor',
    'PolicyKeywordMatcher',
    'PolicyExtraction',
    'process_policy_pdf',
    
    # Phase 4b: Policy Enhancements
    'PolicyRecommendationEngine',
    'PolicyImpactCalculator',
    'InteractiveScenarioExplorer',
    'PolicyComparator',
    'PolicyScore',
    'FiscalGoal',
    
    # Phase 4c: Monte Carlo Scenarios
    'MonteCarloPolicySimulator',
    'PolicySensitivityAnalyzer',
    'StressTestAnalyzer',
    'MonteCarloResult',
    
    # Phase 4b: Report Generation
    'PDFReportGenerator',
    'ExcelReportGenerator',
    'ComprehensiveReportBuilder',
    'ReportSection',
    'ReportMetadata',
]

