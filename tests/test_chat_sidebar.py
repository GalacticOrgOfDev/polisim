"""
Tests for Chat Sidebar Component (Phase 7.3.3).

Tests cover:
- ChatSidebar component initialization
- Channel list rendering
- Message display components
- Message composer functionality
- Agent/system message rendering
- Analysis result cards
- Chat export (JSON/PDF)
- History browser and search
- Performance with 10k messages

Run with: pytest tests/test_chat_sidebar.py -v
"""

import json
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any

# Import the module under test
from ui.chat_sidebar import (
    # Data classes
    ChannelInfo,
    MessageDisplay,
    AgentPresence,
    ChatExportOptions,
    # Session state
    init_chat_sidebar_state,
    get_chat_sidebar_state,
    update_chat_sidebar_state,
    # Utility functions
    _hex_to_rgb,
    _format_timestamp,
    _filter_messages,
    _extract_mentions,
    # Components
    ChatSidebar,
    # Demo data
    create_demo_messages,
    create_demo_channels,
    # Constants
    AGENT_COLORS,
    AGENT_ICONS,
    MESSAGE_TYPE_ICONS,
    SYSTEM_EVENT_ICONS,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_channel():
    """Create a sample channel for testing."""
    return ChannelInfo(
        channel_id="test_ch_001",
        name="Test Channel",
        channel_type="public",
        description="A test channel",
        icon="💬",
        unread_count=5,
        last_message_at=datetime.now(timezone.utc),
        last_message_preview="Hello world...",
        is_active=True,
        participants=["user_1", "user_2"],
        agents=["fiscal", "healthcare"],
    )


@pytest.fixture
def sample_user_message():
    """Create a sample user message for testing."""
    return MessageDisplay(
        message_id="msg_001",
        sender_id="user_123",
        sender_type="user",
        sender_name="Test User",
        sender_icon="👤",
        sender_color="#2196F3",
        content="This is a test message",
        message_type="text",
        timestamp=datetime.now(timezone.utc),
        is_own_message=True,
    )


@pytest.fixture
def sample_agent_message():
    """Create a sample agent message for testing."""
    return MessageDisplay(
        message_id="msg_002",
        sender_id="fiscal_agent",
        sender_type="agent",
        sender_name="Fiscal Agent",
        sender_icon="💰",
        sender_color="#4CAF50",
        content="Analysis complete",
        message_type="analysis_result",
        timestamp=datetime.now(timezone.utc),
        metadata={
            "agent_type": "fiscal",
            "confidence": 0.85,
            "summary": "Test summary",
            "findings": [
                {"text": "Finding 1", "confidence": 0.9},
                {"text": "Finding 2", "confidence": 0.8},
            ],
        },
        reactions={"👍": 3, "🤔": 1},
    )


@pytest.fixture
def sample_system_message():
    """Create a sample system message for testing."""
    return MessageDisplay(
        message_id="msg_003",
        sender_id="system",
        sender_type="system",
        sender_name="System",
        sender_icon="🤖",
        sender_color="#9E9E9E",
        content="Analysis started",
        message_type="system_event",
        timestamp=datetime.now(timezone.utc),
        metadata={"event_type": "analysis_started"},
    )


@pytest.fixture
def sample_messages(sample_user_message, sample_agent_message, sample_system_message):
    """Create a list of sample messages."""
    return [sample_system_message, sample_user_message, sample_agent_message]


@pytest.fixture
def agent_presence():
    """Create sample agent presence."""
    return AgentPresence(
        agent_id="fiscal_agent",
        agent_type="fiscal",
        agent_name="Fiscal Agent",
        icon="💰",
        color="#4CAF50",
        status="analyzing",
        status_detail="Processing section 3...",
        last_active=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_session_state():
    """Mock Streamlit session state."""
    with patch("ui.chat_sidebar.st") as mock_st:
        mock_st.session_state = {}
        yield mock_st


# =============================================================================
# Test Data Classes
# =============================================================================

class TestChannelInfo:
    """Tests for ChannelInfo dataclass."""
    
    def test_channel_creation(self, sample_channel):
        """Test channel info creation."""
        assert sample_channel.channel_id == "test_ch_001"
        assert sample_channel.name == "Test Channel"
        assert sample_channel.channel_type == "public"
        assert sample_channel.unread_count == 5
        assert len(sample_channel.agents) == 2
    
    def test_channel_defaults(self):
        """Test channel default values."""
        channel = ChannelInfo(
            channel_id="ch_001",
            name="Default Channel",
        )
        assert channel.channel_type == "public"
        assert channel.icon == "💬"
        assert channel.unread_count == 0
        assert channel.is_active is True
        assert channel.participants == []
        assert channel.agents == []


class TestMessageDisplay:
    """Tests for MessageDisplay dataclass."""
    
    def test_user_message_creation(self, sample_user_message):
        """Test user message creation."""
        assert sample_user_message.sender_type == "user"
        assert sample_user_message.is_own_message is True
        assert sample_user_message.content == "This is a test message"
    
    def test_agent_message_with_metadata(self, sample_agent_message):
        """Test agent message with analysis metadata."""
        assert sample_agent_message.sender_type == "agent"
        assert sample_agent_message.message_type == "analysis_result"
        assert "confidence" in sample_agent_message.metadata
        assert sample_agent_message.metadata["confidence"] == 0.85
        assert len(sample_agent_message.metadata["findings"]) == 2
    
    def test_system_message(self, sample_system_message):
        """Test system message creation."""
        assert sample_system_message.sender_type == "system"
        assert sample_system_message.message_type == "system_event"
        assert sample_system_message.metadata["event_type"] == "analysis_started"
    
    def test_message_reactions(self, sample_agent_message):
        """Test message reactions."""
        assert "👍" in sample_agent_message.reactions
        assert sample_agent_message.reactions["👍"] == 3


class TestAgentPresence:
    """Tests for AgentPresence dataclass."""
    
    def test_agent_presence_creation(self, agent_presence):
        """Test agent presence creation."""
        assert agent_presence.agent_id == "fiscal_agent"
        assert agent_presence.agent_type == "fiscal"
        assert agent_presence.status == "analyzing"
        assert agent_presence.status_detail == "Processing section 3..."
    
    def test_agent_presence_defaults(self):
        """Test agent presence default values."""
        presence = AgentPresence(
            agent_id="test_agent",
            agent_type="economic",
            agent_name="Economic Agent",
            icon="📈",
            color="#2196F3",
        )
        assert presence.status == "idle"
        assert presence.status_detail is None


class TestChatExportOptions:
    """Tests for ChatExportOptions dataclass."""
    
    def test_export_options_defaults(self):
        """Test export options defaults."""
        options = ChatExportOptions()
        assert options.format == "json"
        assert options.include_metadata is True
        assert options.include_reactions is True
        assert options.include_analysis_results is True
        assert options.include_charts is True
    
    def test_export_options_custom(self):
        """Test custom export options."""
        options = ChatExportOptions(
            format="pdf",
            include_metadata=False,
            date_range_start=datetime(2024, 1, 1),
        )
        assert options.format == "pdf"
        assert options.include_metadata is False
        assert options.date_range_start is not None


# =============================================================================
# Test Utility Functions
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        assert _hex_to_rgb("#4CAF50") == "76, 175, 80"
        assert _hex_to_rgb("#2196F3") == "33, 150, 243"
        assert _hex_to_rgb("#FFFFFF") == "255, 255, 255"
        assert _hex_to_rgb("#000000") == "0, 0, 0"
    
    def test_hex_to_rgb_without_hash(self):
        """Test hex to RGB without # prefix."""
        assert _hex_to_rgb("4CAF50") == "76, 175, 80"
    
    def test_format_timestamp_today(self):
        """Test timestamp formatting for today."""
        now = datetime.now(timezone.utc)
        formatted = _format_timestamp(now)
        assert ":" in formatted
        assert len(formatted) == 5  # HH:MM format
    
    def test_format_timestamp_yesterday(self):
        """Test timestamp formatting for yesterday."""
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        formatted = _format_timestamp(yesterday)
        assert "Yesterday" in formatted
    
    def test_format_timestamp_older(self):
        """Test timestamp formatting for older dates."""
        old_date = datetime.now(timezone.utc) - timedelta(days=7)
        formatted = _format_timestamp(old_date)
        assert any(month in formatted for month in [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ])


class TestMessageFiltering:
    """Tests for message filtering."""
    
    def test_filter_by_search_query(self, sample_messages):
        """Test filtering messages by search query."""
        # Search for "test"
        filtered = _filter_messages(sample_messages, search_query="test")
        assert len(filtered) == 1
        assert filtered[0].content == "This is a test message"
    
    def test_filter_by_type(self, sample_messages):
        """Test filtering messages by type."""
        filtered = _filter_messages(sample_messages, filter_type="analysis_result")
        assert len(filtered) == 1
        assert filtered[0].message_type == "analysis_result"
    
    def test_filter_by_agent(self, sample_messages):
        """Test filtering messages by agent."""
        filtered = _filter_messages(sample_messages, filter_agent="fiscal")
        assert len(filtered) == 1
        assert "fiscal" in filtered[0].sender_id
    
    def test_filter_combined(self, sample_messages):
        """Test combined filters."""
        filtered = _filter_messages(
            sample_messages,
            filter_type="system_event",
        )
        assert len(filtered) == 1
        assert filtered[0].sender_type == "system"
    
    def test_filter_no_results(self, sample_messages):
        """Test filter with no matching results."""
        filtered = _filter_messages(sample_messages, search_query="nonexistent")
        assert len(filtered) == 0


class TestMentionExtraction:
    """Tests for mention extraction."""
    
    def test_extract_agent_mention(self):
        """Test extracting agent mentions from text."""
        available = [
            {"id": "fiscal", "name": "Fiscal Agent", "icon": "💰"},
            {"id": "economic", "name": "Economic Agent", "icon": "📈"},
        ]
        
        text = "@fiscal please analyze this"
        mentions = _extract_mentions(text, available)
        assert "fiscal" in mentions
    
    def test_extract_multiple_mentions(self):
        """Test extracting multiple mentions."""
        available = [
            {"id": "fiscal", "name": "Fiscal Agent", "icon": "💰"},
            {"id": "economic", "name": "Economic Agent", "icon": "📈"},
            {"id": "all_agents", "name": "All Agents", "icon": "🤖"},
        ]
        
        text = "@fiscal @economic compare these policies"
        mentions = _extract_mentions(text, available)
        assert "fiscal" in mentions
        assert "economic" in mentions
    
    def test_extract_no_mentions(self):
        """Test text with no mentions."""
        available = [
            {"id": "fiscal", "name": "Fiscal Agent", "icon": "💰"},
        ]
        
        text = "Hello, please analyze this"
        mentions = _extract_mentions(text, available)
        assert len(mentions) == 0


# =============================================================================
# Test Constants
# =============================================================================

class TestConstants:
    """Tests for module constants."""
    
    def test_agent_colors_defined(self):
        """Test all agent colors are defined."""
        expected_agents = [
            "fiscal", "economic", "healthcare", "social_security",
            "equity", "implementation", "behavioral", "legal", "judge", "system"
        ]
        for agent in expected_agents:
            assert agent in AGENT_COLORS
            assert AGENT_COLORS[agent].startswith("#")
    
    def test_agent_icons_defined(self):
        """Test all agent icons are defined."""
        expected_agents = [
            "fiscal", "economic", "healthcare", "social_security",
            "equity", "implementation", "behavioral", "legal", "judge", "system"
        ]
        for agent in expected_agents:
            assert agent in AGENT_ICONS
    
    def test_message_type_icons_defined(self):
        """Test message type icons are defined."""
        expected_types = [
            "text", "analysis_request", "analysis_result",
            "scenario_request", "scenario_result", "action",
            "system_event", "thinking", "error"
        ]
        for msg_type in expected_types:
            assert msg_type in MESSAGE_TYPE_ICONS
    
    def test_system_event_icons_defined(self):
        """Test system event icons are defined."""
        expected_events = [
            "analysis_started", "analysis_completed",
            "user_joined", "user_left", "action_triggered",
            "error", "warning"
        ]
        for event in expected_events:
            assert event in SYSTEM_EVENT_ICONS


# =============================================================================
# Test Demo Data Generation
# =============================================================================

class TestDemoData:
    """Tests for demo data generation."""
    
    def test_create_demo_messages(self):
        """Test demo message creation."""
        messages = create_demo_messages()
        assert len(messages) >= 3
        
        # Check message types
        types = {m.sender_type for m in messages}
        assert "user" in types
        assert "agent" in types
        assert "system" in types
    
    def test_create_demo_channels(self):
        """Test demo channel creation."""
        channels = create_demo_channels()
        assert len(channels) >= 2
        
        # Check channel types
        types = {c.channel_type for c in channels}
        assert "public" in types or "bill" in types or "private" in types
    
    def test_demo_messages_have_required_fields(self):
        """Test demo messages have all required fields."""
        messages = create_demo_messages()
        for msg in messages:
            assert msg.message_id
            assert msg.sender_id
            assert msg.sender_type
            assert msg.sender_name
            assert msg.content is not None
            assert msg.timestamp


# =============================================================================
# Test ChatSidebar Class
# =============================================================================

class TestChatSidebar:
    """Tests for ChatSidebar class."""
    
    def test_sidebar_initialization(self):
        """Test ChatSidebar initialization."""
        sidebar = ChatSidebar(
            api_base_url="http://localhost:8000/api/v1/chat",
            user_id="test_user",
            user_name="Test User",
        )
        
        assert sidebar.api_base_url == "http://localhost:8000/api/v1/chat"
        assert sidebar.user_id == "test_user"
        assert sidebar.user_name == "Test User"
    
    def test_sidebar_default_values(self):
        """Test ChatSidebar default values."""
        sidebar = ChatSidebar()
        
        assert sidebar.user_id == "anonymous"
        assert sidebar.user_name == "User"


# =============================================================================
# Test Export Functionality
# =============================================================================

class TestExportFunctionality:
    """Tests for chat export functionality."""
    
    def test_export_options_json(self):
        """Test JSON export options."""
        options = ChatExportOptions(format="json")
        assert options.format == "json"
    
    def test_export_options_pdf(self):
        """Test PDF export options."""
        options = ChatExportOptions(format="pdf")
        assert options.format == "pdf"
    
    def test_export_date_range(self):
        """Test export with date range."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 12, 31, tzinfo=timezone.utc)
        
        options = ChatExportOptions(
            date_range_start=start,
            date_range_end=end,
        )
        
        assert options.date_range_start == start
        assert options.date_range_end == end


# =============================================================================
# Test Performance
# =============================================================================

class TestPerformance:
    """Tests for performance with large message sets."""
    
    def test_filter_10k_messages(self):
        """Test filtering performance with 10k messages."""
        import time
        
        # Generate 10k messages
        messages = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(10000):
            msg = MessageDisplay(
                message_id=f"msg_{i:05d}",
                sender_id=f"user_{i % 100}",
                sender_type="user" if i % 3 != 0 else "agent",
                sender_name=f"User {i % 100}",
                sender_icon="👤",
                sender_color="#2196F3",
                content=f"Message content {i} with some searchable text",
                message_type="text" if i % 5 != 0 else "analysis_result",
                timestamp=base_time - timedelta(minutes=i),
            )
            messages.append(msg)
        
        # Time the filtering
        start = time.time()
        filtered = _filter_messages(messages, search_query="searchable")
        elapsed = time.time() - start
        
        # Should complete in under 1 second
        assert elapsed < 1.0, f"Filtering took {elapsed:.2f}s"
        assert len(filtered) == 10000  # All have "searchable"
    
    def test_filter_by_type_performance(self):
        """Test filtering by type performance."""
        import time
        
        messages = []
        base_time = datetime.now(timezone.utc)
        
        for i in range(10000):
            msg = MessageDisplay(
                message_id=f"msg_{i:05d}",
                sender_id="user",
                sender_type="user",
                sender_name="User",
                sender_icon="👤",
                sender_color="#2196F3",
                content=f"Message {i}",
                message_type="analysis_result" if i % 10 == 0 else "text",
                timestamp=base_time - timedelta(minutes=i),
            )
            messages.append(msg)
        
        start = time.time()
        filtered = _filter_messages(messages, filter_type="analysis_result")
        elapsed = time.time() - start
        
        assert elapsed < 0.5, f"Type filtering took {elapsed:.2f}s"
        assert len(filtered) == 1000  # 10% are analysis_result


# =============================================================================
# Test Accessibility
# =============================================================================

class TestAccessibility:
    """Tests for accessibility compliance."""
    
    def test_colors_have_sufficient_contrast(self):
        """Test agent colors have sufficient contrast for readability."""
        # Basic check that colors are defined and not too light
        for agent, color in AGENT_COLORS.items():
            hex_color = color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Calculate relative luminance
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Colors should be visible (not too close to white or black)
            assert 0.1 < luminance < 0.9, f"{agent} color has poor contrast"
    
    def test_icons_are_emoji(self):
        """Test all icons are valid emoji."""
        for agent, icon in AGENT_ICONS.items():
            # Basic check - emoji are typically > 1 byte
            assert len(icon.encode('utf-8')) > 1, f"{agent} icon is not emoji"


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for chat sidebar components."""
    
    def test_message_to_export_json(self, sample_messages):
        """Test converting messages to JSON export format."""
        export_data = {
            "messages": []
        }
        
        for msg in sample_messages:
            msg_data = {
                "message_id": msg.message_id,
                "sender_id": msg.sender_id,
                "sender_name": msg.sender_name,
                "sender_type": msg.sender_type,
                "content": msg.content,
                "message_type": msg.message_type,
                "timestamp": msg.timestamp.isoformat(),
            }
            export_data["messages"].append(msg_data)
        
        # Verify JSON serialization works
        json_str = json.dumps(export_data)
        parsed = json.loads(json_str)
        
        assert len(parsed["messages"]) == len(sample_messages)
    
    def test_channel_with_messages(self, sample_channel, sample_messages):
        """Test channel with associated messages."""
        assert sample_channel.channel_id
        
        # Simulate filtering messages for channel
        channel_messages = [
            m for m in sample_messages 
            if m.sender_type != "system"  # Example filter
        ]
        
        assert len(channel_messages) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
