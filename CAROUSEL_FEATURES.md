# Enhanced Chart Carousel - Feature Summary

## Overview
The Chart Carousel widget now provides an integrated, interactive way to view and explore all generated charts (both static PNG and interactive HTML Plotly charts) directly within the Tkinter application.

## Features

### 1. **Dual Display Modes**
- **PNG Mode (Default):** View high-quality static images of all charts
- **HTML Mode (Interactive):** Preview interactive Plotly charts with ability to open in browser for full Plotly interactivity
  - Hover to inspect values
  - Pan and zoom
  - Toggle data series on/off
  - Export to PNG (Plotly toolbar)

### 2. **Policy Selector Dropdown**
- Automatically detects available policy scenarios in `reports/charts/`
- Quick switch between policies
- Policies are alphabetically sorted

### 3. **Navigation Controls**
- **Prev Button (◀):** Jump to previous chart
- **Next Button (▶):** Jump to next chart
- **Chart Counter:** Shows current position (e.g., "2 / 6")

### 4. **Keyboard Navigation**
- **Left Arrow (←):** Previous chart
- **Right Arrow (→):** Next chart
- **Tab:** Toggle between PNG and HTML display modes
- **Click & Focus:** Widget automatically gains focus for keyboard input

### 5. **Display Mode Toggle**
- **"View Interactive HTML" Button:** Switch to interactive HTML preview mode
  - Button text changes to "View PNG Static" when in HTML mode
  - Clearly labeled preview with instructions
  - Hints to use "Open in Browser" for full Plotly interactivity
- Navigation (prev/next) automatically resets to PNG mode for cleaner UX

### 6. **Open in Browser**
- Launches the interactive HTML chart in your default web browser
- Falls back to PNG if HTML is not available
- Full Plotly functionality in browser (hover, pan, zoom, export)

### 7. **Responsive Canvas**
- Large, expandable canvas that fills available space
- Automatic image scaling with aspect ratio preservation
- Graceful handling of missing or corrupted files

### 8. **Smart Error Handling**
- Informative messages if HTML file not found
- Clear feedback if no charts available for policy
- Exception handling for image loading failures

## Usage in Application

The carousel is embedded in the **Comparison Tab** of the main application under the "Interactive Charts" panel, displayed below the original matplotlib figure plots.

### Typical Workflow:
1. Set up policies and run comparison in the Scenario Setup, Current Policy, and Proposed Policy tabs
2. Switch to the **Comparison Tab**
3. View original matplotlib graphs in the upper area
4. Scroll to the **Interactive Charts** section (carousel widget)
5. Use dropdown to select a policy
6. Navigate charts with buttons or arrow keys
7. Press Tab or click "View Interactive HTML" to toggle modes
8. Click "Open in Browser" to interact with charts in web browser

## File Locations

- **PNG Charts:** `reports/charts/<PolicyName>/<chart_name>.png`
- **HTML Charts:** `reports/charts/<PolicyName>/<chart_name>.html`
- **Carousel Code:** `ui/chart_carousel.py`
- **Chart Generation:** Run `python run_visualize.py` to generate/update charts

## Chart Types Generated

Each policy scenario generates three chart types:
1. **Spending Trend:** Health spending ($) with % GDP on secondary axis
2. **Revenue Breakdown:** Stacked area chart of payroll, general, and other revenues
3. **Debt & Surplus:** Dual-axis chart showing debt reduction and surplus allocation

For two policies (Current + Proposed), you'll see **6 total charts** (3 per policy).

## Technical Details

### Dependencies
- `tkinter` - UI framework
- `PIL/Pillow` - Image rendering
- `webbrowser` - External chart viewing
- `tkinter.messagebox` - User dialogs

### Display Mode Logic
- PNG: Loaded via PIL, scaled for canvas, cached in `self.photo`
- HTML: Preview text with instructions in canvas, full interaction via browser launch

### Performance Notes
- PNG caching prevents repeated re-reads
- Canvas resizing triggers automatic re-render
- Large images scale efficiently with LANCZOS resampling

## Future Enhancements (Optional)

1. **Native HTML Rendering in Tk:**
   - Add `tkinterweb` or similar lightweight browser widget
   - View interactive charts natively in-app without launching browser
   - Would require adding new dependency

2. **Matplotlib Figure Integration:**
   - Convert original matplotlib figures to PNG
   - Add to carousel as additional chart type
   - Enable side-by-side comparison

3. **Scenario Metadata Registry:**
   - Create `scenarios/index.json` with policy descriptions
   - Display human-friendly policy names in dropdown
   - Add policy comparison summaries

4. **Chart Regeneration Triggers:**
   - Add "Refresh Charts" button to regenerate on-demand
   - Wire to run_visualize.py without leaving app

---

**Last Updated:** Phase 3 Enhancement - Carousel v2.0
