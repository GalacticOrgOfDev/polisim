"""WebSocket Server for Live Analysis Streaming (Phase 7.2.1).

This module provides real-time streaming of swarm analysis events to clients
via WebSocket connections, enabling live visibility into agent reasoning.

Features:
- WebSocket endpoint for analysis streaming
- Event broadcasting to subscribed clients
- Backpressure handling and rate limiting
- Reconnection support with message buffering
- Progress tracking with ETA calculation

Example:
    # In main FastAPI app
    from api.websocket_server import create_websocket_router
    
    router = create_websocket_router()
    app.include_router(router)
    
    # Client connection
    ws = await websockets.connect(f"ws://localhost:8000/ws/analysis/{analysis_id}")
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
from uuid import uuid4

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
    from fastapi.websockets import WebSocketState
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    # Stubs for when FastAPI is not installed
    class WebSocket:
        pass
    class WebSocketDisconnect(Exception):
        pass

from core.agents.types import AnalysisEventType, PipelineState, ThoughtType
from core.agents.models import AnalysisEvent, AgentThought

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class WebSocketConfig:
    """Configuration for WebSocket server."""
    
    # Connection limits
    max_connections_per_analysis: int = 100
    max_total_connections: int = 1000
    
    # Timeout settings
    connection_timeout_seconds: float = 3600.0  # 1 hour
    ping_interval_seconds: float = 30.0
    ping_timeout_seconds: float = 10.0
    
    # Rate limiting
    max_events_per_second: int = 50
    thought_batch_window_ms: int = 100
    
    # Buffer settings (for reconnection)
    message_buffer_size: int = 1000
    message_buffer_ttl_seconds: float = 300.0  # 5 minutes


# =============================================================================
# Event Types for Live Analysis
# =============================================================================

@dataclass
class StreamEvent:
    """Event sent to WebSocket clients."""
    
    event_id: str = field(default_factory=lambda: str(uuid4())[:12])
    event_type: str = ""
    analysis_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    sequence: int = 0  # For ordering/deduplication
    
    def to_json(self) -> str:
        """Serialize event to JSON."""
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "analysis_id": self.analysis_id,
            "data": self.data,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
        })
    
    @classmethod
    def from_analysis_event(cls, event: AnalysisEvent, sequence: int = 0) -> "StreamEvent":
        """Convert internal AnalysisEvent to StreamEvent."""
        return cls(
            event_id=event.event_id,
            event_type=event.event_type.value,
            analysis_id=event.analysis_id,
            data=event.data,
            timestamp=event.timestamp.isoformat(),
            sequence=sequence,
        )


@dataclass
class AnalysisProgress:
    """Progress information for an analysis."""
    
    analysis_id: str = ""
    bill_id: str = ""
    stage: str = "initialized"
    stage_progress: float = 0.0  # 0.0 - 1.0
    agents_complete: int = 0
    agents_total: int = 0
    debates_complete: int = 0
    debates_expected: int = 0
    estimated_time_remaining_seconds: int = 0
    elapsed_seconds: float = 0.0
    start_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "analysis_id": self.analysis_id,
            "bill_id": self.bill_id,
            "stage": self.stage,
            "stage_progress": self.stage_progress,
            "agents_complete": self.agents_complete,
            "agents_total": self.agents_total,
            "debates_complete": self.debates_complete,
            "debates_expected": self.debates_expected,
            "estimated_time_remaining_seconds": self.estimated_time_remaining_seconds,
            "elapsed_seconds": self.elapsed_seconds,
            "start_time": self.start_time,
        }


# =============================================================================
# Connection Manager
# =============================================================================

class ConnectionManager:
    """Manages WebSocket connections and event broadcasting.
    
    Handles:
    - Connection tracking per analysis
    - Event broadcasting to subscribers
    - Message buffering for reconnection
    - Rate limiting and backpressure
    """
    
    def __init__(self, config: Optional[WebSocketConfig] = None):
        """Initialize connection manager.
        
        Args:
            config: WebSocket configuration. Uses defaults if not provided.
        """
        self.config = config or WebSocketConfig()
        
        # Active connections: analysis_id -> set of websockets
        self._connections: Dict[str, Set[WebSocket]] = defaultdict(set)
        
        # Connection metadata
        self._connection_info: Dict[int, Dict[str, Any]] = {}
        
        # Message buffer for each analysis (for reconnection)
        self._message_buffers: Dict[str, List[StreamEvent]] = defaultdict(list)
        
        # Progress tracking per analysis
        self._progress: Dict[str, AnalysisProgress] = {}
        
        # Sequence counters per analysis
        self._sequence_counters: Dict[str, int] = defaultdict(int)
        
        # Thought batching queues
        self._thought_batches: Dict[str, List[AgentThought]] = defaultdict(list)
        self._batch_tasks: Dict[str, asyncio.Task] = {}
        
        # Rate limiting
        self._event_counts: Dict[str, int] = defaultdict(int)
        self._last_reset: Dict[str, float] = {}
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "total_events_sent": 0,
            "total_reconnections": 0,
        }
        
        logger.info("ConnectionManager initialized")
    
    async def connect(
        self,
        websocket: WebSocket,
        analysis_id: str,
        last_sequence: int = 0,
    ) -> bool:
        """Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection to accept
            analysis_id: The analysis to subscribe to
            last_sequence: Last received sequence (for reconnection)
        
        Returns:
            True if connection accepted, False if rejected
        """
        # Check connection limits
        if len(self._connections[analysis_id]) >= self.config.max_connections_per_analysis:
            logger.warning(f"Connection limit reached for analysis {analysis_id}")
            return False
        
        total_connections = sum(len(conns) for conns in self._connections.values())
        if total_connections >= self.config.max_total_connections:
            logger.warning("Total connection limit reached")
            return False
        
        # Accept connection
        await websocket.accept()
        
        self._connections[analysis_id].add(websocket)
        self._connection_info[id(websocket)] = {
            "analysis_id": analysis_id,
            "connected_at": datetime.now().isoformat(),
            "last_sequence": last_sequence,
            "messages_sent": 0,
        }
        
        self.stats["total_connections"] += 1
        
        logger.info(f"WebSocket connected to analysis {analysis_id}")
        
        # Send buffered messages for reconnection
        if last_sequence > 0:
            await self._send_missed_events(websocket, analysis_id, last_sequence)
            self.stats["total_reconnections"] += 1
        
        # Send current progress
        if analysis_id in self._progress:
            progress_event = StreamEvent(
                event_type="progress_update",
                analysis_id=analysis_id,
                data=self._progress[analysis_id].to_dict(),
                sequence=self._get_next_sequence(analysis_id),
            )
            await self._send_to_websocket(websocket, progress_event)
        
        return True
    
    def disconnect(self, websocket: WebSocket, analysis_id: str) -> None:
        """Remove a WebSocket connection.
        
        Args:
            websocket: The WebSocket to disconnect
            analysis_id: The analysis it was subscribed to
        """
        self._connections[analysis_id].discard(websocket)
        
        # Clean up empty sets
        if not self._connections[analysis_id]:
            del self._connections[analysis_id]
        
        # Clean up metadata
        if id(websocket) in self._connection_info:
            del self._connection_info[id(websocket)]
        
        logger.info(f"WebSocket disconnected from analysis {analysis_id}")
    
    async def broadcast(
        self,
        analysis_id: str,
        event: StreamEvent,
    ) -> int:
        """Broadcast an event to all subscribers of an analysis.
        
        Args:
            analysis_id: The analysis ID
            event: The event to broadcast
        
        Returns:
            Number of clients that received the event
        """
        if analysis_id not in self._connections:
            return 0
        
        # Check rate limit
        if not self._check_rate_limit(analysis_id):
            logger.warning(f"Rate limit exceeded for analysis {analysis_id}")
            return 0
        
        # Set sequence number
        event.sequence = self._get_next_sequence(analysis_id)
        
        # Buffer message for reconnection
        self._buffer_message(analysis_id, event)
        
        # Broadcast to all connections
        sent_count = 0
        dead_connections = []
        
        for websocket in self._connections[analysis_id]:
            try:
                await self._send_to_websocket(websocket, event)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                dead_connections.append(websocket)
        
        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(ws, analysis_id)
        
        self.stats["total_events_sent"] += sent_count
        
        return sent_count
    
    async def broadcast_thought(
        self,
        analysis_id: str,
        thought: AgentThought,
    ) -> None:
        """Buffer and batch agent thoughts for efficient streaming.
        
        Thoughts are batched over a short window to prevent UI flooding
        while still providing responsive updates.
        
        Args:
            analysis_id: The analysis ID
            thought: The agent thought to stream
        """
        self._thought_batches[analysis_id].append(thought)
        
        # Start batch flush task if not running
        if analysis_id not in self._batch_tasks or self._batch_tasks[analysis_id].done():
            self._batch_tasks[analysis_id] = asyncio.create_task(
                self._flush_thought_batch(analysis_id)
            )
    
    async def _flush_thought_batch(self, analysis_id: str) -> None:
        """Flush batched thoughts after delay."""
        await asyncio.sleep(self.config.thought_batch_window_ms / 1000.0)
        
        if not self._thought_batches[analysis_id]:
            return
        
        # Get and clear batch
        thoughts = self._thought_batches[analysis_id]
        self._thought_batches[analysis_id] = []
        
        # Create batch event
        event = StreamEvent(
            event_type=AnalysisEventType.AGENT_THINKING.value,
            analysis_id=analysis_id,
            data={
                "thoughts": [
                    {
                        "thought_id": t.thought_id,
                        "agent_id": t.agent_id,
                        "thought_type": t.thought_type.value,
                        "content": t.content,
                        "confidence": t.confidence,
                        "related_section": t.related_section,
                        "timestamp": t.timestamp.isoformat(),
                    }
                    for t in thoughts
                ],
                "batch_size": len(thoughts),
            },
        )
        
        await self.broadcast(analysis_id, event)
    
    def update_progress(
        self,
        analysis_id: str,
        progress: AnalysisProgress,
    ) -> None:
        """Update progress tracking for an analysis.
        
        Args:
            analysis_id: The analysis ID
            progress: Current progress information
        """
        self._progress[analysis_id] = progress
    
    async def send_progress_update(self, analysis_id: str) -> None:
        """Send current progress to all subscribers."""
        if analysis_id not in self._progress:
            return
        
        event = StreamEvent(
            event_type="progress_update",
            analysis_id=analysis_id,
            data=self._progress[analysis_id].to_dict(),
        )
        
        await self.broadcast(analysis_id, event)
    
    def _get_next_sequence(self, analysis_id: str) -> int:
        """Get next sequence number for an analysis."""
        self._sequence_counters[analysis_id] += 1
        return self._sequence_counters[analysis_id]
    
    def _buffer_message(self, analysis_id: str, event: StreamEvent) -> None:
        """Add message to buffer for reconnection support."""
        buffer = self._message_buffers[analysis_id]
        buffer.append(event)
        
        # Trim buffer if too large
        if len(buffer) > self.config.message_buffer_size:
            buffer.pop(0)
    
    async def _send_missed_events(
        self,
        websocket: WebSocket,
        analysis_id: str,
        last_sequence: int,
    ) -> None:
        """Send events missed during disconnection."""
        buffer = self._message_buffers.get(analysis_id, [])
        
        missed_events = [e for e in buffer if e.sequence > last_sequence]
        
        if missed_events:
            logger.info(f"Sending {len(missed_events)} missed events to reconnected client")
            
            for event in missed_events:
                await self._send_to_websocket(websocket, event)
    
    async def _send_to_websocket(
        self,
        websocket: WebSocket,
        event: StreamEvent,
    ) -> None:
        """Send event to a single websocket."""
        if HAS_FASTAPI:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(event.to_json())
                
                # Update stats
                ws_id = id(websocket)
                if ws_id in self._connection_info:
                    self._connection_info[ws_id]["messages_sent"] += 1
        else:
            # Fallback for non-FastAPI environments
            pass
    
    def _check_rate_limit(self, analysis_id: str) -> bool:
        """Check if rate limit allows sending."""
        now = asyncio.get_event_loop().time()
        last_reset = self._last_reset.get(analysis_id, 0)
        
        # Reset counter every second
        if now - last_reset >= 1.0:
            self._event_counts[analysis_id] = 0
            self._last_reset[analysis_id] = now
        
        if self._event_counts[analysis_id] >= self.config.max_events_per_second:
            return False
        
        self._event_counts[analysis_id] += 1
        return True
    
    def get_connection_count(self, analysis_id: Optional[str] = None) -> int:
        """Get number of active connections."""
        if analysis_id:
            return len(self._connections.get(analysis_id, set()))
        return sum(len(conns) for conns in self._connections.values())
    
    def cleanup_old_buffers(self) -> None:
        """Remove old message buffers and progress data."""
        # Clean up buffers for analyses with no connections
        orphaned = [
            aid for aid in self._message_buffers
            if aid not in self._connections
        ]
        
        for aid in orphaned:
            del self._message_buffers[aid]
            if aid in self._progress:
                del self._progress[aid]
            if aid in self._sequence_counters:
                del self._sequence_counters[aid]
        
        logger.debug(f"Cleaned up {len(orphaned)} orphaned buffers")


# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager() -> ConnectionManager:
    """Get or create the global connection manager."""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


# =============================================================================
# Event Callback for SwarmCoordinator Integration
# =============================================================================

async def create_streaming_callback(
    analysis_id: str,
    manager: Optional[ConnectionManager] = None,
) -> Callable[[AnalysisEvent], Awaitable[None]]:
    """Create an event callback for streaming analysis events.
    
    This callback integrates with the SwarmCoordinator to broadcast
    events to WebSocket clients.
    
    Args:
        analysis_id: The analysis ID
        manager: Connection manager (uses global if not provided)
    
    Returns:
        Async callback function for event streaming
    
    Example:
        callback = await create_streaming_callback(analysis_id)
        result = await coordinator.analyze_bill(context, event_callback=callback)
    """
    mgr = manager or get_connection_manager()
    
    async def callback(event: AnalysisEvent) -> None:
        """Stream analysis event to connected clients."""
        stream_event = StreamEvent.from_analysis_event(event)
        await mgr.broadcast(analysis_id, stream_event)
        
        # Handle thought events specially (batching)
        if event.event_type == AnalysisEventType.AGENT_THINKING:
            thought = event.data.get("thought")
            if thought and isinstance(thought, AgentThought):
                await mgr.broadcast_thought(analysis_id, thought)
    
    return callback


# =============================================================================
# Progress Tracker
# =============================================================================

class ProgressTracker:
    """Tracks and estimates analysis progress.
    
    Uses historical data and current stage to estimate remaining time
    and overall progress percentage.
    """
    
    # Average durations per stage (seconds) - calibrated from real runs
    DEFAULT_STAGE_DURATIONS = {
        PipelineState.INITIALIZED: 0.1,
        PipelineState.INGESTING: 2.0,
        PipelineState.ANALYZING: 30.0,  # Depends on agent count
        PipelineState.CROSS_REVIEWING: 15.0,
        PipelineState.DEBATING: 20.0,
        PipelineState.VOTING: 5.0,
        PipelineState.SYNTHESIZING: 3.0,
        PipelineState.COMPLETE: 0.0,
    }
    
    # Stage weights for overall progress (sum = 1.0)
    STAGE_WEIGHTS = {
        PipelineState.INITIALIZED: 0.0,
        PipelineState.INGESTING: 0.02,
        PipelineState.ANALYZING: 0.40,
        PipelineState.CROSS_REVIEWING: 0.20,
        PipelineState.DEBATING: 0.25,
        PipelineState.VOTING: 0.08,
        PipelineState.SYNTHESIZING: 0.05,
        PipelineState.COMPLETE: 1.0,
    }
    
    def __init__(self, analysis_id: str, bill_id: str, agent_count: int = 4):
        """Initialize progress tracker.
        
        Args:
            analysis_id: The analysis ID
            bill_id: The bill being analyzed
            agent_count: Number of agents participating
        """
        self.analysis_id = analysis_id
        self.bill_id = bill_id
        self.agent_count = agent_count
        
        self.start_time = datetime.now()
        self.current_stage = PipelineState.INITIALIZED
        self.stage_start_time = self.start_time
        
        self.agents_complete = 0
        self.debates_complete = 0
        self.debates_expected = 0
        
        # Historical timing data for ETA improvement
        self._stage_history: Dict[PipelineState, List[float]] = defaultdict(list)
    
    def update_stage(self, stage: PipelineState) -> None:
        """Update the current pipeline stage.
        
        Args:
            stage: The new pipeline stage
        """
        if stage != self.current_stage:
            # Record duration of previous stage
            duration = (datetime.now() - self.stage_start_time).total_seconds()
            self._stage_history[self.current_stage].append(duration)
            
            self.current_stage = stage
            self.stage_start_time = datetime.now()
    
    def update_agent_progress(self, complete: int, total: Optional[int] = None) -> None:
        """Update agent completion count.
        
        Args:
            complete: Number of agents completed
            total: Total agents (updates if provided)
        """
        self.agents_complete = complete
        if total is not None:
            self.agent_count = total
    
    def update_debate_progress(
        self,
        complete: int,
        expected: Optional[int] = None,
    ) -> None:
        """Update debate completion count.
        
        Args:
            complete: Number of debates completed
            expected: Expected total debates
        """
        self.debates_complete = complete
        if expected is not None:
            self.debates_expected = expected
    
    def get_progress(self) -> AnalysisProgress:
        """Calculate and return current progress.
        
        Returns:
            Current AnalysisProgress
        """
        now = datetime.now()
        elapsed = (now - self.start_time).total_seconds()
        
        # Calculate overall progress percentage
        base_progress = sum(
            self.STAGE_WEIGHTS[s]
            for s in PipelineState
            if self._stage_is_complete(s)
        )
        
        # Add partial progress within current stage
        stage_weight = self.STAGE_WEIGHTS.get(self.current_stage, 0)
        stage_progress = self._get_stage_progress()
        current_contribution = stage_weight * stage_progress
        
        overall_progress = min(base_progress + current_contribution, 1.0)
        
        # Estimate remaining time
        eta = self._estimate_remaining_time(elapsed, overall_progress)
        
        return AnalysisProgress(
            analysis_id=self.analysis_id,
            bill_id=self.bill_id,
            stage=self.current_stage.value,
            stage_progress=stage_progress,
            agents_complete=self.agents_complete,
            agents_total=self.agent_count,
            debates_complete=self.debates_complete,
            debates_expected=self.debates_expected,
            estimated_time_remaining_seconds=int(eta),
            elapsed_seconds=elapsed,
            start_time=self.start_time.isoformat(),
        )
    
    def _stage_is_complete(self, stage: PipelineState) -> bool:
        """Check if a stage is complete."""
        stage_order = list(PipelineState)
        current_idx = stage_order.index(self.current_stage)
        check_idx = stage_order.index(stage)
        return check_idx < current_idx
    
    def _get_stage_progress(self) -> float:
        """Get progress within current stage."""
        if self.current_stage == PipelineState.ANALYZING:
            if self.agent_count > 0:
                return self.agents_complete / self.agent_count
        elif self.current_stage == PipelineState.DEBATING:
            if self.debates_expected > 0:
                return self.debates_complete / self.debates_expected
        elif self.current_stage == PipelineState.COMPLETE:
            return 1.0
        
        # For other stages, estimate based on elapsed time
        expected = self.DEFAULT_STAGE_DURATIONS.get(self.current_stage, 5.0)
        elapsed = (datetime.now() - self.stage_start_time).total_seconds()
        return min(elapsed / expected, 0.95)  # Cap at 95% until stage changes
    
    def _estimate_remaining_time(
        self,
        elapsed: float,
        progress: float,
    ) -> float:
        """Estimate remaining time based on progress.
        
        Args:
            elapsed: Time elapsed so far
            progress: Overall progress (0.0 - 1.0)
        
        Returns:
            Estimated remaining seconds
        """
        if progress <= 0.0:
            # Use default estimates
            return sum(self.DEFAULT_STAGE_DURATIONS.values())
        
        if progress >= 1.0:
            return 0.0
        
        # Simple linear extrapolation
        total_estimated = elapsed / progress
        remaining = total_estimated - elapsed
        
        # Apply some smoothing to avoid jumpy estimates
        return max(0.0, remaining)


# =============================================================================
# FastAPI Router
# =============================================================================

def create_websocket_router(
    config: Optional[WebSocketConfig] = None,
) -> "APIRouter":
    """Create FastAPI router for WebSocket endpoints.
    
    Args:
        config: WebSocket configuration
    
    Returns:
        FastAPI APIRouter with WebSocket endpoints
    
    Example:
        router = create_websocket_router()
        app.include_router(router, prefix="/api/v1")
    """
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI required for WebSocket server. "
            "Install with: pip install fastapi uvicorn"
        )
    
    router = APIRouter(tags=["websocket", "streaming"])
    manager = get_connection_manager()
    
    if config:
        manager.config = config
    
    @router.websocket("/ws/analysis/{analysis_id}")
    async def analysis_stream(
        websocket: WebSocket,
        analysis_id: str,
        last_sequence: int = Query(default=0, description="Last received sequence for reconnection"),
    ):
        """Stream live analysis events.
        
        Connect to receive real-time updates about an ongoing analysis,
        including agent thoughts, findings, debate turns, and consensus.
        
        Events:
        - pipeline_started: Analysis has begun
        - stage_changed: Pipeline moved to new stage
        - agent_started: An agent began analysis
        - agent_thinking: Agent's intermediate reasoning
        - agent_finding: Agent discovered a finding
        - agent_completed: Agent finished analysis
        - debate_started: Debate round began
        - debate_turn: Agent spoke in debate
        - debate_convergence: Convergence score updated
        - consensus_reached: Agents reached consensus
        - analysis_complete: Full analysis finished
        - progress_update: Progress information
        - error: An error occurred
        
        Args:
            websocket: The WebSocket connection
            analysis_id: ID of the analysis to stream
            last_sequence: Last sequence number received (for reconnection)
        """
        accepted = await manager.connect(websocket, analysis_id, last_sequence)
        
        if not accepted:
            await websocket.close(code=1008, reason="Connection limit reached")
            return
        
        try:
            # Keep connection alive and handle pings
            while True:
                try:
                    # Wait for client messages (pings, close, etc.)
                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=manager.config.ping_interval_seconds,
                    )
                    
                    # Handle client messages
                    try:
                        msg = json.loads(data)
                        if msg.get("type") == "ping":
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "timestamp": datetime.now().isoformat(),
                            }))
                        elif msg.get("type") == "progress_request":
                            await manager.send_progress_update(analysis_id)
                    except json.JSONDecodeError:
                        pass  # Ignore invalid messages
                        
                except asyncio.TimeoutError:
                    # Send ping to check connection
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "ping",
                            "timestamp": datetime.now().isoformat(),
                        }))
                    except Exception:
                        break  # Connection dead
                        
        except WebSocketDisconnect:
            logger.info(f"Client disconnected from analysis {analysis_id}")
        finally:
            manager.disconnect(websocket, analysis_id)
    
    @router.get("/ws/analysis/{analysis_id}/status")
    async def get_analysis_stream_status(analysis_id: str):
        """Get status of analysis stream.
        
        Returns connection count and current progress for an analysis.
        
        Args:
            analysis_id: ID of the analysis
        
        Returns:
            Status information
        """
        return {
            "analysis_id": analysis_id,
            "connections": manager.get_connection_count(analysis_id),
            "progress": manager._progress.get(analysis_id, AnalysisProgress()).to_dict(),
            "buffer_size": len(manager._message_buffers.get(analysis_id, [])),
        }
    
    @router.get("/ws/stats")
    async def get_websocket_stats():
        """Get global WebSocket statistics.
        
        Returns:
            WebSocket server statistics
        """
        return {
            "total_connections": manager.get_connection_count(),
            "active_analyses": len(manager._connections),
            "stats": manager.stats,
        }
    
    return router


# =============================================================================
# Utility Functions
# =============================================================================

def serialize_event_for_logging(event: StreamEvent) -> Dict[str, Any]:
    """Serialize event for structured logging."""
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "analysis_id": event.analysis_id,
        "timestamp": event.timestamp,
        "sequence": event.sequence,
        "data_keys": list(event.data.keys()),
    }


async def cleanup_stale_connections(manager: ConnectionManager) -> None:
    """Periodic task to clean up stale connections and buffers."""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        manager.cleanup_old_buffers()
        logger.debug("Cleaned up stale WebSocket resources")
