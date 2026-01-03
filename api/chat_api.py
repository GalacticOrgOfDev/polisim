"""
Chat API Endpoints for PoliSim Chatroom (Phase 7.3.1).

This module provides RESTful API endpoints for chat functionality,
enabling channel management, messaging, and agent integration.

Endpoints:
    POST   /api/v1/chat/channels              - Create channel
    GET    /api/v1/chat/channels              - List user's channels
    GET    /api/v1/chat/channels/{id}         - Get channel details
    DELETE /api/v1/chat/channels/{id}         - Delete channel
    
    POST   /api/v1/chat/channels/{id}/messages  - Send message
    GET    /api/v1/chat/channels/{id}/messages  - Get message history
    DELETE /api/v1/chat/messages/{id}           - Delete message
    
    POST   /api/v1/chat/channels/{id}/agents    - Add agent to channel
    DELETE /api/v1/chat/channels/{id}/agents/{agent_id}  - Remove agent

Example:
    from api.chat_api import create_chat_blueprint
    
    chat_bp = create_chat_blueprint()
    app.register_blueprint(chat_bp, url_prefix='/api/v1/chat')
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

try:
    from flask import Blueprint, request, jsonify, g
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    Blueprint = None

from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session

from api.chat_models import (
    ChatChannel, ChatMessage, ChatAttachment, ChatReaction, ChatPresence,
    ChannelParticipant, ChannelType, SenderType, MessageType,
    ParticipantRole, ReactionType, init_chat_tables
)
from api.database import get_db_session


logger = logging.getLogger(__name__)


# =============================================================================
# Pydantic Request/Response Models
# =============================================================================

class CreateChannelRequest(BaseModel):
    """Request to create a new chat channel."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    channel_type: str = Field(default="public")
    icon: Optional[str] = Field(None, max_length=50)
    bill_id: Optional[str] = Field(None, max_length=50)
    settings: Optional[Dict[str, Any]] = None
    
    @field_validator('channel_type')
    @classmethod
    def validate_channel_type(cls, v):
        valid_types = ['public', 'private', 'group', 'bill']
        if v not in valid_types:
            raise ValueError(f'channel_type must be one of {valid_types}')
        return v


class SendMessageRequest(BaseModel):
    """Request to send a message to a channel."""
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: str = Field(default="text")
    metadata: Optional[Dict[str, Any]] = None
    thread_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    mentions: Optional[List[str]] = None
    
    @field_validator('message_type')
    @classmethod
    def validate_message_type(cls, v):
        valid_types = ['text', 'analysis_request', 'scenario_request', 'action']
        if v not in valid_types:
            raise ValueError(f'message_type must be one of {valid_types}')
        return v


class AddAgentRequest(BaseModel):
    """Request to add an AI agent to a channel."""
    agent_id: str = Field(..., min_length=1, max_length=50)
    agent_type: str = Field(default="fiscal")  # fiscal, healthcare, economic, etc.


class AddReactionRequest(BaseModel):
    """Request to add a reaction to a message."""
    reaction: str = Field(..., min_length=1, max_length=10)


class UpdatePresenceRequest(BaseModel):
    """Request to update user/agent presence."""
    status: str = Field(default="online")
    is_typing: bool = False
    typing_in_channel: Optional[str] = None
    agent_status: Optional[str] = None
    agent_status_detail: Optional[str] = None


# =============================================================================
# Chat Service Layer
# =============================================================================

