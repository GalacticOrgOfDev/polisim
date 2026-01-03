"""
PoliSim Chat Panel - Simplified Chat Interface (Phase 7.3.3 Refactored).

A clean, static chat panel with:
- Tabbed message windows (Global, Regional, Private, Agent Swarm)
- Session management for Private and Agent Swarm chats
- Message input with file attachment support
- Quick action toolbar

Example:
    from ui.chat_sidebar import render_chat_panel
    
    # In Streamlit app
    render_chat_panel(user_id="user_123", user_name="John")
"""

import json
import logging
import io
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from pathlib import Path

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

AGENT_COLORS = {
    "fiscal": "#4CAF50",
    "economic": "#2196F3",
    "healthcare": "#9C27B0",
    "social_security": "#FF9800",
    "equity": "#E91E63",
    "implementation": "#00BCD4",
    "behavioral": "#795548",
    "legal": "#607D8B",
    "judge": "#F44336",
    "system": "#9E9E9E",
}

AGENT_ICONS = {
    "fiscal": "💰",
    "economic": "📈",
    "healthcare": "🏥",
    "social_security": "👴",
    "equity": "⚖️",
    "implementation": "🔧",
    "behavioral": "🧠",
    "legal": "📜",
    "judge": "👨‍⚖️",
    "system": "🤖",
}

MESSAGE_TYPE_ICONS = {
    "text": "💬",
    "analysis_request": "🔍",
    "analysis_result": "📊",
    "scenario_request": "🎯",
    "scenario_result": "📈",
    "action": "⚡",
    "system_event": "ℹ️",
    "thinking": "💭",
    "error": "❌",
}

SYSTEM_EVENT_ICONS = {
    "analysis_started": "🚀",
    "analysis_completed": "✅",
    "user_joined": "👋",
    "user_left": "👤",
    "action_triggered": "⚡",
    "error": "❌",
    "warning": "⚠️",
}

CHAT_TABS = ["🌐 Global", "🗺️ Regional", "🔒 Private", "🤖 Agents"]

# US Regions for regional chat
US_REGIONS = [
    "Northeast", "Southeast", "Midwest", "Southwest", "West Coast", "Pacific"
]


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ChatMessage:
    """A chat message."""
    message_id: str
    sender_id: str
    sender_name: str
    sender_type: str  # user, agent, system
    content: str
    timestamp: datetime
    chat_type: str  # global, regional, private, agent_swarm
    session_id: Optional[str] = None
    region: Optional[str] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ChatSession:
    """A private or agent swarm chat session."""
    session_id: str
    name: str
    chat_type: str  # private, agent_swarm
    created_at: datetime
    participants: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)


# Backward compatible aliases
@dataclass
class ChannelInfo:
    """Channel info (backward compatible)."""
    channel_id: str
    name: str
    channel_type: str = "public"
    description: str = ""
    icon: str = "💬"
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    last_message_preview: str = ""
    is_active: bool = True
    participants: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    bill_id: Optional[str] = None


@dataclass
class MessageDisplay:
    """Message display (backward compatible)."""
    message_id: str
    sender_id: str
    sender_type: str
    sender_name: str
    sender_icon: str
    sender_color: str
    content: str
    message_type: str
    timestamp: datetime
    is_own_message: bool = False
    thread_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    reply_preview: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reactions: Dict[str, int] = field(default_factory=dict)
    is_edited: bool = False
    is_pinned: bool = False


@dataclass
class AgentPresence:
    """Agent presence (backward compatible)."""
    agent_id: str
    agent_type: str
    agent_name: str
    icon: str
    color: str
    status: str = "idle"
    status_detail: Optional[str] = None
    last_active: Optional[datetime] = None


@dataclass
class ChatExportOptions:
    """Export options (backward compatible)."""
    format: str = "json"
    include_metadata: bool = True
    include_reactions: bool = True
    include_analysis_results: bool = True
    include_charts: bool = True
    date_range_start: Optional[datetime] = None
    date_range_end: Optional[datetime] = None
    filter_types: Optional[List[str]] = None


# =============================================================================
# Session State Management
# =============================================================================

def init_chat_state():
    """Initialize chat state."""
    if "polisim_chat" not in st.session_state:
        st.session_state.polisim_chat = {
            # Current view
            "active_tab": 0,  # Index into CHAT_TABS
            "show_history": False,
            
            # Regional chat
            "selected_region": "Northeast",
            
            # Private sessions
            "private_sessions": [],
            "active_private_session": None,
            
            # Agent swarm sessions
            "agent_sessions": [],
            "active_agent_session": None,
            "selected_agents": ["fiscal", "economic", "healthcare"],
            
            # Messages by type
            "global_messages": [],
            "regional_messages": {},  # region -> messages
            "private_messages": {},   # session_id -> messages
            "agent_messages": {},     # session_id -> messages
            
            # History
            "all_history": [],
            
            # Input state
            "pending_attachment": None,
        }
        
        # Initialize with demo data
        _init_demo_data()


def get_chat_state() -> Dict[str, Any]:
    """Get chat state."""
    init_chat_state()
    return st.session_state.polisim_chat


def update_chat_state(**kwargs):
    """Update chat state."""
    init_chat_state()
    for key, value in kwargs.items():
        st.session_state.polisim_chat[key] = value


