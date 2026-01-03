"""Live Analysis Panel for Real-Time Swarm Analysis Streaming (Phase 7.2.2).

This module provides Streamlit UI components for displaying real-time
multi-agent swarm analysis, including:
- Live event stream display
- Agent activity indicators
- Stage progress tracking
- Thought display with filtering
- Time elapsed/ETA display

Example:
    from ui.live_analysis_panel import LiveAnalysisPanel, render_live_analysis
    
    # In Streamlit app
    panel = LiveAnalysisPanel()
    panel.render(analysis_id="abc123")
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum

try:
    import streamlit as st
    import plotly.graph_objects as go
    import pandas as pd
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes for UI State
# =============================================================================

class EventDisplayType(Enum):
    """Display types for filtering events."""
    ALL = "all"
    FINDINGS = "findings"
    THOUGHTS = "thoughts"
    DEBATES = "debates"
    PROGRESS = "progress"


@dataclass
class AgentActivityState:
    """Current state of an agent in the analysis."""
    
    agent_id: str
    agent_type: str
    agent_label: str
    agent_icon: str
    status: str = "idle"  # idle, analyzing, debating, completed
    confidence: Optional[float] = None
    findings_count: int = 0
    latest_thought: Optional[str] = None
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class StreamEventDisplay:
    """Event formatted for UI display."""
    
    event_id: str
    event_type: str
    timestamp: datetime
    agent_id: Optional[str] = None
    agent_icon: str = "🤖"
    agent_label: str = "Agent"
    content: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    importance: str = "normal"  # low, normal, high, critical
    display_type: EventDisplayType = EventDisplayType.ALL
    
    def get_color(self) -> str:
        """Get color based on event type and importance."""
        colors = {
            "pipeline_started": "#4CAF50",   # Green
            "stage_changed": "#2196F3",      # Blue
            "agent_started": "#9C27B0",      # Purple
            "agent_thinking": "#607D8B",     # Blue-grey
            "agent_finding": "#FF9800",      # Orange
            "agent_completed": "#4CAF50",    # Green
            "debate_started": "#E91E63",     # Pink
            "debate_turn": "#FF5722",        # Deep orange
            "debate_convergence": "#00BCD4", # Cyan
            "consensus_reached": "#8BC34A",  # Light green
            "analysis_complete": "#4CAF50",  # Green
            "error": "#F44336",              # Red
        }
        if self.importance == "critical":
            return "#F44336"
        return colors.get(self.event_type, "#9E9E9E")


@dataclass
class AnalysisProgressState:
    """Current progress of the analysis."""
    
    analysis_id: str = ""
    bill_id: str = ""
    stage: str = "initialized"
    stage_progress: float = 0.0
    agents_complete: int = 0
    agents_total: int = 4
    debates_complete: int = 0
    debates_expected: int = 0
    elapsed_seconds: float = 0.0
    estimated_remaining_seconds: int = 0
    start_time: Optional[datetime] = None
    
    def get_stage_label(self) -> str:
        """Get human-readable stage label."""
        labels = {
            "initialized": "🎬 Initializing",
            "ingesting": "📥 Reading Bill",
            "analyzing": "🔍 Analyzing",
            "cross_reviewing": "🔄 Cross-Review",
            "debating": "💬 Debating",
            "voting": "🗳️ Voting",
            "synthesizing": "📝 Synthesizing",
            "complete": "✅ Complete",
            "error": "❌ Error",
        }
        return labels.get(self.stage, self.stage.title())
    
    def get_overall_progress(self) -> float:
        """Calculate overall progress as percentage."""
        stage_weights = {
            "initialized": 0.0,
            "ingesting": 0.1,
            "analyzing": 0.4,
            "cross_reviewing": 0.6,
            "debating": 0.75,
            "voting": 0.85,
            "synthesizing": 0.95,
            "complete": 1.0,
            "error": 0.0,
        }
        base = stage_weights.get(self.stage, 0.0)
        return min(base + (self.stage_progress * 0.1), 1.0)


# =============================================================================
# Session State Management
# =============================================================================

def init_live_analysis_state():
    """Initialize session state for live analysis."""
    if "live_analysis" not in st.session_state:
        st.session_state.live_analysis = {
            "active": False,
            "analysis_id": None,
            "events": [],
            "agents": {},
            "progress": AnalysisProgressState(),
            "filter_type": EventDisplayType.ALL,
            "filter_agent": None,
            "search_query": "",
            "auto_scroll": True,
            "expanded_agents": set(),
            "ws_connected": False,
            "last_event_time": None,
            "confidence_history": {},  # agent_id -> [(timestamp, confidence)]
        }


def get_live_analysis_state() -> Dict[str, Any]:
    """Get current live analysis state from session."""
    init_live_analysis_state()
    return st.session_state.live_analysis


def update_live_analysis_state(**kwargs):
    """Update live analysis state."""
    init_live_analysis_state()
    for key, value in kwargs.items():
        st.session_state.live_analysis[key] = value


# =============================================================================
# Event Processing
# =============================================================================

def process_stream_event(event_data: Dict[str, Any]) -> StreamEventDisplay:
    """Process raw stream event into display format.
    
    Args:
        event_data: Raw event data from WebSocket
    
    Returns:
        StreamEventDisplay for rendering
    """
    event_type = event_data.get("event_type", "unknown")
    data = event_data.get("data", {})
    
    # Determine display type
    display_type = EventDisplayType.PROGRESS
    if event_type in ["agent_finding"]:
        display_type = EventDisplayType.FINDINGS
    elif event_type in ["agent_thinking"]:
        display_type = EventDisplayType.THOUGHTS
    elif event_type in ["debate_started", "debate_turn", "debate_convergence"]:
        display_type = EventDisplayType.DEBATES
    
    # Build content string
    content = _build_event_content(event_type, data)
    
    # Determine importance
    importance = "normal"
    if event_type in ["consensus_reached", "analysis_complete"]:
        importance = "high"
    elif event_type == "error":
        importance = "critical"
    elif event_type == "agent_thinking":
        importance = "low"
    
    return StreamEventDisplay(
        event_id=event_data.get("event_id", ""),
        event_type=event_type,
        timestamp=datetime.fromisoformat(event_data.get("timestamp", datetime.now().isoformat())),
        agent_id=data.get("agent_id"),
        agent_icon=data.get("agent_icon", "🤖"),
        agent_label=data.get("agent_label", "Agent"),
        content=content,
        details=data,
        importance=importance,
        display_type=display_type,
    )


def _build_event_content(event_type: str, data: Dict[str, Any]) -> str:
    """Build human-readable content string for event."""
    if event_type == "pipeline_started":
        return f"Analysis pipeline started for bill {data.get('bill_id', 'Unknown')}"
    
    elif event_type == "stage_changed":
        return f"Stage changed to: {data.get('stage', 'Unknown')}"
    
    elif event_type == "agent_started":
        return f"{data.get('agent_label', 'Agent')} started analysis"
    
    elif event_type == "agent_thinking":
        thought_type = data.get("thought_label", "Thinking")
        return f"{thought_type}: {data.get('content', '')[:200]}"
    
    elif event_type == "agent_finding":
        category = data.get("category", "general")
        desc = data.get("description", "")[:150]
        return f"[{category.upper()}] {desc}"
    
    elif event_type == "agent_completed":
        findings = data.get("findings_count", 0)
        conf = data.get("overall_confidence", 0) * 100
        return f"Completed with {findings} findings (confidence: {conf:.0f}%)"
    
    elif event_type == "debate_started":
        topic = data.get("topic", "Unknown topic")
        participants = data.get("participant_count", 0)
        return f"Debate started: {topic} ({participants} participants)"
    
    elif event_type == "debate_turn":
        turn_type = data.get("turn_type", "statement")
        content = data.get("content", "")[:150]
        target = data.get("target_agent")
        if target:
            return f"[{turn_type.upper()}] → {target}: {content}"
        return f"[{turn_type.upper()}] {content}"
    
    elif event_type == "debate_convergence":
        score = data.get("convergence_score", 0) * 100
        change = data.get("change")
        change_str = f" ({'+' if change > 0 else ''}{change*100:.1f}%)" if change else ""
        return f"Convergence: {score:.0f}%{change_str}"
    
    elif event_type == "consensus_reached":
        level = data.get("consensus_level", "unknown")
        findings = data.get("agreed_findings_count", 0)
        return f"🎉 Consensus reached: {level} ({findings} agreed findings)"
    
    elif event_type == "analysis_complete":
        return "✅ Analysis complete"
    
    elif event_type == "error":
        return f"❌ Error: {data.get('message', 'Unknown error')}"
    
    return f"Event: {event_type}"


def update_agent_state(state: Dict[str, Any], event: StreamEventDisplay):
    """Update agent state based on event."""
    agent_id = event.agent_id
    if not agent_id:
        return
    
    if agent_id not in state["agents"]:
        state["agents"][agent_id] = AgentActivityState(
            agent_id=agent_id,
            agent_type=event.details.get("agent_type", "unknown"),
            agent_label=event.agent_label,
            agent_icon=event.agent_icon,
        )
    
    agent = state["agents"][agent_id]
    agent.last_updated = event.timestamp
    
    if event.event_type == "agent_started":
        agent.status = "analyzing"
    elif event.event_type == "agent_thinking":
        agent.latest_thought = event.content[:100]
    elif event.event_type == "agent_finding":
        agent.findings_count += 1
    elif event.event_type == "agent_completed":
        agent.status = "completed"
        agent.confidence = event.details.get("overall_confidence")
        agent.findings_count = event.details.get("findings_count", agent.findings_count)
    elif event.event_type in ["debate_started", "debate_turn"]:
        agent.status = "debating"
    
    # Track confidence history
    if agent.confidence is not None:
        if agent_id not in state["confidence_history"]:
            state["confidence_history"][agent_id] = []
        state["confidence_history"][agent_id].append(
            (event.timestamp, agent.confidence)
        )


def update_progress_state(state: Dict[str, Any], event_data: Dict[str, Any]):
    """Update progress state from progress event."""
    data = event_data.get("data", {})
    progress = state["progress"]
    
    progress.stage = data.get("stage", progress.stage)
    progress.stage_progress = data.get("stage_progress", progress.stage_progress)
    progress.agents_complete = data.get("agents_complete", progress.agents_complete)
    progress.agents_total = data.get("agents_total", progress.agents_total)
    progress.debates_complete = data.get("debates_complete", progress.debates_complete)
    progress.debates_expected = data.get("debates_expected", progress.debates_expected)
    progress.elapsed_seconds = data.get("elapsed_seconds", progress.elapsed_seconds)
    progress.estimated_remaining_seconds = data.get("estimated_time_remaining_seconds", 0)


# =============================================================================
# UI Rendering Components
# =============================================================================

def render_progress_header(progress: AnalysisProgressState):
    """Render the progress header with stage indicator and progress bar."""
    if not HAS_STREAMLIT:
        return
    
    col1, col2, col3 = st.columns([2, 3, 2])
    
    with col1:
        st.markdown(f"### {progress.get_stage_label()}")
    
    with col2:
        overall = progress.get_overall_progress()
        st.progress(overall, text=f"{overall*100:.0f}% Complete")
    
    with col3:
        elapsed = int(progress.elapsed_seconds)
        eta = progress.estimated_remaining_seconds
        elapsed_str = f"{elapsed//60}:{elapsed%60:02d}"
        eta_str = f"{eta//60}:{eta%60:02d}" if eta > 0 else "--:--"
        st.markdown(f"⏱️ **{elapsed_str}** elapsed | ETA: **{eta_str}**")


def render_agent_status_row(agents: Dict[str, AgentActivityState]):
    """Render row of agent status indicators."""
    if not HAS_STREAMLIT or not agents:
        return
    
    st.markdown("#### 🤖 Agent Status")
    
    # Create columns for agents
    cols = st.columns(min(len(agents), 4))
    
    for i, (agent_id, agent) in enumerate(agents.items()):
        with cols[i % 4]:
            status_emoji = {
                "idle": "⚪",
                "analyzing": "🔵",
                "debating": "🟡",
                "completed": "🟢",
            }.get(agent.status, "⚪")
            
            conf_str = f"{agent.confidence*100:.0f}%" if agent.confidence else "--"
            
            st.markdown(f"""
            <div style="padding: 8px; border-radius: 8px; background: rgba(0,0,0,0.1); margin: 4px 0;">
                <div style="font-size: 24px;">{agent.agent_icon} {status_emoji}</div>
                <div style="font-weight: bold;">{agent.agent_label}</div>
                <div style="font-size: 12px;">
                    📊 {agent.findings_count} findings<br>
                    🎯 Confidence: {conf_str}
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_event_filters(state: Dict[str, Any]) -> Tuple[EventDisplayType, Optional[str], str]:
    """Render event filtering controls."""
    if not HAS_STREAMLIT:
        return EventDisplayType.ALL, None, ""
    
    col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
    
    with col1:
        filter_options = {
            "All Events": EventDisplayType.ALL,
            "Findings Only": EventDisplayType.FINDINGS,
            "Thoughts": EventDisplayType.THOUGHTS,
            "Debates": EventDisplayType.DEBATES,
            "Progress": EventDisplayType.PROGRESS,
        }
        selected = st.selectbox(
            "Filter by Type",
            list(filter_options.keys()),
            key="event_type_filter",
        )
        filter_type = filter_options[selected]
    
    with col2:
        agent_ids = ["All Agents"] + list(state.get("agents", {}).keys())
        selected_agent = st.selectbox(
            "Filter by Agent",
            agent_ids,
            key="agent_filter",
        )
        filter_agent = None if selected_agent == "All Agents" else selected_agent
    
    with col3:
        search_query = st.text_input(
            "Search",
            placeholder="Search events...",
            key="event_search",
        )
    
    with col4:
        auto_scroll = st.checkbox("Auto-scroll", value=True, key="auto_scroll")
        state["auto_scroll"] = auto_scroll
    
    return filter_type, filter_agent, search_query


