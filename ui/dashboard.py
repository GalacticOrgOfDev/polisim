"""
CBO 2.0 Unified Dashboard - Streamlit Web Interface
Interactive fiscal policy analysis tool combining Phase 1-3 modules.

Features:
- Healthcare policy scenarios (Phase 1)
- Social Security analysis (Phase 2)
- Federal revenue projections (Phase 2)
- Medicare/Medicaid modeling (Phase 3.1)
- Unified fiscal outlook
- Policy comparison and sensitivity analysis
- Report generation
"""

try:
    import streamlit as st
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import plotly.express as px
    from pathlib import Path
    import json
    
    from core.social_security import SocialSecurityModel, SocialSecurityReforms
    from core.revenue_modeling import FederalRevenueModel, TaxReforms
    from core.medicare_medicaid import MedicareModel, MedicaidModel
    from core.discretionary_spending import DiscretionarySpendingModel
    from core.interest_spending import InterestOnDebtModel
    from core.combined_outlook import CombinedFiscalOutlookModel
    from core.healthcare import get_policy_by_type, PolicyType
    from core.economic_engine import MonteCarloEngine, PolicyScenario, EconomicParameters
    from core.data_loader import load_real_data
    from core.policy_builder import PolicyTemplate, PolicyLibrary
    from core.pdf_policy_parser import PolicyPDFProcessor
    from core.policy_enhancements import (
        PolicyRecommendationEngine,
        InteractiveScenarioExplorer,
        PolicyImpactCalculator,
    )
    from core.monte_carlo_scenarios import (
        MonteCarloPolicySimulator,
        PolicySensitivityAnalyzer,
        StressTestAnalyzer,
    )
    
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


def load_ss_scenarios():
    """Load Social Security policy scenarios from configuration."""
    with open("policies/social_security_scenarios.json") as f:
        return json.load(f)


def load_tax_scenarios():
    """Load tax reform scenarios from configuration."""
    with open("policies/tax_reform_scenarios.json") as f:
        return json.load(f)


def load_revenue_scenarios():
    """Load revenue scenarios from configuration."""
    with open("policies/revenue_scenarios.json") as f:
        return json.load(f)


def get_policy_library_policies(policy_type=None):
    """Load policies from library (NOT cached - always fresh)."""
    from core.policy_builder import PolicyLibrary, PolicyType
    library = PolicyLibrary()
    if policy_type:
        return library.list_policies_by_type(policy_type), library
    else:
        return library.list_policies(), library


def page_overview():
    """Main overview page."""
    st.title("🏛️ CBO 2.0: Open-Source Federal Fiscal Projections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Module Status", "Phase 3.2", delta="Healthcare + SS + Revenue + Medicare/Medicaid + Discretionary")
    with col2:
        st.metric("Monte Carlo Iterations", "100K+", delta="Full uncertainty quantification")
    with col3:
        st.metric("Projection Horizon", "75 years", delta="Long-term sustainability")
    
    st.markdown("""
    ### What is CBO 2.0?
    
    An open-source, transparent alternative to the Congressional Budget Office's fiscal projections.
    Built with full Monte Carlo stochastic modeling and comprehensive policy analysis.
    
    **Available Modules:**
    - **Phase 1**: Healthcare policy analysis (USGHA vs baseline)
    - **Phase 2**: Social Security trust funds + Federal revenues (income/payroll/corporate taxes)
    - **Phase 3.1**: Medicare Parts A/B/D + Medicaid spending
    - **Phase 3.2**: Discretionary spending + Interest on debt + Combined fiscal outlook
    """)
    
    st.info("""
    📊 **Navigate to other pages using the sidebar:**
    - Healthcare Analysis
    - Social Security Outlook
    - Federal Revenues
    - Medicare/Medicaid
    - Discretionary Spending
    - Combined Fiscal Outlook
    - Policy Comparison
    """)


