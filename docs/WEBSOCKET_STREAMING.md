# WebSocket Streaming API (Phase 7.2.1)

This document describes the WebSocket streaming infrastructure for real-time analysis visibility in PoliSim.

## Overview

The streaming API enables clients to receive real-time updates during swarm analysis, including:
- Pipeline stage changes
- Agent thoughts and findings
- Debate turns and convergence
- Consensus results
- Progress tracking with ETA

## Quick Start

### Connect to Analysis Stream

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis/{analysis_id}');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Event: ${data.event_type}`, data);
};

ws.onopen = () => {
    console.log('Connected to analysis stream');
};
```

### Reconnection Support

If disconnected, pass your last received sequence number to resume:

```javascript
// Reconnect with last sequence
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/analysis/{analysis_id}?last_sequence=42');
```

## Event Types

| Event Type | Description | Data Fields |
|------------|-------------|-------------|
| `pipeline_started` | Analysis has begun | `bill_id`, `agents` |
| `stage_changed` | Pipeline moved to new stage | `stage` |
| `agent_started` | Agent began analysis | `agent_id`, `agent_type`, `agent_label`, `agent_icon` |
| `agent_thinking` | Agent's intermediate reasoning (batched) | `thoughts[]` with type, content, confidence |
| `agent_finding` | Agent discovered a finding | `category`, `description`, `confidence`, `fiscal_impact` |
| `agent_completed` | Agent finished analysis | `findings_count`, `overall_confidence`, `key_takeaways` |
| `debate_started` | Debate round began | `round_number`, `topic`, `participants` |
| `debate_turn` | Agent spoke in debate | `agent_id`, `turn_type`, `content`, `target_agent` |
| `debate_convergence` | Convergence score updated | `convergence_score`, `change`, `threshold_met` |
| `consensus_reached` | Agents reached consensus | `consensus_level`, `agreed_findings_count`, `strong_findings` |
| `analysis_complete` | Full analysis finished | `analysis_id` |
| `progress_update` | Progress information | See Progress section |
| `error` | An error occurred | `error` message |

## Event Examples

### Agent Started Event
```json
{
    "event_id": "abc123",
    "event_type": "agent_started",
    "analysis_id": "analysis-456",
    "data": {
        "agent_id": "fiscal-agent-1",
        "agent_type": "fiscal",
        "agent_label": "Fiscal Analyst",
        "agent_icon": "💰",
        "status": "analyzing"
    },
    "timestamp": "2026-01-03T12:00:00.000Z",
    "sequence": 5
}
```

### Agent Thinking Event (Batched)
```json
{
    "event_type": "agent_thinking",
    "data": {
        "thoughts": [
            {
                "thought_id": "t1",
                "agent_id": "fiscal-agent-1",
                "thought_type": "calculation",
                "thought_label": "Calculating",
                "content": "Computing 10-year revenue impact...",
                "confidence": 0.75,
                "related_section": "Section 3: Tax Provisions"
            }
        ],
        "batch_size": 1
    }
}
```

### Debate Convergence Event
```json
{
    "event_type": "debate_convergence",
    "data": {
        "round_number": 2,
        "convergence_score": 0.75,
        "previous_score": 0.6,
        "change": 0.15,
        "converging": true,
        "threshold_met": false
    }
}
```

### Progress Update Event
```json
{
    "event_type": "progress_update",
    "data": {
        "analysis_id": "analysis-456",
        "bill_id": "bill-123",
        "stage": "analyzing",
        "stage_progress": 0.5,
        "agents_complete": 2,
        "agents_total": 4,
        "debates_complete": 0,
        "debates_expected": 1,
        "estimated_time_remaining_seconds": 45,
        "elapsed_seconds": 30.5,
        "start_time": "2026-01-03T12:00:00.000Z"
    }
}
```

## Client Messages

### Ping/Pong
Keep connection alive with ping messages:

```json
// Client sends
{"type": "ping"}

// Server responds
{"type": "pong", "timestamp": "2026-01-03T12:00:00.000Z"}
```

### Request Progress Update
```json
{"type": "progress_request"}
```

## REST Endpoints

### Get Stream Status
```
GET /api/v1/ws/analysis/{analysis_id}/status
```

Response:
```json
{
    "analysis_id": "analysis-456",
    "connections": 5,
    "progress": { ... },
    "buffer_size": 42
}
```

### Get WebSocket Stats
```
GET /api/v1/ws/stats
```

Response:
```json
{
    "total_connections": 25,
    "active_analyses": 3,
    "stats": {
        "total_connections": 150,
        "total_events_sent": 5000,
        "total_reconnections": 12
    }
}
```

## Configuration

Configure the WebSocket server via `WebSocketConfig`:

| Setting | Default | Description |
|---------|---------|-------------|
| `max_connections_per_analysis` | 100 | Max clients per analysis |
| `max_total_connections` | 1000 | Max total connections |
| `connection_timeout_seconds` | 3600 | Connection timeout (1 hour) |
| `ping_interval_seconds` | 30 | Ping interval for keepalive |
| `max_events_per_second` | 50 | Rate limit per analysis |
| `thought_batch_window_ms` | 100 | Batching window for thoughts |
| `message_buffer_size` | 1000 | Buffer size for reconnection |

## Integration with SwarmCoordinator

### Using StreamingCoordinator

```python
from api.streaming_integration import StreamingCoordinator
from core.agents.base_agent import AnalysisContext

# Create context
context = AnalysisContext(
    bill_id="bill-123",
    bill_text="...",
    bill_sections={},
    extracted_mechanisms={},
    baseline_data={},
)

# Run streaming analysis
coordinator = StreamingCoordinator()
result = await coordinator.run_streaming_analysis(
    context,
    analysis_id="my-analysis-id"
)
```

### Using create_streaming_callback

```python
from api.websocket_server import create_streaming_callback
from core.agents.coordinator import SwarmCoordinator

# Create callback
callback = await create_streaming_callback("analysis-123")

# Use with coordinator
coordinator = SwarmCoordinator()
result = await coordinator.analyze_bill(context, event_callback=callback)
```

## Architecture

```
┌─────────────────┐     ┌─────────────────────┐
│  Web Clients    │────►│  WebSocket Server   │
│  (Browser/CLI)  │◄────│  (FastAPI Router)   │
└─────────────────┘     └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ ConnectionManager   │
                        │ - Per-analysis rooms│
                        │ - Message buffering │
                        │ - Rate limiting     │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │ StreamingCoordinator│
                        │ - Event formatting  │
                        │ - Progress tracking │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │  SwarmCoordinator   │
                        │  (Multi-Agent Core) │
                        └─────────────────────┘
```

## Files

| File | Description |
|------|-------------|
| `api/websocket_server.py` | WebSocket server, ConnectionManager, ProgressTracker |
| `api/streaming_integration.py` | StreamingCoordinator, event formatters |
| `tests/test_websocket_streaming.py` | Comprehensive tests (34 passing) |

## Error Handling

The streaming infrastructure handles:
- Connection limits (graceful rejection)
- Rate limiting (dropped events with warning)
- Dead connections (automatic cleanup)
- Reconnection (message replay from buffer)
- Analysis errors (error events to clients)

## Performance

- Thought batching reduces UI flooding (100ms window)
- Rate limiting prevents overload (50 events/second default)
- Message buffering enables reconnection (1000 messages, 5 min TTL)
- Per-analysis rooms enable targeted broadcasting

## Next Steps (7.2.2)

The Live UI Components slice will build on this infrastructure:
- `LiveAnalysisPanel` - Real-time event display
- Confidence band visualization
- Debate view with conversation-style layout
- Disagreement map visualization
