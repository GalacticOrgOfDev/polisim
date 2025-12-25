"""
Tax Reform Module - CBO 2.0 Phase 2
Comprehensive tax policy analysis including wealth tax, consumption tax, 
carbon tax, financial transaction tax, and distributional analysis.

Covers:
- Wealth taxation on high net worth individuals
- Consumption taxes (VAT/sales tax)
- Carbon pricing and emissions taxation
- Financial transaction taxes
- Tax incidence and distributional analysis
- Behavioral response modeling
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class TaxType(Enum):
    """Types of taxes in the reform module."""
    WEALTH = "wealth"
    CONSUMPTION = "consumption"
    CARBON = "carbon"
    FINANCIAL_TRANSACTION = "financial_transaction"
    INCOME = "income"
    CORPORATE = "corporate"
    PAYROLL = "payroll"


@dataclass
class WealthTaxParameters:
    """Parameters for wealth tax implementation."""
    
    # Base parameters
    exemption_threshold: float = 50_000_000  # $50M exemption
    tax_rate_tier_1: float = 0.02  # 2% on $50M-$1B
    tax_rate_tier_2: float = 0.03  # 3% on $1B+
    tier_2_threshold: float = 1_000_000_000  # $1B
    
    # Enforcement and avoidance
    valuation_method: str = "fair_market_value"
    avoidance_rate: float = 0.20  # 20% avoid through legal means
    evasion_rate: float = 0.05  # 5% evade illegally
    audit_rate: float = 0.30  # 30% of filers audited
    
    # Economic assumptions
    total_wealth_top_0_1_pct: float = 15_000  # $15T held by top 0.1%
    number_of_liable_households: int = 130_000  # ~130k households
    
    @classmethod
    def progressive_wealth_tax(cls) -> "WealthTaxParameters":
        """Progressive wealth tax (Warren/Sanders style)."""
        return cls(
            exemption_threshold=50_000_000,
            tax_rate_tier_1=0.02,
            tax_rate_tier_2=0.06,  # Higher top rate
            tier_2_threshold=1_000_000_000
        )
    
    @classmethod
    def moderate_wealth_tax(cls) -> "WealthTaxParameters":
        """Moderate wealth tax with higher exemption."""
        return cls(
            exemption_threshold=100_000_000,
            tax_rate_tier_1=0.01,
            tax_rate_tier_2=0.02,
            tier_2_threshold=1_000_000_000
        )


@dataclass
class ConsumptionTaxParameters:
    """Parameters for consumption/VAT tax."""
    
    # Base parameters
    tax_rate: float = 0.10  # 10% VAT
    
    # Exemptions
    exempt_food: bool = True
    exempt_medicine: bool = True
    exempt_housing: bool = True
    exemption_share: float = 0.30  # 30% of consumption exempt
    
    # Regressivity adjustments
    low_income_rebate: bool = True
    rebate_threshold: float = 50_000  # Income below this gets rebate
    rebate_amount: float = 2_000  # Annual rebate per household
    
    # Economic base
    total_consumption_gdp_share: float = 0.68  # 68% of GDP
    
    @classmethod
    def broad_based_vat(cls) -> "ConsumptionTaxParameters":
        """Broad-based VAT with limited exemptions."""
        return cls(
            tax_rate=0.10,
            exempt_food=False,
            exempt_medicine=True,
            exempt_housing=True,
            exemption_share=0.15,
            low_income_rebate=True
        )
    
    @classmethod
    def progressive_consumption_tax(cls) -> "ConsumptionTaxParameters":
        """Progressive consumption tax with broad exemptions."""
        return cls(
            tax_rate=0.05,
            exempt_food=True,
            exempt_medicine=True,
            exempt_housing=True,
            exemption_share=0.40,
            low_income_rebate=True,
            rebate_amount=3_000
        )


@dataclass
class CarbonTaxParameters:
    """Parameters for carbon pricing."""
    
    # Base parameters
    price_per_ton_co2: float = 50.0  # $/ton CO2
    annual_price_increase: float = 0.05  # 5% annual increase
    
    # Emissions base
    total_emissions_mt: float = 5_000  # 5 billion metric tons/year
    emissions_elasticity: float = -0.7  # Price elasticity
    
    # Revenue distribution
    dividend_share: float = 0.60  # 60% returned as dividend
    transition_assistance: float = 0.20  # 20% to affected industries
    investment_share: float = 0.20  # 20% to clean energy
    
    # Sectoral impacts
    sectoral_emissions: Dict[str, float] = field(default_factory=lambda: {
        "electricity": 1_750,  # MT CO2
        "transportation": 1_850,
        "industry": 900,
        "residential_commercial": 500
    })
    
    @classmethod
    def aggressive_carbon_tax(cls) -> "CarbonTaxParameters":
        """Aggressive carbon tax ($100/ton)."""
        return cls(
            price_per_ton_co2=100.0,
            annual_price_increase=0.10,
            dividend_share=0.50,
            transition_assistance=0.30,
            investment_share=0.20
        )
    
    @classmethod
    def moderate_carbon_tax(cls) -> "CarbonTaxParameters":
        """Moderate carbon tax ($25/ton)."""
        return cls(
            price_per_ton_co2=25.0,
            annual_price_increase=0.03,
            dividend_share=0.70,
            transition_assistance=0.15,
            investment_share=0.15
        )


@dataclass
class FinancialTransactionTaxParameters:
    """Parameters for financial transaction tax."""
    
    # Base parameters
    stock_tax_rate: float = 0.001  # 0.1% on stocks
    bond_tax_rate: float = 0.0005  # 0.05% on bonds
    derivative_tax_rate: float = 0.0002  # 0.02% on derivatives
    
    # Trading volume (annual, trillions)
    stock_volume: float = 50_000  # $50T
    bond_volume: float = 25_000  # $25T
    derivative_volume: float = 600_000  # $600T (notional)
    
    # Behavioral responses
    volume_elasticity: float = -1.5  # Trading reduces with tax
    
    # Exemptions
    exempt_retirement_accounts: bool = True
    retirement_share: float = 0.15  # 15% of trading
    exempt_market_makers: bool = True
    market_maker_share: float = 0.10  # 10% of trading
    
    @classmethod
    def progressive_ftt(cls) -> "FinancialTransactionTaxParameters":
        """Progressive FTT with higher rates."""
        return cls(
            stock_tax_rate=0.005,  # 0.5%
            bond_tax_rate=0.001,  # 0.1%
            derivative_tax_rate=0.0005  # 0.05%
        )
    
    @classmethod
    def minimal_ftt(cls) -> "FinancialTransactionTaxParameters":
        """Minimal FTT focused on high-frequency trading."""
        return cls(
            stock_tax_rate=0.0001,  # 0.01%
            bond_tax_rate=0.00005,  # 0.005%
            derivative_tax_rate=0.00001,  # 0.001%
            exempt_retirement_accounts=True,
            exempt_market_makers=False
        )


class WealthTaxModel:
    """Model wealth taxation with enforcement and avoidance."""
    
    def __init__(self, parameters: Optional[WealthTaxParameters] = None):
        self.params = parameters or WealthTaxParameters()
        logger.info(f"Wealth tax model initialized: ${self.params.exemption_threshold/1e6:.0f}M threshold")
    
    def calculate_gross_revenue(
        self,
        total_wealth: float,
        number_households: int
    ) -> float:
        """Calculate gross wealth tax revenue before avoidance."""
        # Estimate wealth distribution (simplified tiered approach)
        wealth_tier_1 = total_wealth * 0.40  # 40% between $50M-$1B
        wealth_tier_2 = total_wealth * 0.60  # 60% above $1B
        
        revenue_tier_1 = wealth_tier_1 * self.params.tax_rate_tier_1
        revenue_tier_2 = wealth_tier_2 * self.params.tax_rate_tier_2
        
        gross_revenue = revenue_tier_1 + revenue_tier_2
        
        logger.debug(f"Gross wealth tax revenue: ${gross_revenue:.1f}B")
        return gross_revenue
    
    def apply_avoidance_and_evasion(self, gross_revenue: float) -> float:
        """Apply tax avoidance and evasion adjustments."""
        # Legal avoidance (trusts, foundations, etc.)
        after_avoidance = gross_revenue * (1 - self.params.avoidance_rate)
        
        # Evasion (despite enforcement)
        net_revenue = after_avoidance * (1 - self.params.evasion_rate)
        
        logger.debug(f"Net wealth tax revenue after avoidance/evasion: ${net_revenue:.1f}B")
        return net_revenue
    
    def project_revenue(self, years: int = 10) -> pd.DataFrame:
        """Project wealth tax revenue over multiple years."""
        results = []
        
        for year in range(years):
            # Wealth grows with capital returns (~7% annually)
            wealth_growth = (1.07 ** year)
            current_wealth = self.params.total_wealth_top_0_1_pct * wealth_growth
            
            gross_rev = self.calculate_gross_revenue(
                current_wealth,
                self.params.number_of_liable_households
            )
            net_rev = self.apply_avoidance_and_evasion(gross_rev)
            
            results.append({
                "year": 2025 + year,
                "total_wealth_taxable": current_wealth,
                "gross_revenue": gross_rev,
                "net_revenue": net_rev,
                "avoidance_loss": gross_rev - net_rev
            })
        
        return pd.DataFrame(results)


class ConsumptionTaxModel:
    """Model consumption tax (VAT) with exemptions and regressivity adjustments."""
    
    def __init__(self, parameters: Optional[ConsumptionTaxParameters] = None):
        self.params = parameters or ConsumptionTaxParameters()
        logger.info(f"Consumption tax model initialized: {self.params.tax_rate:.1%} rate")
    
    def calculate_gross_revenue(self, gdp: float) -> float:
        """Calculate gross consumption tax revenue."""
        consumption_base = gdp * self.params.total_consumption_gdp_share
        taxable_consumption = consumption_base * (1 - self.params.exemption_share)
        gross_revenue = taxable_consumption * self.params.tax_rate
        
        logger.debug(f"Gross consumption tax revenue: ${gross_revenue:.1f}B")
        return gross_revenue
    
    def calculate_rebate_cost(self, population: float) -> float:
        """Calculate cost of low-income rebates."""
        if not self.params.low_income_rebate:
            return 0.0
        
        # Assume ~40% of households below threshold
        households_below_threshold = (population / 2.5) * 0.40  # ~2.5 people per household
        rebate_cost = households_below_threshold * self.params.rebate_amount / 1_000  # Convert to billions
        
        logger.debug(f"Rebate cost: ${rebate_cost:.1f}B")
        return rebate_cost
    
    def analyze_distributional_impact(
        self,
        income_quintiles: pd.DataFrame
    ) -> pd.DataFrame:
        """Analyze burden by income quintile."""
        # Consumption tax is regressive - lower income spend higher % of income
        consumption_shares = {
            "Q1": 1.10,  # Spend 110% of income (dissaving)
            "Q2": 0.95,
            "Q3": 0.85,
            "Q4": 0.75,
            "Q5": 0.50   # Top quintile saves 50%
        }
        
        results = []
        for quintile, consumption_rate in consumption_shares.items():
            effective_rate = self.params.tax_rate * consumption_rate * (1 - self.params.exemption_share)
            results.append({
                "quintile": quintile,
                "consumption_rate": consumption_rate,
                "effective_tax_rate": effective_rate,
                "burden_index": effective_rate / consumption_shares["Q5"]  # Relative to richest
            })
        
        return pd.DataFrame(results)
    
    def project_revenue(self, years: int, gdp_growth: np.ndarray, population: float) -> pd.DataFrame:
        """Project consumption tax revenue."""
        results = []
        base_gdp = 28_000  # $28T baseline
        
        for year in range(years):
            current_gdp = base_gdp * ((1 + gdp_growth[year]) ** (year + 1))
            gross_rev = self.calculate_gross_revenue(current_gdp)
            rebate_cost = self.calculate_rebate_cost(population)
            net_rev = gross_rev - rebate_cost
            
            results.append({
                "year": 2025 + year,
                "gdp": current_gdp,
                "gross_revenue": gross_rev,
                "rebate_cost": rebate_cost,
                "net_revenue": net_rev
            })
        
        return pd.DataFrame(results)


class CarbonTaxModel:
    """Model carbon pricing with emissions reduction and revenue distribution."""
    
    def __init__(self, parameters: Optional[CarbonTaxParameters] = None):
        self.params = parameters or CarbonTaxParameters()
        logger.info(f"Carbon tax model initialized: ${self.params.price_per_ton_co2:.0f}/ton CO2")
    
    def calculate_emissions_reduction(self, price: float, year: int) -> float:
        """Calculate emissions reduction from carbon pricing."""
        # Price elasticity: -0.7 means 10% price increase -> 7% emissions reduction
        price_increase_pct = (price - 50) / 50  # Relative to $50 baseline
        emissions_reduction_pct = price_increase_pct * self.params.emissions_elasticity
        
        # Also account for technological improvement over time
        tech_improvement = 0.02 * year  # 2% per year improvement
        
        total_reduction = min(emissions_reduction_pct + tech_improvement, 0.90)  # Max 90% reduction
        reduced_emissions = self.params.total_emissions_mt * (1 + total_reduction)
        
        return max(reduced_emissions, 500)  # Floor of 500 MT
    
    def calculate_revenue(self, emissions: float, price: float) -> float:
        """Calculate carbon tax revenue."""
        revenue = emissions * price
        logger.debug(f"Carbon tax revenue: ${revenue:.1f}B from {emissions:.0f} MT at ${price:.0f}/ton")
        return revenue
    
    def distribute_revenue(self, total_revenue: float) -> Dict[str, float]:
        """Distribute carbon revenue according to policy."""
        return {
            "citizen_dividend": total_revenue * self.params.dividend_share,
            "transition_assistance": total_revenue * self.params.transition_assistance,
            "clean_energy_investment": total_revenue * self.params.investment_share
        }
    
    def analyze_sectoral_impact(self, carbon_price: float) -> pd.DataFrame:
        """Analyze impact on different economic sectors."""
        results = []
        
        for sector, emissions in self.params.sectoral_emissions.items():
            cost_impact = emissions * carbon_price
            
            # Sector-specific pass-through rates
            pass_through = {
                "electricity": 0.90,  # 90% passed to consumers
                "transportation": 0.70,
                "industry": 0.50,
                "residential_commercial": 0.80
            }
            
            results.append({
                "sector": sector,
                "emissions_mt": emissions,
                "cost_impact_billions": cost_impact,
                "consumer_burden_billions": cost_impact * pass_through.get(sector, 0.70),
                "producer_burden_billions": cost_impact * (1 - pass_through.get(sector, 0.70))
            })
        
        return pd.DataFrame(results)
    
    def project_revenue(self, years: int = 10) -> pd.DataFrame:
        """Project carbon tax revenue with declining emissions."""
        results = []
        
        for year in range(years):
            # Price increases annually
            current_price = self.params.price_per_ton_co2 * ((1 + self.params.annual_price_increase) ** year)
            
            # Emissions decline due to price and technology
            current_emissions = self.calculate_emissions_reduction(current_price, year)
            
            # Revenue
            revenue = self.calculate_revenue(current_emissions, current_price)
            distribution = self.distribute_revenue(revenue)
            
            results.append({
                "year": 2025 + year,
                "carbon_price": current_price,
                "emissions_mt": current_emissions,
                "total_revenue": revenue,
                **distribution
            })
        
        return pd.DataFrame(results)


class FinancialTransactionTaxModel:
    """Model financial transaction tax with volume response."""
    
    def __init__(self, parameters: Optional[FinancialTransactionTaxParameters] = None):
        self.params = parameters or FinancialTransactionTaxParameters()
        logger.info(f"FTT model initialized: {self.params.stock_tax_rate:.3%} on stocks")
    
    def calculate_volume_impact(self, baseline_volume: float, tax_rate: float) -> float:
        """Calculate trading volume reduction from FTT."""
        # Volume elasticity: -1.5 means 1% tax -> 1.5% volume reduction
        volume_reduction_pct = tax_rate * self.params.volume_elasticity
        adjusted_volume = baseline_volume * (1 + volume_reduction_pct)
        
        return max(adjusted_volume, baseline_volume * 0.30)  # Floor at 30% of baseline
    
    def calculate_revenue_by_asset_class(self) -> Dict[str, float]:
        """Calculate FTT revenue by asset class."""
        # Apply exemptions
        exemption_factor = 1.0
        if self.params.exempt_retirement_accounts:
            exemption_factor -= self.params.retirement_share
        if self.params.exempt_market_makers:
            exemption_factor -= self.params.market_maker_share
        
        # Stocks
        stock_volume_adjusted = self.calculate_volume_impact(
            self.params.stock_volume,
            self.params.stock_tax_rate
        )
        stock_revenue = stock_volume_adjusted * self.params.stock_tax_rate * exemption_factor
        
        # Bonds
        bond_volume_adjusted = self.calculate_volume_impact(
            self.params.bond_volume,
            self.params.bond_tax_rate
        )
        bond_revenue = bond_volume_adjusted * self.params.bond_tax_rate * exemption_factor
        
        # Derivatives (notional value, so actual revenue is much smaller)
        derivative_volume_adjusted = self.calculate_volume_impact(
            self.params.derivative_volume,
            self.params.derivative_tax_rate
        )
        derivative_revenue = derivative_volume_adjusted * self.params.derivative_tax_rate * exemption_factor * 0.1  # Only 10% of notional
        
        return {
            "stocks": stock_revenue,
            "bonds": bond_revenue,
            "derivatives": derivative_revenue
        }
    
    def assess_market_efficiency_impact(self) -> Dict[str, Any]:
        """Assess impact on market quality."""
        # Higher FTT -> wider spreads, more volatility
        bid_ask_spread_increase = self.params.stock_tax_rate * 2.0  # Spreads widen by 2x tax rate
        volatility_change = -0.05  # Slight reduction in volatility (less HFT)
        
        return {
            "bid_ask_spread_increase_pct": bid_ask_spread_increase,
            "volatility_change_pct": volatility_change,
            "hft_reduction_pct": min(self.params.stock_tax_rate * 100, 0.80),  # Up to 80% HFT reduction
            "liquidity_impact": "negative" if self.params.stock_tax_rate > 0.001 else "minimal"
        }
    
    def project_revenue(self, years: int = 10) -> pd.DataFrame:
        """Project FTT revenue over time."""
        results = []
        
        for year in range(years):
            # Trading volume grows with GDP (~2.5% annually)
            volume_growth = (1.025 ** year)
            
            revenue_by_class = self.calculate_revenue_by_asset_class()
            
            # Adjust for volume growth
            total_revenue = sum(revenue_by_class.values()) * volume_growth
            
            results.append({
                "year": 2025 + year,
                "stock_revenue": revenue_by_class["stocks"] * volume_growth,
                "bond_revenue": revenue_by_class["bonds"] * volume_growth,
                "derivative_revenue": revenue_by_class["derivatives"] * volume_growth,
                "total_revenue": total_revenue
            })
        
        return pd.DataFrame(results)


class TaxIncidenceAnalyzer:
    """Analyze who actually bears the burden of various taxes."""
    
    def __init__(self):
        # Income distribution (quintiles, 2025 estimates)
        self.income_quintiles = pd.DataFrame({
            "quintile": ["Q1", "Q2", "Q3", "Q4", "Q5"],
            "avg_income": [15_000, 40_000, 70_000, 110_000, 280_000],
            "population_share": [0.20, 0.20, 0.20, 0.20, 0.20],
            "income_share": [0.03, 0.08, 0.14, 0.23, 0.52]
        })
        logger.info("Tax incidence analyzer initialized")
    
    def calculate_effective_tax_rates(
        self,
        tax_changes: Dict[str, float]
    ) -> pd.DataFrame:
        """Calculate effective tax rates by income quintile."""
        results = []
        
        for _, row in self.income_quintiles.iterrows():
            quintile = row["quintile"]
            income = row["avg_income"]
            
            # Calculate burden from each tax type
            # (Simplified - in reality this would be much more complex)
            income_tax_burden = tax_changes.get("income_tax", 0) * (income / 280_000) ** 1.2  # Progressive
            payroll_tax_burden = tax_changes.get("payroll_tax", 0)  # Flat up to cap
            consumption_tax_burden = tax_changes.get("consumption_tax", 0) * (1.1 - income / 560_000)  # Regressive
            
            total_burden = income_tax_burden + payroll_tax_burden + consumption_tax_burden
            effective_rate = total_burden / income if income > 0 else 0
            
            results.append({
                "quintile": quintile,
                "avg_income": income,
                "income_tax_burden": income_tax_burden,
                "payroll_tax_burden": payroll_tax_burden,
                "consumption_tax_burden": consumption_tax_burden,
                "total_burden": total_burden,
                "effective_rate": effective_rate
            })
        
        return pd.DataFrame(results)
    
    def calculate_gini_coefficient(
        self,
        pre_tax_income: pd.Series,
        post_tax_income: pd.Series
    ) -> Tuple[float, float]:
        """Calculate Gini coefficient before and after tax."""
        def gini(x):
            # Sort values
            sorted_x = np.sort(x)
            n = len(x)
            cumsum = np.cumsum(sorted_x)
            return (2 * np.sum((np.arange(1, n + 1)) * sorted_x)) / (n * cumsum[-1]) - (n + 1) / n
        
        pre_tax_gini = gini(pre_tax_income.values)
        post_tax_gini = gini(post_tax_income.values)
        
        logger.info(f"Gini coefficient: {pre_tax_gini:.3f} (pre-tax) -> {post_tax_gini:.3f} (post-tax)")
        return pre_tax_gini, post_tax_gini
    
    def analyze_progressivity(
        self,
        tax_system: pd.DataFrame
    ) -> Dict[str, Any]:
        """Assess overall tax system progressivity."""
        # Calculate various progressivity metrics
        
        # 1. Tax burden ratio (top quintile / bottom quintile)
        top_rate = tax_system[tax_system["quintile"] == "Q5"]["effective_rate"].iloc[0]
        bottom_rate = tax_system[tax_system["quintile"] == "Q1"]["effective_rate"].iloc[0]
        progressivity_ratio = top_rate / bottom_rate if bottom_rate > 0 else float('inf')
        
        # 2. Kakwani index (tax concentration - income concentration)
        # Simplified version
        kakwani = (tax_system["effective_rate"] * tax_system.index).sum() / len(tax_system) - 0.5
        
        return {
            "progressivity_ratio": progressivity_ratio,
            "kakwani_index": kakwani,
            "system_type": "progressive" if progressivity_ratio > 1 else "regressive",
            "top_quintile_effective_rate": top_rate,
            "bottom_quintile_effective_rate": bottom_rate
        }
    
    def generate_distributional_table(
        self,
        baseline_system: pd.DataFrame,
        reformed_system: pd.DataFrame
    ) -> pd.DataFrame:
        """Generate CBO-style distributional table."""
        comparison = baseline_system.merge(
            reformed_system,
            on="quintile",
            suffixes=("_baseline", "_reform")
        )
        
        comparison["change_in_burden"] = (
            comparison["total_burden_reform"] - comparison["total_burden_baseline"]
        )
        comparison["change_in_rate"] = (
            comparison["effective_rate_reform"] - comparison["effective_rate_baseline"]
        )
        
        return comparison[["quintile", "avg_income_baseline", "effective_rate_baseline",
                          "effective_rate_reform", "change_in_rate", "change_in_burden"]]


class BehavioralResponseModel:
    """Model behavioral responses to tax changes."""
    
    @staticmethod
    def model_tax_avoidance_response(
        tax_rate_change: float,
        baseline_revenue: float,
        avoidance_elasticity: float = -0.25
    ) -> float:
        """Model tax avoidance in response to rate changes."""
        # Elasticity: -0.25 means 10% rate increase -> 2.5% revenue loss to avoidance
        avoidance_effect = tax_rate_change * avoidance_elasticity
        effective_revenue_change = baseline_revenue * (tax_rate_change + avoidance_effect)
        
        logger.debug(f"Tax avoidance reduces revenue by {abs(avoidance_effect * 100):.1f}%")
        return effective_revenue_change
    
    @staticmethod
    def model_labor_supply_response(
        marginal_rate_change: float,
        baseline_hours: float = 2000,
        labor_elasticity: float = -0.15
    ) -> float:
        """Model labor supply changes from tax changes."""
        # Elasticity: -0.15 means 10% rate increase -> 1.5% reduction in hours worked
        hours_change_pct = marginal_rate_change * labor_elasticity
        new_hours = baseline_hours * (1 + hours_change_pct)
        
        logger.debug(f"Labor supply changes by {hours_change_pct * 100:.1f}% due to tax change")
        return new_hours
    
    @staticmethod
    def model_corporate_profit_shifting(
        rate_differential: float,
        baseline_profits: float,
        shifting_elasticity: float = -0.80
    ) -> float:
        """Model profit shifting to low-tax jurisdictions."""
        # Elasticity: -0.80 means 10% rate differential -> 8% profit shift
        shifted_profits_pct = rate_differential * shifting_elasticity
        remaining_profits = baseline_profits * (1 + shifted_profits_pct)
        
        logger.debug(f"Profit shifting: {abs(shifted_profits_pct * 100):.1f}% of profits shifted")
        return remaining_profits
    
    @staticmethod
    def model_investment_response(
        after_tax_return_change: float,
        baseline_investment: float,
        investment_elasticity: float = 0.40
    ) -> float:
        """Model investment changes from tax-induced return changes."""
        # Elasticity: 0.40 means 10% return increase -> 4% more investment
        investment_change_pct = after_tax_return_change * investment_elasticity
        new_investment = baseline_investment * (1 + investment_change_pct)
        
        logger.debug(f"Investment changes by {investment_change_pct * 100:.1f}%")
        return new_investment


# Comprehensive tax reform analyzer
class ComprehensiveTaxReformAnalyzer:
    """Analyze comprehensive tax reform packages combining multiple tax types."""
    
    def __init__(self):
        self.wealth_tax = WealthTaxModel()
        self.consumption_tax = ConsumptionTaxModel()
        self.carbon_tax = CarbonTaxModel()
        self.ftt = FinancialTransactionTaxModel()
        self.incidence = TaxIncidenceAnalyzer()
        self.behavioral = BehavioralResponseModel()
        logger.info("Comprehensive tax reform analyzer initialized")
    
    def analyze_reform_package(
        self,
        reforms: Dict[str, Any],
        years: int = 10,
        gdp_baseline: float = 28_000,
        gdp_growth: Optional[np.ndarray] = None
    ) -> Dict[str, pd.DataFrame]:
        """Analyze a comprehensive tax reform package."""
        if gdp_growth is None:
            gdp_growth = np.full(years, 0.025)
        
        results = {}
        
        # Project each tax type if included in reform
        if "wealth_tax" in reforms:
            self.wealth_tax.params = WealthTaxParameters(**reforms["wealth_tax"])
            results["wealth_tax"] = self.wealth_tax.project_revenue(years)
        
        if "consumption_tax" in reforms:
            self.consumption_tax.params = ConsumptionTaxParameters(**reforms["consumption_tax"])
            results["consumption_tax"] = self.consumption_tax.project_revenue(years, gdp_growth, 335)
        
        if "carbon_tax" in reforms:
            self.carbon_tax.params = CarbonTaxParameters(**reforms["carbon_tax"])
            results["carbon_tax"] = self.carbon_tax.project_revenue(years)
        
        if "ftt" in reforms:
            self.ftt.params = FinancialTransactionTaxParameters(**reforms["ftt"])
            results["ftt"] = self.ftt.project_revenue(years)
        
        # Combine into total revenue projection
        total_revenue = self._combine_revenue_projections(results, years)
        results["total_combined"] = total_revenue
        
        # Distributional analysis
        tax_changes = self._extract_tax_changes(reforms)
        results["distributional"] = self.incidence.calculate_effective_tax_rates(tax_changes)
        
        return results
    
    def _combine_revenue_projections(
        self,
        projections: Dict[str, pd.DataFrame],
        years: int
    ) -> pd.DataFrame:
        """Combine revenue projections from different tax types."""
        combined = pd.DataFrame({"year": range(2025, 2025 + years)})
        
        for tax_type, df in projections.items():
            if tax_type in ["wealth_tax", "consumption_tax", "carbon_tax", "ftt"]:
                revenue_col = "net_revenue" if "net_revenue" in df.columns else "total_revenue"
                combined[f"{tax_type}_revenue"] = df[revenue_col].values
        
        # Sum all revenue columns
        revenue_cols = [col for col in combined.columns if col.endswith("_revenue")]
        combined["total_revenue"] = combined[revenue_cols].sum(axis=1)
        
        return combined
    
    def _extract_tax_changes(self, reforms: Dict[str, Any]) -> Dict[str, float]:
        """Extract tax burden changes for incidence analysis."""
        changes = {}
        
        if "wealth_tax" in reforms:
            changes["wealth_tax"] = reforms["wealth_tax"].get("tax_rate_tier_1", 0.02)
        
        if "consumption_tax" in reforms:
            changes["consumption_tax"] = reforms["consumption_tax"].get("tax_rate", 0.10)
        
        # Simplified - in reality would be more complex
        return changes