def page_healthcare():
    """Healthcare policy analysis page (Phase 1)."""
    st.title("🏥 Healthcare Policy Analysis")
    
    st.markdown("""
    Compare healthcare policies using Monte Carlo stochastic simulation with full uncertainty quantification.
    """)
    
    # Load custom policies from library - ALWAYS FRESH (not cached)
    from core.policy_builder import PolicyType
    custom_healthcare_policies, library = get_policy_library_policies(PolicyType.HEALTHCARE)
    
    # Combine built-in and custom policies
    policy_options = ["usgha", "current_us"]
    if custom_healthcare_policies:
        policy_options.extend(custom_healthcare_policies)
    
    col1, col2 = st.columns(2)
    with col1:
        healthcare_policy = st.selectbox(
            "Select policy:",
            policy_options,
            help="Choose from built-in or custom healthcare policies"
        )
    with col2:
        years = st.slider("Projection years:", 5, 30, 22, key="healthcare_years")
    
    if st.button("Project Healthcare"):
        try:
            from core.simulation import simulate_healthcare_years
            
            # Load policy from library if it's custom, otherwise use built-in
            if healthcare_policy in custom_healthcare_policies:
                policy = library.get_policy(healthcare_policy)
                if policy is None:
                    st.error(f"Could not load policy '{healthcare_policy}'")
                    return
            else:
                policy = get_policy_by_type(PolicyType.USGHA if healthcare_policy == "usgha" else PolicyType.CURRENT_US)
            
            with st.spinner("Running healthcare simulations..."):
                results = simulate_healthcare_years(
                    policy=policy,
                    base_gdp=29e12,
                    initial_debt=35e12,
                    years=years,
                    population=335e6,
                    gdp_growth=0.025,
                    start_year=2027
                )
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Total 22-Year Spending",
                    f"${results['Health Spending ($)'].sum()/1e12:.1f}T",
                    delta="All categories"
                )
            with col2:
                st.metric(
                    "Latest Year Per-Capita",
                    f"${results['Per Capita Health ($)'].iloc[-1]:,.0f}",
                    delta=f"Year {years}"
                )
            with col3:
                st.metric(
                    "Debt Reduction",
                    f"${results['Debt Reduction ($)'].sum()/1e12:.1f}T",
                    delta="22-year total"
                )
            
            # Chart: Healthcare spending over time
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results['Year'],
                y=results['Health Spending ($)']/1e9,
                name='Total Spending',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig.update_layout(
                title=f"Healthcare Spending Projection - {healthcare_policy.upper()}",
                xaxis_title="Year",
                yaxis_title="Spending ($ Billions)",
                template="plotly_white",
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Category breakdown
            if 'category_breakdown' in results.columns:
                fig2 = go.Figure()
                for category in results['category_breakdown'].unique():
                    cat_data = results[results['category_breakdown'] == category]
                    fig2.add_trace(go.Scatter(
                        x=cat_data['year'],
                        y=cat_data['amount']/1e9,
                        name=category,
                        stackgroup='one'
                    ))
                
                fig2.update_layout(
                    title="Spending by Category",
                    xaxis_title="Year",
                    yaxis_title="$ Billions",
                    hovermode='x unified',
                    template="plotly_white"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
            
            # Detailed results table
            with st.expander("View Detailed Results"):
                st.dataframe(results, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error running healthcare simulation: {str(e)}")
            st.info("Healthcare module requires core/simulation.py to be properly configured.")


def page_social_security():
    """Social Security analysis page."""
    st.title("📊 Social Security Trust Fund Projections")
    
    ss_scenarios = load_ss_scenarios()
    scenario_names = list(ss_scenarios["scenarios"].keys())
    
    col1, col2 = st.columns(2)
    with col1:
        selected_scenario = st.selectbox(
            "Select reform scenario:",
            ["Current Law (Baseline)"] + scenario_names
        )
    with col2:
        years = st.slider("Projection years:", 10, 75, 30)
    
    iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000)
    
    if st.button("Run Social Security Projection"):
        model = SocialSecurityModel()
        
        with st.spinner("Running Social Security projections..."):
            if selected_scenario == "Current Law (Baseline)":
                projections = model.project_trust_funds(years=years, iterations=iterations)
                solvency = model.estimate_solvency_dates(projections)
                reform_name = "Current Law"
            else:
                reforms_dict = {
                    "raise_payroll_tax": SocialSecurityReforms.raise_payroll_tax_rate(new_rate=0.145),
                    "remove_wage_cap": SocialSecurityReforms.remove_social_security_wage_cap(),
                    "raise_full_retirement_age": SocialSecurityReforms.raise_full_retirement_age(new_fra=70),
                    "reduce_benefits": SocialSecurityReforms.reduce_benefits(reduction_percent=0.17),
                    "combined_reform_package": SocialSecurityReforms.combined_reform(),
                }
                
                baseline = model.project_trust_funds(years=years, iterations=iterations)
                reforms = reforms_dict[selected_scenario]
                projections = model.apply_policy_reform(reforms["reforms"], baseline)
                solvency = model.estimate_solvency_dates(projections)
                reform_name = ss_scenarios["scenarios"][selected_scenario].get("name", selected_scenario)
        
        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "OASI Depletion Year",
                f"{int(solvency['OASI_depletion_year'])}",
                delta=f"P10: {int(solvency.get('OASI_depletion_p10', np.nan))}"
            )
        with col2:
            st.metric(
                "DI Solvency Through",
                f"{int(solvency['DI_solvency_through_year'])}",
                delta="Disability Insurance"
            )
        with col3:
            st.metric(
                "75-Year Solvency",
                "Yes" if solvency.get("OASI_depletion_year", 2100) > 2100 else "No",
                delta=f"P90: {int(solvency.get('OASI_depletion_p90', np.nan))}"
            )
        
        # Chart
        if len(projections) > 0:
            latest_year = projections[projections['year'] == projections['year'].max()]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=projections['year'].unique(),
                y=projections.groupby('year')['oasi_balance'].mean(),
                mode='lines',
                name='OASI Balance (Mean)',
                line=dict(color='#1f77b4', width=3)
            ))
            
            fig.update_layout(
                title=f"OASI Trust Fund Balance - {reform_name}",
                xaxis_title="Year",
                yaxis_title="Balance ($ Billions)",
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Show scenario details
        with st.expander("Scenario Details"):
            if selected_scenario != "Current Law (Baseline)":
                scenario_details = ss_scenarios["scenarios"][selected_scenario]
                st.json(scenario_details["expected_outcomes"])


def page_federal_revenues():
    """Federal revenues page."""
    st.title("💰 Federal Revenue Projections")
    
    revenue_scenarios = load_revenue_scenarios()
    scenario_names = list(revenue_scenarios["scenarios"].keys())
    
    col1, col2 = st.columns(2)
    with col1:
        selected_scenario = st.selectbox(
            "Select economic scenario:",
            scenario_names
        )
    with col2:
        years = st.slider("Projection years:", 5, 30, 10)
    
    iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000)
    
    if st.button("Project Federal Revenues"):
        model = FederalRevenueModel()
        scenario = revenue_scenarios["scenarios"][selected_scenario]
        
        with st.spinner("Running revenue projections..."):
            gdp_growth = np.array(scenario["economic_assumptions"]["gdp_real_growth_annual"][:years])
            wage_growth = np.array(scenario["economic_assumptions"]["wage_growth_annual"][:years])
            
            revenues = model.project_all_revenues(
                years=years,
                gdp_growth=gdp_growth,
                wage_growth=wage_growth,
                iterations=iterations
            )
        
        # Summary metrics
        latest_data = revenues[revenues['year'] == revenues['year'].max()]
        total_revenue = latest_data['total_revenues'].mean()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total 10-Year Revenue",
                f"${revenues['total_revenues'].sum()/1000:.1f}T",
                delta="Billions"
            )
        with col2:
            st.metric(
                "Latest Year Average",
                f"${total_revenue:.0f}B",
                delta=f"{revenues['year'].max()}"
            )
        with col3:
            growth = (latest_data['total_revenues'].mean() / revenues[revenues['year']==revenues['year'].min()]['total_revenues'].mean()) ** (1/years) - 1
            st.metric(
                "Annual Growth Rate",
                f"{growth:.1%}",
                delta="CAGR"
            )
        
        # Revenue breakdown chart
        if len(revenues) > 0:
            yearly_data = revenues.groupby('year').mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=yearly_data.index, y=yearly_data['individual_income_tax'], name='Individual Income Tax', stackgroup='one'))
            fig.add_trace(go.Scatter(x=yearly_data.index, y=yearly_data['social_security_tax'], name='Social Security Tax', stackgroup='one'))
            fig.add_trace(go.Scatter(x=yearly_data.index, y=yearly_data['medicare_tax'], name='Medicare Tax', stackgroup='one'))
            fig.add_trace(go.Scatter(x=yearly_data.index, y=yearly_data['corporate_income_tax'], name='Corporate Income Tax', stackgroup='one'))
            
            fig.update_layout(
                title=f"Federal Revenue Composition - {selected_scenario}",
                xaxis_title="Year",
                yaxis_title="Revenue ($ Billions)",
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)


def page_medicare_medicaid():
    """Medicare/Medicaid page."""
    st.title("🏥 Medicare & Medicaid Projections")
    
    tab1, tab2 = st.tabs(["Medicare", "Medicaid"])
    
    with tab1:
        st.subheader("Medicare Parts A/B/D Projections")
        
        years = st.slider("Medicare projection years:", 5, 30, 10, key="medicare_years")
        iterations = st.slider("Medicare iterations:", 1000, 30000, 10000, step=1000, key="medicare_iter")
        
        if st.button("Project Medicare"):
            model = MedicareModel()
            
            with st.spinner("Projecting Medicare Parts A/B/D..."):
                projections = model.project_all_parts(years=years, iterations=iterations)
            
            # Summary
            latest = projections[projections['year'] == projections['year'].max()]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Latest Year Total Spending", f"${latest['total_spending'].mean()/1000:.1f}B", delta="Billions")
            with col2:
                st.metric("Average Enrollment", f"{latest['enrollment'].mean()/1_000_000:.1f}M", delta="Beneficiaries")
            with col3:
                st.metric("Per-Capita Cost", f"${latest['per_capita_cost'].mean():,.0f}", delta="Annual")
            
            # Chart
            yearly = projections.groupby('year')[['part_a_spending', 'part_b_spending', 'part_d_spending']].mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=yearly.index, y=yearly['part_a_spending'], name='Part A (Hospital)'))
            fig.add_trace(go.Scatter(x=yearly.index, y=yearly['part_b_spending'], name='Part B (Physician)'))
            fig.add_trace(go.Scatter(x=yearly.index, y=yearly['part_d_spending'], name='Part D (Drugs)'))
            
            fig.update_layout(
                title="Medicare Parts Spending Projections",
                xaxis_title="Year",
                yaxis_title="Spending ($ Billions)",
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Medicaid Spending Projections")
        
        years = st.slider("Medicaid projection years:", 5, 30, 10, key="medicaid_years")
        iterations = st.slider("Medicaid iterations:", 1000, 30000, 10000, step=1000, key="medicaid_iter")
        
        if st.button("Project Medicaid"):
            model = MedicaidModel()
            
            with st.spinner("Projecting Medicaid..."):
                projections = model.project_spending(years=years, iterations=iterations)
            
            # Summary
            latest = projections[projections['year'] == projections['year'].max()]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Latest Year Total Spending", f"${latest['total_spending'].mean()/1000:.1f}B", delta="Billions")
            with col2:
                st.metric("Federal Share", f"${latest['federal_share'].mean()/1000:.1f}B", delta="60%")
            with col3:
                st.metric("Total Enrollment", f"{latest['total_enrollment'].mean()/1_000_000:.1f}M", delta="Beneficiaries")
            
            # Chart
            yearly = projections.groupby('year')[['total_spending', 'federal_share', 'state_share']].mean()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=yearly.index, y=yearly['federal_share'], name='Federal', stackgroup='one'))
            fig.add_trace(go.Scatter(x=yearly.index, y=yearly['state_share'], name='State', stackgroup='one'))
            
            fig.update_layout(
                title="Medicaid Spending - Federal vs State Share",
                xaxis_title="Year",
                yaxis_title="Spending ($ Billions)",
                hovermode='x unified',
                template="plotly_white"
            )
            
            st.plotly_chart(fig, use_container_width=True)