def _init_demo_data():
    """Initialize demo messages and sessions."""
    state = st.session_state.polisim_chat
    now = datetime.now(timezone.utc)
    
    # Demo global messages
    state["global_messages"] = [
        ChatMessage(
            message_id="g1",
            sender_id="system",
            sender_name="System",
            sender_type="system",
            content="Welcome to PoliSim Global Chat! Discuss policy analysis with users worldwide.",
            timestamp=now - timedelta(hours=2),
            chat_type="global",
        ),
        ChatMessage(
            message_id="g2",
            sender_id="user_alice",
            sender_name="Alice",
            sender_type="user",
            content="Has anyone analyzed the new healthcare bill? Looking for fiscal impact projections.",
            timestamp=now - timedelta(hours=1),
            chat_type="global",
        ),
        ChatMessage(
            message_id="g3",
            sender_id="fiscal",
            sender_name="Fiscal Agent",
            sender_type="agent",
            content="I can help analyze healthcare legislation. The USGHA bill shows a 10-year cost of approximately $32T with projected savings of $7T from administrative efficiency.",
            timestamp=now - timedelta(minutes=45),
            chat_type="global",
            metadata={"agent_type": "fiscal"},
        ),
    ]
    
    # Demo regional messages
    state["regional_messages"]["Northeast"] = [
        ChatMessage(
            message_id="r1",
            sender_id="system",
            sender_name="System",
            sender_type="system",
            content="Northeast Regional Chat - Discuss regional policy impacts.",
            timestamp=now - timedelta(hours=1),
            chat_type="regional",
            region="Northeast",
        ),
    ]
    
    # Demo private session
    demo_session = ChatSession(
        session_id="ps1",
        name="Budget Planning Discussion",
        chat_type="private",
        created_at=now - timedelta(days=1),
        participants=["user_self", "user_bob"],
    )
    state["private_sessions"] = [demo_session]
    state["private_messages"]["ps1"] = [
        ChatMessage(
            message_id="p1",
            sender_id="user_bob",
            sender_name="Bob",
            sender_type="user",
            content="Let's discuss the 2026 budget implications privately.",
            timestamp=now - timedelta(hours=3),
            chat_type="private",
            session_id="ps1",
        ),
    ]
    
    # Demo agent swarm session
    agent_session = ChatSession(
        session_id="as1",
        name="Healthcare Reform Analysis",
        chat_type="agent_swarm",
        created_at=now - timedelta(hours=6),
        agents=["fiscal", "healthcare", "economic"],
    )
    state["agent_sessions"] = [agent_session]
    state["agent_messages"]["as1"] = [
        ChatMessage(
            message_id="a1",
            sender_id="system",
            sender_name="System",
            sender_type="system",
            content="Agent swarm session started with: Fiscal, Healthcare, Economic agents.",
            timestamp=now - timedelta(hours=6),
            chat_type="agent_swarm",
            session_id="as1",
        ),
        ChatMessage(
            message_id="a2",
            sender_id="healthcare",
            sender_name="Healthcare Agent",
            sender_type="agent",
            content="Analyzing healthcare reform impact on coverage rates and costs...",
            timestamp=now - timedelta(hours=5, minutes=55),
            chat_type="agent_swarm",
            session_id="as1",
            metadata={"agent_type": "healthcare"},
        ),
    ]


# =============================================================================
# CSS Styles - Theme-Aware
# =============================================================================