def filter_events(
    events: List[StreamEventDisplay],
    filter_type: EventDisplayType,
    filter_agent: Optional[str],
    search_query: str,
) -> List[StreamEventDisplay]:
    """Filter events based on criteria."""
    filtered = events
    
    # Filter by type
    if filter_type != EventDisplayType.ALL:
        filtered = [e for e in filtered if e.display_type == filter_type]
    
    # Filter by agent
    if filter_agent:
        filtered = [e for e in filtered if e.agent_id == filter_agent]
    
    # Filter by search query
    if search_query:
        query_lower = search_query.lower()
        filtered = [
            e for e in filtered
            if query_lower in e.content.lower() or query_lower in e.agent_label.lower()
        ]
    
    return filtered


def render_event_stream(events: List[StreamEventDisplay], auto_scroll: bool = True):
    """Render the scrollable event stream."""
    if not HAS_STREAMLIT:
        return
    
    # Container for events with custom styling
    st.markdown("""
    <style>
    .event-stream {
        max-height: 500px;
        overflow-y: auto;
        padding: 8px;
        border-radius: 8px;
        background: rgba(0,0,0,0.05);
    }
    .event-item {
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        border-left: 4px solid;
        background: rgba(255,255,255,0.7);
    }
    .event-timestamp {
        font-size: 10px;
        color: #666;
    }
    .event-agent {
        font-weight: bold;
        margin-right: 8px;
    }
    .event-content {
        margin-top: 4px;
    }
    .event-high { background: rgba(76, 175, 80, 0.15); }
    .event-critical { background: rgba(244, 67, 54, 0.15); }
    .event-low { opacity: 0.7; }
    </style>
    """, unsafe_allow_html=True)
    
    if not events:
        st.info("📡 Waiting for analysis events...")
        return
    
    # Render events
    event_container = st.container()
    
    with event_container:
        for event in events[-100:]:  # Show last 100 events
            importance_class = f"event-{event.importance}" if event.importance != "normal" else ""
            timestamp_str = event.timestamp.strftime("%H:%M:%S")
            
            st.markdown(f"""
            <div class="event-item {importance_class}" style="border-left-color: {event.get_color()};">
                <span class="event-timestamp">{timestamp_str}</span>
                <span class="event-agent">{event.agent_icon} {event.agent_label}</span>
                <div class="event-content">{event.content}</div>
            </div>
            """, unsafe_allow_html=True)


