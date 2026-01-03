# PoliSim Chat Infrastructure Documentation

**Phase 7.3.1 - Chat Infrastructure**  
**Status:** ✅ Complete  
**Date:** January 3, 2026

---

## Overview

The PoliSim Chatroom provides an MCP-enabled collaborative workspace where users can interact with AI agents, run analyses, and collaborate on policy exploration. This document covers the chat infrastructure implementation.

---

## Architecture

### Components

```
api/
├── chat_models.py          # SQLAlchemy models for chat data
├── chat_api.py             # REST API endpoints + ChatService
├── chat_mcp_tools.py       # MCP tools for AI agent integration
├── chat_agent_participation.py  # Agent @mention & response logic
└── chat_websocket.py       # Real-time WebSocket server

tests/
└── test_chat.py            # Comprehensive test suite
```

### Data Flow

```
User/Agent → REST API or WebSocket → ChatService → SQLite/PostgreSQL
                    ↓
              AgentChatManager → MCP Tools → SwarmCoordinator
                    ↓
              WebSocket Broadcast → All Channel Subscribers
```

---

## Data Models

### ChatChannel

Represents a conversation space for policy discussions.

| Field | Type | Description |
|-------|------|-------------|
| `channel_id` | string | Unique identifier (UUID) |
| `channel_type` | enum | PUBLIC, PRIVATE, GROUP, BILL_SPECIFIC |
| `name` | string | Display name |
| `description` | string | Optional description |
| `created_by` | string | Creator's user ID |
| `bill_id` | string | Associated bill (for BILL_SPECIFIC) |
| `is_active` | bool | Whether channel is active |
| `is_archived` | bool | Whether channel is archived |

### ChatMessage

Individual messages within a channel.

| Field | Type | Description |
|-------|------|-------------|
| `message_id` | string | Unique identifier (UUID) |
| `channel_id` | FK | Parent channel |
| `sender_id` | string | User or agent ID |
| `sender_type` | enum | USER, AGENT, SYSTEM |
| `content` | text | Message content (markdown supported) |
| `message_type` | enum | TEXT, ANALYSIS_REQUEST, ANALYSIS_RESULT, etc. |
| `metadata` | JSON | Rich content (charts, analysis data) |
| `thread_id` | string | Thread parent (for replies) |
| `mentions` | JSON | List of @mentioned user/agent IDs |

### Other Models

- **ChannelParticipant**: Channel membership and roles
- **ChatAttachment**: File/data attachments
- **ChatReaction**: Emoji reactions (👍 👎 ❤️ 🤔 🎉 ⚠️ ✅ ❓)
- **ChatPresence**: Online/typing status

---

## REST API Endpoints

Base URL: `/api/v1/chat`

### Channel Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/channels` | Create a new channel |
| GET | `/channels` | List user's accessible channels |
| GET | `/channels/{id}` | Get channel details |
| DELETE | `/channels/{id}` | Delete (archive) channel |

### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/channels/{id}/messages` | Send message |
| GET | `/channels/{id}/messages` | Get message history |
| DELETE | `/messages/{id}` | Delete message |
| GET | `/messages/search?q=query` | Search messages |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/channels/{id}/agents` | Add agent to channel |
| DELETE | `/channels/{id}/agents/{agent_id}` | Remove agent |
| GET | `/channels/{id}/agents` | List channel agents |

### Reactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/messages/{id}/reactions` | Add reaction |
| DELETE | `/messages/{id}/reactions/{reaction}` | Remove reaction |

