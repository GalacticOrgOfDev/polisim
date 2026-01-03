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
# mypy: ignore-errors

# Import typing constructs at module level (needed for type hints outside try blocks)
from typing import Dict, Any, Optional, List, Callable

# Import pandas at module level for type hints
import pandas as pd

# Ensure project root is in Python path for imports
import sys
from pathlib import Path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    # Load core modules FIRST (before streamlit) to avoid circular dependency issues
    from core.social_security import SocialSecurityModel, SocialSecurityReforms, TrustFundAssumptions, BenefitFormula
    from core.revenue_modeling import FederalRevenueModel, TaxReforms
    from core.medicare_medicaid import MedicareModel, MedicaidModel
    from core.discretionary_spending import DiscretionarySpendingModel
    from core.interest_spending import InterestOnDebtModel
    from core.combined_outlook import CombinedFiscalOutlookModel
    from core.healthcare import get_policy_by_type, PolicyType
    from core.economic_engine import MonteCarloEngine, PolicyScenario, EconomicParameters
    from core.data_loader import load_real_data
    from core.policy_builder import PolicyTemplate, PolicyLibrary
    from core.pdf_policy_parser import PolicyPDFProcessor
    from core.policy_enhancements import (
        PolicyRecommendationEngine,
        InteractiveScenarioExplorer,
        PolicyImpactCalculator,
    )
    from core.monte_carlo_scenarios import (
        MonteCarloPolicySimulator,
        PolicySensitivityAnalyzer,
        StressTestAnalyzer,
    )
    
    # NOW load streamlit and UI modules
    import streamlit as st
    import pandas as pd  # type: ignore[import-untyped]
    import numpy as np
    import plotly.graph_objects as go  # type: ignore[import-untyped]
    import plotly.express as px  # type: ignore[import-untyped]
    from pathlib import Path
    import json
    from typing import Dict, Any
    
    from ui.auth import StreamlitAuth, show_user_profile_page
    from ui.themes import apply_theme, get_theme_list, preview_theme, customize_theme_colors, apply_plotly_theme
    from ui.animations import apply_animation
    from ui.tooltip_registry import get_tooltip as registry_get_tooltip
    from ui.teaching_mode import teaching_tooltip
    from ui.guided_tour_components import (
        render_teaching_mode_toggle,
        render_tour_overlay,
        render_educational_callout,
        render_welcome_banner,
        enhanced_metric
    )
    
    # Phase 7.2.2: Live Analysis UI Components
    from ui.live_analysis_panel import (
        LiveAnalysisPanel,
        render_live_analysis,
        process_stream_event,
        init_live_analysis_state,
        get_live_analysis_state,
    )
    from ui.confidence_visualization import (
        render_confidence_chart,
        render_confidence_summary,
        update_confidence_from_event,
        ConfidenceTracker,
        get_confidence_tracker,
    )
    from ui.debate_visualization import (
        render_debate_view,
        render_disagreement_map,
        render_debate_timeline,
        process_debate_event,
        create_demo_debate_data,
        init_debate_state,
    )
    HAS_LIVE_ANALYSIS = True
    
    # Phase 7.3.3: Chat UI Components
    from ui.chat_sidebar import (
        ChatSidebar,
        render_chat_sidebar,
        render_chat_right_panel,
        init_chat_sidebar_state,
        get_chat_sidebar_state,
        create_demo_messages,
        create_demo_channels,
    )
    HAS_CHAT_UI = True
    
    HAS_STREAMLIT = True
except ImportError as e:
    import traceback
    print(f"ImportError during dashboard initialization: {e}")
    traceback.print_exc()
    HAS_STREAMLIT = False
    HAS_LIVE_ANALYSIS = False
    HAS_CHAT_UI = False


# Centralized default settings for Streamlit UI
DEFAULT_SETTINGS = {
    'tooltips_enabled': True,
    'show_advanced_options': False,
    'decimal_places': 1,
    'chart_theme': 'plotly_dark',
    'theme': 'light',
    'animation_enabled': False,
    'animation_speed': 'normal',
    'bg_opacity': 0.6,
    'content_opacity': 0.8,
    'sidebar_opacity': 0.9,
    'header_opacity': 1.0,
    'matrix_font_size': 16,
    'custom_theme_enabled': False,
    'custom_theme_config': None,
    'language': 'English (US)',
    'timezone': 'UTC',
    'date_format': 'YYYY-MM-DD',
    'currency_symbol': '$',
    'number_format': '1,234,567.89',
    'abbreviation_style': 'Billions',
    'policy_cache_ttl_hours': 24,
    'chart_cache_ttl_minutes': 30,
    'auto_refresh_data': False,
    'debug_mode': False,
    'experimental_features': False,
    'max_monte_carlo_iterations': 100000,
    # Teaching Mode settings
    'teaching_mode_enabled': True,
    'teaching_mode_level': 'beginner',
    # Chat settings (Phase 7.3.3)
    'chat_panel_enabled': True,
    'chat_panel_width': 0.25,  # 25% of screen width
}


# =============================================================================
# Page Layout Wrapper with Chat Panel (Phase 7.3.3)
# =============================================================================

def render_page_with_chat(page_render_func, show_chat: bool = True):
    """Render a page with the PoliSim Chat panel as a fixed right sidebar.
    
    The chat panel is fixed in position and does not scroll with page content.
    Main content has a right margin to avoid overlap.
    
    Args:
        page_render_func: Function that renders the page content
        show_chat: Whether to show the chat panel (default True)
    
    Example:
        render_page_with_chat(page_overview)
    """
    if not show_chat or not HAS_CHAT_UI:
        # Render page without chat
        page_render_func()
        return
    
    # Check if chat is enabled in settings
    chat_enabled = st.session_state.get('settings', {}).get('chat_panel_enabled', True)
    if not chat_enabled:
        page_render_func()
        return
    
    # Get user info from auth if available
    user_id = None
    user_name = "User"
    try:
        from ui.auth import StreamlitAuth
        if StreamlitAuth.is_authenticated():
            user_data = StreamlitAuth.get_current_user()
            if user_data:
                user_id = user_data.get('user_id') or user_data.get('id')
                user_name = user_data.get('username') or user_data.get('name', 'User')
    except Exception:
        pass
    
    # Use columns layout: main content on left, chat on right
    # This keeps chat in normal document flow, avoiding overlap issues
    content_col, chat_col = st.columns([3, 1], gap="small")

    with content_col:
        page_render_func()

    with chat_col:
        # Render chat panel in the right column
        render_chat_right_panel(
            user_id=user_id,
            user_name=user_name,
            demo_mode=True,
            use_column_mode=True,  # Signal to use column-friendly styling
        )


def initialize_settings():
    """Initialize app settings in session state."""
    from ui.auth import StreamlitAuth
    import requests
    from pathlib import Path
    import json
    
    if 'settings' in st.session_state:
        return

    # Try to load from local file first
    settings_file = Path.home() / '.polisim' / 'settings.json'
    local_settings = None
    if settings_file.exists():
        try:
            with open(settings_file, 'r') as f:
                local_settings = json.load(f)
                st.session_state.settings = {**DEFAULT_SETTINGS, **local_settings}
        except Exception:
            pass

    # Sprint 5.4: Load from API if authenticated (overrides local file)
    if StreamlitAuth.is_authenticated():
        try:
            response = requests.get(
                f"{StreamlitAuth.API_BASE}/api/users/preferences",
                headers=StreamlitAuth.get_auth_header(),
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                prefs = data.get('preferences', {})
                
                # Merge API preferences with defaults (or local settings)
                current = st.session_state.settings if local_settings else DEFAULT_SETTINGS
                st.session_state.settings = {**current, **prefs}
            else:
                if not local_settings:
                    st.session_state.settings = dict(DEFAULT_SETTINGS)
        except Exception:
            # Fallback to local or defaults if API call fails
            if not local_settings:
                st.session_state.settings = dict(DEFAULT_SETTINGS)
    else:
        if not local_settings:
            st.session_state.settings = dict(DEFAULT_SETTINGS)


def save_settings():
    """Save current settings to API if authenticated and to local file."""
    from ui.auth import StreamlitAuth
    import requests
    from pathlib import Path
    import json
    
    # Save to local file first
    settings_file = Path.home() / '.polisim' / 'settings.json'
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(st.session_state.settings, f, indent=2)
        local_save_success = True
    except Exception as e:
        local_save_success = False
        local_error = str(e)
    
    if StreamlitAuth.is_authenticated():
        try:
            response = requests.put(
                f"{StreamlitAuth.API_BASE}/api/users/preferences",
                headers=StreamlitAuth.get_auth_header(),
                json=st.session_state.settings,
                timeout=5
            )
            
            if response.status_code == 200:
                return True, "Settings saved successfully (local + cloud)!"
            else:
                if local_save_success:
                    return True, f"Settings saved locally (API error: {response.json().get('error', 'Unknown')})"
                else:
                    return False, f"Failed to save: API error and local save failed"
        except Exception as e:
            # If API fails, still indicate local save status
            if local_save_success:
                return True, f"Settings saved locally (API unavailable: {str(e)[:50]}...)"
            else:
                return False, f"Failed to save locally and to API"
    else:
        # Not authenticated - local file only
        if local_save_success:
            return True, "Settings saved locally (login to sync across devices)"
        else:
            return False, f"Failed to save settings: {local_error}"


def reset_settings():
    """Reset settings to defaults locally and in the API when available."""
    from ui.auth import StreamlitAuth
    import requests
    from pathlib import Path
    import json

    # Reset in session
    st.session_state.settings = dict(DEFAULT_SETTINGS)

    # Reset local file
    settings_file = Path.home() / '.polisim' / 'settings.json'
    try:
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_file, 'w') as f:
            json.dump(st.session_state.settings, f, indent=2)
    except Exception:
        pass

    # Reset in API if authenticated
    if StreamlitAuth.is_authenticated():
        try:
            requests.post(
                f"{StreamlitAuth.API_BASE}/api/users/preferences/reset",
                headers=StreamlitAuth.get_auth_header(),
                timeout=5,
            )
        except Exception:
            # Swallow API errors; local reset already applied
            pass

    return True, "Settings reset to defaults"

def get_tooltip(term, definition):
    """Return tooltip if tooltips are enabled in settings."""
    if st.session_state.get('settings', {}).get('tooltips_enabled', True):
        return registry_get_tooltip(term, definition)
    return None


def show_uploaded_policy_selector():
    """
    Display a selector for uploaded policies and return the selected policy or None.
    Returns a tuple of (selected_policy_dict, policy_name) or (None, None).
    """
    from core.policy_builder import PolicyLibrary
    
    library = PolicyLibrary()
    all_policies = library.list_policies()
    
    # Filter for uploaded policies, with fallback for legacy saves missing category
    uploaded_policies = []
    for name in all_policies:
        policy = library.get_policy(name)
        if not policy:
            continue
        is_uploaded_category = getattr(policy, "category", "General") == "Uploaded Policies"
        has_uploaded_traits = policy.author == "PDF Upload" or bool(getattr(policy, "structured_mechanics", None))
        if is_uploaded_category or has_uploaded_traits:
            uploaded_policies.append(name)
    
    if not uploaded_policies:
        st.info("📌 No uploaded policies yet. Use the 'Policy Upload' page to extract policies from PDFs.")
        return None, None
    
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_policy_name = st.selectbox(
            "Select an uploaded policy to analyze:",
            uploaded_policies,
            help=get_tooltip(
                "Uploaded Policy Selection",
                "Select a policy you've previously uploaded and extracted from a PDF document. This will apply the policy's parameters to your analysis."
            )
        )
    
    with col2:
        if st.button("🔄 Refresh", key=f"refresh_policy_{selected_policy_name}"):
            st.rerun()
    
    if selected_policy_name:
        policy = library.get_policy(selected_policy_name)
        if policy:
            st.session_state[f"selected_policy_{selected_policy_name}"] = policy
            return policy, selected_policy_name
    
    return None, None


def get_policy_scenario_overrides(policy) -> Dict[str, Dict[str, Any]]:
    """Derive scenario overrides from structured mechanics for modules.

    Returns dict with per-domain adjustments and labels to drive default scenario choices.
    """
    overrides: Dict[str, Dict[str, Any]] = {"revenue": {}, "ss": {}, "medicaid": {}, "discretionary": {}}

    if not policy or not getattr(policy, "structured_mechanics", None):
        return overrides

    mech = policy.structured_mechanics
    tax = mech.get("tax_mechanics") or {}
    ss = mech.get("social_security_mechanics") or {}
    spend = mech.get("spending_mechanics") or {}

    # Revenue overrides
    payroll_rate = tax.get("payroll_tax_rate") or ss.get("payroll_tax_rate")
    corporate_rate = tax.get("corporate_tax_rate")
    if payroll_rate or corporate_rate or tax.get("consumption_tax_rate") or tax.get("carbon_tax_per_ton"):
        overrides["revenue"].update({
            "label": "Policy-derived scenario",
            "payroll_rate": payroll_rate,
            "corporate_rate": corporate_rate,
            "carbon_tax": tax.get("carbon_tax_per_ton"),
            "consumption_tax": tax.get("consumption_tax_rate"),
        })

    # Social Security overrides
    if ss:
        overrides["ss"].update({
            "label": "Policy-derived scenario",
            "payroll_rate": ss.get("payroll_tax_rate"),
            "cap_change": ss.get("payroll_tax_cap_change"),
            "cap_increase": ss.get("payroll_tax_cap_increase"),
            "fra": ss.get("full_retirement_age") or (67 + ss.get("full_retirement_age_change", 0)) if ss.get("full_retirement_age_change") else None,
            "cola_hint": ss.get("cola_adjustments"),
        })

    # Medicaid / discretionary hints for defaults
    if spend:
        overrides["medicaid"].update({
            "label": "Policy-derived scenario",
            "expansion": spend.get("medicaid_expansion"),
            "block_grant": spend.get("medicaid_block_grant"),
            "per_capita_cap": spend.get("medicaid_per_capita_cap"),
            "fmap": spend.get("medicaid_fmap_change"),
        })
        overrides["discretionary"].update({
            "label": "Policy-derived scenario",
            "defense_change": spend.get("defense_spending_change"),
            "nondefense_change": spend.get("nondefense_discretionary_change"),
            "budget_caps": spend.get("budget_caps_enabled"),
        })

    return overrides


def get_column_safe(df: pd.DataFrame, primary: str, fallback: str) -> str:
    """
    Get column name with fallback support for legacy data compatibility.
    
    M1 Fix: Standardized column name resolution across all dashboard pages.
    
    Args:
        df: DataFrame to check
        primary: Preferred column name (modern convention)
        fallback: Legacy column name to use if primary not found
        
    Returns:
        Column name that exists in the DataFrame
        
    Raises:
        KeyError: If neither primary nor fallback exist
    """
    if primary in df.columns:
        return primary
    elif fallback in df.columns:
        return fallback
    else:
        raise KeyError(f"Column not found. Tried '{primary}' and '{fallback}'")


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


def get_policy_library_policies(policy_type=None):
    """Load policies from library (NOT cached - always fresh)."""
    from core.policy_builder import PolicyLibrary, PolicyType
    library = PolicyLibrary()
    if policy_type:
        return library.list_policies_by_type(policy_type), library
    else:
        return library.list_policies(), library


def page_settings():
    """Application settings page."""
    st.title("⚙️ Settings")
    
    # Prepare theme lists once for tab use
    themes = get_theme_list()
    theme_names = [t['name'] for t in themes]
    theme_ids = [t['id'] for t in themes]
    current_theme = st.session_state.settings.get('theme', 'light')
    current_index = theme_ids.index(current_theme) if current_theme in theme_ids else 0

    tabs = st.tabs(["General", "Display", "Themes", "Performance", "Advanced", "Account"])

    with tabs[0]:
        st.subheader("General Preferences")
        language = st.selectbox(
            "Language",
            ["English (US)", "English (UK)", "Spanish (beta)", "French (beta)"],
            index=["English (US)", "English (UK)", "Spanish (beta)", "French (beta)"].index(
                st.session_state.settings.get('language', 'English (US)')
            ),
            help="Choose your preferred language for labels and reports",
        )
        timezone = st.selectbox(
            "Timezone",
            ["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific"],
            index=["UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific"].index(
                st.session_state.settings.get('timezone', 'UTC')
            ),
            help="Set timezone for timestamps and report generation",
        )
        date_format = st.selectbox(
            "Date Format",
            ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"],
            index=["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"].index(
                st.session_state.settings.get('date_format', 'YYYY-MM-DD')
            ),
            help="Preferred display format for dates",
        )
        currency_symbol = st.selectbox(
            "Currency Symbol",
            ["$", "€", "£", "¥"],
            index=["$", "€", "£", "¥"].index(
                st.session_state.settings.get('currency_symbol', '$')
            ),
            help="Default currency indicator for reports and charts",
        )
        st.session_state.settings.update({
            'language': language,
            'timezone': timezone,
            'date_format': date_format,
            'currency_symbol': currency_symbol,
        })

    with tabs[1]:
        st.subheader("Display & Numbers")
        tooltips_enabled = st.toggle(
            "Enable Educational Tooltips",
            value=st.session_state.settings.get('tooltips_enabled', True),
            help="Show helpful explanations when hovering over technical terms",
        )
        st.session_state.settings['tooltips_enabled'] = tooltips_enabled

        # Phase 7.3.3: Chat Panel Settings
        st.divider()
        st.markdown("#### 💬 Chat Panel")
        chat_enabled = st.toggle(
            "Show PoliSim Chat Panel",
            value=st.session_state.settings.get('chat_panel_enabled', True),
            help="Display the AI chat panel on the right side of every page",
        )
        st.session_state.settings['chat_panel_enabled'] = chat_enabled
        
        if chat_enabled:
            chat_width = st.slider(
                "Chat Panel Width",
                min_value=0.15,
                max_value=0.35,
                value=st.session_state.settings.get('chat_panel_width', 0.25),
                step=0.05,
                format="%.0f%%",
                help="Adjust the width of the chat panel (15-35% of screen)",
            )
            # Convert to percentage for display
            st.caption(f"Chat panel takes {int(chat_width * 100)}% of screen width")
            st.session_state.settings['chat_panel_width'] = chat_width
        
        st.divider()

        decimal_places = st.slider(
            "Decimal Places for Numbers",
            min_value=0,
            max_value=3,
            value=st.session_state.settings.get('decimal_places', 1),
            help="Number of decimal places to display in results",
        )
        st.session_state.settings['decimal_places'] = decimal_places

        number_format = st.selectbox(
            "Number Format",
            ["1,234,567.89", "1.234.567,89", "1 234 567.89"],
            index=["1,234,567.89", "1.234.567,89", "1 234 567.89"].index(
                st.session_state.settings.get('number_format', '1,234,567.89')
            ),
            help="Choose thousand and decimal separators",
        )
        abbreviation_style = st.selectbox(
            "Large Number Abbreviation",
            ["Full", "Thousands", "Millions", "Billions"],
            index=["Full", "Thousands", "Millions", "Billions"].index(
                st.session_state.settings.get('abbreviation_style', 'Billions')
            ),
            help="Control how large figures are abbreviated in tables and charts",
        )
        chart_theme = st.selectbox(
            "Chart Theme",
            options=['plotly_white', 'plotly_dark', 'seaborn', 'simple_white'],
            index=['plotly_white', 'plotly_dark', 'seaborn', 'simple_white'].index(
                st.session_state.settings.get('chart_theme', 'plotly_dark')
            ),
            help="Visual theme for all charts and graphs",
        )
        st.session_state.settings.update({
            'number_format': number_format,
            'abbreviation_style': abbreviation_style,
            'chart_theme': chart_theme,
        })

    with tabs[2]:
        st.subheader("Themes & Animations")
        selected_theme_name = st.selectbox(
            "Select Theme",
            options=theme_names,
            index=current_index,
            help="Choose a visual theme for the dashboard",
        )
        selected_theme_id = theme_ids[theme_names.index(selected_theme_name)]
        st.session_state.settings['theme'] = selected_theme_id

        with st.expander("👁️ Preview & Customize Theme", expanded=False):
            enable_custom = st.checkbox(
                "🎨 Enable Custom Colors",
                value=st.session_state.settings.get('custom_theme_enabled', False),
                help="Customize colors for this theme",
            )

            if enable_custom:
                custom_colors = customize_theme_colors(selected_theme_id)
                st.session_state.settings['custom_theme_config'] = custom_colors
                st.session_state.settings['custom_theme_enabled'] = True
                st.markdown("---")
                preview_theme(selected_theme_id, custom_colors)

                if st.button("🔄 Reset to Default Colors"):
                    st.session_state.settings['custom_theme_enabled'] = False
                    st.session_state.settings['custom_theme_config'] = None
                    st.success("Colors reset to defaults!")
                    st.rerun()
            else:
                st.session_state.settings['custom_theme_enabled'] = False
                preview_theme(selected_theme_id)

        from ui.animations import get_animation_config
        anim_config = get_animation_config(selected_theme_id)
        if anim_config['type'] != 'none':
            st.markdown("#### ✨ Animation Settings")
            col1, col2 = st.columns(2)

            with col1:
                animation_enabled = st.toggle(
                    "Enable Animations",
                    value=st.session_state.settings.get('animation_enabled', True),
                    help=f"{anim_config['description']}",
                )
                st.session_state.settings['animation_enabled'] = animation_enabled

            with col2:
                if animation_enabled and anim_config['supports_speed']:
                    animation_speed = st.select_slider(
                        "Animation Speed",
                        options=['slow', 'normal', 'fast'],
                        value=st.session_state.settings.get('animation_speed', 'normal'),
                        help="Adjust animation speed (affects performance)",
                    )
                    st.session_state.settings['animation_speed'] = animation_speed

            if animation_enabled and selected_theme_id == 'matrix':
                st.markdown("#### Matrix Rain Settings")
                matrix_font_size = st.slider(
                    "Rain Text Size",
                    min_value=10,
                    max_value=32,
                    value=st.session_state.settings.get('matrix_font_size', 16),
                    step=2,
                    help="Adjust the size of falling characters (10-32px)",
                )
                st.session_state.settings['matrix_font_size'] = matrix_font_size
                approx_columns = 1920 // matrix_font_size
                st.caption(f"Current: {matrix_font_size}px characters (~{approx_columns} columns on 1920px screen)")

            if animation_enabled:
                st.info("💡 **Performance Tip:** Set to 'slow' or disable animations if experiencing lag.")

        if selected_theme_id in ['matrix', 'cyberpunk', 'dark'] and st.session_state.settings.get('animation_enabled', False):
            st.markdown("#### 🎛️ Background Transparency")
            st.caption("Adjust transparency to balance content readability with animation visibility")
            col1, col2 = st.columns(2)

            with col1:
                bg_opacity = st.slider(
                    "Main Background Opacity",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.settings.get('bg_opacity', 0.6),
                    step=0.05,
                    help="Lower = more animation visible (0.5-0.7 recommended)",
                )
                st.session_state.settings['bg_opacity'] = bg_opacity

            with col2:
                content_opacity = st.slider(
                    "Content Block Opacity",
                    min_value=0.0,
                    max_value=1.0,
                    value=st.session_state.settings.get('content_opacity', 0.8),
                    step=0.05,
                    help="Lower = more animation visible (0.7-0.9 recommended)",
                )
                st.session_state.settings['content_opacity'] = content_opacity

            st.markdown("#### Sidebar & Header Transparency")
            shared_opacity = st.slider(
                "Sidebar & Header Opacity",
                min_value=0.0,
                max_value=1.0,
                value=st.session_state.settings.get('sidebar_opacity', 0.9),
                step=0.05,
                help="Lower = more animation visible through the sidebar and top bar (0.8-0.95 recommended for readability)",
            )
            st.session_state.settings['sidebar_opacity'] = shared_opacity
            st.session_state.settings['header_opacity'] = shared_opacity

            st.caption(
                f"📊 Current: Background {int(bg_opacity*100)}% opaque, "
                f"Content {int(content_opacity*100)}% opaque, "
                f"Sidebar/Header {int(shared_opacity*100)}% opaque",
            )

    with tabs[3]:
        st.subheader("Performance")
        policy_cache_ttl = st.slider(
            "Policy Cache Duration (hours)",
            min_value=1,
            max_value=72,
            value=st.session_state.settings.get('policy_cache_ttl_hours', 24),
            help="How long to cache policy data before refreshing",
        )
        chart_cache_ttl = st.slider(
            "Chart Cache Duration (minutes)",
            min_value=5,
            max_value=120,
            value=st.session_state.settings.get('chart_cache_ttl_minutes', 30),
            help="How long to cache chart data for faster reloads",
        )
        auto_refresh = st.toggle(
            "Auto-refresh data on page load",
            value=st.session_state.settings.get('auto_refresh_data', False),
            help="Refresh cached data each time you open a page (slower, but freshest data)",
        )
        st.session_state.settings.update({
            'policy_cache_ttl_hours': policy_cache_ttl,
            'chart_cache_ttl_minutes': chart_cache_ttl,
            'auto_refresh_data': auto_refresh,
        })

    with tabs[4]:
        st.subheader("Advanced")
        show_advanced = st.toggle(
            "Show Advanced Options",
            value=st.session_state.settings.get('show_advanced_options', False),
            help="Display advanced configuration options in analysis pages",
        )
        debug_mode = st.toggle(
            "Debug Mode",
            value=st.session_state.settings.get('debug_mode', False),
            help="Show additional diagnostics (for troubleshooting)",
        )
        experimental_features = st.toggle(
            "Experimental Features",
            value=st.session_state.settings.get('experimental_features', False),
            help="Enable beta features for testing",
        )
        max_iterations = st.slider(
            "Max Monte Carlo Iterations",
            min_value=10_000,
            max_value=200_000,
            value=st.session_state.settings.get('max_monte_carlo_iterations', 100_000),
            step=5_000,
            help="Upper bound for Monte Carlo runs to prevent runaway jobs",
        )
        st.session_state.settings.update({
            'show_advanced_options': show_advanced,
            'debug_mode': debug_mode,
            'experimental_features': experimental_features,
            'max_monte_carlo_iterations': max_iterations,
        })

    with tabs[5]:
        st.subheader("Account & Sync")
        if StreamlitAuth.is_authenticated():
            user = StreamlitAuth.get_current_user() or {}
            st.markdown(StreamlitAuth.render_user_summary(user))
            st.caption("Preferences sync automatically when saved.")
            if st.button("🚪 Logout", key="settings_logout", use_container_width=True):
                StreamlitAuth.logout(reason="Signed out.")
        else:
            st.info("Login to sync your preferences across devices.")
        st.write("Use the User Profile page for password and API key management.")

    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("✨ Apply Changes", use_container_width=True):
            st.success("Settings applied! Preview your changes.")
            st.rerun()

    with col2:
        if st.button("💾 Save Settings", type="primary", use_container_width=True):
            success, message = save_settings()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with col3:
        if st.button("♻️ Reset to Defaults", use_container_width=True):
            success, message = reset_settings()
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    st.markdown("---")
    st.markdown("### Glossary of Terms")
    
    with st.expander("📚 Social Security Terms", expanded=False):
        st.markdown(
            "\n".join([
                "- **COLA (Cost of Living Adjustment)**: Annual increase in Social Security benefits to account for inflation, typically based on the Consumer Price Index (CPI-W).",
                "- **FRA (Full Retirement Age)**: Age at which a person can claim full Social Security retirement benefits without reduction (currently 67 for those born 1960+).",
                "- **OASI (Old-Age and Survivors Insurance)**: Largest Social Security trust fund, providing retirement and survivor benefits.",
                "- **DI (Disability Insurance)**: Trust fund providing benefits to disabled workers and their families.",
                "- **Payroll Tax Rate**: Combined employer and employee Social Security tax rate (currently 12.4% total).",
                "- **Wage Cap**: Maximum earnings subject to Social Security payroll tax (2025: $168,600).",
                "- **Trust Fund Depletion**: Year when reserves are exhausted and benefits are limited to incoming revenue (~77% of scheduled benefits).",
                "- **Monte Carlo Simulation**: Statistical method running many scenarios with different assumptions to quantify uncertainty.",
            ])
        )
    
    with st.expander("📚 Economic Terms", expanded=False):
        st.markdown(
            "\n".join([
                "- **GDP (Gross Domestic Product)**: Total value of all goods and services produced in the economy.",
                "- **CPI (Consumer Price Index)**: Measure of inflation tracking changes in prices consumers pay for goods and services.",
                "- **Baseline Scenario**: Projection under current law with no policy changes.",
                "- **Fiscal Outlook**: Long-term projection of government revenues, spending, deficits, and debt.",
                "- **Actuarial Balance**: Measure of Social Security's long-term financial status as percentage of taxable payroll.",
            ])
        )
    
    with st.expander("📚 Healthcare Terms", expanded=False):
        st.markdown(
            "\n".join([
                "- **Medicare Part A**: Hospital insurance covering inpatient care.",
                "- **Medicare Part B**: Medical insurance covering doctor visits and outpatient care.",
                "- **Medicare Part D**: Prescription drug coverage.",
                "- **Medicaid**: Joint federal-state program providing health coverage to low-income individuals.",
                "- **USGHA (United States Guaranteed Healthcare Act)**: Proposed comprehensive healthcare reform.",
            ])
        )
    
    st.success("Settings saved automatically!")