def get_chat_css(theme_id: str = "matrix") -> str:
    """Generate theme-aware CSS for the chat panel.
    
    Uses CSS variables from the theme system and adapts colors based on theme.
    """
    # Theme-specific color configurations
    theme_colors = {
        "light": {
            "panel_bg": "rgba(240, 242, 246, 0.98)",
            "panel_border": "rgba(0, 120, 212, 0.3)",
            "text_color": "#000000",
            "text_muted": "#666666",
            "header_bg": "rgba(240, 242, 246, 0.95)",
            "msg_user_bg": "rgba(0, 120, 212, 0.15)",
            "msg_user_border": "rgba(0, 120, 212, 0.4)",
            "msg_agent_bg": "rgba(76, 175, 80, 0.12)",
            "msg_agent_border": "rgba(76, 175, 80, 0.3)",
            "msg_system_bg": "rgba(128, 128, 128, 0.1)",
            "msg_system_border": "rgba(128, 128, 128, 0.2)",
            "session_bg": "rgba(220, 220, 230, 0.6)",
            "session_hover": "rgba(200, 200, 220, 0.8)",
            "session_active": "rgba(0, 120, 212, 0.2)",
            "input_bg": "rgba(255, 255, 255, 0.95)",
            "input_border": "rgba(128, 128, 128, 0.4)",
            "accent": "#0078D4",
        },
        "dark": {
            "panel_bg": "rgba(38, 39, 48, 0.98)",
            "panel_border": "rgba(90, 90, 90, 0.4)",
            "text_color": "#FAFAFA",
            "text_muted": "#AAAAAA",
            "header_bg": "rgba(38, 39, 48, 0.95)",
            "msg_user_bg": "rgba(90, 90, 90, 0.25)",
            "msg_user_border": "rgba(90, 90, 90, 0.5)",
            "msg_agent_bg": "rgba(76, 175, 80, 0.15)",
            "msg_agent_border": "rgba(76, 175, 80, 0.35)",
            "msg_system_bg": "rgba(100, 100, 100, 0.15)",
            "msg_system_border": "rgba(100, 100, 100, 0.25)",
            "session_bg": "rgba(50, 50, 60, 0.6)",
            "session_hover": "rgba(60, 60, 75, 0.8)",
            "session_active": "rgba(90, 90, 90, 0.3)",
            "input_bg": "rgba(38, 39, 48, 0.95)",
            "input_border": "rgba(64, 64, 64, 0.6)",
            "accent": "#5A5A5A",
        },
        "matrix": {
            "panel_bg": "rgba(5, 10, 5, 0.96)",
            "panel_border": "rgba(0, 255, 65, 0.35)",
            "text_color": "#FFFFFF",
            "text_muted": "rgba(0, 255, 65, 0.7)",
            "header_bg": "rgba(5, 15, 5, 0.95)",
            "msg_user_bg": "rgba(0, 255, 65, 0.12)",
            "msg_user_border": "rgba(0, 255, 65, 0.4)",
            "msg_agent_bg": "rgba(0, 200, 50, 0.1)",
            "msg_agent_border": "rgba(0, 200, 50, 0.35)",
            "msg_system_bg": "rgba(0, 255, 65, 0.08)",
            "msg_system_border": "rgba(0, 255, 65, 0.2)",
            "session_bg": "rgba(0, 50, 20, 0.5)",
            "session_hover": "rgba(0, 80, 30, 0.7)",
            "session_active": "rgba(0, 255, 65, 0.2)",
            "input_bg": "rgba(0, 20, 5, 0.9)",
            "input_border": "rgba(0, 255, 65, 0.4)",
            "accent": "#00FF41",
        },
        "cyberpunk": {
            "panel_bg": "rgba(15, 5, 25, 0.96)",
            "panel_border": "rgba(255, 0, 255, 0.35)",
            "text_color": "#FFFFFF",
            "text_muted": "rgba(0, 255, 255, 0.7)",
            "header_bg": "rgba(20, 5, 30, 0.95)",
            "msg_user_bg": "rgba(255, 0, 255, 0.12)",
            "msg_user_border": "rgba(255, 0, 255, 0.4)",
            "msg_agent_bg": "rgba(0, 255, 255, 0.1)",
            "msg_agent_border": "rgba(0, 255, 255, 0.35)",
            "msg_system_bg": "rgba(255, 255, 0, 0.08)",
            "msg_system_border": "rgba(255, 255, 0, 0.2)",
            "session_bg": "rgba(50, 20, 60, 0.5)",
            "session_hover": "rgba(80, 30, 90, 0.7)",
            "session_active": "rgba(255, 0, 255, 0.2)",
            "input_bg": "rgba(20, 5, 30, 0.9)",
            "input_border": "rgba(255, 0, 255, 0.4)",
            "accent": "#FF00FF",
        },
        "nord": {
            "panel_bg": "rgba(46, 52, 64, 0.98)",
            "panel_border": "rgba(136, 192, 208, 0.35)",
            "text_color": "#ECEFF4",
            "text_muted": "#88C0D0",
            "header_bg": "rgba(46, 52, 64, 0.95)",
            "msg_user_bg": "rgba(136, 192, 208, 0.15)",
            "msg_user_border": "rgba(136, 192, 208, 0.4)",
            "msg_agent_bg": "rgba(163, 190, 140, 0.12)",
            "msg_agent_border": "rgba(163, 190, 140, 0.35)",
            "msg_system_bg": "rgba(76, 86, 106, 0.2)",
            "msg_system_border": "rgba(76, 86, 106, 0.35)",
            "session_bg": "rgba(59, 66, 82, 0.6)",
            "session_hover": "rgba(67, 76, 94, 0.8)",
            "session_active": "rgba(136, 192, 208, 0.25)",
            "input_bg": "rgba(46, 52, 64, 0.95)",
            "input_border": "rgba(136, 192, 208, 0.4)",
            "accent": "#88C0D0",
        },
        "solarized": {
            "panel_bg": "rgba(0, 43, 54, 0.98)",
            "panel_border": "rgba(38, 139, 210, 0.35)",
            "text_color": "#93A1A1",
            "text_muted": "#657B83",
            "header_bg": "rgba(0, 43, 54, 0.95)",
            "msg_user_bg": "rgba(38, 139, 210, 0.15)",
            "msg_user_border": "rgba(38, 139, 210, 0.4)",
            "msg_agent_bg": "rgba(133, 153, 0, 0.12)",
            "msg_agent_border": "rgba(133, 153, 0, 0.35)",
            "msg_system_bg": "rgba(88, 110, 117, 0.15)",
            "msg_system_border": "rgba(88, 110, 117, 0.3)",
            "session_bg": "rgba(7, 54, 66, 0.6)",
            "session_hover": "rgba(7, 54, 66, 0.85)",
            "session_active": "rgba(38, 139, 210, 0.25)",
            "input_bg": "rgba(0, 43, 54, 0.95)",
            "input_border": "rgba(38, 139, 210, 0.4)",
            "accent": "#268BD2",
        },
    }
    
    # Default to matrix if theme not found
    colors = theme_colors.get(theme_id, theme_colors["matrix"])
    
    return f"""
<style>
/* ============================================
   POLISIM CHAT PANEL (FIXED OVERLAY MODE) - THEME: {theme_id.upper()}
   NOTE: This is the legacy fixed overlay mode. Column mode is now preferred.
   ============================================ */

/* Fixed chat panel on the right side - does NOT scroll with page */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) {{
    position: fixed !important;
    top: 70px !important;
    right: 15px !important;
    width: 320px !important;
    height: calc(100vh - 90px) !important;
    z-index: 9999 !important;
    background: {colors['panel_bg']} !important;
    border-radius: 12px !important;
    border: 1px solid {colors['panel_border']} !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding: 12px !important;
}}

/* Prevent any parent containers from affecting position */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]),
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) > * {{
    transform: none !important;
}}

/* Style all elements inside the chat panel */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) * {{
    color: {colors['text_color']} !important;
}}

/* Chat header */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) h4 {{
    color: {colors['text_color']} !important;
    margin: 0 0 8px 0 !important;
    font-size: 1.1rem !important;
    text-shadow: 0 0 8px {colors['accent']}40;
}}

/* Tab buttons */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stButton"] button {{
    background: transparent !important;
    border: 1px solid {colors['panel_border']} !important;
    color: {colors['text_color']} !important;
    border-radius: 8px !important;
    padding: 6px 10px !important;
    font-size: 1.1rem !important;
    transition: all 0.2s ease !important;
    min-height: 36px !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stButton"] button:hover {{
    background: {colors['session_hover']} !important;
    border-color: {colors['accent']} !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stButton"] button[kind="primary"] {{
    background: {colors['session_active']} !important;
    border-color: {colors['accent']} !important;
    box-shadow: 0 0 8px {colors['accent']}50 !important;
}}

/* Message container with scrollable area */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stVerticalBlockBorderWrapper"] {{
    background: {colors['header_bg']} !important;
    border-radius: 8px !important;
    border: 1px solid {colors['panel_border']}60 !important;
}}

/* Message bubbles */
.message {{
    padding: 10px 14px !important;
    border-radius: 12px !important;
    max-width: 90% !important;
    word-wrap: break-word !important;
    margin-bottom: 8px !important;
    color: {colors['text_color']} !important;
}}

.message-user {{
    background: {colors['msg_user_bg']} !important;
    border: 1px solid {colors['msg_user_border']} !important;
    margin-left: auto !important;
}}

.message-agent {{
    background: {colors['msg_agent_bg']} !important;
    border: 1px solid {colors['msg_agent_border']} !important;
}}

.message-system {{
    background: {colors['msg_system_bg']} !important;
    border: 1px solid {colors['msg_system_border']} !important;
    text-align: center !important;
    font-size: 0.85em !important;
    color: {colors['text_muted']} !important;
    margin: 0 auto !important;
}}

.message-sender {{
    font-weight: 600 !important;
    font-size: 0.85em !important;
    margin-bottom: 4px !important;
}}

.message-content {{
    font-size: 0.95em !important;
    line-height: 1.4 !important;
}}

.message-time {{
    font-size: 0.75em !important;
    color: {colors['text_muted']} !important;
    margin-top: 4px !important;
}}

/* Input styling */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stTextInput"] input {{
    background: {colors['input_bg']} !important;
    border: 1px solid {colors['input_border']} !important;
    color: {colors['text_color']} !important;
    border-radius: 8px !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stTextInput"] input::placeholder {{
    color: {colors['text_muted']} !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stTextInput"] input:focus {{
    border-color: {colors['accent']} !important;
    box-shadow: 0 0 6px {colors['accent']}40 !important;
}}

/* Selectbox styling */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stSelectbox"] > div > div {{
    background: {colors['input_bg']} !important;
    border: 1px solid {colors['input_border']} !important;
    color: {colors['text_color']} !important;
    border-radius: 8px !important;
}}

/* Session items */
.session-item {{
    padding: 10px 12px !important;
    margin: 4px 0 !important;
    background: {colors['session_bg']} !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}}

.session-item:hover {{
    background: {colors['session_hover']} !important;
}}

.session-item.active {{
    background: {colors['session_active']} !important;
    border-left: 3px solid {colors['accent']} !important;
}}

/* Popover for file attachments */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stPopover"] > div {{
    background: {colors['panel_bg']} !important;
    border: 1px solid {colors['panel_border']} !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stFileUploaderDropzone"] {{
    background: {colors['input_bg']} !important;
    border: 1px dashed {colors['input_border']} !important;
    padding: 10px !important;
    min-height: auto !important;
}}

/* Multiselect for agents */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stMultiSelect"] > div {{
    background: {colors['input_bg']} !important;
    border: 1px solid {colors['input_border']} !important;
}}

/* Captions */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"]) [data-testid="stCaptionContainer"] {{
    color: {colors['text_muted']} !important;
}}

/* Scrollbar */
[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"])::-webkit-scrollbar {{
    width: 6px !important;
}}

[data-testid="stVerticalBlock"]:has([data-polisim-chat="true"])::-webkit-scrollbar-thumb {{
    background: {colors['accent']}50 !important;
    border-radius: 3px !important;
}}
</style>
"""


