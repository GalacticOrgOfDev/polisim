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
        background_color="#FFFFFF",
        secondary_background_color="#F0F2F6",
        text_color="#262730",
        font_family="'Segoe UI', 'Roboto', sans-serif",
        
        # Buttons - Windows default style
        button=ElementStyle(
            background="#0078D4",
            color="#FFFFFF",
            border="1px solid #0078D4",
            hover_bg="#106EBE",
            hover_border="#106EBE",
        ),
        
        # Radio buttons - Windows style
        radio=ElementStyle(
            background="transparent",
            color="#262730",
            border_color="#8A8A8A",
            hover_bg="rgba(0, 120, 212, 0.1)",
            hover_border="#0078D4",
            active_bg="#FFFFFF",
            active_color="#0078D4",
        ),
        
        # Selectbox/dropdowns
        selectbox=ElementStyle(
            background="#FFFFFF",
            color="#262730",
            border_color="#8A8A8A",
            hover_bg="#F0F2F6",
        ),
        
        # Text inputs
        text_input=ElementStyle(
            background="#FFFFFF",
            color="#262730",
            border_color="#8A8A8A",
        ),
        
        # Tooltips
        tooltip=ElementStyle(
            background="#F9F9F9",
            color="#262730",
            border="1px solid #CCCCCC",
        ),
        
        # Sidebar
        sidebar=ElementStyle(
            background="#F0F2F6",
            color="#262730",
        ),
    ),
    
    "dark": ThemeConfig(
        name="Dark Mode",
        id="dark",
        primary_color="#FF4B4B",
        background_color="#0E1117",
        secondary_background_color="#262730",
        text_color="#FAFAFA",
        accent_color="#FF6B6B",
        font_family="'Segoe UI', 'Roboto', sans-serif",
        needs_transparency=True,
        
        button=ElementStyle(
            background="#FF4B4B",
            color="#FFFFFF",
            hover_bg="#FF6B6B",
        ),
        
        radio=ElementStyle(
            background="transparent",
            color="#FAFAFA",
            border_color="#666666",
            hover_border="#FF4B4B",
            active_color="#FF4B4B",
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
    ),
    
    "matrix": ThemeConfig(
        name="Matrix AI Theme",
        id="matrix",
        primary_color="#00FF41",
        background_color="#000000",
        secondary_background_color="#0A0A0A",
        text_color="#00FF41",
        accent_color="#39FF14",
        font_family="'Courier New', 'Consolas', monospace",
        animation="falling_symbols",
        effects={"glow": True, "scanlines": True, "text_outline": True},
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
            color="#00FF41",
            border_color="#00FF41",
            hover_border="#39FF14",
            active_color="#39FF14",
            text_shadow="0 0 5px #00FF41",
        ),
        
        selectbox=ElementStyle(
            background="rgba(0, 0, 0, 0.8)",
            color="#00FF41",
            border_color="#00FF41",
            text_shadow="0 0 5px #00FF41",
        ),
        
        text_input=ElementStyle(
            background="rgba(0, 0, 0, 0.8)",
            color="#00FF41",
            border_color="#00FF41",
        ),
        
        tooltip=ElementStyle(
            background="rgba(0, 0, 0, 0.95)",
            color="#00FF41",
            border="1px solid #00FF41",
            box_shadow="0 0 10px #00FF41",
        ),
        
        sidebar=ElementStyle(
            background="rgba(10, 10, 10, 0.9)",
            color="#00FF41",
        ),
    ),
    
    "cyberpunk": ThemeConfig(
        name="Cyberpunk 2077",
        id="cyberpunk",
        primary_color="#FFFF00",
        background_color="#0A0E27",
        secondary_background_color="#1A1F3A",
        text_color="#FFFFFF",
        accent_color="#FF00FF",
        font_family="'Orbitron', 'Rajdhani', sans-serif",
        effects={"glow": True, "neon": True},
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
    ),
    
    "nord": ThemeConfig(
        name="Nord Arctic",
        id="nord",
        primary_color="#88C0D0",
        background_color="#2E3440",
        secondary_background_color="#3B4252",
        text_color="#ECEFF4",
        accent_color="#5E81AC",
        font_family="'Inter', 'Roboto', sans-serif",
        
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
    ),
    
    "solarized": ThemeConfig(
        name="Solarized Dark",
        id="solarized",
        primary_color="#268BD2",
        background_color="#002B36",
        secondary_background_color="#073642",
        text_color="#839496",
        accent_color="#2AA198",
        font_family="'Source Code Pro', 'Consolas', monospace",
        
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
    ),
}
        info_color="#268BD2",
    ),
}


