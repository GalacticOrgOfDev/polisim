"""
Tests for PoliSim Chat Infrastructure (Phase 7.3.1).

This module provides comprehensive tests for:
- Chat data models
- Chat API endpoints
- Chat service layer
- MCP tool integration
- Agent participation
- WebSocket functionality

Run with: pytest tests/test_chat.py -v
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture
def test_db_session():
    """Create a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from api.models import Base
    from api.chat_models import (
        ChatChannel, ChatMessage, ChatAttachment, ChatReaction,
        ChatPresence, ChannelParticipant, init_chat_tables
    )
    
    # In-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    init_chat_tables(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def chat_service(test_db_session):
    """Create a ChatService instance for testing."""
    from api.chat_api import ChatService
    return ChatService(test_db_session)


# =============================================================================
# Model Tests
# =============================================================================

class TestChatModels:
    """Tests for chat data models."""
    
    def test_channel_type_enum(self):
        """Test ChannelType enum values."""
        from api.chat_models import ChannelType
        
        assert ChannelType.PUBLIC.value == "public"
        assert ChannelType.PRIVATE.value == "private"
        assert ChannelType.GROUP.value == "group"
        assert ChannelType.BILL_SPECIFIC.value == "bill"
    
    def test_message_type_enum(self):
        """Test MessageType enum values."""
        from api.chat_models import MessageType
        
        assert MessageType.TEXT.value == "text"
        assert MessageType.ANALYSIS_REQUEST.value == "analysis_request"
        assert MessageType.ANALYSIS_RESULT.value == "analysis_result"
        assert MessageType.THINKING.value == "thinking"
    
    def test_sender_type_enum(self):
        """Test SenderType enum values."""
        from api.chat_models import SenderType
        
        assert SenderType.USER.value == "user"
        assert SenderType.AGENT.value == "agent"
        assert SenderType.SYSTEM.value == "system"
    
    def test_reaction_type_enum(self):
        """Test ReactionType emoji values."""
        from api.chat_models import ReactionType
        
        assert ReactionType.THUMBS_UP.value == "👍"
        assert ReactionType.HEART.value == "❤️"
        assert ReactionType.THINKING.value == "🤔"
    
    def test_chat_channel_creation(self, test_db_session):
        """Test ChatChannel model creation."""
        from api.chat_models import ChatChannel, ChannelType
        
        channel = ChatChannel(
            channel_id=str(uuid4()),
            name="Test Channel",
            channel_type=ChannelType.PUBLIC,
            created_by="user_123",
        )
        
        test_db_session.add(channel)
        test_db_session.commit()
        
        assert channel.id is not None
        assert channel.name == "Test Channel"
        assert channel.is_active is True
        assert channel.is_archived is False
    
    def test_chat_channel_to_dict(self, test_db_session):
        """Test ChatChannel serialization."""
        from api.chat_models import ChatChannel, ChannelType
        
        channel = ChatChannel(
            channel_id="test-channel-123",
            name="Test Channel",
            description="A test channel",
            channel_type=ChannelType.PUBLIC,
            created_by="user_123",
        )
        
        test_db_session.add(channel)
        test_db_session.commit()
        
        data = channel.to_dict()
        
        assert data["channel_id"] == "test-channel-123"
        assert data["name"] == "Test Channel"
        assert data["description"] == "A test channel"
        assert data["channel_type"] == "public"
        assert data["is_active"] is True
    
    def test_chat_message_creation(self, test_db_session):
        """Test ChatMessage model creation."""
        from api.chat_models import (
            ChatChannel, ChatMessage, ChannelType, 
            SenderType, MessageType
        )
        
        # Create channel first
        channel = ChatChannel(
            channel_id=str(uuid4()),
            name="Test Channel",
            channel_type=ChannelType.PUBLIC,
            created_by="user_123",
        )
        test_db_session.add(channel)
        test_db_session.commit()
        
        # Create message
        message = ChatMessage(
            message_id=str(uuid4()),
            channel_id=channel.id,
            sender_id="user_456",
            sender_type=SenderType.USER,
            sender_name="Test User",
            content="Hello, world!",
            message_type=MessageType.TEXT,
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        assert message.id is not None
        assert message.content == "Hello, world!"
        assert message.is_deleted is False
    
    def test_chat_message_with_mentions(self, test_db_session):
        """Test ChatMessage with @mentions."""
        from api.chat_models import (
            ChatChannel, ChatMessage, ChannelType, 
            SenderType, MessageType
        )
        
        channel = ChatChannel(
            channel_id=str(uuid4()),
            name="Test Channel",
            channel_type=ChannelType.PUBLIC,
            created_by="user_123",
        )
        test_db_session.add(channel)
        test_db_session.commit()
        
        message = ChatMessage(
            message_id=str(uuid4()),
            channel_id=channel.id,
            sender_id="user_456",
            sender_type=SenderType.USER,
            content="Hey @fiscal can you analyze this?",
            message_type=MessageType.TEXT,
            mentions=["fiscal", "healthcare"],
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        assert message.mentions == ["fiscal", "healthcare"]
    
    def test_chat_reaction_creation(self, test_db_session):
        """Test ChatReaction model creation."""
        from api.chat_models import (
            ChatChannel, ChatMessage, ChatReaction, ChannelType, 
            SenderType, MessageType, ReactionType
        )
        
        # Setup channel and message
        channel = ChatChannel(
            channel_id=str(uuid4()),
            name="Test Channel",
            channel_type=ChannelType.PUBLIC,
            created_by="user_123",
        )
        test_db_session.add(channel)
        test_db_session.commit()
        
        message = ChatMessage(
            message_id=str(uuid4()),
            channel_id=channel.id,
            sender_id="user_456",
            sender_type=SenderType.USER,
            content="Great analysis!",
            message_type=MessageType.TEXT,
        )
        test_db_session.add(message)
        test_db_session.commit()
        
        # Add reaction
        reaction = ChatReaction(
            message_id=message.id,
            user_id="user_789",
            reaction_type=ReactionType.THUMBS_UP,
        )
        test_db_session.add(reaction)
        test_db_session.commit()
        
        assert reaction.id is not None
        assert reaction.reaction_type == ReactionType.THUMBS_UP


# =============================================================================
# Service Layer Tests
# =============================================================================

class TestChatService:
    """Tests for ChatService operations."""
    
    def test_create_channel(self, chat_service):
        """Test channel creation."""
        channel = chat_service.create_channel(
            name="Budget Analysis 2026",
            created_by="user_123",
            channel_type="public",
            description="Discuss budget proposals",
        )
        
        assert channel is not None
        assert channel.name == "Budget Analysis 2026"
        assert channel.created_by == "user_123"
    
    def test_create_private_channel(self, chat_service):
        """Test private channel creation."""
        channel = chat_service.create_channel(
            name="Private Discussion",
            created_by="user_123",
            channel_type="private",
        )
        
        assert channel.channel_type.value == "private"
    
    def test_get_channel(self, chat_service):
        """Test channel retrieval."""
        created = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        fetched = chat_service.get_channel(created.channel_id)
        
        assert fetched is not None
        assert fetched.channel_id == created.channel_id
    
    def test_get_nonexistent_channel(self, chat_service):
        """Test retrieval of nonexistent channel."""
        channel = chat_service.get_channel("nonexistent-id")
        assert channel is None
    
    def test_list_public_channels(self, chat_service):
        """Test listing public channels."""
        # Create multiple channels
        chat_service.create_channel(name="Channel 1", created_by="user_123")
        chat_service.create_channel(name="Channel 2", created_by="user_456")
        
        channels = chat_service.list_channels(user_id="user_789")
        
        assert len(channels) >= 2
    
    def test_send_message(self, chat_service):
        """Test sending a message."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        message = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="Hello, everyone!",
        )
        
        assert message is not None
        assert message.content == "Hello, everyone!"
    
    def test_send_message_to_invalid_channel(self, chat_service):
        """Test sending message to invalid channel."""
        message = chat_service.send_message(
            channel_id="invalid-channel",
            sender_id="user_123",
            content="Hello",
        )
        
        assert message is None
    
    def test_get_messages(self, chat_service):
        """Test retrieving messages."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        # Send multiple messages
        for i in range(5):
            chat_service.send_message(
                channel_id=channel.channel_id,
                sender_id="user_123",
                content=f"Message {i}",
            )
        
        messages = chat_service.get_messages(channel.channel_id, limit=10)
        
        assert len(messages) == 5
    
    def test_delete_message(self, chat_service):
        """Test message deletion."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        message = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="Delete me!",
        )
        
        success = chat_service.delete_message(message.message_id, "user_123")
        
        assert success is True
    
    def test_add_agent_to_channel(self, chat_service):
        """Test adding an agent to a channel."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        participant = chat_service.add_agent_to_channel(
            channel_id=channel.channel_id,
            agent_id="fiscal",
            added_by="user_123",
        )
        
        assert participant is not None
        assert participant.participant_id == "fiscal"
    
    def test_remove_agent_from_channel(self, chat_service):
        """Test removing an agent from a channel."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        chat_service.add_agent_to_channel(
            channel_id=channel.channel_id,
            agent_id="fiscal",
            added_by="user_123",
        )
        
        success = chat_service.remove_agent_from_channel(
            channel_id=channel.channel_id,
            agent_id="fiscal",
            removed_by="user_123",
        )
        
        assert success is True
    
    def test_add_reaction(self, chat_service):
        """Test adding a reaction."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        message = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="React to this!",
        )
        
        reaction = chat_service.add_reaction(
            message_id=message.message_id,
            user_id="user_456",
            reaction="👍",
        )
        
        assert reaction is not None
    
    def test_search_messages(self, chat_service):
        """Test message search."""
        channel = chat_service.create_channel(
            name="Test Channel",
            created_by="user_123",
        )
        
        chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="Healthcare reform analysis",
        )
        
        chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="Budget projections",
        )
        
        results = chat_service.search_messages(
            user_id="user_123",
            query="healthcare",
        )
        
        assert len(results) >= 1
        assert "healthcare" in results[0].content.lower()