def page_overview():
    """Main overview page."""
    st.title("🏛️ CBO 2.0: Open-Source Federal Fiscal Projections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Module Status", "Phase 6.2.5", delta="Security hardening complete")
    with col2:
        st.metric("Monte Carlo Iterations", "100K+", delta="Full uncertainty quantification")
    with col3:
        st.metric("Projection Horizon", "75 years", delta="Long-term sustainability")
    
    st.markdown(
        "\n".join([
            "### What is CBO 2.0?",
            "",
            "An open-source, transparent alternative to the Congressional Budget Office's fiscal projections.",
            "Built with full Monte Carlo stochastic modeling and comprehensive policy analysis.",
            "",
            "**Completed Phases:**",
            "- **Phase 1-4**: Healthcare, Tax Reform, Social Security, Medicare/Medicaid, Revenue, Combined Outlook",
            "- **Phase 5**: Web UI, Launcher, Scenario Builder, Reports, Public API",
            "- **Phase 6.2**: Security hardening (audit, CORS, secrets, auth, DDoS protection)",
            "",
            "**Current Work:**",
            "- Policy extraction enhancements and Combined Outlook policy adaptation",
        ])
    )
    
    st.info(
        "\n".join([
            "📊 **Navigate to other pages using the sidebar:**",
            "- Healthcare Analysis",
            "- Social Security Outlook",
            "- Federal Revenues",
            "- Medicare/Medicaid",
            "- Discretionary Spending",
            "- Combined Fiscal Outlook",
            "- Policy Comparison",
        ])
    )


def page_healthcare():
    """Healthcare policy analysis page (Phase 1)."""
    st.title("🏥 Healthcare Policy Analysis")
    
    st.markdown("""
    Comprehensive healthcare policy simulation with projections for spending, 
    revenue, debt reduction, and key metrics.
    """)
    
    from core.healthcare import get_policy_by_type, PolicyType as HealthcarePolicyType
    from core.policy_builder import PolicyType as PolicyBuilderType
    from core.simulation import simulate_healthcare_years
    
    # Load custom policies from library - ALWAYS FRESH (not cached)
    custom_healthcare_policies, library = get_policy_library_policies(PolicyBuilderType.HEALTHCARE)
    combined_policies = library.list_policies_by_type(PolicyBuilderType.COMBINED)
    
    # Combine built-in and custom policies with visual indicators
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Policy Selection")

        if "policy_category" not in st.session_state:
            st.session_state.policy_category = "Built-in Policies"

        cat_col1, cat_col2 = st.columns(2)
        with cat_col1:
            if st.button(
                "Built-in Policies",
                type="primary" if st.session_state.policy_category == "Built-in Policies" else "secondary",
                key="policy_category_builtin",
                help="Use the bundled healthcare scenarios",
                # width param replaces deprecated use_container_width
                width="stretch",
            ):
                st.session_state.policy_category = "Built-in Policies"
        with cat_col2:
            if st.button(
                "Custom Policies",
                type="primary" if st.session_state.policy_category == "Custom Policies" else "secondary",
                key="policy_category_custom",
                help="Use your saved custom healthcare scenarios",
                width="stretch",
            ):
                st.session_state.policy_category = "Custom Policies"

        policy_category = st.session_state.policy_category
        
        if policy_category == "Built-in Policies":
            selected_display = st.selectbox(
                "Built-in Policy:",
                ["Current US System", "USGHA (Proposed)"],
                help=get_tooltip(
                    "healthcare_policy_builtin",
                    "Choose a built-in healthcare policy for simulation",
                ),
            )
            selected_policy = "current_us" if "Current US" in selected_display else "usgha"
            is_custom = False
        else:
            # Merge dedicated healthcare and combined policies so combined uploads can flow into healthcare simulations
            selectable_custom = custom_healthcare_policies[:]
            for name in combined_policies:
                if name not in selectable_custom:
                    selectable_custom.append(name)

            if not selectable_custom:
                st.info("No custom or combined policies found. Upload or create one in the Library Manager.")
                selected_policy = None
                is_custom = False
            else:
                selected_display = st.selectbox(
                    "Custom Policy:",
                    selectable_custom,
                    help=get_tooltip(
                        "healthcare_policy_custom",
                        "Choose a custom healthcare policy",
                    ),
                )
                selected_policy = selected_display
                is_custom = True
    
    with col2:
        st.subheader("Simulation Parameters")
        years = st.slider(
            "Projection years:",
            min_value=5,
            max_value=30,
            value=22,
            key="healthcare_years",
            help=get_tooltip(
                "healthcare_projection_years",
                "Number of years to simulate",
            ),
        )
        
        # If "Current US System" is selected, fetch real CBO data with live status updates
        if not is_custom and selected_policy == "current_us":
            with st.status("📊 Fetching real-time CBO data...", expanded=True) as status:
                try:
                    from core.cbo_scraper import get_current_us_parameters
                    cbo_params = get_current_us_parameters()
                    if cbo_params:
                        default_gdp = cbo_params['general'].get('gdp', 29.0)
                        default_debt = cbo_params['general'].get('national_debt', 35.0)
                        status.update(
                            label=f"✓ CBO Data Loaded: GDP=${default_gdp:.1f}T, Debt=${default_debt:.1f}T",
                            state="complete",
                            expanded=False,
                        )
                    else:
                        default_gdp = 29.0
                        default_debt = 35.0
                        status.update(
                            label="⚠️ Using default values (CBO data unavailable)",
                            state="error",
                            expanded=False,
                        )
                except Exception as e:
                    default_gdp = 29.0
                    default_debt = 35.0
                    status.update(
                        label=f"⚠️ Using default values (CBO fetch failed: {str(e)})",
                        state="error",
                        expanded=False,
                    )
        else:
            default_gdp = 29.0
            default_debt = 35.0
        
        base_gdp = st.number_input(
            "Base GDP ($T):",
            value=default_gdp,
            min_value=10.0,
            max_value=100.0,
            step=0.5,
            help=get_tooltip(
                "healthcare_base_gdp",
                "Starting GDP in trillions",
            ),
        ) * 1e12
        initial_debt = st.number_input(
            "Initial Debt ($T):",
            value=default_debt,
            min_value=10.0,
            max_value=100.0,
            step=0.5,
            help=get_tooltip(
                "healthcare_initial_debt",
                "Starting national debt in trillions",
            ),
        ) * 1e12
    
    # Show policy details if custom
    if is_custom and selected_policy:
        policy_obj = library.get_policy(selected_policy)
        if policy_obj:
            with st.expander("📋 Custom Policy Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {policy_obj.policy_type.value}")
                    st.write(f"**Category:** {policy_obj.category}")
                    st.write(f"**Author:** {policy_obj.author}")
                with col2:
                    st.write(f"**Created:** {policy_obj.created_date[:10]}")
                    st.write(f"**Parameters:** {len(policy_obj.parameters)}")
                
                st.write(f"**Description:** {policy_obj.description}")
                
                if policy_obj.parameters:
                    st.subheader("Parameters")
                    params_df = pd.DataFrame([
                        {
                            "Parameter": p.name,
                            "Value": f"{p.value:.1f} {p.unit}",
                            "Range": f"[{p.min_value:.1f} - {p.max_value:.1f}]"
                        }
                        for p in policy_obj.parameters.values()
                    ])
                    st.dataframe(params_df, width="stretch")
    
    # Simulation button and results
    if st.button("Run Simulation", type="primary", width="stretch"):
        if is_custom and not selected_policy:
            st.error("Please select a custom policy first")
            st.stop()
        
        try:
            from core.simulation import simulate_healthcare_years
            
            # Load policy - either built-in or custom
            if is_custom:
                # Get custom policy from library
                policy_obj = library.get_policy(selected_policy)
                if not policy_obj:
                    st.error(f"Could not load custom policy: {selected_policy}")
                    st.stop()
                
                # Convert custom policy to healthcare policy for simulation
                try:
                    policy = policy_obj.to_healthcare_policy()
                    st.info(f"Running simulation with custom policy: {policy_obj.name}")
                except Exception as e:
                    st.error(f"Could not convert custom policy to simulation format: {str(e)}")
                    st.stop()
            else:
                # Load built-in policy
                policy = get_policy_by_type(
                    HealthcarePolicyType.USGHA if selected_policy == "usgha" else HealthcarePolicyType.CURRENT_US
                )
            
            # If Current US, fetch and use real CBO data
            cbo_data = None
            if not is_custom and selected_policy == "current_us":
                try:
                    from core.cbo_scraper import get_current_us_parameters
                    cbo_data = get_current_us_parameters()
                    if cbo_data:
                        st.info(f"Using real CBO data: GDP=${cbo_data['general']['gdp']:.1f}T, Debt=${cbo_data['general']['national_debt']:.1f}T")
                except Exception as e:
                    st.warning(f"Could not fetch CBO data: {str(e)}. Using defaults.")
            
            # M5 Fix: Comprehensive error handling with user-friendly messages
            try:
                with st.status("🚀 Initializing simulation...", expanded=True) as sim_status:
                    progress_bar = st.progress(0)
                    progress_bar.progress(0.1)
                    sim_status.update(label="⚙️ Preparing inputs...", state="running", expanded=True)
                    progress_bar.progress(0.2)

                    sim_status.update(label="🧮 Running simulation...", state="running", expanded=True)
                    progress_bar.progress(0.6)
                    results = simulate_healthcare_years(
                        policy=policy,
                        base_gdp=base_gdp,
                        initial_debt=initial_debt,
                        years=years,
                        population=335e6,
                        gdp_growth=0.025,
                        start_year=2025,
                        cbo_data=cbo_data  # Pass CBO data if available
                    )

                    progress_bar.progress(1.0)
                    sim_status.update(
                        label=f"✅ Simulation completed: {len(results)} years",
                        state="complete",
                        expanded=False,
                    )
            except ValueError as e:
                st.error(f"❌ Invalid simulation parameters: {str(e)}")
                st.info("💡 Please check your input values and try again.")
                return
            except TypeError as e:
                st.error(f"❌ Data type error in simulation: {str(e)}")
                st.info("💡 This might be due to incompatible policy parameters.")
                return
            except Exception as e:
                st.error(f"❌ Simulation failed: {str(e)}")
                st.info("💡 Please try a different policy or adjust parameters.")
                st.exception(e)  # Show full traceback in debug mode
                return
            
            if results is None or len(results) == 0:
                st.error("❌ Simulation produced no results.")
                st.info("💡 Try reducing projection years or adjusting policy parameters.")
                return
            
            # Check for partial results
            if len(results) < years:
                st.warning(f"⚠️ Simulation completed only {len(results)} of {years} years. Showing partial results.")
            else:
                st.success(f"✅ Simulation completed: {len(results)} years")
            
            # Summary metrics with legacy + context-aware column support
            st.subheader("Key Metrics")
            col1, col2, col3, col4 = st.columns(4)

            # Column fallbacks
            # M1 Fix: Use standardized column resolution
            spend_col = get_column_safe(results, 'Health Spending ($)', 'Healthcare Spending')
            rev_col = get_column_safe(results, 'Revenue ($)', 'Total Revenue')
            surplus_col = get_column_safe(results, 'Surplus ($)', 'Surplus/Deficit')
            debt_red_col = get_column_safe(results, 'Debt Reduction ($)', 'Debt Reduction')
            debt_col = get_column_safe(results, 'Remaining Debt ($)', 'National Debt')
            per_cap_col = get_column_safe(results, 'Per Capita Health ($)', 'Per Capita Spending')

            with col1:
                total_spending = results[spend_col].sum()
                st.metric("Total Spending", f"${total_spending/1e12:.2f}T", delta=f"{len(results)}-year total")

            with col2:
                final_per_capita = results[per_cap_col].iloc[-1] if per_cap_col in results else float('nan')
                st.metric("Final Per-Capita", f"${final_per_capita:,.0f}", delta=f"Year {years}")

            with col3:
                total_debt_reduction = results[debt_red_col].sum() if debt_red_col in results else 0.0
                st.metric("Debt Reduction", f"${total_debt_reduction/1e12:.2f}T", delta="Total impact")

            with col4:
                final_debt = results[debt_col].iloc[-1]
                st.metric("Final Debt", f"${final_debt/1e12:.2f}T", delta=f"From ${initial_debt/1e12:.1f}T")
            
            # Main visualization: Spending trend
            st.subheader("Healthcare Spending Projection")
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=results['Year'],
                y=results[spend_col]/1e9,
                name='Health Spending',
                line=dict(color='#1f77b4', width=3),
                mode='lines+markers'
            ))
            
            fig.update_layout(
                title=f"Healthcare Spending Over Time - {policy.policy_name}",
                xaxis_title="Year",
                yaxis_title="Spending ($ Billions)",
                hovermode='x unified',
                height=400
            )
            apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig, width="stretch")
            
            # Revenue and surplus analysis
            st.subheader("Revenue & Surplus Analysis")
            fig2 = go.Figure()
            
            fig2.add_trace(go.Scatter(
                x=results['Year'],
                y=results[rev_col]/1e9,
                name='Total Revenue',
                line=dict(color='green', width=2)
            ))
            
            fig2.add_trace(go.Bar(
                x=results['Year'],
                y=results[surplus_col]/1e9,
                name='Annual Surplus',
                marker=dict(color=results[surplus_col].apply(lambda x: 'green' if x > 0 else 'red'))
            ))
            
            fig2.update_layout(
                title="Annual Revenue vs Surplus",
                xaxis_title="Year",
                yaxis_title="Amount ($ Billions)",
                hovermode='x unified',
                height=400
            )
            apply_plotly_theme(fig2, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig2, width="stretch")
            
            # Debt trajectory
            st.subheader("National Debt Trajectory")
            fig3 = go.Figure()
            
            fig3.add_trace(go.Scatter(
                x=results['Year'],
                y=results[debt_col]/1e12,
                name='National Debt',
                line=dict(color='#d62728', width=3),
                mode='lines+markers',
                fill='tozeroy',
                fillcolor='rgba(214, 39, 40, 0.2)'
            ))
            
            fig3.update_layout(
                title="Impact on National Debt",
                xaxis_title="Year",
                yaxis_title="Debt ($ Trillions)",
                hovermode='x unified',
                height=400
            )
            apply_plotly_theme(fig3, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig3, width="stretch")
            
            # Detailed results table
            with st.expander("View Detailed Year-by-Year Results", expanded=False):
                # Format the dataframe for display
                display_df = results.copy()
                display_df['Year'] = display_df['Year'].astype(int)
                # Normalize column names for display
                col_map = {
                    spend_col: 'Spending ($B)',
                    'Healthcare % GDP': 'Health % GDP',
                    'Health % GDP': 'Health % GDP',
                    per_cap_col: 'Per Capita ($)',
                    rev_col: 'Revenue ($B)',
                    surplus_col: 'Surplus ($B)',
                    debt_red_col: 'Debt Reduction ($B)',
                    debt_col: 'Remaining Debt ($T)',
                }

                # Scale values
                if spend_col in display_df:
                    display_df[spend_col] = display_df[spend_col] / 1e9
                if rev_col in display_df:
                    display_df[rev_col] = display_df[rev_col] / 1e9
                if surplus_col in display_df:
                    display_df[surplus_col] = display_df[surplus_col] / 1e9
                if debt_red_col in display_df:
                    display_df[debt_red_col] = display_df[debt_red_col] / 1e9
                if debt_col in display_df:
                    display_df[debt_col] = display_df[debt_col] / 1e12

                display_df = display_df.rename(columns=col_map)
                
                st.dataframe(display_df, width="stretch")
                
                # Download button
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download Results as CSV",
                    data=csv,
                    file_name=f"healthcare_simulation_{selected_policy}.csv",
                    mime="text/csv"
                )
            
            # Interpretation section
            st.subheader("Interpretation & Key Insights")
            
            col1, col2 = st.columns(2)
            
            with col1:
                spending_target_pct = policy.healthcare_spending_target_gdp * 100
                final_health_spend = results[spend_col].iloc[-1] / 1e9
                final_revenue = results[rev_col].iloc[-1] / 1e9
                final_surplus = results[surplus_col].iloc[-1] / 1e9
                st.info(
                    "\n".join([
                        f"**Policy:** {policy.policy_name}",
                        "",
                        f"**Spending Target:** {spending_target_pct:.1f}% of GDP",
                        "",
                        f"**Final Year (Year {years}):",
                        f"- Health Spending: ${final_health_spend:.0f}B",
                        f"- Revenue: ${final_revenue:.0f}B",
                        f"- Surplus: ${final_surplus:.1f}B",
                    ])
                )
            
            with col2:
                debt_change = results[debt_col].iloc[-1] - initial_debt
                debt_change_pct = (debt_change / initial_debt) * 100
                average_surplus = results[surplus_col].mean() / 1e9
                st.info(
                    "\n".join([
                        "**22-Year Impact:**",
                        "",
                        f"- Debt Change: ${debt_change/1e12:.2f}T ({debt_change_pct:+.1f}%)",
                        f"- Total Debt Reduction: ${total_debt_reduction/1e12:.2f}T",
                        f"- Avg Annual Surplus: ${average_surplus:.1f}B",
                        "",
                        f"Circuit Breaker Triggered: {results['Circuit Breaker Triggered'].sum()} times",
                    ])
                )
            
        except Exception as e:
            st.error(f"Error running simulation: {str(e)}")
            st.write(f"Details: {type(e).__name__}")
            import traceback
            with st.expander("Technical Details"):
                st.code(traceback.format_exc())