def get_theme(theme_id: str) -> ThemeConfig:
    """Get theme configuration by ID."""
    return THEMES.get(theme_id, THEMES["light"])


def get_theme_list() -> list:
    """Get list of available themes."""
    return [{"id": t.id, "name": t.name} for t in THEMES.values()]


def generate_element_css(element: ElementStyle, selectors: List[str]) -> str:
    """Generate CSS for a UI element based on its ElementStyle configuration."""
    if not element:
        return ""
    
    css_parts = []
    
    # Base styles
    if element.background or element.color or element.border or element.border_color:
        styles = []
        if element.background:
            styles.append(f"background-color: {element.background} !important;")
        if element.color:
            styles.append(f"color: {element.color} !important;")
        if element.border:
            styles.append(f"border: {element.border} !important;")
        elif element.border_color:
            styles.append(f"border-color: {element.border_color} !important;")
        if element.text_shadow:
            styles.append(f"text-shadow: {element.text_shadow} !important;")
        if element.box_shadow:
            styles.append(f"box-shadow: {element.box_shadow} !important;")
        
        if styles:
            for selector in selectors:
                css_parts.append(f"{selector} {{ {' '.join(styles)} }}")
    
    # Hover styles
    if element.hover_bg or element.hover_color or element.hover_border:
        styles = []
        if element.hover_bg:
            styles.append(f"background-color: {element.hover_bg} !important;")
        if element.hover_color:
            styles.append(f"color: {element.hover_color} !important;")
        if element.hover_border:
            styles.append(f"border-color: {element.hover_border} !important;")
        
        if styles:
            for selector in selectors:
                css_parts.append(f"{selector}:hover {{ {' '.join(styles)} }}")
    
    # Active/checked styles
    if element.active_bg or element.active_color:
        styles = []
        if element.active_bg:
            styles.append(f"background-color: {element.active_bg} !important;")
        if element.active_color:
            styles.append(f"color: {element.active_color} !important;")
        
        if styles:
            # For radio buttons (checked state)
            css_parts.append(f".stRadio input:checked ~ div {{ {' '.join(styles)} }}")
    
    # Additional CSS
    if element.additional_css:
        css_parts.append(element.additional_css)
    
    return "\n".join(css_parts)


