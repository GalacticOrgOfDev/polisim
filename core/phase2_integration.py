"""
Phase 2 Integration Module

Integrates tax reform and Social Security enhancements into the main simulation engine.
Provides unified interface for running comprehensive fiscal policy simulations.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import numpy as np
import logging

from core.tax_reform import (
    WealthTaxModel,
    ConsumptionTaxModel,
    CarbonTaxModel,
    FinancialTransactionTaxModel,
    ComprehensiveTaxReformAnalyzer,
    WealthTaxParameters,
    ConsumptionTaxParameters,
    CarbonTaxParameters,
    FinancialTransactionTaxParameters,
)
from core.social_security import (
    SocialSecurityModel,
    SocialSecurityReforms,
    DemographicAssumptions,
    BenefitFormula,
    TrustFundAssumptions,
)
from core.revenue_modeling import TaxReforms

logger = logging.getLogger(__name__)


@dataclass
class Phase2PolicyPackage:
    """
    Comprehensive policy package combining tax reforms and Social Security reforms.
    """
    
    # Tax reform configuration
    wealth_tax_enabled: bool = False
    wealth_tax_params: Optional[WealthTaxParameters] = None
    
    consumption_tax_enabled: bool = False
    consumption_tax_params: Optional[ConsumptionTaxParameters] = None
    
    carbon_tax_enabled: bool = False
    carbon_tax_params: Optional[CarbonTaxParameters] = None
    
    ftt_enabled: bool = False
    ftt_params: Optional[FinancialTransactionTaxParameters] = None
    
    # Social Security reform configuration
    ss_payroll_tax_increase: Optional[float] = None
    ss_remove_wage_cap: bool = False
    ss_raise_fra: Optional[int] = None
    ss_means_testing_enabled: bool = False
    ss_means_testing_threshold_1: float = 85_000
    ss_means_testing_threshold_2: float = 150_000
    ss_longevity_indexing_enabled: bool = False
    ss_cola_formula: str = "cpi_w"  # cpi_w, cpi_e, chained_cpi
    ss_progressive_tax_enabled: bool = False
    ss_progressive_tax_threshold: float = 250_000
    ss_progressive_additional_rate: float = 0.05
    
    # Traditional tax reforms
    income_tax_increase: Optional[float] = None
    corporate_tax_increase: Optional[float] = None
    
    def __post_init__(self):
        """Initialize default tax parameters if enabled but not specified."""
        if self.wealth_tax_enabled and self.wealth_tax_params is None:
            self.wealth_tax_params = WealthTaxParameters.progressive_wealth_tax()
        
        if self.consumption_tax_enabled and self.consumption_tax_params is None:
            self.consumption_tax_params = ConsumptionTaxParameters.progressive_consumption_tax()
        
        if self.carbon_tax_enabled and self.carbon_tax_params is None:
            self.carbon_tax_params = CarbonTaxParameters.moderate_carbon_tax()
        
        if self.ftt_enabled and self.ftt_params is None:
            self.ftt_params = FinancialTransactionTaxParameters.progressive_ftt()


class Phase2SimulationEngine:
    """
    Enhanced simulation engine with Phase 2 tax reform and Social Security integration.
    """
    
    def __init__(
        self,
        base_gdp: float,
        population: float,
        start_year: int = 2025,
        seed: Optional[int] = None,
    ):
        """
        Initialize Phase 2 simulation engine.
        
        Args:
            base_gdp: Initial GDP in billions
            population: Population in millions
            start_year: Starting year for projections
            seed: Random seed for reproducibility
        """
        self.base_gdp = base_gdp
        self.population = population
        self.start_year = start_year
        self.seed = seed
        
        # Initialize models
        self.ss_model = SocialSecurityModel(start_year=start_year, seed=seed)
        self.tax_reform_analyzer = ComprehensiveTaxReformAnalyzer()
        self.tax_reforms = TaxReforms()
        
        logger.info(
            f"Phase2SimulationEngine initialized: GDP=${base_gdp:.1f}B, "
            f"Pop={population:.1f}M, Year={start_year}"
        )
    
    def simulate_comprehensive_reform(
        self,
        policy_package: Phase2PolicyPackage,
        years: int = 30,
        gdp_growth_rate: float = 0.025,
        iterations: int = 1000,
    ) -> Dict[str, pd.DataFrame]:
        """
        Run comprehensive simulation with tax reforms and Social Security reforms.
        
        Args:
            policy_package: Policy configuration
            years: Number of years to project
            gdp_growth_rate: Annual GDP growth rate
            iterations: Monte Carlo iterations for Social Security
            
        Returns:
            Dictionary with simulation results:
                - 'overview': High-level fiscal indicators
                - 'tax_reforms': Tax reform revenue projections
                - 'social_security': Social Security trust fund projections
                - 'combined': Combined fiscal impact
        """
        logger.info(f"Running comprehensive Phase 2 simulation: {years} years, {iterations} iterations")
        
        # 1. Run tax reform analysis
        tax_results = self._simulate_tax_reforms(policy_package, years, gdp_growth_rate)
        
        # 2. Run Social Security reforms
        ss_results = self._simulate_social_security_reforms(
            policy_package, years, iterations
        )
        
        # 3. Combine results into unified fiscal projection
        combined_results = self._combine_fiscal_projections(
            tax_results, ss_results, years, gdp_growth_rate
        )
        
        return {
            'overview': combined_results,
            'tax_reforms': tax_results,
            'social_security': ss_results,
            'policy_package': policy_package,
        }
    
    def _simulate_tax_reforms(
        self,
        policy_package: Phase2PolicyPackage,
        years: int,
        gdp_growth_rate: float,
    ) -> pd.DataFrame:
        """
        Simulate tax reform revenue impacts.
        
        Returns DataFrame with annual revenue by tax type.
        """
        # Build reform dictionary for ComprehensiveTaxReformAnalyzer
        reforms = {}
        
        if policy_package.wealth_tax_enabled:
            reforms['wealth_tax'] = asdict(policy_package.wealth_tax_params)
        
        if policy_package.consumption_tax_enabled:
            reforms['consumption_tax'] = asdict(policy_package.consumption_tax_params)
        
        if policy_package.carbon_tax_enabled:
            reforms['carbon_tax'] = asdict(policy_package.carbon_tax_params)
        
        if policy_package.ftt_enabled:
            reforms['ftt'] = asdict(policy_package.ftt_params)
        
        # Run analysis
        if reforms:
            results = self.tax_reform_analyzer.analyze_reform_package(
                reforms, years=years, gdp_growth=np.full(years, gdp_growth_rate)
            )
            return results['total_combined']
        else:
            # No tax reforms, return zero revenue
            return pd.DataFrame({
                'year': range(self.start_year, self.start_year + years),
                'total_revenue': [0.0] * years,
            })
    
    def _simulate_social_security_reforms(
        self,
        policy_package: Phase2PolicyPackage,
        years: int,
        iterations: int,
    ) -> pd.DataFrame:
        """
        Simulate Social Security reform impacts.
        
        Returns DataFrame with trust fund projections.
        """
        # Apply reforms to model
        if policy_package.ss_payroll_tax_increase:
            self.ss_model.trust_fund.payroll_tax_rate = policy_package.ss_payroll_tax_increase
        
        if policy_package.ss_remove_wage_cap:
            self.ss_model.trust_fund.payroll_tax_cap = None
        
        if policy_package.ss_raise_fra:
            self.ss_model.benefit_formula.full_retirement_age = policy_package.ss_raise_fra
        
        if policy_package.ss_means_testing_enabled:
            self.ss_model.benefit_formula.means_test_threshold_1 = (
                policy_package.ss_means_testing_threshold_1
            )
            self.ss_model.benefit_formula.means_test_threshold_2 = (
                policy_package.ss_means_testing_threshold_2
            )
        
        if policy_package.ss_longevity_indexing_enabled:
            self.ss_model.benefit_formula.longevity_indexing_enabled = True
        
        if policy_package.ss_cola_formula != "cpi_w":
            self.ss_model.benefit_formula.cola_formula = policy_package.ss_cola_formula
        
        if policy_package.ss_progressive_tax_enabled:
            # Apply progressive tax in revenue calculations
            pass  # Would need to modify revenue calculations
        
        # Run projections
        projections = self.ss_model.project_trust_funds(years=years, iterations=iterations)
        
        # Calculate summary statistics by year
        summary = (
            projections.groupby('year')
            .agg({
                'oasi_balance_billions': ['mean', 'std', 'min', 'max'],
                'di_balance_billions': ['mean', 'std', 'min', 'max'],
                'payroll_tax_income_billions': ['mean'],
                'benefit_payments_billions': ['mean'],
                'oasi_solvent': ['mean'],  # Proportion of iterations solvent
            })
            .reset_index()
        )
        
        return summary
    
    def _combine_fiscal_projections(
        self,
        tax_results: pd.DataFrame,
        ss_results: pd.DataFrame,
        years: int,
        gdp_growth_rate: float,
    ) -> pd.DataFrame:
        """
        Combine tax reform and Social Security results into unified projection.
        
        Returns DataFrame with comprehensive fiscal indicators.
        """
        rows = []
        
        for year_idx in range(years):
            year = self.start_year + year_idx
            current_gdp = self.base_gdp * ((1 + gdp_growth_rate) ** year_idx)
            
            # Get tax reform revenue for this year
            if 'year' in tax_results.columns:
                tax_row = tax_results[tax_results['year'] == year]
                if len(tax_row) > 0:
                    tax_revenue = tax_row['total_revenue'].iloc[0]
                else:
                    tax_revenue = 0.0
            else:
                tax_revenue = tax_results['total_revenue'].iloc[year_idx] if year_idx < len(tax_results) else 0.0
            
            # Get Social Security data for this year
            ss_row = ss_results[ss_results['year'] == year]
            if len(ss_row) > 0:
                ss_balance = ss_row[('oasi_balance_billions', 'mean')].iloc[0]
                ss_payroll_revenue = ss_row[('payroll_tax_income_billions', 'mean')].iloc[0]
                ss_benefit_payments = ss_row[('benefit_payments_billions', 'mean')].iloc[0]
                ss_solvency_prob = ss_row[('oasi_solvent', 'mean')].iloc[0]
            else:
                ss_balance = 0.0
                ss_payroll_revenue = 0.0
                ss_benefit_payments = 0.0
                ss_solvency_prob = 0.0
            
            # Calculate combined impact
            total_new_revenue = tax_revenue + ss_payroll_revenue
            total_spending = ss_benefit_payments
            net_fiscal_impact = total_new_revenue - total_spending
            
            rows.append({
                'year': year,
                'gdp': current_gdp,
                'tax_reform_revenue': tax_revenue,
                'ss_payroll_revenue': ss_payroll_revenue,
                'total_new_revenue': total_new_revenue,
                'ss_benefit_payments': ss_benefit_payments,
                'ss_trust_fund_balance': ss_balance,
                'ss_solvency_probability': ss_solvency_prob,
                'net_fiscal_impact': net_fiscal_impact,
                'new_revenue_pct_gdp': (total_new_revenue / current_gdp) * 100,
            })
        
        return pd.DataFrame(rows)
    
    def compare_scenarios(
        self,
        baseline_package: Optional[Phase2PolicyPackage] = None,
        reform_packages: Optional[List[Tuple[str, Phase2PolicyPackage]]] = None,
        years: int = 30,
        gdp_growth_rate: float = 0.025,
    ) -> pd.DataFrame:
        """
        Compare multiple policy scenarios side-by-side.
        
        Args:
            baseline_package: Baseline policy (current law)
            reform_packages: List of (name, package) tuples for reforms
            years: Number of years to project
            gdp_growth_rate: Annual GDP growth
            
        Returns:
            DataFrame with scenario comparison
        """
        scenarios = []
        
        # Run baseline
        if baseline_package is None:
            baseline_package = Phase2PolicyPackage()  # No reforms
        
        baseline_results = self.simulate_comprehensive_reform(
            baseline_package, years=years, gdp_growth_rate=gdp_growth_rate, iterations=500
        )
        scenarios.append(('Baseline', baseline_results['overview']))
        
        # Run reform scenarios
        if reform_packages:
            for name, package in reform_packages:
                reform_results = self.simulate_comprehensive_reform(
                    package, years=years, gdp_growth_rate=gdp_growth_rate, iterations=500
                )
                scenarios.append((name, reform_results['overview']))
        
        # Build comparison DataFrame
        comparison_rows = []
        for year_idx in range(years):
            year = self.start_year + year_idx
            row = {'year': year}
            
            for scenario_name, scenario_df in scenarios:
                year_data = scenario_df[scenario_df['year'] == year]
                if len(year_data) > 0:
                    row[f'{scenario_name}_revenue'] = year_data['total_new_revenue'].iloc[0]
                    row[f'{scenario_name}_ss_balance'] = year_data['ss_trust_fund_balance'].iloc[0]
                    row[f'{scenario_name}_net_impact'] = year_data['net_fiscal_impact'].iloc[0]
            
            comparison_rows.append(row)
        
        return pd.DataFrame(comparison_rows)


# Pre-defined reform packages
class Phase2ReformPackages:
    """Common Phase 2 reform packages for testing and comparison."""
    
    @staticmethod
    def comprehensive_progressive_reform() -> Phase2PolicyPackage:
        """Comprehensive progressive reform package."""
        return Phase2PolicyPackage(
            # Tax reforms
            wealth_tax_enabled=True,
            consumption_tax_enabled=True,
            carbon_tax_enabled=True,
            ftt_enabled=True,
            # Social Security reforms
            ss_remove_wage_cap=True,
            ss_means_testing_enabled=True,
            ss_longevity_indexing_enabled=True,
            ss_cola_formula="chained_cpi",
            ss_progressive_tax_enabled=True,
        )
    
    @staticmethod
    def moderate_reform() -> Phase2PolicyPackage:
        """Moderate reform package."""
        return Phase2PolicyPackage(
            # Consumption tax only
            consumption_tax_enabled=True,
            carbon_tax_enabled=True,
            # SS: Remove cap + raise FRA
            ss_remove_wage_cap=True,
            ss_raise_fra=69,
        )
    
    @staticmethod
    def revenue_focused_reform() -> Phase2PolicyPackage:
        """Revenue-focused reform (maximizes revenue)."""
        return Phase2PolicyPackage(
            wealth_tax_enabled=True,
            consumption_tax_enabled=True,
            carbon_tax_enabled=True,
            ftt_enabled=True,
            ss_payroll_tax_increase=0.144,  # Increase from 12.4% to 14.4%
            ss_remove_wage_cap=True,
        )
    
    @staticmethod
    def benefit_preservation_reform() -> Phase2PolicyPackage:
        """Preserve benefits while extending solvency."""
        return Phase2PolicyPackage(
            ss_remove_wage_cap=True,
            ss_progressive_tax_enabled=True,
            ss_progressive_tax_threshold=250_000,
            ss_progressive_additional_rate=0.06,
        )
    
    @staticmethod
    def climate_focused_reform() -> Phase2PolicyPackage:
        """Climate and environmental focus."""
        return Phase2PolicyPackage(
            carbon_tax_enabled=True,
            carbon_tax_params=CarbonTaxParameters(
                price_per_ton_co2=50.0,
                annual_price_increase=0.05,
                total_emissions_mt=5_000,
            ),
        )


def create_phase2_comparison_scenarios() -> List[Tuple[str, Phase2PolicyPackage]]:
    """
    Create a comprehensive set of Phase 2 comparison scenarios.
    
    Returns:
        List of (scenario_name, policy_package) tuples
    """
    return [
        ("Baseline (No Reforms)", Phase2PolicyPackage()),
        ("Comprehensive Progressive", Phase2ReformPackages.comprehensive_progressive_reform()),
        ("Moderate Reform", Phase2ReformPackages.moderate_reform()),
        ("Revenue Maximization", Phase2ReformPackages.revenue_focused_reform()),
        ("Benefit Preservation", Phase2ReformPackages.benefit_preservation_reform()),
        ("Climate-Focused", Phase2ReformPackages.climate_focused_reform()),
    ]


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Initialize engine
    engine = Phase2SimulationEngine(
        base_gdp=28_000.0,  # $28T GDP
        population=340.0,   # 340M population
        start_year=2025,
    )
    
    # Create reform package
    reform = Phase2ReformPackages.comprehensive_progressive_reform()
    
    # Run simulation
    results = engine.simulate_comprehensive_reform(reform, years=10)
    
    print("\n=== Phase 2 Simulation Results ===")
    print(results['overview'][['year', 'total_new_revenue', 'ss_trust_fund_balance', 'net_fiscal_impact']])
