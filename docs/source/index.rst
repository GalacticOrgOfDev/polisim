PoliSim API Documentation
===========================

PoliSim is a production-grade policy analysis simulator for government-level fiscal modeling.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   quickstart
   modules/core
   modules/api
   modules/scripts
   modules/utils

Overview
--------

PoliSim provides comprehensive tools for:

- Healthcare policy simulation (Phase 1)
- Social Security and tax reform modeling (Phase 2)
- Medicare/Medicaid projections (Phase 3)
- Monte Carlo uncertainty quantification
- Multi-scenario comparison and visualization

Quick Start
-----------

Import the core modules:

.. code-block:: python

   from core.social_security import SocialSecurityModel
   from core.revenue_modeling import FederalRevenueModel
   from core.simulation import simulate_comprehensive_reform

   # Create a Social Security model
   model = SocialSecurityModel()
   
   # Run a 30-year projection with 1000 Monte Carlo iterations
   results = model.project_trust_funds(years=30, iterations=1000)

Key Features
------------

**Phase 1: Healthcare Simulation**
   - Multi-year healthcare spending projections
   - Coverage expansion modeling
   - Revenue growth calculations
   - Fiscal circuit breaker logic

**Phase 2: Social Security + Tax Reform**
   - OASI and DI trust fund projections
   - Monte Carlo uncertainty modeling
   - Solvency analysis with confidence intervals
   - Progressive tax reform scenarios (wealth, consumption, carbon, FTT)

**Phase 2B: Production Polish**
   - High-performance vectorized operations (5.97x faster)
   - Comprehensive visualization suite (3 scripts, 9+ chart types)
   - 111 tests with 100% pass rate
   - Edge case and boundary condition coverage

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