def get_column_chat_css(theme_id: str = "matrix") -> str:
    """Generate CSS for column-mode chat panel (not fixed overlay).

    This styling is used when chat is rendered inside a Streamlit column,
    so it stays in normal document flow and doesn't need fixed positioning.
    """
    theme_colors = {
        "matrix": {
            "panel_bg": "rgba(0, 20, 0, 0.95)",
            "panel_border": "rgba(0, 255, 65, 0.3)",
            "text_color": "#00FF41",
            "text_muted": "#00AA2A",
            "header_bg": "rgba(0, 30, 0, 0.95)",
            "accent": "#00FF41",
        },
        "cyberpunk": {
            "panel_bg": "rgba(13, 2, 33, 0.95)",
            "panel_border": "rgba(255, 0, 128, 0.35)",
            "text_color": "#FF00FF",
            "text_muted": "#BB00BB",
            "header_bg": "rgba(20, 5, 45, 0.95)",
            "accent": "#FF00FF",
        },
        "dark": {
            "panel_bg": "rgba(26, 26, 26, 0.98)",
            "panel_border": "rgba(255, 255, 255, 0.15)",
            "text_color": "#E0E0E0",
            "text_muted": "#888888",
            "header_bg": "rgba(35, 35, 35, 0.95)",
            "accent": "#4A9EFF",
        },
        "nord": {
            "panel_bg": "rgba(46, 52, 64, 0.98)",
            "panel_border": "rgba(136, 192, 208, 0.3)",
            "text_color": "#ECEFF4",
            "text_muted": "#D8DEE9",
            "header_bg": "rgba(59, 66, 82, 0.95)",
            "accent": "#88C0D0",
        },
        "solarized": {
            "panel_bg": "rgba(0, 43, 54, 0.98)",
            "panel_border": "rgba(38, 139, 210, 0.35)",
            "text_color": "#93A1A1",
            "text_muted": "#657B83",
            "header_bg": "rgba(0, 43, 54, 0.95)",
            "accent": "#268BD2",
        },
    }

    colors = theme_colors.get(theme_id, theme_colors["matrix"])

    return f"""
<style>
/* ============================================
   POLISIM CHAT PANEL (COLUMN MODE) - THEME: {theme_id.upper()}
   ============================================ */

/* Hide the marker element */
[data-polisim-chat="true"] {{
    display: none !important;
}}

/* Chat column with class applied by JS */
.polisim-chat-column {{
    position: sticky !important;
    top: 70px !important;
    align-self: flex-start !important;
    height: auto !important;
    max-height: calc(100vh - 90px) !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
    z-index: 50 !important;
}}

/* Style the inner container of the chat column */
.polisim-chat-column > div:first-child {{
    background: {colors['panel_bg']} !important;
    border-radius: 12px !important;
    border: 1px solid {colors['panel_border']} !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    padding: 12px !important;
    max-height: calc(100vh - 110px) !important;
    overflow-y: auto !important;
}}

/* Fallback CSS-only sticky (for browsers supporting :has) */
[data-testid="column"]:has([data-polisim-chat="true"]) {{
    position: sticky !important;
    top: 70px !important;
    align-self: flex-start !important;
    max-height: calc(100vh - 90px) !important;
    overflow-y: auto !important;
    z-index: 50 !important;
}}

[data-testid="column"]:has([data-polisim-chat="true"]) > div:first-child {{
    background: {colors['panel_bg']} !important;
    border-radius: 12px !important;
    border: 1px solid {colors['panel_border']} !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
    padding: 12px !important;
}}

/* Style all text inside chat panel */
.polisim-chat-column *,
[data-testid="column"]:has([data-polisim-chat="true"]) * {{
    color: {colors['text_color']} !important;
}}

/* Style headers */
.polisim-chat-column h4,
[data-testid="column"]:has([data-polisim-chat="true"]) h4 {{
    color: {colors['accent']} !important;
}}

/* Style buttons */
.polisim-chat-column button,
[data-testid="column"]:has([data-polisim-chat="true"]) button {{
    background: transparent !important;
    border: 1px solid {colors['panel_border']} !important;
    color: {colors['text_color']} !important;
}}

.polisim-chat-column button:hover,
[data-testid="column"]:has([data-polisim-chat="true"]) button:hover {{
    background: {colors['panel_border']} !important;
}}

/* Style text inputs */
.polisim-chat-column input,
.polisim-chat-column textarea,
[data-testid="column"]:has([data-polisim-chat="true"]) input,
[data-testid="column"]:has([data-polisim-chat="true"]) textarea {{
    background: rgba(0, 0, 0, 0.3) !important;
    border: 1px solid {colors['panel_border']} !important;
    color: {colors['text_color']} !important;
}}

/* Scrollbar */
.polisim-chat-column::-webkit-scrollbar,
[data-testid="column"]:has([data-polisim-chat="true"])::-webkit-scrollbar {{
    width: 6px !important;
}}

.polisim-chat-column::-webkit-scrollbar-thumb,
[data-testid="column"]:has([data-polisim-chat="true"])::-webkit-scrollbar-thumb {{
    background: {colors['accent']}50 !important;
    border-radius: 3px !important;
}}

/* Muted text color for captions */
.polisim-chat-column [data-testid="stCaptionContainer"] p,
[data-testid="column"]:has([data-polisim-chat="true"]) [data-testid="stCaptionContainer"] p {{
    color: {colors['text_muted']} !important;
}}
</style>

<script>
// Make chat panel fixed position
(function() {{
    const marker = document.querySelector('[data-polisim-chat="true"]');
    if (!marker) return;

    // Find the column ancestor
    let column = marker.parentElement;
    while (column && !column.matches('[data-testid="column"]')) {{
        column = column.parentElement;
    }}
    if (!column) return;

    // Mark it for CSS
    column.classList.add('polisim-chat-column');

    // Get the horizontal block (columns container)
    const hBlock = column.closest('[data-testid="stHorizontalBlock"]');
    if (!hBlock) return;

    // Calculate position based on column's position in the layout
    const rect = column.getBoundingClientRect();
    const scrollTop = window.scrollY || document.documentElement.scrollTop;

    // Apply fixed positioning
    column.style.cssText = `
        position: fixed !important;
        top: 70px !important;
        right: 20px !important;
        width: ${{rect.width}}px !important;
        max-height: calc(100vh - 90px) !important;
        overflow-y: auto !important;
        z-index: 100 !important;
    `;

    // Add a placeholder to maintain layout
    if (!hBlock.querySelector('.polisim-chat-placeholder')) {{
        const placeholder = document.createElement('div');
        placeholder.className = 'polisim-chat-placeholder';
        placeholder.style.cssText = `width: ${{rect.width}}px; min-width: ${{rect.width}}px; flex-shrink: 0;`;
        hBlock.appendChild(placeholder);
    }}
}})();
</script>
"""


