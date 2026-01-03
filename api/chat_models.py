"""
Chat Data Models for PoliSim Chatroom (Phase 7.3.1).

This module defines SQLAlchemy models for chat channels, messages,
reactions, and attachments enabling collaborative policy analysis.

Features:
- ChatChannel: Public/private conversation spaces
- ChatMessage: Messages with rich content types
- ChatReaction: Emoji reactions to messages
- ChatAttachment: File/data attachments
- ChannelParticipant: Channel membership tracking

Example:
    from api.chat_models import ChatChannel, ChatMessage, ChannelType
    
    # Create a public channel
    channel = ChatChannel(
        name="Budget Analysis 2026",
        channel_type=ChannelType.PUBLIC,
        created_by="user_123"
    )
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean, DateTime, Enum as SQLEnum, Float, ForeignKey, 
    Index, Integer, String, Text
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models import Base, JSONBCompat


# =============================================================================
# Enums
# =============================================================================

class ChannelType(enum.Enum):
    """Type of chat channel."""
    PUBLIC = "public"           # MVP: Open to all users
    PRIVATE = "private"         # v1.1: Invite-only
    GROUP = "group"             # v1.1: Named group of users
    BILL_SPECIFIC = "bill"      # v1.1: Tied to specific bill analysis


class SenderType(enum.Enum):
    """Type of message sender."""
    USER = "user"               # Human user
    AGENT = "agent"             # AI agent
    SYSTEM = "system"           # System notifications


class MessageType(enum.Enum):
    """Type of chat message."""
    TEXT = "text"                       # Plain text message
    ANALYSIS_REQUEST = "analysis_request"   # Request for swarm analysis
    ANALYSIS_RESULT = "analysis_result"     # Swarm analysis results
    SCENARIO_REQUEST = "scenario_request"   # Request for scenario run
    SCENARIO_RESULT = "scenario_result"     # Scenario results
    ACTION = "action"                   # User/agent action
    SYSTEM_EVENT = "system_event"       # System notification
    THINKING = "thinking"               # Agent thinking indicator
    ERROR = "error"                     # Error message


class ReactionType(enum.Enum):
    """Emoji reactions for messages."""
    THUMBS_UP = "👍"
    THUMBS_DOWN = "👎"
    HEART = "❤️"
    THINKING = "🤔"
    CELEBRATE = "🎉"
    WARNING = "⚠️"
    CHECK = "✅"
    QUESTION = "❓"


class ParticipantRole(enum.Enum):
    """Role of participant in a channel."""
    OWNER = "owner"             # Channel creator
    ADMIN = "admin"             # Can manage channel
    MEMBER = "member"           # Regular participant
    VIEWER = "viewer"           # Read-only access


# =============================================================================
# Chat Channel Model
# =============================================================================

class ChatChannel(Base):
    """Chat channel for policy discussions and analysis collaboration.
    
    Attributes:
        channel_id: Unique channel identifier
        channel_type: PUBLIC, PRIVATE, GROUP, or BILL_SPECIFIC
        name: Display name of channel
        description: Optional channel description
        created_by: User ID of channel creator
        bill_id: Optional associated bill ID (for BILL_SPECIFIC type)
        is_active: Whether channel is active
        is_archived: Whether channel is archived
    """
    
    __tablename__ = "chat_channels"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    
    # Channel metadata
    channel_type: Mapped[ChannelType] = mapped_column(
        SQLEnum(ChannelType), default=ChannelType.PUBLIC, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    icon: Mapped[Optional[str]] = mapped_column(String(50))  # Emoji or icon name
    
    # Ownership
    created_by: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    # Bill association (for BILL_SPECIFIC channels)
    bill_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    analysis_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Settings
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONBCompat)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage", 
        back_populates="channel",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    participants: Mapped[List["ChannelParticipant"]] = relationship(
        "ChannelParticipant",
        back_populates="channel",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_chat_channels_type_active', 'channel_type', 'is_active'),
        Index('ix_chat_channels_created_by_active', 'created_by', 'is_active'),
    )
    
    def to_dict(self, include_participants: bool = False) -> Dict[str, Any]:
        """Convert channel to dictionary representation."""
        data = {
            "channel_id": self.channel_id,
            "channel_type": self.channel_type.value,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "created_by": self.created_by,
            "bill_id": self.bill_id,
            "analysis_id": self.analysis_id,
            "is_active": self.is_active,
            "is_archived": self.is_archived,
            "settings": self.settings,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
        }
        if include_participants:
            data["participants"] = [p.to_dict() for p in self.participants]
        return data


# =============================================================================
# Channel Participant Model
# =============================================================================

class ChannelParticipant(Base):
    """Channel membership and role tracking.
    
    Tracks which users and agents are members of a channel,
    along with their roles and notification preferences.
    """
    
    __tablename__ = "channel_participants"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_channels.id", ondelete="CASCADE"), nullable=False
    )
    
    # Participant identity (can be user_id or agent_id)
    participant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    participant_type: Mapped[SenderType] = mapped_column(
        SQLEnum(SenderType), default=SenderType.USER, nullable=False
    )
    
    # Role and permissions
    role: Mapped[ParticipantRole] = mapped_column(
        SQLEnum(ParticipantRole), default=ParticipantRole.MEMBER, nullable=False
    )
    
    # Status
    is_muted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_read_message_id: Mapped[Optional[int]] = mapped_column(Integer)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    joined_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    left_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    channel: Mapped["ChatChannel"] = relationship(
        "ChatChannel", back_populates="participants"
    )
    
    # Unique constraint: one participant per channel
    __table_args__ = (
        Index('ix_channel_participant_unique', 'channel_id', 'participant_id', unique=True),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert participant to dictionary."""
        return {
            "participant_id": self.participant_id,
            "participant_type": self.participant_type.value,
            "role": self.role.value,
            "is_muted": self.is_muted,
            "unread_count": self.unread_count,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


# =============================================================================
# Chat Message Model
# =============================================================================

class ChatMessage(Base):
    """Chat message in a channel.
    
    Supports rich message types including text, analysis requests/results,
    and action triggers. Messages can have attachments, reactions, and
    belong to threads.
    
    Attributes:
        message_id: Unique message identifier
        channel_id: Channel this message belongs to
        sender_id: User or agent who sent the message
        sender_type: USER, AGENT, or SYSTEM
        content: Message text content
        message_type: TEXT, ANALYSIS_REQUEST, etc.
    """
    
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    
    # Channel association
    channel_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_channels.id", ondelete="CASCADE"), nullable=False
    )
    
    # Sender information
    sender_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sender_type: Mapped[SenderType] = mapped_column(
        SQLEnum(SenderType), default=SenderType.USER, nullable=False
    )
    sender_name: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Content
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(
        SQLEnum(MessageType), default=MessageType.TEXT, nullable=False
    )
    
    # Rich content (for analysis results, action data, etc.)
    # Note: Using 'message_metadata' instead of 'metadata' because 'metadata' is reserved by SQLAlchemy
    message_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONBCompat)
    
    # Threading support
    thread_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    reply_to_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    
    # @mentions
    mentions: Mapped[Optional[List[str]]] = mapped_column(JSONBCompat)
    
    # Status
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), index=True
    )
    edited_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relationships
    channel: Mapped["ChatChannel"] = relationship(
        "ChatChannel", back_populates="messages"
    )
    attachments: Mapped[List["ChatAttachment"]] = relationship(
        "ChatAttachment",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    reactions: Mapped[List["ChatReaction"]] = relationship(
        "ChatReaction",
        back_populates="message",
        cascade="all, delete-orphan"
    )
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_chat_messages_channel_created', 'channel_id', 'created_at'),
        Index('ix_chat_messages_thread', 'thread_id', 'created_at'),
        Index('ix_chat_messages_sender', 'sender_id', 'created_at'),
    )
    
    def to_dict(self, include_attachments: bool = True, include_reactions: bool = True) -> Dict[str, Any]:
        """Convert message to dictionary representation."""
        data = {
            "message_id": self.message_id,
            "channel_id": self.channel.channel_id if self.channel else None,
            "sender_id": self.sender_id,
            "sender_type": self.sender_type.value,
            "sender_name": self.sender_name,
            "content": self.content,
            "message_type": self.message_type.value,
            "metadata": self.message_metadata,  # API returns as 'metadata' for compatibility
            "thread_id": self.thread_id,
            "reply_to_id": self.reply_to_id,
            "mentions": self.mentions,
            "is_edited": self.is_edited,
            "is_deleted": self.is_deleted,
            "is_pinned": self.is_pinned,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "edited_at": self.edited_at.isoformat() if self.edited_at else None,
        }
        if include_attachments and self.attachments:
            data["attachments"] = [a.to_dict() for a in self.attachments]
        if include_reactions and self.reactions:
            # Aggregate reactions by type
            reaction_counts: Dict[str, int] = {}
            for r in self.reactions:
                emoji = r.reaction_type.value
                reaction_counts[emoji] = reaction_counts.get(emoji, 0) + 1
            data["reactions"] = reaction_counts
            data["reaction_details"] = [r.to_dict() for r in self.reactions]
        return data


