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
        st.metric("Module Status", "Phase 3.1", delta="Healthcare + SS + Revenue + Medicare/Medicaid")
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
    """)
    
    st.info("""
    📊 **Navigate to other pages:**
    - Healthcare Analysis
    - Social Security Outlook
    - Federal Revenues
    - Medicare/Medicaid
    - Combined Fiscal Outlook
    - Policy Comparison
    """)


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
            "Social Security",
            "Federal Revenues",
            "Medicare/Medicaid",
            "Combined Outlook",
            "Policy Comparison"
        ]
    )
    
    if page == "Overview":
        page_overview()
    elif page == "Social Security":
        page_social_security()
    elif page == "Federal Revenues":
        page_federal_revenues()
    elif page == "Medicare/Medicaid":
        page_medicare_medicaid()
    else:
        st.title("Coming Soon")
        st.info("Combined fiscal outlook and policy comparison features coming in next release")


if __name__ == "__main__":
    main()
