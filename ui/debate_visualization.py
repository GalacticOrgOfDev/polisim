"""Debate Visualization for Live Analysis (Phase 7.2.2).

This module provides Streamlit/Plotly components for visualizing
agent debates in real-time, including:
- Conversation-style debate view
- Critique/rebuttal threading
- Position change indicators
- Disagreement network map
- Debate replay functionality

Example:
    from ui.debate_visualization import (
        render_debate_view,
        render_disagreement_map,
        DebateVisualizationState,
    )
    
    # Render debate conversation
    render_debate_view(debate_rounds)
    
    # Render network graph
    render_disagreement_map(disagreement_data)
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Set
from enum import Enum
import math

try:
    import streamlit as st
    import plotly.graph_objects as go
    import pandas as pd
    import numpy as np
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

class TurnType(Enum):
    """Types of debate turns."""
    OPENING = "opening"
    CRITIQUE = "critique"
    REBUTTAL = "rebuttal"
    CONCESSION = "concession"
    QUESTION = "question"
    CLARIFICATION = "clarification"
    CLOSING = "closing"


@dataclass
class DebateTurn:
    """Single turn in a debate."""
    
    turn_id: str
    round_number: int
    agent_id: str
    agent_type: str
    agent_label: str
    agent_icon: str
    turn_type: TurnType
    content: str
    target_agent: Optional[str] = None
    target_turn_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    confidence_before: Optional[float] = None
    confidence_after: Optional[float] = None
    position_changed: bool = False
    severity: str = "normal"  # minor, normal, major, critical
    
    def get_turn_icon(self) -> str:
        """Get icon for turn type."""
        icons = {
            TurnType.OPENING: "🎤",
            TurnType.CRITIQUE: "🔍",
            TurnType.REBUTTAL: "💬",
            TurnType.CONCESSION: "🤝",
            TurnType.QUESTION: "❓",
            TurnType.CLARIFICATION: "💡",
            TurnType.CLOSING: "✅",
        }
        return icons.get(self.turn_type, "💬")
    
    def get_color(self) -> str:
        """Get color based on turn type and severity."""
        if self.severity == "critical":
            return "#F44336"
        if self.severity == "major":
            return "#FF9800"
        
        colors = {
            TurnType.OPENING: "#4CAF50",
            TurnType.CRITIQUE: "#E91E63",
            TurnType.REBUTTAL: "#2196F3",
            TurnType.CONCESSION: "#8BC34A",
            TurnType.QUESTION: "#9C27B0",
            TurnType.CLARIFICATION: "#00BCD4",
            TurnType.CLOSING: "#4CAF50",
        }
        return colors.get(self.turn_type, "#9E9E9E")


@dataclass
class DebateRoundData:
    """Data for a complete debate round."""
    
    round_number: int
    topic: str
    turns: List[DebateTurn] = field(default_factory=list)
    convergence_start: float = 0.0
    convergence_end: float = 0.0
    participants: List[str] = field(default_factory=list)
    key_arguments: List[str] = field(default_factory=list)
    position_changes: int = 0
    
    @property
    def convergence_improvement(self) -> float:
        """Calculate convergence improvement."""
        return self.convergence_end - self.convergence_start


@dataclass
class Disagreement:
    """Represents a disagreement between agents."""
    
    agent_a: str
    agent_b: str
    topic: str
    magnitude: float  # 0.0 - 1.0, higher = more disagreement
    reason: str
    category: str
    resolved: bool = False
    resolution_round: Optional[int] = None


@dataclass
class AgentPosition:
    """Tracks an agent's position on a topic."""
    
    agent_id: str
    topic: str
    position: str  # Brief position statement
    confidence: float
    supporting_evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# Agent Colors and Icons (imported from confidence_visualization)
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
}


def get_agent_color(agent_type: str) -> str:
    """Get color for agent type."""
    return AGENT_COLORS.get(agent_type, "#9E9E9E")


def get_agent_icon(agent_type: str) -> str:
    """Get icon for agent type."""
    return AGENT_ICONS.get(agent_type, "🤖")