### Presence

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/presence` | Update presence status |
| GET | `/channels/{id}/presence` | Get channel presence |
| POST | `/channels/{id}/read` | Mark messages as read |

---

## WebSocket API

### Connection

```
ws://host/ws/chat/{channel_id}?user_id={id}&user_type=user
```

Or for multi-channel:
```
ws://host/ws/chat?user_id={id}&user_type=user
```

### Event Types

**Messages:**
- `new_message` - New message in channel
- `message_edited` - Message was edited
- `message_deleted` - Message was deleted

**Presence:**
- `user_joined` - User joined channel
- `user_left` - User left channel
- `presence_update` - Presence status changed
- `typing_start` / `typing_stop` - Typing indicators

**Agents:**
- `agent_joined` / `agent_left` - Agent channel membership
- `agent_thinking` - Agent processing indicator
- `agent_response` - Agent sent a response

**Analysis:**
- `analysis_started` - Swarm analysis began
- `analysis_progress` - Progress update
- `analysis_complete` - Results available

**System:**
- `ping` / `pong` - Keepalive
- `ack` - Acknowledgment
- `error` - Error occurred

### Event Format

```json
{
  "event_id": "abc123",
  "event_type": "new_message",
  "channel_id": "channel-uuid",
  "data": {
    "message_id": "msg-uuid",
    "sender_id": "user_123",
    "content": "Hello!",
    ...
  },
  "timestamp": "2026-01-03T12:00:00Z",
  "sequence": 42
}
```

---

## MCP Tools

Tools available for AI agents in chat:

### analyze_bill
Trigger full swarm analysis on a bill.

```python
await tools.analyze_bill(
    bill_id="HR1234",
    focus_areas=["revenue", "healthcare"],
    channel_id="optional-channel"  # Posts results here
)
```

### run_scenario
Run economic scenario simulation.

```python
await tools.run_scenario(
    scenario_type="recession",  # or "inflation", "policy_change"
    parameters={"severity": 0.8},
    years=10,
    channel_id="optional-channel"
)
```

### compare_policies
Compare multiple policies side-by-side.

```python
await tools.compare_policies(
    policy_ids=["policy_a", "policy_b", "policy_c"],
    comparison_metrics=["fiscal_impact", "coverage"]
)
```

### query_cbo_data
Query CBO baseline data.

```python
await tools.query_cbo_data(
    metric="total_revenue",
    start_year=2026,
    end_year=2036
)
```

### send_chat_message
Send a message as an agent.

```python
await tools.send_chat_message(
    channel_id="channel-uuid",
    content="Here's my analysis...",
    message_type="text",
    agent_id="fiscal"
)
```

### get_channel_context
Get recent messages for context.

```python
await tools.get_channel_context(
    channel_id="channel-uuid",
    message_count=20
)
```

---

## Agent Participation

### Available Agents (Tier 1)

| Agent ID | Name | Specialty | Emoji |
|----------|------|-----------|-------|
| `fiscal` | Fiscal Agent | Revenue, spending, debt | 💰 |
| `healthcare` | Healthcare Agent | Medicare, Medicaid, ACA | 🏥 |
| `economic` | Economic Agent | GDP, employment, macro | 📈 |
| `social_security` | Social Security Agent | Trust funds, benefits | 👴 |

### Tier 2 Agents

| Agent ID | Name | Specialty | Emoji |
|----------|------|-----------|-------|
| `equity` | Equity Agent | Distributional impact | ⚖️ |
| `implementation` | Implementation Agent | Practical feasibility | 🔧 |

### @Mention Response

Agents respond when:
1. Directly @mentioned (`@fiscal analyze this`)
2. Question asked on their specialty topic
3. Analysis request for their domain

### Rate Limiting

- Max 5 messages/minute per agent
- Max 50 messages/hour per agent
- 30-second cooldown after burst

---

## Usage Examples

### Create Channel & Add Agent

```python
from api.chat_api import ChatService
from api.database import get_db_session

with get_db_session() as session:
    service = ChatService(session)
    
    # Create channel
    channel = service.create_channel(
        name="Budget Analysis 2026",
        created_by="user_123",
        description="Discuss federal budget proposals"
    )
    
    # Add fiscal agent
    service.add_agent_to_channel(
        channel_id=channel.channel_id,
        agent_id="fiscal",
        added_by="user_123"
    )