# =============================================================================
# MCP Tools Tests
# =============================================================================

class TestChatMCPTools:
    """Tests for chat MCP tools."""
    
    @pytest.fixture
    def mcp_tools(self):
        """Create MCP tools instance."""
        from api.chat_mcp_tools import ChatMCPTools
        return ChatMCPTools()
    
    def test_tool_definitions(self, mcp_tools):
        """Test that all tools are defined."""
        tools = mcp_tools.get_tool_definitions()
        
        tool_names = [t["name"] for t in tools]
        
        assert "analyze_bill" in tool_names
        assert "run_scenario" in tool_names
        assert "compare_policies" in tool_names
        assert "query_cbo_data" in tool_names
        assert "send_chat_message" in tool_names
        assert "get_channel_context" in tool_names
    
    @pytest.mark.asyncio
    async def test_analyze_bill_returns_result(self, mcp_tools):
        """Test analyze_bill returns an AnalysisResult."""
        result = await mcp_tools.analyze_bill(
            bill_id="HR1234",
            focus_areas=["revenue", "spending"],
        )
        
        assert result is not None
        assert result.bill_id == "HR1234"
        assert result.status in ["completed", "pending", "failed"]
    
    @pytest.mark.asyncio
    async def test_run_scenario_returns_result(self, mcp_tools):
        """Test run_scenario returns a ScenarioResult."""
        result = await mcp_tools.run_scenario(
            scenario_type="recession",
            years=10,
        )
        
        assert result is not None
        assert result.scenario_name == "recession"
    
    @pytest.mark.asyncio
    async def test_compare_policies_requires_two(self, mcp_tools):
        """Test compare_policies requires at least 2 policies."""
        result = await mcp_tools.compare_policies(
            policy_ids=["policy_1"],
        )
        
        assert "error" in result.differences[0]
    
    @pytest.mark.asyncio
    async def test_query_cbo_data(self, mcp_tools):
        """Test CBO data query."""
        result = await mcp_tools.query_cbo_data(
            metric="total_revenue",
            start_year=2026,
            end_year=2030,
        )
        
        assert result is not None
        assert result.metric == "total_revenue"
        assert len(result.years) > 0


