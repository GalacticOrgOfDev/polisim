# Theme System Overview

**Last Updated:** December 31, 2025  \
**Scope:** Consolidated reference for themes, fixes, and testing (supersedes prior theme audit/quick-reference/testing docs)

## Available Themes

| Theme | ID | Purpose | Animation | Font |
|-------|----|---------|-----------|------|
| Light | `light` | Professional/Windows-style default | None | Segoe UI |
| Dark | `dark` | Eye-friendly dark with red accents | Optional particles | Segoe UI |
| Matrix AI | `matrix` | Hacker/AI aesthetic | Matrix rain | Courier New |
| Cyberpunk | `cyberpunk` | Neon yellow/magenta | Particle field | Orbitron |
| Nord Arctic | `nord` | Cool minimalist palette | None | Inter |
| Solarized Dark | `solarized` | Classic coding palette | None | Source Code Pro |

## Key Fixes (Dec 26)
- Deep copy of theme configs prevents mutation; single CSS injection with cleanup on theme switch.
- Removed legacy light-mode overrides and redundant CSS; theme styles now flow from ElementStyle definitions.
- Radio/buttons/sliders/checkboxes standardized per theme; navigation labels restored after radio CSS cleanup.
- Plotly/chart palettes mapped per theme; animations cleaned on switch.

## Using Themes
- Dashboard: Settings → Theme Settings → pick theme → Apply Theme Now (optional: custom colors).
- Code: `from ui.themes import apply_theme, apply_plotly_theme; apply_theme(theme_id); apply_plotly_theme(fig, theme_id)`.

## Test & Smoke Checklist
- Switch through all 6 themes; confirm no color bleed and only one injected style tag remains.
- Text readability: Light/Dark use high-contrast text; Matrix/Cyberpunk text stays white/off-white; sliders/radios/checkboxes visibly styled.
- Animations: Matrix rain and Cyberpunk particles visible behind content without layout shifts; cleanup works when switching away.
- Accessibility: Keyboard navigation and tooltip readability on light/dark; contrast acceptable for key inputs and navigation.
- Charts: Plotly colors match theme palette; legends/text readable on dark backgrounds.

## Optional Windows 2000 Variant (Light)
- If the classic beveled look is needed, use the Light theme with ElementStyle tweaks (3D borders, gray panel background, blue focus). Keep these in ElementStyle—not hardcoded CSS overrides—to avoid divergence.

## References
- Implementation: `ui/themes.py`, `ui/animations.py`
- Animations: matrix rain/particle helpers in `ui/animations.py`
- Testing script entry point: `streamlit run ui/dashboard.py` (Settings → Theme Settings)