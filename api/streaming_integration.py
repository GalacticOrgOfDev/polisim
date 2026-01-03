"""Streaming Integration for Live Analysis Mode (Phase 7.2.1).

This module provides integration between the SwarmCoordinator and
WebSocket streaming infrastructure for real-time analysis visibility.

Features:
- Streaming-enabled coordinator wrapper
- Progress tracking integration
- Event transformation and routing
- UI-friendly event formatting

Example:
    from api.streaming_integration import StreamingCoordinator
    
    coordinator = StreamingCoordinator(analysis_id="abc123")
    result = await coordinator.run_streaming_analysis(context)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, List, Optional
from uuid import uuid4

from core.agents.types import (
    AgentType,
    AnalysisEventType,
    PipelineState,
    ThoughtType,
)
from core.agents.models import (
    AnalysisEvent,
    AgentAnalysis,
    AgentThought,
    SwarmAnalysis,
    Finding,
    Critique,
    DebateRound,
    Vote,
    ConsensusFinding,
)
from core.agents.base_agent import AnalysisContext
from core.agents.coordinator import SwarmCoordinator

try:
    from api.websocket_server import (
        ConnectionManager,
        StreamEvent,
        AnalysisProgress,
        ProgressTracker,
        get_connection_manager,
        create_streaming_callback,
    )
    HAS_WEBSOCKET = True
except ImportError:
    HAS_WEBSOCKET = False


logger = logging.getLogger(__name__)


# =============================================================================
# Event Formatters
# =============================================================================

def format_agent_started_event(
    agent_id: str,
    agent_type: AgentType,
) -> Dict[str, Any]:
    """Format agent_started event data for UI."""
    return {
        "agent_id": agent_id,
        "agent_type": agent_type.value,
        "agent_label": _get_agent_label(agent_type),
        "agent_icon": _get_agent_icon(agent_type),
        "status": "analyzing",
    }


def format_agent_finding_event(
    agent_id: str,
    finding: Finding,
) -> Dict[str, Any]:
    """Format agent_finding event data for UI."""
    return {
        "agent_id": agent_id,
        "finding_id": finding.finding_id,
        "category": finding.category.value,
        "description": finding.description,
        "impact_magnitude": finding.impact_magnitude.value,
        "confidence": finding.confidence,
        "time_horizon": finding.time_horizon,
        "fiscal_impact": _format_fiscal_impact(finding.fiscal_impact),
    }


def format_agent_completed_event(
    agent_id: str,
    analysis: AgentAnalysis,
) -> Dict[str, Any]:
    """Format agent_completed event data for UI."""
    return {
        "agent_id": agent_id,
        "agent_type": analysis.agent_type.value,
        "findings_count": len(analysis.findings),
        "overall_confidence": analysis.overall_confidence,
        "key_takeaways": analysis.key_takeaways[:3],  # Top 3
        "execution_time_seconds": analysis.execution_time_seconds,
        "status": "completed",
    }


def format_thought_event(
    thought: AgentThought,
) -> Dict[str, Any]:
    """Format agent_thinking event data for UI."""
    return {
        "thought_id": thought.thought_id,
        "agent_id": thought.agent_id,
        "thought_type": thought.thought_type.value,
        "thought_label": _get_thought_label(thought.thought_type),
        "content": thought.content,
        "confidence": thought.confidence,
        "related_section": thought.related_section,
        "timestamp": thought.timestamp.isoformat(),
    }


def format_debate_started_event(
    round_number: int,
    topic: str,
    participants: List[str],
) -> Dict[str, Any]:
    """Format debate_started event data for UI."""
    return {
        "round_number": round_number,
        "topic": topic,
        "participants": participants,
        "participant_count": len(participants),
    }


def format_debate_turn_event(
    agent_id: str,
    turn_type: str,  # "critique" or "rebuttal"
    content: str,
    target_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """Format debate_turn event data for UI."""
    return {
        "agent_id": agent_id,
        "agent_label": agent_id.split("-")[0].title(),  # Extract type
        "turn_type": turn_type,
        "content": content,
        "target_agent": target_agent,
    }


def format_debate_convergence_event(
    round_number: int,
    convergence_score: float,
    previous_score: Optional[float] = None,
) -> Dict[str, Any]:
    """Format debate_convergence event data for UI."""
    change = None
    if previous_score is not None:
        change = convergence_score - previous_score
    
    return {
        "round_number": round_number,
        "convergence_score": convergence_score,
        "previous_score": previous_score,
        "change": change,
        "converging": change > 0 if change else None,
        "threshold_met": convergence_score >= 0.8,
    }


def format_consensus_reached_event(
    findings: List[ConsensusFinding],
    consensus_level: str,
) -> Dict[str, Any]:
    """Format consensus_reached event data for UI."""
    return {
        "consensus_level": consensus_level,
        "agreed_findings_count": len(findings),
        "strong_findings": [
            {
                "description": f.description,
                "confidence": f.weighted_confidence,
            }
            for f in findings[:5]  # Top 5 findings
        ],
    }


# =============================================================================
# Helper Functions
# =============================================================================

def _get_agent_label(agent_type: AgentType) -> str:
    """Get human-readable label for agent type."""
    labels = {
        AgentType.FISCAL: "Fiscal Analyst",
        AgentType.ECONOMIC: "Economist",
        AgentType.HEALTHCARE: "Healthcare Expert",
        AgentType.SOCIAL_SECURITY: "Social Security Analyst",
        AgentType.EQUITY: "Equity Analyst",
        AgentType.IMPLEMENTATION: "Implementation Specialist",
        AgentType.BEHAVIORAL: "Behavioral Economist",
        AgentType.LEGAL: "Legal Analyst",
        AgentType.JUDGE: "Senior Arbitrator",
        AgentType.COORDINATOR: "Coordinator",
    }
    return labels.get(agent_type, agent_type.value.title())


def _get_agent_icon(agent_type: AgentType) -> str:
    """Get icon/emoji for agent type."""
    icons = {
        AgentType.FISCAL: "💰",
        AgentType.ECONOMIC: "📈",
        AgentType.HEALTHCARE: "🏥",
        AgentType.SOCIAL_SECURITY: "👴",
        AgentType.EQUITY: "⚖️",
        AgentType.IMPLEMENTATION: "🔧",
        AgentType.BEHAVIORAL: "🧠",
        AgentType.LEGAL: "⚖️",
        AgentType.JUDGE: "👨‍⚖️",
        AgentType.COORDINATOR: "🎯",
    }
    return icons.get(agent_type, "🤖")


def _get_thought_label(thought_type: ThoughtType) -> str:
    """Get human-readable label for thought type."""
    labels = {
        ThoughtType.OBSERVATION: "Observing",
        ThoughtType.HYPOTHESIS: "Hypothesizing",
        ThoughtType.CALCULATION: "Calculating",
        ThoughtType.CONCLUSION: "Concluding",
        ThoughtType.QUESTION: "Questioning",
        ThoughtType.REFERENCE: "Referencing",
        ThoughtType.COMPARISON: "Comparing",
    }
    return labels.get(thought_type, thought_type.value.title())


def _format_fiscal_impact(fiscal_impact) -> Optional[Dict[str, Any]]:
    """Format fiscal impact for display."""
    if fiscal_impact is None:
        return None
    
    return {
        "amount_billions": fiscal_impact.amount_billions,
        "time_period": fiscal_impact.time_period,
        "confidence_range": f"${fiscal_impact.confidence_low:.1f}B - ${fiscal_impact.confidence_high:.1f}B",
        "is_revenue": fiscal_impact.is_revenue,
        "is_recurring": fiscal_impact.is_recurring,
    }


# =============================================================================
# Streaming Coordinator Wrapper
# =============================================================================

class StreamingCoordinator:
    """Wrapper around SwarmCoordinator with streaming capabilities.
    
    Provides real-time event streaming to WebSocket clients while
    running swarm analysis.
    
    Example:
        coordinator = StreamingCoordinator()
        result = await coordinator.run_streaming_analysis(
            context,
            analysis_id="my-analysis-id"
        )
    """
    
    def __init__(
        self,
        coordinator: Optional[SwarmCoordinator] = None,
        connection_manager: Optional["ConnectionManager"] = None,
    ):
        """Initialize streaming coordinator.
        
        Args:
            coordinator: SwarmCoordinator instance (creates one if not provided)
            connection_manager: WebSocket connection manager
        """
        self.coordinator = coordinator or SwarmCoordinator()
        
        if HAS_WEBSOCKET:
            self.connection_manager = connection_manager or get_connection_manager()
        else:
            self.connection_manager = None
            logger.warning("WebSocket not available - streaming disabled")
        
        self._progress_tracker: Optional["ProgressTracker"] = None
        self._analysis_id: Optional[str] = None
    
    async def run_streaming_analysis(
        self,
        context: AnalysisContext,
        analysis_id: Optional[str] = None,
    ) -> SwarmAnalysis:
        """Run swarm analysis with real-time streaming.
        
        Args:
            context: Analysis context with bill data
            analysis_id: Optional analysis ID (generated if not provided)
        
        Returns:
            Complete SwarmAnalysis result
        """
        self._analysis_id = analysis_id or str(uuid4())
        
        # Initialize progress tracker
        if HAS_WEBSOCKET:
            self._progress_tracker = ProgressTracker(
                analysis_id=self._analysis_id,
                bill_id=context.bill_id,
                agent_count=len(self.coordinator.agents),
            )
        
        logger.info(f"Starting streaming analysis {self._analysis_id}")
        
        # Create streaming callback
        callback = await self._create_enhanced_callback()
        
        # Run analysis with streaming
        result = await self.coordinator.analyze_bill(
            context,
            event_callback=callback,
        )
        
        # Send final completion event
        await self._emit_final_event(result)
        
        return result
    
    async def _create_enhanced_callback(
        self,
    ) -> Callable[[AnalysisEvent], Awaitable[None]]:
        """Create an enhanced callback that formats events for UI.
        
        Returns:
            Async callback function
        """
        async def callback(event: AnalysisEvent) -> None:
            """Process and stream analysis event."""
            # Update progress tracker
            if self._progress_tracker:
                await self._update_progress(event)
            
            # Format event data for UI
            formatted_data = self._format_event_data(event)
            
            # Broadcast to WebSocket clients
            if self.connection_manager and self._analysis_id:
                stream_event = StreamEvent(
                    event_type=event.event_type.value,
                    analysis_id=self._analysis_id,
                    data=formatted_data,
                    timestamp=event.timestamp.isoformat(),
                )
                await self.connection_manager.broadcast(
                    self._analysis_id,
                    stream_event,
                )
        
        return callback
    
    async def _update_progress(self, event: AnalysisEvent) -> None:
        """Update progress tracker based on event."""
        if not self._progress_tracker:
            return
        
        event_type = event.event_type
        
        if event_type == AnalysisEventType.STAGE_CHANGED:
            stage_name = event.data.get("stage", "")
            try:
                stage = PipelineState(stage_name)
                self._progress_tracker.update_stage(stage)
            except ValueError:
                pass
        
        elif event_type == AnalysisEventType.AGENT_COMPLETED:
            self._progress_tracker.agents_complete += 1
        
        elif event_type == AnalysisEventType.DEBATE_CONVERGENCE:
            self._progress_tracker.debates_complete += 1
        
        # Update connection manager with progress
        if self.connection_manager and self._analysis_id:
            progress = self._progress_tracker.get_progress()
            self.connection_manager.update_progress(self._analysis_id, progress)
            
            # Send progress update periodically
            if event_type in {
                AnalysisEventType.STAGE_CHANGED,
                AnalysisEventType.AGENT_COMPLETED,
                AnalysisEventType.DEBATE_CONVERGENCE,
            }:
                await self.connection_manager.send_progress_update(self._analysis_id)
    
    def _format_event_data(self, event: AnalysisEvent) -> Dict[str, Any]:
        """Format event data based on event type."""
        event_type = event.event_type
        data = event.data
        
        # Use specialized formatters for specific events
        if event_type == AnalysisEventType.AGENT_STARTED:
            agent_type_str = data.get("agent_type", "")
            try:
                agent_type = AgentType(agent_type_str)
                return format_agent_started_event(
                    data.get("agent_id", ""),
                    agent_type,
                )
            except ValueError:
                pass
        
        elif event_type == AnalysisEventType.AGENT_THINKING:
            thought = data.get("thought")
            if isinstance(thought, AgentThought):
                return format_thought_event(thought)
        
        elif event_type == AnalysisEventType.DEBATE_STARTED:
            return format_debate_started_event(
                data.get("round_number", 1),
                data.get("topic", ""),
                data.get("participants", []),
            )
        
        elif event_type == AnalysisEventType.DEBATE_CONVERGENCE:
            return format_debate_convergence_event(
                data.get("round_number", 1),
                data.get("convergence_score", 0.0),
                data.get("previous_score"),
            )
        
        elif event_type == AnalysisEventType.CONSENSUS_REACHED:
            return format_consensus_reached_event(
                data.get("findings", []),
                data.get("consensus_level", "consensus"),
            )
        
        # Default: return original data with some enrichment
        return {
            **data,
            "event_type": event_type.value,
            "timestamp": event.timestamp.isoformat(),
        }
    
    async def _emit_final_event(self, result: SwarmAnalysis) -> None:
        """Emit final completion event with summary."""
        if not self.connection_manager or not self._analysis_id:
            return
        
        summary = {
            "analysis_id": result.analysis_id,
            "bill_id": result.bill_id,
            "total_findings": len(result.consensus_findings),
            "disagreements": len(result.disagreements),
            "agents_participated": result.metadata.agents_participated,
            "debate_rounds": result.metadata.debate_rounds_conducted,
            "execution_time_seconds": result.metadata.total_execution_time_seconds,
            "consensus_level": (
                result.consensus_report.confidence_level.value
                if result.consensus_report
                else "unknown"
            ),
        }
        
        event = StreamEvent(
            event_type="analysis_summary",
            analysis_id=self._analysis_id,
            data=summary,
        )
        
        await self.connection_manager.broadcast(self._analysis_id, event)


# =============================================================================
# API Endpoint Helpers
# =============================================================================

@dataclass
class AnalysisStreamInfo:
    """Information about an active analysis stream."""
    
    analysis_id: str
    bill_id: str
    started_at: str
    current_stage: str
    connections: int
    progress: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "bill_id": self.bill_id,
            "started_at": self.started_at,
            "current_stage": self.current_stage,
            "connections": self.connections,
            "progress": self.progress,
        }


def get_active_streams(
    connection_manager: Optional["ConnectionManager"] = None,
) -> List[AnalysisStreamInfo]:
    """Get information about active analysis streams.
    
    Args:
        connection_manager: Connection manager (uses global if not provided)
    
    Returns:
        List of active stream information
    """
    if not HAS_WEBSOCKET:
        return []
    
    manager = connection_manager or get_connection_manager()
    
    streams = []
    for analysis_id in manager._connections.keys():
        progress = manager._progress.get(analysis_id)
        
        streams.append(AnalysisStreamInfo(
            analysis_id=analysis_id,
            bill_id=progress.bill_id if progress else "",
            started_at=progress.start_time if progress else "",
            current_stage=progress.stage if progress else "unknown",
            connections=manager.get_connection_count(analysis_id),
            progress=progress.stage_progress if progress else 0.0,
        ))
    
    return streams


async def start_analysis_with_streaming(
    context: AnalysisContext,
    analysis_id: Optional[str] = None,
) -> SwarmAnalysis:
    """Convenience function to start a streaming analysis.
    
    Args:
        context: Analysis context
        analysis_id: Optional analysis ID
    
    Returns:
        Complete SwarmAnalysis
    """
    coordinator = StreamingCoordinator()
    return await coordinator.run_streaming_analysis(context, analysis_id)