def render_agent_thought_expanders(state: Dict[str, Any]):
    """Render expandable sections for each agent's thoughts."""
    if not HAS_STREAMLIT:
        return
    
    agents = state.get("agents", {})
    events = state.get("events", [])
    
    if not agents:
        return
    
    st.markdown("#### 💭 Agent Thoughts")
    
    for agent_id, agent in agents.items():
        # Get this agent's thoughts
        agent_thoughts = [
            e for e in events
            if e.agent_id == agent_id and e.event_type == "agent_thinking"
        ]
        
        with st.expander(
            f"{agent.agent_icon} {agent.agent_label} ({len(agent_thoughts)} thoughts)",
            expanded=agent_id in state.get("expanded_agents", set()),
        ):
            if not agent_thoughts:
                st.caption("No thoughts recorded yet.")
            else:
                for thought in agent_thoughts[-20:]:  # Last 20 thoughts
                    thought_type = thought.details.get("thought_label", "Thinking")
                    st.markdown(f"""
                    **{thought_type}** ({thought.timestamp.strftime('%H:%M:%S')})  
                    {thought.content}
                    """)
                    st.divider()


# =============================================================================
# Main Panel Component
# =============================================================================

class LiveAnalysisPanel:
    """Main component for live analysis streaming display.
    
    Provides a complete UI for viewing real-time swarm analysis,
    including progress tracking, agent status, and event streaming.
    
    Example:
        panel = LiveAnalysisPanel()
        panel.render(analysis_id="abc123")
    """
    
    def __init__(self, ws_url: Optional[str] = None):
        """Initialize the live analysis panel.
        
        Args:
            ws_url: WebSocket server URL (defaults to localhost:8000)
        """
        self.ws_url = ws_url or "ws://localhost:8000"
        init_live_analysis_state()
    
    def render(self, analysis_id: Optional[str] = None):
        """Render the complete live analysis panel.
        
        Args:
            analysis_id: ID of analysis to display (or use active analysis)
        """
        if not HAS_STREAMLIT:
            logger.warning("Streamlit not available - cannot render panel")
            return
        
        state = get_live_analysis_state()
        
        # Header
        st.markdown("## 🔴 Live Analysis")
        
        # Check if analysis is active
        if not state["active"] and not analysis_id:
            st.info("No active analysis. Start a swarm analysis to see live updates.")
            self._render_demo_mode()
            return
        
        # Progress header
        render_progress_header(state["progress"])
        
        st.divider()
        
        # Agent status row
        render_agent_status_row(state["agents"])
        
        st.divider()
        
        # Event stream with filters
        filter_type, filter_agent, search_query = render_event_filters(state)
        
        # Filter and render events
        filtered_events = filter_events(
            state["events"],
            filter_type,
            filter_agent,
            search_query,
        )
        render_event_stream(filtered_events, state["auto_scroll"])
        
        # Agent thought expanders
        if state.get("events"):
            render_agent_thought_expanders(state)
    
    def _render_demo_mode(self):
        """Render demo mode with simulated events."""
        st.markdown("### 🎮 Demo Mode")
        
        if st.button("▶️ Run Demo Analysis"):
            self._run_demo_analysis()
    
    def _run_demo_analysis(self):
        """Run a simulated analysis for demo purposes."""
        state = get_live_analysis_state()
        state["active"] = True
        state["events"] = []
        state["agents"] = {}
        state["progress"] = AnalysisProgressState(
            analysis_id="demo-123",
            bill_id="HR-001",
            start_time=datetime.now(),
        )
        
        # Simulate some events
        demo_events = [
            {"event_type": "pipeline_started", "data": {"bill_id": "HR-001"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "stage_changed", "data": {"stage": "analyzing"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_started", "data": {"agent_id": "fiscal-1", "agent_type": "fiscal", "agent_label": "Fiscal Analyst", "agent_icon": "💰"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_started", "data": {"agent_id": "healthcare-1", "agent_type": "healthcare", "agent_label": "Healthcare Expert", "agent_icon": "🏥"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_thinking", "data": {"agent_id": "fiscal-1", "agent_label": "Fiscal Analyst", "agent_icon": "💰", "thought_label": "Calculating", "content": "Analyzing revenue impact from proposed tax changes..."}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_finding", "data": {"agent_id": "fiscal-1", "agent_label": "Fiscal Analyst", "agent_icon": "💰", "category": "revenue", "description": "Proposed tax increase expected to generate $150B over 10 years", "confidence": 0.85}, "timestamp": datetime.now().isoformat()},
        ]
        
        for event_data in demo_events:
            event = process_stream_event(event_data)
            state["events"].append(event)
            update_agent_state(state, event)
        
        st.rerun()
    
    async def connect_websocket(self, analysis_id: str):
        """Connect to WebSocket and receive events.
        
        Args:
            analysis_id: Analysis ID to subscribe to
        """
        if not HAS_WEBSOCKETS:
            logger.warning("websockets package not available")
            return
        
        state = get_live_analysis_state()
        url = f"{self.ws_url}/ws/analysis/{analysis_id}"
        
        try:
            async with websockets.connect(url) as ws:
                state["ws_connected"] = True
                state["active"] = True
                state["analysis_id"] = analysis_id
                
                async for message in ws:
                    event_data = json.loads(message)
                    event = process_stream_event(event_data)
                    
                    state["events"].append(event)
                    state["last_event_time"] = datetime.now()
                    
                    update_agent_state(state, event)
                    update_progress_state(state, event_data)
                    
                    # Check for completion
                    if event.event_type in ["analysis_complete", "error"]:
                        state["active"] = False
                        break
                        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            state["ws_connected"] = False
            state["active"] = False


# =============================================================================
# Convenience Functions
# =============================================================================

def render_live_analysis(analysis_id: Optional[str] = None):
    """Render live analysis panel (convenience function).
    
    Args:
        analysis_id: Optional analysis ID to display
    """
    panel = LiveAnalysisPanel()
    panel.render(analysis_id)


def start_live_analysis_stream(analysis_id: str, ws_url: Optional[str] = None):
    """Start streaming live analysis events.
    
    Args:
        analysis_id: Analysis ID to stream
        ws_url: Optional WebSocket URL
    """
    panel = LiveAnalysisPanel(ws_url)
    asyncio.run(panel.connect_websocket(analysis_id))


def add_demo_event(event_type: str, data: Dict[str, Any]):
    """Add a demo event to the live analysis state.
    
    Useful for testing and demonstrations without a live WebSocket.
    
    Args:
        event_type: Type of event
        data: Event data dictionary
    """
    state = get_live_analysis_state()
    
    event_data = {
        "event_id": f"demo-{len(state['events'])}",
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now().isoformat(),
    }
    
    event = process_stream_event(event_data)
    state["events"].append(event)
    update_agent_state(state, event)


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "LiveAnalysisPanel",
    "render_live_analysis",
    "start_live_analysis_stream",
    "add_demo_event",
    "process_stream_event",
    "StreamEventDisplay",
    "AgentActivityState",
    "AnalysisProgressState",
    "EventDisplayType",
]
