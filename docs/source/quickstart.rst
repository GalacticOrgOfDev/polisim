Quick Start Guide
==================

This guide helps you get started with PoliSim API documentation.

Installation
------------

Install PoliSim and its dependencies:

.. code-block:: bash

   pip install -r requirements.txt

For development (including documentation tools):

.. code-block:: bash

   pip install -r requirements-dev.txt

Basic Usage Examples
--------------------

Social Security Projection
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core.social_security import SocialSecurityModel
   
   # Create model with default SSA 2024 Trustees assumptions
   model = SocialSecurityModel()
   
   # Project trust funds for 30 years with 1000 Monte Carlo iterations
   projections = model.project_trust_funds(years=30, iterations=1000)
   
   # Analyze solvency dates
   solvency = model.estimate_solvency_dates(projections)
   print(f"OASI depletion probability: {solvency['OASI']['probability_depleted']:.1%}")

Tax Reform Analysis
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core.revenue_modeling import FederalRevenueModel
   
   # Create revenue model with CBO 2025 baseline
   model = FederalRevenueModel()
   
   # Project all federal revenues for 20 years
   revenues = model.project_all_revenues(years=20, iterations=500)
   
   # Analyze tax reform impact
   reform = {'corporate_tax_rate': 0.28}  # Raise corporate rate to 28%
   impact = model.apply_tax_reform(reform)
   print(f"Additional revenue: ${impact['total_additional_revenue']:.1f}B")

Comprehensive Reform Simulation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from core.simulation import simulate_comprehensive_reform
   import pandas as pd
   
   # Define policy reform package
   policy = {
       'name': 'Progressive Reform',
       'social_security': {
           'payroll_tax_rate': 0.145,  # Raise to 14.5%
           'payroll_tax_cap': None      # Remove cap
       },
       'tax_reform': {
           'wealth_tax_rate': 0.02,     # 2% wealth tax
           'wealth_tax_threshold': 50_000_000
       }
   }
   
   # Run simulation
   results = simulate_comprehensive_reform(
       policy=policy,
       years=30,
       iterations=1000
   )
   
   # Results include aggregated statistics
   print(results[('OASI_balance', 'mean')].tail())

Visualization
~~~~~~~~~~~~~

.. code-block:: bash

   # Generate trust fund trajectory charts
   python scripts/visualize_trust_fund.py --scenario baseline --years 30
   
   # Generate tax revenue analysis
   python scripts/visualize_tax_revenue.py --scenario progressive --years 20
   
   # Generate multi-scenario comparison dashboard
   python scripts/visualize_scenarios.py --scenarios baseline progressive --years 30

Key Concepts
------------

Monte Carlo Simulation
~~~~~~~~~~~~~~~~~~~~~~~

PoliSim uses Monte Carlo methods to quantify uncertainty in projections:

- **Iterations**: Number of simulation runs (typically 1000-10000)
- **Uncertainty Parameters**: Standard deviations for demographic and economic factors
- **Confidence Intervals**: 90% and 50% bands around mean projections

Trust Fund Accounting
~~~~~~~~~~~~~~~~~~~~~

Social Security trust funds follow SSA accounting standards:

- **OASI**: Old-Age and Survivors Insurance
- **DI**: Disability Insurance
- **Combined**: OASDI combined trust fund
- **Solvency Date**: Year when trust fund balance reaches zero

Tax Reform Components
~~~~~~~~~~~~~~~~~~~~~

Phase 2 supports four progressive tax types:

1. **Wealth Tax**: Annual tax on net worth above threshold
2. **Consumption Tax**: Progressive VAT-style tax
3. **Carbon Tax**: Tax on CO2 emissions
4. **Financial Transaction Tax (FTT)**: Tax on stock/bond trades

Policy Reform Parameters
~~~~~~~~~~~~~~~~~~~~~~~~

Common reform parameters:

- ``payroll_tax_rate``: Social Security payroll tax rate (default: 0.124)
- ``payroll_tax_cap``: Maximum taxable earnings (None = no cap)
- ``full_retirement_age``: Age for full Social Security benefits
- ``benefit_reduction_pct``: Percentage reduction in benefits
- ``wealth_tax_rate``: Annual wealth tax rate
- ``carbon_tax_per_ton``: Tax per ton of CO2

Performance Tips
----------------

Large Simulations
~~~~~~~~~~~~~~~~~

For large-scale analysis:

1. Start with fewer iterations to test (100-500)
2. Increase to 1000+ for final analysis
3. Use vectorized operations (already optimized)
4. Monitor memory usage with very long projections (50+ years)

Parallel Processing
~~~~~~~~~~~~~~~~~~~

Monte Carlo iterations are independent and can be parallelized:

.. code-block:: python

   # Current implementation uses single-threaded NumPy
   # Future enhancement: parallel processing for 10000+ iterations

Caching Results
~~~~~~~~~~~~~~~

Save results for reuse:

.. code-block:: python

   # Save projections
   projections.to_csv('projections_baseline.csv', index=False)
   
   # Load projections
   projections = pd.read_csv('projections_baseline.csv')

Common Patterns
---------------

Scenario Comparison
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   scenarios = ['baseline', 'progressive', 'moderate']
   results = {}
   
   for scenario in scenarios:
       policy = load_policy(scenario)
       results[scenario] = simulate_comprehensive_reform(
           policy=policy,
           years=30,
           iterations=1000
       )
   
   # Compare solvency
   for name, data in results.items():
       solvency = model.estimate_solvency_dates(data)
       print(f"{name}: {solvency}")

Sensitivity Analysis
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   tax_rates = [0.12, 0.13, 0.14, 0.15]
   solvency_years = []
   
   for rate in tax_rates:
       policy = {'payroll_tax_rate': rate}
       result = model.apply_policy_reform(policy)
       solvency_years.append(result['oasi_extension_years'])
   
   # Plot sensitivity
   import matplotlib.pyplot as plt
   plt.plot(tax_rates, solvency_years)
   plt.xlabel('Payroll Tax Rate')
   plt.ylabel('Years of Solvency Extension')
   plt.show()

Troubleshooting
---------------

Import Errors
~~~~~~~~~~~~~

If you get import errors, ensure:

1. Python path includes project root: ``export PYTHONPATH=/path/to/polisim``
2. All dependencies installed: ``pip install -r requirements.txt``
3. Using correct Python environment

Memory Issues
~~~~~~~~~~~~~

For large simulations (years * iterations > 1,000,000):

1. Reduce iterations first
2. Reduce projection horizon
3. Process results in chunks
4. Use aggregated statistics instead of raw data

Slow Performance
~~~~~~~~~~~~~~~~

If simulations are slow:

1. Check iteration count (1000-5000 is typical)
2. Ensure NumPy is using optimized BLAS
3. Profile with: ``python -m cProfile script.py``

Further Reading
---------------

- :doc:`modules/core` - Core API reference
- :doc:`modules/scripts` - Visualization tools
- :doc:`index` - Full documentation index