# =============================================================================
# Session State Management
# =============================================================================

def init_debate_state():
    """Initialize session state for debate visualization."""
    if "debate_viz" not in st.session_state:
        st.session_state.debate_viz = {
            "rounds": [],
            "disagreements": [],
            "positions": {},  # agent_id -> latest position
            "selected_round": None,
            "replay_mode": False,
            "replay_index": 0,
            "show_threading": True,
            "highlight_changes": True,
        }


def get_debate_state() -> Dict[str, Any]:
    """Get debate visualization state."""
    init_debate_state()
    return st.session_state.debate_viz


# =============================================================================
# Debate View Rendering
# =============================================================================

def render_debate_turn(turn: DebateTurn, show_threading: bool = True):
    """Render a single debate turn as a styled message.
    
    Args:
        turn: DebateTurn to render
        show_threading: Whether to show reply threading
    """
    if not HAS_STREAMLIT:
        return
    
    # Determine alignment (left for critiques, right for rebuttals)
    is_rebuttal = turn.turn_type in [TurnType.REBUTTAL, TurnType.CLARIFICATION]
    align = "right" if is_rebuttal else "left"
    margin = "margin-left: 40px;" if is_rebuttal else "margin-right: 40px;"
    
    # Build content
    turn_icon = turn.get_turn_icon()
    color = turn.get_color()
    timestamp = turn.timestamp.strftime("%H:%M:%S")
    
    # Position change indicator
    change_indicator = ""
    if turn.position_changed:
        if turn.confidence_before and turn.confidence_after:
            change = turn.confidence_after - turn.confidence_before
            change_icon = "📈" if change > 0 else "📉"
            change_indicator = f' <span style="color: {"#4CAF50" if change > 0 else "#F44336"};">{change_icon} {change:+.0%}</span>'
    
    # Target agent indicator
    target_str = ""
    if turn.target_agent and show_threading:
        target_str = f'<span style="color: #666; font-size: 12px;">→ {turn.target_agent}</span><br>'
    
    st.markdown(f"""
    <div style="
        {margin}
        padding: 12px 16px;
        margin: 8px 0;
        border-radius: 12px;
        background: linear-gradient(135deg, {color}15, {color}05);
        border-left: 4px solid {color};
        text-align: {align};
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <span style="font-weight: bold; color: {color};">
                {turn.agent_icon} {turn.agent_label}
            </span>
            <span style="font-size: 11px; color: #888;">
                {turn_icon} {turn.turn_type.value.title()} • {timestamp}{change_indicator}
            </span>
        </div>
        {target_str}
        <div style="color: #333; line-height: 1.5;">
            {turn.content}
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_debate_round(
    round_data: DebateRoundData,
    expanded: bool = True,
    show_threading: bool = True,
):
    """Render a complete debate round.
    
    Args:
        round_data: DebateRoundData to render
        expanded: Whether to expand the round by default
        show_threading: Whether to show reply threading
    """
    if not HAS_STREAMLIT:
        return
    
    # Convergence badge
    conv_color = "#4CAF50" if round_data.convergence_end >= 0.8 else "#FF9800"
    conv_improvement = round_data.convergence_improvement
    conv_arrow = "↑" if conv_improvement > 0 else "↓" if conv_improvement < 0 else "→"
    
    header = f"""
    **Round {round_data.round_number}**: {round_data.topic}
    <span style="
        background: {conv_color}20;
        color: {conv_color};
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
    ">
        Convergence: {round_data.convergence_end:.0%} {conv_arrow}
    </span>
    """
    
    with st.expander(header, expanded=expanded):
        # Round stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Turns", len(round_data.turns))
        with col2:
            st.metric("Position Changes", round_data.position_changes)
        with col3:
            st.metric(
                "Convergence",
                f"{round_data.convergence_end:.0%}",
                delta=f"{conv_improvement:+.0%}",
            )
        
        st.divider()
        
        # Render turns
        for turn in round_data.turns:
            render_debate_turn(turn, show_threading)
        
        # Key arguments summary
        if round_data.key_arguments:
            st.markdown("**Key Arguments:**")
            for arg in round_data.key_arguments[:3]:
                st.markdown(f"- {arg}")


def render_debate_view(
    rounds: Optional[List[DebateRoundData]] = None,
    show_controls: bool = True,
):
    """Render the complete debate view.
    
    Args:
        rounds: List of debate rounds (uses session state if None)
        show_controls: Whether to show view controls
    """
    if not HAS_STREAMLIT:
        return
    
    init_debate_state()
    state = get_debate_state()
    
    if rounds is None:
        rounds = state.get("rounds", [])
    
    st.markdown("### 💬 Debate View")
    
    if not rounds:
        st.info("No debates to display. Debates occur when agents disagree on findings.")
        return
    
    # Controls
    if show_controls:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            state["show_threading"] = st.checkbox(
                "Show Threading",
                value=state.get("show_threading", True),
                key="debate_threading",
            )
        
        with col2:
            state["highlight_changes"] = st.checkbox(
                "Highlight Changes",
                value=state.get("highlight_changes", True),
                key="debate_highlight",
            )
        
        with col3:
            # Replay controls
            if st.button("🔄 Replay Debate", key="debate_replay"):
                state["replay_mode"] = True
                state["replay_index"] = 0
    
    st.divider()
    
    # Summary stats
    total_turns = sum(len(r.turns) for r in rounds)
    total_changes = sum(r.position_changes for r in rounds)
    final_conv = rounds[-1].convergence_end if rounds else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Rounds", len(rounds))
    with col2:
        st.metric("Total Turns", total_turns)
    with col3:
        st.metric("Position Changes", total_changes)
    with col4:
        st.metric("Final Convergence", f"{final_conv:.0%}")
    
    st.divider()
    
    # Render rounds
    for i, round_data in enumerate(rounds):
        render_debate_round(
            round_data,
            expanded=(i == len(rounds) - 1),  # Expand last round
            show_threading=state.get("show_threading", True),
        )


# =============================================================================
# Disagreement Map (Network Graph)
# =============================================================================

def create_disagreement_map(
    disagreements: List[Disagreement],
    agent_positions: Optional[Dict[str, AgentPosition]] = None,
    height: int = 500,
) -> "go.Figure":
    """Create a network graph showing agent disagreements.
    
    Args:
        disagreements: List of disagreements between agents
        agent_positions: Optional dict of agent positions
        height: Chart height
    
    Returns:
        Plotly Figure with network graph
    """
    fig = go.Figure()
    
    if not disagreements:
        fig.add_annotation(
            text="No disagreements to display",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color="#666"),
        )
        fig.update_layout(height=height)
        return fig
    
    # Extract unique agents
    agents = set()
    for d in disagreements:
        agents.add(d.agent_a)
        agents.add(d.agent_b)
    agents = list(agents)
    
    # Create node positions (circular layout)
    n = len(agents)
    node_x = []
    node_y = []
    for i in range(n):
        angle = 2 * math.pi * i / n
        node_x.append(math.cos(angle))
        node_y.append(math.sin(angle))
    
    agent_to_idx = {agent: i for i, agent in enumerate(agents)}
    
    # Create edges
    edge_x = []
    edge_y = []
    edge_colors = []
    edge_widths = []
    edge_texts = []
    
    for d in disagreements:
        idx_a = agent_to_idx[d.agent_a]
        idx_b = agent_to_idx[d.agent_b]
        
        # Add line
        edge_x.extend([node_x[idx_a], node_x[idx_b], None])
        edge_y.extend([node_y[idx_a], node_y[idx_b], None])
        
        # Color by topic category
        category_colors = {
            "revenue": "#4CAF50",
            "spending": "#2196F3",
            "healthcare": "#9C27B0",
            "social_security": "#FF9800",
            "other": "#9E9E9E",
        }
        color = category_colors.get(d.category, "#9E9E9E")
        if d.resolved:
            color = "#BDBDBD"  # Gray for resolved
        
        edge_colors.append(color)
        edge_widths.append(d.magnitude * 8 + 2)  # Width based on magnitude
        edge_texts.append(f"{d.topic}: {d.reason}")
    
    # Add edge traces (one per edge for different colors)
    for i, d in enumerate(disagreements):
        idx_a = agent_to_idx[d.agent_a]
        idx_b = agent_to_idx[d.agent_b]
        
        category_colors = {
            "revenue": "#4CAF50",
            "spending": "#2196F3",
            "healthcare": "#9C27B0",
            "social_security": "#FF9800",
            "other": "#9E9E9E",
        }
        color = category_colors.get(d.category, "#9E9E9E")
        opacity = 0.3 if d.resolved else 0.8
        
        fig.add_trace(go.Scatter(
            x=[node_x[idx_a], node_x[idx_b]],
            y=[node_y[idx_a], node_y[idx_b]],
            mode="lines",
            line=dict(
                width=d.magnitude * 8 + 2,
                color=color,
            ),
            opacity=opacity,
            hoverinfo="text",
            hovertext=f"<b>{d.topic}</b><br>{d.reason}<br>Magnitude: {d.magnitude:.0%}",
            showlegend=False,
        ))
    
    # Add nodes
    node_colors = []
    node_texts = []
    for agent in agents:
        agent_type = agent.split("-")[0] if "-" in agent else agent
        node_colors.append(get_agent_color(agent_type))
        icon = get_agent_icon(agent_type)
        node_texts.append(f"{icon} {agent_type.title()}")
    
    fig.add_trace(go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=40,
            color=node_colors,
            line=dict(width=2, color="white"),
        ),
        text=node_texts,
        textposition="bottom center",
        hoverinfo="text",
        hovertext=[f"<b>{agent}</b>" for agent in agents],
    ))
    
    # Layout
    fig.update_layout(
        height=height,
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=40, b=40),
    )
    
    return fig


def render_disagreement_map(
    disagreements: Optional[List[Disagreement]] = None,
    show_legend: bool = True,
):
    """Render the disagreement network map.
    
    Args:
        disagreements: List of disagreements (uses session state if None)
        show_legend: Whether to show category legend
    """
    if not HAS_STREAMLIT:
        return
    
    init_debate_state()
    state = get_debate_state()
    
    if disagreements is None:
        disagreements = state.get("disagreements", [])
    
    st.markdown("### 🗺️ Disagreement Map")
    
    if not disagreements:
        st.info("No disagreements to visualize. The map will appear when agents have differing views.")
        return
    
    # Legend
    if show_legend:
        st.markdown("""
        <div style="display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 16px;">
            <span>📏 Line thickness = disagreement magnitude</span>
            <span style="color: #4CAF50;">● Revenue</span>
            <span style="color: #2196F3;">● Spending</span>
            <span style="color: #9C27B0;">● Healthcare</span>
            <span style="color: #FF9800;">● Social Security</span>
            <span style="color: #BDBDBD;">● Resolved</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Create and render chart
    fig = create_disagreement_map(disagreements)
    st.plotly_chart(fig, use_container_width=True)
    
    # Disagreement list
    unresolved = [d for d in disagreements if not d.resolved]
    resolved = [d for d in disagreements if d.resolved]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"**Unresolved ({len(unresolved)})**")
        for d in unresolved[:5]:
            st.markdown(f"""
            - **{d.topic}** ({d.magnitude:.0%})  
              {d.agent_a} ↔ {d.agent_b}: {d.reason[:50]}...
            """)
    
    with col2:
        st.markdown(f"**Resolved ({len(resolved)})**")
        for d in resolved[:5]:
            st.markdown(f"""
            - ~~{d.topic}~~ (Round {d.resolution_round})
            """)