def page_social_security():
    """Social Security analysis page."""
    st.title("📊 Social Security Trust Fund Projections")
    
    # M6: initialize_settings() now called globally in main()
    
    st.info("💡 This page uses Phase 2 Social Security Monte Carlo engine with full uncertainty quantification.")
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    policy_overrides = get_policy_scenario_overrides(uploaded_policy)
    ss_override = policy_overrides.get("ss", {})
    
    # Baseline defaults used when no uploaded mechanics are present
    BASE_TAX_RATE_PCT = 12.4
    BASE_WAGE_CAP = 168_600
    BASE_FRA = 67
    BASE_COLA_PCT = 3.2

    ss_mechanics = None
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        ss_mechanics = (
            uploaded_policy.structured_mechanics or {}
        ).get("social_security_mechanics") if hasattr(uploaded_policy, "structured_mechanics") else None

        # Prefill controls only when switching to a new uploaded policy
        if ss_mechanics and st.session_state.get("ss_uploaded_policy_applied") != policy_name:
            # Map extracted mechanics into UI defaults
            tax_rate_pct = round((ss_mechanics.get("payroll_tax_rate") or (BASE_TAX_RATE_PCT / 100)) * 100, 3)
            cap_change = ss_mechanics.get("payroll_tax_cap_change")
            cap_increase = ss_mechanics.get("payroll_tax_cap_increase")
            fra_val = ss_mechanics.get("full_retirement_age")
            fra_delta = ss_mechanics.get("full_retirement_age_change")
            cola_hint = ss_mechanics.get("cola_adjustments")

            # Wage cap handling
            use_no_cap_default = cap_change == "remove_cap"
            cap_value_default = BASE_WAGE_CAP
            if use_no_cap_default:
                cap_value_default = BASE_WAGE_CAP
            elif cap_change == "increase_cap" and cap_increase:
                cap_value_default = cap_increase

            # FRA handling
            fra_default = fra_val or (BASE_FRA + fra_delta if fra_delta else BASE_FRA)

            # COLA handling: chained CPI typically implies slightly lower COLA
            cola_default = BASE_COLA_PCT
            if cola_hint == "chained_cpi":
                cola_default = 2.6
            elif cola_hint:
                cola_default = BASE_COLA_PCT

            # Seed session state values so widgets render prefilled
            st.session_state["ss_tax_rate_value"] = tax_rate_pct
            st.session_state["ss_tax_cap_value"] = cap_value_default
            st.session_state["ss_use_no_cap"] = use_no_cap_default
            st.session_state["ss_fra_value"] = fra_default
            st.session_state["ss_cola_value"] = cola_default
            st.session_state["ss_benefit_reduction_value"] = st.session_state.get("ss_benefit_reduction_value", 0)
            st.session_state["ss_uploaded_policy_applied"] = policy_name

        if ss_mechanics:
            with st.expander("📑 Extracted Social Security Mechanics", expanded=False):
                st.write("- Payroll tax rate: {}%".format(round((ss_mechanics.get("payroll_tax_rate") or (BASE_TAX_RATE_PCT/100)) * 100, 2)))
                cap_change = ss_mechanics.get("payroll_tax_cap_change")
                cap_text = "Remove cap" if cap_change == "remove_cap" else (
                    f"Raise cap to ${ss_mechanics.get('payroll_tax_cap_increase'):,.0f}" if cap_change == "increase_cap" and ss_mechanics.get("payroll_tax_cap_increase") else "No change"
                )
                st.write(f"- Payroll tax cap: {cap_text}")
                if ss_mechanics.get("full_retirement_age") or ss_mechanics.get("full_retirement_age_change"):
                    fra_display = ss_mechanics.get("full_retirement_age") or (BASE_FRA + ss_mechanics.get("full_retirement_age_change", 0))
                    st.write(f"- Full retirement age: {fra_display}")
                if ss_mechanics.get("cola_adjustments"):
                    st.write(f"- COLA adjustment: {ss_mechanics.get('cola_adjustments')}")
                if ss_mechanics.get("means_testing_enabled"):
                    threshold = ss_mechanics.get("means_testing_threshold")
                    st.write(f"- Means testing enabled{f' at ${threshold:,.0f}' if threshold else ''}")
                if ss_mechanics.get("benefit_formula_changes"):
                    st.write(f"- Benefit formula changes: {ss_mechanics.get('benefit_formula_changes')}")
    
    st.divider()
    
    # Initialize session state for results
    if 'ss_projections' not in st.session_state:
        st.session_state.ss_projections = None
    if 'ss_solvency' not in st.session_state:
        st.session_state.ss_solvency = None
    if 'ss_reform_name' not in st.session_state:
        st.session_state.ss_reform_name = None
    if 'ss_params_display' not in st.session_state:
        st.session_state.ss_params_display = None
    
    # Create tabs for scenario selection vs custom parameters
    tab1, tab2 = st.tabs(["📋 Quick Scenarios", "🔧 Custom Parameters"])
    
    with tab1:
        st.markdown("### Pre-configured Reform Scenarios")
        
        col1, col2 = st.columns(2)
        with col1:
            quick_options = [
                "Current Law (Baseline)",
                "Raise Payroll Tax",
                "Remove Wage Cap",
                "Raise Retirement Age",
                "Combined Reform",
            ]
            policy_quick_label = None
            if ss_override.get("label"):
                policy_quick_label = f"{ss_override['label']} ({policy_name})" if policy_name else ss_override["label"]
                quick_options = [policy_quick_label] + quick_options
            quick_default_index = 0 if policy_quick_label else 0
            selected_scenario = st.selectbox(
                "Select reform scenario:",
                quick_options,
                index=quick_default_index,
                help=get_tooltip("Reform Scenario", "Compare different Social Security reform proposals to see their impact on trust fund solvency")
            )
        with col2:
            years = st.slider(
                "Projection years:", 
                10, 50, 30, 
                key="quick_years",
                help=get_tooltip("Projection Years", "Number of years to project into the future (Social Security typically uses 75-year window)")
            )
        
        iterations = st.slider(
            "Monte Carlo iterations:", 
            100, 5000, 1000, 
            step=100, 
            key="quick_iterations",
            help=get_tooltip("Monte Carlo Iterations", "Number of simulation runs with varying assumptions to capture uncertainty (more iterations = more accurate but slower)")
        )
        
        run_quick = st.button("Run Quick Scenario", type="primary", key="run_quick")
    
    with tab2:
        st.markdown("### Customize Parameters")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Trust Fund Parameters**")
            custom_tax_rate = st.number_input(
                "Payroll Tax Rate (%)", 
                min_value=10.0,
                max_value=20.0,
                value=st.session_state.get("ss_tax_rate_value", BASE_TAX_RATE_PCT),
                step=0.1,
                key="ss_tax_rate_value",
                help=get_tooltip("Payroll Tax Rate", "Combined employer + employee Social Security tax rate. Current law: 12.4% (6.2% each)")
            ) / 100
            custom_tax_cap = st.number_input(
                "Payroll Tax Cap ($)", 
                min_value=0,
                max_value=1_000_000,
                value=int(st.session_state.get("ss_tax_cap_value", BASE_WAGE_CAP)),
                step=1000,
                key="ss_tax_cap_value",
                help=get_tooltip("Payroll Tax Cap", "Maximum annual earnings subject to Social Security tax. 2025 cap: $168,600. Earnings above this are not taxed.")
            )
            use_no_cap = st.checkbox(
                "Remove wage cap (override value above)",
                value=st.session_state.get("ss_use_no_cap", False),
                key="ss_use_no_cap",
                help=get_tooltip("Remove Wage Cap", "Eliminate the earnings cap so all wages are taxed for Social Security, increasing revenue by ~20%")
            )
            custom_interest = st.number_input(
                "Trust Fund Interest Rate (%)", 
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.get("ss_interest_value", 3.5),
                step=0.1,
                key="ss_interest_value",
                help=get_tooltip("Interest Rate", "Annual interest rate earned on trust fund reserves invested in special Treasury securities")
            ) / 100
        
        with col2:
            st.markdown("**Benefit Formula Parameters**")
            custom_fra = st.number_input(
                "Full Retirement Age", 
                min_value=62,
                max_value=75,
                value=int(st.session_state.get("ss_fra_value", BASE_FRA)),
                step=1,
                key="ss_fra_value",
                help=get_tooltip("Full Retirement Age (FRA)", "Age at which workers can claim full retirement benefits without reduction. Currently 67 for those born 1960+. Raising FRA reduces costs by ~6.7% per year.")
            )
            custom_cola = st.number_input(
                "Annual COLA (%)", 
                min_value=0.0,
                max_value=10.0,
                value=st.session_state.get("ss_cola_value", BASE_COLA_PCT),
                step=0.1,
                key="ss_cola_value",
                help=get_tooltip("COLA", "Cost of Living Adjustment - annual increase in benefits to account for inflation. Based on CPI-W (Consumer Price Index for Urban Wage Earners).")
            ) / 100
            benefit_reduction = st.slider(
                "Benefit Reduction (%)", 
                0,
                50,
                int(st.session_state.get("ss_benefit_reduction_value", 0)),
                step=5,
                key="ss_benefit_reduction_value",
                help=get_tooltip("Benefit Reduction", "Across-the-board percentage reduction in all Social Security benefits. A painful but direct way to reduce costs.")
            )
        
        col3, col4 = st.columns(2)
        with col3:
            custom_years = st.slider("Projection years:", 10, 50, 30, key="custom_years")
        with col4:
            custom_iterations = st.slider("Monte Carlo iterations:", 100, 5000, 1000, step=100, key="custom_iterations")
        
        run_custom = st.button("Run Custom Scenario", type="primary", key="run_custom")
        run_uploaded_policy = False
        if ss_mechanics:
            run_uploaded_policy = st.button("Apply Uploaded Policy & Run", type="secondary", key="run_ss_uploaded")
    
    # Determine which scenario to run
    if run_quick:
        with st.status("🚀 Running Social Security projections...", expanded=True) as status:
            progress = st.progress(0.05)
            try:
                status.update(label="⚙️ Initializing model...", state="running", expanded=True)
                progress.progress(0.15)

                # Initialize model with reform parameters
                params_display = {}
                use_policy_quick = policy_quick_label and selected_scenario == policy_quick_label

                if use_policy_quick:
                    trust_fund = TrustFundAssumptions()
                    trust_fund.payroll_tax_rate = ss_override.get("payroll_rate") or trust_fund.payroll_tax_rate
                    cap_change = ss_override.get("cap_change")
                    if cap_change == "remove_cap":
                        trust_fund.payroll_tax_cap = None
                    elif cap_change == "increase_cap" and ss_override.get("cap_increase"):
                        trust_fund.payroll_tax_cap = ss_override.get("cap_increase")
                    benefit_formula = BenefitFormula()
                    fra_value = ss_override.get("fra") or BASE_FRA
                    benefit_formula.full_retirement_age = fra_value
                    cola_hint = ss_override.get("cola_hint")
                    if cola_hint == "chained_cpi":
                        benefit_formula.annual_cola = 0.026
                    model = SocialSecurityModel(trust_fund=trust_fund, benefit_formula=benefit_formula)
                    reform_name = "Uploaded Policy"
                    params_display = {
                        "Payroll Tax Rate": f"{trust_fund.payroll_tax_rate*100:.1f}%" if trust_fund.payroll_tax_rate else "12.4%",
                        "Payroll Tax Cap": "No Cap" if trust_fund.payroll_tax_cap is None else f"${trust_fund.payroll_tax_cap:,}",
                        "Full Retirement Age": str(benefit_formula.full_retirement_age),
                        "COLA": f"{benefit_formula.annual_cola*100:.1f}%",
                    }
                elif selected_scenario == "Current Law (Baseline)":
                    model = SocialSecurityModel()
                    reform_name = "Current Law"
                    params_display = {
                        "Payroll Tax Rate": "12.4%",
                        "Payroll Tax Cap": "$168,600",
                        "Full Retirement Age": "67",
                        "COLA": "3.2%"
                    }
                elif selected_scenario == "Raise Payroll Tax":
                    trust_fund = TrustFundAssumptions()
                    trust_fund.payroll_tax_rate = 0.145
                    model = SocialSecurityModel(trust_fund=trust_fund)
                    reform_name = "Raise Payroll Tax to 14.5%"
                    params_display = {
                        "Payroll Tax Rate": "14.5% ⬆️",
                        "Payroll Tax Cap": "$168,600",
                        "Full Retirement Age": "67",
                        "COLA": "3.2%"
                    }
                elif selected_scenario == "Remove Wage Cap":
                    trust_fund = TrustFundAssumptions()
                    trust_fund.payroll_tax_cap = None
                    model = SocialSecurityModel(trust_fund=trust_fund)
                    reform_name = "Remove Wage Cap"
                    params_display = {
                        "Payroll Tax Rate": "12.4%",
                        "Payroll Tax Cap": "No Cap ⬆️",
                        "Full Retirement Age": "67",
                        "COLA": "3.2%"
                    }
                elif selected_scenario == "Raise Retirement Age":
                    benefit_formula = BenefitFormula()
                    benefit_formula.full_retirement_age = 69
                    model = SocialSecurityModel(benefit_formula=benefit_formula)
                    reform_name = "Raise Retirement Age to 69"
                    params_display = {
                        "Payroll Tax Rate": "12.4%",
                        "Payroll Tax Cap": "$168,600",
                        "Full Retirement Age": "69 ⬆️",
                        "COLA": "3.2%"
                    }
                elif selected_scenario == "Combined Reform":
                    trust_fund = TrustFundAssumptions()
                    trust_fund.payroll_tax_rate = 0.135
                    benefit_formula = BenefitFormula()
                    benefit_formula.full_retirement_age = 68
                    model = SocialSecurityModel(trust_fund=trust_fund, benefit_formula=benefit_formula)
                    reform_name = "Combined Reform Package"
                    params_display = {
                        "Payroll Tax Rate": "13.5% ⬆️",
                        "Payroll Tax Cap": "$168,600",
                        "Full Retirement Age": "68 ⬆️",
                        "COLA": "3.2%"
                    }
                else:
                    model = SocialSecurityModel()
                    reform_name = "Unknown"
                    params_display = {}

                progress.progress(0.35)
                status.update(label="🧮 Running projections...", state="running", expanded=True)
                projections = model.project_trust_funds(years=years, iterations=iterations)
                progress.progress(0.7)
                status.update(label="📈 Estimating solvency dates...", state="running", expanded=True)
                solvency = model.estimate_solvency_dates(projections)
                progress.progress(0.9)
                
                # Store in session state
                st.session_state.ss_projections = projections
                st.session_state.ss_solvency = solvency
                st.session_state.ss_reform_name = reform_name
                st.session_state.ss_params_display = params_display
                progress.progress(1.0)
                status.update(
                    label=f"✅ Completed {iterations:,} iterations over {years} years",
                    state="complete",
                    expanded=False,
                )
                st.success(f"✅ Completed {iterations:,} iterations over {years} years")
                
            except ValueError as e:
                status.update(label="❌ Invalid projection parameters", state="error", expanded=True)
                st.error(f"❌ Invalid projection parameters: {str(e)}")
                st.info("💡 Check tax rates, interest rates, and benefit parameters.")
                return
            except TypeError as e:
                status.update(label="❌ Data type error", state="error", expanded=True)
                st.error(f"❌ Data type error: {str(e)}")
                st.info("💡 Ensure all numeric parameters are valid numbers.")
                return
            except Exception as e:
                status.update(label="❌ Projection failed", state="error", expanded=True)
                st.error(f"❌ Projection failed: {str(e)}")
                st.info("💡 Try reducing iterations or projection years.")
                st.exception(e)
                return
    
    elif run_custom or run_uploaded_policy:
        should_run = True
        with st.status("🚀 Running custom Social Security projections...", expanded=True) as status:
            progress = st.progress(0.05)
            try:
                status.update(label="⚙️ Building custom model...", state="running", expanded=True)
                progress.progress(0.2)
                # Build custom model seeded either from user sliders or uploaded mechanics
                tf_rate = custom_tax_rate
                tf_cap = None if use_no_cap else custom_tax_cap
                fra_val = custom_fra
                cola_val = custom_cola
                benefit_reduction_val = benefit_reduction

                if run_uploaded_policy and ss_mechanics:
                    # Payroll tax rate
                    if ss_mechanics.get("payroll_tax_rate"):
                        tf_rate = ss_mechanics.get("payroll_tax_rate")
                    # Cap handling
                    cap_change = ss_mechanics.get("payroll_tax_cap_change")
                    if cap_change == "remove_cap":
                        tf_cap = None
                    elif cap_change == "increase_cap" and ss_mechanics.get("payroll_tax_cap_increase"):
                        tf_cap = ss_mechanics.get("payroll_tax_cap_increase")
                    # FRA
                    if ss_mechanics.get("full_retirement_age"):
                        fra_val = ss_mechanics.get("full_retirement_age")
                    elif ss_mechanics.get("full_retirement_age_change"):
                        fra_val = BASE_FRA + ss_mechanics.get("full_retirement_age_change")
                    # COLA hint
                    cola_hint = ss_mechanics.get("cola_adjustments")
                    if cola_hint == "chained_cpi":
                        cola_val = 0.026
                    elif cola_hint:
                        cola_val = BASE_COLA_PCT / 100.0

                trust_fund = TrustFundAssumptions()
                trust_fund.payroll_tax_rate = tf_rate
                trust_fund.payroll_tax_cap = tf_cap
                trust_fund.trust_fund_interest_rate = custom_interest
                
                benefit_formula = BenefitFormula()
                benefit_formula.full_retirement_age = int(fra_val)
                benefit_formula.annual_cola = cola_val
                if benefit_reduction_val > 0:
                    benefit_formula.primary_insurance_amount_avg_2025 *= (1 - benefit_reduction_val / 100)
                
                model = SocialSecurityModel(trust_fund=trust_fund, benefit_formula=benefit_formula)
                reform_name = "Uploaded Policy" if run_uploaded_policy else "Custom Parameters"
                
                params_display = {
                    "Payroll Tax Rate": f"{tf_rate*100:.1f}%",
                    "Payroll Tax Cap": "No Cap" if tf_cap is None else f"${tf_cap:,}",
                    "Full Retirement Age": str(fra_val),
                    "COLA": f"{cola_val*100:.1f}%",
                    "Interest Rate": f"{custom_interest*100:.1f}%",
                    "Benefit Reduction": f"{benefit_reduction_val}%" if benefit_reduction_val > 0 else "None"
                }
                
                progress.progress(0.45)
                status.update(label="🧮 Running projections...", state="running", expanded=True)
                projections = model.project_trust_funds(years=custom_years, iterations=custom_iterations)
                
                if projections is None or len(projections) == 0:
                    status.update(label="⚠️ Projection returned no results", state="error", expanded=True)
                    st.error("❌ Projection produced no results.")
                    st.info("💡 Try different parameters or reduce projection years.")
                    return
                
                progress.progress(0.75)
                status.update(label="📈 Estimating solvency dates...", state="running", expanded=True)
                solvency = model.estimate_solvency_dates(projections)
                
                # Store in session state
                st.session_state.ss_projections = projections
                st.session_state.ss_solvency = solvency
                st.session_state.ss_reform_name = reform_name
                st.session_state.ss_params_display = params_display
                progress.progress(1.0)
                status.update(
                    label=f"✅ Completed {custom_iterations:,} iterations over {custom_years} years",
                    state="complete",
                    expanded=False,
                )
                st.success(f"✅ Completed {custom_iterations:,} iterations over {custom_years} years")
                
            except ValueError as e:
                status.update(label="❌ Invalid custom parameters", state="error", expanded=True)
                st.error(f"❌ Invalid custom parameters: {str(e)}")
                st.info("💡 Check that all values are within reasonable ranges.")
                return
            except TypeError as e:
                status.update(label="❌ Data type error", state="error", expanded=True)
                st.error(f"❌ Data type error: {str(e)}")
                st.info("💡 Ensure all parameters are valid numbers.")
                return
            except Exception as e:
                status.update(label="❌ Custom projection failed", state="error", expanded=True)
                st.error(f"❌ Custom projection failed: {str(e)}")
                st.info("💡 Try simpler parameters or contact support.")
                st.exception(e)
                return
    
    # Display results if available
    if st.session_state.ss_projections is not None:
        st.markdown("---")
        st.subheader(f"Results: {st.session_state.ss_reform_name}")
        
        # Show parameters used
        if st.session_state.ss_params_display:
            with st.expander("📋 Parameters Used", expanded=False):
                param_cols = st.columns(len(st.session_state.ss_params_display))
                for idx, (key, val) in enumerate(st.session_state.ss_params_display.items()):
                    with param_cols[idx]:
                        st.metric(key, val)
        
        projections = st.session_state.ss_projections
        solvency = st.session_state.ss_solvency
        reform_name = st.session_state.ss_reform_name
        projections = st.session_state.ss_projections
        solvency = st.session_state.ss_solvency
        reform_name = st.session_state.ss_reform_name
        
        # Display solvency metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            oasi_data = solvency.get('OASI', {})
            depl_year = oasi_data.get('depletion_year_mean')
            prob_depl = oasi_data.get('probability_depleted', 0)
            
            if depl_year and not np.isnan(depl_year):
                st.metric(
                    "OASI Depletion Year",
                    f"{int(depl_year)}",
                    delta=f"{prob_depl*100:.0f}% prob",
                    delta_color="inverse"
                )
            else:
                st.metric("OASI Status", "✅ Solvent", delta="No depletion")
        
        with col2:
            di_data = solvency.get('DI', {})
            di_depl = di_data.get('depletion_year_mean')
            di_prob = di_data.get('probability_depleted', 0)
            
            if di_depl and not np.isnan(di_depl):
                st.metric(
                    "DI Depletion Year",
                    f"{int(di_depl)}",
                    delta=f"{di_prob*100:.0f}% prob",
                    delta_color="inverse"
                )
            else:
                st.metric("DI Status", "✅ Solvent", delta="No depletion")
        
        with col3:
            combined_data = solvency.get('Combined', {})
            comb_depl = combined_data.get('depletion_year_mean')
            
            if comb_depl and not np.isnan(comb_depl):
                st.metric("Combined Depletion", f"{int(comb_depl)}", delta_color="inverse")
            else:
                st.metric("Combined Status", "✅ Solvent")
        
        # Chart with corrected column names
        if len(projections) > 0:
            fig = go.Figure()
            
            # M1 Fix: Use standardized column resolution with fallbacks
            oasi_balance_col = get_column_safe(projections, 'oasi_balance_billions', 'OASI Balance')
            di_balance_col = get_column_safe(projections, 'di_balance_billions', 'DI Balance')
            
            # OASI Balance
            oasi_mean = projections.groupby('year')[oasi_balance_col].mean()
            oasi_std = projections.groupby('year')[oasi_balance_col].std()
            years_arr = oasi_mean.index
            
            fig.add_trace(go.Scatter(
                x=years_arr,
                y=oasi_mean,
                mode='lines',
                name='OASI Balance (Mean)',
                line=dict(color='#1f77b4', width=3)
            ))
            
            # Confidence band
            fig.add_trace(go.Scatter(
                x=list(years_arr) + list(years_arr)[::-1],
                y=list(oasi_mean + oasi_std) + list(oasi_mean - oasi_std)[::-1],
                fill='toself',
                fillcolor='rgba(31, 119, 180, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='±1 Std Dev',
                showlegend=True
            ))
            
            # DI Balance
            di_mean = projections.groupby('year')[di_balance_col].mean()
            fig.add_trace(go.Scatter(
                x=years_arr,
                y=di_mean,
                mode='lines',
                name='DI Balance (Mean)',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            
            fig.update_layout(
                title=f"Social Security Trust Fund Balances - {reform_name}",
                xaxis_title="Year",
                yaxis_title="Balance ($ Billions)",
                hovermode='x unified',
                height=500
            )
            apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig, width="stretch")
            
            # Summary statistics
            st.subheader("Projection Summary")
            final_year = projections['year'].max()
            final_oasi = oasi_mean.iloc[-1]
            final_di = di_mean.iloc[-1]
            
            summary_data = {
                "Metric": [
                    "Monte Carlo Iterations",
                    "Years Projected",
                    f"Final OASI Balance ({int(final_year)})",
                    f"Final DI Balance ({int(final_year)})",
                    "OASI Depletion Risk",
                    "DI Depletion Risk"
                ],
                "Value": [
                    f"{len(projections['iteration'].unique()):,}",
                    f"{int(final_year - projections['year'].min())} years",
                    f"${final_oasi:,.1f}B" if final_oasi > 0 else f"-${abs(final_oasi):,.1f}B (depleted)",
                    f"${final_di:,.1f}B" if final_di > 0 else f"-${abs(final_di):,.1f}B (depleted)",
                    f"{prob_depl*100:.0f}%" if not np.isnan(depl_year or 0) else "0%",
                    f"{di_prob*100:.0f}%" if not np.isnan(di_depl or 0) else "0%"
                ]
            }
            st.dataframe(pd.DataFrame(summary_data), hide_index=True, width="stretch")


def page_federal_revenues():
    """Federal revenues page."""
    st.title("💰 Federal Revenue Projections")
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    policy_overrides = get_policy_scenario_overrides(uploaded_policy)
    revenue_override = policy_overrides.get("revenue", {})
    
    tax_mechanics = None
    ss_mechanics = None
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        if hasattr(uploaded_policy, "structured_mechanics") and uploaded_policy.structured_mechanics:
            tax_mechanics = uploaded_policy.structured_mechanics.get("tax_mechanics")
            ss_mechanics = uploaded_policy.structured_mechanics.get("social_security_mechanics")
        if tax_mechanics:
            with st.expander("📑 Extracted Tax Mechanics", expanded=False):
                if tax_mechanics.get("payroll_tax_rate"):
                    st.write(f"- Payroll tax: {tax_mechanics['payroll_tax_rate']*100:.2f}%")
                if tax_mechanics.get("corporate_tax_rate"):
                    st.write(f"- Corporate rate: {tax_mechanics['corporate_tax_rate']*100:.2f}%")
                if tax_mechanics.get("consumption_tax_rate"):
                    st.write(f"- Consumption/VAT: {tax_mechanics['consumption_tax_rate']*100:.2f}%")
                if tax_mechanics.get("carbon_tax_per_ton"):
                    st.write(f"- Carbon tax: ${tax_mechanics['carbon_tax_per_ton']}/ton")
    
    st.divider()
    
    revenue_scenarios = load_revenue_scenarios()
    scenario_names = list(revenue_scenarios["scenarios"].keys())
    baseline_scenario = next((n for n in scenario_names if "baseline" in n.lower()), scenario_names[0])

    policy_scenario_name = None
    if revenue_override.get("label"):
        policy_scenario_name = f"{revenue_override['label']} ({policy_name})" if policy_name else revenue_override["label"]
    
    col1, col2 = st.columns(2)
    with col1:
        scenario_options = scenario_names.copy()
        default_index = 0
        if policy_scenario_name:
            scenario_options = [policy_scenario_name] + scenario_options
            default_index = 0
        else:
            default_index = scenario_options.index(baseline_scenario) if baseline_scenario in scenario_options else 0
        selected_scenario = st.selectbox(
            "Select economic scenario:",
            scenario_options,
            index=default_index,
            help=get_tooltip(
                "revenue_economic_scenario",
                "Pre-defined combinations of GDP growth, wage growth, and other economic assumptions that affect revenue projections",
            ),
        )
    with col2:
        years = st.slider(
            "Projection years:", 
            5, 30, 10,
            help=get_tooltip(
                "revenue_projection_years",
                "Number of years into the future to project federal revenues. CBO typically uses 10-year budget window",
            ),
        )
    
    iterations = st.slider(
        "Monte Carlo iterations:", 
        1000, 50000, 10000, step=1000,
        help=get_tooltip(
            "revenue_iterations",
            "Number of simulation runs with varying economic assumptions to capture uncertainty. More iterations = more accurate confidence intervals but slower",
        ),
    )
    
    if st.button("Project Federal Revenues"):
        from core.revenue_modeling import PayrollTaxAssumptions, CorporateIncomeTaxAssumptions

        payroll_assump = PayrollTaxAssumptions.ssa_2024_trustees()
        corp_assump = CorporateIncomeTaxAssumptions.cbo_2025_baseline()

        # Map extracted mechanics to revenue assumptions
        payroll_rate = None
        if tax_mechanics and tax_mechanics.get("payroll_tax_rate"):
            payroll_rate = tax_mechanics.get("payroll_tax_rate")
        if not payroll_rate and ss_mechanics and ss_mechanics.get("payroll_tax_rate"):
            payroll_rate = ss_mechanics.get("payroll_tax_rate")
        if payroll_rate:
            # Model uses employee share; split combined rate in half
            payroll_assump.social_security_rate = payroll_rate / 2
        if tax_mechanics and tax_mechanics.get("corporate_tax_rate"):
            corp_assump.marginal_tax_rate = tax_mechanics.get("corporate_tax_rate")
            corp_assump.effective_tax_rate = max(0.01, corp_assump.marginal_tax_rate * 0.65)
        # Apply policy-derived overrides even if mechanics not explicitly mapped above
        if revenue_override.get("payroll_rate") and not payroll_rate:
            payroll_assump.social_security_rate = revenue_override.get("payroll_rate") / 2
        if revenue_override.get("corporate_rate") and not (tax_mechanics and tax_mechanics.get("corporate_tax_rate")):
            corp_assump.marginal_tax_rate = revenue_override.get("corporate_rate")
            corp_assump.effective_tax_rate = max(0.01, corp_assump.marginal_tax_rate * 0.65)

        model = FederalRevenueModel(payroll_taxes=payroll_assump, corporate_income_tax=corp_assump)
        use_policy_scenario = policy_scenario_name and selected_scenario == policy_scenario_name
        scenario_key = baseline_scenario if use_policy_scenario else selected_scenario
        scenario = revenue_scenarios["scenarios"].get(scenario_key, revenue_scenarios["scenarios"][baseline_scenario])
        
        with st.spinner("Running revenue projections..."):
            gdp_growth = np.array(scenario["economic_assumptions"]["gdp_real_growth_annual"][:years])
            wage_growth = np.array(scenario["economic_assumptions"]["wage_growth_annual"][:years])
            
            revenues = model.project_all_revenues(
                years=years,
                gdp_growth=gdp_growth,
                wage_growth=wage_growth,
                iterations=iterations
            )

        if use_policy_scenario:
            with st.expander("Policy-derived revenue adjustments", expanded=False):
                if revenue_override.get("payroll_rate"):
                    st.write(f"- Payroll tax rate set to {revenue_override['payroll_rate']*100:.2f}%")
                if revenue_override.get("corporate_rate"):
                    st.write(f"- Corporate tax rate set to {revenue_override['corporate_rate']*100:.2f}%")
                if revenue_override.get("consumption_tax"):
                    st.write(f"- Consumption/VAT noted at {revenue_override['consumption_tax']*100:.2f}% (not yet modeled)")
                if revenue_override.get("carbon_tax"):
                    st.write(f"- Carbon tax detected: ${revenue_override['carbon_tax']}/ton (not yet modeled)")
        
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
                hovermode='x unified'
            )
            apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig, width="stretch")