class ChatService:
    """Service layer for chat operations.
    
    Handles business logic for channels, messages, and participants,
    abstracting database operations from API endpoints.
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    # -------------------------------------------------------------------------
    # Channel Operations
    # -------------------------------------------------------------------------
    
    def create_channel(
        self,
        name: str,
        created_by: str,
        channel_type: str = "public",
        description: Optional[str] = None,
        icon: Optional[str] = None,
        bill_id: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> ChatChannel:
        """Create a new chat channel."""
        channel_id = str(uuid4())
        
        # Map string to enum
        type_map = {
            "public": ChannelType.PUBLIC,
            "private": ChannelType.PRIVATE,
            "group": ChannelType.GROUP,
            "bill": ChannelType.BILL_SPECIFIC,
        }
        ch_type = type_map.get(channel_type, ChannelType.PUBLIC)
        
        channel = ChatChannel(
            channel_id=channel_id,
            name=name,
            description=description,
            channel_type=ch_type,
            icon=icon,
            created_by=created_by,
            bill_id=bill_id,
            settings=settings or {},
        )
        self.session.add(channel)
        # Flush to get the auto-generated channel.id before creating participant
        self.session.flush()
        
        # Add creator as owner
        participant = ChannelParticipant(
            channel_id=channel.id,
            participant_id=created_by,
            participant_type=SenderType.USER,
            role=ParticipantRole.OWNER,
        )
        self.session.add(participant)
        self.session.commit()
        
        logger.info(f"Created channel {channel_id}: {name}")
        return channel
    
    def get_channel(self, channel_id: str) -> Optional[ChatChannel]:
        """Get channel by ID."""
        return self.session.query(ChatChannel).filter(
            ChatChannel.channel_id == channel_id,
            ChatChannel.is_active == True
        ).first()
    
    def list_channels(
        self,
        user_id: str,
        channel_type: Optional[str] = None,
        include_public: bool = True,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatChannel]:
        """List channels accessible to user."""
        query = self.session.query(ChatChannel).filter(
            ChatChannel.is_active == True,
            ChatChannel.is_archived == False
        )
        
        # Filter by type if specified
        if channel_type:
            type_map = {
                "public": ChannelType.PUBLIC,
                "private": ChannelType.PRIVATE,
                "group": ChannelType.GROUP,
                "bill": ChannelType.BILL_SPECIFIC,
            }
            if channel_type in type_map:
                query = query.filter(ChatChannel.channel_type == type_map[channel_type])
        
        # For MVP: return all public channels + user's private channels
        if include_public:
            query = query.filter(
                or_(
                    ChatChannel.channel_type == ChannelType.PUBLIC,
                    ChatChannel.created_by == user_id,
                    ChatChannel.participants.any(
                        ChannelParticipant.participant_id == user_id
                    )
                )
            )
        else:
            # Only user's channels
            query = query.filter(
                or_(
                    ChatChannel.created_by == user_id,
                    ChatChannel.participants.any(
                        ChannelParticipant.participant_id == user_id
                    )
                )
            )
        
        return query.order_by(desc(ChatChannel.last_message_at)).offset(offset).limit(limit).all()
    
    def delete_channel(self, channel_id: str, user_id: str) -> bool:
        """Delete (soft) a channel. Only owner can delete."""
        channel = self.get_channel(channel_id)
        if not channel:
            return False
        
        # Check ownership
        if channel.created_by != user_id:
            raise PermissionError("Only channel owner can delete")
        
        channel.is_active = False
        channel.is_archived = True
        self.session.commit()
        
        logger.info(f"Deleted channel {channel_id} by user {user_id}")
        return True
    
    # -------------------------------------------------------------------------
    # Message Operations
    # -------------------------------------------------------------------------
    
    def send_message(
        self,
        channel_id: str,
        sender_id: str,
        content: str,
        sender_type: str = "user",
        sender_name: Optional[str] = None,
        message_type: str = "text",
        message_metadata: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
        reply_to_id: Optional[str] = None,
        mentions: Optional[List[str]] = None
    ) -> Optional[ChatMessage]:
        """Send a message to a channel."""
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        
        message_id = str(uuid4())
        
        # Map string to enum
        sender_type_map = {
            "user": SenderType.USER,
            "agent": SenderType.AGENT,
            "system": SenderType.SYSTEM,
        }
        msg_type_map = {
            "text": MessageType.TEXT,
            "analysis_request": MessageType.ANALYSIS_REQUEST,
            "analysis_result": MessageType.ANALYSIS_RESULT,
            "scenario_request": MessageType.SCENARIO_REQUEST,
            "scenario_result": MessageType.SCENARIO_RESULT,
            "action": MessageType.ACTION,
            "system_event": MessageType.SYSTEM_EVENT,
            "thinking": MessageType.THINKING,
            "error": MessageType.ERROR,
        }
        
        message = ChatMessage(
            message_id=message_id,
            channel_id=channel.id,
            sender_id=sender_id,
            sender_type=sender_type_map.get(sender_type, SenderType.USER),
            sender_name=sender_name,
            content=content,
            message_type=msg_type_map.get(message_type, MessageType.TEXT),
            message_metadata=message_metadata,
            thread_id=thread_id,
            reply_to_id=reply_to_id,
            mentions=mentions,
        )
        self.session.add(message)
        
        # Update channel last_message_at
        channel.last_message_at = datetime.now(timezone.utc)
        
        # Update unread counts for other participants
        for participant in channel.participants:
            if participant.participant_id != sender_id:
                participant.unread_count += 1
        
        self.session.commit()
        
        logger.debug(f"Message {message_id} sent to channel {channel_id}")
        return message
    
    def get_messages(
        self,
        channel_id: str,
        limit: int = 50,
        before_id: Optional[str] = None,
        after_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> List[ChatMessage]:
        """Get messages from a channel with pagination."""
        channel = self.get_channel(channel_id)
        if not channel:
            return []
        
        query = self.session.query(ChatMessage).filter(
            ChatMessage.channel_id == channel.id,
            ChatMessage.is_deleted == False
        )
        
        # Filter by thread if specified
        if thread_id:
            query = query.filter(ChatMessage.thread_id == thread_id)
        
        # Pagination: before a specific message
        if before_id:
            before_msg = self.session.query(ChatMessage).filter(
                ChatMessage.message_id == before_id
            ).first()
            if before_msg:
                query = query.filter(ChatMessage.created_at < before_msg.created_at)
        
        # Pagination: after a specific message
        if after_id:
            after_msg = self.session.query(ChatMessage).filter(
                ChatMessage.message_id == after_id
            ).first()
            if after_msg:
                query = query.filter(ChatMessage.created_at > after_msg.created_at)
        
        return query.order_by(desc(ChatMessage.created_at)).limit(limit).all()
    
    def delete_message(self, message_id: str, user_id: str) -> bool:
        """Delete (soft) a message. Only sender can delete."""
        message = self.session.query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()
        
        if not message:
            return False
        
        # Check ownership (sender or channel owner)
        if message.sender_id != user_id:
            channel = self.session.query(ChatChannel).get(message.channel_id)
            if channel and channel.created_by != user_id:
                raise PermissionError("Only message sender or channel owner can delete")
        
        message.is_deleted = True
        message.content = "[Message deleted]"
        self.session.commit()
        
        logger.debug(f"Message {message_id} deleted by {user_id}")
        return True
    
    def search_messages(
        self,
        user_id: str,
        query: str,
        channel_id: Optional[str] = None,
        limit: int = 50
    ) -> List[ChatMessage]:
        """Search messages by content."""
        msg_query = self.session.query(ChatMessage).filter(
            ChatMessage.content.ilike(f'%{query}%'),
            ChatMessage.is_deleted == False
        )
        
        if channel_id:
            channel = self.get_channel(channel_id)
            if channel:
                msg_query = msg_query.filter(ChatMessage.channel_id == channel.id)
        
        return msg_query.order_by(desc(ChatMessage.created_at)).limit(limit).all()
    
    # -------------------------------------------------------------------------
    # Agent Operations
    # -------------------------------------------------------------------------
    
    def add_agent_to_channel(
        self,
        channel_id: str,
        agent_id: str,
        added_by: str
    ) -> Optional[ChannelParticipant]:
        """Add an AI agent to a channel."""
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        
        # Check if agent already in channel
        existing = self.session.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == channel.id,
            ChannelParticipant.participant_id == agent_id
        ).first()
        
        if existing:
            return existing
        
        participant = ChannelParticipant(
            channel_id=channel.id,
            participant_id=agent_id,
            participant_type=SenderType.AGENT,
            role=ParticipantRole.MEMBER,
        )
        self.session.add(participant)
        
        # Send system message
        self.send_message(
            channel_id=channel_id,
            sender_id="system",
            sender_type="system",
            content=f"Agent @{agent_id} has joined the channel",
            message_type="system_event",
            message_metadata={"event": "agent_joined", "agent_id": agent_id, "added_by": added_by}
        )
        
        self.session.commit()
        logger.info(f"Agent {agent_id} added to channel {channel_id}")
        return participant
    
    def remove_agent_from_channel(
        self,
        channel_id: str,
        agent_id: str,
        removed_by: str
    ) -> bool:
        """Remove an AI agent from a channel."""
        channel = self.get_channel(channel_id)
        if not channel:
            return False
        
        participant = self.session.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == channel.id,
            ChannelParticipant.participant_id == agent_id,
            ChannelParticipant.participant_type == SenderType.AGENT
        ).first()
        
        if not participant:
            return False
        
        participant.left_at = datetime.now(timezone.utc)
        
        # Send system message
        self.send_message(
            channel_id=channel_id,
            sender_id="system",
            sender_type="system",
            content=f"Agent @{agent_id} has left the channel",
            message_type="system_event",
            message_metadata={"event": "agent_left", "agent_id": agent_id, "removed_by": removed_by}
        )
        
        self.session.delete(participant)
        self.session.commit()
        
        logger.info(f"Agent {agent_id} removed from channel {channel_id}")
        return True
    
    def get_channel_agents(self, channel_id: str) -> List[ChannelParticipant]:
        """Get all agents in a channel."""
        channel = self.get_channel(channel_id)
        if not channel:
            return []
        
        return self.session.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == channel.id,
            ChannelParticipant.participant_type == SenderType.AGENT,
            ChannelParticipant.left_at == None
        ).all()
    
    # -------------------------------------------------------------------------
    # Reaction Operations
    # -------------------------------------------------------------------------
    
    def add_reaction(
        self,
        message_id: str,
        user_id: str,
        reaction: str
    ) -> Optional[ChatReaction]:
        """Add a reaction to a message."""
        message = self.session.query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()
        
        if not message:
            return None
        
        # Map reaction string to enum
        reaction_map = {
            "👍": ReactionType.THUMBS_UP,
            "thumbs_up": ReactionType.THUMBS_UP,
            "👎": ReactionType.THUMBS_DOWN,
            "thumbs_down": ReactionType.THUMBS_DOWN,
            "❤️": ReactionType.HEART,
            "heart": ReactionType.HEART,
            "🤔": ReactionType.THINKING,
            "thinking": ReactionType.THINKING,
            "🎉": ReactionType.CELEBRATE,
            "celebrate": ReactionType.CELEBRATE,
            "⚠️": ReactionType.WARNING,
            "warning": ReactionType.WARNING,
            "✅": ReactionType.CHECK,
            "check": ReactionType.CHECK,
            "❓": ReactionType.QUESTION,
            "question": ReactionType.QUESTION,
        }
        
        reaction_type = reaction_map.get(reaction)
        if not reaction_type:
            return None
        
        # Check if user already reacted with this type
        existing = self.session.query(ChatReaction).filter(
            ChatReaction.message_id == message.id,
            ChatReaction.user_id == user_id,
            ChatReaction.reaction_type == reaction_type
        ).first()
        
        if existing:
            return existing
        
        chat_reaction = ChatReaction(
            message_id=message.id,
            user_id=user_id,
            reaction_type=reaction_type,
        )
        self.session.add(chat_reaction)
        self.session.commit()
        
        return chat_reaction
    
    def remove_reaction(
        self,
        message_id: str,
        user_id: str,
        reaction: str
    ) -> bool:
        """Remove a reaction from a message."""
        message = self.session.query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()
        
        if not message:
            return False
        
        # Map reaction string to enum (same as add_reaction)
        reaction_map = {
            "👍": ReactionType.THUMBS_UP,
            "thumbs_up": ReactionType.THUMBS_UP,
            "👎": ReactionType.THUMBS_DOWN,
            "thumbs_down": ReactionType.THUMBS_DOWN,
            "❤️": ReactionType.HEART,
            "heart": ReactionType.HEART,
            "🤔": ReactionType.THINKING,
            "thinking": ReactionType.THINKING,
            "🎉": ReactionType.CELEBRATE,
            "celebrate": ReactionType.CELEBRATE,
            "⚠️": ReactionType.WARNING,
            "warning": ReactionType.WARNING,
            "✅": ReactionType.CHECK,
            "check": ReactionType.CHECK,
            "❓": ReactionType.QUESTION,
            "question": ReactionType.QUESTION,
        }
        
        reaction_type = reaction_map.get(reaction)
        if not reaction_type:
            return False
        
        existing = self.session.query(ChatReaction).filter(
            ChatReaction.message_id == message.id,
            ChatReaction.user_id == user_id,
            ChatReaction.reaction_type == reaction_type
        ).first()
        
        if not existing:
            return False
        
        self.session.delete(existing)
        self.session.commit()
        return True
    
    # -------------------------------------------------------------------------
    # Presence Operations
    # -------------------------------------------------------------------------
    
    def update_presence(
        self,
        participant_id: str,
        participant_type: str = "user",
        status: str = "online",
        current_channel_id: Optional[str] = None,
        is_typing: bool = False,
        typing_in_channel: Optional[str] = None,
        agent_status: Optional[str] = None,
        agent_status_detail: Optional[str] = None
    ) -> ChatPresence:
        """Update user/agent presence."""
        type_map = {
            "user": SenderType.USER,
            "agent": SenderType.AGENT,
        }
        p_type = type_map.get(participant_type, SenderType.USER)
        
        presence = self.session.query(ChatPresence).filter(
            ChatPresence.participant_id == participant_id,
            ChatPresence.participant_type == p_type
        ).first()
        
        if not presence:
            presence = ChatPresence(
                participant_id=participant_id,
                participant_type=p_type,
            )
            self.session.add(presence)
        
        presence.status = status
        presence.current_channel_id = current_channel_id
        presence.is_typing = is_typing
        presence.typing_in_channel = typing_in_channel
        presence.agent_status = agent_status
        presence.agent_status_detail = agent_status_detail
        presence.last_seen = datetime.now(timezone.utc)
        
        if is_typing and not presence.typing_started:
            presence.typing_started = datetime.now(timezone.utc)
        elif not is_typing:
            presence.typing_started = None
        
        self.session.commit()
        return presence
    
    def get_channel_presence(self, channel_id: str) -> List[ChatPresence]:
        """Get presence info for users in a channel."""
        return self.session.query(ChatPresence).filter(
            ChatPresence.current_channel_id == channel_id
        ).all()
    
    def mark_messages_read(self, channel_id: str, user_id: str) -> bool:
        """Mark all messages in channel as read for user."""
        channel = self.get_channel(channel_id)
        if not channel:
            return False
        
        participant = self.session.query(ChannelParticipant).filter(
            ChannelParticipant.channel_id == channel.id,
            ChannelParticipant.participant_id == user_id
        ).first()
        
        if participant:
            # Get last message ID
            last_message = self.session.query(ChatMessage).filter(
                ChatMessage.channel_id == channel.id
            ).order_by(desc(ChatMessage.created_at)).first()
            
            if last_message:
                participant.last_read_message_id = last_message.id
            participant.unread_count = 0
            self.session.commit()
            return True
        return False


# =============================================================================
# Flask Blueprint
# =============================================================================

def create_chat_blueprint() -> "Blueprint":
    """Create Flask blueprint for chat API endpoints."""
    if not HAS_FLASK:
        raise ImportError("Flask required for chat API. Install with: pip install flask")
    
    bp = Blueprint('chat', __name__)
    
    def get_current_user_id() -> str:
        """Get current user ID from request context.
        
        In production, this would come from JWT/session.
        For MVP, we use a header or default.
        """
        return request.headers.get('X-User-Id', 'anonymous')
    
    def get_chat_service() -> ChatService:
        """Get chat service instance."""
        with get_db_session() as session:
            return ChatService(session)
    
    # -------------------------------------------------------------------------
    # Channel Endpoints
    # -------------------------------------------------------------------------
    
    @bp.route('/channels', methods=['POST'])
    def create_channel():
        """Create a new chat channel."""
        try:
            data = CreateChannelRequest(**request.get_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            channel = service.create_channel(
                name=data.name,
                created_by=user_id,
                channel_type=data.channel_type,
                description=data.description,
                icon=data.icon,
                bill_id=data.bill_id,
                settings=data.settings,
            )
            return jsonify(channel.to_dict(include_participants=True)), 201
    
    @bp.route('/channels', methods=['GET'])
    def list_channels():
        """List channels accessible to user."""
        user_id = get_current_user_id()
        channel_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        with get_db_session() as session:
            service = ChatService(session)
            channels = service.list_channels(
                user_id=user_id,
                channel_type=channel_type,
                limit=limit,
                offset=offset,
            )
            return jsonify({
                "channels": [c.to_dict() for c in channels],
                "total": len(channels),
                "limit": limit,
                "offset": offset,
            })
    
    @bp.route('/channels/<channel_id>', methods=['GET'])
    def get_channel(channel_id: str):
        """Get channel details."""
        with get_db_session() as session:
            service = ChatService(session)
            channel = service.get_channel(channel_id)
            if not channel:
                return jsonify({"error": "Channel not found"}), 404
            return jsonify(channel.to_dict(include_participants=True))
    
    @bp.route('/channels/<channel_id>', methods=['DELETE'])
    def delete_channel(channel_id: str):
        """Delete a channel."""
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            try:
                success = service.delete_channel(channel_id, user_id)
                if not success:
                    return jsonify({"error": "Channel not found"}), 404
                return jsonify({"success": True})
            except PermissionError as e:
                return jsonify({"error": str(e)}), 403
    
    # -------------------------------------------------------------------------
    # Message Endpoints
    # -------------------------------------------------------------------------
    
    @bp.route('/channels/<channel_id>/messages', methods=['POST'])
    def send_message(channel_id: str):
        """Send a message to a channel."""
        try:
            data = SendMessageRequest(**request.get_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        user_id = get_current_user_id()
        user_name = request.headers.get('X-User-Name')
        
        with get_db_session() as session:
            service = ChatService(session)
            message = service.send_message(
                channel_id=channel_id,
                sender_id=user_id,
                sender_name=user_name,
                content=data.content,
                message_type=data.message_type,
                message_metadata=data.metadata,
                thread_id=data.thread_id,
                reply_to_id=data.reply_to_id,
                mentions=data.mentions,
            )
            if not message:
                return jsonify({"error": "Channel not found"}), 404
            return jsonify(message.to_dict()), 201
    
    @bp.route('/channels/<channel_id>/messages', methods=['GET'])
    def get_messages(channel_id: str):
        """Get message history for a channel."""
        limit = int(request.args.get('limit', 50))
        before_id = request.args.get('before')
        after_id = request.args.get('after')
        thread_id = request.args.get('thread')
        
        with get_db_session() as session:
            service = ChatService(session)
            messages = service.get_messages(
                channel_id=channel_id,
                limit=limit,
                before_id=before_id,
                after_id=after_id,
                thread_id=thread_id,
            )
            # Reverse to get chronological order
            messages.reverse()
            return jsonify({
                "messages": [m.to_dict() for m in messages],
                "total": len(messages),
            })
    
    @bp.route('/messages/<message_id>', methods=['DELETE'])
    def delete_message(message_id: str):
        """Delete a message."""
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            try:
                success = service.delete_message(message_id, user_id)
                if not success:
                    return jsonify({"error": "Message not found"}), 404
                return jsonify({"success": True})
            except PermissionError as e:
                return jsonify({"error": str(e)}), 403
    
    @bp.route('/messages/search', methods=['GET'])
    def search_messages():
        """Search messages."""
        user_id = get_current_user_id()
        query = request.args.get('q', '')
        channel_id = request.args.get('channel')
        limit = int(request.args.get('limit', 50))
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        with get_db_session() as session:
            service = ChatService(session)
            messages = service.search_messages(
                user_id=user_id,
                query=query,
                channel_id=channel_id,
                limit=limit,
            )
            return jsonify({
                "messages": [m.to_dict() for m in messages],
                "total": len(messages),
                "query": query,
            })
    
    # -------------------------------------------------------------------------
    # Agent Endpoints
    # -------------------------------------------------------------------------
    
    @bp.route('/channels/<channel_id>/agents', methods=['POST'])
    def add_agent(channel_id: str):
        """Add an AI agent to a channel."""
        try:
            data = AddAgentRequest(**request.get_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            participant = service.add_agent_to_channel(
                channel_id=channel_id,
                agent_id=data.agent_id,
                added_by=user_id,
            )
            if not participant:
                return jsonify({"error": "Channel not found"}), 404
            return jsonify(participant.to_dict()), 201
    
    @bp.route('/channels/<channel_id>/agents/<agent_id>', methods=['DELETE'])
    def remove_agent(channel_id: str, agent_id: str):
        """Remove an AI agent from a channel."""
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            success = service.remove_agent_from_channel(
                channel_id=channel_id,
                agent_id=agent_id,
                removed_by=user_id,
            )
            if not success:
                return jsonify({"error": "Agent not found in channel"}), 404
            return jsonify({"success": True})
    
    @bp.route('/channels/<channel_id>/agents', methods=['GET'])
    def list_agents(channel_id: str):
        """List AI agents in a channel."""
        with get_db_session() as session:
            service = ChatService(session)
            agents = service.get_channel_agents(channel_id)
            return jsonify({
                "agents": [a.to_dict() for a in agents],
                "total": len(agents),
            })
    
    # -------------------------------------------------------------------------
    # Reaction Endpoints
    # -------------------------------------------------------------------------
    
    @bp.route('/messages/<message_id>/reactions', methods=['POST'])
    def add_reaction(message_id: str):
        """Add a reaction to a message."""
        try:
            data = AddReactionRequest(**request.get_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            reaction = service.add_reaction(
                message_id=message_id,
                user_id=user_id,
                reaction=data.reaction,
            )
            if not reaction:
                return jsonify({"error": "Message not found or invalid reaction"}), 404
            return jsonify(reaction.to_dict()), 201
    
    @bp.route('/messages/<message_id>/reactions/<reaction>', methods=['DELETE'])
    def remove_reaction(message_id: str, reaction: str):
        """Remove a reaction from a message."""
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            success = service.remove_reaction(
                message_id=message_id,
                user_id=user_id,
                reaction=reaction,
            )
            if not success:
                return jsonify({"error": "Reaction not found"}), 404
            return jsonify({"success": True})
    
    # -------------------------------------------------------------------------
    # Presence Endpoints
    # -------------------------------------------------------------------------
    
    @bp.route('/presence', methods=['POST'])
    def update_presence():
        """Update user/agent presence."""
        try:
            data = UpdatePresenceRequest(**request.get_json())
        except Exception as e:
            return jsonify({"error": str(e)}), 400
        
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            presence = service.update_presence(
                participant_id=user_id,
                status=data.status,
                is_typing=data.is_typing,
                typing_in_channel=data.typing_in_channel,
                agent_status=data.agent_status,
                agent_status_detail=data.agent_status_detail,
            )
            return jsonify(presence.to_dict())
    
    @bp.route('/channels/<channel_id>/presence', methods=['GET'])
    def get_presence(channel_id: str):
        """Get presence info for users in a channel."""
        with get_db_session() as session:
            service = ChatService(session)
            presence_list = service.get_channel_presence(channel_id)
            return jsonify({
                "presence": [p.to_dict() for p in presence_list],
            })
    
    @bp.route('/channels/<channel_id>/read', methods=['POST'])
    def mark_read(channel_id: str):
        """Mark all messages in channel as read."""
        user_id = get_current_user_id()
        
        with get_db_session() as session:
            service = ChatService(session)
            success = service.mark_messages_read(channel_id, user_id)
            if not success:
                return jsonify({"error": "Channel not found"}), 404
            return jsonify({"success": True})
    
    # -------------------------------------------------------------------------
    # Action Button Endpoints (Phase 7.3.2)
    # -------------------------------------------------------------------------
    
    @bp.route('/actions', methods=['GET'])
    def list_available_actions():
        """List all available action types and their definitions."""
        from api.chat_actions import get_action_registry
        
        registry = get_action_registry()
        return jsonify({
            "actions": registry.get_all_actions(),
            "total": len(registry.get_all_actions()),
        })
    
    @bp.route('/actions/suggest', methods=['POST'])
    def suggest_actions():
        """Get context-aware action suggestions.
        
        Request body:
            channel_id: str - Current channel
            recent_messages: List[dict] - Recent message data
            current_analysis: dict - Current analysis (if any)
            mentioned_bills: List[str] - Bills mentioned
            mentioned_scenarios: List[str] - Scenarios mentioned
        """
        from api.chat_actions import (
            ActionContext, SuggestionEngine, get_action_registry
        )
        
        data = request.get_json() or {}
        
        context = ActionContext(
            channel_id=data.get('channel_id', ''),
            channel_type=data.get('channel_type', 'public'),
            recent_messages=data.get('recent_messages', []),
            current_analysis=data.get('current_analysis'),
            mentioned_bills=data.get('mentioned_bills', []),
            mentioned_scenarios=data.get('mentioned_scenarios', []),
            mentioned_metrics=data.get('mentioned_metrics', []),
            user_preferences=data.get('user_preferences', {}),
        )
        
        engine = SuggestionEngine(get_action_registry())
        
        # Run async suggestion engine in sync context
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        max_suggestions = int(request.args.get('max', 4))
        suggestions = loop.run_until_complete(
            engine.suggest_actions(context, max_suggestions)
        )
        
        return jsonify({
            "suggestions": [
                {
                    "action": s.action.to_dict(),
                    "relevance_score": s.relevance_score,
                    "trigger_reason": s.trigger_reason,
                    "confidence": s.confidence,
                }
                for s in suggestions
            ],
            "total": len(suggestions),
        })
    
    @bp.route('/actions/execute', methods=['POST'])
    def execute_action():
        """Execute an action.
        
        Request body:
            action_type: str - Action type to execute
            params: dict - Action parameters
            channel_id: str - Channel to post results
        """
        from api.chat_actions import (
            ActionType, ActionExecutor, get_action_registry
        )
        
        data = request.get_json() or {}
        
        action_type_str = data.get('action_type')
        if not action_type_str:
            return jsonify({"error": "action_type is required"}), 400
        
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            return jsonify({
                "error": f"Invalid action_type: {action_type_str}",
                "valid_types": [at.value for at in ActionType],
            }), 400
        
        params = data.get('params', {})
        channel_id = data.get('channel_id')
        
        # Validate params
        registry = get_action_registry()
        is_valid, error = registry.validate_params(action_type, params)
        if not is_valid:
            return jsonify({"error": error}), 400
        
        # Execute action
        executor = ActionExecutor(registry)
        
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            executor.execute(
                action_type=action_type,
                params=params,
                channel_id=channel_id,
            )
        )
        
        return jsonify(result.to_dict()), 200 if result.status.value == 'completed' else 500
    
    @bp.route('/actions/<action_id>/status', methods=['GET'])
    def get_action_status(action_id: str):
        """Get status of a running action."""
        from api.chat_actions import ActionExecutor
        
        executor = ActionExecutor()
        result = executor.get_status(action_id)
        
        if not result:
            return jsonify({"error": "Action not found"}), 404
        
        return jsonify(result.to_dict())
    
    @bp.route('/actions/<action_id>/cancel', methods=['POST'])
    def cancel_action(action_id: str):
        """Cancel a running action."""
        from api.chat_actions import ActionExecutor
        
        executor = ActionExecutor()
        success = executor.cancel(action_id)
        
        if not success:
            return jsonify({"error": "Action not found or already completed"}), 404
        
        return jsonify({"success": True, "action_id": action_id})
    
    @bp.route('/actions/running', methods=['GET'])
    def list_running_actions():
        """List all currently running actions."""
        from api.chat_actions import ActionExecutor
        
        executor = ActionExecutor()
        running = executor.list_running()
        
        return jsonify({
            "actions": [r.to_dict() for r in running],
            "total": len(running),
        })
    
    @bp.route('/actions/button', methods=['POST'])
    def create_action_button():
        """Create a configured action button.
        
        Request body:
            action_type: str - Action type
            params: dict - Pre-filled parameters
            label: str - Custom label (optional)
        """
        from api.chat_actions import (
            ActionType, get_action_registry
        )
        
        data = request.get_json() or {}
        
        action_type_str = data.get('action_type')
        if not action_type_str:
            return jsonify({"error": "action_type is required"}), 400
        
        try:
            action_type = ActionType(action_type_str)
        except ValueError:
            return jsonify({
                "error": f"Invalid action_type: {action_type_str}",
            }), 400
        
        registry = get_action_registry()
        button = registry.create_button(
            action_type=action_type,
            params=data.get('params'),
            label_override=data.get('label'),
            disabled=data.get('disabled', False),
            disabled_reason=data.get('disabled_reason'),
        )
        
        return jsonify(button.to_dict())
    
    return bp
