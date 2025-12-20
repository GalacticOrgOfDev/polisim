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
    
    col1, col2 = st.columns(2)
    with col1:
        healthcare_policy = st.selectbox(
            "Select policy:",
            ["usgha", "current_law"],
            help="USGHA = US Galactic Health Act proposal"
        )
    with col2:
        years = st.slider("Projection years:", 5, 30, 22, key="healthcare_years")
    
    if st.button("Project Healthcare"):
        try:
            from core.simulation import simulate_healthcare_years
            
            policy = get_policy_by_type(PolicyType.USGHA if healthcare_policy == "usgha" else PolicyType.CURRENT_LAW)
            
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
                    f"${results['total_spending'].sum()/1e12:.1f}T",
                    delta="All categories"
                )
            with col2:
                st.metric(
                    "Latest Year Per-Capita",
                    f"${results['per_capita_spending'].iloc[-1]:,.0f}",
                    delta=f"Year {years}"
                )
            with col3:
                st.metric(
                    "Debt Reduction",
                    f"${results['debt_reduction'].sum()/1e12:.1f}T",
                    delta="22-year total"
                )
            
            # Chart: Healthcare spending over time
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=results['year'],
                y=results['total_spending']/1e9,
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
    
    col1, col2 = st.columns(2)
    with col1:
        num_policies = st.slider("Number of policies to compare:", 2, 3, 2, key="num_policies")
        years = st.slider("Projection years:", 10, 75, 30, key="compare_years")
    with col2:
        metric_to_compare = st.selectbox(
            "Compare by metric:",
            ["10-year deficit", "Average annual deficit", "Interest spending", "Total spending"]
        )
        iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000, key="compare_iter")
    
    # Policy/scenario selectors
    policies = {}
    for i in range(num_policies):
        st.subheader(f"Policy {i+1}")
        
        col1, col2 = st.columns(2)
        with col1:
            rev_scenario = st.selectbox(f"Revenue Scenario {i+1}:", ["baseline", "recession_2026", "strong_growth"], key=f"rev_scenario_{i}")
        with col2:
            discret_scenario = st.selectbox(f"Discretionary {i+1}:", ["baseline", "growth", "reduction"], key=f"discret_scenario_{i}")
        
        policies[f"Policy {i+1}"] = {
            "revenue_scenario": rev_scenario,
            "discretionary_scenario": discret_scenario,
        }
    
    if st.button("Compare Policies"):
        model = CombinedFiscalOutlookModel()
        
        with st.spinner("Running policy comparison..."):
            comparison_data = {}
            
            try:
                for policy_name, config in policies.items():
                    summary = model.get_fiscal_summary(
                        years=years,
                        iterations=iterations,
                        revenue_scenario=config["revenue_scenario"],
                        discretionary_scenario=config["discretionary_scenario"]
                    )
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
            "Policy Comparison"
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


if __name__ == "__main__":
    main()
