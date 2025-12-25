"""
Policy Enhancements Module
Advanced features for policy analysis, recommendations, and interactive exploration.

Features:
- PolicyRecommendationEngine: Suggest best policies based on fiscal goals
- InteractiveScenarioExplorer: Compare multiple scenarios with real-time updates
- PolicyImpactCalculator: Calculate fiscal impact of policy changes
- PolicyComparator: Advanced comparison with multiple metrics
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class FiscalGoal(Enum):
    """Fiscal policy goals."""
    MINIMIZE_DEFICIT = "minimize_deficit"
    MAXIMIZE_REVENUE = "maximize_revenue"
    REDUCE_SPENDING = "reduce_spending"
    BALANCE_BUDGET = "balance_budget"
    SUSTAINABLE_DEBT = "sustainable_debt"
    GROWTH_FOCUSED = "growth_focused"
    EQUITY_FOCUSED = "equity_focused"


@dataclass
class PolicyScore:
    """Score and ranking for a policy."""
    policy_name: str
    overall_score: float  # 0-100
    fiscal_impact: float  # Deficit reduction in $B
    sustainability: float  # 0-100 (how sustainable is this policy)
    feasibility: float  # 0-100 (political feasibility)
    equity_score: float  # 0-100 (progressive vs regressive)
    growth_impact: float  # -100 to 100 (negative = contraction, positive = growth)
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "policy_name": self.policy_name,
            "overall_score": round(self.overall_score, 1),
            "fiscal_impact": f"${self.fiscal_impact:,.0f}B",
            "sustainability": f"{self.sustainability:.0f}%",
            "feasibility": f"{self.feasibility:.0f}%",
            "equity_score": f"{self.equity_score:.0f}%",
            "growth_impact": f"{self.growth_impact:+.1f}%",
        }


class PolicyRecommendationEngine:
    """Recommends policies based on fiscal goals and constraints."""
    
    def __init__(self):
        """Initialize recommendation engine."""
        self.policy_scores: Dict[str, PolicyScore] = {}
    
    def score_policy(
        self,
        policy_name: str,
        deficit_reduction: float,  # $B per year
        revenue_change: float,  # % change
        spending_change: float,  # % change
        growth_impact: float,  # % impact on GDP growth
        equity_impact: str = "neutral",  # "regressive", "neutral", "progressive"
        feasibility: float = 50.0,  # 0-100
    ) -> PolicyScore:
        """
        Score a policy on multiple dimensions.
        
        Args:
            policy_name: Name of policy
            deficit_reduction: Annual deficit reduction in billions
            revenue_change: Percent change in revenue
            spending_change: Percent change in spending
            growth_impact: Impact on GDP growth rate (percentage points)
            equity_impact: "regressive", "neutral", or "progressive"
            feasibility: Political feasibility 0-100
        
        Returns:
            PolicyScore object
        """
        # Fiscal impact score (normalized to 0-25)
        # Assume $500B deficit reduction = 25 points
        fiscal_score = min((deficit_reduction / 500) * 25, 25)
        
        # Sustainability score (based on balance and growth)
        # Positive growth and deficit reduction = more sustainable
        sustainability = min(50 + (deficit_reduction / 100) + (growth_impact * 5), 100)
        
        # Equity score
        equity_map = {
            "regressive": 30.0,
            "neutral": 50.0,
            "progressive": 75.0,
        }
        equity_score = equity_map.get(equity_impact, 50.0)
        
        # Growth impact normalized to -100 to 100
        growth_normalized = growth_impact * 10  # Assuming max 10% impact
        
        # Overall score: 40% fiscal + 30% sustainability + 15% equity + 15% feasibility
        overall = (
            (fiscal_score / 25) * 40 +
            (sustainability / 100) * 30 +
            (equity_score / 100) * 15 +
            (feasibility / 100) * 15
        )
        
        score = PolicyScore(
            policy_name=policy_name,
            overall_score=overall,
            fiscal_impact=deficit_reduction,
            sustainability=sustainability,
            feasibility=feasibility,
            equity_score=equity_score,
            growth_impact=growth_normalized,
        )
        
        self.policy_scores[policy_name] = score
        return score
    
    def recommend_policies(
        self,
        goal: FiscalGoal,
        num_recommendations: int = 3,
    ) -> List[PolicyScore]:
        """
        Recommend policies for a specific goal.
        
        Args:
            goal: FiscalGoal enum
            num_recommendations: Number of recommendations to return
        
        Returns:
            Sorted list of PolicyScore objects
        """
        if not self.policy_scores:
            return []
        
        # Weight scoring based on goal
        weighted_scores = {}
        
        for name, score in self.policy_scores.items():
            if goal == FiscalGoal.MINIMIZE_DEFICIT:
                # Weight: fiscal impact (50%), sustainability (30%), feasibility (20%)
                weighted = (
                    (score.fiscal_impact / 1000) * 50 +
                    (score.sustainability / 100) * 30 +
                    (score.feasibility / 100) * 20
                )
            elif goal == FiscalGoal.MAXIMIZE_REVENUE:
                # Weight: revenue increase, feasibility
                weighted = (score.feasibility / 100) * 60 + (score.overall_score / 100) * 40
            elif goal == FiscalGoal.BALANCE_BUDGET:
                # Weight: fiscal impact (50%), sustainability (50%)
                weighted = (
                    (score.fiscal_impact / 1000) * 50 +
                    (score.sustainability / 100) * 50
                )
            elif goal == FiscalGoal.SUSTAINABLE_DEBT:
                # Weight: sustainability (60%), equity (20%), feasibility (20%)
                weighted = (
                    (score.sustainability / 100) * 60 +
                    (score.equity_score / 100) * 20 +
                    (score.feasibility / 100) * 20
                )
            elif goal == FiscalGoal.GROWTH_FOCUSED:
                # Weight: growth impact (50%), feasibility (30%), overall (20%)
                weighted = (
                    ((score.growth_impact + 100) / 200) * 50 +
                    (score.feasibility / 100) * 30 +
                    (score.overall_score / 100) * 20
                )
            elif goal == FiscalGoal.EQUITY_FOCUSED:
                # Weight: equity (50%), feasibility (30%), overall (20%)
                weighted = (
                    (score.equity_score / 100) * 50 +
                    (score.feasibility / 100) * 30 +
                    (score.overall_score / 100) * 20
                )
            else:  # REDUCE_SPENDING
                weighted = score.overall_score
            
            weighted_scores[name] = weighted
        
        # Sort and return top N
        sorted_policies = sorted(
            weighted_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            self.policy_scores[name]
            for name, _ in sorted_policies[:num_recommendations]
        ]
    
    def get_policy_reasoning(self, policy_name: str) -> List[str]:
        """Get explanation for policy score."""
        if policy_name not in self.policy_scores:
            return []
        
        score = self.policy_scores[policy_name]
        reasoning = []
        
        if score.fiscal_impact > 200:
            reasoning.append(f"Strong deficit reduction of ${score.fiscal_impact:,.0f}B/year")
        elif score.fiscal_impact > 50:
            reasoning.append(f"Moderate deficit reduction of ${score.fiscal_impact:,.0f}B/year")
        
        if score.sustainability > 75:
            reasoning.append("Highly sustainable long-term")
        elif score.sustainability > 50:
            reasoning.append("Moderately sustainable")
        
        if score.feasibility > 75:
            reasoning.append("High political feasibility")
        elif score.feasibility < 25:
            reasoning.append("Challenging political environment")
        
        if score.equity_score > 70:
            reasoning.append("Progressive/equitable design")
        elif score.equity_score < 35:
            reasoning.append("Regressive elements present")
        
        if score.growth_impact > 0.5:
            reasoning.append(f"Positive growth impact (+{score.growth_impact:.1f}%)")
        elif score.growth_impact < -0.5:
            reasoning.append(f"Potential drag on growth ({score.growth_impact:.1f}%)")
        
        return reasoning


class PolicyImpactCalculator:
    """Calculate real-time fiscal impact of policy changes."""
    
    @staticmethod
    def calculate_impact(
        base_revenue: float,  # $B
        base_spending: float,  # $B
        revenue_change_pct: float,  # % change
        spending_change_pct: float,  # % change
        years: int = 10,
    ) -> pd.DataFrame:
        """
        Calculate fiscal impact over time.
        
        Args:
            base_revenue: Starting revenue in billions
            base_spending: Starting spending in billions
            revenue_change_pct: Percent change in revenue (positive = increase)
            spending_change_pct: Percent change in spending (negative = decrease)
            years: Number of years to project
        
        Returns:
            DataFrame with year-by-year fiscal impact
        """
        results = []
        
        for year in range(years):
            # Apply changes with 2% annual growth
            annual_revenue = base_revenue * ((1 + revenue_change_pct/100) ** ((year + 1) / years)) * (1.02 ** year)
            annual_spending = base_spending * ((1 + spending_change_pct/100) ** ((year + 1) / years)) * (1.02 ** year)
            
            deficit = annual_spending - annual_revenue
            deficit_change = deficit - (base_spending - base_revenue)
            
            results.append({
                "year": 2025 + year,
                "revenue": annual_revenue,
                "spending": annual_spending,
                "deficit": deficit,
                "deficit_change": deficit_change,
                "cumulative_savings": -deficit_change * (year + 1),  # Simplified
            })
        
        return pd.DataFrame(results)
    
    @staticmethod
    def compare_scenarios(
        scenarios: Dict[str, Dict[str, float]],
        base_revenue: float = 5_980.0,
        base_spending: float = 6_911.0,
    ) -> pd.DataFrame:
        """
        Compare fiscal impact across multiple scenarios.
        
        Args:
            scenarios: Dict of scenario name -> {revenue_change_pct, spending_change_pct}
            base_revenue: Baseline revenue
            base_spending: Baseline spending
        
        Returns:
            DataFrame comparing scenarios
        """
        comparison = []
        
        for scenario_name, params in scenarios.items():
            impact_df = PolicyImpactCalculator.calculate_impact(
                base_revenue,
                base_spending,
                params.get("revenue_change_pct", 0),
                params.get("spending_change_pct", 0),
                years=10
            )
            
            # 10-year totals
            if impact_df.empty:
                logger.warning(f"Impact DataFrame for {scenario_name} is empty, skipping")
                continue
            
            total_deficit = impact_df["deficit"].sum()
            total_savings = impact_df["cumulative_savings"].iloc[-1]
            avg_annual_deficit = impact_df["deficit"].mean()
            
            comparison.append({
                "Scenario": scenario_name,
                "10-Year Total Deficit": f"${total_deficit:,.0f}B",
                "Cumulative Savings": f"${total_savings:,.0f}B",
                "Avg Annual Deficit": f"${avg_annual_deficit:,.0f}B",
                "Final Year Revenue": f"${impact_df['revenue'].iloc[-1]:,.0f}B",
                "Final Year Spending": f"${impact_df['spending'].iloc[-1]:,.0f}B",
            })
        
        return pd.DataFrame(comparison)


@dataclass
class ScenarioConfig:
    """Configuration for a scenario."""
    name: str
    revenue_change_pct: float
    spending_change_pct: float
    description: str = ""


class InteractiveScenarioExplorer:
    """Explore and compare multiple policy scenarios interactively."""
    
    def __init__(self, base_revenue: float = 5_980.0, base_spending: float = 6_911.0):
        """Initialize explorer with baseline values."""
        self.base_revenue = base_revenue
        self.base_spending = base_spending
        self.scenarios: Dict[str, ScenarioConfig] = {}
        self.results: Dict[str, pd.DataFrame] = {}
    
    def add_scenario(
        self,
        name: str,
        revenue_change_pct: float,
        spending_change_pct: float,
        description: str = "",
    ) -> None:
        """Add a scenario to explore."""
        self.scenarios[name] = ScenarioConfig(
            name=name,
            revenue_change_pct=revenue_change_pct,
            spending_change_pct=spending_change_pct,
            description=description,
        )
    
    def calculate_all_scenarios(self, years: int = 10) -> None:
        """Calculate results for all scenarios."""
        for name, config in self.scenarios.items():
            self.results[name] = PolicyImpactCalculator.calculate_impact(
                self.base_revenue,
                self.base_spending,
                config.revenue_change_pct,
                config.spending_change_pct,
                years=years,
            )
    
    def get_scenario_summary(self) -> pd.DataFrame:
        """Get summary of all scenarios."""
        if not self.results:
            self.calculate_all_scenarios()
        
        summaries = []
        for name, df in self.results.items():
            config = self.scenarios[name]
            summaries.append({
                "Scenario": name,
                "Description": config.description,
                "Revenue Change": f"{config.revenue_change_pct:+.1f}%",
                "Spending Change": f"{config.spending_change_pct:+.1f}%",
                "10-Year Deficit": f"${df['deficit'].sum():,.0f}B",
                "Avg Annual Deficit": f"${df['deficit'].mean():,.0f}B",
                "Final Year Deficit": f"${df['deficit'].iloc[-1]:,.0f}B",
            })
        
        return pd.DataFrame(summaries)
    
    def get_best_scenario(self, metric: str = "lowest_deficit") -> Tuple[str, pd.DataFrame]:
        """
        Get best scenario by metric.
        
        Args:
            metric: "lowest_deficit", "highest_revenue", "best_balance"
        
        Returns:
            Tuple of (scenario_name, scenario_df)
        """
        if not self.results:
            self.calculate_all_scenarios()
        
        if metric == "lowest_deficit":
            best = min(
                self.results.items(),
                key=lambda x: x[1]["deficit"].sum()
            )
        elif metric == "highest_revenue":
            best = max(
                self.results.items(),
                key=lambda x: x[1]["revenue"].sum()
            )
        elif metric == "best_balance":
            best = min(
                self.results.items(),
                key=lambda x: abs(x[1]["deficit"].mean())
            )
        else:
            best = list(self.results.items())[0]
        
        return best[0], best[1]


class PolicyComparator:
    """Advanced policy comparison with multiple metrics."""
    
    @staticmethod
    def create_comparison_matrix(
        policies: Dict[str, Dict[str, float]],
        metrics: List[str] = None,
    ) -> pd.DataFrame:
        """
        Create comprehensive comparison matrix.
        
        Args:
            policies: Dict of policy_name -> {metric_name: value}
            metrics: List of metrics to compare (None = all)
        
        Returns:
            DataFrame with policies as rows, metrics as columns
        """
        if not policies:
            return pd.DataFrame()
        
        # Get all metrics if not specified
        if metrics is None:
            all_metrics = set()
            for policy_metrics in policies.values():
                all_metrics.update(policy_metrics.keys())
            metrics = sorted(all_metrics)
        
        # Build comparison matrix
        rows = []
        for policy_name, policy_metrics in policies.items():
            row = {"Policy": policy_name}
            for metric in metrics:
                value = policy_metrics.get(metric, np.nan)
                row[metric] = value
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    @staticmethod
    def rank_policies(
        comparison_df: pd.DataFrame,
        weights: Dict[str, float] = None,
    ) -> pd.DataFrame:
        """
        Rank policies based on weighted score.
        
        Args:
            comparison_df: Comparison matrix from create_comparison_matrix
            weights: Dict of metric -> weight (must sum to 1.0)
        
        Returns:
            DataFrame with rankings
        """
        if comparison_df.empty or "Policy" not in comparison_df.columns:
            return comparison_df
        
        # Default equal weights
        numeric_cols = [
            col for col in comparison_df.columns
            if col != "Policy" and pd.api.types.is_numeric_dtype(comparison_df[col])
        ]
        
        if not numeric_cols:
            return comparison_df
        
        if weights is None:
            weights = {col: 1.0 / len(numeric_cols) for col in numeric_cols}
        
        # Normalize each metric to 0-100
        normalized_df = comparison_df.copy()
        for col in numeric_cols:
            min_val = comparison_df[col].min()
            max_val = comparison_df[col].max()
            if max_val > min_val:
                normalized_df[col] = (
                    (comparison_df[col] - min_val) / (max_val - min_val) * 100
                )
            else:
                normalized_df[col] = 50  # Equal score if all same
        
        # Calculate weighted score
        score_cols = [col for col in numeric_cols if col in weights]
        if score_cols:
            normalized_df["Weighted Score"] = 0
            for col in score_cols:
                normalized_df["Weighted Score"] += normalized_df[col] * weights.get(col, 0)
        
        # Sort by score
        result = normalized_df.sort_values("Weighted Score", ascending=False)
        
        return result