def apply_theme(theme_id: str):
    """Apply custom CSS for selected theme using element-based styling."""
    theme = get_theme(theme_id)
    
    # Get transparency settings from session state for animated themes
    bg_opacity = st.session_state.get('settings', {}).get('bg_opacity', 0.6)
    content_opacity = st.session_state.get('settings', {}).get('content_opacity', 0.8)
    sidebar_opacity = st.session_state.get('settings', {}).get('sidebar_opacity', 0.9)
    
    # Start building CSS
    css_parts = ["""<style>
    /* Reset previous theme styling */
    * { text-shadow: none !important; box-shadow: none !important; }
    .stApp::before { content: none !important; display: none !important; }
    """]
    
    # Core theme colors
    css_parts.append(f"""
    /* Core theme: {theme.name} */
    .stApp {{
        background-color: {theme.background_color} !important;
        color: {theme.text_color} !important;
        font-family: {theme.font_family};
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: {theme.background_color} !important;
    }}
    
    [data-testid="stHeader"] {{
        background-color: rgba(255, 255, 255, 0.05) !important;
    }}
    
    h1, h2, h3, h4, h5, h6, p, span, div, label {{
        color: {theme.text_color} !important;
    }}
    """)
        css = """
    <style>
    /* Reset any previous theme styling */
    * {
        text-shadow: none !important;
        box-shadow: none !important;
    }
    
    .stApp::before {
        content: none !important;
        display: none !important;
    }
    
    /* Light mode - clean Streamlit defaults */
    .stApp {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
    }
    
    section[data-testid="stSidebar"] {
        background-color: #F0F2F6 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(255, 255, 255, 0.8) !important;
    }
    
    /* Ensure all text is readable */
    h1, h2, h3, h4, h5, h6, p, span, div, label {
        color: #262730 !important;
        text-shadow: none !important;
        box-shadow: none !important;
    }
    
    /* Reset buttons to default Streamlit red */
    .stButton > button {
        background-color: #FF4B4B !important;
        color: #FFFFFF !important;
        border: 1px solid #FF4B4B !important;
        text-shadow: none !important;
        box-shadow: none !important;
    }
    
    .stButton > button:hover {
        background-color: #FF6B6B !important;
        border-color: #FF6B6B !important;
    }
    
    /* Fix selectbox/dropdown styling */
    .stSelectbox > div > div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    .stSelectbox [data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border-color: #CCCCCC !important;
    }
    
    /* Fix dropdown menu */
    [data-baseweb="popover"] {
        background-color: #FFFFFF !important;
    }
    
    [role="listbox"] {
        background-color: #FFFFFF !important;
    }
    
    [role="option"] {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    [role="option"]:hover {
        background-color: #F0F2F6 !important;
    }
    
    /* Fix radio buttons - Windows default style */
    .stRadio > label {
        color: #262730 !important;
    }
    
    .stRadio [role="radiogroup"] label {
        color: #262730 !important;
        background-color: transparent !important;
    }
    
    .stRadio [role="radiogroup"] label:hover {
        background-color: rgba(0, 120, 212, 0.1) !important;
    }
    
    .stRadio [data-baseweb="radio"] {
        background-color: transparent !important;
    }
    
    .stRadio [data-baseweb="radio"] > div {
        border-color: #8A8A8A !important;
        background-color: #FFFFFF !important;
    }
    
    .stRadio [data-baseweb="radio"] > div:hover {
        border-color: #0078D4 !important;
    }
    
    /* Selected radio button - Windows blue */
    .stRadio input:checked ~ div {
        background-color: #FFFFFF !important;
        border-color: #0078D4 !important;
    }
    
    .stRadio input:checked ~ div::after {
        background-color: #0078D4 !important;
    }
    
    /* Tooltip icon - should be dark in light mode */
    button[kind="icon"] {
        color: #262730 !important;
    }
    
    button[aria-label*="help"] {
        color: #262730 !important;
    }
    
    /* Tooltip popup */
    [data-baseweb="tooltip"] {
        background-color: #F9F9F9 !important;
        color: #262730 !important;
        border: 1px solid #CCCCCC !important;
    }
    
    .stTooltipIcon {
        color: #262730 !important;
    }
    
    /* Fix text inputs */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #FFFFFF !important;
        color: #262730 !important;
        border-color: #CCCCCC !important;
    }
    
    /* Fix sliders */
    .stSlider [data-baseweb="slider"] {
        background-color: transparent !important;
    }
    
    /* Fix checkboxes */
    .stCheckbox label {
        color: #262730 !important;
    }
    
    /* Fix expanders */
    .streamlit-expanderHeader {
        background-color: #F0F2F6 !important;
        color: #262730 !important;
    }
    </style>
    """
        st.markdown(css, unsafe_allow_html=True)
        return  # Exit early for light mode
    
    # For all other themes, apply full custom styling
    # Calculate background colors
    if needs_transparency:
        # Parse theme background color to RGB
        bg_color = theme.background_color.lstrip('#')
        r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
        main_bg = f"rgba({r}, {g}, {b}, {bg_opacity})"
        content_bg = f"rgba({r+10}, {g+10}, {b+10}, {content_opacity})"
        sidebar_bg = f"rgba({r+10}, {g+10}, {b+10}, {sidebar_opacity})"
    else:
        # Solid backgrounds for non-animated themes
        main_bg = theme.background_color
        content_bg = theme.secondary_background_color
        sidebar_bg = theme.secondary_background_color
    
    # Base CSS for all themes
    css = f"""
    <style>
    /* Theme Reset - Override any previous theme styles to prevent bleed-over */
    * {{
        text-shadow: none !important;
        box-shadow: none !important;
    }}
    
    /* Remove any previous glow or neon effects */
    .stButton > button,
    h1, h2, h3, h4, h5, h6 {{
        text-shadow: none !important;
        box-shadow: none !important;
    }}
    
    /* Remove scanlines from previous themes */
    .stApp::before {{
        content: none !important;
        display: none !important;
    }}
    
    /* Global theme variables */
    :root {{
        --primary-color: {theme.primary_color};
        --background-color: {theme.background_color};
        --secondary-background-color: {theme.secondary_background_color};
        --text-color: {theme.text_color};
        --accent-color: {theme.accent_color or theme.primary_color};
        --border-color: {theme.border_color or theme.text_color};
        --font-family: {theme.font_family};
    }}
    
    /* Main app background */
    .stApp {{
        background-color: {main_bg} !important;
        color: {theme.text_color} !important;
        font-family: {theme.font_family};
    }}
    
    /* Content containers */
    [data-testid="stAppViewContainer"] {{
        background-color: {main_bg} !important;
    }}
    
    /* Streamlit header/toolbar - make transparent for animated themes */
    header[data-testid="stHeader"] {{
        background-color: {'rgba(0, 0, 0, 0.3)' if needs_transparency else 'transparent'} !important;
        backdrop-filter: blur(10px);
    }}
    
    .main .block-container {{
        background-color: {content_bg} !important;
        border-radius: 10px;
        padding: 2rem;
    }}
    
    /* Make sure all text is visible */
    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: {theme.text_color} !important;
    }}
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {sidebar_bg} !important;
        z-index: 2;
        color: {theme.text_color} !important;
    }}
    
    section[data-testid="stSidebar"] * {{
        color: {theme.text_color} !important;
    }}
    
    section[data-testid="stSidebar"] .stRadio > label {{
        color: {theme.text_color} !important;
    }}
    
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label {{
        color: {theme.text_color} !important;
    }}
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {theme.text_color} !important;
        font-family: {theme.font_family};
    }}
    
    h1 {{
        color: {theme.primary_color} !important;
    }}
    
    /* Text outline for Matrix theme */
    {"" if not theme.effects or not theme.effects.get('text_outline') else f'''
    h1, h2, h3, h4, h5, h6, p, span, div, label {{
        text-shadow: 
            -1px -1px 0 #000,
            1px -1px 0 #000,
            -1px 1px 0 #000,
            1px 1px 0 #000;
    }}
    
    h1, h2 {{
        text-shadow: 
            -1px -1px 0 #000,
            1px -1px 0 #000,
            -1px 1px 0 #000,
            1px 1px 0 #000,
            0 0 10px {theme.primary_color},
            0 0 20px {theme.primary_color};
    }}
    '''}
    
    /* Text and paragraphs */
    p, span, div {{
        color: {theme.text_color};
    }}
    
    /* Buttons */
    .stButton > button {{
        background-color: {theme.primary_color};
        color: {theme.background_color};
        border: 1px solid {theme.primary_color};
        font-weight: 600;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {theme.accent_color or theme.primary_color};
        border-color: {theme.accent_color or theme.primary_color};
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }}
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stMultiSelect > div > div > div {{
        background-color: {theme.secondary_background_color};
        color: {theme.text_color};
        border: 1px solid {theme.border_color or theme.text_color};
    }}
    
    /* Metrics */
    [data-testid="stMetricValue"] {{
        color: {theme.primary_color} !important;
        font-weight: bold;
    }}
    
    [data-testid="stMetricLabel"] {{
        color: {theme.text_color} !important;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {theme.secondary_background_color};
    }}
    
    .stTabs [data-baseweb="tab"] {{
        color: {theme.text_color};
        border-color: {theme.border_color or theme.text_color};
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {theme.primary_color} !important;
        color: {theme.background_color} !important;
    }}
    
    /* Expanders */
    .streamlit-expanderHeader {{
        background-color: {theme.secondary_background_color};
        color: {theme.text_color};
        border: 1px solid {theme.border_color or theme.text_color};
    }}
    
    /* Dataframes */
    .dataframe {{
        background-color: {theme.secondary_background_color} !important;
        color: {theme.text_color} !important;
    }}
    
    .dataframe th {{
        background-color: {theme.primary_color} !important;
        color: {theme.background_color} !important;
    }}
    
    .dataframe td {{
        background-color: {theme.secondary_background_color} !important;
        color: {theme.text_color} !important;
        border-color: {theme.border_color or theme.text_color} !important;
    }}
    
    /* Charts */
    .js-plotly-plot .plotly .modebar {{
        background-color: {theme.secondary_background_color} !important;
    }}
    
    /* Alerts */
    .stAlert {{
        background-color: {theme.secondary_background_color};
        color: {theme.text_color};
        border-left: 4px solid {theme.primary_color};
    }}
    
    /* Success messages */
    .stSuccess {{
        background-color: rgba(0, 255, 0, 0.1);
        color: {theme.success_color};
        border-left-color: {theme.success_color} !important;
    }}
    
    /* Warning messages */
    .stWarning {{
        background-color: rgba(255, 255, 0, 0.1);
        color: {theme.warning_color};
        border-left-color: {theme.warning_color} !important;
    }}
    
    /* Error messages */
    .stError {{
        background-color: rgba(255, 0, 0, 0.1);
        color: {theme.error_color};
        border-left-color: {theme.error_color} !important;
    }}
    
    /* Info messages */
    .stInfo {{
        background-color: rgba(0, 191, 255, 0.1);
        color: {theme.info_color};
        border-left-color: {theme.info_color} !important;
    }}
    
    /* Code blocks */
    .stCodeBlock {{
        background-color: {theme.secondary_background_color} !important;
        border: 1px solid {theme.border_color or theme.text_color};
    }}
    
    code {{
        color: {theme.accent_color or theme.primary_color} !important;
        background-color: {theme.secondary_background_color} !important;
    }}
    
    /* Links */
    a {{
        color: {theme.primary_color} !important;
    }}
    
    a:hover {{
        color: {theme.accent_color or theme.primary_color} !important;
        text-decoration: underline;
    }}
    
    /* Tooltips - ensure visibility */
    .stTooltipIcon {{
        color: {theme.primary_color} !important;
        fill: {theme.primary_color} !important;
    }}
    
    .stTooltipIcon svg {{
        fill: {theme.primary_color} !important;
    }}
    
    [data-baseweb="tooltip"] {{
        background-color: {theme.background_color} !important;
        color: {theme.text_color} !important;
        border: 1px solid {theme.primary_color} !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }}
    
    /* Help text */
    .stTextInput > label > div[data-testid="stMarkdownContainer"] > p,
    .stSelectbox > label > div[data-testid="stMarkdownContainer"] > p,
    .stSlider > label > div[data-testid="stMarkdownContainer"] > p,
    .stCheckbox > label > div[data-testid="stMarkdownContainer"] > p {{
        color: {theme.text_color} !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {theme.secondary_background_color};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {theme.primary_color};
        border-radius: 5px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {theme.accent_color or theme.primary_color};
    }}
    """
    
    # Theme-specific effects
    if theme.effects:
        if theme.effects.get("glow"):
            css += f"""
    /* Glow effect */
    h1, h2 {{
        text-shadow: 0 0 10px {theme.primary_color},
                     0 0 20px {theme.primary_color},
                     0 0 30px {theme.primary_color};
    }}
    
    .stButton > button {{
        box-shadow: 0 0 10px {theme.primary_color};
    }}
    
    .stButton > button:hover {{
        box-shadow: 0 0 20px {theme.primary_color},
                    0 0 30px {theme.primary_color};
    }}
    """
        
        if theme.effects.get("scanlines"):
            css += """
    /* Scanline effect */
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: repeating-linear-gradient(
            0deg,
            rgba(0, 0, 0, 0.15),
            rgba(0, 0, 0, 0.15) 1px,
            transparent 1px,
            transparent 2px
        );
        pointer-events: none;
        z-index: 0;
    }
    """
        
        if theme.effects.get("neon"):
            css += f"""
    /* Neon border effect */
    .stButton > button,
    .stTextInput > div > div > input,
    .streamlit-expanderHeader {{
        border: 2px solid {theme.primary_color};
        box-shadow: 0 0 5px {theme.primary_color},
                    inset 0 0 5px {theme.primary_color};
    }}
    """
    
    # Close the style tag with theme identifier comment for debugging
    css += f"""
    <!-- Theme: {theme_id} -->
    </style>
    """
    
    st.markdown(css, unsafe_allow_html=True)


