# Sprint 5.4 Slice Work Plan

Date: December 27, 2025  
Scope: Streamlit UI enhancement (auth, prefs, themes, tooltips, outputs, mobile, performance)

## Ordered Slices
1. Preferences & session sync: default merge, API/local save, reset-to-defaults, offline-safe fallback. **Status: implemented (UI + tests)**
2. Auth UX polish: production gating (done), logout everywhere, token-expiry messaging, profile/mini-card consistency. **Status: implemented (UI + tests)**
3. Theme application: ensure CSS + Plotly themes honor selected theme/custom colors; guard transparency for dark themes. **Status: implemented (UI + tests)**
4. Animations: Matrix/cyberpunk toggles, speed/font controls, sensible performance caps (FPS/columns) and disable on low power.
5. Settings UI completeness: tooltips toggle, decimals/number format, language/timezone/date format, chart theme, custom theme preview/reset, animation toggles.
6. Universal tooltips: wire registry across all pages and respect enable/disable.
7. Output UX: reliable download buttons (PDF/Excel/JSON), status/progress, naming consistency, graceful fallbacks if deps missing.
8. Mobile responsiveness: sidebar behavior on small widths, touch-friendly buttons, column stacking, chart/container widths, header/nav z-index.
9. Performance pass: cache/lazy-load heavy components, reduce initial render cost, disable animations by default when needed.
10. Docs & release hygiene: update README/CHANGELOG, sprint summary, and any new guides created during implementation.

## Readiness Notes
- Dashboard production auth gating is live; dev mode still bypasses auth for local use.
- New auth/prefs tests added (tests/test_ui_auth.py).
- Full suite currently: 486 passed, 3 skipped, 14 PytestReturnNotNone warnings (tests returning values vs asserts).

## Execution Tips
- Keep preferences merge deterministic: defaults → local → API.
- Avoid regressions to existing sidebar/header styling; preserve button-based nav.
- Run `python -m pytest -vv` after each slice; add targeted tests when feasible.
