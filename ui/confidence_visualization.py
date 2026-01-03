"""Confidence Band Visualization for Live Analysis (Phase 7.2.2).

This module provides Streamlit/Plotly components for visualizing
agent confidence levels in real-time, including:
- Live confidence line chart over time/stages
- Per-agent confidence tracking
- Convergence moment highlighting
- Interactive hover details
- Shaded confidence bands

Example:
    from ui.confidence_visualization import (
        render_confidence_chart,
        ConfidenceTracker,
    )
    
    # Track confidence over time
    tracker = ConfidenceTracker()
    tracker.add_point("fiscal-1", 0.85, stage="analyzing")
    
    # Render chart
    render_confidence_chart(tracker.get_data())
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import numpy as np
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ConfidencePoint:
    """Single confidence measurement point."""
    
    agent_id: str
    agent_type: str
    agent_label: str
    confidence: float
    timestamp: datetime
    stage: str = "analyzing"
    finding_id: Optional[str] = None
    event_type: str = "measurement"  # measurement, finding, debate, consensus
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "agent_label": self.agent_label,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "event_type": self.event_type,
        }


@dataclass
class ConfidenceBand:
    """Aggregate confidence band across agents."""
    
    timestamp: datetime
    stage: str
    mean_confidence: float
    p10: float  # 10th percentile
    p25: float  # 25th percentile
    p50: float  # Median
    p75: float  # 75th percentile
    p90: float  # 90th percentile
    agent_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "stage": self.stage,
            "mean": self.mean_confidence,
            "p10": self.p10,
            "p25": self.p25,
            "p50": self.p50,
            "p75": self.p75,
            "p90": self.p90,
            "agent_count": self.agent_count,
        }


@dataclass
class ConvergenceMoment:
    """Marks a significant convergence event."""
    
    timestamp: datetime
    stage: str
    convergence_score: float
    previous_score: float
    description: str
    agents_involved: List[str] = field(default_factory=list)
    
    @property
    def improvement(self) -> float:
        """Calculate improvement from previous score."""
        return self.convergence_score - self.previous_score


# =============================================================================
# Agent Color Mapping
# =============================================================================

AGENT_COLORS = {
    "fiscal": "#4CAF50",        # Green
    "economic": "#2196F3",      # Blue
    "healthcare": "#9C27B0",    # Purple
    "social_security": "#FF9800",  # Orange
    "equity": "#E91E63",        # Pink
    "implementation": "#00BCD4", # Cyan
    "behavioral": "#795548",    # Brown
    "legal": "#607D8B",         # Blue-grey
    "judge": "#F44336",         # Red
    "coordinator": "#9E9E9E",   # Grey
}

AGENT_ICONS = {
    "fiscal": "💰",
    "economic": "📈",
    "healthcare": "🏥",
    "social_security": "👴",
    "equity": "⚖️",
    "implementation": "🔧",
    "behavioral": "🧠",
    "legal": "⚖️",
    "judge": "👨‍⚖️",
    "coordinator": "🎯",
}


def get_agent_color(agent_type: str) -> str:
    """Get color for agent type."""
    return AGENT_COLORS.get(agent_type, "#9E9E9E")


def get_agent_icon(agent_type: str) -> str:
    """Get icon for agent type."""
    return AGENT_ICONS.get(agent_type, "🤖")


# =============================================================================
# Confidence Tracker
# =============================================================================

class ConfidenceTracker:
    """Tracks confidence levels over time for visualization.
    
    Collects confidence points from agents and calculates
    aggregate bands for chart rendering.
    
    Example:
        tracker = ConfidenceTracker()
        tracker.add_point("fiscal-1", 0.85, agent_type="fiscal", stage="analyzing")
        tracker.add_point("healthcare-1", 0.78, agent_type="healthcare", stage="analyzing")
        
        df = tracker.get_dataframe()
        bands = tracker.get_confidence_bands()
    """
    
    def __init__(self):
        """Initialize confidence tracker."""
        self._points: List[ConfidencePoint] = []
        self._convergence_moments: List[ConvergenceMoment] = []
        self._latest_by_agent: Dict[str, float] = {}
    
    def add_point(
        self,
        agent_id: str,
        confidence: float,
        agent_type: str = "unknown",
        agent_label: Optional[str] = None,
        stage: str = "analyzing",
        timestamp: Optional[datetime] = None,
        event_type: str = "measurement",
        finding_id: Optional[str] = None,
    ):
        """Add a confidence measurement point.
        
        Args:
            agent_id: Unique agent identifier
            confidence: Confidence value (0.0 - 1.0)
            agent_type: Type of agent (fiscal, healthcare, etc.)
            agent_label: Human-readable agent name
            stage: Current pipeline stage
            timestamp: When measurement was taken (defaults to now)
            event_type: Type of event that triggered measurement
            finding_id: Optional finding ID if from a finding
        """
        point = ConfidencePoint(
            agent_id=agent_id,
            agent_type=agent_type,
            agent_label=agent_label or agent_type.replace("_", " ").title(),
            confidence=confidence,
            timestamp=timestamp or datetime.now(),
            stage=stage,
            event_type=event_type,
            finding_id=finding_id,
        )
        self._points.append(point)
        self._latest_by_agent[agent_id] = confidence
    
    def add_convergence_moment(
        self,
        convergence_score: float,
        previous_score: float,
        description: str,
        stage: str = "debating",
        agents_involved: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
    ):
        """Mark a convergence moment.
        
        Args:
            convergence_score: Current convergence score
            previous_score: Previous convergence score
            description: Description of what caused convergence
            stage: Current pipeline stage
            agents_involved: List of agent IDs involved
            timestamp: When convergence occurred
        """
        moment = ConvergenceMoment(
            timestamp=timestamp or datetime.now(),
            stage=stage,
            convergence_score=convergence_score,
            previous_score=previous_score,
            description=description,
            agents_involved=agents_involved or [],
        )
        self._convergence_moments.append(moment)
    
    def get_dataframe(self) -> "pd.DataFrame":
        """Get confidence data as pandas DataFrame.
        
        Returns:
            DataFrame with columns: agent_id, agent_type, agent_label,
            confidence, timestamp, stage, event_type
        """
        if not self._points:
            return pd.DataFrame()
        
        return pd.DataFrame([p.to_dict() for p in self._points])
    
    def get_confidence_bands(
        self,
        window_size: int = 5,
    ) -> List[ConfidenceBand]:
        """Calculate aggregate confidence bands.
        
        Args:
            window_size: Number of points to aggregate
        
        Returns:
            List of ConfidenceBand objects
        """
        if not self._points:
            return []
        
        bands = []
        
        # Group points by stage and time windows
        df = self.get_dataframe()
        if df.empty:
            return []
        
        df = df.sort_values("timestamp")
        
        # Create bands at each unique timestamp
        for ts in df["timestamp"].unique():
            ts_data = df[df["timestamp"] == ts]
            confidences = ts_data["confidence"].values
            
            if len(confidences) == 0:
                continue
            
            band = ConfidenceBand(
                timestamp=ts,
                stage=ts_data["stage"].iloc[0],
                mean_confidence=float(np.mean(confidences)),
                p10=float(np.percentile(confidences, 10)) if len(confidences) > 1 else float(np.min(confidences)),
                p25=float(np.percentile(confidences, 25)) if len(confidences) > 1 else float(np.min(confidences)),
                p50=float(np.median(confidences)),
                p75=float(np.percentile(confidences, 75)) if len(confidences) > 1 else float(np.max(confidences)),
                p90=float(np.percentile(confidences, 90)) if len(confidences) > 1 else float(np.max(confidences)),
                agent_count=len(confidences),
            )
            bands.append(band)
        
        return bands
    
    def get_latest_confidences(self) -> Dict[str, float]:
        """Get latest confidence value for each agent."""
        return dict(self._latest_by_agent)
    
    def get_convergence_moments(self) -> List[ConvergenceMoment]:
        """Get all convergence moments."""
        return list(self._convergence_moments)
    
    def clear(self):
        """Clear all tracked data."""
        self._points.clear()
        self._convergence_moments.clear()
        self._latest_by_agent.clear()


# =============================================================================
# Session State Management
# =============================================================================

def init_confidence_state():
    """Initialize session state for confidence tracking."""
    if "confidence_tracker" not in st.session_state:
        st.session_state.confidence_tracker = ConfidenceTracker()
    if "confidence_settings" not in st.session_state:
        st.session_state.confidence_settings = {
            "show_bands": True,
            "show_agents": True,
            "show_convergence": True,
            "selected_agents": [],  # Empty = all
            "chart_height": 400,
        }


def get_confidence_tracker() -> ConfidenceTracker:
    """Get the confidence tracker from session state."""
    init_confidence_state()
    return st.session_state.confidence_tracker


# =============================================================================
# Chart Rendering
# =============================================================================

def create_confidence_chart(
    tracker: ConfidenceTracker,
    show_bands: bool = True,
    show_agents: bool = True,
    show_convergence: bool = True,
    selected_agents: Optional[List[str]] = None,
    height: int = 400,
    x_axis: str = "timestamp",  # "timestamp" or "stage"
) -> "go.Figure":
    """Create interactive confidence chart with Plotly.
    
    Args:
        tracker: ConfidenceTracker with data
        show_bands: Whether to show aggregate confidence bands
        show_agents: Whether to show individual agent lines
        show_convergence: Whether to show convergence markers
        selected_agents: List of agent IDs to show (None = all)
        height: Chart height in pixels
        x_axis: What to use for X axis
    
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    df = tracker.get_dataframe()
    
    if df.empty:
        # Empty chart with message
        fig.add_annotation(
            text="No confidence data yet",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666"),
        )
        fig.update_layout(
            height=height,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig
    
    # Sort by timestamp
    df = df.sort_values("timestamp")
    
    # Filter agents if specified
    if selected_agents:
        df = df[df["agent_id"].isin(selected_agents)]
    
    # Calculate time offset for x-axis
    min_time = df["timestamp"].min()
    df["time_offset"] = (df["timestamp"] - min_time).dt.total_seconds()
    
    # Add confidence bands (shaded area)
    if show_bands:
        bands = tracker.get_confidence_bands()
        if bands:
            band_df = pd.DataFrame([b.to_dict() for b in bands])
            band_df["time_offset"] = (band_df["timestamp"] - min_time).dt.total_seconds()
            
            # P10-P90 band (outer)
            fig.add_trace(go.Scatter(
                x=list(band_df["time_offset"]) + list(band_df["time_offset"])[::-1],
                y=list(band_df["p90"]) + list(band_df["p10"])[::-1],
                fill="toself",
                fillcolor="rgba(100, 100, 100, 0.1)",
                line=dict(color="rgba(100, 100, 100, 0)"),
                name="P10-P90 Range",
                showlegend=True,
                hoverinfo="skip",
            ))
            
            # P25-P75 band (inner)
            fig.add_trace(go.Scatter(
                x=list(band_df["time_offset"]) + list(band_df["time_offset"])[::-1],
                y=list(band_df["p75"]) + list(band_df["p25"])[::-1],
                fill="toself",
                fillcolor="rgba(100, 100, 100, 0.2)",
                line=dict(color="rgba(100, 100, 100, 0)"),
                name="P25-P75 Range",
                showlegend=True,
                hoverinfo="skip",
            ))
            
            # Mean line
            fig.add_trace(go.Scatter(
                x=band_df["time_offset"],
                y=band_df["mean"],
                mode="lines",
                line=dict(color="#333", width=2, dash="dash"),
                name="Mean Confidence",
            ))
    
    # Add individual agent lines
    if show_agents:
        for agent_id in df["agent_id"].unique():
            agent_df = df[df["agent_id"] == agent_id]
            agent_type = agent_df["agent_type"].iloc[0]
            agent_label = agent_df["agent_label"].iloc[0]
            color = get_agent_color(agent_type)
            icon = get_agent_icon(agent_type)
            
            fig.add_trace(go.Scatter(
                x=agent_df["time_offset"],
                y=agent_df["confidence"],
                mode="lines+markers",
                name=f"{icon} {agent_label}",
                line=dict(color=color, width=2),
                marker=dict(size=8, color=color),
                hovertemplate=(
                    f"<b>{agent_label}</b><br>"
                    "Confidence: %{y:.1%}<br>"
                    "Time: %{x:.0f}s<br>"
                    "<extra></extra>"
                ),
            ))
    
    # Add convergence markers
    if show_convergence:
        moments = tracker.get_convergence_moments()
        for moment in moments:
            time_offset = (moment.timestamp - min_time).total_seconds()
            
            # Vertical line
            fig.add_vline(
                x=time_offset,
                line=dict(color="#4CAF50", width=2, dash="dot"),
                annotation_text=f"📈 {moment.convergence_score:.0%}",
                annotation_position="top",
            )
    
    # Layout
    fig.update_layout(
        height=height,
        margin=dict(l=50, r=50, t=30, b=50),
        xaxis=dict(
            title="Time (seconds)",
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.3)",
        ),
        yaxis=dict(
            title="Confidence",
            range=[0, 1.05],
            tickformat=".0%",
            showgrid=True,
            gridcolor="rgba(200, 200, 200, 0.3)",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig


def render_confidence_chart(
    tracker: Optional[ConfidenceTracker] = None,
    title: str = "Agent Confidence Over Time",
    show_controls: bool = True,
):
    """Render confidence chart with optional controls.
    
    Args:
        tracker: ConfidenceTracker with data (uses session state if None)
        title: Chart title
        show_controls: Whether to show filter controls
    """
    if not HAS_STREAMLIT:
        logger.warning("Streamlit not available")
        return
    
    init_confidence_state()
    
    if tracker is None:
        tracker = get_confidence_tracker()
    
    settings = st.session_state.confidence_settings
    
    # Title
    st.markdown(f"### 📊 {title}")
    
    # Controls
    if show_controls:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            settings["show_bands"] = st.checkbox(
                "Show Bands",
                value=settings.get("show_bands", True),
                key="conf_show_bands",
            )
        
        with col2:
            settings["show_agents"] = st.checkbox(
                "Show Agents",
                value=settings.get("show_agents", True),
                key="conf_show_agents",
            )
        
        with col3:
            settings["show_convergence"] = st.checkbox(
                "Convergence",
                value=settings.get("show_convergence", True),
                key="conf_show_convergence",
            )
        
        with col4:
            # Agent filter
            df = tracker.get_dataframe()
            if not df.empty:
                agent_options = ["All Agents"] + list(df["agent_id"].unique())
                selected = st.multiselect(
                    "Agents",
                    agent_options,
                    default=["All Agents"],
                    key="conf_agent_filter",
                )
                if "All Agents" in selected or not selected:
                    settings["selected_agents"] = []
                else:
                    settings["selected_agents"] = selected
    
    # Create and render chart
    fig = create_confidence_chart(
        tracker=tracker,
        show_bands=settings.get("show_bands", True),
        show_agents=settings.get("show_agents", True),
        show_convergence=settings.get("show_convergence", True),
        selected_agents=settings.get("selected_agents") or None,
        height=settings.get("chart_height", 400),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show latest confidence values
    latest = tracker.get_latest_confidences()
    if latest:
        st.markdown("#### Latest Confidence Values")
        cols = st.columns(min(len(latest), 4))
        df = tracker.get_dataframe()
        
        for i, (agent_id, conf) in enumerate(latest.items()):
            agent_data = df[df["agent_id"] == agent_id].iloc[-1] if not df.empty else None
            with cols[i % 4]:
                if agent_data is not None:
                    icon = get_agent_icon(agent_data["agent_type"])
                    label = agent_data["agent_label"]
                else:
                    icon = "🤖"
                    label = agent_id
                
                st.metric(
                    label=f"{icon} {label}",
                    value=f"{conf:.0%}",
                )


def render_confidence_summary(tracker: Optional[ConfidenceTracker] = None):
    """Render a compact confidence summary card.
    
    Args:
        tracker: ConfidenceTracker with data
    """
    if not HAS_STREAMLIT:
        return
    
    if tracker is None:
        tracker = get_confidence_tracker()
    
    latest = tracker.get_latest_confidences()
    
    if not latest:
        st.info("No confidence data available")
        return
    
    # Calculate statistics
    values = list(latest.values())
    mean_conf = sum(values) / len(values)
    min_conf = min(values)
    max_conf = max(values)
    spread = max_conf - min_conf
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mean Confidence", f"{mean_conf:.0%}")
    
    with col2:
        st.metric("Range", f"{min_conf:.0%} - {max_conf:.0%}")
    
    with col3:
        st.metric("Spread", f"{spread:.0%}")
    
    with col4:
        st.metric("Agents", len(latest))


# =============================================================================
# Integration with Live Analysis
# =============================================================================

def update_confidence_from_event(event_data: Dict[str, Any]):
    """Update confidence tracker from a stream event.
    
    Call this when receiving events from WebSocket to automatically
    track confidence data.
    
    Args:
        event_data: Raw event data from stream
    """
    init_confidence_state()
    tracker = st.session_state.confidence_tracker
    
    event_type = event_data.get("event_type", "")
    data = event_data.get("data", {})
    timestamp = datetime.fromisoformat(event_data.get("timestamp", datetime.now().isoformat()))
    
    # Extract confidence from various event types
    if event_type == "agent_finding":
        confidence = data.get("confidence")
        if confidence is not None:
            tracker.add_point(
                agent_id=data.get("agent_id", "unknown"),
                confidence=confidence,
                agent_type=data.get("agent_type", "unknown"),
                agent_label=data.get("agent_label"),
                stage=data.get("stage", "analyzing"),
                timestamp=timestamp,
                event_type="finding",
                finding_id=data.get("finding_id"),
            )
    
    elif event_type == "agent_completed":
        confidence = data.get("overall_confidence")
        if confidence is not None:
            tracker.add_point(
                agent_id=data.get("agent_id", "unknown"),
                confidence=confidence,
                agent_type=data.get("agent_type", "unknown"),
                agent_label=data.get("agent_label"),
                stage="completed",
                timestamp=timestamp,
                event_type="completion",
            )
    
    elif event_type == "debate_convergence":
        score = data.get("convergence_score", 0)
        prev_score = data.get("previous_score", 0)
        
        if score != prev_score:
            tracker.add_convergence_moment(
                convergence_score=score,
                previous_score=prev_score or 0,
                description=f"Debate convergence: {score:.0%}",
                stage="debating",
                timestamp=timestamp,
            )


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "ConfidenceTracker",
    "ConfidencePoint",
    "ConfidenceBand",
    "ConvergenceMoment",
    "create_confidence_chart",
    "render_confidence_chart",
    "render_confidence_summary",
    "update_confidence_from_event",
    "get_confidence_tracker",
    "get_agent_color",
    "get_agent_icon",
    "AGENT_COLORS",
    "AGENT_ICONS",
]