def get_plotly_template(theme_id: str) -> str:
    """
    Get appropriate Plotly template for theme.
    
    Returns:
        Plotly template name (plotly, plotly_white, plotly_dark, etc.)
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


def apply_plotly_theme(fig, theme_id: str):
    """
    Apply theme colors to Plotly figure.
    
    Args:
        fig: Plotly figure object
        theme_id: Theme identifier
    
    Returns:
        Modified figure with theme applied
    """
    theme = get_theme(theme_id)
    template = get_plotly_template(theme_id)
    
    # Apply template
    fig.update_layout(template=template)
    
    # Apply custom colors
    fig.update_layout(
        paper_bgcolor=theme.background_color,
        plot_bgcolor=theme.secondary_background_color,
        font=dict(
            color=theme.text_color,
            family=theme.font_family,
        ),
        title_font=dict(
            color=theme.primary_color,
        ),
        xaxis=dict(
            gridcolor=theme.border_color or theme.text_color,
            linecolor=theme.border_color or theme.text_color,
            zerolinecolor=theme.border_color or theme.text_color,
        ),
        yaxis=dict(
            gridcolor=theme.border_color or theme.text_color,
            linecolor=theme.border_color or theme.text_color,
            zerolinecolor=theme.border_color or theme.text_color,
        ),
    )
    
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
    
    # Theme-specific color palettes
    if theme.id == "matrix":
        return ["#00FF41", "#39FF14", "#00CC33", "#00FF00", "#00FFFF", "#7FFF00"]
    elif theme.id == "cyberpunk":
        return ["#FFFF00", "#FF00FF", "#00FFFF", "#FF6600", "#00FF00", "#FF0066"]
    elif theme.id == "nord":
        return ["#88C0D0", "#81A1C1", "#5E81AC", "#BF616A", "#A3BE8C", "#EBCB8B"]
    elif theme.id == "solarized":
        return ["#268BD2", "#2AA198", "#859900", "#B58900", "#CB4B16", "#DC322F"]
    elif theme.id == "dark":
        return ["#FF4B4B", "#FF6B6B", "#FFB4B4", "#FF8C8C", "#FFA0A0", "#FFC0C0"]
    else:  # light
        return ["#FF4B4B", "#FF6B6B", "#1F77B4", "#FF7F0E", "#2CA02C", "#D62728"]


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
            theme.border_color or theme.text_color,
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