```

### Send Message with @Mention

```python
message = service.send_message(
    channel_id=channel.channel_id,
    sender_id="user_123",
    content="@fiscal What's the 10-year deficit projection?",
    mentions=["fiscal"]
)
```

### Trigger Analysis

```python
from api.chat_mcp_tools import ChatMCPTools

tools = ChatMCPTools()
result = await tools.analyze_bill(
    bill_id="HR4521",
    focus_areas=["revenue", "healthcare"],
    channel_id=channel.channel_id
)
```

---

## Database Schema

```sql
-- Chat channels
CREATE TABLE chat_channels (
    id INTEGER PRIMARY KEY,
    channel_id VARCHAR(36) UNIQUE NOT NULL,
    channel_type VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_by VARCHAR(36) NOT NULL,
    bill_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    last_message_at TIMESTAMP
);

-- Chat messages
CREATE TABLE chat_messages (
    id INTEGER PRIMARY KEY,
    message_id VARCHAR(36) UNIQUE NOT NULL,
    channel_id INTEGER REFERENCES chat_channels(id),
    sender_id VARCHAR(36) NOT NULL,
    sender_type VARCHAR(20) NOT NULL,
    sender_name VARCHAR(255),
    content TEXT NOT NULL,
    message_type VARCHAR(30) NOT NULL,
    metadata JSON,
    thread_id VARCHAR(36),
    reply_to_id VARCHAR(36),
    mentions JSON,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    is_pinned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    edited_at TIMESTAMP
);

-- Channel participants
CREATE TABLE channel_participants (
    id INTEGER PRIMARY KEY,
    channel_id INTEGER REFERENCES chat_channels(id),
    participant_id VARCHAR(36) NOT NULL,
    participant_type VARCHAR(20) NOT NULL,
    role VARCHAR(20) DEFAULT 'member',
    is_muted BOOLEAN DEFAULT FALSE,
    unread_count INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    left_at TIMESTAMP
);
```

---

## Action Buttons (Phase 7.3.2)

The action button system enables users to trigger analyses, run scenarios, and compare policies directly from the chat interface.

### Action Types

| Action Type | Label | Icon | Category | Description |
|-------------|-------|------|----------|-------------|
| `analyze_bill` | "Analyze this bill" | 🔍 | Analysis | Triggers full swarm analysis |
| `run_scenario` | "Run scenario" | 📊 | Scenario | Applies economic scenarios |
| `show_disagreement` | "Show disagreement map" | 🗺️ | Analysis | Views agent disagreements |
| `compare_policies` | "Compare policies" | ⚖️ | Comparison | Side-by-side comparison |
| `export_results` | "Export results" | 📥 | Export | Download analysis results |
| `query_cbo` | "Query CBO data" | 📈 | Query | Query CBO baseline data |

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/chat/actions` | List available actions |
| POST | `/api/v1/chat/actions/suggest` | Get context-aware suggestions |
| POST | `/api/v1/chat/actions/execute` | Execute an action |
| GET | `/api/v1/chat/actions/{id}/status` | Get action status |
| POST | `/api/v1/chat/actions/{id}/cancel` | Cancel running action |
| POST | `/api/v1/chat/actions/button` | Create action button |

### Suggestion Engine

The suggestion engine analyzes conversation context to recommend relevant actions:

```python
from api.chat_actions import suggest_actions, ActionContext

context = ActionContext(
    channel_id="ch_123",
    recent_messages=[{"content": "What if HR 456 passes?"}],
    mentioned_bills=["HR456"],
)

suggestions = await suggest_actions(context)
# Returns: [SuggestedAction(action=analyze_bill, relevance=0.9), ...]
```

**Detection Patterns:**
- Bill references (HR 123, S. 456) → suggest `analyze_bill`
- Scenario keywords (recession, what if) → suggest `run_scenario`
- Comparison keywords (compare, versus) → suggest `compare_policies`
- Export keywords (download, save) → suggest `export_results`

### Action Execution