# =============================================================================
# Chat Attachment Model
# =============================================================================

class ChatAttachment(Base):
    """File or data attachment to a chat message.
    
    Supports charts, PDFs, analysis results, and other file types.
    """
    
    __tablename__ = "chat_attachments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    attachment_id: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    
    # Message association
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False
    )
    
    # Attachment details
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # image, pdf, chart, data
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)  # bytes
    
    # Storage
    storage_path: Mapped[Optional[str]] = mapped_column(String(500))
    storage_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    # For embedded data (charts, small files)
    inline_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONBCompat)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage", back_populates="attachments"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert attachment to dictionary."""
        return {
            "attachment_id": self.attachment_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "file_size": self.file_size,
            "storage_url": self.storage_url,
            "has_inline_data": self.inline_data is not None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Chat Reaction Model
# =============================================================================

class ChatReaction(Base):
    """Emoji reaction to a chat message."""
    
    __tablename__ = "chat_reactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # Message association
    message_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False
    )
    
    # Reactor
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    
    # Reaction
    reaction_type: Mapped[ReactionType] = mapped_column(
        SQLEnum(ReactionType), nullable=False
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    message: Mapped["ChatMessage"] = relationship(
        "ChatMessage", back_populates="reactions"
    )
    
    # Unique constraint: one reaction type per user per message
    __table_args__ = (
        Index('ix_chat_reaction_unique', 'message_id', 'user_id', 'reaction_type', unique=True),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reaction to dictionary."""
        return {
            "user_id": self.user_id,
            "reaction": self.reaction_type.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# =============================================================================
# Chat Presence Model (for real-time status)
# =============================================================================

class ChatPresence(Base):
    """User/agent presence and typing status.
    
    Ephemeral status data - can be stored in Redis for production,
    but SQLite works for development.
    """
    
    __tablename__ = "chat_presence"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # User/agent identity
    participant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    participant_type: Mapped[SenderType] = mapped_column(
        SQLEnum(SenderType), default=SenderType.USER, nullable=False
    )
    
    # Current channel (if any)
    current_channel_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(20), default="offline")  # online, away, busy, offline
    is_typing: Mapped[bool] = mapped_column(Boolean, default=False)
    typing_in_channel: Mapped[Optional[str]] = mapped_column(String(36))
    
    # Agent-specific: "thinking" indicator with context
    agent_status: Mapped[Optional[str]] = mapped_column(String(50))  # thinking, analyzing, debating
    agent_status_detail: Mapped[Optional[str]] = mapped_column(String(255))
    
    # Timestamps
    last_seen: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    typing_started: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Unique: one presence record per participant
    __table_args__ = (
        Index('ix_presence_participant', 'participant_id', 'participant_type', unique=True),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert presence to dictionary."""
        return {
            "participant_id": self.participant_id,
            "participant_type": self.participant_type.value,
            "status": self.status,
            "is_typing": self.is_typing,
            "typing_in_channel": self.typing_in_channel,
            "agent_status": self.agent_status,
            "agent_status_detail": self.agent_status_detail,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


# =============================================================================
# Helper Functions
# =============================================================================

def init_chat_tables(engine) -> None:
    """Initialize chat database tables.
    
    Call this after the main database is initialized to create
    chat-specific tables.
    """
    # Only create tables that inherit from Base
    ChatChannel.__table__.create(engine, checkfirst=True)
    ChannelParticipant.__table__.create(engine, checkfirst=True)
    ChatMessage.__table__.create(engine, checkfirst=True)
    ChatAttachment.__table__.create(engine, checkfirst=True)
    ChatReaction.__table__.create(engine, checkfirst=True)
    ChatPresence.__table__.create(engine, checkfirst=True)