# =============================================================================
# Agent Participation Tests
# =============================================================================

class TestAgentParticipation:
    """Tests for agent chat participation."""
    
    def test_message_analysis_detects_mentions(self):
        """Test that message analysis detects @mentions."""
        from api.chat_agent_participation import analyze_message, DEFAULT_AGENTS
        
        analysis = analyze_message(
            "@fiscal can you analyze this bill?",
            DEFAULT_AGENTS,
        )
        
        assert len(analysis.mentions) == 1
        assert analysis.mentions[0].agent_id == "fiscal"
    
    def test_message_analysis_detects_questions(self):
        """Test that message analysis detects questions."""
        from api.chat_agent_participation import analyze_message, DEFAULT_AGENTS
        
        analysis = analyze_message(
            "What is the projected deficit for 2030?",
            DEFAULT_AGENTS,
        )
        
        assert analysis.is_question is True
    
    def test_message_analysis_detects_bill_mentions(self):
        """Test that message analysis detects bill mentions."""
        from api.chat_agent_participation import analyze_message, DEFAULT_AGENTS
        
        analysis = analyze_message(
            "Can you analyze HR1234?",
            DEFAULT_AGENTS,
        )
        
        assert analysis.bill_mentioned is not None
        assert "1234" in analysis.bill_mentioned
    
    def test_message_analysis_detects_topics(self):
        """Test that message analysis identifies topics."""
        from api.chat_agent_participation import analyze_message, DEFAULT_AGENTS
        
        analysis = analyze_message(
            "What's the medicare spending projection?",
            DEFAULT_AGENTS,
        )
        
        assert len(analysis.topics) > 0
    
    def test_agent_chat_manager_initialization(self):
        """Test AgentChatManager initialization."""
        from api.chat_agent_participation import AgentChatManager
        
        manager = AgentChatManager()
        
        assert manager is not None
        assert len(manager.agents) > 0
    
    def test_agent_info_retrieval(self):
        """Test getting agent information."""
        from api.chat_agent_participation import AgentChatManager
        
        manager = AgentChatManager()
        info = manager.get_agent_info("fiscal")
        
        assert info is not None
        assert info["agent_id"] == "fiscal"
        assert "specialty" in info
    
    def test_list_available_agents(self):
        """Test listing available agents."""
        from api.chat_agent_participation import AgentChatManager
        
        manager = AgentChatManager()
        agents = manager.list_available_agents()
        
        assert len(agents) >= 4  # Tier 1 agents