def page_medicare_medicaid():
    """Medicare/Medicaid page."""
    st.title("🏥 Medicare & Medicaid Projections")
    from core.medicare_medicaid import MedicareModel, MedicaidModel, MedicaidAssumptions
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    medicaid_mechanics = None
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        medicaid_mechanics = None
        if hasattr(uploaded_policy, "structured_mechanics") and uploaded_policy.structured_mechanics:
            medicaid_mechanics = uploaded_policy.structured_mechanics.get("spending_mechanics")
        if medicaid_mechanics:
            with st.expander("📑 Extracted Medicaid/Spending Mechanics", expanded=False):
                st.write(f"- Medicaid expansion: {'Yes' if medicaid_mechanics.get('medicaid_expansion') else 'No/Not detected'}")
                st.write(f"- Block grant: {'Yes' if medicaid_mechanics.get('medicaid_block_grant') else 'No'}")
                st.write(f"- Per-capita cap: {'Yes' if medicaid_mechanics.get('medicaid_per_capita_cap') else 'No'}")
                fmap = medicaid_mechanics.get("medicaid_fmap_change")
                if fmap is not None:
                    st.write(f"- FMAP change: {fmap:+.1f} percentage points")
                if medicaid_mechanics.get("medicaid_waivers"):
                    st.write("- Section 1115/waiver activity detected")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["Medicare", "Medicaid"])
    
    with tab1:
        st.subheader("Medicare Parts A/B/D Projections")
        
        years = st.slider(
            "Medicare projection years:", 
            5, 30, 10, 
            key="medicare_years",
            help=get_tooltip(
                "medicare_projection_years",
                "Number of years to project Medicare spending. Trustees report uses 75-year window but 10-30 years is typical for budget analysis",
            )
        )
        iterations = st.slider(
            "Medicare iterations:", 
            1000, 30000, 10000, 
            step=1000, 
            key="medicare_iter",
            help=get_tooltip(
                "medicare_iterations",
                "Number of simulation runs with varying assumptions (enrollment growth, cost trends, etc.). More iterations = smoother confidence bands",
            )
        )
        
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
                hovermode='x unified'
            )
            apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig, width="stretch")
    
    with tab2:
        st.subheader("Medicaid Spending Projections")
        
        years = st.slider(
            "Medicaid projection years:", 
            5, 30, 10, 
            key="medicaid_years",
            help=get_tooltip(
                "medicaid_projection_years",
                "Number of years to project Medicaid spending. Medicaid is jointly funded by federal and state governments",
            )
        )
        iterations = st.slider(
            "Medicaid iterations:", 
            1000, 30000, 10000, 
            step=1000, 
            key="medicaid_iter",
            help=get_tooltip(
                "medicaid_iterations",
                "Number of simulation runs with varying assumptions about enrollment and per-capita costs. Medicaid enrollment is more volatile than Medicare",
            )
        )
        
        if st.button("Project Medicaid"):
            assumptions = MedicaidAssumptions()
            if medicaid_mechanics:
                if medicaid_mechanics.get("medicaid_expansion"):
                    assumptions.medicaid_expansion_enrollment *= 1.2
                    assumptions.total_medicaid_spending *= 1.1
                if medicaid_mechanics.get("medicaid_block_grant"):
                    assumptions.medicaid_cost_growth_annual = 0.02
                if medicaid_mechanics.get("medicaid_per_capita_cap"):
                    assumptions.medicaid_cost_growth_annual = min(assumptions.medicaid_cost_growth_annual, 0.02)
                fmap = medicaid_mechanics.get("medicaid_fmap_change")
                if fmap is not None:
                    assumptions.federal_medicaid_spending *= (1 + fmap / 100)
                if medicaid_mechanics.get("medicaid_waivers"):
                    assumptions.long_term_care_growth_annual = max(0.025, assumptions.long_term_care_growth_annual - 0.005)

            model = MedicaidModel(assumptions=assumptions)
            
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
                hovermode='x unified'
            )
            apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
            
            st.plotly_chart(fig, width="stretch")


def page_discretionary_spending():
    """Discretionary spending analysis page."""
    st.title("💰 Federal Discretionary Spending")
    from core.discretionary_spending import DiscretionarySpendingModel, DiscretionaryAssumptions
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    discretionary_mechanics = None
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        if hasattr(uploaded_policy, "structured_mechanics") and uploaded_policy.structured_mechanics:
            discretionary_mechanics = uploaded_policy.structured_mechanics.get("spending_mechanics")
        if discretionary_mechanics:
            with st.expander("📑 Extracted Spending Mechanics", expanded=False):
                if discretionary_mechanics.get("defense_spending_change") is not None:
                    st.write(f"- Defense change: {discretionary_mechanics.get('defense_spending_change')*100:+.1f}%")
                if discretionary_mechanics.get("nondefense_discretionary_change") is not None:
                    st.write(f"- Non-defense change: {discretionary_mechanics.get('nondefense_discretionary_change')*100:+.1f}%")
                if discretionary_mechanics.get("budget_caps_enabled"):
                    st.write(f"- Budget caps enabled: {discretionary_mechanics.get('budget_cap_levels', {})}")
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    # Map extracted spending mechanics to default scenario suggestions
    defense_default = "baseline"
    nondefense_default = "baseline"
    if discretionary_mechanics:
        defense_delta = discretionary_mechanics.get("defense_spending_change")
        if defense_delta is not None:
            if defense_delta > 0.01:
                defense_default = "growth"
            elif defense_delta < -0.01:
                defense_default = "reduction"
        nondef_delta = discretionary_mechanics.get("nondefense_discretionary_change")
        if nondef_delta is not None:
            if nondef_delta > 0.01:
                nondefense_default = "growth"
            elif nondef_delta < -0.01:
                nondefense_default = "reduction"

    with col1:
        defense_scenario = st.selectbox(
            "Defense Scenario:",
            ["baseline", "growth", "reduction"],
            index=["baseline", "growth", "reduction"].index(defense_default),
            help=get_tooltip(
                "defense_scenario",
                "baseline=inflation only (~2%), growth=+3.5% annually, reduction=+1.5% annually. Defense is ~50% of discretionary spending",
            ),
        )
    with col2:
        nondefense_scenario = st.selectbox(
            "Non-Defense Scenario:",
            ["baseline", "growth", "reduction", "infrastructure"],
            index=["baseline", "growth", "reduction", "infrastructure"].index(nondefense_default) if nondefense_default in ["baseline", "growth", "reduction", "infrastructure"] else 0,
            help=get_tooltip(
                "nondefense_scenario",
                "baseline=inflation only (~2%), growth=+3.5% annually, reduction=+1.5% annually. Defense is ~50% of discretionary spending",
            ),
        )
    with col3:
        years = st.slider(
            "Projection years:", 
            5,
            30,
            10,
            key="discret_years",
            help=get_tooltip(
                "discretionary_projection_years",
                "Discretionary spending requires annual Congressional appropriations, making long-term projections uncertain",
            ),
        )
    
    iterations = st.slider(
        "Monte Carlo iterations:", 
        1000, 50000, 10000, 
        step=1000, 
        key="discret_iter",
        help=get_tooltip("Monte Carlo Iterations", "Number of simulation runs. Discretionary spending has high variance due to policy changes and emergencies")
    )
    
    if st.button("Project Discretionary Spending"):
        assumptions = DiscretionaryAssumptions()
        if discretionary_mechanics:
            if discretionary_mechanics.get("defense_spending_change") is not None:
                assumptions.defense_2025_billions *= (1 + discretionary_mechanics.get("defense_spending_change"))
            if discretionary_mechanics.get("nondefense_discretionary_change") is not None:
                assumptions.nondefense_discretionary_2025_billions *= (1 + discretionary_mechanics.get("nondefense_discretionary_change"))
            if discretionary_mechanics.get("budget_caps_enabled"):
                assumptions.inflation_annual = min(assumptions.inflation_annual, 0.02)
        model = DiscretionarySpendingModel(assumptions=assumptions)
        
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
            hovermode='x unified'
        )
        apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
        
        st.plotly_chart(fig, width="stretch")
        
        # Category breakdown table
        with st.expander("View Year-by-Year Breakdown"):
            st.dataframe(projections, width="stretch")


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
    
    # ==========================================================================
    # ENHANCED: Policy Selector with Baseline + Library Policies
    # ==========================================================================
    st.markdown("### 📋 Policy Selection")
    
    from core.policy_builder import PolicyLibrary
    library = PolicyLibrary()
    all_policies = library.list_policies()
    
    # Build policy options: Baseline + all library policies
    policy_options = ["📊 Baseline (Current Law)"]
    policy_map = {"📊 Baseline (Current Law)": None}
    
    for name in all_policies:
        policy = library.get_policy(name)
        if policy:
            # Add category prefix for clarity
            category = getattr(policy, "category", "General")
            if category == "Uploaded Policies":
                display_name = f"📄 {name}"
            else:
                display_name = f"📁 {name}"
            policy_options.append(display_name)
            policy_map[display_name] = policy
    
    col_policy, col_refresh = st.columns([4, 1])
    with col_policy:
        selected_policy_display = st.selectbox(
            "Select Policy:",
            policy_options,
            index=0,
            help="Choose 'Baseline (Current Law)' for static projections, or select a policy from your library to see how it affects fiscal outcomes."
        )
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_combined_policies"):
            st.rerun()
    
    # Get selected policy object
    uploaded_policy = policy_map.get(selected_policy_display)
    policy_name = selected_policy_display.replace("📄 ", "").replace("📁 ", "").replace("📊 ", "")
    
    # Extract mechanics from policy
    discretionary_mechanics = None
    medicaid_mechanics = None
    tax_mechanics = None
    ss_mechanics = None
    policy_overrides = {"revenue": {}, "ss": {}, "medicaid": {}, "discretionary": {}}
    
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        if hasattr(uploaded_policy, "structured_mechanics") and uploaded_policy.structured_mechanics:
            discretionary_mechanics = uploaded_policy.structured_mechanics.get("spending_mechanics")
            medicaid_mechanics = discretionary_mechanics
            tax_mechanics = uploaded_policy.structured_mechanics.get("tax_mechanics")
            ss_mechanics = uploaded_policy.structured_mechanics.get("social_security_mechanics")
            
            # Get scenario overrides from policy
            policy_overrides = get_policy_scenario_overrides(uploaded_policy)
        
        # Display extracted mechanics summary
        with st.expander("📑 Extracted Policy Mechanics", expanded=False):
            col_tax, col_ss, col_spend = st.columns(3)
            
            with col_tax:
                st.markdown("**💰 Tax Mechanics**")
                if tax_mechanics:
                    if tax_mechanics.get("payroll_tax_rate"):
                        st.write(f"• Payroll tax: {tax_mechanics.get('payroll_tax_rate')*100:.1f}%")
                    if tax_mechanics.get("financial_transaction_tax_rate"):
                        st.write(f"• FTT: {tax_mechanics.get('financial_transaction_tax_rate')*100:.1f}%")
                    income_changes = tax_mechanics.get("income_tax_changes", {})
                    if income_changes.get("eitc_expansion"):
                        st.write("• EITC expansion: Yes")
                    if income_changes.get("dollar_for_dollar_offset"):
                        st.write("• FICA offset: Yes")
                else:
                    st.write("• No tax mechanics detected")
            
            with col_ss:
                st.markdown("**👴 Social Security**")
                if ss_mechanics:
                    if ss_mechanics.get("payroll_tax_rate"):
                        st.write(f"• Payroll rate: {ss_mechanics.get('payroll_tax_rate')*100:.1f}%")
                    if ss_mechanics.get("payroll_tax_cap_change"):
                        st.write(f"• Cap change: {ss_mechanics.get('payroll_tax_cap_change')}")
                    benefit_changes = ss_mechanics.get("benefit_formula_changes", {})
                    if benefit_changes.get("grandfathered"):
                        st.write("• Benefits: Grandfathered")
                    if benefit_changes.get("health_fund_integration"):
                        st.write("• Health fund integration: Yes")
                else:
                    st.write("• No SS mechanics detected")
            
            with col_spend:
                st.markdown("**📊 Spending Mechanics**")
                if discretionary_mechanics:
                    if discretionary_mechanics.get("national_health_fund"):
                        st.write("• National health fund: Yes")
                    if discretionary_mechanics.get("medicare_transfer"):
                        st.write("• Medicare redirect: Yes")
                    if discretionary_mechanics.get("medicaid_expansion"):
                        st.write("• Medicaid expansion: Yes")
                    budget_caps = discretionary_mechanics.get("budget_cap_levels", {})
                    if budget_caps.get("gdp_cap_pct"):
                        st.write(f"• GDP cap: {budget_caps.get('gdp_cap_pct')}%")
                else:
                    st.write("• No spending mechanics detected")
    else:
        st.info("📊 Using **Baseline (Current Law)** - no policy adjustments applied")
    
    st.divider()
    
    # ==========================================================================
    # ENHANCED: Scenario Selectors with Policy-Derived Defaults
    # ==========================================================================
    st.markdown("### ⚙️ Scenario Configuration")
    
    # Determine defaults based on policy mechanics
    economic_default = "baseline"
    discretionary_default = "baseline"
    interest_default = "baseline"
    
    # Policy-driven economic scenario default
    if policy_overrides.get("revenue", {}).get("payroll_rate"):
        # If policy changes tax rates significantly, suggest strong_growth (optimistic) or baseline
        payroll_rate = policy_overrides["revenue"]["payroll_rate"]
        if payroll_rate and payroll_rate < 0.12:  # Lower than current ~12.4%
            economic_default = "strong_growth"
    
    # Policy-driven discretionary scenario default
    disc_override = policy_overrides.get("discretionary", {})
    if disc_override:
        nd = disc_override.get("nondefense_change")
        dfc = disc_override.get("defense_change")
        if (nd is not None and nd > 0.01) or (dfc is not None and dfc > 0.01):
            discretionary_default = "growth"
        elif (nd is not None and nd < -0.01) or (dfc is not None and dfc < -0.01):
            discretionary_default = "reduction"
        elif disc_override.get("budget_caps"):
            discretionary_default = "reduction"
    
    # Policy-driven interest scenario default
    # If policy aims for surplus/debt reduction, suggest falling rates
    if discretionary_mechanics:
        budget_caps = discretionary_mechanics.get("budget_cap_levels", {})
        if budget_caps.get("surplus_allocations", {}).get("debt_reduction_pct"):
            interest_default = "falling"
    
    col1, col2 = st.columns(2)
    with col1:
        # Show policy influence on economic scenario
        econ_help = "Macro assumption set driving revenue and discretionary forecasts."
        if economic_default != "baseline" and uploaded_policy:
            econ_help += f" **Policy suggests: {economic_default}**"
        
        revenue_scenario = st.selectbox(
            "Economic Scenario:",
            ["baseline", "recession_2026", "strong_growth", "demographic_challenge"],
            index=["baseline", "recession_2026", "strong_growth", "demographic_challenge"].index(economic_default),
            help=econ_help,
        )

        # Show policy influence on discretionary scenario
        disc_help = "Growth path for discretionary spending."
        if discretionary_default != "baseline" and uploaded_policy:
            disc_help += f" **Policy suggests: {discretionary_default}**"
        
        discretionary_scenario = st.selectbox(
            "Discretionary Scenario:",
            ["baseline", "growth", "reduction"],
            index=["baseline", "growth", "reduction"].index(discretionary_default),
            help=disc_help,
        )
    
    with col2:
        # Show policy influence on interest scenario
        int_help = "Projected path for interest rates on federal debt."
        if interest_default != "baseline" and uploaded_policy:
            int_help += f" **Policy suggests: {interest_default}**"
        
        interest_scenario = st.selectbox(
            "Interest Rate Scenario:",
            ["baseline", "rising", "falling", "spike"],
            index=["baseline", "rising", "falling", "spike"].index(interest_default),
            help=int_help,
        )
        
        years = st.slider(
            "Projection years:",
            10,
            75,
            30,
            key="outlook_years",
            help="Years to simulate the unified federal outlook.",
        )
    
    iterations = st.slider(
        "Monte Carlo iterations:",
        1000,
        50000,
        10000,
        step=1000,
        key="outlook_iter",
        help="Monte Carlo runs for the unified outlook. Higher counts give smoother confidence bands.",
    )
    
    if st.button("Calculate Combined Fiscal Outlook"):
        model = CombinedFiscalOutlookModel()

        # Apply extracted mechanics using unified method
        if uploaded_policy and hasattr(uploaded_policy, "structured_mechanics") and uploaded_policy.structured_mechanics:
            model.apply_policy_mechanics(uploaded_policy.structured_mechanics)
            st.info("📊 Policy mechanics applied to fiscal projections")
        else:
            # Legacy manual application for backward compatibility
            if tax_mechanics:
                if tax_mechanics.get("payroll_tax_rate"):
                    model.revenue_model.payroll.social_security_rate = tax_mechanics.get("payroll_tax_rate") / 2
                if tax_mechanics.get("corporate_tax_rate"):
                    model.revenue_model.corporate.marginal_tax_rate = tax_mechanics.get("corporate_tax_rate")
            if ss_mechanics:
                tf = model.ss_model.trust_fund
                if ss_mechanics.get("payroll_tax_rate"):
                    tf.payroll_tax_rate = ss_mechanics.get("payroll_tax_rate")
                if ss_mechanics.get("payroll_tax_cap_change") == "remove_cap":
                    tf.payroll_tax_cap = None
                elif ss_mechanics.get("payroll_tax_cap_change") == "increase_cap" and ss_mechanics.get("payroll_tax_cap_increase"):
                    tf.payroll_tax_cap = ss_mechanics.get("payroll_tax_cap_increase")
                if ss_mechanics.get("full_retirement_age"):
                    model.ss_model.benefit_formula.full_retirement_age = ss_mechanics.get("full_retirement_age")
                elif ss_mechanics.get("full_retirement_age_change"):
                    model.ss_model.benefit_formula.full_retirement_age = 67 + ss_mechanics.get("full_retirement_age_change")
                cola_hint = ss_mechanics.get("cola_adjustments")
                if cola_hint == "chained_cpi":
                    model.ss_model.benefit_formula.annual_cola = 0.026
            if discretionary_mechanics:
                if discretionary_mechanics.get("defense_spending_change") is not None:
                    model.discretionary_model.assumptions.defense_2025_billions *= (1 + discretionary_mechanics.get("defense_spending_change"))
                if discretionary_mechanics.get("nondefense_discretionary_change") is not None:
                    model.discretionary_model.assumptions.nondefense_discretionary_2025_billions *= (1 + discretionary_mechanics.get("nondefense_discretionary_change"))
                if discretionary_mechanics.get("budget_caps_enabled"):
                    model.discretionary_model.assumptions.inflation_annual = min(model.discretionary_model.assumptions.inflation_annual, 0.02)
            if medicaid_mechanics:
                # Apply Medicaid-related signals to Medicaid model
                if medicaid_mechanics.get("medicaid_expansion"):
                    model.medicaid_model.assumptions.medicaid_expansion_enrollment *= 1.2
                    model.medicaid_model.assumptions.total_medicaid_spending *= 1.1
                if medicaid_mechanics.get("medicaid_block_grant"):
                    model.medicaid_model.assumptions.medicaid_cost_growth_annual = 0.02
                if medicaid_mechanics.get("medicaid_per_capita_cap"):
                    model.medicaid_model.assumptions.medicaid_cost_growth_annual = min(model.medicaid_model.assumptions.medicaid_cost_growth_annual, 0.02)
                fmap = medicaid_mechanics.get("medicaid_fmap_change")
                if fmap is not None:
                    model.medicaid_model.assumptions.federal_medicaid_spending *= (1 + fmap / 100)
                if medicaid_mechanics.get("medicaid_waivers"):
                    model.medicaid_model.assumptions.long_term_care_growth_annual = max(0.025, model.medicaid_model.assumptions.long_term_care_growth_annual - 0.005)
        
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
                    hovermode='x unified'
                )
                apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
                
                st.plotly_chart(fig, width="stretch")
                
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
                    hovermode='x unified'
                )
                apply_plotly_theme(fig2, st.session_state.settings.get('theme', 'light'))
                
                st.plotly_chart(fig2, width="stretch")
                
                # Deficit trend
                fig3 = go.Figure()
                fig3.add_trace(go.Bar(x=df['year'], y=df['deficit_surplus'], name='Deficit/Surplus'))
                fig3.add_hline(y=0, line_dash="dash", line_color="black")
                
                fig3.update_layout(
                    title="Annual Deficit/Surplus",
                    xaxis_title="Year",
                    yaxis_title="$ Billions (negative = deficit)"
                )
                apply_plotly_theme(fig3, st.session_state.settings.get('theme', 'light'))
                
                st.plotly_chart(fig3, width="stretch")
                
                # Detailed data table
                with st.expander("View Detailed Budget Data"):
                    st.dataframe(df, width="stretch")
                    
            except Exception as e:
                st.error(f"Error calculating outlook: {str(e)}")
                st.info("This feature combines multiple modules. Ensure all dependencies are installed.")