```python
from api.chat_actions import execute_action, ActionType

result = await execute_action(
    ActionType.ANALYZE_BILL,
    {"bill_id": "HR456"},
    channel_id="ch_123",
)
# result.status: COMPLETED | FAILED
# result.result_data: analysis findings
```

### Action Button Creation

```python
from api.chat_actions import create_action_button, ActionType

button = create_action_button(
    ActionType.RUN_SCENARIO,
    {"scenario_type": "recession"},
    label="Test Recession Impact",
)
# button.to_dict() → JSON for frontend
```

---

## Testing

Run the chat test suite:

```bash
# All chat tests
pytest tests/test_chat.py -v

# Action button tests
pytest tests/test_chat_actions.py -v
```

Test categories:
- Model tests (15 tests)
- Service layer tests (15 tests)
- MCP tools tests (8 tests)
- Agent participation tests (10 tests)
- WebSocket tests (5 tests)
- Integration tests (5 tests)
- **Action button tests (53 tests)** ✨ New

---

## Configuration

Add to `config.yaml`:

```yaml
chat:
  # Connection limits
  max_connections_per_channel: 100
  max_total_connections: 1000
  
  # Message settings
  max_message_length: 10000
  message_retention_days: 365
  
  # Agent settings
  agent_rate_limit_per_minute: 5
  agent_rate_limit_per_hour: 50
  enable_proactive_insights: true
  
  # WebSocket settings
  ping_interval_seconds: 30
  typing_timeout_seconds: 5
  
  # Action settings (Phase 7.3.2)
  actions:
    max_concurrent_actions: 3
    default_timeout_seconds: 60
    enable_suggestions: true
```

---

## Next Steps (Phase 7.3.3) ✅ COMPLETE

### Chat UI Implementation (January 2026)

The Chat UI has been fully implemented in `ui/chat_sidebar.py` with the following features:

1. **ChatSidebar Component**
   - Channel list with unread indicators
   - Agent presence display with status
   - Tab-based interface (Channels, History, Export)
   - Responsive design for sidebar or main panel

2. **Message List with Infinite Scroll**
   - Date separators between messages
   - Load more button for pagination
   - Support for 10k+ messages (tested)
   - Auto-scroll and manual navigation

3. **Message Composer**
   - Rich text input area
   - @mention autocomplete for agents
   - Quick action buttons (Analyze, Compare, Project, Summary)
   - File attachment support

4. **Agent Message Rendering**
   - Agent avatar/icon with specialty badge
   - Confidence indicator visualization
   - "Thinking..." animation for processing
   - Color-coded by agent type

5. **System Message Styles**
   - Analysis started/completed events
   - User joined/left notifications
   - Action triggered confirmations
   - Error/warning messages

6. **Analysis Result Cards**
   - Collapsible summary sections
   - Key findings list with confidence
   - Progress bar visualization
   - Drill down / Export / Copy actions

7. **Chat Export (JSON + PDF)**
   - JSON format with full data
   - PDF format with formatted conversation
   - Include/exclude options for metadata
   - Date range filtering

8. **History Browser**
   - Full-text search
   - Filter by type, agent, date
   - Jump to specific messages
   - Message bookmarking

### UI Module Location

```
ui/
├── chat_sidebar.py          # Main chat UI component (Phase 7.3.3)
├── live_analysis_panel.py   # Streaming analysis UI (Phase 7.2.2)
├── confidence_visualization.py  # Confidence charts
└── debate_visualization.py  # Debate view components
```

### Usage Example

```python
from ui.chat_sidebar import ChatSidebar, render_chat_sidebar

# In Streamlit app
sidebar = ChatSidebar(
    api_base_url="http://localhost:8000/api/v1/chat",
    user_id="user_123",
    user_name="John Analyst",
)
sidebar.render()

# Or use convenience function
render_chat_sidebar(user_id="user_123", demo_mode=True)
```

### Test Coverage

- 41 tests covering all components
- Performance tested with 10k messages
- Accessibility compliance verified
- All tests passing ✅