# =============================================================================
# Debate Timeline Visualization
# =============================================================================

def create_debate_timeline(
    rounds: List[DebateRoundData],
    height: int = 200,
) -> "go.Figure":
    """Create a timeline showing debate progression.
    
    Args:
        rounds: List of debate rounds
        height: Chart height
    
    Returns:
        Plotly Figure with timeline
    """
    fig = go.Figure()
    
    if not rounds:
        return fig
    
    # Extract data
    round_nums = [r.round_number for r in rounds]
    conv_start = [r.convergence_start for r in rounds]
    conv_end = [r.convergence_end for r in rounds]
    
    # Convergence area
    fig.add_trace(go.Scatter(
        x=round_nums + round_nums[::-1],
        y=conv_start + conv_end[::-1],
        fill="toself",
        fillcolor="rgba(33, 150, 243, 0.2)",
        line=dict(color="rgba(0,0,0,0)"),
        name="Convergence Range",
    ))
    
    # End convergence line
    fig.add_trace(go.Scatter(
        x=round_nums,
        y=conv_end,
        mode="lines+markers",
        line=dict(color="#4CAF50", width=3),
        marker=dict(size=10),
        name="Final Convergence",
        hovertemplate="Round %{x}<br>Convergence: %{y:.0%}<extra></extra>",
    ))
    
    # Threshold line
    fig.add_hline(
        y=0.8,
        line=dict(color="#FF9800", dash="dash"),
        annotation_text="Consensus Threshold",
    )
    
    # Layout
    fig.update_layout(
        height=height,
        margin=dict(l=50, r=50, t=30, b=50),
        xaxis=dict(title="Debate Round", dtick=1),
        yaxis=dict(title="Convergence", range=[0, 1.05], tickformat=".0%"),
        legend=dict(orientation="h", y=1.1),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    
    return fig


def render_debate_timeline(rounds: Optional[List[DebateRoundData]] = None):
    """Render the debate timeline.
    
    Args:
        rounds: List of debate rounds
    """
    if not HAS_STREAMLIT:
        return
    
    init_debate_state()
    state = get_debate_state()
    
    if rounds is None:
        rounds = state.get("rounds", [])
    
    if not rounds:
        return
    
    st.markdown("### 📈 Debate Progression")
    fig = create_debate_timeline(rounds)
    st.plotly_chart(fig, use_container_width=True)


# =============================================================================
# Integration with Live Analysis
# =============================================================================

def process_debate_event(event_data: Dict[str, Any]):
    """Process debate event and update visualization state.
    
    Args:
        event_data: Raw event data from stream
    """
    init_debate_state()
    state = get_debate_state()
    
    event_type = event_data.get("event_type", "")
    data = event_data.get("data", {})
    timestamp = datetime.fromisoformat(
        event_data.get("timestamp", datetime.now().isoformat())
    )
    
    if event_type == "debate_started":
        # Create new round
        round_data = DebateRoundData(
            round_number=data.get("round_number", len(state["rounds"]) + 1),
            topic=data.get("topic", "Unknown topic"),
            participants=data.get("participants", []),
            convergence_start=data.get("initial_convergence", 0.0),
        )
        state["rounds"].append(round_data)
    
    elif event_type == "debate_turn":
        # Add turn to current round
        if state["rounds"]:
            current_round = state["rounds"][-1]
            
            turn = DebateTurn(
                turn_id=f"turn-{len(current_round.turns)}",
                round_number=current_round.round_number,
                agent_id=data.get("agent_id", "unknown"),
                agent_type=data.get("agent_type", "unknown"),
                agent_label=data.get("agent_label", "Agent"),
                agent_icon=data.get("agent_icon", "🤖"),
                turn_type=TurnType(data.get("turn_type", "statement")),
                content=data.get("content", ""),
                target_agent=data.get("target_agent"),
                timestamp=timestamp,
                position_changed=data.get("position_changed", False),
            )
            current_round.turns.append(turn)
            
            if turn.position_changed:
                current_round.position_changes += 1
    
    elif event_type == "debate_convergence":
        # Update convergence
        if state["rounds"]:
            current_round = state["rounds"][-1]
            current_round.convergence_end = data.get("convergence_score", 0.0)


def add_disagreement(
    agent_a: str,
    agent_b: str,
    topic: str,
    magnitude: float,
    reason: str,
    category: str = "other",
):
    """Add a disagreement to the visualization state.
    
    Args:
        agent_a: First agent ID
        agent_b: Second agent ID
        topic: Topic of disagreement
        magnitude: How severe (0.0 - 1.0)
        reason: Brief explanation
        category: Category (revenue, spending, healthcare, etc.)
    """
    init_debate_state()
    state = get_debate_state()
    
    disagreement = Disagreement(
        agent_a=agent_a,
        agent_b=agent_b,
        topic=topic,
        magnitude=magnitude,
        reason=reason,
        category=category,
    )
    state["disagreements"].append(disagreement)


def resolve_disagreement(agent_a: str, agent_b: str, topic: str, round_number: int):
    """Mark a disagreement as resolved.
    
    Args:
        agent_a: First agent ID
        agent_b: Second agent ID
        topic: Topic that was resolved
        round_number: Round in which it was resolved
    """
    init_debate_state()
    state = get_debate_state()
    
    for d in state["disagreements"]:
        if (
            (d.agent_a == agent_a and d.agent_b == agent_b) or
            (d.agent_a == agent_b and d.agent_b == agent_a)
        ) and d.topic == topic:
            d.resolved = True
            d.resolution_round = round_number
            break


# =============================================================================
# Demo Functions
# =============================================================================

def create_demo_debate_data() -> Tuple[List[DebateRoundData], List[Disagreement]]:
    """Create demo debate data for testing.
    
    Returns:
        Tuple of (rounds, disagreements)
    """
    # Create demo turns
    turns_r1 = [
        DebateTurn(
            turn_id="t1",
            round_number=1,
            agent_id="fiscal-1",
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            agent_icon="💰",
            turn_type=TurnType.OPENING,
            content="Based on CBO scoring methodology, this bill will increase revenue by approximately $150B over 10 years through the proposed tax adjustments.",
        ),
        DebateTurn(
            turn_id="t2",
            round_number=1,
            agent_id="economic-1",
            agent_type="economic",
            agent_label="Economist",
            agent_icon="📈",
            turn_type=TurnType.CRITIQUE,
            content="I disagree with the revenue estimate. The behavioral response to higher taxes will reduce the effective revenue gain. My estimate is closer to $100B.",
            target_agent="Fiscal Analyst",
        ),
        DebateTurn(
            turn_id="t3",
            round_number=1,
            agent_id="fiscal-1",
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            agent_icon="💰",
            turn_type=TurnType.REBUTTAL,
            content="I acknowledge the behavioral effects but believe they're already factored into CBO's elasticity assumptions. However, I'll revise my estimate to $135B to account for additional uncertainty.",
            target_agent="Economist",
            position_changed=True,
            confidence_before=0.85,
            confidence_after=0.78,
        ),
    ]
    
    rounds = [
        DebateRoundData(
            round_number=1,
            topic="Revenue Impact Estimation",
            turns=turns_r1,
            convergence_start=0.45,
            convergence_end=0.72,
            participants=["fiscal-1", "economic-1", "healthcare-1"],
            key_arguments=["CBO methodology supports $150B", "Behavioral effects reduce to $100B", "Compromise at $135B"],
            position_changes=1,
        ),
    ]
    
    disagreements = [
        Disagreement(
            agent_a="fiscal-1",
            agent_b="economic-1",
            topic="Revenue Impact",
            magnitude=0.6,
            reason="Different elasticity assumptions",
            category="revenue",
            resolved=True,
            resolution_round=1,
        ),
        Disagreement(
            agent_a="healthcare-1",
            agent_b="economic-1",
            topic="Healthcare Cost Savings",
            magnitude=0.4,
            reason="Disagreement on implementation timeline",
            category="healthcare",
        ),
    ]
    
    return rounds, disagreements


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "DebateTurn",
    "DebateRoundData",
    "Disagreement",
    "AgentPosition",
    "TurnType",
    "render_debate_view",
    "render_debate_turn",
    "render_debate_round",
    "render_disagreement_map",
    "render_debate_timeline",
    "create_disagreement_map",
    "create_debate_timeline",
    "process_debate_event",
    "add_disagreement",
    "resolve_disagreement",
    "create_demo_debate_data",
    "get_debate_state",
    "init_debate_state",
]