# =============================================================================
# Helper Functions
# =============================================================================

def _format_time(dt: datetime) -> str:
    """Format timestamp for display."""
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "Just now"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}m ago"
        else:
            return dt.strftime("%I:%M %p")
    elif diff.days == 1:
        return "Yesterday"
    else:
        return dt.strftime("%b %d")


def _get_agent_icon(agent_type: str) -> str:
    """Get icon for agent type."""
    return AGENT_ICONS.get(agent_type, "🤖")


def _get_agent_color(agent_type: str) -> str:
    """Get color for agent type."""
    return AGENT_COLORS.get(agent_type, "#9E9E9E")


def _hex_to_rgb(hex_color: str) -> str:
    """Convert hex to RGB string."""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"{r}, {g}, {b}"


def _format_timestamp(dt: datetime) -> str:
    """Format timestamp (backward compatible)."""
    return _format_time(dt)


def _filter_messages(messages, **kwargs):
    """Filter messages (backward compatible stub)."""
    return messages


def _extract_mentions(text: str, available_mentions: list) -> List[str]:
    """Extract @mentions from message text."""
    mentions = []
    for mention in available_mentions:
        if f"@{mention['id']}" in text or f"@{mention['name'].lower()}" in text.lower():
            mentions.append(mention['id'])
    return mentions


# =============================================================================
# Message Rendering
# =============================================================================

def _render_message(msg: ChatMessage, is_own: bool = False):
    """Render a single message."""
    if msg.sender_type == "system":
        st.markdown(
            f"""<div class="message message-system">
                <div class="message-content">{msg.content}</div>
                <div class="message-time">{_format_time(msg.timestamp)}</div>
            </div>""",
            unsafe_allow_html=True
        )
    elif msg.sender_type == "agent":
        agent_type = msg.metadata.get("agent_type", "system")
        icon = _get_agent_icon(agent_type)
        color = _get_agent_color(agent_type)
        st.markdown(
            f"""<div class="message message-agent" style="border-color: {color}40; background: {color}15;">
                <div class="message-sender" style="color: {color};">{icon} {msg.sender_name}</div>
                <div class="message-content">{msg.content}</div>
                <div class="message-time">{_format_time(msg.timestamp)}</div>
            </div>""",
            unsafe_allow_html=True
        )
    else:
        css_class = "message-user" if is_own else "message-agent"
        st.markdown(
            f"""<div class="message {css_class}">
                <div class="message-sender">{'You' if is_own else msg.sender_name}</div>
                <div class="message-content">{msg.content}</div>
                <div class="message-time">{_format_time(msg.timestamp)}</div>
            </div>""",
            unsafe_allow_html=True
        )


def _render_messages(messages: List[ChatMessage], current_user_id: str):
    """Render message list."""
    if not messages:
        st.caption("No messages yet. Start the conversation!")
        return
    
    for msg in messages:
        is_own = msg.sender_id == current_user_id
        _render_message(msg, is_own)


# =============================================================================
# Tab Content Renderers
# =============================================================================

def _render_global_chat(user_id: str, user_name: str):
    """Render global chat tab."""
    state = get_chat_state()
    messages = state.get("global_messages", [])
    
    # Message container
    with st.container(height=350):
        _render_messages(messages, user_id)


def _render_regional_chat(user_id: str, user_name: str):
    """Render regional chat tab."""
    state = get_chat_state()
    
    # Region selector
    selected_region = st.selectbox(
        "Select Region",
        US_REGIONS,
        index=US_REGIONS.index(state.get("selected_region", "Northeast")),
        key="region_selector",
        label_visibility="collapsed",
    )
    
    if selected_region != state.get("selected_region"):
        update_chat_state(selected_region=selected_region)
    
    # Get messages for region
    regional = state.get("regional_messages", {})
    messages = regional.get(selected_region, [])
    
    # Message container
    with st.container(height=310):
        if not messages:
            st.caption(f"No messages in {selected_region} yet.")
        else:
            _render_messages(messages, user_id)


def _render_private_chat(user_id: str, user_name: str):
    """Render private chat tab with session management."""
    state = get_chat_state()
    sessions = state.get("private_sessions", [])
    active_session = state.get("active_private_session")
    
    # Session selector/management row
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        session_names = ["Select session..."] + [s.name for s in sessions]
        selected_idx = 0
        if active_session:
            for i, s in enumerate(sessions):
                if s.session_id == active_session:
                    selected_idx = i + 1
                    break
        
        selected = st.selectbox(
            "Session",
            session_names,
            index=selected_idx,
            key="private_session_selector",
            label_visibility="collapsed",
        )
        
        if selected != "Select session..." and sessions:
            for s in sessions:
                if s.name == selected:
                    if s.session_id != active_session:
                        update_chat_state(active_private_session=s.session_id)
                    break
    
    with col2:
        if st.button("➕", key="new_private", help="New Session"):
            _create_private_session()
    
    with col3:
        if st.button("🗑️", key="del_private", help="Delete Session", disabled=not active_session):
            if active_session:
                _delete_private_session(active_session)
    
    # Messages
    with st.container(height=280):
        if active_session:
            messages = state.get("private_messages", {}).get(active_session, [])
            _render_messages(messages, user_id)
        else:
            st.caption("Select or create a private session to start chatting.")


def _render_agent_chat(user_id: str, user_name: str):
    """Render agent swarm chat tab."""
    state = get_chat_state()
    sessions = state.get("agent_sessions", [])
    active_session = state.get("active_agent_session")
    
    # Session selector/management row
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        session_names = ["Select swarm..."] + [s.name for s in sessions]
        selected_idx = 0
        if active_session:
            for i, s in enumerate(sessions):
                if s.session_id == active_session:
                    selected_idx = i + 1
                    break
        
        selected = st.selectbox(
            "Agent Swarm",
            session_names,
            index=selected_idx,
            key="agent_session_selector",
            label_visibility="collapsed",
        )
        
        if selected != "Select swarm..." and sessions:
            for s in sessions:
                if s.name == selected:
                    if s.session_id != active_session:
                        update_chat_state(active_agent_session=s.session_id)
                    break
    
    with col2:
        if st.button("➕", key="new_agent", help="New Swarm"):
            _create_agent_session()
    
    with col3:
        if st.button("🗑️", key="del_agent", help="Delete Swarm", disabled=not active_session):
            if active_session:
                _delete_agent_session(active_session)
    
    # Agent selector (for new sessions)
    if not active_session:
        st.multiselect(
            "Select Agents",
            list(AGENT_ICONS.keys()),
            default=state.get("selected_agents", ["fiscal", "economic"]),
            format_func=lambda x: f"{AGENT_ICONS[x]} {x.title()}",
            key="agent_multiselect",
        )
    
    # Messages
    with st.container(height=250):
        if active_session:
            messages = state.get("agent_messages", {}).get(active_session, [])
            _render_messages(messages, user_id)
        else:
            st.caption("Select agents and create a swarm to start analysis.")