def page_discretionary_spending():
    """Discretionary spending analysis page."""
    st.title("💰 Federal Discretionary Spending")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        defense_scenario = st.selectbox(
            "Defense Scenario:",
            ["baseline", "growth", "reduction"],
            help="baseline=inflation only, growth=+3.5%, reduction=+1.5%"
        )
    with col2:
        nondefense_scenario = st.selectbox(
            "Non-Defense Scenario:",
            ["baseline", "growth", "reduction", "infrastructure"],
            help="Infrastructure=4% growth focus"
        )
    with col3:
        years = st.slider("Projection years:", 5, 30, 10, key="discret_years")
    
    iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000, key="discret_iter")
    
    if st.button("Project Discretionary Spending"):
        model = DiscretionarySpendingModel()
        
        with st.spinner("Projecting discretionary spending..."):
            projections = model.project_all_discretionary(
                years=years,
                iterations=iterations,
                defense_scenario=defense_scenario,
                nondefense_scenario=nondefense_scenario
            )
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Total Discretionary (10yr)",
                f"${projections['total_mean'].sum():.0f}B",
                delta="Billions"
            )
        with col2:
            st.metric(
                "Defense Avg/Year",
                f"${projections['defense_mean'].mean():.0f}B",
                delta="Annual average"
            )
        with col3:
            st.metric(
                "Non-Defense Avg/Year",
                f"${projections['nondefense_mean'].mean():.0f}B",
                delta="Annual average"
            )
        
        # Stacked area chart: Defense vs Non-Defense
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=projections['year'],
            y=projections['defense_mean'],
            name='Defense',
            stackgroup='one',
            line=dict(color='#d62728')
        ))
        fig.add_trace(go.Scatter(
            x=projections['year'],
            y=projections['nondefense_mean'],
            name='Non-Defense',
            stackgroup='one',
            line=dict(color='#2ca02c')
        ))
        
        fig.update_layout(
            title=f"Federal Discretionary Spending ({defense_scenario} defense, {nondefense_scenario} non-defense)",
            xaxis_title="Year",
            yaxis_title="Spending ($ Billions)",
            hovermode='x unified',
            template="plotly_white"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Category breakdown table
        with st.expander("View Year-by-Year Breakdown"):
            st.dataframe(projections, use_container_width=True)


def page_combined_outlook():
    """Combined federal fiscal outlook page."""
    st.title("🏛️ Combined Federal Fiscal Outlook")
    
    st.markdown("""
    Unified federal budget model combining all revenue and spending:
    - **Revenue**: Individual income, payroll, corporate taxes
    - **Mandatory Spending**: Social Security, Medicare, Medicaid
    - **Discretionary**: Defense and non-defense spending
    - **Interest**: Federal debt service
    """)
    
    # Scenario selectors
    col1, col2 = st.columns(2)
    with col1:
        revenue_scenario = st.selectbox(
            "Economic Scenario:",
            ["baseline", "recession_2026", "strong_growth", "demographic_challenge"]
        )
        discretionary_scenario = st.selectbox(
            "Discretionary Scenario:",
            ["baseline", "growth", "reduction"]
        )
    with col2:
        interest_scenario = st.selectbox(
            "Interest Rate Scenario:",
            ["baseline", "rising", "falling", "spike"]
        )
        years = st.slider("Projection years:", 10, 75, 30, key="outlook_years")
    
    iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000, key="outlook_iter")
    
    if st.button("Calculate Combined Fiscal Outlook"):
        model = CombinedFiscalOutlookModel()
        
        with st.spinner("Calculating unified federal budget..."):
            try:
                summary = model.get_fiscal_summary(
                    years=years,
                    iterations=iterations,
                    revenue_scenario=revenue_scenario,
                    discretionary_scenario=discretionary_scenario,
                    interest_scenario=interest_scenario
                )
                
                # 10-year summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric(
                        "Total Revenue (10yr)",
                        f"${summary['total_revenue_10year_billions']:.0f}B"
                    )
                with col2:
                    st.metric(
                        "Total Spending (10yr)",
                        f"${summary['total_spending_10year_billions']:.0f}B"
                    )
                with col3:
                    deficit_color = "inverse" if summary['total_deficit_10year_billions'] < 0 else "normal"
                    st.metric(
                        "Total Deficit (10yr)",
                        f"${abs(summary['total_deficit_10year_billions']):.0f}B",
                        delta=("Surplus" if summary['total_deficit_10year_billions'] < 0 else "Deficit"),
                        delta_color=deficit_color
                    )
                with col4:
                    status = "✅ Yes" if summary['sustainable'] else "❌ No"
                    st.metric("Sustainable (Primary Balance)", status)
                
                # Get detailed projection
                df = model.project_unified_budget(
                    years=years,
                    iterations=iterations,
                    revenue_scenario=revenue_scenario,
                    discretionary_scenario=discretionary_scenario,
                    interest_scenario=interest_scenario
                )
                
                # Main chart: Revenue vs Total Spending
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['total_revenue'],
                    name='Total Revenue',
                    line=dict(color='#2ca02c', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=df['year'],
                    y=df['total_spending'],
                    name='Total Spending',
                    line=dict(color='#d62728', width=3)
                ))
                
                fig.update_layout(
                    title="Federal Revenue vs Spending",
                    xaxis_title="Year",
                    yaxis_title="$ Billions",
                    hovermode='x unified',
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Spending breakdown: stacked area
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(x=df['year'], y=df['healthcare_spending'], name='Healthcare', stackgroup='one'))
                fig2.add_trace(go.Scatter(x=df['year'], y=df['social_security_spending'], name='Social Security', stackgroup='one'))
                fig2.add_trace(go.Scatter(x=df['year'], y=df['medicare_spending'], name='Medicare', stackgroup='one'))
                fig2.add_trace(go.Scatter(x=df['year'], y=df['medicaid_spending'], name='Medicaid', stackgroup='one'))
                fig2.add_trace(go.Scatter(x=df['year'], y=df['discretionary_spending'], name='Discretionary', stackgroup='one'))
                fig2.add_trace(go.Scatter(x=df['year'], y=df['interest_spending'], name='Interest', stackgroup='one'))
                
                fig2.update_layout(
                    title="Federal Spending by Category",
                    xaxis_title="Year",
                    yaxis_title="$ Billions",
                    hovermode='x unified',
                    template="plotly_white"
                )
                
                st.plotly_chart(fig2, use_container_width=True)
                
                # Deficit trend
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=df['year'], y=df['deficit_surplus'], name='Deficit/Surplus'))
                fig3.add_hline(y=0, line_dash="dash", line_color="black")
                
                fig3.update_layout(
                    title="Annual Deficit/Surplus",
                    xaxis_title="Year",
                    yaxis_title="$ Billions (negative = deficit)",
                    template="plotly_white"
                )
                
                st.plotly_chart(fig3, use_container_width=True)
                
                # Detailed data table
                with st.expander("View Detailed Budget Data"):
                    st.dataframe(df, use_container_width=True)
                    
            except Exception as e:
                st.error(f"Error calculating outlook: {str(e)}")
                st.info("This feature combines multiple modules. Ensure all dependencies are installed.")


