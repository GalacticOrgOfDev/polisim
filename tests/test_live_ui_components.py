"""Tests for Phase 7.2.2 Live UI Components.

Tests cover:
- LiveAnalysisPanel event processing
- ConfidenceTracker data management
- DebateVisualization data structures
- Event filtering and transformation
- Session state management
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import UI components
from ui.live_analysis_panel import (
    StreamEventDisplay,
    AgentActivityState,
    AnalysisProgressState,
    EventDisplayType,
    process_stream_event,
    filter_events,
    _build_event_content,
)
from ui.confidence_visualization import (
    ConfidenceTracker,
    ConfidencePoint,
    ConfidenceBand,
    ConvergenceMoment,
    get_agent_color,
    get_agent_icon,
    AGENT_COLORS,
    AGENT_ICONS,
)
from ui.debate_visualization import (
    DebateTurn,
    DebateRoundData,
    Disagreement,
    TurnType,
    create_demo_debate_data,
)


# =============================================================================
# LiveAnalysisPanel Tests
# =============================================================================

class TestStreamEventDisplay:
    """Tests for StreamEventDisplay dataclass."""
    
    def test_event_display_creation(self):
        """Test creating a stream event display."""
        event = StreamEventDisplay(
            event_id="test-1",
            event_type="agent_started",
            timestamp=datetime.now(),
            agent_id="fiscal-1",
            agent_icon="💰",
            agent_label="Fiscal Analyst",
            content="Agent started analysis",
        )
        
        assert event.event_id == "test-1"
        assert event.event_type == "agent_started"
        assert event.agent_id == "fiscal-1"
        assert event.agent_icon == "💰"
    
    def test_event_color_by_type(self):
        """Test that events get correct colors by type."""
        event_types = [
            ("pipeline_started", "#4CAF50"),
            ("stage_changed", "#2196F3"),
            ("agent_started", "#9C27B0"),
            ("agent_finding", "#FF9800"),
            ("error", "#F44336"),
        ]
        
        for event_type, expected_color in event_types:
            event = StreamEventDisplay(
                event_id="test",
                event_type=event_type,
                timestamp=datetime.now(),
            )
            assert event.get_color() == expected_color
    
    def test_critical_importance_overrides_color(self):
        """Test that critical importance returns red regardless of type."""
        event = StreamEventDisplay(
            event_id="test",
            event_type="agent_started",  # Would normally be purple
            timestamp=datetime.now(),
            importance="critical",
        )
        assert event.get_color() == "#F44336"  # Red


class TestAgentActivityState:
    """Tests for AgentActivityState dataclass."""
    
    def test_agent_state_creation(self):
        """Test creating agent activity state."""
        state = AgentActivityState(
            agent_id="fiscal-1",
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            agent_icon="💰",
        )
        
        assert state.status == "idle"
        assert state.findings_count == 0
        assert state.confidence is None
    
    def test_agent_state_update(self):
        """Test updating agent state."""
        state = AgentActivityState(
            agent_id="fiscal-1",
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            agent_icon="💰",
        )
        
        state.status = "analyzing"
        state.findings_count = 3
        state.confidence = 0.85
        
        assert state.status == "analyzing"
        assert state.findings_count == 3
        assert state.confidence == 0.85


class TestAnalysisProgressState:
    """Tests for AnalysisProgressState dataclass."""
    
    def test_progress_stage_labels(self):
        """Test stage label generation."""
        progress = AnalysisProgressState(stage="analyzing")
        assert "Analyzing" in progress.get_stage_label()
        
        progress.stage = "debating"
        assert "Debating" in progress.get_stage_label()
        
        progress.stage = "complete"
        assert "Complete" in progress.get_stage_label()
    
    def test_overall_progress_calculation(self):
        """Test overall progress calculation."""
        progress = AnalysisProgressState(stage="initialized")
        assert progress.get_overall_progress() == 0.0
        
        progress.stage = "analyzing"
        assert 0.3 <= progress.get_overall_progress() <= 0.5
        
        progress.stage = "complete"
        assert progress.get_overall_progress() == 1.0


class TestEventProcessing:
    """Tests for event processing functions."""
    
    def test_process_pipeline_started_event(self):
        """Test processing pipeline_started event."""
        event_data = {
            "event_id": "e1",
            "event_type": "pipeline_started",
            "data": {"bill_id": "HR-001"},
            "timestamp": datetime.now().isoformat(),
        }
        
        event = process_stream_event(event_data)
        
        assert event.event_type == "pipeline_started"
        assert "HR-001" in event.content
        assert event.display_type == EventDisplayType.PROGRESS
    
    def test_process_agent_finding_event(self):
        """Test processing agent_finding event."""
        event_data = {
            "event_id": "e2",
            "event_type": "agent_finding",
            "data": {
                "agent_id": "fiscal-1",
                "agent_label": "Fiscal Analyst",
                "agent_icon": "💰",
                "category": "revenue",
                "description": "Revenue increase of $150B",
                "confidence": 0.85,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        event = process_stream_event(event_data)
        
        assert event.event_type == "agent_finding"
        assert event.display_type == EventDisplayType.FINDINGS
        assert "REVENUE" in event.content
        assert event.importance == "normal"
    
    def test_process_debate_turn_event(self):
        """Test processing debate_turn event."""
        event_data = {
            "event_id": "e3",
            "event_type": "debate_turn",
            "data": {
                "agent_id": "fiscal-1",
                "turn_type": "critique",
                "content": "I disagree with the methodology",
                "target_agent": "economic-1",
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        event = process_stream_event(event_data)
        
        assert event.event_type == "debate_turn"
        assert event.display_type == EventDisplayType.DEBATES
        assert "CRITIQUE" in event.content
    
    def test_process_consensus_reached_event(self):
        """Test processing consensus_reached event."""
        event_data = {
            "event_id": "e4",
            "event_type": "consensus_reached",
            "data": {
                "consensus_level": "strong_consensus",
                "agreed_findings_count": 12,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        event = process_stream_event(event_data)
        
        assert event.event_type == "consensus_reached"
        assert event.importance == "high"
        assert "🎉" in event.content


class TestEventFiltering:
    """Tests for event filtering."""
    
    def test_filter_by_type(self):
        """Test filtering events by type."""
        events = [
            StreamEventDisplay(
                event_id="e1",
                event_type="agent_finding",
                timestamp=datetime.now(),
                display_type=EventDisplayType.FINDINGS,
            ),
            StreamEventDisplay(
                event_id="e2",
                event_type="agent_thinking",
                timestamp=datetime.now(),
                display_type=EventDisplayType.THOUGHTS,
            ),
            StreamEventDisplay(
                event_id="e3",
                event_type="debate_turn",
                timestamp=datetime.now(),
                display_type=EventDisplayType.DEBATES,
            ),
        ]
        
        findings_only = filter_events(events, EventDisplayType.FINDINGS, None, "")
        assert len(findings_only) == 1
        assert findings_only[0].event_id == "e1"
        
        debates_only = filter_events(events, EventDisplayType.DEBATES, None, "")
        assert len(debates_only) == 1
        assert debates_only[0].event_id == "e3"
    
    def test_filter_by_agent(self):
        """Test filtering events by agent."""
        events = [
            StreamEventDisplay(
                event_id="e1",
                event_type="agent_finding",
                timestamp=datetime.now(),
                agent_id="fiscal-1",
            ),
            StreamEventDisplay(
                event_id="e2",
                event_type="agent_finding",
                timestamp=datetime.now(),
                agent_id="healthcare-1",
            ),
        ]
        
        fiscal_only = filter_events(events, EventDisplayType.ALL, "fiscal-1", "")
        assert len(fiscal_only) == 1
        assert fiscal_only[0].agent_id == "fiscal-1"
    
    def test_filter_by_search_query(self):
        """Test filtering events by search query."""
        events = [
            StreamEventDisplay(
                event_id="e1",
                event_type="agent_finding",
                timestamp=datetime.now(),
                content="Revenue increase expected",
            ),
            StreamEventDisplay(
                event_id="e2",
                event_type="agent_finding",
                timestamp=datetime.now(),
                content="Healthcare costs rising",
            ),
        ]
        
        revenue_events = filter_events(events, EventDisplayType.ALL, None, "revenue")
        assert len(revenue_events) == 1
        assert "Revenue" in revenue_events[0].content


# =============================================================================
# ConfidenceTracker Tests
# =============================================================================

class TestConfidenceTracker:
    """Tests for ConfidenceTracker class."""
    
    def test_tracker_initialization(self):
        """Test tracker initializes empty."""
        tracker = ConfidenceTracker()
        
        assert tracker.get_dataframe().empty
        assert len(tracker.get_latest_confidences()) == 0
        assert len(tracker.get_convergence_moments()) == 0
    
    def test_add_confidence_point(self):
        """Test adding confidence points."""
        tracker = ConfidenceTracker()
        
        tracker.add_point(
            agent_id="fiscal-1",
            confidence=0.85,
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            stage="analyzing",
        )
        
        df = tracker.get_dataframe()
        assert len(df) == 1
        assert df.iloc[0]["agent_id"] == "fiscal-1"
        assert df.iloc[0]["confidence"] == 0.85
    
    def test_latest_confidences(self):
        """Test getting latest confidence values."""
        tracker = ConfidenceTracker()
        
        # Add multiple points for same agent
        tracker.add_point("fiscal-1", 0.7, agent_type="fiscal")
        tracker.add_point("fiscal-1", 0.8, agent_type="fiscal")
        tracker.add_point("fiscal-1", 0.85, agent_type="fiscal")
        
        latest = tracker.get_latest_confidences()
        assert latest["fiscal-1"] == 0.85
    
    def test_confidence_bands_calculation(self):
        """Test confidence band calculation."""
        tracker = ConfidenceTracker()
        
        # Add points for multiple agents at same time
        now = datetime.now()
        for agent, conf in [("a", 0.7), ("b", 0.8), ("c", 0.9)]:
            tracker.add_point(agent, conf, timestamp=now)
        
        bands = tracker.get_confidence_bands()
        assert len(bands) == 1
        
        band = bands[0]
        assert band.agent_count == 3
        assert 0.75 <= band.mean_confidence <= 0.85  # Mean of 0.7, 0.8, 0.9
    
    def test_convergence_moments(self):
        """Test convergence moment tracking."""
        tracker = ConfidenceTracker()
        
        tracker.add_convergence_moment(
            convergence_score=0.85,
            previous_score=0.65,
            description="Agents reached consensus on revenue",
        )
        
        moments = tracker.get_convergence_moments()
        assert len(moments) == 1
        assert abs(moments[0].improvement - 0.2) < 0.001  # Allow floating point tolerance
    
    def test_tracker_clear(self):
        """Test clearing tracker data."""
        tracker = ConfidenceTracker()
        
        tracker.add_point("fiscal-1", 0.85)
        tracker.add_convergence_moment(0.8, 0.6, "Test")
        
        tracker.clear()
        
        assert tracker.get_dataframe().empty
        assert len(tracker.get_convergence_moments()) == 0


class TestAgentColorIcons:
    """Tests for agent color and icon mappings."""
    
    def test_all_agent_types_have_colors(self):
        """Test that all defined agent types have colors."""
        agent_types = [
            "fiscal", "economic", "healthcare", "social_security",
            "equity", "implementation", "behavioral", "legal", "judge",
        ]
        
        for agent_type in agent_types:
            color = get_agent_color(agent_type)
            assert color.startswith("#")
            assert len(color) == 7  # #RRGGBB format
    
    def test_all_agent_types_have_icons(self):
        """Test that all defined agent types have icons."""
        agent_types = [
            "fiscal", "economic", "healthcare", "social_security",
            "equity", "implementation", "behavioral", "legal", "judge",
        ]
        
        for agent_type in agent_types:
            icon = get_agent_icon(agent_type)
            assert len(icon) > 0
    
    def test_unknown_agent_type_fallback(self):
        """Test fallback for unknown agent types."""
        assert get_agent_color("unknown") == "#9E9E9E"
        assert get_agent_icon("unknown") == "🤖"


# =============================================================================
# DebateVisualization Tests
# =============================================================================

class TestDebateTurn:
    """Tests for DebateTurn dataclass."""
    
    def test_debate_turn_creation(self):
        """Test creating a debate turn."""
        turn = DebateTurn(
            turn_id="t1",
            round_number=1,
            agent_id="fiscal-1",
            agent_type="fiscal",
            agent_label="Fiscal Analyst",
            agent_icon="💰",
            turn_type=TurnType.CRITIQUE,
            content="I disagree with this estimate.",
            target_agent="economic-1",
        )
        
        assert turn.turn_id == "t1"
        assert turn.turn_type == TurnType.CRITIQUE
        assert turn.target_agent == "economic-1"
    
    def test_turn_icons(self):
        """Test that turn types have icons."""
        turn_types = [
            TurnType.OPENING,
            TurnType.CRITIQUE,
            TurnType.REBUTTAL,
            TurnType.CONCESSION,
        ]
        
        for tt in turn_types:
            turn = DebateTurn(
                turn_id="t1",
                round_number=1,
                agent_id="a",
                agent_type="fiscal",
                agent_label="A",
                agent_icon="💰",
                turn_type=tt,
                content="Test",
            )
            icon = turn.get_turn_icon()
            assert len(icon) > 0
    
    def test_turn_colors(self):
        """Test that turn types have colors."""
        for tt in TurnType:
            turn = DebateTurn(
                turn_id="t1",
                round_number=1,
                agent_id="a",
                agent_type="fiscal",
                agent_label="A",
                agent_icon="💰",
                turn_type=tt,
                content="Test",
            )
            color = turn.get_color()
            assert color.startswith("#")


class TestDebateRoundData:
    """Tests for DebateRoundData dataclass."""
    
    def test_round_data_creation(self):
        """Test creating debate round data."""
        round_data = DebateRoundData(
            round_number=1,
            topic="Revenue estimation methodology",
            convergence_start=0.5,
            convergence_end=0.75,
            position_changes=2,
        )
        
        assert round_data.round_number == 1
        assert round_data.convergence_improvement == 0.25
    
    def test_convergence_improvement(self):
        """Test convergence improvement calculation."""
        round_data = DebateRoundData(
            round_number=1,
            topic="Test",
            convergence_start=0.4,
            convergence_end=0.8,
        )
        
        assert round_data.convergence_improvement == 0.4


class TestDisagreement:
    """Tests for Disagreement dataclass."""
    
    def test_disagreement_creation(self):
        """Test creating a disagreement."""
        disagreement = Disagreement(
            agent_a="fiscal-1",
            agent_b="economic-1",
            topic="Revenue Impact",
            magnitude=0.6,
            reason="Different elasticity assumptions",
            category="revenue",
        )
        
        assert disagreement.agent_a == "fiscal-1"
        assert disagreement.magnitude == 0.6
        assert not disagreement.resolved
    
    def test_disagreement_resolution(self):
        """Test marking disagreement as resolved."""
        disagreement = Disagreement(
            agent_a="fiscal-1",
            agent_b="economic-1",
            topic="Revenue Impact",
            magnitude=0.6,
            reason="Test",
            category="revenue",
        )
        
        disagreement.resolved = True
        disagreement.resolution_round = 2
        
        assert disagreement.resolved
        assert disagreement.resolution_round == 2


class TestDemoData:
    """Tests for demo data generation."""
    
    def test_create_demo_debate_data(self):
        """Test demo debate data creation."""
        rounds, disagreements = create_demo_debate_data()
        
        assert len(rounds) >= 1
        assert len(disagreements) >= 1
        
        # Check round structure
        round1 = rounds[0]
        assert round1.round_number == 1
        assert len(round1.turns) > 0
        
        # Check disagreement structure
        d1 = disagreements[0]
        assert d1.agent_a
        assert d1.agent_b
        assert 0 <= d1.magnitude <= 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestEventIntegration:
    """Integration tests for event processing."""
    
    def test_full_event_pipeline(self):
        """Test processing a full sequence of events."""
        events_data = [
            {"event_type": "pipeline_started", "data": {"bill_id": "HR-001"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_started", "data": {"agent_id": "fiscal-1", "agent_type": "fiscal"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_finding", "data": {"agent_id": "fiscal-1", "category": "revenue", "description": "Test finding"}, "timestamp": datetime.now().isoformat()},
            {"event_type": "agent_completed", "data": {"agent_id": "fiscal-1", "overall_confidence": 0.85}, "timestamp": datetime.now().isoformat()},
            {"event_type": "consensus_reached", "data": {"consensus_level": "consensus"}, "timestamp": datetime.now().isoformat()},
        ]
        
        processed = [process_stream_event(e) for e in events_data]
        
        assert len(processed) == 5
        assert processed[0].event_type == "pipeline_started"
        assert processed[4].event_type == "consensus_reached"
    
    def test_confidence_from_multiple_agents(self):
        """Test tracking confidence from multiple agents."""
        tracker = ConfidenceTracker()
        
        agents = ["fiscal-1", "healthcare-1", "economic-1"]
        
        for i in range(5):
            for agent in agents:
                conf = 0.6 + (i * 0.05) + (hash(agent) % 10) / 100
                tracker.add_point(
                    agent_id=agent,
                    confidence=min(conf, 1.0),
                    agent_type=agent.split("-")[0],
                )
        
        latest = tracker.get_latest_confidences()
        assert len(latest) == 3
        
        for conf in latest.values():
            assert 0.6 <= conf <= 1.0


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
