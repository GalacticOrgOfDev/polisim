# UI Module

This module provides **visualization, reporting, and user interface components**.

## Components

- **`chart_carousel.py`** - Multi-scenario visualization carousel
  - Compare policies side-by-side across key metrics
  - Interactive hover information
  - Export to HTML/PDF

- **`healthcare_charts.py`** - Healthcare-specific visualizations
  - Cost projections (line charts, stacked bars)
  - Coverage and outcome metrics
  - Comparative analysis charts

- **`server.py`** - Web server interface (future Streamlit/FastAPI)
  - Real-time simulation dashboard
  - Interactive parameter sliders
  - Report generation endpoint

- **`widgets.py`** - Reusable UI components
  - Chart wrappers
  - Data table formatters
  - Export utilities

## Usage

```python
from ui.chart_carousel import ScenarioCarousel
from ui.healthcare_charts import create_cost_projection_chart

# Create visualization suite
carousel = ScenarioCarousel(scenarios=[policy1, policy2])
carousel.generate_html("reports/comparison.html")

# Individual charts
chart = create_cost_projection_chart(results)
chart.save("reports/costs.html")
```

## Planned Enhancements (Phase 2+)

- **Streamlit App** - Interactive web interface with real-time sliders
- **Dash/Plotly** - Professional dashboards with advanced interactivity
- **FastAPI Backend** - RESTful API for automated report generation
- **React Frontend** - Modern SPA for complex scenarios

## Chart Types

- Line charts (time-series projections)
- Stacked bar charts (budget allocation, spending categories)
- Histograms (Monte Carlo distributions)
- Box plots (confidence intervals)
- Heatmaps (sensitivity analysis)
- Waterfall charts (scenario differences)