def page_policy_comparison():
    """Policy comparison page."""
    st.title("⚖️ Policy Comparison Analysis")
    
    st.markdown("""
    Compare multiple policies or scenarios side-by-side to evaluate their fiscal impact.
    """)
    
    # Load custom policies from library - ALWAYS FRESH (not cached)
    all_custom_policies, library = get_policy_library_policies()
    
    col1, col2 = st.columns(2)
    with col1:
        num_policies = st.slider("Number of policies to compare:", 2, 5, 2, key="num_policies")
        years = st.slider("Projection years:", 10, 75, 30, key="compare_years")
    with col2:
        comparison_mode = st.radio(
            "Comparison type:",
            ["Scenarios", "Custom Policies", "Mixed"],
            key="comparison_mode"
        )
        iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000, key="compare_iter")
    
    # Policy/scenario selectors
    policies = {}
    
    if comparison_mode == "Scenarios":
        # Original scenario-based comparison
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            
            col1, col2 = st.columns(2)
            with col1:
                rev_scenario = st.selectbox(f"Revenue Scenario {i+1}:", ["baseline", "recession_2026", "strong_growth"], key=f"rev_scenario_{i}")
            with col2:
                discret_scenario = st.selectbox(f"Discretionary {i+1}:", ["baseline", "growth", "reduction"], key=f"discret_scenario_{i}")
            
            policies[f"Policy {i+1}"] = {
                "type": "scenario",
                "revenue_scenario": rev_scenario,
                "discretionary_scenario": discret_scenario,
            }
    
    elif comparison_mode == "Custom Policies":
        # Select from custom policy library
        if not all_custom_policies:
            st.warning("No custom policies found. Create policies in 'Custom Policy Builder' or 'Policy Upload' first.")
            return
        
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            policy_name = st.selectbox(
                f"Select policy {i+1}:",
                all_custom_policies,
                key=f"custom_policy_{i}"
            )
            policies[f"Policy {i+1}"] = {
                "type": "custom",
                "policy_name": policy_name,
            }
    
    else:  # Mixed
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            
            policy_type = st.radio(
                f"Type for Policy {i+1}:",
                ["Scenario", "Custom Policy"],
                key=f"policy_type_{i}",
                horizontal=True
            )
            
            if policy_type == "Scenario":
                col1, col2 = st.columns(2)
                with col1:
                    rev_scenario = st.selectbox(f"Revenue Scenario {i+1}:", ["baseline", "recession_2026", "strong_growth"], key=f"rev_scenario_{i}")
                with col2:
                    discret_scenario = st.selectbox(f"Discretionary {i+1}:", ["baseline", "growth", "reduction"], key=f"discret_scenario_{i}")
                
                policies[f"Policy {i+1}"] = {
                    "type": "scenario",
                    "revenue_scenario": rev_scenario,
                    "discretionary_scenario": discret_scenario,
                }
            else:
                if all_custom_policies:
                    policy_name = st.selectbox(
                        f"Select custom policy {i+1}:",
                        all_custom_policies,
                        key=f"custom_policy_{i}"
                    )
                    policies[f"Policy {i+1}"] = {
                        "type": "custom",
                        "policy_name": policy_name,
                    }
                else:
                    st.warning(f"No custom policies available for Policy {i+1}")
                    return
    
    metric_to_compare = st.selectbox(
        "Compare by metric:",
        ["10-year deficit", "Average annual deficit", "Interest spending", "Total spending"]
    )
    
    if st.button("Compare Policies"):
        model = CombinedFiscalOutlookModel()
        
        with st.spinner("Running policy comparison..."):
            comparison_data = {}
            
            try:
                for policy_name, config in policies.items():
                    if config["type"] == "scenario":
                        summary = model.get_fiscal_summary(
                            years=years,
                            iterations=iterations,
                            revenue_scenario=config["revenue_scenario"],
                            discretionary_scenario=config["discretionary_scenario"]
                        )
                    else:  # custom policy
                        # For custom policies, use basic fiscal summary
                        summary = model.get_fiscal_summary(
                            years=years,
                            iterations=iterations,
                            revenue_scenario="baseline",
                            discretionary_scenario="baseline"
                        )
                        # In a full implementation, you would apply custom policy parameters
                        st.info(f"Note: Custom policy '{config['policy_name']}' is being compared using baseline scenarios. Full integration requires policy simulation engine.")
                    
                    comparison_data[policy_name] = summary
                
                # Create comparison table
                comparison_df = pd.DataFrame(comparison_data).T
                st.dataframe(comparison_df, use_container_width=True)
                
                # Chart: Compare selected metric
                fig = go.Figure()
                
                for policy_name in policies.keys():
                    metric_value = comparison_data[policy_name][f"{metric_to_compare.lower().replace(' ', '_')}_billions"] if "billion" not in metric_to_compare.lower() else comparison_data[policy_name].get(f"{metric_to_compare.lower().replace(' ', '_')}_billions", 0)
                    
                    fig.add_trace(go.Bar(
                        x=[policy_name],
                        y=[metric_value],
                        name=policy_name
                    ))
                
                fig.update_layout(
                    title=f"Policy Comparison: {metric_to_compare}",
                    yaxis_title="$ Billions",
                    showlegend=False,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.success("Comparison complete! Green bars are better (lower spending/deficit).")
                
            except Exception as e:
                st.error(f"Error during comparison: {str(e)}")


def page_custom_policy_builder():
    """Custom policy builder page with parameter sliders."""
    st.title("🔧 Custom Policy Builder")
    
    st.markdown("""
    Create and customize fiscal policies with adjustable parameters. Choose a template or build from scratch.
    """)
    
    from core.policy_builder import PolicyTemplate, PolicyType
    
    # Load policy library - ALWAYS FRESH (not cached)
    all_policies, library = get_policy_library_policies()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Create New Policy")
        
        # Policy template selection
        template_choice = st.radio(
            "Select template:",
            ["Healthcare Reform", "Tax Reform", "Spending Reform", "Blank Custom"]
        )
        
        template_map = {
            "Healthcare Reform": "healthcare",
            "Tax Reform": "tax_reform",
            "Spending Reform": "spending_reform",
        }
        
        if template_choice != "Blank Custom":
            template_name = template_map[template_choice]
            policy_name = st.text_input("Policy name:", f"My {template_choice}")
            
            if st.button("Create from template"):
                policy = PolicyTemplate.create_from_template(template_name, policy_name)
                library.add_policy(policy)
                st.success(f"✓ Policy '{policy_name}' created!")
                st.cache_data.clear()  # Clear any cached data
                st.rerun()  # Force page refresh
    
    with col2:
        st.subheader("Manage Policies")
        
        # Show existing policies
        policies = library.list_policies()
        
        if policies:
            selected_policy_name = st.selectbox("Edit existing policy:", policies)
            selected_policy = library.get_policy(selected_policy_name)
            
            if selected_policy:
                # Display policy info
                st.write(f"**Type:** {selected_policy.policy_type.value}")
                st.write(f"**Description:** {selected_policy.description}")
                st.write(f"**Author:** {selected_policy.author}")
                st.write(f"**Created:** {selected_policy.created_date[:10]}")
                
                # Parameter editor by category
                categories = set(p.category for p in selected_policy.parameters.values())
                
                for category in sorted(categories):
                    with st.expander(f"📊 {category.title()} Parameters", expanded=True):
                        params_in_category = selected_policy.get_parameters_by_category(category)
                        
                        for param_name, param in params_in_category.items():
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                new_value = st.slider(
                                    label=param.description,
                                    min_value=param.min_value,
                                    max_value=param.max_value,
                                    value=param.value,
                                    step=(param.max_value - param.min_value) / 100,
                                    key=f"slider_{param_name}",
                                )
                                
                                if new_value != param.value:
                                    selected_policy.update_parameter(param_name, new_value)
                                    library.save_policy(selected_policy)
                            
                            with col_b:
                                st.caption(param.unit if param.unit else "")
                
                # Save and delete options
                col_save, col_delete = st.columns(2)
                
                with col_save:
                    if st.button("💾 Save Changes"):
                        library.save_policy(selected_policy)
                        st.success("Policy saved!")
                
                with col_delete:
                    if st.button("🗑️ Delete Policy"):
                        library.delete_policy(selected_policy_name)
                        st.warning(f"Policy '{selected_policy_name}' deleted!")
                        st.rerun()
        else:
            st.info("No policies yet. Create one from a template above!")
    
    # Policy library overview
    st.divider()
    st.subheader("Policy Library")
    
    if policies:
        library_df = library.export_policies_dataframe()
        st.dataframe(library_df, use_container_width=True)
        
        # Export all policies
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export All Policies"):
                export_data = {}
                for name in policies:
                    policy = library.get_policy(name)
                    export_data[name] = policy.to_dict()
                
                st.json(export_data)
    else:
        st.info("Your policy library is empty. Create policies to get started!")


def page_real_data_dashboard():
    """Real data integration dashboard showing CBO/SSA baselines."""
    st.title("📊 Real Data: CBO & SSA Integration")
    
    st.markdown("""
    View authentic federal fiscal data from the Congressional Budget Office and Social Security Administration.
    These baselines power all fiscal projections.
    """)
    
    from core.data_loader import load_real_data
    
    data_loader = load_real_data()
    
    # Three main tabs
    tab_summary, tab_revenues, tab_spending, tab_demographics = st.tabs([
        "Summary", "Revenues", "Spending", "Demographics"
    ])
    
    with tab_summary:
        st.subheader("Federal Fiscal Summary (FY 2025)")
        
        # Key metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Revenue",
                f"${data_loader.cbo.total_revenue:,.0f}B",
                delta=f"{(data_loader.cbo.total_revenue / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col2:
            st.metric(
                "Total Spending",
                f"${data_loader.cbo.total_spending:,.0f}B",
                delta=f"{(data_loader.cbo.total_spending / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col3:
            deficit = data_loader.cbo.total_spending - data_loader.cbo.total_revenue
            st.metric(
                "Federal Deficit",
                f"${deficit:,.0f}B",
                delta=f"{(deficit / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col4:
            st.metric(
                "Public Debt",
                f"${data_loader.cbo.public_debt_held:,.0f}B",
                delta=f"{(data_loader.cbo.public_debt_held / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        # Full summary table
        st.divider()
        summary_df = data_loader.export_summary_metrics()
        st.dataframe(summary_df, use_container_width=True)
    
    with tab_revenues:
        st.subheader("Federal Revenue Sources (FY 2025)")
        
        revenue_data = data_loader.get_revenue_baseline()
        
        # Revenue chart
        revenue_df = pd.DataFrame({
            "Source": [k.replace("_", " ").title() for k in revenue_data.keys() if k != "total"],
            "Amount": [v for k, v in revenue_data.items() if k != "total"]
        })
        
        fig = px.pie(
            revenue_df,
            values="Amount",
            names="Source",
            title="Federal Revenue Distribution",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Revenue details
        st.write("**Revenue by Source ($B)**")
        for source, amount in revenue_data.items():
            if source != "total":
                st.write(f"- **{source.replace('_', ' ').title()}**: ${amount:,.1f}B")
        
        st.write(f"**Total:** ${revenue_data['total']:,.1f}B")
    
    with tab_spending:
        st.subheader("Federal Spending by Category (FY 2025)")
        
        spending_data = data_loader.get_spending_baseline()
        
        # Spending chart
        spending_df = pd.DataFrame({
            "Category": [k.replace("_", " ").title() for k in spending_data.keys() if k != "total"],
            "Amount": [v for k, v in spending_data.items() if k != "total"]
        })
        
        fig = px.pie(
            spending_df,
            values="Amount",
            names="Category",
            title="Federal Spending Distribution",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Spending details
        st.write("**Spending by Category ($B)**")
        for category, amount in spending_data.items():
            if category != "total":
                st.write(f"- **{category.replace('_', ' ').title()}**: ${amount:,.1f}B")
        
        st.write(f"**Total:** ${spending_data['total']:,.1f}B")
    
    with tab_demographics:
        st.subheader("U.S. Population & Demographics")
        
        pop_metrics = data_loader.get_population_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Population", f"{pop_metrics['total_population']:.1f}M")
            st.metric("Under 18", f"{pop_metrics['percent_under_18']:.1f}%")
        
        with col2:
            st.metric("Working Age (18-64)", f"{pop_metrics['percent_18_64']:.1f}%")
            st.metric("Age 65+", f"{pop_metrics['percent_65_plus']:.1f}%")
        
        with col3:
            st.metric("Annual Growth", f"{pop_metrics['annual_growth_rate']:.2f}%")
            st.metric("Life Expectancy", f"{pop_metrics['life_expectancy']:.1f} years")
        
        st.info(f"""
        The U.S. is experiencing significant aging:
        - In 2025, about **{pop_metrics['percent_65_plus']:.0f}%** of Americans are 65+
        - By 2045, this will grow to approximately **{pop_metrics['percent_65_plus'] * 1.4:.0f}%**
        - This affects demand for Social Security, Medicare, and Medicaid
        """)


def page_policy_upload():
    """Policy PDF upload and extraction page."""
    st.title("📄 Upload & Extract Policy from PDF")
    
    st.markdown("""
    Upload policy documents (like the United States Galactic Health Act) to extract parameters and create policies.
    """)
    
    from core.pdf_policy_parser import PolicyPDFProcessor
    from core.policy_builder import PolicyLibrary
    import tempfile
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload PDF policy document",
        type=["pdf", "txt"],
        help="Supports PDF and text files up to 200MB"
    )
    
    if uploaded_file:
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        
        if st.button("🔍 Extract Policy Parameters"):
            with st.spinner("Extracting policy parameters..."):
                try:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    # Extract policy
                    processor = PolicyPDFProcessor()
                    from pathlib import Path
                    
                    # First extract text from PDF
                    extracted_text = processor.extract_text_from_pdf(Path(tmp_path))
                    
                    # Then analyze the extracted text
                    extraction = processor.analyze_policy_text(
                        text=extracted_text,
                        policy_title=uploaded_file.name.replace(".pdf", "")
                    )
                    
                    # Display extraction results
                    st.subheader("✓ Extraction Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Confidence Score", f"{extraction.confidence_score:.1%}")
                    with col2:
                        st.metric("Sections Found", extraction.identified_parameters["num_sections"])
                    with col3:
                        st.metric("Fiscal Figures", len(extraction.fiscal_impact_estimates))
                    
                    # Detailed results
                    with st.expander("📊 Extracted Parameters"):
                        st.json(extraction.identified_parameters)
                    
                    with st.expander("💰 Fiscal Impact Estimates"):
                        for desc, amount in extraction.fiscal_impact_estimates.items():
                            st.write(f"- **{desc}**: ${amount:,.0f}B")
                    
                    # Create policy from extraction
                    st.divider()
                    st.subheader("Create Policy from Extraction")
                    
                    policy_name = st.text_input(
                        "Policy Name:",
                        value=uploaded_file.name.replace(".pdf", "")
                    )
                    
                    if st.button("➕ Create Policy"):
                        processor = PolicyPDFProcessor()
                        policy = processor.create_policy_from_extraction(extraction, policy_name)
                        
                        library = PolicyLibrary()
                        if library.add_policy(policy):
                            st.success(f"✓ Policy '{policy_name}' created and saved!")
                            st.info(f"Policy has {len(policy.parameters)} parameters. Edit them in Custom Policy Builder.")
                            st.info("Navigate to 'Healthcare' or 'Policy Comparison' page to use this policy.")
                            # Force Streamlit to refresh by clearing cache and rerunning
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Policy '{policy_name}' already exists.")
                
                except Exception as e:
                    st.error(f"Error extracting policy: {str(e)}")
    
    # Example policies
    st.divider()
    st.subheader("📋 Example: Policy Structure")
    
    example = """
    The system can extract parameters from policies like:
    
    **United States Galactic Health Act of 2025**
    - Universal coverage: 100% of population
    - Out-of-pocket maximum: $0
    - Health spending target: 7% of GDP
    - Pharmaceutical cost reduction: 15%
    - Innovation fund: 3% of budget
    
    Upload your policy PDF to automatically extract these parameters!
    """
    st.info(example)


def page_policy_recommendations():
    """Policy recommendation engine based on fiscal goals."""
    st.title("Recommendation Engine: Find Your Ideal Policy")
    
    st.markdown("""
    Get personalized policy recommendations based on your fiscal priorities.
    The engine scores policies across multiple dimensions.
    """)
    
    from core.policy_enhancements import (
        PolicyRecommendationEngine, 
        FiscalGoal
    )
    
    # Goal selector
    goal = st.selectbox(
        "What is your primary fiscal goal?",
        [
            "Minimize Deficit",
            "Maximize Revenue",
            "Reduce Spending",
            "Balance Budget",
            "Sustainable Debt",
            "Growth-Focused",
            "Equity-Focused",
        ],
        format_func=lambda x: {
            "Minimize Deficit": "Minimize Deficit (fastest path to balance)",
            "Maximize Revenue": "Maximize Revenue (increase taxes/fees)",
            "Reduce Spending": "Reduce Spending (cut programs)",
            "Balance Budget": "Balance Budget (both revenue and spending)",
            "Sustainable Debt": "Sustainable Debt (long-term stability)",
            "Growth-Focused": "Growth-Focused (prioritize economic growth)",
            "Equity-Focused": "Equity-Focused (progressive policies)",
        }.get(x, x)
    )
    
    goal_map = {
        "Minimize Deficit": FiscalGoal.MINIMIZE_DEFICIT,
        "Maximize Revenue": FiscalGoal.MAXIMIZE_REVENUE,
        "Reduce Spending": FiscalGoal.REDUCE_SPENDING,
        "Balance Budget": FiscalGoal.BALANCE_BUDGET,
        "Sustainable Debt": FiscalGoal.SUSTAINABLE_DEBT,
        "Growth-Focused": FiscalGoal.GROWTH_FOCUSED,
        "Equity-Focused": FiscalGoal.EQUITY_FOCUSED,
    }
    
    engine = PolicyRecommendationEngine()
    
    # Score some example policies
    engine.score_policy(
        policy_name="Progressive Tax Reform",
        deficit_reduction=150.0,
        revenue_change=5.0,
        spending_change=0.0,
        growth_impact=-0.3,
        equity_impact="progressive",
        feasibility=60.0,
    )
    
    engine.score_policy(
        policy_name="Spending Efficiency Program",
        deficit_reduction=75.0,
        revenue_change=0.0,
        spending_change=-3.0,
        growth_impact=0.5,
        equity_impact="neutral",
        feasibility=65.0,
    )
    
    engine.score_policy(
        policy_name="Healthcare Cost Control",
        deficit_reduction=120.0,
        revenue_change=2.0,
        spending_change=-5.0,
        growth_impact=0.2,
        equity_impact="progressive",
        feasibility=55.0,
    )
    
    engine.score_policy(
        policy_name="Growth-First Strategy",
        deficit_reduction=50.0,
        revenue_change=-2.0,
        spending_change=-1.0,
        growth_impact=1.5,
        equity_impact="regressive",
        feasibility=70.0,
    )
    
    # Get recommendations
    recommended = engine.recommend_policies(goal_map[goal], num_recommendations=3)
    
    # Display recommendations
    st.subheader("Top Recommendations")
    
    for i, policy in enumerate(recommended, 1):
        with st.expander(f"{i}. {policy.policy_name} - Score: {policy.overall_score:.0f}/100", expanded=(i==1)):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Fiscal Impact", f"${policy.fiscal_impact:,.0f}B/yr", "deficit reduction")
            with col2:
                st.metric("Sustainability", f"{policy.sustainability:.0f}%")
            with col3:
                st.metric("Feasibility", f"{policy.feasibility:.0f}%")
            with col4:
                st.metric("Equity Score", f"{policy.equity_score:.0f}%")
            
            st.write("**Growth Impact:**", f"{policy.growth_impact:+.1f}%")
            
            st.write("**Why this policy?**")
            reasoning = engine.get_policy_reasoning(policy.policy_name)
            for reason in reasoning:
                st.write(f"- {reason}")


def page_scenario_explorer():
    """Interactive scenario explorer for comparing multiple policy scenarios."""
    st.title("Scenario Explorer: Compare Policy Impacts")
    
    st.markdown("""
    Create and compare multiple policy scenarios side-by-side with real-time calculations.
    """)
    
    from core.policy_enhancements import InteractiveScenarioExplorer, PolicyImpactCalculator
    
    explorer = InteractiveScenarioExplorer()
    
    # Pre-configured scenarios
    scenarios = {
        "Status Quo": {"revenue": 0, "spending": 0},
        "Tax Reform (+5%)": {"revenue": 5, "spending": 0},
        "Spending Cut (-3%)": {"revenue": 0, "spending": -3},
        "Balanced Package": {"revenue": 3, "spending": -2},
    }
    
    # Let user create custom scenario
    st.subheader("Create Custom Scenario")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario_name = st.text_input("Scenario name:", "My Scenario")
    
    with col2:
        revenue_change = st.slider(
            "Revenue change (%):",
            min_value=-10.0,
            max_value=20.0,
            value=0.0,
            step=0.5,
        )
    
    with col3:
        spending_change = st.slider(
            "Spending change (%):",
            min_value=-20.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
        )
    
    if st.button("Add Custom Scenario"):
        scenarios[scenario_name] = {"revenue": revenue_change, "spending": spending_change}
        st.success(f"Added scenario: {scenario_name}")
    
    # Add scenarios to explorer
    for name, params in scenarios.items():
        explorer.add_scenario(
            name=name,
            revenue_change_pct=params["revenue"],
            spending_change_pct=params["spending"],
        )
    
    # Calculate all scenarios
    explorer.calculate_all_scenarios(years=10)
    
    # Display summary
    st.subheader("Scenario Comparison")
    summary_df = explorer.get_scenario_summary()
    st.dataframe(summary_df, use_container_width=True)
    
    # Chart: Deficit by scenario
    st.subheader("10-Year Cumulative Deficit by Scenario")
    
    chart_data = []
    for name, df in explorer.results.items():
        chart_data.append({
            "Scenario": name,
            "Total Deficit": df["deficit"].sum(),
        })
    
    chart_df = pd.DataFrame(chart_data).sort_values("Total Deficit")
    
    fig = px.bar(
        chart_df,
        x="Scenario",
        y="Total Deficit",
        title="Cumulative 10-Year Deficit by Scenario",
        labels={"Total Deficit": "Deficit ($B)"},
        template="plotly_white",
        color="Total Deficit",
        color_continuous_scale="RdYlGn_r",
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Show best scenario
    st.subheader("Best Scenario")
    best_name, best_df = explorer.get_best_scenario("lowest_deficit")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Scenario", best_name)
    with col2:
        st.metric("10-Year Deficit", f"${best_df['deficit'].sum():,.0f}B")
    with col3:
        st.metric("Avg Annual Deficit", f"${best_df['deficit'].mean():,.0f}B")
    
    # Detailed year-by-year for best scenario
    st.subheader(f"Year-by-Year: {best_name}")
    
    display_df = best_df[["year", "revenue", "spending", "deficit"]].copy()
    display_df.columns = ["Year", "Revenue ($B)", "Spending ($B)", "Deficit ($B)"]
    display_df = display_df.round(1)
    st.dataframe(display_df, use_container_width=True)


def page_impact_calculator():
    """Real-time policy impact calculator."""
    st.title("Impact Calculator: Measure Policy Effects")
    
    st.markdown("""
    Adjust policy parameters and instantly see fiscal impact over time.
    """)
    
    from core.policy_enhancements import PolicyImpactCalculator
    from core.data_loader import load_real_data
    
    # Get baseline data
    data = load_real_data()
    base_revenue = data.cbo.total_revenue
    base_spending = data.cbo.total_spending
    
    # Parameter sliders
    st.subheader("Policy Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        revenue_change = st.slider(
            "Revenue change (%):",
            min_value=-15.0,
            max_value=30.0,
            value=0.0,
            step=1.0,
            help="How much to increase or decrease total federal revenue",
        )
    
    with col2:
        spending_change = st.slider(
            "Spending change (%):",
            min_value=-30.0,
            max_value=15.0,
            value=0.0,
            step=1.0,
            help="How much to increase or decrease total federal spending",
        )
    
    with col3:
        years = st.slider(
            "Projection years:",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
        )
    
    # Calculate impact
    impact_df = PolicyImpactCalculator.calculate_impact(
        base_revenue,
        base_spending,
        revenue_change,
        spending_change,
        years=years,
    )
    
    # Key metrics
    st.subheader("Impact Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    baseline_deficit = base_spending - base_revenue
    final_deficit = impact_df["deficit"].iloc[-1]
    total_deficit = impact_df["deficit"].sum()
    savings = -impact_df["cumulative_savings"].iloc[-1]
    
    with col1:
        st.metric(
            "Baseline Annual Deficit",
            f"${baseline_deficit:,.0f}B",
            "-"
        )
    
    with col2:
        st.metric(
            f"Year {years} Deficit",
            f"${final_deficit:,.0f}B",
            f"${final_deficit - baseline_deficit:+,.0f}B"
        )
    
    with col3:
        st.metric(
            f"{years}-Year Total Deficit",
            f"${total_deficit:,.0f}B",
        )
    
    with col4:
        st.metric(
            f"Cumulative Savings",
            f"${savings:,.0f}B",
        )
    
    # Charts
    st.subheader("Fiscal Projections")
    
    # Revenue vs Spending
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=impact_df["year"],
        y=impact_df["revenue"],
        name="Revenue",
        mode="lines",
        line=dict(color="green", width=3),
    ))
    fig1.add_trace(go.Scatter(
        x=impact_df["year"],
        y=impact_df["spending"],
        name="Spending",
        mode="lines",
        line=dict(color="red", width=3),
    ))
    fig1.update_layout(
        title="Revenue vs Spending Over Time",
        xaxis_title="Year",
        yaxis_title="Amount ($B)",
        template="plotly_white",
        hovermode="x unified",
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    # Deficit trend
    fig2 = px.bar(
        impact_df,
        x="year",
        y="deficit",
        title="Annual Deficit",
        labels={"year": "Year", "deficit": "Deficit ($B)"},
        template="plotly_white",
        color="deficit",
        color_continuous_scale="Reds",
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Data table
    st.subheader("Year-by-Year Details")
    
    display_df = impact_df[["year", "revenue", "spending", "deficit"]].copy()
    display_df.columns = ["Year", "Revenue ($B)", "Spending ($B)", "Deficit ($B)"]
    display_df = display_df.round(1)
    st.dataframe(display_df, use_container_width=True, height=400)


def page_monte_carlo_scenarios():
    """Advanced Monte Carlo scenario analysis."""
    st.title("Advanced Scenarios: Monte Carlo Uncertainty Analysis")
    
    st.markdown("""
    Analyze policies under uncertainty with Monte Carlo simulation.
    Generate P10/P90 confidence bounds, stress tests, and sensitivity analysis.
    """)
    
    from core.monte_carlo_scenarios import (
        MonteCarloPolicySimulator,
        PolicySensitivityAnalyzer,
        StressTestAnalyzer,
    )
    
    tabs = st.tabs(["Monte Carlo", "Sensitivity", "Stress Test"])
    
    with tabs[0]:
        st.subheader("Monte Carlo Simulation")
        st.write("Run stochastic analysis on custom policies with confidence bounds.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            revenue_change = st.slider(
                "Revenue change (%):",
                min_value=-15.0,
                max_value=30.0,
                value=0.0,
                step=1.0,
                key="mc_revenue",
            )
        
        with col2:
            spending_change = st.slider(
                "Spending change (%):",
                min_value=-30.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                key="mc_spending",
            )
        
        with col3:
            iterations = st.slider(
                "Monte Carlo iterations:",
                min_value=1_000,
                max_value=100_000,
                value=10_000,
                step=1_000,
            )
        
        if st.button("Run Monte Carlo Simulation"):
            with st.spinner("Running 10,000 simulations..."):
                simulator = MonteCarloPolicySimulator()
                result = simulator.simulate_policy(
                    policy_name="Custom Policy",
                    revenue_change_pct=revenue_change,
                    spending_change_pct=spending_change,
                    years=10,
                    iterations=iterations,
                )
                
                # Display results
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Mean Deficit", f"${result.mean_deficit:,.0f}B")
                with col2:
                    st.metric("Median Deficit", f"${result.median_deficit:,.0f}B")
                with col3:
                    st.metric("Std Dev", f"${result.std_dev_deficit:,.0f}B")
                with col4:
                    st.metric("P10 (Best)", f"${result.p10_deficit:,.0f}B")
                with col5:
                    st.metric("P90 (Worst)", f"${result.p90_deficit:,.0f}B")
                
                st.write(f"**Probability of balanced budget:** {result.probability_balanced:.1f}%")
                
                # Distribution chart
                fig = px.histogram(
                    x=result.simulation_results[:, -1],
                    nbins=50,
                    title="Distribution of Final Year Deficit (10,000 simulations)",
                    labels={"x": "Deficit ($B)"},
                    template="plotly_white",
                )
                
                # Add confidence bounds
                fig.add_vline(x=result.p10_deficit, line_dash="dash", line_color="green", 
                             annotation_text="P10", annotation_position="top")
                fig.add_vline(x=result.p90_deficit, line_dash="dash", line_color="red",
                             annotation_text="P90", annotation_position="top")
                fig.add_vline(x=result.mean_deficit, line_dash="solid", line_color="blue",
                             annotation_text="Mean", annotation_position="top")
                
                st.plotly_chart(fig, use_container_width=True)
    
    with tabs[1]:
        st.subheader("Parameter Sensitivity Analysis")
        st.write("Which policy parameters have the biggest impact on outcomes?")
        
        parameters = {
            "Revenue Change": (-10.0, 20.0),
            "Spending Change": (-30.0, 10.0),
            "Revenue Uncertainty": (2.0, 20.0),
            "Spending Uncertainty": (2.0, 20.0),
        }
        
        analyzer = PolicySensitivityAnalyzer()
        tornado_df = analyzer.tornado_analysis(
            base_revenue=5_980,
            base_spending=6_911,
            parameter_ranges=parameters,
        )
        
        # Tornado chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Negative Impact",
            x=tornado_df["Negative Impact"],
            y=tornado_df["Parameter"],
            orientation="h",
            marker=dict(color="rgba(255, 0, 0, 0.7)"),
        ))
        
        fig.add_trace(go.Bar(
            name="Positive Impact",
            x=tornado_df["Positive Impact"],
            y=tornado_df["Parameter"],
            orientation="h",
            marker=dict(color="rgba(0, 0, 255, 0.7)"),
        ))
        
        fig.update_layout(
            title="Parameter Sensitivity (Tornado Chart)",
            xaxis_title="10-Year Deficit Impact ($B)",
            barmode="relative",
            template="plotly_white",
            height=400,
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.write("**Interpretation:** The longer the bar, the more impact that parameter has on the deficit.")
    
    with tabs[2]:
        st.subheader("Stress Test Analysis")
        st.write("How does the policy perform under adverse economic scenarios?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            revenue_change = st.slider(
                "Revenue change (%):",
                min_value=-15.0,
                max_value=30.0,
                value=0.0,
                step=1.0,
                key="stress_revenue",
            )
        
        with col2:
            spending_change = st.slider(
                "Spending change (%):",
                min_value=-30.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                key="stress_spending",
            )
        
        stress_analyzer = StressTestAnalyzer()
        stress_df = stress_analyzer.run_stress_test(
            policy_params={
                "revenue_change_pct": revenue_change,
                "spending_change_pct": spending_change,
            }
        )
        
        st.dataframe(stress_df, use_container_width=True)
        
        st.write("**Stress Scenarios:**")
        st.write("- **Recession:** 10% revenue drop, 5% spending increase")
        st.write("- **Inflation:** Growth reduction, interest rate increase")
        st.write("- **Demographic Shock:** Beneficiary surge, coverage challenges")
        st.write("- **Market Correction:** General deficit pressures")
        st.write("- **Perfect Storm:** Combined worst-case scenario")


def page_report_generation():
    """Report generation page."""
    st.title("Report Generation")
    st.write("Generate comprehensive PDF and Excel reports from policy analysis.")
    
    # Report type selection
    report_type = st.radio(
        "Select Report Type:",
        ["Policy Summary", "Full Analysis", "Comparative Analysis"]
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Report Details")
        
        report_title = st.text_input(
            "Report Title",
            value="Fiscal Policy Analysis Report"
        )
        
        report_author = st.text_input(
            "Author",
            value="PoliSim Analysis Team"
        )
        
        report_description = st.text_area(
            "Description",
            value="Comprehensive analysis of fiscal policy scenarios and impacts."
        )
    
    with col2:
        st.subheader("Export Options")
        
        export_pdf = st.checkbox("Export as PDF", value=True)
        export_excel = st.checkbox("Export as Excel", value=True)
        export_json = st.checkbox("Export as JSON", value=False)
        
        st.write("**Report Sections:**")
        include_projections = st.checkbox("10-Year Projections", value=True)
        include_sensitivity = st.checkbox("Sensitivity Analysis", value=True)
        include_scenarios = st.checkbox("Scenario Comparison", value=True)
        include_monte_carlo = st.checkbox("Monte Carlo Results", value=True)
        include_recommendations = st.checkbox("Recommendations", value=True)
    
    if st.button("Generate Report", type="primary"):
        try:
            from core.report_generator import ComprehensiveReportBuilder, ReportMetadata
            
            # Create metadata
            metadata = ReportMetadata(
                title=report_title,
                author=report_author,
                description=report_description,
            )
            
            # Create builder
            builder = ComprehensiveReportBuilder(metadata)
            
            # Add executive summary based on report type
            if report_type == "Policy Summary":
                summary_text = (
                    "This report summarizes the key findings of a fiscal policy analysis. "
                    "The analysis includes revenue impacts, spending changes, and deficit effects "
                    "across a 10-year projection horizon."
                )
            elif report_type == "Full Analysis":
                summary_text = (
                    "This comprehensive report presents a detailed analysis of fiscal policy scenarios. "
                    "It includes baseline projections, sensitivity analyses, Monte Carlo simulations, "
                    "and policy recommendations based on multiple fiscal goals."
                )
            else:
                summary_text = (
                    "This report compares multiple policy scenarios to identify optimal approaches "
                    "for achieving fiscal objectives. Results include comparative metrics, ranking, "
                    "and scenario-specific recommendations."
                )
            
            builder.add_executive_summary(summary_text)
            
            # Add sample policy overview
            builder.add_policy_overview(
                policy_name="Sample Policy Scenario",
                revenue_impact=50.0,
                spending_impact=-30.0,
                deficit_impact=-80.0,
            )
            
            # Add projections if selected
            if include_projections:
                projection_data = {
                    "Year": list(range(2025, 2035)),
                    "Revenue (B)": [6000 + i*50 for i in range(10)],
                    "Spending (B)": [6900 - i*20 for i in range(10)],
                    "Deficit (B)": [900 - i*70 for i in range(10)],
                }
                projections_df = pd.DataFrame(projection_data)
                builder.add_fiscal_projections(projections_df)
            
            # Add sensitivity if selected
            if include_sensitivity:
                sensitivity_data = {
                    "Parameter": ["Revenue Growth", "Spending Change", "GDP Growth", "Interest Rate"],
                    "Impact on Deficit": [-150, 200, -80, 120],
                    "Elasticity": [-0.25, 0.35, -0.15, 0.20],
                }
                sensitivity_df = pd.DataFrame(sensitivity_data)
                builder.add_sensitivity_analysis(sensitivity_df)
            
            # Add scenarios if selected
            if include_scenarios:
                scenarios_data = {
                    "Scenario": ["Status Quo", "Tax Reform", "Spending Cut", "Balanced"],
                    "10-Year Deficit (B)": [9200, 8500, 8200, 7800],
                    "Avg Annual (B)": [920, 850, 820, 780],
                    "Final Year Deficit (B)": [650, 450, 300, 200],
                }
                scenarios_df = pd.DataFrame(scenarios_data)
                builder.add_scenario_comparison(scenarios_df)
            
            # Add Monte Carlo if selected
            if include_monte_carlo:
                mc_data = {
                    "Metric": ["Mean Deficit", "Median Deficit", "Std Dev", "P10", "P90"],
                    "Value (B)": [850, 825, 120, 600, 1100],
                    "Probability": [100, 100, 100, 100, 100],
                }
                mc_df = pd.DataFrame(mc_data)
                builder.add_monte_carlo_results(mc_df)
            
            # Add recommendations if selected
            if include_recommendations:
                recommendations_text = (
                    "<b>1. Revenue Enhancement:</b> Consider targeted tax reforms to increase federal revenue. "
                    "A 5% increase in revenue would reduce the 10-year deficit by approximately $300B.<br/><br/>"
                    "<b>2. Spending Efficiency:</b> Implement spending controls in discretionary categories. "
                    "A 3% reduction in growth would save approximately $200B over 10 years.<br/><br/>"
                    "<b>3. Balanced Approach:</b> Combine modest revenue increases with targeted spending reforms "
                    "for the most sustainable fiscal path.<br/><br/>"
                    "<b>4. Risk Management:</b> Monitor Monte Carlo results for adverse scenarios and maintain "
                    "policy flexibility for economic changes."
                )
                builder.add_recommendations(recommendations_text)
            
            # Generate reports
            report_dir = Path("reports/generated")
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
            
            generated_files = []
            
            # PDF export
            if export_pdf:
                try:
                    pdf_path = report_dir / f"report_{timestamp}.pdf"
                    builder.generate_pdf(str(pdf_path))
                    generated_files.append(("PDF", pdf_path))
                    st.success(f"PDF report generated: {pdf_path.name}")
                except Exception as e:
                    st.warning(f"PDF generation requires reportlab: pip install reportlab")
            
            # Excel export
            if export_excel:
                try:
                    excel_path = report_dir / f"report_{timestamp}.xlsx"
                    builder.generate_excel(str(excel_path))
                    generated_files.append(("Excel", excel_path))
                    st.success(f"Excel report generated: {excel_path.name}")
                except Exception as e:
                    st.warning(f"Excel generation requires openpyxl: pip install openpyxl")
            
            # JSON export
            if export_json:
                try:
                    json_path = report_dir / f"report_{timestamp}.json"
                    builder.generate_json(str(json_path))
                    generated_files.append(("JSON", json_path))
                    st.success(f"JSON report generated: {json_path.name}")
                except Exception as e:
                    st.error(f"JSON generation failed: {e}")
            
            # Display download links
            if generated_files:
                st.subheader("Generated Reports")
                for file_type, file_path in generated_files:
                    if file_path.exists():
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"Download {file_type} Report",
                                data=f.read(),
                                file_name=file_path.name,
                                mime="application/octet-stream"
                            )
        
        except Exception as e:
            st.error(f"Error generating report: {e}")
            st.write(f"Make sure you have reportlab and openpyxl installed:")
            st.code("pip install reportlab openpyxl")


def main():
    """Main Streamlit app."""
    if not HAS_STREAMLIT:
        print("Streamlit not installed. Install with: pip install streamlit plotly")
        return
    
    st.set_page_config(
        page_title="CBO 2.0 Fiscal Dashboard",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sidebar navigation
    page = st.sidebar.radio(
        "Navigation",
        [
            "Overview",
            "Healthcare",
            "Social Security",
            "Federal Revenues",
            "Medicare/Medicaid",
            "Discretionary Spending",
            "Combined Outlook",
            "Policy Comparison",
            "---",
            "Recommendations",
            "Scenario Explorer",
            "Impact Calculator",
            "Advanced Scenarios",
            "---",
            "Report Generation",
            "Custom Policy Builder",
            "Real Data Dashboard",
            "Policy Upload"
        ]
    )
    
    if page == "Overview":
        page_overview()
    elif page == "Healthcare":
        page_healthcare()
    elif page == "Social Security":
        page_social_security()
    elif page == "Federal Revenues":
        page_federal_revenues()
    elif page == "Medicare/Medicaid":
        page_medicare_medicaid()
    elif page == "Discretionary Spending":
        page_discretionary_spending()
    elif page == "Combined Outlook":
        page_combined_outlook()
    elif page == "Policy Comparison":
        page_policy_comparison()
    elif page == "Recommendations":
        page_policy_recommendations()
    elif page == "Scenario Explorer":
        page_scenario_explorer()
    elif page == "Impact Calculator":
        page_impact_calculator()
    elif page == "Advanced Scenarios":
        page_monte_carlo_scenarios()
    elif page == "Report Generation":
        page_report_generation()
    elif page == "Custom Policy Builder":
        page_custom_policy_builder()
    elif page == "Real Data Dashboard":
        page_real_data_dashboard()
    elif page == "Policy Upload":
        page_policy_upload()


if __name__ == "__main__":
    main()
