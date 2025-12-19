# Quick Start: Enhanced Carousel

## Launch the App
```bash
python main.py
```

## Navigate to Carousel
1. Click **Comparison** tab
2. Scroll down to **Interactive Charts** section

## Control the Carousel

### Using Buttons (Mouse)
- **◀ Prev** - Previous chart
- **Next ▶** - Next chart  
- **View Interactive HTML** - Toggle to interactive mode (shows as "View PNG Static" when in HTML mode)
- **Open in Browser** - Launch full Plotly chart in web browser

### Using Keyboard (Faster!)
- **← / →** - Previous / next chart
- **Tab** - Toggle between PNG and HTML modes

### Select Policy
- Use dropdown at top of carousel to switch between:
  - Current_US_Healthcare_System
  - United_States_Galactic_Health_Act
  - (Or any other policies you've configured)

## Chart Types
Each policy has 3 charts:
1. **Spending Trend** - Annual health spending ($) + % GDP
2. **Revenue Breakdown** - Stacked payroll/general/other revenues
3. **Debt & Surplus** - Debt reduction and surplus allocation

## View Modes

### PNG Mode (Static)
- Sharp, publication-ready image
- Perfect for reports and presentations
- No interaction needed

### HTML Mode (Interactive - In App)
- Preview in carousel canvas
- Instructions to click "Open in Browser" for full interactivity

### Browser (Full Interactivity)
- Click "Open in Browser" button
- Or click any chart when in HTML mode
- Full Plotly toolbar: hover, pan, zoom, toggle series, export

## Workflow Example

1. Set up scenarios in the **Scenario Setup** tab
2. Configure current and proposed policies
3. Run comparison to generate charts
4. Go to **Comparison** tab
5. Scroll to carousel (bottom)
6. **Browse PNG charts** with arrow keys (← / →)
7. Press **Tab** to toggle to HTML mode
8. Click **Open in Browser** for full interactivity
9. Back to app: press **Tab** again to return to PNG mode

## Files & Locations

| Item | Location |
|------|----------|
| **Carousel Code** | `ui/chart_carousel.py` |
| **Chart Generator** | `ui/healthcare_charts.py` |
| **PNG Charts** | `reports/charts/<PolicyName>/*.png` |
| **HTML Charts** | `reports/charts/<PolicyName>/*.html` |
| **Regenerate Charts** | `python run_visualize.py` |
| **Create Full Report** | `python run_report.py` |

## Keyboard Shortcuts Reference

| Key | Action |
|-----|--------|
| `←` | Previous chart |
| `→` | Next chart |
| `Tab` | Toggle PNG ↔ HTML mode |

## Tips

- **Fastest workflow:** Use keyboard navigation (arrows + Tab)
- **Large displays:** Carousel expands to fill available space
- **High DPI screens:** PNG images scale automatically
- **Interactive analysis:** Use HTML mode + browser for full Plotly tools
- **Reports:** PNG mode perfect for exporting to documents

---

**For detailed feature documentation, see CAROUSEL_FEATURES.md**
