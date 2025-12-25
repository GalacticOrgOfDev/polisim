Visualization Scripts
=====================

These scripts generate charts and dashboards for policy analysis.

Trust Fund Visualization
-------------------------

Generate Social Security trust fund trajectory charts with uncertainty bands.

.. automodule:: scripts.visualize_trust_fund
   :members:
   :undoc-members:
   :show-inheritance:

**Usage:**

.. code-block:: bash

   python scripts/visualize_trust_fund.py --scenario baseline --years 30 --iterations 1000

Tax Revenue Visualization
--------------------------

Generate tax revenue breakdown and comparison charts.

.. automodule:: scripts.visualize_tax_revenue
   :members:
   :undoc-members:
   :show-inheritance:

**Usage:**

.. code-block:: bash

   python scripts/visualize_tax_revenue.py --scenario progressive --years 20
   python scripts/visualize_tax_revenue.py --compare baseline progressive moderate

Multi-Scenario Dashboard
-------------------------

Generate comprehensive 9-panel comparison dashboards.

.. automodule:: scripts.visualize_scenarios
   :members:
   :undoc-members:
   :show-inheritance:

**Usage:**

.. code-block:: bash

   python scripts/visualize_scenarios.py --scenarios baseline progressive --years 30 --iterations 1000

Phase 2 Demo Script
--------------------

Demonstration of Phase 2 capabilities.

.. automodule:: scripts.demo_phase2_scenarios
   :members:
   :undoc-members:
   :show-inheritance:
