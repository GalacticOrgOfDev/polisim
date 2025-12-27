"""
Streamlit Theme System - Refactored Architecture
Provides visual themes with custom CSS and animations.

Features:
- 6 pre-built themes (light, dark, matrix, cyberpunk, nord, solarized)
- Element-based styling system
- CSS injection with theme-specific rules
- Animation support
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import copy


@dataclass
class ElementStyle:
    """Styling configuration for a UI element."""
    background: Optional[str] = None
    color: Optional[str] = None
    border: Optional[str] = None
    border_color: Optional[str] = None
    hover_bg: Optional[str] = None
    hover_color: Optional[str] = None
    hover_border: Optional[str] = None
    active_bg: Optional[str] = None
    active_color: Optional[str] = None
    text_shadow: Optional[str] = None
    box_shadow: Optional[str] = None
    additional_css: Optional[str] = None
    selectors: Optional[List[str]] = None
    radio: Optional[str] = None
    selectbox: Optional[str] = None
    text_input: Optional[str] = None
    slider: Optional[str] = None
    checkbox: Optional[str] = None
    tooltip: Optional[str] = None
    sidebar: Optional[str] = None
    expander: Optional[str] = None
    number_input: Optional[str] = None
    date_input: Optional[str] = None
    multiselect: Optional[str] = None
    file_uploader: Optional[str] = None



@dataclass
class ThemeConfig:
    """Complete theme configuration with element-specific styling."""
    name: str
    id: str
    
    # Core colors
    primary_color: str
    background_color: str
    secondary_background_color: str
    text_color: str
    accent_color: Optional[str] = None
    font_family: str = "sans-serif"
    
    # Element-specific styles
    button: ElementStyle = field(default_factory=ElementStyle)
    radio: ElementStyle = field(default_factory=ElementStyle)
    selectbox: ElementStyle = field(default_factory=ElementStyle)
    text_input: ElementStyle = field(default_factory=ElementStyle)
    slider: ElementStyle = field(default_factory=ElementStyle)
    checkbox: ElementStyle = field(default_factory=ElementStyle)
    tooltip: ElementStyle = field(default_factory=ElementStyle)
    sidebar: ElementStyle = field(default_factory=ElementStyle)
    expander: ElementStyle = field(default_factory=ElementStyle)
    number_input: ElementStyle = field(default_factory=ElementStyle)
    date_input: ElementStyle = field(default_factory=ElementStyle)
    multiselect: ElementStyle = field(default_factory=ElementStyle)
    file_uploader: ElementStyle = field(default_factory=ElementStyle)
    menu: ElementStyle = field(default_factory=ElementStyle)
    
    # Effects
    animation: Optional[str] = None
    effects: Optional[Dict[str, bool]] = None
    needs_transparency: bool = False


# Theme definitions with element-specific styling
THEMES = {
    "light": ThemeConfig(
        name="Light Mode",
        id="light",
        primary_color="#0078D4",  # Windows blue
        background_color="#FFFFFF",  # Pure white
        secondary_background_color="#F0F2F6",  # Classic Windows gray
        text_color="#000000",  # Pure black for maximum readability
        accent_color="#003D99",  # Darker blue for accents
        font_family="'Segoe UI', 'Tahoma', 'MS Sans Serif', sans-serif",
        
        # Buttons - Classic Windows 2000 style with 3D effect
        button=ElementStyle(
            background="#0078D4",
            color="#FFFFFF",
            border="1px solid #003D99",
            hover_bg="#106EBE",
            hover_border="#003D99",
            box_shadow="0 1px 2px rgba(0, 0, 0, 0.15)",
        ),
        
        # Radio buttons - Windows 2000 classic style
        radio=ElementStyle(
            background="#FFFFFF",  # White circle for radio button
            color="#000000",       # Black text
            border_color="#808080",  # Gray border for unchecked
            hover_bg="#E5F1FB",    # Light blue hover for label
            hover_border="#0078D4",  # Blue border on hover
            active_bg="#FFFFFF",   # White circle when checked
            active_color="#0078D4",  # Windows blue dot inside
        ),
        
        # Selectbox/dropdowns - Classic Windows 2000 style
        selectbox=ElementStyle(
            background="#FFFFFF",
            color="#000000",
            border_color="#808080",
            hover_bg="#E5F1FB",
            border="1px solid #808080",
            box_shadow="inset 0 1px 2px rgba(0, 0, 0, 0.1)",
        ),
        
        # Text inputs - Classic Windows 2000 sunken field
        text_input=ElementStyle(
            background="#FFFFFF",
            color="#000000",
            border_color="#808080",
            border="1px solid #808080",
            box_shadow="inset 0 1px 2px rgba(0, 0, 0, 0.1)",
        ),
        
        # Tooltips - Classic Windows yellow tooltip
        tooltip=ElementStyle(
            background="#F0F2F6",
            color="#000000",
            border="1px solid #767676",
            box_shadow="1px 1px 2px rgba(0, 0, 0, 0.2)",
        ),
        
        # Sidebar - Soft grey
        sidebar=ElementStyle(
            background="#F0F2F6",
            color="#000000",
            border="1px solid #D0D0D0",
        ),
        
        # Menus and dropdowns - Windows 2000 style
        menu=ElementStyle(
            background="#F0F2F6",
            color="#000000",
            border="2px solid #FFFFFF",
            hover_bg="#0078D4",
            hover_color="#FFFFFF",
            box_shadow="2px 2px 4px rgba(0, 0, 0, 0.3)",
        ),
        
        # Checkboxes - Windows 2000 classic style
        checkbox=ElementStyle(
            background="#FFFFFF",
            color="#000000",
            border_color="#808080",
            hover_border="#0078D4",
            hover_bg="#E5F1FB",
            active_bg="#0078D4",
            active_color="#FFFFFF",
            box_shadow="inset 0 1px 2px rgba(0, 0, 0, 0.1)",
        ),
        
        # Expanders - Classic Windows 2000 group box
        expander=ElementStyle(
            background="#F0F2F6",
            color="#000000",
            border="2px groove #ACA899",
            hover_bg="#E5F1FB",
            hover_border="2px groove #0078D4",
            box_shadow="0 1px 2px rgba(0, 0, 0, 0.05)",
        ),
        
        # Sliders - Classic Windows 2000 trackbar
        slider=ElementStyle(
            background="#F0F2F6",
            active_color="#0078D4",
            border_color="#808080",
            hover_color="#003D99",
            box_shadow="inset 0 1px 2px rgba(0, 0, 0, 0.1)",
        ),
    ),
    
    "dark": ThemeConfig(
        name="Dark Mode",
        id="dark",
        primary_color="#5A5A5A",  # Streamlit red
        background_color="#0E1117",  # Deep charcoal
        secondary_background_color="#262730",  # Lighter charcoal
        text_color="#FAFAFA",  # Pure white
        accent_color="#414141",  # Lighter red
        font_family="'Segoe UI', '-apple-system', 'Roboto', sans-serif",
        needs_transparency=True,
        
        button=ElementStyle(
            background="#000000",
            color="#191720",
            hover_bg="#1C1B22",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#FAFAFA",
            border_color="#666666",
            hover_border="#262529",
            active_color="#2A2335",
        ),
        
        selectbox=ElementStyle(
            background="#262730",
            color="#FAFAFA",
            border_color="#404040",
        ),
        
        text_input=ElementStyle(
            background="#262730",
            color="#FAFAFA",
            border_color="#404040",
        ),
        
        tooltip=ElementStyle(
            background="#3B3B3B",
            color="#FAFAFA",
            border="1px solid #666666",
        ),
        
        sidebar=ElementStyle(
            background="#262730",
            color="#FAFAFA",
        ),
        
        # Checkboxes
        checkbox=ElementStyle(
            background="transparent",
            color="#FFFFFF",
            border_color="#666666",
            hover_border="#9B9B9B",
            active_bg="#464545",
            active_color="#C4C4C4",
        ),
        
        # Expanders
        expander=ElementStyle(
            background="#262730",
            color="#FAFAFA",
            border="1px solid #404040",
            hover_bg="#2C2C36",
            hover_border="#FF4B4B",
        ),
        
        # Sliders
        slider=ElementStyle(
            background="rgba(255, 75, 75, 0.2)",
            active_color="#FF4B4B",
            border_color="#FF4B4B",
        ),
    ),
    
    "matrix": ThemeConfig(
        name="Matrix AI Theme",
        id="matrix",
        primary_color="#00FF41",
        background_color="#000000",
        secondary_background_color="#0A0A0A",
        text_color="#FFFFFF",  # White text for readability
        accent_color="#00FF41",
        font_family="'Courier New', 'Consolas', monospace",
        animation="falling_symbols",
        effects={"glow": True, "scanlines": False, "text_outline": False},
        needs_transparency=True,
        
        button=ElementStyle(
            background="rgba(0, 255, 65, 0.2)",
            color="#00FF41",
            border="1px solid #00FF41",
            hover_bg="rgba(0, 255, 65, 0.4)",
            text_shadow="0 0 10px #00FF41",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#FFFFFF",  # White radio labels
            border_color="#00FF41",
            hover_border="#39FF14",
            active_color="#39FF14",
        ),
        
        selectbox=ElementStyle(
            background="rgba(0, 0, 0, 0.8)",
            color="#FFFFFF",  # White dropdown text
            border_color="#00FF41",
        ),
        
        text_input=ElementStyle(
            background="rgba(0, 0, 0, 0.8)",
            color="#FFFFFF",  # White input text
            border_color="#00FF41",
        ),
        
        tooltip=ElementStyle(
            background="rgba(0, 0, 0, 0.95)",
            color="#FFFFFF",  # White tooltip text
            border="1px solid #00FF41",
            box_shadow="0 0 10px #00FF41",
        ),
        
        sidebar=ElementStyle(
            background="rgba(10, 10, 10, 0.9)",
            color="#FFFFFF",  # White sidebar text
        ),
        
        # Checkboxes
        checkbox=ElementStyle(
            background="transparent",
            color="#FFFFFF",
            border_color="#00FF41",
            hover_border="#39FF14",
            active_bg="rgba(0, 255, 65, 0.3)",
            active_color="#00FF41",
        ),
        
        # Expanders
        expander=ElementStyle(
            background="rgba(10, 10, 10, 0.8)",
            color="#FFFFFF",
            border="1px solid #00FF41",
            hover_bg="rgba(0, 255, 65, 0.1)",
            hover_border="#39FF14",
        ),
        
        # Sliders
        slider=ElementStyle(
            background="rgba(0, 255, 65, 0.2)",
            active_color="#00FF41",
            border_color="#00FF41",
        ),
    ),
    
    "cyberpunk": ThemeConfig(
        name="Cyberpunk 2077",
        id="cyberpunk",
        primary_color="#FFFF00",  # Neon yellow
        background_color="#0A0E27",  # Deep night blue
        secondary_background_color="#1A1F3A",  # Slightly lighter blue
        text_color="#E0E0E0",  # Bright off-white for readability
        accent_color="#FF00FF",  # Neon magenta
        font_family="'Orbitron', 'Rajdhani', 'Arial Black', sans-serif",
        effects={"glow": True, "neon": True, "vibrant": True},
        needs_transparency=True,
        
        button=ElementStyle(
            background="rgba(255, 255, 0, 0.2)",
            color="#FFFF00",
            border="2px solid #FFFF00",
            hover_bg="rgba(255, 255, 0, 0.4)",
            text_shadow="0 0 10px #FFFF00",
            box_shadow="0 0 20px rgba(255, 255, 0, 0.5)",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#FFFFFF",
            border_color="#FF00FF",
            hover_border="#FFFF00",
            active_color="#FFFF00",
            text_shadow="0 0 5px #FF00FF",
        ),
        
        selectbox=ElementStyle(
            background="rgba(26, 31, 58, 0.8)",
            color="#FFFFFF",
            border_color="#FF00FF",
        ),
        
        text_input=ElementStyle(
            background="rgba(26, 31, 58, 0.8)",
            color="#FFFFFF",
            border_color="#FF00FF",
        ),
        
        tooltip=ElementStyle(
            background="rgba(10, 14, 39, 0.95)",
            color="#FFFF00",
            border="1px solid #FFFF00",
            box_shadow="0 0 15px #FF00FF",
        ),
        
        sidebar=ElementStyle(
            background="rgba(26, 31, 58, 0.9)",
            color="#FFFFFF",
        ),
        
        # Checkboxes
        checkbox=ElementStyle(
            background="transparent",
            color="#FFFF00",
            border_color="#FF00FF",
            hover_border="#FFFF00",
            active_bg="rgba(255, 255, 0, 0.3)",
            active_color="#FFFF00",
        ),
        
        # Expanders
        expander=ElementStyle(
            background="rgba(26, 31, 58, 0.8)",
            color="#FFFFFF",
            border="1px solid #FF00FF",
            hover_bg="rgba(255, 0, 255, 0.1)",
            hover_border="#FFFF00",
        ),
        
        # Sliders
        slider=ElementStyle(
            background="rgba(255, 255, 0, 0.2)",
            active_color="#FFFF00",
            border_color="#FF00FF",
        ),
    ),
    
    "nord": ThemeConfig(
        name="Nordic",
        id="nord",
        primary_color="#88C0D0",  # Frost: Polar blue
        background_color="#2E3440",  # Polar Night: Darkest
        secondary_background_color="#3B4252",  # Polar Night: Dark
        text_color="#ECEFF4",  # Snow Storm: Bright white
        accent_color="#81A1C1",  # Frost: Light blue
        font_family="'Inter', 'SF Pro Display', 'Roboto', sans-serif",
        
        button=ElementStyle(
            background="#88C0D0",
            color="#2E3440",
            hover_bg="#81A1C1",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#ECEFF4",
            border_color="#4C566A",
            hover_border="#88C0D0",
            active_color="#88C0D0",
        ),
        
        selectbox=ElementStyle(
            background="#3B4252",
            color="#ECEFF4",
            border_color="#4C566A",
        ),
        
        text_input=ElementStyle(
            background="#3B4252",
            color="#ECEFF4",
            border_color="#4C566A",
        ),
        
        tooltip=ElementStyle(
            background="#3B4252",
            color="#ECEFF4",
            border="1px solid #4C566A",
        ),
        
        sidebar=ElementStyle(
            background="#3B4252",
            color="#ECEFF4",
        ),
        
        # Checkboxes
        checkbox=ElementStyle(
            background="transparent",
            color="#ECEFF4",
            border_color="#4C566A",
            hover_border="#88C0D0",
            active_bg="#88C0D0",
            active_color="#88C0D0",
        ),
        
        # Expanders
        expander=ElementStyle(
            background="#3B4252",
            color="#ECEFF4",
            border="1px solid #4C566A",
            hover_bg="#434C5E",
            hover_border="#88C0D0",
        ),
        
        # Sliders
        slider=ElementStyle(
            background="rgba(136, 192, 208, 0.2)",
            active_color="#88C0D0",
            border_color="#88C0D0",
        ),
    ),
    
    "solarized": ThemeConfig(
        name="Solarized Dark",
        id="solarized",
        primary_color="#268BD2",  # Blue accent
        background_color="#002B36",  # Base03: Dark background
        secondary_background_color="#073642",  # Base02: Highlighted background
        text_color="#93A1A1",  # Base1: Primary content
        accent_color="#2AA198",  # Cyan accent
        font_family="'Source Code Pro', 'SF Mono', 'Consolas', monospace",
        
        button=ElementStyle(
            background="#268BD2",
            color="#FDF6E3",
            hover_bg="#2AA198",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#839496",
            border_color="#586E75",
            hover_border="#268BD2",
            active_color="#268BD2",
        ),
        
        selectbox=ElementStyle(
            background="#073642",
            color="#839496",
            border_color="#586E75",
        ),
        
        text_input=ElementStyle(
            background="#073642",
            color="#839496",
            border_color="#586E75",
        ),
        
        tooltip=ElementStyle(
            background="#073642",
            color="#93A1A1",
            border="1px solid #586E75",
        ),
        
        sidebar=ElementStyle(
            background="#073642",
            color="#839496",
        ),
        
        # Checkboxes
        checkbox=ElementStyle(
            background="transparent",
            color="#FDF6E3",
            border_color="#586E75",
            hover_border="#268BD2",
            active_bg="#268BD2",
            active_color="#268BD2",
        ),
        
        # Expanders
        expander=ElementStyle(
            background="#073642",
            color="#839496",
            border="1px solid #586E75",
            hover_bg="#002B36",
            hover_border="#268BD2",
        ),
        
        # Sliders
        slider=ElementStyle(
            background="rgba(38, 139, 210, 0.2)",
            active_color="#268BD2",
            border_color="#268BD2",
        ),
    ),
}


def get_theme(theme_id: str) -> ThemeConfig:
    """Get theme configuration by ID."""
    return THEMES.get(theme_id, THEMES["light"])


def get_theme_list() -> list:
    """Get list of available themes."""
    return [{"id": t.id, "name": t.name} for t in THEMES.values()]


def _merge_custom_colors(theme: ThemeConfig, custom_colors: Optional[Dict[str, str]]) -> ThemeConfig:
    """Apply user-provided colors onto a theme copy without mutating globals."""
    if not custom_colors:
        return theme

    theme.primary_color = custom_colors.get('primary_color', theme.primary_color)
    theme.background_color = custom_colors.get('background_color', theme.background_color)
    theme.secondary_background_color = custom_colors.get('secondary_background_color', theme.secondary_background_color)
    theme.text_color = custom_colors.get('text_color', theme.text_color)
    theme.accent_color = custom_colors.get('accent_color', theme.accent_color or theme.primary_color)

    # Align core element styling with the updated palette so custom themes are visible.
    theme.button.background = custom_colors.get('primary_color', theme.button.background)
    theme.button.hover_bg = custom_colors.get('accent_color', custom_colors.get('primary_color', theme.button.hover_bg))
    theme.slider.active_color = custom_colors.get('primary_color', theme.slider.active_color)
    theme.slider.border_color = custom_colors.get('primary_color', theme.slider.border_color)
    theme.checkbox.active_bg = custom_colors.get('primary_color', theme.checkbox.active_bg)
    theme.checkbox.active_color = custom_colors.get('text_color', theme.checkbox.active_color)

    return theme


def _clamp_opacity(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp opacity to a safe range for readability."""
    try:
        return max(min(value, maximum), minimum)
    except Exception:
        return minimum


def apply_theme(theme_id: str, custom_colors: Optional[Dict[str, str]] = None):
    """Apply custom CSS for selected theme using element-based styling."""
    # Create a deep copy to prevent mutating the global THEMES dict
    theme = _merge_custom_colors(copy.deepcopy(get_theme(theme_id)), custom_colors)
    
    # Get transparency settings from session state for animated themes
    settings = st.session_state.get('settings', {})
    bg_opacity = _clamp_opacity(settings.get('bg_opacity', 0.6))
    content_opacity = _clamp_opacity(settings.get('content_opacity', 0.8))
    sidebar_opacity = _clamp_opacity(settings.get('sidebar_opacity', 0.9))
    header_opacity = _clamp_opacity(settings.get('header_opacity', 1.0))
    
    # Calculate background colors
    if theme.needs_transparency:
        # Guard against excessive transparency on dark themes for readability
        bg_opacity = _clamp_opacity(bg_opacity, minimum=0.55)
        content_opacity = _clamp_opacity(content_opacity, minimum=0.65)
        sidebar_opacity = _clamp_opacity(sidebar_opacity, minimum=0.7)
        header_opacity = _clamp_opacity(header_opacity, minimum=0.75)
        bg_color = theme.background_color.lstrip('#')
        r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
        main_bg = f"rgba({r}, {g}, {b}, {bg_opacity})"
        content_bg = f"rgba({min(r+10, 255)}, {min(g+10, 255)}, {min(b+10, 255)}, {content_opacity})"
        sidebar_bg = f"rgba({min(r+10, 255)}, {min(g+10, 255)}, {min(b+10, 255)}, {sidebar_opacity})"
    else:
        main_bg = theme.background_color
        content_bg = theme.secondary_background_color
        sidebar_bg = theme.secondary_background_color

    # Sidebar respects transparency slider even if theme defines a static background
    sidebar_background = sidebar_bg if theme.needs_transparency or theme.sidebar.background is None else theme.sidebar.background

    # Header background respects transparency slider and uses secondary background color
    header_color = theme.secondary_background_color.lstrip('#')
    try:
        hr, hg, hb = int(header_color[0:2], 16), int(header_color[2:4], 16), int(header_color[4:6], 16)
        header_bg = f"rgba({hr}, {hg}, {hb}, {header_opacity})"
    except Exception:
        header_bg = theme.secondary_background_color

    # Title glow colors per theme
    title_glow_map = {
        "light": "#DAA520",  # golden shine
        "matrix": "#00FF41",  # neon green
        "cyberpunk": "#FF00FF",  # magenta neon
        "nord": "#88C0D0",  # ice blue
    }
    title_glow = title_glow_map.get(theme_id, theme.accent_color or theme.primary_color)
    
    # Build CSS with unique ID for theme tracking and removal
    css = f"""
    <style id="polisim-theme-{theme_id}">
    /* Remove old theme styles */
    <![CDATA[
    (function() {{
        const oldStyles = document.querySelectorAll('style[id^="polisim-theme-"]');
        oldStyles.forEach(function(style) {{
            if (style.id !== 'polisim-theme-{theme_id}') {{
                style.remove();
            }}
        }});
    }})();
    ]]>
    
    /* Import web fonts for themes */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@400;500;700;900&family=Rajdhani:wght@400;500;600;700&family=Source+Code+Pro:wght@400;500;600&display=swap');
    
    /* Allow theme background/animation layers (no hard reset) */
    
    /* Core theme: Light Mode - Windows 2000 Classic */
    { 'body {{ background-color: transparent !important; }}' if theme.needs_transparency else '' }
    .stApp {{
        background-color: {main_bg} !important;
        color: {theme.text_color} !important;
        font-family: {theme.font_family};
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: {main_bg} !important;
    }}
    
    [data-testid="stHeader"] {{
        position: relative;
        background-color: {header_bg} !important;
        border-bottom: 1px solid {theme.text_color}33 !important;
        box-shadow: inset 0 1px 0 {theme.text_color}11 !important;
        z-index: 100;
    }}
    
    [data-testid="stToolbar"] {{
        background-color: {header_bg} !important;
        z-index: 99;
    }}
    
    /* Centered product name in header */
    [data-testid="stHeader"]::after {{
        content: "PoliSim";
        position: absolute;
        left: 50%;
        top: 50%;
        transform: translate(-50%, -50%);
        color: {theme.text_color} !important;
        font-weight: 800;
        font-size: 1.6rem;
        letter-spacing: 0.02em;
        pointer-events: none;
        z-index: 101;
        text-shadow: 0 0 6px {title_glow}, 0 0 12px {title_glow};
    }}
    
    h1, h2, h3, h4, h5, h6, p, span, div, label {{
        color: {theme.text_color} !important;
    }}
    
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_background} !important;
        color: {theme.sidebar.color or theme.text_color} !important;
    }}

    /* Sidebar nav header positioned near collapse control */
    section[data-testid="stSidebar"] .nav-header {{
        font-size: 1.05rem;
        font-weight: 700;
        margin: -6px 0 10px 4px;
        display: inline-block;
    }}

    /* Sidebar button stack spacing */
    section[data-testid="stSidebar"] .stButton {{
        margin-bottom: 4px;
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {theme.button.background or theme.primary_color} !important;
        color: {theme.button.color or '#FFFFFF'} !important;
        border: {theme.button.border or 'none'} !important;
        {f'text-shadow: {theme.button.text_shadow} !important;' if theme.button.text_shadow else ''}
        {f'box-shadow: {theme.button.box_shadow} !important;' if theme.button.box_shadow else ''}
    }}
    
    .stButton > button:hover {{
        background-color: {theme.button.hover_bg or theme.accent_color or theme.primary_color} !important;
        {f'border-color: {theme.button.hover_border} !important;' if theme.button.hover_border else ''}
    }}

    /* Sidebar buttons keep contrast on blue background */
    section[data-testid="stSidebar"] .stButton > button {{
        background-color: {theme.button.background or theme.primary_color} !important;
        color: {theme.button.color or '#FFFFFF'} !important;
        border: {theme.button.border or 'none'} !important;
        padding: 0.2rem 0.5rem !important;
        font-size: 0.7rem !important;
        line-height: 1.1 !important;
        min-height: unset !important;
    }}

    /* Force white text inside sidebar buttons on light theme */
    section[data-testid="stSidebar"] .stButton > button span,
    section[data-testid="stSidebar"] .stButton > button p {{
        color: #FFFFFF !important;
    }}

    /* Compact nav section dividers */
    section[data-testid="stSidebar"] hr.nav-hr {{
        margin: 4px 0;
        border: 0;
        border-top: 1px solid {(theme.sidebar.color or theme.text_color)}33;
    }}

    section[data-testid="stSidebar"] .stButton > button:hover {{
        background-color: {theme.button.hover_bg or theme.accent_color or theme.primary_color} !important;
        {f'border-color: {theme.button.hover_border} !important;' if theme.button.hover_border else ''}
    }}
    
    /* Radio labels */
    .stRadio [role="radiogroup"] label {{
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 4px 6px !important;
        color: {theme.text_color} !important;
        background-color: transparent !important;
        white-space: nowrap !important;
    }}

    .stRadio [role="radiogroup"] label span,
    .stRadio [role="radiogroup"] label p,
    .stRadio [role="radiogroup"] label div:last-child {{
        color: {theme.text_color} !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        line-height: 1.25 !important;
    }}

    .stRadio [role="radiogroup"] label:hover {{
        background-color: {theme.radio.hover_bg or theme.secondary_background_color} !important;
    }}

    /* Baseweb radio container */
    .stRadio [data-baseweb="radio"] {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 8px !important;
    }}

    /* Hide native input but keep accessible */
    .stRadio [data-baseweb="radio"] input[type="radio"] {{
        position: absolute !important;
        opacity: 0 !important;
        width: 16px !important;
        height: 16px !important;
        margin: 0 !important;
        pointer-events: none !important;
    }}

    /* Hide default svg/icon to avoid duplicate circles */
    .stRadio [data-baseweb="radio"] svg {{
        display: none !important;
    }}

    /* Icon circle (first div after input) */
    .stRadio [data-baseweb="radio"] input[type="radio"] + div {{
        border: 2px solid {theme.radio.border_color or '#808080'} !important;
        background-color: {theme.radio.background or '#FFFFFF'} !important;
        width: 16px !important;
        height: 16px !important;
        border-radius: 50% !important;
        position: relative !important;
        flex-shrink: 0 !important;
        box-sizing: border-box !important;
    }}

    .stRadio [data-baseweb="radio"] input[type="radio"] + div:hover {{
        border-color: {theme.radio.hover_border or theme.primary_color} !important;
    }}

    /* Checked circle */
    .stRadio [data-baseweb="radio"] input[type="radio"]:checked + div {{
        background-color: {theme.radio.active_bg or '#FFFFFF'} !important;
        border-color: {theme.radio.active_color or theme.primary_color} !important;
    }}

    /* Dot */
    .stRadio [data-baseweb="radio"] input[type="radio"] + div::after {{
        content: '' !important;
        position: absolute !important;
        width: 8px !important;
        height: 8px !important;
        border-radius: 50% !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        display: none !important;
    }}

    .stRadio [data-baseweb="radio"] input[type="radio"]:checked + div::after {{
        display: block !important;
        background-color: {theme.radio.active_color or theme.primary_color} !important;
    }}

    /* Sidebar navigation radios - keep layout predictable */
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] {{
        display: flex !important;
        flex-direction: column !important;
        gap: 6px !important;
    }}

    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label {{
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        padding: 4px 6px !important;
        color: {theme.text_color} !important;
        background-color: transparent !important;
        border-radius: 4px !important;
        line-height: 1.25 !important;
        white-space: nowrap !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        opacity: 1 !important;
    }}

    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label:hover {{
        background-color: {theme.radio.hover_bg or theme.secondary_background_color} !important;
    }}

    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label span,
    section[data-testid="stSidebar"] .stRadio [role="radiogroup"] label p {{
        display: inline !important;
        color: {theme.text_color} !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        line-height: 1.25 !important;
        opacity: 1 !important;
    }}
    
    /* Selectbox/dropdowns */
    .stSelectbox [data-baseweb="select"] > div {{
        background-color: {theme.selectbox.background or theme.secondary_background_color} !important;
        color: {theme.selectbox.color or theme.text_color} !important;
        border-color: {theme.selectbox.border_color or theme.text_color} !important;
        {f'text-shadow: {theme.selectbox.text_shadow} !important;' if theme.selectbox.text_shadow else ''}
    }}
    
    [data-baseweb="popover"],
    [role="listbox"] {{
        background-color: {theme.selectbox.background or theme.secondary_background_color} !important;
    }}
    
    [role="option"] {{
        background-color: {theme.selectbox.background or theme.secondary_background_color} !important;
        color: {theme.selectbox.color or theme.text_color} !important;
    }}
    
    [role="option"]:hover {{
        background-color: {theme.selectbox.hover_bg or theme.primary_color} !important;
    }}
    
    /* Text inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        background-color: {theme.text_input.background or theme.secondary_background_color} !important;
        color: {theme.text_input.color or theme.text_color} !important;
        border-color: {theme.text_input.border_color or theme.text_color} !important;
    }}
    
    /* Tooltips */
    [data-baseweb="tooltip"] {{
        background-color: {theme.tooltip.background or theme.secondary_background_color} !important;
        color: {theme.tooltip.color or theme.text_color} !important;
        border: {theme.tooltip.border or 'none'} !important;
        {f'box-shadow: {theme.tooltip.box_shadow} !important;' if theme.tooltip.box_shadow else ''}
    }}
    
    button[kind="icon"],
    button[aria-label*="help"],
    .stTooltipIcon {{
        color: {theme.text_color} !important;
    }}
    
    /* Checkboxes */
    .stCheckbox label {{
        color: {theme.text_color} !important;
    }}
    
    .stCheckbox [data-baseweb="checkbox"] > div {{
        border-color: {theme.checkbox.border_color or theme.text_color} !important;
        background-color: {theme.checkbox.background or 'transparent'} !important;
    }}
    
    .stCheckbox [data-baseweb="checkbox"] > div:hover {{
        border-color: {theme.checkbox.hover_border or theme.primary_color} !important;
        background-color: {theme.checkbox.hover_bg or theme.secondary_background_color} !important;
    }}
    
    .stCheckbox input:checked ~ div {{
        background-color: {theme.checkbox.active_bg or theme.primary_color} !important;
        border-color: {theme.checkbox.active_color or theme.primary_color} !important;
    }}
    
    .stCheckbox input:checked ~ div svg {{
        fill: {theme.checkbox.color or '#FFFFFF'} !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {theme.expander.background or theme.secondary_background_color} !important;
        color: {theme.expander.color or theme.text_color} !important;
        border: {theme.expander.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
    }}

    /* Ensure expander summary/title inherits the theme instead of default black bar */
    [data-testid="stExpander"] summary {{
        background-color: {theme.expander.background or theme.secondary_background_color} !important;
        color: {theme.expander.color or theme.text_color} !important;
        border-bottom: {theme.expander.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
        list-style: none !important;
    }}
    [data-testid="stExpander"] summary:hover {{
        background-color: {theme.expander.hover_bg or theme.secondary_background_color} !important;
        color: {theme.expander.hover_color or theme.expander.color or theme.text_color} !important;
    }}

    /* Expander container to prevent dark flash when collapsed */
    [data-testid="stExpander"] > details {{
        background-color: {theme.expander.background or theme.secondary_background_color} !important;
        border: {theme.expander.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
    }}
    [data-testid="stExpander"] > details:hover {{
        background-color: {theme.expander.hover_bg or theme.secondary_background_color} !important;
        border-color: {theme.expander.hover_border or theme.primary_color} !important;
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: {theme.expander.hover_bg or theme.secondary_background_color} !important;
        border-color: {theme.expander.hover_border or theme.primary_color} !important;
    }}
    
    .streamlit-expanderHeader svg {{
        fill: {theme.expander.color or theme.text_color} !important;
    }}
    
    details[open] .streamlit-expanderHeader {{
        border-bottom: {theme.expander.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
    }}
    
    /* Sliders */
    .stSlider [data-baseweb="slider"] {{
        background-color: transparent !important;
    }}
    
    .stSlider [data-baseweb="slider"] [role="slider"] {{
        background-color: {theme.slider.active_color or theme.primary_color} !important;
        border-color: {theme.slider.border_color or theme.primary_color} !important;
    }}
    
    .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] > div {{
        background-color: {theme.slider.active_color or theme.primary_color} !important;
    }}
    
    .stSlider [data-baseweb="slider"] > div > div {{
        background-color: {theme.slider.background or theme.secondary_background_color} !important;
    }}
    
    .stSlider [data-baseweb="slider"] > div > div > div {{
        background-color: {theme.slider.active_color or theme.primary_color} !important;
    }}
    
    /* Multiselect */
    .stMultiSelect [data-baseweb="tag"] {{
        background-color: {theme.primary_color} !important;
        color: {theme.button.color or '#FFFFFF'} !important;
    }}
    
    /* File Uploader */
    .stFileUploader section {{
        border-color: {theme.text_color} !important;
        background-color: {theme.secondary_background_color} !important;
    }}
    
    .stFileUploader section:hover {{
        border-color: {theme.primary_color} !important;
    }}
    
    /* Progress bar */
    .stProgress > div > div {{
        background-color: {theme.primary_color} !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme.secondary_background_color} !important;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {theme.text_color} !important;
    }}
    
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: {theme.secondary_background_color} !important;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {theme.primary_color} !important;
        color: {theme.button.color or '#FFFFFF'} !important;
    }}
    
    /* Dataframe/Table */
    .stDataFrame {{
        background-color: {theme.secondary_background_color} !important;
        color: {theme.text_color} !important;
    }}
    
    /* Metrics */
    .stMetric {{
        background-color: {theme.secondary_background_color} !important;
    }}
    
    .stMetric label {{
        color: {theme.text_color} !important;
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        color: {theme.primary_color} !important;
    }}
    
    /* Header anchor link icons - the chain link buttons that appear next to headers on hover */
    [class*="stMarkdown"] h1 [class*="headerlink"],
    [class*="stMarkdown"] h2 [class*="headerlink"],
    [class*="stMarkdown"] h3 [class*="headerlink"],
    [class*="stMarkdown"] h4 [class*="headerlink"],
    [class*="stMarkdown"] h5 [class*="headerlink"],
    [class*="stMarkdown"] h6 [class*="headerlink"],
    h1 a[href^="#"], h2 a[href^="#"], h3 a[href^="#"],
    h4 a[href^="#"], h5 a[href^="#"], h6 a[href^="#"],
    a[class*="header-anchor"],
    a[class*="anchor"] {{
        background-color: {theme.background_color} !important;
        border: 1px solid {theme.text_color}33 !important;
        padding: 2px 4px !important;
        border-radius: 3px !important;
        opacity: 1 !important;
        visibility: visible !important;
        display: inline-flex !important;
        align-items: center !important;
        transition: background-color 0.2s, border-color 0.2s !important;
    }}
    
    /* Header anchor links on hover - blue background */
    [class*="headerlink"]:hover,
    h1 a[href^="#"]:hover, h2 a[href^="#"]:hover, h3 a[href^="#"]:hover,
    h4 a[href^="#"]:hover, h5 a[href^="#"]:hover, h6 a[href^="#"]:hover,
    a[class*="header-anchor"]:hover,
    a[class*="anchor"]:hover {{
        background-color: {theme.primary_color} !important;
        border-color: {theme.primary_color} !important;
    }}
    
    /* SVG icons inside header anchor links - black by default */
    [class*="headerlink"] svg,
    h1 a[href^="#"] svg, h2 a[href^="#"] svg, h3 a[href^="#"] svg,
    h4 a[href^="#"] svg, h5 a[href^="#"] svg, h6 a[href^="#"] svg,
    a[class*="header-anchor"] svg,
    a[class*="anchor"] svg {{
        fill: {theme.text_color} !important;
        stroke: {theme.text_color} !important;
        opacity: 1 !important;
        visibility: visible !important;
        width: 16px !important;
        height: 16px !important;
        transition: fill 0.2s, stroke 0.2s !important;
    }}
    
    /* SVG icons on hover - white */
    [class*="headerlink"]:hover svg,
    h1 a[href^="#"]:hover svg, h2 a[href^="#"]:hover svg, h3 a[href^="#"]:hover svg,
    h4 a[href^="#"]:hover svg, h5 a[href^="#"]:hover svg, h6 a[href^="#"]:hover svg,
    a[class*="header-anchor"]:hover svg,
    a[class*="anchor"]:hover svg {{
        fill: #FFFFFF !important;
        stroke: #FFFFFF !important;
    }}
    
    /* Menus, Dropdowns, and Three-Dot Menu - Using theme.menu ElementStyle */
    /* Three-dot menu button */
    button[kind="header"],
    button[kind="headerNoPadding"] {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        color: {theme.menu.color or theme.text_color} !important;
        border: {theme.menu.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
    }}
    
    button[kind="header"]:hover,
    button[kind="headerNoPadding"]:hover {{
        background-color: {theme.menu.hover_bg or theme.primary_color} !important;
        color: {theme.menu.hover_color or theme.menu.color or theme.text_color} !important;
    }}
    
    /* Menu container and popover */
    [role="menu"],
    [data-baseweb="menu"],
    [data-baseweb="popover"],
    [class*="popover"],
    [class*="menu"] {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        color: {theme.menu.color or theme.text_color} !important;
        border: {theme.menu.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
        {f'box-shadow: {theme.menu.box_shadow} !important;' if theme.menu.box_shadow else ''}
    }}
    
    /* Menu items */
    [role="menuitem"],
    [data-baseweb="list-item"],
    [class*="menuitem"],
    button[role="menuitem"],
    [data-baseweb="menu"] li,
    [data-baseweb="menu"] button,
    [data-baseweb="menu"] a {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        color: {theme.menu.color or theme.text_color} !important;
        border: none !important;
    }}
    
    /* Menu item hover states */
    [role="menuitem"]:hover,
    [data-baseweb="list-item"]:hover,
    [class*="menuitem"]:hover,
    button[role="menuitem"]:hover,
    [data-baseweb="menu"] li:hover,
    [data-baseweb="menu"] button:hover,
    [data-baseweb="menu"] a:hover {{
        background-color: {theme.menu.hover_bg or theme.primary_color} !important;
        color: {theme.menu.hover_color or '#FFFFFF'} !important;
    }}
    
    /* Specific targeting for Streamlit's three-dot menu dropdown */
    button[aria-haspopup="menu"] ~ div,
    button[aria-haspopup="menu"] + div,
    [data-testid="stHeaderActionElements"] {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        border: {theme.menu.border or '1px solid rgba(255, 255, 255, 0.1)'} !important;
        {f'box-shadow: {theme.menu.box_shadow} !important;' if theme.menu.box_shadow else ''}
    }}
    
    /* Three-dot menu nested items */
    button[aria-haspopup="menu"] ~ div button,
    button[aria-haspopup="menu"] ~ div a,
    button[aria-haspopup="menu"] ~ div [role="menuitem"],
    button[aria-haspopup="menu"] ~ div li,
    [data-testid="stHeaderActionElements"] button,
    [data-testid="stHeaderActionElements"] a {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        color: {theme.menu.color or theme.text_color} !important;
        text-align: left !important;
    }}
    
    button[aria-haspopup="menu"] ~ div button:hover,
    button[aria-haspopup="menu"] ~ div a:hover,
    button[aria-haspopup="menu"] ~ div [role="menuitem"]:hover,
    [data-testid="stHeaderActionElements"] button:hover,
    [data-testid="stHeaderActionElements"] a:hover {{
        background-color: {theme.menu.hover_bg or theme.primary_color} !important;
        color: {theme.menu.hover_color or '#FFFFFF'} !important;
    }}
    
    /* Override Streamlit's emotion-cache classes for menus */
    [class*="emotion-cache"][class*="menu"],
    [role="menu"] [class*="emotion-cache"],
    [data-baseweb="popover"] [class*="emotion-cache"] {{
        background-color: {theme.menu.background or theme.secondary_background_color} !important;
        color: {theme.menu.color or theme.text_color} !important;
    }}
    </style>
    """
    
    # Inject CSS once - base CSS now uses theme.* properties for all elements
    st.markdown(css, unsafe_allow_html=True)


def create_custom_theme(
    name: str,
    primary_color: str,
    background_color: str,
    text_color: str,
    **kwargs
) -> ThemeConfig:
    """Create a custom theme with specified colors."""
    return ThemeConfig(
        name=name,
        id=name.lower().replace(" ", "_"),
        primary_color=primary_color,
        background_color=background_color,
        secondary_background_color=kwargs.get('secondary_bg', background_color),
        text_color=text_color,
        **kwargs
    )


def get_plotly_template(theme_id: str) -> str:
    """
    Get Plotly template name for the theme.
    
    Args:
        theme_id: Theme identifier
    
    Returns:
        Plotly template name
    """
    theme = get_theme(theme_id)
    
    # Map themes to Plotly templates
    if theme.id in ["light"]:
        return "plotly_white"
    elif theme.id in ["dark", "matrix", "cyberpunk", "solarized"]:
        return "plotly_dark"
    elif theme.id == "nord":
        return "seaborn"
    else:
        return "plotly_white"


def apply_plotly_theme(fig, theme_id: str, custom_colors: Optional[Dict[str, str]] = None):
    """
    Apply theme colors to Plotly figure.
    
    Args:
        fig: Plotly figure object
        theme_id: Theme identifier
    
    Returns:
        Modified figure with theme applied
    """
    if custom_colors is None:
        settings = st.session_state.get('settings', {})
        if settings.get('custom_theme_enabled'):
            custom_colors = settings.get('custom_theme_config')

    theme = _merge_custom_colors(copy.deepcopy(get_theme(theme_id)), custom_colors)
    template = get_plotly_template(theme_id)
    
    # Determine grid color based on theme
    if theme.id == "light":
        grid_color = "rgba(0, 0, 0, 0.1)"
        line_color = "#CCCCCC"
    elif theme.id == "matrix":
        grid_color = "rgba(0, 255, 65, 0.15)"
        line_color = "#00FF41"
    elif theme.id == "cyberpunk":
        grid_color = "rgba(255, 0, 255, 0.2)"
        line_color = "#FF00FF"
    elif theme.id == "nord":
        grid_color = "rgba(136, 192, 208, 0.15)"
        line_color = "#4C566A"
    elif theme.id == "solarized":
        grid_color = "rgba(88, 110, 117, 0.3)"
        line_color = "#586E75"
    else:  # dark
        grid_color = "rgba(255, 255, 255, 0.1)"
        line_color = "#404040"
    
    # Apply template
    fig.update_layout(template=template)
    
    # Apply custom colors
    fig.update_layout(
        paper_bgcolor=theme.background_color,
        plot_bgcolor=theme.secondary_background_color,
        font=dict(
            color=theme.text_color,
            family=theme.font_family,
            size=12,
        ),
        title_font=dict(
            color=theme.primary_color,
            size=18,
            family=theme.font_family,
        ),
        xaxis=dict(
            gridcolor=grid_color,
            linecolor=line_color,
            zerolinecolor=line_color,
            tickfont=dict(color=theme.text_color),
            title=dict(font=dict(color=theme.primary_color)),
        ),
        yaxis=dict(
            gridcolor=grid_color,
            linecolor=line_color,
            zerolinecolor=line_color,
            tickfont=dict(color=theme.text_color),
            title=dict(font=dict(color=theme.primary_color)),
        ),
        legend=dict(
            bgcolor=theme.secondary_background_color,
            bordercolor=line_color,
            font=dict(color=theme.text_color),
        ),
        hoverlabel=dict(
            bgcolor=theme.secondary_background_color,
            font=dict(color=theme.text_color, family=theme.font_family),
            bordercolor=theme.primary_color,
        ),
    )
    
    # Update trace colors to match theme palette
    chart_colors = get_chart_colors(theme_id)
    if fig.data:
        for i, trace in enumerate(fig.data):
            if hasattr(trace, 'marker'):
                trace.marker.color = chart_colors[i % len(chart_colors)]
            if hasattr(trace, 'line'):
                if hasattr(trace.line, 'color'):
                    trace.line.color = chart_colors[i % len(chart_colors)]
    
    return fig


def get_chart_colors(theme_id: str, custom_colors: Optional[list] = None) -> list:
    """
    Get color palette for charts based on theme.
    
    Args:
        theme_id: Theme identifier
        custom_colors: Optional custom color palette
    
    Returns:
        List of hex colors for chart series
    """
    if custom_colors:
        return custom_colors
    
    theme = get_theme(theme_id)
    
    # Theme-specific color palettes - carefully chosen for distinction and aesthetics
    if theme.id == "matrix":
        # Matrix: Shades of green with occasional cyan for contrast
        return ["#00FF41", "#39FF14", "#00CC33", "#7FFF00", "#00FFFF", "#00FF7F", "#ADFF2F", "#32CD32"]
    elif theme.id == "cyberpunk":
        # Cyberpunk: Neon yellow, magenta, cyan rotation
        return ["#FFFF00", "#FF00FF", "#00FFFF", "#FF6600", "#FF0099", "#00FF66", "#FF3366", "#FFCC00"]
    elif theme.id == "nord":
        # Nord: Frost blues and Aurora colors
        return ["#88C0D0", "#81A1C1", "#5E81AC", "#BF616A", "#A3BE8C", "#EBCB8B", "#D08770", "#B48EAD"]
    elif theme.id == "solarized":
        # Solarized: Official accent colors
        return ["#268BD2", "#2AA198", "#859900", "#B58900", "#CB4B16", "#DC322F", "#D33682", "#6C71C4"]
    elif theme.id == "dark":
        # Dark: Red spectrum with complementary colors
        return ["#FF4B4B", "#FF6B6B", "#FF8C8C", "#FFA0A0", "#FFB4B4", "#FFC0C0", "#FFD0D0", "#FFE0E0"]
    else:  # light
        # Light: Professional Windows-style palette
        return ["#0078D4", "#106EBE", "#005A9E", "#107C10", "#FFB900", "#D83B01", "#8764B8", "#00B7C3"]


def customize_theme_colors(theme_id: str) -> Dict[str, str]:
    """
    Allow user to customize theme colors.
    
    Returns:
        Dictionary of customized colors
    """
    theme = get_theme(theme_id)
    custom_colors = {}
    
    st.markdown("#### 🎨 Customize Colors")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        custom_colors['primary_color'] = st.color_picker(
            "Primary Color",
            theme.primary_color,
            key=f"custom_primary_{theme_id}"
        )
        custom_colors['background_color'] = st.color_picker(
            "Background",
            theme.background_color,
            key=f"custom_bg_{theme_id}"
        )
    
    with col2:
        custom_colors['text_color'] = st.color_picker(
            "Text Color",
            theme.text_color,
            key=f"custom_text_{theme_id}"
        )
        custom_colors['accent_color'] = st.color_picker(
            "Accent Color",
            theme.accent_color or theme.primary_color,
            key=f"custom_accent_{theme_id}"
        )
    
    with col3:
        custom_colors['border_color'] = st.color_picker(
            "Border Color",
            theme.text_color,
            key=f"custom_border_{theme_id}"
        )
        custom_colors['secondary_background_color'] = st.color_picker(
            "Secondary Background",
            theme.secondary_background_color,
            key=f"custom_sec_bg_{theme_id}"
        )
    
    return custom_colors


def preview_theme(theme_id: str, custom_colors: Optional[Dict[str, str]] = None):
    """Display theme preview with sample elements."""
    theme = get_theme(theme_id)
    
    st.markdown(f"### 🎨 {theme.name} Preview")
    
    col1, col2, col3 = st.columns(3)
    
    display_primary = custom_colors.get('primary_color', theme.primary_color) if custom_colors else theme.primary_color
    display_bg = custom_colors.get('background_color', theme.background_color) if custom_colors else theme.background_color
    display_text = custom_colors.get('text_color', theme.text_color) if custom_colors else theme.text_color
    
    with col1:
        st.metric("Primary Color", display_primary)
        st.color_picker("Primary", display_primary, disabled=True, label_visibility="hidden", key=f"preview_primary_{theme_id}_display")
    
    with col2:
        st.metric("Background", display_bg)
        st.color_picker("Background", display_bg, disabled=True, label_visibility="hidden", key=f"preview_bg_{theme_id}_display")
    
    with col3:
        st.metric("Text Color", display_text)
        st.color_picker("Text", display_text, disabled=True, label_visibility="hidden", key=f"preview_text_{theme_id}_display")
    
    st.markdown("---")
    
    # Sample elements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sample Text**")
        st.write("This is how regular text will look in this theme.")
        st.success("✓ Success message example")
        st.info("ℹ️ Info message example")
    
    with col2:
        st.markdown("**Sample Buttons**")
        st.button("Primary Button", key=f"preview_btn_{theme_id}")
        st.warning("⚠️ Warning message example")
        st.error("❌ Error message example")
    
    # Effects
    if theme.effects:
        st.markdown("**Special Effects:**")
        effects_list = ", ".join([k.title() for k, v in theme.effects.items() if v])
        st.write(f"✨ {effects_list}")
    
    if theme.animation:
        st.write(f"🎬 Animation: {theme.animation.replace('_', ' ').title()}")