# =============================================================================
# Session Management
# =============================================================================

def _create_private_session():
    """Create a new private chat session."""
    state = get_chat_state()
    sessions = state.get("private_sessions", [])
    
    new_id = f"ps_{len(sessions) + 1}_{datetime.now().timestamp():.0f}"
    new_session = ChatSession(
        session_id=new_id,
        name=f"Private Chat {len(sessions) + 1}",
        chat_type="private",
        created_at=datetime.now(timezone.utc),
        participants=["user_self"],
    )
    
    sessions.append(new_session)
    update_chat_state(
        private_sessions=sessions,
        active_private_session=new_id,
    )
    
    # Initialize empty message list
    private_msgs = state.get("private_messages", {})
    private_msgs[new_id] = []
    update_chat_state(private_messages=private_msgs)
    
    st.rerun()


def _delete_private_session(session_id: str):
    """Delete a private chat session."""
    state = get_chat_state()
    sessions = [s for s in state.get("private_sessions", []) if s.session_id != session_id]
    
    private_msgs = state.get("private_messages", {})
    if session_id in private_msgs:
        del private_msgs[session_id]
    
    update_chat_state(
        private_sessions=sessions,
        active_private_session=None,
        private_messages=private_msgs,
    )
    st.rerun()


def _create_agent_session():
    """Create a new agent swarm session."""
    state = get_chat_state()
    sessions = state.get("agent_sessions", [])
    selected_agents = st.session_state.get("agent_multiselect", ["fiscal", "economic"])
    
    new_id = f"as_{len(sessions) + 1}_{datetime.now().timestamp():.0f}"
    agent_names = ", ".join([a.title() for a in selected_agents[:3]])
    new_session = ChatSession(
        session_id=new_id,
        name=f"Swarm: {agent_names}",
        chat_type="agent_swarm",
        created_at=datetime.now(timezone.utc),
        agents=selected_agents,
    )
    
    sessions.append(new_session)
    update_chat_state(
        agent_sessions=sessions,
        active_agent_session=new_id,
    )
    
    # Initialize with system message
    agent_msgs = state.get("agent_messages", {})
    agent_msgs[new_id] = [
        ChatMessage(
            message_id=f"sys_{new_id}",
            sender_id="system",
            sender_name="System",
            sender_type="system",
            content=f"Agent swarm started with: {agent_names}",
            timestamp=datetime.now(timezone.utc),
            chat_type="agent_swarm",
            session_id=new_id,
        )
    ]
    update_chat_state(agent_messages=agent_msgs)
    
    st.rerun()


def _delete_agent_session(session_id: str):
    """Delete an agent swarm session."""
    state = get_chat_state()
    sessions = [s for s in state.get("agent_sessions", []) if s.session_id != session_id]
    
    agent_msgs = state.get("agent_messages", {})
    if session_id in agent_msgs:
        del agent_msgs[session_id]
    
    update_chat_state(
        agent_sessions=sessions,
        active_agent_session=None,
        agent_messages=agent_msgs,
    )
    st.rerun()


# =============================================================================
# Message Sending
# =============================================================================

def _send_message(content: str, user_id: str, user_name: str, attachment=None):
    """Send a message to the active chat."""
    if not content.strip():
        return
    
    state = get_chat_state()
    active_tab = state.get("active_tab", 0)
    now = datetime.now(timezone.utc)
    
    # Determine chat type and get message list
    if active_tab == 0:  # Global
        chat_type = "global"
        messages = state.get("global_messages", [])
        msg_key = "global_messages"
        session_id = None
    elif active_tab == 1:  # Regional
        chat_type = "regional"
        region = state.get("selected_region", "Northeast")
        regional = state.get("regional_messages", {})
        messages = regional.get(region, [])
        msg_key = None  # Handle separately
        session_id = None
    elif active_tab == 2:  # Private
        chat_type = "private"
        session_id = state.get("active_private_session")
        if not session_id:
            st.warning("Please select or create a private session first.")
            return
        private = state.get("private_messages", {})
        messages = private.get(session_id, [])
        msg_key = None
    else:  # Agent Swarm
        chat_type = "agent_swarm"
        session_id = state.get("active_agent_session")
        if not session_id:
            st.warning("Please select or create an agent swarm first.")
            return
        agent = state.get("agent_messages", {})
        messages = agent.get(session_id, [])
        msg_key = None
    
    # Create message
    new_msg = ChatMessage(
        message_id=f"msg_{now.timestamp():.0f}",
        sender_id=user_id,
        sender_name=user_name,
        sender_type="user",
        content=content,
        timestamp=now,
        chat_type=chat_type,
        session_id=session_id,
        region=state.get("selected_region") if chat_type == "regional" else None,
        attachments=[{"name": attachment.name}] if attachment else [],
    )
    
    messages.append(new_msg)
    
    # Update state
    if msg_key:
        update_chat_state(**{msg_key: messages})
    elif chat_type == "regional":
        regional = state.get("regional_messages", {})
        regional[state.get("selected_region", "Northeast")] = messages
        update_chat_state(regional_messages=regional)
    elif chat_type == "private":
        private = state.get("private_messages", {})
        private[session_id] = messages
        update_chat_state(private_messages=private)
    else:
        agent = state.get("agent_messages", {})
        agent[session_id] = messages
        update_chat_state(agent_messages=agent)
    
    # Add to history
    history = state.get("all_history", [])
    history.append(new_msg)
    update_chat_state(all_history=history)


# =============================================================================
# History Browser
# =============================================================================

