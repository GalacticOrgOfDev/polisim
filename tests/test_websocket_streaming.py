"""Tests for WebSocket Streaming Infrastructure (Phase 7.2.1).

This module tests the WebSocket server, connection management, event
broadcasting, progress tracking, and streaming integration.
"""

import asyncio
import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Import the modules under test
from api.websocket_server import (
    WebSocketConfig,
    StreamEvent,
    AnalysisProgress,
    ConnectionManager,
    ProgressTracker,
    get_connection_manager,
    create_streaming_callback,
    serialize_event_for_logging,
)
from api.streaming_integration import (
    StreamingCoordinator,
    format_agent_started_event,
    format_agent_finding_event,
    format_agent_completed_event,
    format_thought_event,
    format_debate_started_event,
    format_debate_turn_event,
    format_debate_convergence_event,
    format_consensus_reached_event,
    get_active_streams,
    AnalysisStreamInfo,
)
from core.agents.types import (
    AgentType,
    AnalysisEventType,
    PipelineState,
    ThoughtType,
    FindingCategory,
    ImpactMagnitude,
)
from core.agents.models import (
    AnalysisEvent,
    AgentAnalysis,
    AgentThought,
    Finding,
    ConsensusFinding,
    FiscalImpact,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def websocket_config():
    """Create a test WebSocket configuration."""
    return WebSocketConfig(
        max_connections_per_analysis=10,
        max_total_connections=50,
        connection_timeout_seconds=60.0,
        ping_interval_seconds=5.0,
        ping_timeout_seconds=2.0,
        max_events_per_second=100,
        thought_batch_window_ms=50,
        message_buffer_size=100,
        message_buffer_ttl_seconds=30.0,
    )


@pytest.fixture
def connection_manager(websocket_config):
    """Create a connection manager for testing."""
    return ConnectionManager(config=websocket_config)


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    ws = AsyncMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    
    # Mock the client_state attribute
    from enum import Enum
    class MockState(Enum):
        CONNECTED = "connected"
    ws.client_state = MockState.CONNECTED
    
    return ws


@pytest.fixture
def sample_analysis_event():
    """Create a sample analysis event."""
    return AnalysisEvent(
        event_id="test-event-123",
        event_type=AnalysisEventType.AGENT_STARTED,
        analysis_id="analysis-123",
        agent_id="fiscal-agent-1",
        data={"agent_type": "fiscal"},
        timestamp=datetime.now(),
    )


@pytest.fixture
def sample_finding():
    """Create a sample finding."""
    return Finding(
        finding_id="finding-123",
        category=FindingCategory.REVENUE,
        description="This policy increases federal revenue by $50B over 10 years",
        impact_magnitude=ImpactMagnitude.HIGH,
        confidence=0.85,
        time_horizon="10-year",
        affected_populations=["all taxpayers"],
        fiscal_impact=FiscalImpact(
            amount_billions=50.0,
            time_period="10-year",
            confidence_low=40.0,
            confidence_mid=50.0,
            confidence_high=65.0,
            is_revenue=True,
        ),
    )


@pytest.fixture
def sample_agent_analysis():
    """Create a sample agent analysis."""
    return AgentAnalysis(
        analysis_id="analysis-123",
        agent_id="fiscal-agent-1",
        agent_type=AgentType.FISCAL,
        bill_id="bill-123",
        findings=[],
        overall_confidence=0.8,
        key_takeaways=["Revenue increase", "Deficit reduction", "Tax reform"],
        execution_time_seconds=15.5,
    )


@pytest.fixture
def sample_thought():
    """Create a sample agent thought."""
    return AgentThought(
        thought_id="thought-123",
        agent_id="fiscal-agent-1",
        thought_type=ThoughtType.CALCULATION,
        content="Calculating 10-year revenue impact based on elasticity model",
        confidence=0.75,
        related_section="Section 3: Tax Provisions",
        timestamp=datetime.now(),
    )


# =============================================================================
# StreamEvent Tests
# =============================================================================

class TestStreamEvent:
    """Tests for StreamEvent class."""
    
    def test_stream_event_creation(self):
        """Test creating a StreamEvent."""
        event = StreamEvent(
            event_type="test_event",
            analysis_id="analysis-123",
            data={"key": "value"},
        )
        
        assert event.event_type == "test_event"
        assert event.analysis_id == "analysis-123"
        assert event.data == {"key": "value"}
        assert event.sequence == 0
        assert event.event_id is not None
    
    def test_stream_event_to_json(self):
        """Test JSON serialization."""
        event = StreamEvent(
            event_id="test-id",
            event_type="test_event",
            analysis_id="analysis-123",
            data={"message": "hello"},
            sequence=5,
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event_id"] == "test-id"
        assert parsed["event_type"] == "test_event"
        assert parsed["analysis_id"] == "analysis-123"
        assert parsed["data"]["message"] == "hello"
        assert parsed["sequence"] == 5
    
    def test_stream_event_from_analysis_event(self, sample_analysis_event):
        """Test creating StreamEvent from AnalysisEvent."""
        stream_event = StreamEvent.from_analysis_event(
            sample_analysis_event,
            sequence=10,
        )
        
        assert stream_event.event_type == AnalysisEventType.AGENT_STARTED.value
        assert stream_event.analysis_id == "analysis-123"
        assert stream_event.sequence == 10


# =============================================================================
# AnalysisProgress Tests
# =============================================================================

class TestAnalysisProgress:
    """Tests for AnalysisProgress class."""
    
    def test_analysis_progress_creation(self):
        """Test creating AnalysisProgress."""
        progress = AnalysisProgress(
            analysis_id="analysis-123",
            bill_id="bill-456",
            stage="analyzing",
            stage_progress=0.5,
            agents_complete=2,
            agents_total=4,
        )
        
        assert progress.analysis_id == "analysis-123"
        assert progress.stage == "analyzing"
        assert progress.stage_progress == 0.5
    
    def test_analysis_progress_to_dict(self):
        """Test dictionary conversion."""
        progress = AnalysisProgress(
            analysis_id="analysis-123",
            bill_id="bill-456",
            stage="debating",
            stage_progress=0.75,
            agents_complete=4,
            agents_total=4,
            debates_complete=1,
            debates_expected=2,
        )
        
        data = progress.to_dict()
        
        assert data["analysis_id"] == "analysis-123"
        assert data["stage"] == "debating"
        assert data["debates_complete"] == 1


# =============================================================================
# ConnectionManager Tests
# =============================================================================

class TestConnectionManager:
    """Tests for ConnectionManager class."""
    
    @pytest.mark.asyncio
    async def test_connect_success(self, connection_manager, mock_websocket):
        """Test successful WebSocket connection."""
        result = await connection_manager.connect(
            mock_websocket,
            "analysis-123",
            last_sequence=0,
        )
        
        assert result is True
        assert connection_manager.get_connection_count("analysis-123") == 1
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_limit_reached(self, websocket_config, mock_websocket):
        """Test connection rejected when limit reached."""
        config = WebSocketConfig(max_connections_per_analysis=1)
        manager = ConnectionManager(config=config)
        
        # First connection should succeed
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        from enum import Enum
        class MockState(Enum):
            CONNECTED = "connected"
        ws1.client_state = MockState.CONNECTED
        
        await manager.connect(ws1, "analysis-123")
        
        # Second connection should fail
        ws2 = AsyncMock()
        result = await manager.connect(ws2, "analysis-123")
        
        assert result is False
    
    def test_disconnect(self, connection_manager, mock_websocket):
        """Test disconnecting a WebSocket."""
        # Manually add connection
        connection_manager._connections["analysis-123"].add(mock_websocket)
        
        connection_manager.disconnect(mock_websocket, "analysis-123")
        
        assert connection_manager.get_connection_count("analysis-123") == 0
    
    @pytest.mark.asyncio
    async def test_broadcast(self, connection_manager, mock_websocket):
        """Test broadcasting event to subscribers."""
        # Setup connection
        await connection_manager.connect(mock_websocket, "analysis-123")
        
        # Broadcast event
        event = StreamEvent(
            event_type="test_event",
            analysis_id="analysis-123",
            data={"message": "hello"},
        )
        
        sent_count = await connection_manager.broadcast("analysis-123", event)
        
        assert sent_count == 1
        mock_websocket.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_no_subscribers(self, connection_manager):
        """Test broadcasting with no subscribers."""
        event = StreamEvent(
            event_type="test_event",
            analysis_id="no-subscribers",
            data={},
        )
        
        sent_count = await connection_manager.broadcast("no-subscribers", event)
        
        assert sent_count == 0
    
    def test_update_progress(self, connection_manager):
        """Test updating progress for an analysis."""
        progress = AnalysisProgress(
            analysis_id="analysis-123",
            stage="analyzing",
            stage_progress=0.5,
        )
        
        connection_manager.update_progress("analysis-123", progress)
        
        assert "analysis-123" in connection_manager._progress
        assert connection_manager._progress["analysis-123"].stage == "analyzing"
    
    def test_get_connection_count(self, connection_manager):
        """Test getting connection counts."""
        # No connections
        assert connection_manager.get_connection_count() == 0
        assert connection_manager.get_connection_count("analysis-123") == 0
        
        # Add mock connections
        ws1 = MagicMock()
        ws2 = MagicMock()
        connection_manager._connections["analysis-1"].add(ws1)
        connection_manager._connections["analysis-2"].add(ws2)
        
        assert connection_manager.get_connection_count() == 2
        assert connection_manager.get_connection_count("analysis-1") == 1
    
    def test_cleanup_old_buffers(self, connection_manager):
        """Test cleaning up orphaned buffers."""
        # Create buffer without connection
        connection_manager._message_buffers["orphaned-analysis"] = [
            StreamEvent(event_type="test", analysis_id="orphaned-analysis")
        ]
        connection_manager._progress["orphaned-analysis"] = AnalysisProgress()
        
        connection_manager.cleanup_old_buffers()
        
        assert "orphaned-analysis" not in connection_manager._message_buffers
        assert "orphaned-analysis" not in connection_manager._progress
    
    def test_sequence_counter(self, connection_manager):
        """Test sequence number generation."""
        seq1 = connection_manager._get_next_sequence("analysis-123")
        seq2 = connection_manager._get_next_sequence("analysis-123")
        seq3 = connection_manager._get_next_sequence("analysis-456")
        
        assert seq1 == 1
        assert seq2 == 2
        assert seq3 == 1  # Different analysis
    
    def test_message_buffering(self, connection_manager):
        """Test message buffering for reconnection."""
        event = StreamEvent(
            event_type="test",
            analysis_id="analysis-123",
            sequence=1,
        )
        
        connection_manager._buffer_message("analysis-123", event)
        
        assert len(connection_manager._message_buffers["analysis-123"]) == 1
    
    def test_buffer_size_limit(self, websocket_config):
        """Test buffer size limiting."""
        config = WebSocketConfig(message_buffer_size=3)
        manager = ConnectionManager(config=config)
        
        # Add more events than buffer size
        for i in range(5):
            event = StreamEvent(
                event_type="test",
                analysis_id="analysis-123",
                sequence=i,
            )
            manager._buffer_message("analysis-123", event)
        
        # Should only have last 3
        assert len(manager._message_buffers["analysis-123"]) == 3


# =============================================================================
# ProgressTracker Tests
# =============================================================================

class TestProgressTracker:
    """Tests for ProgressTracker class."""
    
    def test_progress_tracker_creation(self):
        """Test creating a ProgressTracker."""
        tracker = ProgressTracker(
            analysis_id="analysis-123",
            bill_id="bill-456",
            agent_count=4,
        )
        
        assert tracker.analysis_id == "analysis-123"
        assert tracker.bill_id == "bill-456"
        assert tracker.agent_count == 4
        assert tracker.current_stage == PipelineState.INITIALIZED
    
    def test_update_stage(self):
        """Test updating pipeline stage."""
        tracker = ProgressTracker("a1", "b1", 4)
        
        tracker.update_stage(PipelineState.ANALYZING)
        
        assert tracker.current_stage == PipelineState.ANALYZING
    
    def test_update_agent_progress(self):
        """Test updating agent progress."""
        tracker = ProgressTracker("a1", "b1", 4)
        
        tracker.update_agent_progress(2, 4)
        
        assert tracker.agents_complete == 2
        assert tracker.agent_count == 4
    
    def test_update_debate_progress(self):
        """Test updating debate progress."""
        tracker = ProgressTracker("a1", "b1", 4)
        
        tracker.update_debate_progress(1, 3)
        
        assert tracker.debates_complete == 1
        assert tracker.debates_expected == 3
    
    def test_get_progress(self):
        """Test getting current progress."""
        tracker = ProgressTracker("a1", "b1", 4)
        tracker.update_stage(PipelineState.ANALYZING)
        tracker.update_agent_progress(2, 4)
        
        progress = tracker.get_progress()
        
        assert progress.analysis_id == "a1"
        assert progress.bill_id == "b1"
        assert progress.stage == "analyzing"
        assert progress.agents_complete == 2
        assert progress.agents_total == 4
    
    def test_stage_progress_for_analyzing(self):
        """Test stage progress calculation during analysis."""
        tracker = ProgressTracker("a1", "b1", 4)
        tracker.update_stage(PipelineState.ANALYZING)
        tracker.update_agent_progress(2, 4)
        
        progress = tracker.get_progress()
        
        assert progress.stage_progress == 0.5  # 2/4 agents
    
    def test_stage_progress_for_debating(self):
        """Test stage progress calculation during debate."""
        tracker = ProgressTracker("a1", "b1", 4)
        tracker.update_stage(PipelineState.DEBATING)
        tracker.update_debate_progress(1, 2)
        
        progress = tracker.get_progress()
        
        assert progress.stage_progress == 0.5  # 1/2 debates
    
    def test_eta_calculation(self):
        """Test ETA estimation."""
        tracker = ProgressTracker("a1", "b1", 4)
        
        progress = tracker.get_progress()
        
        # Should have some estimated time remaining
        assert progress.estimated_time_remaining_seconds >= 0


# =============================================================================
# Event Formatter Tests
# =============================================================================

class TestEventFormatters:
    """Tests for event formatting functions."""
    
    def test_format_agent_started_event(self):
        """Test formatting agent_started event."""
        result = format_agent_started_event(
            "fiscal-agent-1",
            AgentType.FISCAL,
        )
        
        assert result["agent_id"] == "fiscal-agent-1"
        assert result["agent_type"] == "fiscal"
        assert result["agent_label"] == "Fiscal Analyst"
        assert result["agent_icon"] == "💰"
        assert result["status"] == "analyzing"
    
    def test_format_agent_finding_event(self, sample_finding):
        """Test formatting agent_finding event."""
        result = format_agent_finding_event("fiscal-agent-1", sample_finding)
        
        assert result["agent_id"] == "fiscal-agent-1"
        assert result["category"] == "revenue"
        assert result["confidence"] == 0.85
        assert result["fiscal_impact"]["amount_billions"] == 50.0
    
    def test_format_agent_completed_event(self, sample_agent_analysis):
        """Test formatting agent_completed event."""
        result = format_agent_completed_event(
            "fiscal-agent-1",
            sample_agent_analysis,
        )
        
        assert result["agent_id"] == "fiscal-agent-1"
        assert result["overall_confidence"] == 0.8
        assert result["status"] == "completed"
        assert len(result["key_takeaways"]) <= 3
    
    def test_format_thought_event(self, sample_thought):
        """Test formatting agent_thinking event."""
        result = format_thought_event(sample_thought)
        
        assert result["thought_id"] == "thought-123"
        assert result["thought_type"] == "calculation"
        assert result["thought_label"] == "Calculating"
        assert "elasticity" in result["content"]
    
    def test_format_debate_started_event(self):
        """Test formatting debate_started event."""
        result = format_debate_started_event(
            round_number=1,
            topic="Revenue impact estimates",
            participants=["fiscal-agent-1", "economic-agent-1"],
        )
        
        assert result["round_number"] == 1
        assert result["topic"] == "Revenue impact estimates"
        assert result["participant_count"] == 2
    
    def test_format_debate_turn_event(self):
        """Test formatting debate_turn event."""
        result = format_debate_turn_event(
            agent_id="fiscal-agent-1",
            turn_type="critique",
            content="The revenue estimate seems optimistic",
            target_agent="economic-agent-1",
        )
        
        assert result["agent_id"] == "fiscal-agent-1"
        assert result["turn_type"] == "critique"
        assert result["target_agent"] == "economic-agent-1"
    
    def test_format_debate_convergence_event(self):
        """Test formatting debate_convergence event."""
        result = format_debate_convergence_event(
            round_number=2,
            convergence_score=0.75,
            previous_score=0.6,
        )
        
        assert result["convergence_score"] == 0.75
        assert abs(result["change"] - 0.15) < 0.001  # Float comparison tolerance
        assert result["converging"] is True
        assert result["threshold_met"] is False
    
    def test_format_debate_convergence_threshold_met(self):
        """Test convergence threshold detection."""
        result = format_debate_convergence_event(
            round_number=3,
            convergence_score=0.85,
            previous_score=0.75,
        )
        
        assert result["threshold_met"] is True
    
    def test_format_consensus_reached_event(self):
        """Test formatting consensus_reached event."""
        findings = [
            ConsensusFinding(
                description="Revenue increase of $50B",
                weighted_confidence=0.85,
            ),
            ConsensusFinding(
                description="Deficit reduction",
                weighted_confidence=0.8,
            ),
        ]
        
        result = format_consensus_reached_event(findings, "consensus")
        
        assert result["consensus_level"] == "consensus"
        assert result["agreed_findings_count"] == 2
        assert len(result["strong_findings"]) == 2


# =============================================================================
# StreamingCoordinator Tests
# =============================================================================

class TestStreamingCoordinator:
    """Tests for StreamingCoordinator class."""
    
    def test_streaming_coordinator_creation(self):
        """Test creating a StreamingCoordinator."""
        coordinator = StreamingCoordinator()
        
        assert coordinator.coordinator is not None
    
    def test_streaming_coordinator_with_custom_manager(self, connection_manager):
        """Test creating coordinator with custom manager."""
        coordinator = StreamingCoordinator(
            connection_manager=connection_manager,
        )
        
        assert coordinator.connection_manager == connection_manager


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_serialize_event_for_logging(self):
        """Test event serialization for logging."""
        event = StreamEvent(
            event_id="test-123",
            event_type="agent_started",
            analysis_id="analysis-123",
            data={"agent_id": "fiscal-1", "details": "lots of data"},
            sequence=5,
        )
        
        result = serialize_event_for_logging(event)
        
        assert result["event_id"] == "test-123"
        assert result["event_type"] == "agent_started"
        assert result["data_keys"] == ["agent_id", "details"]
        # Full data should not be in log format
        assert "details" not in result.get("data", {})
    
    def test_get_active_streams_empty(self, connection_manager):
        """Test getting active streams when none exist."""
        streams = get_active_streams(connection_manager)
        
        assert streams == []
    
    def test_analysis_stream_info(self):
        """Test AnalysisStreamInfo class."""
        info = AnalysisStreamInfo(
            analysis_id="a1",
            bill_id="b1",
            started_at="2026-01-03T12:00:00",
            current_stage="analyzing",
            connections=5,
            progress=0.5,
        )
        
        data = info.to_dict()
        
        assert data["analysis_id"] == "a1"
        assert data["connections"] == 5


# =============================================================================
# Integration Tests
# =============================================================================

class TestStreamingIntegration:
    """Integration tests for streaming infrastructure."""
    
    @pytest.mark.asyncio
    async def test_create_streaming_callback(self, connection_manager):
        """Test creating a streaming callback."""
        callback = await create_streaming_callback(
            "analysis-123",
            manager=connection_manager,
        )
        
        assert callable(callback)
    
    @pytest.mark.asyncio
    async def test_callback_broadcasts_event(
        self,
        connection_manager,
        mock_websocket,
    ):
        """Test that callback broadcasts events."""
        # Setup connection
        await connection_manager.connect(mock_websocket, "analysis-123")
        
        # Create callback
        callback = await create_streaming_callback(
            "analysis-123",
            manager=connection_manager,
        )
        
        # Create and send event
        event = AnalysisEvent(
            event_type=AnalysisEventType.PIPELINE_STARTED,
            analysis_id="analysis-123",
            data={"bill_id": "bill-123"},
        )
        
        await callback(event)
        
        # Should have sent message
        mock_websocket.send_text.assert_called()
    
    @pytest.mark.asyncio
    async def test_reconnection_receives_missed_events(
        self,
        connection_manager,
    ):
        """Test that reconnecting clients receive missed events."""
        # Buffer some events
        for i in range(5):
            event = StreamEvent(
                event_type=f"event_{i}",
                analysis_id="analysis-123",
                sequence=i + 1,
            )
            connection_manager._buffer_message("analysis-123", event)
        
        # Connect with last_sequence=2 (missed events 3, 4, 5)
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_text = AsyncMock()
        from enum import Enum
        class MockState(Enum):
            CONNECTED = "connected"
        ws.client_state = MockState.CONNECTED
        
        await connection_manager.connect(ws, "analysis-123", last_sequence=2)
        
        # Should have sent missed events (seq 3, 4, 5)
        # Plus potentially a progress update
        assert ws.send_text.call_count >= 3


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