def page_policy_comparison():
    """Policy comparison page."""
    st.title("⚖️ Policy Comparison Analysis")
    
    st.markdown("""
    Compare multiple policies or scenarios side-by-side to evaluate their fiscal impact.
    """)
    
    # Load custom policies from library - ALWAYS FRESH (not cached)
    all_custom_policies, library = get_policy_library_policies()
    
    col1, col2 = st.columns(2)
    with col1:
        num_policies = st.slider("Number of policies to compare:", 2, 5, 2, key="num_policies")
        years = st.slider("Projection years:", 10, 75, 30, key="compare_years")
    with col2:
        st.write("Comparison type:")
        comparison_options = ["Scenarios", "Custom Policies", "Mixed"]
        if "comparison_mode" not in st.session_state:
            st.session_state["comparison_mode"] = comparison_options[0]
        cols = st.columns(len(comparison_options))
        for idx, opt in enumerate(comparison_options):
            if cols[idx].button(opt, key=f"comparison_mode_btn_{opt}"):
                st.session_state["comparison_mode"] = opt
        comparison_mode = st.session_state["comparison_mode"]
        iterations = st.slider("Monte Carlo iterations:", 1000, 50000, 10000, step=1000, key="compare_iter")
    
    # Policy/scenario selectors
    policies = {}
    
    if comparison_mode == "Scenarios":
        # Original scenario-based comparison
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            
            col1, col2 = st.columns(2)
            with col1:
                rev_scenario = st.selectbox(f"Revenue Scenario {i+1}:", ["baseline", "recession_2026", "strong_growth"], key=f"rev_scenario_{i}")
            with col2:
                discret_scenario = st.selectbox(f"Discretionary {i+1}:", ["baseline", "growth", "reduction"], key=f"discret_scenario_{i}")
            
            policies[f"Policy {i+1}"] = {
                "type": "scenario",
                "revenue_scenario": rev_scenario,
                "discretionary_scenario": discret_scenario,
            }
    
    elif comparison_mode == "Custom Policies":
        # Select from custom policy library
        if not all_custom_policies:
            st.warning("No custom policies found. Create policies in 'Custom Policy Builder' or 'Policy Upload' first.")
            return
        
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            policy_name = st.selectbox(
                f"Select policy {i+1}:",
                all_custom_policies,
                key=f"custom_policy_{i}"
            )
            policies[f"Policy {i+1}"] = {
                "type": "custom",
                "policy_name": policy_name,
            }
    
    else:  # Mixed
        for i in range(num_policies):
            st.subheader(f"Policy {i+1}")
            
            type_key = f"policy_type_{i}"
            if type_key not in st.session_state:
                st.session_state[type_key] = "Scenario"
            col_btn1, col_btn2 = st.columns(2)
            if col_btn1.button(f"Scenario {i+1}", key=f"btn_scenario_{i}"):
                st.session_state[type_key] = "Scenario"
            if col_btn2.button(f"Custom {i+1}", key=f"btn_custom_{i}"):
                st.session_state[type_key] = "Custom Policy"
            policy_type = st.session_state[type_key]
            
            if policy_type == "Scenario":
                col1, col2 = st.columns(2)
                with col1:
                    rev_scenario = st.selectbox(f"Revenue Scenario {i+1}:", ["baseline", "recession_2026", "strong_growth"], key=f"rev_scenario_{i}")
                with col2:
                    discret_scenario = st.selectbox(f"Discretionary {i+1}:", ["baseline", "growth", "reduction"], key=f"discret_scenario_{i}")
                
                policies[f"Policy {i+1}"] = {
                    "type": "scenario",
                    "revenue_scenario": rev_scenario,
                    "discretionary_scenario": discret_scenario,
                }
            else:
                if all_custom_policies:
                    policy_name = st.selectbox(
                        f"Select custom policy {i+1}:",
                        all_custom_policies,
                        key=f"custom_policy_{i}"
                    )
                    policies[f"Policy {i+1}"] = {
                        "type": "custom",
                        "policy_name": policy_name,
                    }
                else:
                    st.warning(f"No custom policies available for Policy {i+1}")
                    return
    
    metric_to_compare = st.selectbox(
        "Compare by metric:",
        ["10-year deficit", "Average annual deficit", "Interest spending", "Total spending"]
    )
    
    if st.button("Compare Policies"):
        model = CombinedFiscalOutlookModel()
        
        with st.spinner("Running policy comparison..."):
            comparison_data = {}
            
            try:
                for policy_name, config in policies.items():
                    if config["type"] == "scenario":
                        summary = model.get_fiscal_summary(
                            years=years,
                            iterations=iterations,
                            revenue_scenario=config["revenue_scenario"],
                            discretionary_scenario=config["discretionary_scenario"]
                        )
                    else:  # custom policy
                        # For custom policies, use basic fiscal summary
                        summary = model.get_fiscal_summary(
                            years=years,
                            iterations=iterations,
                            revenue_scenario="baseline",
                            discretionary_scenario="baseline"
                        )
                        # In a full implementation, you would apply custom policy parameters
                        st.info(f"Note: Custom policy '{config['policy_name']}' is being compared using baseline scenarios. Full integration requires policy simulation engine.")
                    
                    comparison_data[policy_name] = summary
                
                # Create comparison table
                comparison_df = pd.DataFrame(comparison_data).T
                st.dataframe(comparison_df, width="stretch")
                
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
                    showlegend=False
                )
                apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
                
                st.plotly_chart(fig, width="stretch")
                
                st.success("Comparison complete! Green bars are better (lower spending/deficit).")
                
            except Exception as e:
                st.error(f"Error during comparison: {str(e)}")


def page_custom_policy_builder():
    """Custom policy builder page with parameter sliders."""
    st.title("🔧 Custom Policy Builder")
    
    st.markdown("""
    Create and customize fiscal policies with adjustable parameters. Choose a template or build from scratch.
    """)
    
    from core.policy_builder import PolicyTemplate, PolicyType
    
    # Load policy library - ALWAYS FRESH (not cached)
    all_policies, library = get_policy_library_policies()
    policies = library.list_policies()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Create New Policy")
        
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <small><strong>💡 Tip:</strong> Start with a template that matches your policy focus. Each template includes pre-configured parameters you can customize.</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Policy template selection via buttons
        template_options = ["Healthcare Reform", "Tax Reform", "Spending Reform", "Blank Custom"]
        if "template_choice" not in st.session_state:
            st.session_state["template_choice"] = template_options[0]
        
        st.markdown("""**Select template:** 
        - 🏥 **Healthcare Reform** - Modify healthcare spending, coverage, and funding
        - 💵 **Tax Reform** - Adjust tax rates and revenue sources  
        - 📉 **Spending Reform** - Control discretionary and mandatory spending
        - ⚙️ **Blank Custom** - Start from scratch with no defaults
        """)
        
        cols = st.columns(len(template_options))
        for idx, opt in enumerate(template_options):
            if cols[idx].button(opt, key=f"template_choice_{opt}"):
                st.session_state["template_choice"] = opt
        template_choice = st.session_state["template_choice"]
        
        template_map = {
            "Healthcare Reform": "healthcare",
            "Tax Reform": "tax_reform",
            "Spending Reform": "spending_reform",
        }
        
        if template_choice != "Blank Custom":
            template_name = template_map[template_choice]
            policy_name = st.text_input(
                "Policy name:", 
                f"My {template_choice}",
                help=get_tooltip(
                    "Policy Name",
                    "Give your policy a descriptive name. This is used to identify and reference the policy across all dashboard pages."
                )
            )
            
            if st.button("Create from template"):
                policy = PolicyTemplate.create_from_template(template_name, policy_name)
                library.add_policy(policy)
                st.success(f"✓ Policy '{policy_name}' created!")
                st.cache_data.clear()  # Clear any cached data
                st.rerun()  # Force page refresh
    
    with col2:
        st.subheader("Manage Policies")
        
        st.markdown("""
        <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <small><strong>💡 Tip:</strong> Select a policy to edit its parameters. Changes are saved automatically. Use the sliders to adjust values while seeing real-time updates.</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Show existing policies

        if policies:
            selected_policy_name = st.selectbox("Edit existing policy:", policies)
            selected_policy = library.get_policy(selected_policy_name)
            
            if selected_policy:
                # Display policy info in a nice card format
                st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h4>📋 Policy Details</h4>
                    <p><strong>Name:</strong> {selected_policy_name}</p>
                    <p><strong>Type:</strong> {selected_policy.policy_type.value}</p>
                    <p><strong>Description:</strong> {selected_policy.description}</p>
                    <p><strong>Author:</strong> {selected_policy.author} | <strong>Created:</strong> {selected_policy.created_date[:10]}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Parameter editor by category
                categories = set(p.category for p in selected_policy.parameters.values())
                
                st.markdown("#### Adjust Parameters")
                st.markdown("""
                <small>💡 **Tip:** Move the sliders to adjust policy parameters. Changes are automatically saved. The unit of measurement is shown on the right.</small>
                """, unsafe_allow_html=True)
                
                for category in sorted(categories):
                    with st.expander(f"📊 {category.title()} Parameters", expanded=True):
                        params_in_category = selected_policy.get_parameters_by_category(category)
                        
                        for param_name, param in params_in_category.items():
                            col_a, col_b = st.columns([3, 1])
                            
                            with col_a:
                                new_value = st.slider(
                                    label=param.description,
                                    min_value=param.min_value,
                                    max_value=param.max_value,
                                    value=param.value,
                                    step=(param.max_value - param.min_value) / 100,
                                    key=f"slider_{param_name}",
                                    help=get_tooltip(
                                        param.description,
                                        f"Range: {param.min_value} to {param.max_value} {param.unit if param.unit else ''}. Adjust this parameter to see its impact on fiscal outcomes."
                                    )
                                )
                                
                                if new_value != param.value:
                                    selected_policy.update_parameter(param_name, new_value)
                                    library.save_policy(selected_policy)
                            
                            with col_b:
                                st.caption(param.unit if param.unit else "")
                
                # Save and delete options
                col_save, col_delete = st.columns(2)
                
                with col_save:
                    if st.button("💾 Save Changes"):
                        library.save_policy(selected_policy)
                        st.success("Policy saved!")
                
                with col_delete:
                    if st.button("🗑️ Delete Policy"):
                        library.delete_policy(selected_policy_name)
                        st.warning(f"Policy '{selected_policy_name}' deleted!")
                        st.rerun()
        else:
            st.info("No policies yet. Create one from a template above!")
    
    # Policy library overview
    st.divider()
    st.subheader("Policy Library")
    
    if policies:
        library_df = library.export_policies_dataframe()
        st.dataframe(library_df, width="stretch")
        
        # Export all policies
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export All Policies"):
                export_data = {}
                for name in policies:
                    policy = library.get_policy(name)
                    export_data[name] = policy.to_dict()
                
                st.json(export_data)
    else:
        st.info("Your policy library is empty. Create policies to get started!")

    # Scenario builder: compare and save bundles
    st.divider()
    st.subheader("Scenario Builder: compare, diff, save")

    from core.policy_builder import ScenarioBundleLibrary, ScenarioBundle, build_policy_comparison_table

    scenario_lib = ScenarioBundleLibrary()
    saved_scenarios = scenario_lib.list_bundles()

    if "scenario_selected_policies" not in st.session_state:
        st.session_state["scenario_selected_policies"] = policies[:2] if len(policies) >= 2 else policies

    col_pick, col_saved = st.columns([2, 1])

    with col_pick:
        st.session_state["scenario_selected_policies"] = st.multiselect(
            "Select policies to compare",
            options=policies,
            default=st.session_state.get("scenario_selected_policies", policies[:2] if len(policies) >= 2 else policies),
            help="Pick two or more saved policies to see parameter deltas",
        )

    with col_saved:
        load_choice = st.selectbox(
            "Load saved scenario",
            options=["<none>"] + saved_scenarios,
            index=0,
            help="Apply a previously saved scenario bundle",
        )
        if load_choice != "<none>":
            bundle = scenario_lib.get_bundle(load_choice)
            if bundle:
                st.session_state["scenario_selected_policies"] = [
                    name for name in bundle.policy_names if name in policies
                ]
                st.info(f"Loaded scenario '{bundle.name}'")
        if load_choice != "<none>" and st.button("🗑️ Delete scenario", key="delete_scenario"):
            scenario_lib.delete_bundle(load_choice)
            st.rerun()

    selected = st.session_state.get("scenario_selected_policies", [])

    if selected:
        selected_objs = [library.get_policy(name) for name in selected if library.get_policy(name)]
        if selected_objs:
            diff_df = build_policy_comparison_table(selected_objs)

            def _highlight_deltas(data):
                styles = pd.DataFrame("", index=data.index, columns=data.columns)
                for col in data.columns:
                    if "Δ" in col:
                        styles[col] = ["color: green" if (v is not None and v >= 0) else "color: red" for v in data[col]]
                return styles

            st.dataframe(diff_df.style.apply(_highlight_deltas, axis=None), use_container_width=True)

            # Quick variance chips
            spread_rows = []
            for param in sorted({p for policy in selected_objs for p in policy.parameters.keys()}):
                values = [policy.parameters[param].value for policy in selected_objs if param in policy.parameters]
                if len(values) >= 2:
                    spread_rows.append({
                        "Parameter": param,
                        "Spread": float(np.max(values) - np.min(values)),
                    })
            if spread_rows:
                spread_df = pd.DataFrame(spread_rows).sort_values(by="Spread", ascending=False).head(5)
                st.caption("Top variance parameters (spread across selected policies)")
                st.dataframe(spread_df, use_container_width=True)

            csv_data = diff_df.to_csv(index=False)
            st.download_button(
                "Download comparison CSV",
                data=csv_data,
                file_name="scenario_comparison.csv",
                mime="text/csv",
            )

            # Clone helper
            col_clone_src, col_clone_name = st.columns([1, 2])
            with col_clone_src:
                clone_source = st.selectbox("Clone policy", options=policies, index=0)
            with col_clone_name:
                clone_target = st.text_input("New policy name", value=f"{clone_source} Copy")
            if st.button("🔁 Clone", key="clone_policy_btn"):
                if clone_target.strip():
                    ok = library.clone_policy(clone_source, clone_target.strip())
                    if ok:
                        st.success(f"Cloned to '{clone_target}'")
                        st.rerun()
                    else:
                        st.error("Clone failed (name exists?)")
                else:
                    st.error("Provide a new policy name")

            # Save/load bundle
            col_save_name, col_save_desc = st.columns([1, 2])
            with col_save_name:
                scenario_name = st.text_input("Scenario name", value="New Scenario")
            with col_save_desc:
                scenario_desc = st.text_input("Notes", value="")

            if st.button("💾 Save scenario bundle", type="primary"):
                if scenario_name.strip():
                    bundle = ScenarioBundle(
                        name=scenario_name.strip(),
                        policy_names=selected,
                        description=scenario_desc.strip(),
                    )
                    scenario_lib.save_bundle(bundle)
                    st.success(f"Saved scenario '{scenario_name}'")
                else:
                    st.error("Scenario name is required")

            # Zip bundle download
            from core.policy_builder import build_scenario_bundle_zip

            bundle_bytes = build_scenario_bundle_zip(selected_objs, diff_df)
            st.download_button(
                "⬇️ Download scenario bundle (zip)",
                data=bundle_bytes,
                file_name="scenario_bundle.zip",
                mime="application/zip",
            )
        else:
            st.info("No matching policies found for selection.")
    else:
        st.info("Select at least one policy to build a scenario.")


def page_real_data_dashboard():
    """Real data integration dashboard showing CBO/SSA baselines."""
    st.title("📊 Real Data: CBO & SSA Integration")
    
    st.markdown("""
    View authentic federal fiscal data from the Congressional Budget Office and Social Security Administration.
    These baselines power all fiscal projections.
    """)
    
    from core.data_loader import load_real_data
    import requests
    from ui.auth import StreamlitAuth
    
    data_loader = load_real_data()
    
    # CBO freshness badge via API ingestion health endpoint
    ingestion_payload = None
    api_base = StreamlitAuth.API_BASE
    headers = StreamlitAuth.get_auth_header() if StreamlitAuth.is_authenticated() else {}

    try:
        resp = requests.get(f"{api_base}/api/data/ingestion-health", headers=headers, timeout=5)
        if resp.status_code == 200:
            ingestion_payload = resp.json().get("data", {})
        else:
            st.warning(f"Ingestion health API returned {resp.status_code}: {resp.text[:120]}")
    except Exception as exc:
        st.info(f"Ingestion health unavailable ({str(exc)[:80]}). Falling back to cached metrics.")

    if ingestion_payload:
        fetched_at = ingestion_payload.get('fetched_at') or ingestion_payload.get('last_updated')
        freshness_hours = ingestion_payload.get('freshness_hours')
        cache_used = ingestion_payload.get('cache_used', False)
        cache_age_hours = ingestion_payload.get('cache_age_hours')
        checksum = ingestion_payload.get('checksum', 'n/a')
        source = ingestion_payload.get('data_source', 'CBO/Treasury')
        schema_valid = ingestion_payload.get('schema_valid', True)
        validation_errors = ingestion_payload.get('validation_errors', []) or []

        status_bits = [f"Source: {source}"]
        if fetched_at:
            status_bits.append(f"Fetched at {fetched_at}")
        if freshness_hours is not None:
            status_bits.append(f"Age {freshness_hours:.1f}h")
        if cache_age_hours is not None:
            status_bits.append(f"Cache age {cache_age_hours:.1f}h")
        status_bits.append(f"Checksum {checksum}")
        status_text = " • ".join(status_bits)

        if not schema_valid:
            detail = "; ".join(validation_errors) if validation_errors else "Schema validation failed"
            st.error(f"❌ CBO ingestion schema invalid. {detail}")
        elif cache_used:
            st.warning(f"⚠️ Using cached CBO data. {status_text}")
        else:
            st.success(f"✅ Live CBO data. {status_text}")
    else:
        st.info("CBO ingestion health unavailable. Showing built-in baseline metrics.")
    
    # Three main tabs
    tab_summary, tab_revenues, tab_spending, tab_demographics = st.tabs([
        "Summary", "Revenues", "Spending", "Demographics"
    ])
    
    with tab_summary:
        st.subheader("Federal Fiscal Summary (FY 2025)")
        
        # Key metrics cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Revenue",
                f"${data_loader.cbo.total_revenue:,.0f}B",
                delta=f"{(data_loader.cbo.total_revenue / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col2:
            st.metric(
                "Total Spending",
                f"${data_loader.cbo.total_spending:,.0f}B",
                delta=f"{(data_loader.cbo.total_spending / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col3:
            deficit = data_loader.cbo.total_spending - data_loader.cbo.total_revenue
            st.metric(
                "Federal Deficit",
                f"${deficit:,.0f}B",
                delta=f"{(deficit / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        with col4:
            st.metric(
                "Public Debt",
                f"${data_loader.cbo.public_debt_held:,.0f}B",
                delta=f"{(data_loader.cbo.public_debt_held / data_loader.cbo.gdp * 100):.1f}% of GDP"
            )
        
        # Full summary table
        st.divider()
        summary_df = data_loader.export_summary_metrics()
        st.dataframe(summary_df, width="stretch")
    
    with tab_revenues:
        st.subheader("Federal Revenue Sources (FY 2025)")
        
        revenue_data = data_loader.get_revenue_baseline()
        
        # Revenue chart
        revenue_df = pd.DataFrame({
            "Source": [k.replace("_", " ").title() for k in revenue_data.keys() if k != "total"],
            "Amount": [v for k, v in revenue_data.items() if k != "total"]
        })
        
        fig = px.pie(
            revenue_df,
            values="Amount",
            names="Source",
            title="Federal Revenue Distribution"
        )
        apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
        st.plotly_chart(fig, width="stretch")
        
        # Revenue details
        st.write("**Revenue by Source ($B)**")
        for source, amount in revenue_data.items():
            if source != "total":
                st.write(f"- **{source.replace('_', ' ').title()}**: ${amount:,.1f}B")
        
        st.write(f"**Total:** ${revenue_data['total']:,.1f}B")
    
    with tab_spending:
        st.subheader("Federal Spending by Category (FY 2025)")
        
        spending_data = data_loader.get_spending_baseline()
        
        # Spending chart
        spending_df = pd.DataFrame({
            "Category": [k.replace("_", " ").title() for k in spending_data.keys() if k != "total"],
            "Amount": [v for k, v in spending_data.items() if k != "total"]
        })
        
        fig = px.pie(
            spending_df,
            values="Amount",
            names="Category",
            title="Federal Spending Distribution"
        )
        apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
        st.plotly_chart(fig, width="stretch")
        
        # Spending details
        st.write("**Spending by Category ($B)**")
        for category, amount in spending_data.items():
            if category != "total":
                st.write(f"- **{category.replace('_', ' ').title()}**: ${amount:,.1f}B")
        
        st.write(f"**Total:** ${spending_data['total']:,.1f}B")
    
    with tab_demographics:
        st.subheader("U.S. Population & Demographics")
        
        pop_metrics = data_loader.get_population_metrics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Population", f"{pop_metrics['total_population']:.1f}M")
            st.metric("Under 18", f"{pop_metrics['percent_under_18']:.1f}%")
        
        with col2:
            st.metric("Working Age (18-64)", f"{pop_metrics['percent_18_64']:.1f}%")
            st.metric("Age 65+", f"{pop_metrics['percent_65_plus']:.1f}%")
        
        with col3:
            st.metric("Annual Growth", f"{pop_metrics['annual_growth_rate']:.2f}%")
            st.metric("Life Expectancy", f"{pop_metrics['life_expectancy']:.1f} years")
        
        percent_65_now = pop_metrics['percent_65_plus']
        percent_65_future = percent_65_now * 1.4
        st.info(
            "\n".join([
                "The U.S. is experiencing significant aging:",
                f"- In 2025, about **{percent_65_now:.0f}%** of Americans are 65+",
                f"- By 2045, this will grow to approximately **{percent_65_future:.0f}%**",
                "- This affects demand for Social Security, Medicare, and Medicaid",
            ])
        )


def page_library_manager():
    """Policy library manager with CRUD operations and categorization."""
    st.title("📚 Policy Library Manager")
    
    st.markdown("""
    Manage your custom policies and uploaded PDFs. Organize by category, edit parameters, 
    clone for variations, and reorder your collection.
    """)
    
    from core.policy_builder import PolicyLibrary
    library = PolicyLibrary()
    
    # Get categories and determine best default (prefer category with policies)
    categories = library.get_categories()
    default_category = "General"
    
    # Find first category that has policies, prioritizing "Uploaded Policies"
    if "Uploaded Policies" in categories and library.list_policies_by_category("Uploaded Policies"):
        default_category = "Uploaded Policies"
    else:
        for cat in categories:
            if library.list_policies_by_category(cat):
                default_category = cat
                break
    
    default_index = categories.index(default_category) if default_category in categories else 0
    
    # Tab navigation
    tab_browse, tab_organize, tab_manage_categories = st.tabs(
        ["📖 Browse & Edit", "🔄 Reorder", "🏷️ Categories"]
    )
    
    # ========== BROWSE & EDIT TAB ==========
    with tab_browse:
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_category = st.selectbox(
                "Select Category:",
                options=categories,
                index=default_index,
                key="browse_category"
            )
        
        with col2:
            if st.button("🔄 Refresh", width="stretch"):
                st.rerun()
        
        # Show total policy count summary
        total_policies = len(library.list_policies())
        if total_policies > 0:
            st.success(f"📚 **{total_policies} total policies** in library")
        
        category_policies = library.list_policies_by_category(selected_category)
        
        if not category_policies:
            st.info(f"No policies in '{selected_category}' category")
        else:
            st.subheader(f"Policies in {selected_category} ({len(category_policies)})")
            
            for policy_name in category_policies:
                policy = library.get_policy(policy_name)
                if not policy:
                    continue
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{policy.name}**")
                        st.caption(f"Type: {policy.policy_type.value} | Author: {policy.author}")
                        st.text(policy.description)
                        st.write(f"📊 Parameters: {len(policy.parameters)} | Created: {policy.created_date[:10]}")
                    
                    with col2:
                        operation = st.selectbox(
                            "Action:",
                            ["Select...", "Edit", "View", "Clone", "Rename", "Move", "Delete"],
                            key=f"action_{policy_name}"
                        )
                        
                        if operation == "View":
                            with st.expander("📋 View Parameters"):
                                params_df = pd.DataFrame([
                                    {
                                        "Parameter": p.name,
                                        "Value": p.value,
                                        "Min": p.min_value,
                                        "Max": p.max_value,
                                        "Unit": p.unit,
                                    }
                                    for p in policy.parameters.values()
                                ])
                                st.dataframe(params_df, width="stretch")
                        
                        elif operation == "Edit":
                            with st.expander("✏️ Edit Policy", expanded=True):
                                policy.description = st.text_area(
                                    "Description:",
                                    value=policy.description,
                                    key=f"desc_{policy_name}"
                                )
                                
                                st.subheader("Edit Parameters")
                                for param_name, param in policy.parameters.items():
                                    new_val = st.slider(
                                        f"{param.description}",
                                        min_value=param.min_value,
                                        max_value=param.max_value,
                                        value=param.value,
                                        key=f"param_{policy_name}_{param_name}"
                                    )
                                    param.value = new_val
                                
                                if st.button("💾 Save Changes", key=f"save_{policy_name}"):
                                    if library.save_policy(policy):
                                        st.success(f"✓ {policy_name} updated!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to save policy")
                        
                        elif operation == "Clone":
                            with st.expander("👯 Clone Policy", expanded=True):
                                clone_name = st.text_input(
                                    "New Policy Name:",
                                    value=f"{policy_name} (Clone)",
                                    key=f"clone_name_{policy_name}"
                                )
                                if st.button("✨ Create Clone", key=f"clone_{policy_name}"):
                                    if library.clone_policy(policy_name, clone_name):
                                        st.success(f"✓ Created {clone_name}!")
                                        st.rerun()
                                    else:
                                        st.error(f"Policy '{clone_name}' already exists")
                        
                        elif operation == "Rename":
                            with st.expander("📝 Rename Policy", expanded=True):
                                new_name = st.text_input(
                                    "New Name:",
                                    value=policy_name,
                                    key=f"rename_{policy_name}"
                                )
                                if st.button("✓ Rename", key=f"rename_btn_{policy_name}"):
                                    if library.rename_policy(policy_name, new_name):
                                        st.success(f"✓ Renamed to {new_name}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to rename (name may already exist)")
                        
                        elif operation == "Move":
                            with st.expander("↔️ Change Category", expanded=True):
                                new_category = st.selectbox(
                                    "Move to category:",
                                    options=library.get_categories(),
                                    key=f"move_{policy_name}"
                                )
                                if st.button("🔗 Move", key=f"move_btn_{policy_name}"):
                                    policy.category = new_category
                                    if library.save_policy(policy):
                                        st.success(f"✓ Moved to {new_category}!")
                                        st.rerun()
                                    else:
                                        st.error("Failed to move policy")
                        
                        elif operation == "Delete":
                            with st.expander("🗑️ Delete Policy", expanded=True):
                                st.warning(f"Delete '{policy_name}'? This cannot be undone!")
                                if st.button("🗑️ Confirm Delete", key=f"delete_{policy_name}"):
                                    if library.delete_policy(policy_name):
                                        st.success(f"✓ Deleted {policy_name}")
                                        st.rerun()
                                    else:
                                        st.error("Failed to delete policy")
    
    # ========== REORDER TAB ==========
    with tab_organize:
        selected_category = st.selectbox(
            "Select Category to Reorder:",
            options=library.get_categories(),
            key="reorder_category"
        )
        
        category_policies = library.list_policies_by_category(selected_category)
        
        if not category_policies:
            st.info(f"No policies in '{selected_category}' to reorder")
        else:
            st.markdown("### Drag to reorder (or use buttons below)")
            
            # Display ordered list with up/down buttons
            ordered_list = list(category_policies)
            
            for idx, policy_name in enumerate(ordered_list):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.write(f"**{idx + 1}.** {policy_name}")
                
                with col2:
                    if idx > 0 and st.button("⬆️", key=f"up_{policy_name}"):
                        ordered_list[idx], ordered_list[idx-1] = ordered_list[idx-1], ordered_list[idx]
                        library.reorder_policies(selected_category, ordered_list)
                        st.rerun()
                
                with col3:
                    if idx < len(ordered_list) - 1 and st.button("⬇️", key=f"down_{policy_name}"):
                        ordered_list[idx], ordered_list[idx+1] = ordered_list[idx+1], ordered_list[idx]
                        library.reorder_policies(selected_category, ordered_list)
                        st.rerun()
                
                with col4:
                    if st.button("📌", key=f"pin_{policy_name}"):
                        st.info(f"Pinned: {policy_name}")
    
    # ========== CATEGORIES TAB ==========
    with tab_manage_categories:
        current_categories = library.get_categories()
        st.subheader("Current Categories")
        st.write(", ".join(current_categories))
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("➕ Add New Category")
            new_cat = st.text_input("Category Name:")
            if st.button("Create Category"):
                if new_cat:
                    if library.add_category(new_cat):
                        st.success(f"✓ Created '{new_cat}'")
                        st.rerun()
                    else:
                        st.error(f"Category '{new_cat}' already exists")
                else:
                    st.error("Category name cannot be empty")
        
        with col2:
            st.subheader("🗑️ Delete Category")
            cat_to_delete = st.selectbox(
                "Select category to delete:",
                options=[c for c in current_categories if c != "General"],
                key="delete_cat"
            )
            if st.button("Delete Category"):
                if library.delete_category(cat_to_delete):
                    st.success(f"✓ Deleted '{cat_to_delete}' (policies moved to General)")
                    st.rerun()
                else:
                    st.error("Failed to delete category")


def page_policy_upload():
    """Policy PDF upload and extraction page."""
    st.title("📄 Upload & Extract Policy from PDF")
    
    st.markdown("""
    Upload policy documents (like the United States Galactic Health Act) to extract parameters and create policies.
    """)
    
    from core.pdf_policy_parser import PolicyPDFProcessor
    from core.policy_builder import PolicyLibrary, PolicyType
    import tempfile
    
    # Policy type selector
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### What type of policy are you uploading?")
    with col2:
        policy_type = st.selectbox(
            "Policy Type",
            options=[pt.value for pt in PolicyType],
            format_func=lambda x: {
                "healthcare": "🏥 Healthcare",
                "tax_reform": "💰 Tax Reform",
                "spending_reform": "📊 Spending Reform",
                "combined": "🔗 Combined Policy",
                "custom": "⚙️ Custom",
            }.get(x, x),
            help="Select the policy category to help the extraction process identify relevant parameters",
            label_visibility="collapsed"
        )
    
    st.info(f"**Extraction will focus on:** {policy_type.upper()} policy parameters")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload PDF policy document",
        type=["pdf", "txt"],
        help="Supports PDF and text files up to 200MB"
    )
    
    if uploaded_file:
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        
        if st.button("🔍 Extract Policy Parameters"):
            with st.spinner("Extracting policy parameters..."):
                try:
                    # Save to temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    # Extract policy
                    processor = PolicyPDFProcessor()
                    from pathlib import Path
                    
                    # First extract text from PDF
                    extracted_text = processor.extract_text_from_pdf(Path(tmp_path))
                    
                    # Then analyze the extracted text with policy type context
                    extraction = processor.analyze_policy_text(
                        text=extracted_text,
                        policy_title=uploaded_file.name.replace(".pdf", ""),
                        policy_type=policy_type
                    )
                    
                    # Store extraction in session state
                    st.session_state.policy_extraction = extraction
                    st.session_state.uploaded_filename = uploaded_file.name
                    st.session_state.selected_policy_type = policy_type
                    
                except Exception as e:
                    st.error(f"Error extracting policy: {str(e)}")
                    st.info(f"Full error: {type(e).__name__}: {e}")
                    return
        
        # Display extraction results if we have them
        if hasattr(st.session_state, 'policy_extraction') and st.session_state.policy_extraction:
            extraction = st.session_state.policy_extraction
            
            # Display extraction results
            st.subheader("✓ Extraction Results")
            
            # Handle both new structured mechanics and old format
            params = extraction.identified_parameters
            has_structured = "structured_mechanics" in params
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Confidence Score", f"{extraction.confidence_score:.1%}")
            with col2:
                # Get num_sections from either old or new format
                if has_structured:
                    num_sections = len(params.get("structured_mechanics", {}).get("timeline_milestones", []))
                    st.metric("Timeline Milestones", num_sections)
                else:
                    st.metric("Sections Found", params.get("num_sections", 0))
            with col3:
                if has_structured:
                    num_mechanisms = len(params.get("structured_mechanics", {}).get("funding_mechanisms", []))
                    st.metric("Funding Mechanisms", num_mechanisms)
                else:
                    st.metric("Fiscal Figures", len(extraction.fiscal_impact_estimates))
            
            # Show structured mechanics if available
            if has_structured:
                mechanics = params["structured_mechanics"]

                domains = []
                if mechanics.get("tax_mechanics"):
                    domains.append("Tax")
                if mechanics.get("social_security_mechanics"):
                    domains.append("Social Security")
                if mechanics.get("spending_mechanics"):
                    domains.append("Spending/Medicaid")
                if mechanics.get("target_spending_pct_gdp"):
                    domains.append("Healthcare")
                if domains:
                    st.info("Detected domains: " + ", ".join(domains))
                
                # Funding mechanisms
                if mechanics.get("funding_mechanisms"):
                    with st.expander("💰 Funding Mechanisms", expanded=True):
                        for mech in mechanics["funding_mechanisms"]:
                            st.write(f"**{mech['source_type'].replace('_', ' ').title()}**")
                            if mech.get('percentage_rate'):
                                st.write(f"  - Rate: {mech['percentage_rate']}%")
                            if mech.get('percentage_gdp'):
                                st.write(f"  - % GDP: {mech['percentage_gdp']}%")
                            st.write(f"  - {mech.get('description', '')}")
                
                # Surplus allocation
                if mechanics.get("surplus_allocation"):
                    with st.expander("📊 Surplus Allocation", expanded=True):
                        alloc = mechanics["surplus_allocation"]
                        st.write(f"- **Contingency Reserves:** {alloc['contingency_reserve_pct']}%")
                        st.write(f"- **Debt Reduction:** {alloc['debt_reduction_pct']}%")
                        st.write(f"- **Infrastructure:** {alloc['infrastructure_pct']}%")
                        st.write(f"- **Dividends:** {alloc['dividends_pct']}%")
                
                # Circuit breakers
                if mechanics.get("circuit_breakers"):
                    with st.expander("⚠️ Circuit Breakers"):
                        for cb in mechanics["circuit_breakers"]:
                            st.write(f"**{cb['trigger_type'].replace('_', ' ').title()}**")
                            st.write(f"  - Threshold: {cb['threshold_value']} {cb['threshold_unit']}")
                            st.write(f"  - Action: {cb['action']}")
                
                # Innovation fund
                if mechanics.get("innovation_fund"):
                    with st.expander("🚀 Innovation Fund"):
                        fund = mechanics["innovation_fund"]
                        st.write(f"- **Funding Range:** {fund['funding_min_pct']}% - {fund['funding_max_pct']}%")
                        st.write(f"- **Prize Range:** ${fund['prize_min_dollars']:,.0f} - ${fund['prize_max_dollars']:,.0f}")
                        st.write(f"- **Annual Cap:** {fund['annual_cap_pct']}%")
                
                # Healthcare targets
                with st.expander("🎯 Healthcare Targets"):
                    st.write(f"**Healthcare Spending Target:** {mechanics.get('target_spending_pct_gdp', 'N/A')}% GDP")
                    st.write(f"**Target Year:** {mechanics.get('target_spending_year', 'N/A')}")
                    st.write(f"**Zero Out-of-Pocket:** {'✓ Yes' if mechanics.get('zero_out_of_pocket') else '✗ No'}")
                    st.write(f"**Universal Coverage:** {'✓ Yes' if mechanics.get('universal_coverage') else '✗ No'}")

                # Tax mechanics
                if mechanics.get("tax_mechanics"):
                    tax = mechanics["tax_mechanics"]
                    with st.expander("💵 Tax Mechanics"):
                        if tax.get("wealth_tax_rate"):
                            st.write(f"- Wealth tax rate: {tax['wealth_tax_rate']*100:.2f}%")
                        if tax.get("consumption_tax_rate"):
                            st.write(f"- Consumption tax: {tax['consumption_tax_rate']*100:.2f}%")
                        if tax.get("carbon_tax_per_ton"):
                            st.write(f"- Carbon tax: ${tax['carbon_tax_per_ton']}/ton")
                        if tax.get("financial_transaction_tax_rate"):
                            st.write(f"- FTT: {tax['financial_transaction_tax_rate']*100:.2f}%")
                        if tax.get("income_tax_changes"):
                            st.json(tax.get("income_tax_changes"))

                # Social Security mechanics
                if mechanics.get("social_security_mechanics"):
                    ss = mechanics["social_security_mechanics"]
                    with st.expander("🧓 Social Security Mechanics"):
                        if ss.get("payroll_tax_rate"):
                            st.write(f"- Payroll tax rate: {ss['payroll_tax_rate']*100:.2f}%")
                        if ss.get("payroll_tax_cap_change"):
                            st.write(f"- Payroll tax cap change: {ss['payroll_tax_cap_change']}")
                        if ss.get("full_retirement_age"):
                            st.write(f"- FRA: {ss['full_retirement_age']}")
                        if ss.get("cola_adjustments"):
                            st.write(f"- COLA: {ss['cola_adjustments']}")
                        if ss.get("benefit_formula_changes"):
                            st.json(ss.get("benefit_formula_changes"))
                        if ss.get("means_testing_enabled"):
                            threshold = ss.get("means_testing_threshold")
                            st.write(f"- Means testing: enabled{f' at ${threshold:,.0f}' if threshold else ''}")

                # Spending/Medicaid mechanics
                if mechanics.get("spending_mechanics"):
                    sp = mechanics["spending_mechanics"]
                    with st.expander("🏛️ Spending/Medicaid Mechanics"):
                        if sp.get("defense_spending_change") is not None:
                            st.write(f"- Defense change: {sp['defense_spending_change']*100:+.1f}%")
                        if sp.get("nondefense_discretionary_change") is not None:
                            st.write(f"- Non-defense change: {sp['nondefense_discretionary_change']*100:+.1f}%")
                        st.write(f"- Medicaid expansion: {'Yes' if sp.get('medicaid_expansion') else 'No/Not detected'}")
                        st.write(f"- Block grant: {'Yes' if sp.get('medicaid_block_grant') else 'No'}")
                        st.write(f"- Per-capita cap: {'Yes' if sp.get('medicaid_per_capita_cap') else 'No'}")
                        if sp.get("medicaid_fmap_change") is not None:
                            st.write(f"- FMAP change: {sp['medicaid_fmap_change']:+.1f} pp")
                        if sp.get("medicaid_waivers"):
                            st.write("- Waivers detected")
                        if sp.get("national_health_fund"):
                            st.write("- National health fund detected (consolidated financing)")
                        if sp.get("medicare_transfer"):
                            st.write("- Medicare funding redirected into health fund")
                        if sp.get("social_security_health_transfer"):
                            st.write("- Social Security payroll redirected to health fund")
                        if sp.get("payroll_to_health_fund") and not sp.get("social_security_health_transfer"):
                            st.write("- Payroll contributions allocated to health fund")
            else:
                # Legacy format - show old parameters
                with st.expander("📊 Extracted Parameters"):
                    st.json(params)
                
                with st.expander("💰 Fiscal Impact Estimates"):
                    for desc, amount in extraction.fiscal_impact_estimates.items():
                        st.write(f"- **{desc}**: ${amount:,.0f}B")
            
            # Create policy from extraction
            st.divider()
            st.subheader("Create Policy from Extraction")
            
            # Show the policy type that was selected
            st.info(f"📌 **Policy Type:** {st.session_state.get('selected_policy_type', policy_type).upper()}")
            
            policy_name = st.text_input(
                "Policy Name:",
                value=st.session_state.get('uploaded_filename', uploaded_file.name).replace(".pdf", "")
            )
            
            if st.button("➕ Create Policy"):
                try:
                    processor = PolicyPDFProcessor()
                    selected_type = st.session_state.get('selected_policy_type', policy_type)
                    policy = processor.create_policy_from_extraction(
                        extraction, 
                        policy_name,
                        policy_type=selected_type
                    )
                    
                    # Set the category to "Uploaded Policies" for PDFs
                    policy.category = "Uploaded Policies"
                    
                    library = PolicyLibrary()
                    if library.add_policy(policy):
                        st.success(f"✓ Policy '{policy_name}' created and saved!")
                        st.info(f"Policy has {len(policy.parameters)} parameters. Edit them in Custom Policy Builder.")
                        st.info("Navigate to 'Healthcare' or 'Policy Comparison' page to use this policy.")
                        
                        # Clear session state
                        st.session_state.policy_extraction = None
                        st.session_state.uploaded_filename = None
                        st.session_state.selected_policy_type = None
                        
                        # Force Streamlit to refresh
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"Policy '{policy_name}' already exists.")
                except Exception as e:
                    st.error(f"Error creating policy: {str(e)}")
                    st.info(f"Full error: {type(e).__name__}: {e}")
    
    # Example policies
    st.divider()
    st.subheader("📋 Example: Policy Structure")
    
    example = """
    The system can extract parameters from policies like:
    
    **United States Galactic Health Act of 2025**
    - Universal coverage: 100% of population
    - Out-of-pocket maximum: $0
    - Health spending target: 7% of GDP
    - Pharmaceutical cost reduction: 15%
    - Innovation fund: 3% of budget
    
    Upload your policy PDF to automatically extract these parameters!
    """
    st.info(example)


def page_policy_recommendations():
    # Policy recommendation engine based on fiscal goals
    st.title("Recommendation Engine: Find Your Ideal Policy")
    
    st.markdown(
        "\n".join([
            "Get personalized policy recommendations based on your fiscal priorities.",
            "The engine scores policies across multiple dimensions.",
        ])
    )
    
    from core.policy_enhancements import (
        PolicyRecommendationEngine, 
        FiscalGoal
    )
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        st.info("Your uploaded policy will be evaluated against the selected fiscal goal.")
    
    st.divider()
    
    # Goal selector
    goal = st.selectbox(
        "What is your primary fiscal goal?",
        [
            "Minimize Deficit",
            "Maximize Revenue",
            "Reduce Spending",
            "Balance Budget",
            "Sustainable Debt",
            "Growth-Focused",
            "Equity-Focused",
        ],
        format_func=lambda x: {
            "Minimize Deficit": "Minimize Deficit (fastest path to balance)",
            "Maximize Revenue": "Maximize Revenue (increase taxes/fees)",
            "Reduce Spending": "Reduce Spending (cut programs)",
            "Balance Budget": "Balance Budget (both revenue and spending)",
            "Sustainable Debt": "Sustainable Debt (long-term stability)",
            "Growth-Focused": "Growth-Focused (prioritize economic growth)",
            "Equity-Focused": "Equity-Focused (progressive policies)",
        }.get(x, x)
    )
    
    goal_map = {
        "Minimize Deficit": FiscalGoal.MINIMIZE_DEFICIT,
        "Maximize Revenue": FiscalGoal.MAXIMIZE_REVENUE,
        "Reduce Spending": FiscalGoal.REDUCE_SPENDING,
        "Balance Budget": FiscalGoal.BALANCE_BUDGET,
        "Sustainable Debt": FiscalGoal.SUSTAINABLE_DEBT,
        "Growth-Focused": FiscalGoal.GROWTH_FOCUSED,
        "Equity-Focused": FiscalGoal.EQUITY_FOCUSED,
    }
    
    engine = PolicyRecommendationEngine()
    
    # Score some example policies
    engine.score_policy(
        policy_name="Progressive Tax Reform",
        deficit_reduction=150.0,
        revenue_change=5.0,
        spending_change=0.0,
        growth_impact=-0.3,
        equity_impact="progressive",
        feasibility=60.0,
    )
    
    engine.score_policy(
        policy_name="Spending Efficiency Program",
        deficit_reduction=75.0,
        revenue_change=0.0,
        spending_change=-3.0,
        growth_impact=0.5,
        equity_impact="neutral",
        feasibility=65.0,
    )
    
    engine.score_policy(
        policy_name="Healthcare Cost Control",
        deficit_reduction=120.0,
        revenue_change=2.0,
        spending_change=-5.0,
        growth_impact=0.2,
        equity_impact="progressive",
        feasibility=55.0,
    )
    
    engine.score_policy(
        policy_name="Growth-First Strategy",
        deficit_reduction=50.0,
        revenue_change=-2.0,
        spending_change=-1.0,
        growth_impact=1.5,
        equity_impact="regressive",
        feasibility=70.0,
    )
    
    # Get recommendations
    recommended = engine.recommend_policies(goal_map[goal], num_recommendations=3)
    
    # Display recommendations
    st.subheader("Top Recommendations")
    
    for i, policy in enumerate(recommended, 1):
        with st.expander(f"{i}. {policy.policy_name} - Score: {policy.overall_score:.0f}/100", expanded=(i==1)):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Fiscal Impact", f"${policy.fiscal_impact:,.0f}B/yr", "deficit reduction")
            with col2:
                st.metric("Sustainability", f"{policy.sustainability:.0f}%")
            with col3:
                st.metric("Feasibility", f"{policy.feasibility:.0f}%")
            with col4:
                st.metric("Equity Score", f"{policy.equity_score:.0f}%")
            
            st.write("**Growth Impact:**", f"{policy.growth_impact:+.1f}%")
            
            st.write("**Why this policy?**")
            reasoning = engine.get_policy_reasoning(policy.policy_name)
            for reason in reasoning:
                st.write(f"- {reason}")


def page_scenario_explorer():
    # Interactive scenario explorer for comparing multiple policy scenarios
    st.title("Scenario Explorer: Compare Policy Impacts")
    
    st.markdown(
        "\n".join([
            "Create and compare multiple policy scenarios side-by-side with real-time calculations.",
        ])
    )
    
    from core.policy_enhancements import InteractiveScenarioExplorer, PolicyImpactCalculator
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        st.info("Your uploaded policy will be used as the baseline for scenario comparison.")
    
    st.divider()
    
    explorer = InteractiveScenarioExplorer()
    
    # Pre-configured scenarios
    scenarios = {
        "Status Quo": {"revenue": 0, "spending": 0},
        "Tax Reform (+5%)": {"revenue": 5, "spending": 0},
        "Spending Cut (-3%)": {"revenue": 0, "spending": -3},
        "Balanced Package": {"revenue": 3, "spending": -2},
    }
    
    # Let user create custom scenario
    st.subheader("Create Custom Scenario")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        scenario_name = st.text_input("Scenario name:", "My Scenario")
    
    with col2:
        revenue_change = st.slider(
            "Revenue change (%):",
            min_value=-10.0,
            max_value=20.0,
            value=0.0,
            step=0.5,
        )
    
    with col3:
        spending_change = st.slider(
            "Spending change (%):",
            min_value=-20.0,
            max_value=10.0,
            value=0.0,
            step=0.5,
        )
    
    if st.button("Add Custom Scenario"):
        scenarios[scenario_name] = {"revenue": revenue_change, "spending": spending_change}
        st.success(f"Added scenario: {scenario_name}")
    
    # Add scenarios to explorer
    for name, params in scenarios.items():
        explorer.add_scenario(
            name=name,
            revenue_change_pct=params["revenue"],
            spending_change_pct=params["spending"],
        )
    
    # Calculate all scenarios
    explorer.calculate_all_scenarios(years=10)
    
    # Display summary
    st.subheader("Scenario Comparison")
    summary_df = explorer.get_scenario_summary()
    st.dataframe(summary_df, width="stretch")
    
    # Add scenario diff viewer
    st.subheader("Scenario Diff View")
    from ui.scenario_diff_viewer import ScenarioDiffViewer
    
    diff_viewer = ScenarioDiffViewer()
    
    # Add all scenarios to diff viewer
    for name, params in scenarios.items():
        diff_viewer.add_scenario(name, params)
    
    # Two-scenario comparison
    col1, col2 = st.columns(2)
    with col1:
        scenario_1 = st.selectbox("Compare scenario 1:", list(scenarios.keys()), key="scenario_1")
    with col2:
        scenario_2 = st.selectbox("Compare scenario 2:", list(scenarios.keys()), key="scenario_2", index=1 if len(scenarios) > 1 else 0)
    
    if scenario_1 != scenario_2:
        diff = diff_viewer.calculate_diff(scenario_1, scenario_2)
        diff_viewer.render_streamlit_diff(diff)
    
    # Multi-scenario comparison
    st.write("---")
    st.write("**Multi-Scenario Comparison** (Compare 3+ scenarios)")
    selected_scenarios = st.multiselect(
        "Select scenarios to compare:",
        list(scenarios.keys()),
        default=list(scenarios.keys())[:3] if len(scenarios) >= 3 else list(scenarios.keys()),
        key="multi_scenario_comparison"
    )
    
    if len(selected_scenarios) >= 2:
        diff_viewer.render_streamlit_multi_comparison(selected_scenarios)
    
    # Chart: Deficit by scenario
    st.subheader("10-Year Cumulative Deficit by Scenario")
    
    chart_data = []
    for name, df in explorer.results.items():
        chart_data.append({
            "Scenario": name,
            "Total Deficit": df["deficit"].sum(),
        })
    
    chart_df = pd.DataFrame(chart_data).sort_values("Total Deficit")
    
    fig = px.bar(
        chart_df,
        x="Scenario",
        y="Total Deficit",
        title="Cumulative 10-Year Deficit by Scenario",
        labels={"Total Deficit": "Deficit ($B)"},
        color="Total Deficit",
        color_continuous_scale="RdYlGn_r",
    )
    apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
    st.plotly_chart(fig, width="stretch")
    
    # Show best scenario
    st.subheader("Best Scenario")
    best_name, best_df = explorer.get_best_scenario("lowest_deficit")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Scenario", best_name)
    with col2:
        st.metric("10-Year Deficit", f"${best_df['deficit'].sum():,.0f}B")
    with col3:
        st.metric("Avg Annual Deficit", f"${best_df['deficit'].mean():,.0f}B")
    
    # Detailed year-by-year for best scenario
    st.subheader(f"Year-by-Year: {best_name}")
    
    display_df = best_df[["year", "revenue", "spending", "deficit"]].copy()
    display_df.columns = ["Year", "Revenue ($B)", "Spending ($B)", "Deficit ($B)"]
    display_df = display_df.round(1)
    st.dataframe(display_df, width="stretch")


def page_impact_calculator():
    # Real-time policy impact calculator
    st.title("Impact Calculator: Measure Policy Effects")
    
    st.markdown(
        "\n".join([
            "Adjust policy parameters and instantly see fiscal impact over time.",
        ])
    )
    
    from core.policy_enhancements import PolicyImpactCalculator
    from core.data_loader import load_real_data
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        st.info("The impact calculator will evaluate this policy's fiscal effects.")
    
    st.divider()
    
    # Get baseline data
    data = load_real_data()
    base_revenue = data.cbo.total_revenue
    base_spending = data.cbo.total_spending
    
    # Parameter sliders
    st.subheader("Policy Parameters")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        revenue_change = st.slider(
            "Revenue change (%):",
            min_value=-15.0,
            max_value=30.0,
            value=0.0,
            step=1.0,
            help="How much to increase or decrease total federal revenue",
        )
    
    with col2:
        spending_change = st.slider(
            "Spending change (%):",
            min_value=-30.0,
            max_value=15.0,
            value=0.0,
            step=1.0,
            help="How much to increase or decrease total federal spending",
        )
    
    with col3:
        years = st.slider(
            "Projection years:",
            min_value=1,
            max_value=30,
            value=10,
            step=1,
        )
    
    # Calculate impact
    impact_df = PolicyImpactCalculator.calculate_impact(
        base_revenue,
        base_spending,
        revenue_change,
        spending_change,
        years=years,
    )
    
    # Key metrics
    st.subheader("Impact Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    baseline_deficit = base_spending - base_revenue
    final_deficit = impact_df["deficit"].iloc[-1]
    total_deficit = impact_df["deficit"].sum()
    savings = -impact_df["cumulative_savings"].iloc[-1]
    
    with col1:
        st.metric(
            "Baseline Annual Deficit",
            f"${baseline_deficit:,.0f}B",
            "-"
        )
    
    with col2:
        st.metric(
            f"Year {years} Deficit",
            f"${final_deficit:,.0f}B",
            f"${final_deficit - baseline_deficit:+,.0f}B"
        )
    
    with col3:
        st.metric(
            f"{years}-Year Total Deficit",
            f"${total_deficit:,.0f}B",
        )
    
    with col4:
        st.metric(
            f"Cumulative Savings",
            f"${savings:,.0f}B",
        )
    
    # Charts
    st.subheader("Fiscal Projections")
    
    # Revenue vs Spending
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=impact_df["year"],
        y=impact_df["revenue"],
        name="Revenue",
        mode="lines",
        line=dict(color="green", width=3),
    ))
    fig1.add_trace(go.Scatter(
        x=impact_df["year"],
        y=impact_df["spending"],
        name="Spending",
        mode="lines",
        line=dict(color="red", width=3),
    ))
    fig1.update_layout(
        title="Revenue vs Spending Over Time",
        xaxis_title="Year",
        yaxis_title="Amount ($B)",
        hovermode="x unified",
    )
    apply_plotly_theme(fig1, st.session_state.settings.get('theme', 'light'))
    st.plotly_chart(fig1, width="stretch")
    
    # Deficit trend
    fig2 = px.bar(
        impact_df,
        x="year",
        y="deficit",
        title="Annual Deficit",
        labels={"year": "Year", "deficit": "Deficit ($B)"},
        color="deficit",
        color_continuous_scale="Reds",
    )
    apply_plotly_theme(fig2, st.session_state.settings.get('theme', 'light'))
    st.plotly_chart(fig2, width="stretch")
    
    # Data table
    st.subheader("Year-by-Year Details")
    
    display_df = impact_df[["year", "revenue", "spending", "deficit"]].copy()
    display_df.columns = ["Year", "Revenue ($B)", "Spending ($B)", "Deficit ($B)"]
    display_df = display_df.round(1)
    st.dataframe(display_df, width="stretch", height=400)


def page_monte_carlo_scenarios():
    # Advanced Monte Carlo scenario analysis
    st.title("Advanced Scenarios: Monte Carlo Uncertainty Analysis")
    
    st.markdown(
        "\n".join([
            "Analyze policies under uncertainty with Monte Carlo simulation.",
            "Generate P10/P90 confidence bounds, stress tests, and sensitivity analysis.",
        ])
    )
    
    from core.monte_carlo_scenarios import (
        MonteCarloPolicySimulator,
        PolicySensitivityAnalyzer,
        StressTestAnalyzer,
    )
    
    # Display uploaded policy selector
    st.markdown("### 📋 Use an Uploaded Policy")
    uploaded_policy, policy_name = show_uploaded_policy_selector()
    
    if uploaded_policy:
        st.success(f"✅ Using policy: **{policy_name}**")
        st.info("Monte Carlo analysis will stress-test this policy under various economic scenarios.")
    
    st.divider()
    
    tabs = st.tabs(["Monte Carlo", "Sensitivity", "Stress Test"])
    
    with tabs[0]:
        st.subheader("Monte Carlo Simulation")
        st.write("Run stochastic analysis on custom policies with confidence bounds.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            revenue_change = st.slider(
                "Revenue change (%):",
                min_value=-15.0,
                max_value=30.0,
                value=0.0,
                step=1.0,
                key="mc_revenue",
            )
        
        with col2:
            spending_change = st.slider(
                "Spending change (%):",
                min_value=-30.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                key="mc_spending",
            )
        
        with col3:
            iterations = st.slider(
                "Monte Carlo iterations:",
                min_value=1_000,
                max_value=100_000,
                value=10_000,
                step=1_000,
            )
        
        if st.button("Run Monte Carlo Simulation"):
            with st.status("🚀 Running Monte Carlo simulation...", expanded=True) as status:
                progress = st.progress(0.1)
                status.update(label="⚙️ Initializing simulator...", state="running", expanded=True)
                simulator = MonteCarloPolicySimulator()
                progress.progress(0.3)
                status.update(label="🧮 Executing simulation runs...", state="running", expanded=True)

                result = simulator.simulate_policy(
                    policy_name="Custom Policy",
                    revenue_change_pct=revenue_change,
                    spending_change_pct=spending_change,
                    years=10,
                    iterations=iterations,
                )
                progress.progress(0.7)
                status.update(label="📊 Preparing results...", state="running", expanded=True)
                
                # Display results
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("Mean Deficit", f"${result.mean_deficit:,.0f}B")
                with col2:
                    st.metric("Median Deficit", f"${result.median_deficit:,.0f}B")
                with col3:
                    st.metric("Std Dev", f"${result.std_dev_deficit:,.0f}B")
                with col4:
                    st.metric("P10 (Best)", f"${result.p10_deficit:,.0f}B")
                with col5:
                    st.metric("P90 (Worst)", f"${result.p90_deficit:,.0f}B")
                
                st.write(f"**Probability of balanced budget:** {result.probability_balanced:.1f}%")
                
                # Distribution chart
                fig = px.histogram(
                    x=result.simulation_results[:, -1],
                    nbins=50,
                    title=f"Distribution of Final Year Deficit ({iterations:,} simulations)",
                    labels={"x": "Deficit ($B)"}
                )
                apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
                
                # Add confidence bounds
                fig.add_vline(x=result.p10_deficit, line_dash="dash", line_color="green", 
                             annotation_text="P10", annotation_position="top")
                fig.add_vline(x=result.p90_deficit, line_dash="dash", line_color="red",
                             annotation_text="P90", annotation_position="top")
                fig.add_vline(x=result.mean_deficit, line_dash="solid", line_color="blue",
                             annotation_text="Mean", annotation_position="top")
                
                st.plotly_chart(fig, width="stretch")
                progress.progress(1.0)
                status.update(label="✅ Monte Carlo simulation complete", state="complete", expanded=False)
    
    with tabs[1]:
        st.subheader("Parameter Sensitivity Analysis")
        st.write("Which policy parameters have the biggest impact on outcomes?")
        
        parameters = {
            "Revenue Change": (-10.0, 20.0),
            "Spending Change": (-30.0, 10.0),
            "Revenue Uncertainty": (2.0, 20.0),
            "Spending Uncertainty": (2.0, 20.0),
        }
        
        analyzer = PolicySensitivityAnalyzer()
        tornado_df = analyzer.tornado_analysis(
            base_revenue=5_980,
            base_spending=6_911,
            parameter_ranges=parameters,
        )
        
        # Tornado chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name="Negative Impact",
            x=tornado_df["Negative Impact"],
            y=tornado_df["Parameter"],
            orientation="h",
            marker=dict(color="rgba(255, 0, 0, 0.7)"),
        ))
        
        fig.add_trace(go.Bar(
            name="Positive Impact",
            x=tornado_df["Positive Impact"],
            y=tornado_df["Parameter"],
            orientation="h",
            marker=dict(color="rgba(0, 0, 255, 0.7)"),
        ))
        
        fig.update_layout(
            title="Parameter Sensitivity (Tornado Chart)",
            xaxis_title="10-Year Deficit Impact ($B)",
            barmode="relative",
            height=400,
        )
        apply_plotly_theme(fig, st.session_state.settings.get('theme', 'light'))
        
        st.plotly_chart(fig, width="stretch")
        
        st.write("**Interpretation:** The longer the bar, the more impact that parameter has on the deficit.")
    
    with tabs[2]:
        st.subheader("Stress Test Analysis")
        st.write("How does the policy perform under adverse economic scenarios?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            revenue_change = st.slider(
                "Revenue change (%):",
                min_value=-15.0,
                max_value=30.0,
                value=0.0,
                step=1.0,
                key="stress_revenue",
            )
        
        with col2:
            spending_change = st.slider(
                "Spending change (%):",
                min_value=-30.0,
                max_value=15.0,
                value=0.0,
                step=1.0,
                key="stress_spending",
            )
        
        stress_analyzer = StressTestAnalyzer()
        stress_df = stress_analyzer.run_stress_test(
            policy_params={
                "revenue_change_pct": revenue_change,
                "spending_change_pct": spending_change,
            }
        )
        
        st.dataframe(stress_df, width="stretch")
        
        st.write("**Stress Scenarios:**")
        st.write("- **Recession:** 10% revenue drop, 5% spending increase")
        st.write("- **Inflation:** Growth reduction, interest rate increase")
        st.write("- **Demographic Shock:** Beneficiary surge, coverage challenges")
        st.write("- **Market Correction:** General deficit pressures")
        st.write("- **Perfect Storm:** Combined worst-case scenario")


def page_report_generation():
    # Report generation page
    st.title("Report Generation")
    st.write("Generate comprehensive PDF and Excel reports from policy analysis.")

    from core.policy_builder import (
        ScenarioBundleLibrary,
        build_policy_comparison_table,
        build_scenario_bundle_zip,
    )

    _, policy_library = get_policy_library_policies()
    available_policies = policy_library.list_policies()
    scenario_lib = ScenarioBundleLibrary()
    saved_bundles = scenario_lib.list_bundles()

    st.subheader("Select policies for this report")
    col_pick, col_load = st.columns([2, 1])
    with col_pick:
        st.multiselect(
            "Policies to include",
            options=available_policies,
            default=available_policies[:2] if len(available_policies) >= 2 else available_policies,
            help="These policies will be compared and exported in the report",
            key="report_policy_picker",
        )
        selected_policy_names = st.session_state.get("report_policy_picker", [])
    with col_load:
        bundle_choice = st.selectbox(
            "Load saved scenario",
            options=["<none>"] + saved_bundles,
            index=0,
        )
        if bundle_choice != "<none>":
            bundle = scenario_lib.get_bundle(bundle_choice)
            if bundle:
                selected_policy_names = [name for name in bundle.policy_names if name in available_policies]
                st.session_state["report_policy_picker"] = selected_policy_names
                st.info(f"Loaded bundle '{bundle_choice}'")
                st.rerun()
    
    # Report type selection (buttons)
    report_options = ["Policy Summary", "Full Analysis", "Comparative Analysis"]
    if "report_type" not in st.session_state:
        st.session_state["report_type"] = report_options[0]
    st.write("Select Report Type:")
    report_cols = st.columns(len(report_options))
    for idx, opt in enumerate(report_options):
        if report_cols[idx].button(opt, key=f"report_type_{opt}"):
            st.session_state["report_type"] = opt
    report_type = st.session_state["report_type"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Report Details")
        
        report_title = st.text_input(
            "Report Title",
            value="Fiscal Policy Analysis Report"
        )
        
        report_author = st.text_input(
            "Author",
            value="PoliSim Analysis Team"
        )
        
        report_description = st.text_area(
            "Description",
            value="Comprehensive analysis of fiscal policy scenarios and impacts."
        )
    
    with col2:
        st.subheader("Export Options")
        
        export_pdf = st.checkbox("Export as PDF", value=True)
        export_excel = st.checkbox("Export as Excel", value=True)
        export_html = st.checkbox("Export as HTML", value=True)
        export_json = st.checkbox("Export as JSON", value=False)
        
        st.write("**Report Sections:**")
        include_projections = st.checkbox("10-Year Projections", value=True)
        include_sensitivity = st.checkbox("Sensitivity Analysis", value=True)
        include_scenarios = st.checkbox("Scenario Comparison", value=True)
        include_monte_carlo = st.checkbox("Monte Carlo Results", value=True)
        include_recommendations = st.checkbox("Recommendations", value=True)

    # Precompute bundle download for convenience
    selected_policies_for_bundle = [
        policy_library.get_policy(name)
        for name in st.session_state.get("report_policy_picker", [])
        if policy_library.get_policy(name)
    ]
    if selected_policies_for_bundle:
        bundle_preview_df = build_policy_comparison_table(selected_policies_for_bundle)
        bundle_zip = build_scenario_bundle_zip(selected_policies_for_bundle, bundle_preview_df)
        st.download_button(
            "⬇️ Download scenario bundle (zip)",
            data=bundle_zip,
            file_name="report_scenario_bundle.zip",
            mime="application/zip",
            help="Bundle of selected policies plus comparison CSV/JSON for external tools",
        )
    
    if st.button("Generate Report", type="primary"):
        with st.status("📄 Building report...", expanded=True) as status:
            progress = st.progress(0.1)
            try:
                from core.report_generator import ComprehensiveReportBuilder, ReportMetadata
                
                # Create metadata
                metadata = ReportMetadata(
                    title=report_title,
                    author=report_author,
                    description=report_description,
                )
                progress.progress(0.2)
                status.update(label="🧭 Preparing report metadata...", state="running", expanded=True)
                
                selected_policies = [
                    policy_library.get_policy(name)
                    for name in selected_policy_names
                    if policy_library.get_policy(name)
                ]

                if not selected_policies:
                    st.error("Select at least one policy to generate a report.")
                    return

                # Create builder
                builder = ComprehensiveReportBuilder(metadata)
                progress.progress(0.3)
                status.update(label="✍️ Drafting content sections...", state="running", expanded=True)
                
                # Add executive summary based on report type
                scenario_label = ", ".join(selected_policy_names) if selected_policy_names else "No policies"
                if report_type == "Policy Summary":
                    summary_text = (
                        f"This report summarizes the selected policies ({scenario_label}). "
                        "It captures parameter deltas, metadata, and comparison tables derived from "
                        "the Custom Policy Builder."
                    )
                elif report_type == "Full Analysis":
                    summary_text = (
                        f"This comprehensive report uses the Custom Policy Builder data for: {scenario_label}. "
                        "It includes metadata snapshots, parameter spreads, and comparison tables to inform "
                        "downstream fiscal simulations."
                    )
                else:
                    summary_text = (
                        f"This report compares multiple policy scenarios ({scenario_label}) to highlight "
                        "differences across parameters and categories for rapid review."
                    )
                
                builder.add_executive_summary(summary_text)
                
                # Derive simple impact proxies from the first selected policy
                base_policy = selected_policies[0]
                values = [param.value for param in base_policy.parameters.values()]
                revenue_impact = float(sum(v for v in values if v >= 0))
                spending_impact = float(sum(v for v in values if v < 0))
                deficit_impact = revenue_impact + spending_impact

                builder.add_policy_overview(
                    policy_name=base_policy.name,
                    revenue_impact=revenue_impact,
                    spending_impact=spending_impact,
                    deficit_impact=deficit_impact,
                )
                progress.progress(0.45)
                status.update(label="📊 Adding projections and analysis...", state="running", expanded=True)
                
                # Prepare derived tables from selected policies
                comparison_df = build_policy_comparison_table(selected_policies)

                metadata_rows = []
                for policy in selected_policies:
                    metadata_rows.append({
                        "Policy": policy.name,
                        "Type": policy.policy_type.value,
                        "Parameters": len(policy.parameters),
                        "Author": policy.author,
                        "Created": policy.created_date,
                    })
                metadata_df = pd.DataFrame(metadata_rows)

                # Parameter spread table to show where policies diverge most
                spread_rows = []
                spread_df = pd.DataFrame()  # Initialize as empty
                
                # Only calculate spread if we have multiple policies
                if len(selected_policies) > 1:
                    for param in sorted({p for policy in selected_policies for p in policy.parameters.keys()}):
                        values = [policy.parameters[param].value for policy in selected_policies if param in policy.parameters]
                        if len(values) >= 2:
                            spread_rows.append({
                                "Parameter": param,
                                "Min": float(np.min(values)),
                                "Max": float(np.max(values)),
                                "Spread": float(np.max(values) - np.min(values)),  # Renamed from "Range" to avoid Excel keyword
                                "Policies": len(values),
                            })
                    if spread_rows:
                        spread_df = pd.DataFrame(spread_rows).sort_values(by="Spread", ascending=False).reset_index(drop=True)

                # Add projections if selected (metadata snapshot)
                if include_projections and not metadata_df.empty:
                    builder.add_fiscal_projections(metadata_df)
                
                # Add sensitivity if selected (only if we have multiple policies with variance)
                if include_sensitivity and not spread_df.empty:
                    builder.add_sensitivity_analysis(spread_df)
                
                # Add scenarios if selected
                if include_scenarios and not comparison_df.empty:
                    builder.add_scenario_comparison(comparison_df)
                
                # Add Monte Carlo if selected (use spread stats as proxy)
                if include_monte_carlo:
                    mc_rows = []
                    if not spread_df.empty and "Spread" in spread_df.columns:
                        try:
                            mc_rows.append({"Metric": "Mean Spread", "Value": spread_df["Spread"].mean()})
                            mc_rows.append({"Metric": "Max Spread", "Value": spread_df["Spread"].max()})
                        except Exception:
                            pass
                        mc_rows.append({"Metric": "Parameters Compared", "Value": len(spread_df)})
                    else:
                        mc_rows.append({"Metric": "Parameters Compared", "Value": 0})
                    mc_df = pd.DataFrame(mc_rows)
                    builder.add_monte_carlo_results(mc_df)
                
                # Add recommendations if selected
                if include_recommendations:
                    recommendations_text = (
                        "<b>1. Focus analysis on parameters with the widest ranges.</b> These are the biggest levers across your selected policies.<br/><br/>"
                        "<b>2. Export the scenario CSV/JSON bundle.</b> Feed it into downstream simulators for quantified fiscal impacts.<br/><br/>"
                        "<b>3. Tighten assumptions iteratively.</b> Use the Custom Policy Builder to converge on aligned parameter values before running Monte Carlo engines."
                    )
                    builder.add_recommendations(recommendations_text)
                
                progress.progress(0.65)
                status.update(label="💾 Rendering exports...", state="running", expanded=True)
                
                # Generate reports
                report_dir = Path("reports/generated")
                report_dir.mkdir(parents=True, exist_ok=True)
                
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                
                generated_files = []

                # Persist scenario comparison data for downstream tools
                scenario_dir = report_dir / "scenario_data"
                scenario_dir.mkdir(parents=True, exist_ok=True)
                scenario_timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                comparison_csv = scenario_dir / f"scenario_comparison_{scenario_timestamp}.csv"
                comparison_json = scenario_dir / f"scenario_comparison_{scenario_timestamp}.json"

                if not comparison_df.empty:
                    comparison_df.to_csv(comparison_csv, index=False)
                    comparison_df.to_json(comparison_json, orient="records", indent=2)
                    generated_files.append(("Scenario CSV", comparison_csv))
                    generated_files.append(("Scenario JSON", comparison_json))
                
                # PDF export
                if export_pdf:
                    try:
                        pdf_path = report_dir / f"report_{timestamp}.pdf"
                        builder.generate_pdf(str(pdf_path))
                        generated_files.append(("PDF", pdf_path))
                        st.success(f"PDF report generated: {pdf_path.name}")
                    except Exception as e:
                        st.error(f"PDF generation failed: {type(e).__name__}: {str(e)}\n\nMake sure reportlab is installed: pip install reportlab")
                
                # Excel export
                if export_excel:
                    try:
                        excel_path = report_dir / f"report_{timestamp}.xlsx"
                        builder.generate_excel(str(excel_path))
                        generated_files.append(("Excel", excel_path))
                        st.success(f"Excel report generated: {excel_path.name}")
                    except Exception as e:
                        st.error(f"Excel generation failed: {type(e).__name__}: {str(e)}\n\nMake sure openpyxl is installed: pip install openpyxl")

                # HTML export
                if export_html:
                    try:
                        html_path = report_dir / f"report_{timestamp}.html"
                        builder.generate_html(str(html_path))
                        generated_files.append(("HTML", html_path))
                        st.success(f"HTML report generated: {html_path.name}")
                    except Exception as e:
                        st.error(f"HTML generation failed: {e}")
                
                # JSON export
                if export_json:
                    try:
                        json_path = report_dir / f"report_{timestamp}.json"
                        builder.generate_json(str(json_path))
                        generated_files.append(("JSON", json_path))
                        st.success(f"JSON report generated: {json_path.name}")
                    except Exception as e:
                        st.error(f"JSON generation failed: {e}")
                
                progress.progress(0.9)
                status.update(label="🔗 Preparing download links...", state="running", expanded=True)
                
                # Display download links
                if generated_files:
                    st.subheader("Generated Reports")
                    for file_type, file_path in generated_files:
                        if file_path.exists():
                            with open(file_path, "rb") as f:
                                st.download_button(
                                    label=f"Download {file_type} Report",
                                    data=f.read(),
                                    file_name=file_path.name,
                                    mime="application/octet-stream"
                                )
                
                progress.progress(1.0)
                status.update(label="✅ Report generation complete", state="complete", expanded=False)
        
            except Exception as e:
                status.update(label="❌ Report generation failed", state="error", expanded=True)
                st.error(f"Error generating report: {type(e).__name__}")
                st.write(f"**Details:** {str(e)}")
                st.write(f"**Solution:** Make sure you have reportlab and openpyxl installed:")
                st.code("pip install reportlab openpyxl")


def page_live_analysis():
    """Live Analysis page - Phase 7.2.2 Multi-Agent Swarm Analysis UI.
    
    This page provides real-time visibility into the multi-agent swarm
    analysis process, including:
    - Live event streaming from agents
    - Confidence visualization over time
    - Debate view with conversation threading
    - Disagreement map showing agent positions
    """
    st.title("🔴 Live Analysis")
    st.markdown("""
    Watch AI agents collaborate in real-time to analyze policy documents.
    See their reasoning, debates, and how they reach consensus.
    """)
    
    if not HAS_LIVE_ANALYSIS:
        st.error("Live Analysis components not available. Please check installation.")
        return
    
    # Initialize states
    init_live_analysis_state()
    init_debate_state()
    
    # Create tabs for different views
    tab_live, tab_confidence, tab_debates, tab_map = st.tabs([
        "📡 Live Stream",
        "📊 Confidence Bands",
        "💬 Debates",
        "🗺️ Disagreement Map",
    ])
    
    with tab_live:
        st.markdown("### Real-Time Analysis Stream")
        
        # Check if there's an active analysis
        state = get_live_analysis_state()
        
        if not state.get("active"):
            st.info("""
            **No active analysis running.**
            
            To start a live analysis:
            1. Go to **Policy Upload** and upload a policy document
            2. Select "Analyze with AI Swarm" 
            3. Return here to watch the analysis in real-time
            
            Or click the button below to see a demo of the live analysis interface.
            """)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎮 Run Demo Analysis", type="primary"):
                    _run_demo_analysis()
                    st.rerun()
            with col2:
                if st.button("🔄 Refresh", key="refresh_live"):
                    st.rerun()
        else:
            # Render the live analysis panel
            render_live_analysis()
    
    with tab_confidence:
        st.markdown("### Agent Confidence Over Time")
        st.markdown("""
        This chart shows how each agent's confidence evolves during analysis.
        Watch for convergence moments when agents reach agreement.
        """)
        
        tracker = get_confidence_tracker()
        
        if not tracker.get_dataframe().empty:
            render_confidence_chart(tracker, show_controls=True)
            
            st.divider()
            render_confidence_summary(tracker)
        else:
            st.info("Confidence data will appear here once analysis begins.")
            
            # Show demo button
            if st.button("📊 Load Demo Data", key="demo_confidence"):
                _load_demo_confidence_data()
                st.rerun()
    
    with tab_debates:
        st.markdown("### Agent Debate History")
        st.markdown("""
        When agents disagree, they engage in structured debates to resolve
        their differences. View the conversation threads and see how
        positions evolve through critique and rebuttal.
        """)
        
        from ui.debate_visualization import get_debate_state
        debate_state = get_debate_state()
        
        if debate_state.get("rounds"):
            render_debate_view(show_controls=True)
            
            st.divider()
            render_debate_timeline()
        else:
            st.info("No debates have occurred yet. Debates happen when agents disagree on findings.")
            
            if st.button("💬 Load Demo Debate", key="demo_debate"):
                _load_demo_debate_data()
                st.rerun()
    
    with tab_map:
        st.markdown("### Agent Disagreement Network")
        st.markdown("""
        This network graph visualizes disagreements between agents.
        - **Nodes** represent agents
        - **Edges** represent disagreements
        - **Edge thickness** shows disagreement magnitude
        - **Colors** indicate topic category
        """)
        
        from ui.debate_visualization import get_debate_state
        debate_state = get_debate_state()
        
        if debate_state.get("disagreements"):
            render_disagreement_map(show_legend=True)
        else:
            st.info("No disagreements to visualize yet.")
            
            if st.button("🗺️ Load Demo Map", key="demo_map"):
                _load_demo_debate_data()
                st.rerun()


def _run_demo_analysis():
    """Run a demo analysis with simulated events."""
    from datetime import datetime
    import time
    
    state = get_live_analysis_state()
    state["active"] = True
    state["events"] = []
    state["agents"] = {}
    
    # Set up progress
    from ui.live_analysis_panel import AnalysisProgressState
    state["progress"] = AnalysisProgressState(
        analysis_id="demo-001",
        bill_id="HR-Demo-001",
        stage="analyzing",
        agents_total=4,
        start_time=datetime.now(),
    )
    
    # Add some demo events
    demo_events = [
        {"event_type": "pipeline_started", "data": {"bill_id": "HR-Demo-001"}, "timestamp": datetime.now().isoformat(), "event_id": "e1"},
        {"event_type": "stage_changed", "data": {"stage": "analyzing"}, "timestamp": datetime.now().isoformat(), "event_id": "e2"},
        {"event_type": "agent_started", "data": {"agent_id": "fiscal-1", "agent_type": "fiscal", "agent_label": "Fiscal Analyst", "agent_icon": "💰"}, "timestamp": datetime.now().isoformat(), "event_id": "e3"},
        {"event_type": "agent_started", "data": {"agent_id": "healthcare-1", "agent_type": "healthcare", "agent_label": "Healthcare Expert", "agent_icon": "🏥"}, "timestamp": datetime.now().isoformat(), "event_id": "e4"},
        {"event_type": "agent_started", "data": {"agent_id": "economic-1", "agent_type": "economic", "agent_label": "Economist", "agent_icon": "📈"}, "timestamp": datetime.now().isoformat(), "event_id": "e5"},
        {"event_type": "agent_started", "data": {"agent_id": "social_security-1", "agent_type": "social_security", "agent_label": "SS Analyst", "agent_icon": "👴"}, "timestamp": datetime.now().isoformat(), "event_id": "e6"},
        {"event_type": "agent_thinking", "data": {"agent_id": "fiscal-1", "agent_label": "Fiscal Analyst", "agent_icon": "💰", "thought_label": "Calculating", "content": "Analyzing revenue impact from proposed tax changes using CBO scoring methodology..."}, "timestamp": datetime.now().isoformat(), "event_id": "e7"},
        {"event_type": "agent_thinking", "data": {"agent_id": "healthcare-1", "agent_label": "Healthcare Expert", "agent_icon": "🏥", "thought_label": "Observing", "content": "Reviewing healthcare coverage expansion provisions in Section 3..."}, "timestamp": datetime.now().isoformat(), "event_id": "e8"},
        {"event_type": "agent_finding", "data": {"agent_id": "fiscal-1", "agent_label": "Fiscal Analyst", "agent_icon": "💰", "category": "revenue", "description": "Proposed tax adjustments expected to generate $150B over 10 years", "confidence": 0.85}, "timestamp": datetime.now().isoformat(), "event_id": "e9"},
        {"event_type": "agent_finding", "data": {"agent_id": "healthcare-1", "agent_label": "Healthcare Expert", "agent_icon": "🏥", "category": "coverage", "description": "Medicare expansion would cover an additional 2.3M beneficiaries", "confidence": 0.78}, "timestamp": datetime.now().isoformat(), "event_id": "e10"},
        {"event_type": "agent_thinking", "data": {"agent_id": "economic-1", "agent_label": "Economist", "agent_icon": "📈", "thought_label": "Hypothesizing", "content": "Evaluating behavioral response to tax changes using elasticity estimates..."}, "timestamp": datetime.now().isoformat(), "event_id": "e11"},
        {"event_type": "agent_finding", "data": {"agent_id": "economic-1", "agent_label": "Economist", "agent_icon": "📈", "category": "gdp", "description": "GDP impact estimated at -0.1% to +0.2% depending on implementation timeline", "confidence": 0.72}, "timestamp": datetime.now().isoformat(), "event_id": "e12"},
    ]
    
    for event_data in demo_events:
        event = process_stream_event(event_data)
        state["events"].append(event)
        from ui.live_analysis_panel import update_agent_state
        update_agent_state(state, event)


def _load_demo_confidence_data():
    """Load demo confidence data for visualization."""
    from datetime import datetime, timedelta
    
    tracker = get_confidence_tracker()
    tracker.clear()
    
    # Add confidence points over time
    base_time = datetime.now() - timedelta(minutes=5)
    
    # Fiscal agent confidence evolution
    for i, conf in enumerate([0.6, 0.7, 0.75, 0.8, 0.85, 0.82, 0.85]):
        tracker.add_point(
            agent_id="fiscal-1",
            confidence=conf,
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            stage="analyzing" if i < 4 else "debating",
            timestamp=base_time + timedelta(seconds=i*30),
        )
    
    # Healthcare agent
    for i, conf in enumerate([0.5, 0.6, 0.65, 0.72, 0.75, 0.78, 0.78]):
        tracker.add_point(
            agent_id="healthcare-1",
            confidence=conf,
            agent_type="healthcare",
            agent_label="Healthcare Expert",
            stage="analyzing" if i < 4 else "debating",
            timestamp=base_time + timedelta(seconds=i*30),
        )
    
    # Economic agent
    for i, conf in enumerate([0.55, 0.58, 0.65, 0.68, 0.72, 0.75, 0.76]):
        tracker.add_point(
            agent_id="economic-1",
            confidence=conf,
            agent_type="economic",
            agent_label="Economist",
            stage="analyzing" if i < 4 else "debating",
            timestamp=base_time + timedelta(seconds=i*30),
        )
    
    # Add convergence moment
    tracker.add_convergence_moment(
        convergence_score=0.82,
        previous_score=0.65,
        description="Agents converged on revenue estimate",
        stage="debating",
        timestamp=base_time + timedelta(seconds=180),
    )


def _load_demo_debate_data():
    """Load demo debate data for visualization."""
    rounds, disagreements = create_demo_debate_data()
    
    from ui.debate_visualization import get_debate_state
    state = get_debate_state()
    state["rounds"] = rounds
    state["disagreements"] = disagreements


def main():
    # Main Streamlit app entry point
    if not HAS_STREAMLIT:
        print("Streamlit not installed. Install with: pip install streamlit plotly")
        return
    
    st.set_page_config(
        page_title="CBO 2.0 Fiscal Dashboard",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Sprint 5.4: Initialize authentication
    StreamlitAuth.initialize()

    # Enforce authentication in production mode before rendering the app
    if not StreamlitAuth.is_authenticated():
        StreamlitAuth.show_auth_page()
        return
    
    # M6 Fix: Initialize settings globally for all pages
    initialize_settings()
    
    # Phase 6.6: Initialize teaching mode from settings (session state)
    # Note: Teaching mode state is now managed via session_state in guided_tour_components
    # We just sync the initial settings if teaching_mode_state doesn't exist yet
    if 'teaching_mode_state' not in st.session_state:
        teaching_enabled = st.session_state.settings.get('teaching_mode_enabled', True)
        teaching_level = st.session_state.settings.get('teaching_mode_level', 'beginner')
        st.session_state.teaching_mode_state = {
            'enabled': teaching_enabled,
            'level': teaching_level,
            'guided_tour_active': False,
            'current_tour_id': None,
            'current_step_index': 0,
            'completed_tours': [],
            'show_explanations': True,
            'show_why_it_matters': True,
        }
    
    # Sprint 5.4: Apply theme
    current_theme = st.session_state.settings.get('theme', 'light')
    
    # Apply custom colors if enabled
    custom_colors = None
    if st.session_state.settings.get('custom_theme_enabled', False):
        custom_colors = st.session_state.settings.get('custom_theme_config', None)
    
    apply_theme(current_theme, custom_colors)
    
    # Sprint 5.4: Apply animations if enabled
    animation_enabled = st.session_state.settings.get('animation_enabled', True)
    animation_speed = st.session_state.settings.get('animation_speed', 'normal')
    matrix_font_size = st.session_state.settings.get('matrix_font_size', 16)
    apply_animation(current_theme, animation_enabled, animation_speed, matrix_font_size)
    
    # Sprint 5.4: Show user widget in sidebar
    StreamlitAuth.show_user_widget()
    
    # Phase 6.6: Teaching mode toggle in sidebar
    render_teaching_mode_toggle()
    
    # Sidebar navigation (button-based to avoid radio icons)
    st.sidebar.markdown('<div class="nav-header">Navigation</div>', unsafe_allow_html=True)
    nav_items = [
        "Overview",
        "Healthcare",
        "Social Security",
        "Federal Revenues",
        "Medicare/Medicaid",
        "Discretionary Spending",
        "Combined Outlook",
        "Policy Comparison",
        "---",
        "🔴 Live Analysis",
        "Recommendations",
        "Scenario Explorer",
        "Impact Calculator",
        "Advanced Scenarios",
        "---",
        "Report Generation",
        "Custom Policy Builder",
        "Policy Library Manager",
        "Real Data Dashboard",
        "Policy Upload",
        "---",
        "👤 User Profile",
        "⚙️ Settings",
    ]

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = nav_items[0]

    for item in nav_items:
        if item == "---":
            st.sidebar.markdown('<hr class="nav-hr" />', unsafe_allow_html=True)
            continue
        is_active = st.session_state.get("nav_page") == item
        clicked = st.sidebar.button(
            item,
            key=f"nav_{item}",
            width="stretch",
            type="primary" if is_active else "secondary",
        )
        if clicked:
            st.session_state["nav_page"] = item

    page = st.session_state.get("nav_page", nav_items[0])
    
    # Phase 6.6: Render teaching mode components
    render_tour_overlay()
    if page == "Overview":
        render_welcome_banner()
    
    # Phase 7.3.3: Initialize chat sidebar state
    if HAS_CHAT_UI:
        init_chat_sidebar_state()
    
    # Render pages with chat panel on right side (Phase 7.3.3)
    # Some pages (Settings, User Profile) don't need chat
    pages_without_chat = {"👤 User Profile", "⚙️ Settings"}
    show_chat = page not in pages_without_chat
    
    if page == "Overview":
        render_page_with_chat(page_overview, show_chat)
    elif page == "Healthcare":
        render_page_with_chat(page_healthcare, show_chat)
    elif page == "Social Security":
        render_page_with_chat(page_social_security, show_chat)
    elif page == "Federal Revenues":
        render_page_with_chat(page_federal_revenues, show_chat)
    elif page == "Medicare/Medicaid":
        render_page_with_chat(page_medicare_medicaid, show_chat)
    elif page == "Discretionary Spending":
        render_page_with_chat(page_discretionary_spending, show_chat)
    elif page == "Combined Outlook":
        render_page_with_chat(page_combined_outlook, show_chat)
    elif page == "Policy Comparison":
        render_page_with_chat(page_policy_comparison, show_chat)
    elif page == "🔴 Live Analysis":
        render_page_with_chat(page_live_analysis, show_chat)
    elif page == "Recommendations":
        render_page_with_chat(page_policy_recommendations, show_chat)
    elif page == "Scenario Explorer":
        render_page_with_chat(page_scenario_explorer, show_chat)
    elif page == "Impact Calculator":
        render_page_with_chat(page_impact_calculator, show_chat)
    elif page == "Advanced Scenarios":
        render_page_with_chat(page_monte_carlo_scenarios, show_chat)
    elif page == "Report Generation":
        render_page_with_chat(page_report_generation, show_chat)
    elif page == "Custom Policy Builder":
        render_page_with_chat(page_custom_policy_builder, show_chat)
    elif page == "Policy Library Manager":
        render_page_with_chat(page_library_manager, show_chat)
    elif page == "Real Data Dashboard":
        render_page_with_chat(page_real_data_dashboard, show_chat)
    elif page == "Policy Upload":
        render_page_with_chat(page_policy_upload, show_chat)
    elif page == "👤 User Profile":
        show_user_profile_page()
    elif page == "⚙️ Settings":
        page_settings()


if __name__ == "__main__":
    main()