def _render_history_browser():
    """Render chat history browser - shows sessions, not individual messages."""
    state = get_chat_state()
    
    st.markdown("### 📚 Chat Sessions")
    
    # Search sessions
    search = st.text_input("Search sessions...", key="history_search", placeholder="Filter sessions...", label_visibility="collapsed")
    search_lower = search.lower() if search else ""
    
    # Collect all sessions
    sessions_list = []
    
    # Global chat as a "session"
    global_msgs = state.get("global_messages", [])
    if global_msgs:
        last_msg = max(global_msgs, key=lambda m: m.timestamp) if global_msgs else None
        sessions_list.append({
            "type": "global",
            "icon": "🌐",
            "name": "Global Chat",
            "id": "global",
            "msg_count": len(global_msgs),
            "last_activity": last_msg.timestamp if last_msg else datetime.now(timezone.utc),
            "preview": last_msg.content[:50] + "..." if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else "No messages"),
        })
    
    # Regional chats
    for region, msgs in state.get("regional_messages", {}).items():
        if msgs:
            last_msg = max(msgs, key=lambda m: m.timestamp)
            sessions_list.append({
                "type": "regional",
                "icon": "🗺️",
                "name": f"{region} Regional",
                "id": f"regional_{region}",
                "msg_count": len(msgs),
                "last_activity": last_msg.timestamp,
                "preview": last_msg.content[:50] + "..." if len(last_msg.content) > 50 else last_msg.content,
            })
    
    # Private sessions
    for session in state.get("private_sessions", []):
        msgs = state.get("private_messages", {}).get(session.session_id, [])
        last_msg = max(msgs, key=lambda m: m.timestamp) if msgs else None
        sessions_list.append({
            "type": "private",
            "icon": "🔒",
            "name": session.name,
            "id": session.session_id,
            "msg_count": len(msgs),
            "last_activity": last_msg.timestamp if last_msg else session.created_at,
            "preview": last_msg.content[:50] + "..." if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else "Empty session"),
        })
    
    # Agent swarm sessions
    for session in state.get("agent_sessions", []):
        msgs = state.get("agent_messages", {}).get(session.session_id, [])
        last_msg = max(msgs, key=lambda m: m.timestamp) if msgs else None
        sessions_list.append({
            "type": "agent_swarm",
            "icon": "🤖",
            "name": session.name,
            "id": session.session_id,
            "msg_count": len(msgs),
            "last_activity": last_msg.timestamp if last_msg else session.created_at,
            "preview": last_msg.content[:50] + "..." if last_msg and len(last_msg.content) > 50 else (last_msg.content if last_msg else "Empty session"),
            "agents": session.agents,
        })
    
    # Filter by search
    if search_lower:
        sessions_list = [s for s in sessions_list if search_lower in s["name"].lower() or search_lower in s["preview"].lower()]
    
    # Sort by last activity
    sessions_list.sort(key=lambda x: x["last_activity"], reverse=True)
    
    st.caption(f"{len(sessions_list)} sessions")
    
    # Display sessions
    with st.container(height=380):
        for sess in sessions_list:
            with st.container():
                col_icon, col_info = st.columns([0.15, 0.85])
                with col_icon:
                    st.markdown(f"### {sess['icon']}")
                with col_info:
                    st.markdown(f"**{sess['name']}**")
                    st.caption(f"{sess['msg_count']} messages • {_format_time(sess['last_activity'])}")
                    st.caption(sess['preview'])
                
                # Click to open session
                if st.button("Open →", key=f"open_{sess['id']}", use_container_width=True):
                    _open_session_from_history(sess)
                    st.rerun()
                
                st.markdown("---")
    
    if st.button("← Back to Chat", use_container_width=True):
        update_chat_state(show_history=False)
        st.rerun()


def _open_session_from_history(session: dict):
    """Open a session from history view."""
    sess_type = session["type"]
    sess_id = session["id"]
    
    if sess_type == "global":
        update_chat_state(active_tab=0, show_history=False)
    elif sess_type == "regional":
        region = sess_id.replace("regional_", "")
        update_chat_state(active_tab=1, selected_region=region, show_history=False)
    elif sess_type == "private":
        update_chat_state(active_tab=2, active_private_session=sess_id, show_history=False)
    elif sess_type == "agent_swarm":
        update_chat_state(active_tab=3, active_agent_session=sess_id, show_history=False)


# =============================================================================
# Export Functions
# =============================================================================

def _export_chat_json():
    """Export chat history as JSON."""
    state = get_chat_state()
    
    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "global_messages": [_msg_to_dict(m) for m in state.get("global_messages", [])],
        "regional_messages": {
            region: [_msg_to_dict(m) for m in msgs]
            for region, msgs in state.get("regional_messages", {}).items()
        },
        "private_sessions": [
            {
                "session": {
                    "id": s.session_id,
                    "name": s.name,
                    "created_at": s.created_at.isoformat(),
                },
                "messages": [_msg_to_dict(m) for m in state.get("private_messages", {}).get(s.session_id, [])]
            }
            for s in state.get("private_sessions", [])
        ],
        "agent_sessions": [
            {
                "session": {
                    "id": s.session_id,
                    "name": s.name,
                    "agents": s.agents,
                    "created_at": s.created_at.isoformat(),
                },
                "messages": [_msg_to_dict(m) for m in state.get("agent_messages", {}).get(s.session_id, [])]
            }
            for s in state.get("agent_sessions", [])
        ],
    }
    
    return json.dumps(export_data, indent=2)


def _msg_to_dict(msg: ChatMessage) -> dict:
    """Convert message to dict for export."""
    return {
        "id": msg.message_id,
        "sender": msg.sender_name,
        "sender_type": msg.sender_type,
        "content": msg.content,
        "timestamp": msg.timestamp.isoformat(),
        "chat_type": msg.chat_type,
    }


# =============================================================================
# Main Render Function
# =============================================================================