# =============================================================================
# WebSocket Tests
# =============================================================================

class TestChatWebSocket:
    """Tests for chat WebSocket functionality."""
    
    def test_chat_event_serialization(self):
        """Test ChatEvent JSON serialization."""
        from api.chat_websocket import ChatEvent
        
        event = ChatEvent(
            event_type="new_message",
            channel_id="test-channel",
            data={"content": "Hello"},
        )
        
        json_str = event.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["event_type"] == "new_message"
        assert parsed["channel_id"] == "test-channel"
    
    def test_chat_event_deserialization(self):
        """Test ChatEvent JSON deserialization."""
        from api.chat_websocket import ChatEvent
        
        json_str = json.dumps({
            "event_type": "new_message",
            "channel_id": "test-channel",
            "data": {"content": "Hello"},
        })
        
        event = ChatEvent.from_json(json_str)
        
        assert event.event_type == "new_message"
        assert event.channel_id == "test-channel"
    
    def test_websocket_manager_initialization(self):
        """Test ChatWebSocketManager initialization."""
        from api.chat_websocket import ChatWebSocketManager
        
        manager = ChatWebSocketManager()
        
        assert manager is not None
        assert manager.stats["total_connections"] == 0
    
    def test_presence_info_creation(self):
        """Test PresenceInfo creation."""
        from api.chat_websocket import PresenceInfo
        
        presence = PresenceInfo(
            participant_id="user_123",
            participant_type="user",
            status="online",
        )
        
        assert presence.status == "online"
        assert presence.is_typing is False


# =============================================================================
# Integration Tests
# =============================================================================

class TestChatIntegration:
    """Integration tests for chat functionality."""
    
    @pytest.mark.asyncio
    async def test_full_message_flow(self, chat_service):
        """Test complete message flow from send to retrieve."""
        # Create channel
        channel = chat_service.create_channel(
            name="Integration Test",
            created_by="user_123",
        )
        
        # Send messages
        msg1 = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="First message",
        )
        
        msg2 = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_456",
            content="Reply to first",
        )
        
        # Add reaction
        chat_service.add_reaction(
            message_id=msg1.message_id,
            user_id="user_456",
            reaction="thumbs_up",
        )
        
        # Retrieve and verify
        messages = chat_service.get_messages(channel.channel_id)
        
        assert len(messages) == 2
    
    @pytest.mark.asyncio
    async def test_agent_in_channel_flow(self, chat_service):
        """Test adding agent and getting responses."""
        # Create channel
        channel = chat_service.create_channel(
            name="Agent Test",
            created_by="user_123",
        )
        
        # Add agent
        participant = chat_service.add_agent_to_channel(
            channel_id=channel.channel_id,
            agent_id="fiscal",
            added_by="user_123",
        )
        
        # Check agents
        agents = chat_service.get_channel_agents(channel.channel_id)
        
        assert len(agents) >= 1
        assert any(a.participant_id == "fiscal" for a in agents)
    
    @pytest.mark.asyncio
    async def test_message_with_analysis_request(self, chat_service):
        """Test sending an analysis request message."""
        channel = chat_service.create_channel(
            name="Analysis Test",
            created_by="user_123",
        )
        
        message = chat_service.send_message(
            channel_id=channel.channel_id,
            sender_id="user_123",
            content="@fiscal please analyze HR1234",
            message_type="analysis_request",
            metadata={"bill_id": "HR1234"},
        )
        
        assert message is not None
        assert message.message_type.value == "analysis_request"
        assert message.metadata["bill_id"] == "HR1234"


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