def render_chat_panel(
    user_id: str = "user_self",
    user_name: str = "You",
    theme_id: Optional[str] = None,
    use_column_mode: bool = False,
):
    """Render the PoliSim chat panel.

    Args:
        user_id: Current user's ID
        user_name: Current user's display name
        theme_id: Theme ID for styling (auto-detected from session state if not provided)
        use_column_mode: If True, render as column-friendly panel instead of fixed overlay
    """
    if not HAS_STREAMLIT:
        return

    init_chat_state()
    state = get_chat_state()

    # Get current theme from session state if not provided
    if theme_id is None:
        settings = st.session_state.get("settings", {})
        theme_id = settings.get("theme", "matrix")

    # Inject theme-aware CSS (column mode uses simpler styling)
    if use_column_mode:
        chat_css = get_column_chat_css(theme_id or "matrix")
    else:
        chat_css = get_chat_css(theme_id or "matrix")
    st.markdown(chat_css, unsafe_allow_html=True)

    # Use a container with a marker div that CSS can use to identify and style this block
    # The marker must be the first child for :has() selector to work
    with st.container():
        # Marker element - CSS targets parent container via :has([data-polisim-chat])
        st.markdown('<div data-polisim-chat="true" style="display:none;"></div>', unsafe_allow_html=True)
        
        # Check if showing history
        if state.get("show_history", False):
            _render_history_browser()
            return
        
        # Header with title and history button
        col_title, col_history = st.columns([0.8, 0.2])
        with col_title:
            st.markdown("#### 💬 PoliSim Chat")
        with col_history:
            if st.button("📚", key="open_history", help="Chat History - View Sessions"):
                update_chat_state(show_history=True)
                st.rerun()
        
        # Tab selection with icon buttons (not radio)
        active_tab = state.get("active_tab", 0)
        tab_icons = ["🌐", "🗺️", "🔒", "🤖"]
        tab_labels = ["Global", "Regional", "Private", "Agents"]
        
        cols = st.columns(4)
        for i, (icon, label) in enumerate(zip(tab_icons, tab_labels)):
            with cols[i]:
                # Use different styling for active tab
                btn_type = "primary" if i == active_tab else "secondary"
                if st.button(icon, key=f"tab_{i}", help=label, use_container_width=True, type=btn_type):
                    if i != active_tab:
                        update_chat_state(active_tab=i)
                        st.rerun()
        
        # Render active tab content
        if active_tab == 0:
            _render_global_chat(user_id, user_name)
        elif active_tab == 1:
            _render_regional_chat(user_id, user_name)
        elif active_tab == 2:
            _render_private_chat(user_id, user_name)
        else:
            _render_agent_chat(user_id, user_name)
        
        # Message input area with paperclip on left
        col_attach, col_input, col_send = st.columns([0.12, 0.73, 0.15])
        
        # Track uploaded file in session state
        if "pending_file" not in st.session_state:
            st.session_state.pending_file = None
        
        with col_attach:
            # Paperclip button opens popover with file uploader
            with st.popover("📎", help="Attach file"):
                uploaded_file = st.file_uploader(
                    "Choose file",
                    key="attach_file_hidden",
                    label_visibility="collapsed",
                )
                if uploaded_file:
                    st.session_state.pending_file = uploaded_file
                    st.success(f"✅ {uploaded_file.name}")
        
        with col_input:
            message_input = st.text_input(
                "Message",
                placeholder="Type a message...",
                key="chat_message_input",
                label_visibility="collapsed",
            )
        
        with col_send:
            send_clicked = st.button("📤", key="send_btn", use_container_width=True, help="Send")
        
        # Show attached file indicator below input
        if st.session_state.pending_file:
            col_file, col_clear = st.columns([0.85, 0.15])
            with col_file:
                st.caption(f"📎 {st.session_state.pending_file.name}")
            with col_clear:
                if st.button("✕", key="clear_file", help="Remove file"):
                    st.session_state.pending_file = None
                    st.rerun()
        
        # Handle send
        if send_clicked and message_input:
            _send_message(message_input, user_id, user_name, st.session_state.pending_file)
            st.session_state.pending_file = None
            st.rerun()
        
        # Compact action bar
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📥", key="export_btn", help="Export Chat", use_container_width=True):
                export_json = _export_chat_json()
                st.download_button(
                    "💾 JSON",
                    export_json,
                    file_name=f"polisim_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    key="download_json",
                )
        
        with col2:
            st.button("🤖", key="agents_btn", help="Agent Selection", use_container_width=True)
        
        with col3:
            st.button("🔍", key="analyze_btn", help="Quick Analyze", use_container_width=True)
        
        with col4:
            st.button("📊", key="chart_btn", help="Request Chart", use_container_width=True)


# =============================================================================
# Backward Compatibility Wrappers
# =============================================================================

# Keep old function names for compatibility with dashboard.py
def init_chat_sidebar_state():
    """Initialize chat state (backward compatible)."""
    init_chat_state()


def get_chat_sidebar_state() -> Dict[str, Any]:
    """Get chat state (backward compatible)."""
    return get_chat_state()


def update_chat_sidebar_state(**kwargs):
    """Update chat state (backward compatible)."""
    update_chat_state(**kwargs)


def render_chat_right_panel(
    user_id: Optional[str] = None,
    user_name: str = "User",
    api_base_url: str = "",
    demo_mode: bool = True,
    use_column_mode: bool = False,
):
    """Render chat panel (backward compatible).

    Args:
        user_id: User ID for chat
        user_name: Display name for user
        api_base_url: API base URL (unused, for backward compat)
        demo_mode: Whether in demo mode (unused, for backward compat)
        use_column_mode: If True, use column-friendly styling instead of fixed overlay
    """
    render_chat_panel(
        user_id=user_id or "user_self",
        user_name=user_name,
        use_column_mode=use_column_mode,
    )


def render_chat_sidebar(
    user_id: Optional[str] = None,
    user_name: str = "User",
    api_base_url: str = "",
    demo_mode: bool = True,
):
    """Render chat panel in sidebar (backward compatible)."""
    render_chat_panel(
        user_id=user_id or "user_self",
        user_name=user_name,
    )


# Keep these for test compatibility
def create_demo_messages():
    """Create demo messages (backward compatible)."""
    init_chat_state()
    state = get_chat_state()
    # Convert to MessageDisplay for test compatibility
    messages = []
    for msg in state.get("global_messages", []):
        messages.append(MessageDisplay(
            message_id=msg.message_id,
            sender_id=msg.sender_id,
            sender_type=msg.sender_type,
            sender_name=msg.sender_name,
            sender_icon=AGENT_ICONS.get(msg.metadata.get("agent_type", "system"), "👤"),
            sender_color=AGENT_COLORS.get(msg.metadata.get("agent_type", "system"), "#2196F3"),
            content=msg.content,
            message_type="text",
            timestamp=msg.timestamp,
        ))
    return messages


def create_demo_channels():
    """Create demo channels (backward compatible)."""
    return [
        ChannelInfo(
            channel_id="ch_global",
            name="Global Chat",
            channel_type="public",
            icon="🌐",
        ),
        ChannelInfo(
            channel_id="ch_regional",
            name="Regional Chat",
            channel_type="public",
            icon="🗺️",
        ),
    ]


class ChatSidebar:
    """Chat sidebar class (backward compatible)."""
    
    def __init__(self, api_base_url: str = "", user_id: str = "", user_name: str = ""):
        self.user_id = user_id or "user_self"
        self.user_name = user_name or "User"
    
    def render(self):
        render_chat_panel(self.user_id, self.user_name)
    
    def render_right_panel(self):
        render_chat_panel(self.user_id, self.user_name)


# Exports for imports
__all__ = [
    "render_chat_panel",
    "render_chat_right_panel", 
    "render_chat_sidebar",
    "init_chat_state",
    "init_chat_sidebar_state",
    "get_chat_state",
    "get_chat_sidebar_state",
    "update_chat_sidebar_state",
    "ChatSidebar",
    "ChatMessage",
    "ChatSession",
    "ChannelInfo",
    "MessageDisplay",
    "AgentPresence",
    "ChatExportOptions",
    "create_demo_messages",
    "create_demo_channels",
    "AGENT_COLORS",
    "AGENT_ICONS",
    "MESSAGE_TYPE_ICONS",
    "SYSTEM_EVENT_ICONS",
    "_hex_to_rgb",
    "_format_timestamp",
    "_filter_messages",
    "_extract_mentions",
]


if __name__ == "__main__":
    if HAS_STREAMLIT:
        st.set_page_config(layout="wide", page_title="PoliSim Chat")
        render_chat_panel()
