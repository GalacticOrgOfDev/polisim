"""
Chat WebSocket Server Extension for PoliSim Chatroom (Phase 7.3.1).

This module extends the WebSocket server to support real-time chat functionality,
including message streaming, presence updates, and typing indicators.

Features:
- Real-time message delivery
- Presence tracking (online/offline/typing)
- Agent thinking indicators
- Message delivery acknowledgments
- Reconnection with message replay

Example:
    from api.chat_websocket import ChatWebSocketManager
    
    manager = ChatWebSocketManager()
    await manager.connect(websocket, channel_id, user_id)
    await manager.broadcast_message(channel_id, message)
"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set
from uuid import uuid4

try:
    from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
    from fastapi.websockets import WebSocketState
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    class WebSocket:
        pass
    class WebSocketDisconnect(Exception):
        pass

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ChatWebSocketConfig:
    """Configuration for chat WebSocket server."""
    
    # Connection limits
    max_connections_per_channel: int = 100
    max_total_connections: int = 1000
    max_channels_per_user: int = 50
    
    # Timeout settings
    connection_timeout_seconds: float = 3600.0  # 1 hour
    ping_interval_seconds: float = 30.0
    ping_timeout_seconds: float = 10.0
    
    # Presence settings
    typing_timeout_seconds: float = 5.0
    presence_update_interval_seconds: float = 60.0
    
    # Message settings
    max_message_size_bytes: int = 64 * 1024  # 64KB
    message_buffer_size: int = 100  # Messages buffered per channel
    message_buffer_ttl_seconds: float = 300.0  # 5 minutes


# =============================================================================
# Event Types
# =============================================================================

class ChatEventType:
    """Event types for chat WebSocket."""
    # Messages
    NEW_MESSAGE = "new_message"
    MESSAGE_EDITED = "message_edited"
    MESSAGE_DELETED = "message_deleted"
    
    # Reactions
    REACTION_ADDED = "reaction_added"
    REACTION_REMOVED = "reaction_removed"
    
    # Presence
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    PRESENCE_UPDATE = "presence_update"
    TYPING_START = "typing_start"
    TYPING_STOP = "typing_stop"
    
    # Agents
    AGENT_JOINED = "agent_joined"
    AGENT_LEFT = "agent_left"
    AGENT_THINKING = "agent_thinking"
    AGENT_RESPONSE = "agent_response"
    
    # Channel
    CHANNEL_UPDATED = "channel_updated"
    
    # Analysis
    ANALYSIS_STARTED = "analysis_started"
    ANALYSIS_PROGRESS = "analysis_progress"
    ANALYSIS_COMPLETE = "analysis_complete"
    
    # System
    ERROR = "error"
    ACK = "ack"
    PING = "ping"
    PONG = "pong"


@dataclass
class ChatEvent:
    """Event sent to/from WebSocket clients."""
    
    event_id: str = field(default_factory=lambda: str(uuid4())[:12])
    event_type: str = ""
    channel_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sequence: int = 0
    sender_id: Optional[str] = None
    
    def to_json(self) -> str:
        """Serialize event to JSON."""
        return json.dumps({
            "event_id": self.event_id,
            "event_type": self.event_type,
            "channel_id": self.channel_id,
            "data": self.data,
            "timestamp": self.timestamp,
            "sequence": self.sequence,
            "sender_id": self.sender_id,
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> "ChatEvent":
        """Deserialize event from JSON."""
        data = json.loads(json_str)
        return cls(
            event_id=data.get("event_id", str(uuid4())[:12]),
            event_type=data.get("event_type", ""),
            channel_id=data.get("channel_id", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
            sequence=data.get("sequence", 0),
            sender_id=data.get("sender_id"),
        )


# =============================================================================
# Connection Info
# =============================================================================

@dataclass
class ChatConnection:
    """Information about a WebSocket connection."""
    
    connection_id: str
    websocket: Any  # WebSocket
    user_id: str
    user_type: str  # user, agent
    channels: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_ping: Optional[datetime] = None
    last_sequence: Dict[str, int] = field(default_factory=dict)  # Per channel


@dataclass
class PresenceInfo:
    """User/agent presence information."""
    
    participant_id: str
    participant_type: str
    status: str  # online, away, offline
    current_channel: Optional[str] = None
    is_typing: bool = False
    typing_in_channel: Optional[str] = None
    typing_started: Optional[datetime] = None
    agent_status: Optional[str] = None
    agent_status_detail: Optional[str] = None
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# Chat WebSocket Manager
# =============================================================================

class ChatWebSocketManager:
    """Manager for chat WebSocket connections.
    
    Handles connection management, message broadcasting,
    presence tracking, and agent participation.
    """
    
    def __init__(self, config: Optional[ChatWebSocketConfig] = None):
        self.config = config or ChatWebSocketConfig()
        
        # Connections by channel
        self._channel_connections: Dict[str, Set[str]] = defaultdict(set)  # channel_id -> connection_ids
        
        # All connections
        self._connections: Dict[str, ChatConnection] = {}  # connection_id -> ChatConnection
        
        # Presence tracking
        self._presence: Dict[str, PresenceInfo] = {}  # participant_id -> PresenceInfo
        
        # Message buffer for reconnection
        self._message_buffer: Dict[str, List[ChatEvent]] = defaultdict(list)
        
        # Sequence numbers per channel
        self._sequences: Dict[str, int] = defaultdict(int)
        
        # Typing timeout tasks
        self._typing_timeouts: Dict[str, asyncio.Task] = {}
        
        # Stats
        self.stats = {
            "total_connections": 0,
            "total_messages": 0,
            "total_reconnections": 0,
        }
        
        logger.info("ChatWebSocketManager initialized")
    
    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------
    
    async def connect(
        self,
        websocket: WebSocket,
        user_id: str,
        user_type: str = "user",
        initial_channels: Optional[List[str]] = None,
        last_sequences: Optional[Dict[str, int]] = None,
    ) -> str:
        """Accept and register a WebSocket connection.
        
        Args:
            websocket: The WebSocket connection
            user_id: ID of the connecting user/agent
            user_type: Type (user or agent)
            initial_channels: Channels to join immediately
            last_sequences: Last received sequences for reconnection
        
        Returns:
            Connection ID
        """
        # Check total connection limit
        if len(self._connections) >= self.config.max_total_connections:
            logger.warning("Total connection limit reached")
            await websocket.close(code=1013, reason="Server at capacity")
            return ""
        
        # Accept connection
        await websocket.accept()
        
        # Create connection record
        connection_id = str(uuid4())
        connection = ChatConnection(
            connection_id=connection_id,
            websocket=websocket,
            user_id=user_id,
            user_type=user_type,
            last_sequence=last_sequences or {},
        )
        
        self._connections[connection_id] = connection
        self.stats["total_connections"] += 1
        
        # Update presence
        self._update_presence(user_id, user_type, "online")
        
        # Join initial channels
        if initial_channels:
            for channel_id in initial_channels:
                await self.join_channel(connection_id, channel_id)
        
        logger.info(f"Chat WebSocket connected: {user_id} ({user_type})")
        
        # Check for reconnection and replay missed messages
        if last_sequences:
            self.stats["total_reconnections"] += 1
            await self._replay_missed_messages(connection_id, last_sequences)
        
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """Disconnect and cleanup a WebSocket connection."""
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        # Leave all channels
        for channel_id in list(connection.channels):
            self._leave_channel_sync(connection_id, channel_id)
        
        # Update presence
        self._update_presence(connection.user_id, connection.user_type, "offline")
        
        # Remove connection
        del self._connections[connection_id]
        
        logger.info(f"Chat WebSocket disconnected: {connection.user_id}")
    
    async def join_channel(self, connection_id: str, channel_id: str) -> bool:
        """Have a connection join a channel.
        
        Args:
            connection_id: The connection to join
            channel_id: The channel to join
        
        Returns:
            True if successful
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return False
        
        # Check channel connection limit
        if len(self._channel_connections[channel_id]) >= self.config.max_connections_per_channel:
            logger.warning(f"Channel {channel_id} at connection limit")
            return False
        
        # Check user channel limit
        if len(connection.channels) >= self.config.max_channels_per_user:
            logger.warning(f"User {connection.user_id} at channel limit")
            return False
        
        # Add to channel
        connection.channels.add(channel_id)
        self._channel_connections[channel_id].add(connection_id)
        
        # Broadcast join event
        await self.broadcast(
            channel_id=channel_id,
            event_type=ChatEventType.USER_JOINED,
            data={
                "user_id": connection.user_id,
                "user_type": connection.user_type,
            },
            exclude_connection=connection_id,
        )
        
        logger.debug(f"Connection {connection_id} joined channel {channel_id}")
        return True
    
    async def leave_channel(self, connection_id: str, channel_id: str) -> bool:
        """Have a connection leave a channel."""
        connection = self._connections.get(connection_id)
        if not connection or channel_id not in connection.channels:
            return False
        
        # Broadcast leave event first
        await self.broadcast(
            channel_id=channel_id,
            event_type=ChatEventType.USER_LEFT,
            data={
                "user_id": connection.user_id,
                "user_type": connection.user_type,
            },
            exclude_connection=connection_id,
        )
        
        self._leave_channel_sync(connection_id, channel_id)
        return True
    
    def _leave_channel_sync(self, connection_id: str, channel_id: str) -> None:
        """Synchronous channel leave (for cleanup)."""
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        connection.channels.discard(channel_id)
        self._channel_connections[channel_id].discard(connection_id)
        
        # Cleanup empty channel
        if not self._channel_connections[channel_id]:
            del self._channel_connections[channel_id]
    
    # -------------------------------------------------------------------------
    # Message Broadcasting
    # -------------------------------------------------------------------------
    
    async def broadcast(
        self,
        channel_id: str,
        event_type: str,
        data: Dict[str, Any],
        sender_id: Optional[str] = None,
        exclude_connection: Optional[str] = None,
    ) -> int:
        """Broadcast an event to all connections in a channel.
        
        Args:
            channel_id: Channel to broadcast to
            event_type: Type of event
            data: Event data
            sender_id: Optional sender ID
            exclude_connection: Optional connection to exclude
        
        Returns:
            Number of recipients
        """
        if channel_id not in self._channel_connections:
            return 0
        
        # Create event
        event = ChatEvent(
            event_type=event_type,
            channel_id=channel_id,
            data=data,
            sender_id=sender_id,
            sequence=self._get_next_sequence(channel_id),
        )
        
        # Buffer for reconnection
        self._buffer_message(channel_id, event)
        
        # Send to all connections
        sent_count = 0
        dead_connections = []
        
        for conn_id in self._channel_connections[channel_id]:
            if conn_id == exclude_connection:
                continue
            
            connection = self._connections.get(conn_id)
            if not connection:
                dead_connections.append(conn_id)
                continue
            
            try:
                await self._send_event(connection.websocket, event)
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send to {conn_id}: {e}")
                dead_connections.append(conn_id)
        
        # Cleanup dead connections
        for conn_id in dead_connections:
            self.disconnect(conn_id)
        
        self.stats["total_messages"] += sent_count
        return sent_count
    
    async def broadcast_message(
        self,
        channel_id: str,
        message: Dict[str, Any],
    ) -> int:
        """Broadcast a new chat message to a channel."""
        return await self.broadcast(
            channel_id=channel_id,
            event_type=ChatEventType.NEW_MESSAGE,
            data=message,
            sender_id=message.get("sender_id"),
        )
    
    async def send_to_user(
        self,
        user_id: str,
        event_type: str,
        data: Dict[str, Any],
        channel_id: Optional[str] = None,
    ) -> bool:
        """Send an event to a specific user's connections.
        
        Args:
            user_id: Target user ID
            event_type: Event type
            data: Event data
            channel_id: Optional channel context
        
        Returns:
            True if sent to at least one connection
        """
        sent = False
        
        for conn_id, connection in self._connections.items():
            if connection.user_id != user_id:
                continue
            
            event = ChatEvent(
                event_type=event_type,
                channel_id=channel_id or "",
                data=data,
            )
            
            try:
                await self._send_event(connection.websocket, event)
                sent = True
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
        
        return sent
    
    async def _send_event(self, websocket: WebSocket, event: ChatEvent) -> None:
        """Send an event to a WebSocket."""
        if HAS_FASTAPI:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(event.to_json())
        else:
            await websocket.send_text(event.to_json())
    
    # -------------------------------------------------------------------------
    # Presence & Typing
    # -------------------------------------------------------------------------
    
    def _update_presence(
        self,
        participant_id: str,
        participant_type: str,
        status: str,
        current_channel: Optional[str] = None,
    ) -> None:
        """Update participant presence."""
        if participant_id not in self._presence:
            self._presence[participant_id] = PresenceInfo(
                participant_id=participant_id,
                participant_type=participant_type,
                status=status,
            )
        
        presence = self._presence[participant_id]
        presence.status = status
        presence.last_seen = datetime.now(timezone.utc)
        
        if current_channel is not None:
            presence.current_channel = current_channel
    
    async def set_typing(
        self,
        connection_id: str,
        channel_id: str,
        is_typing: bool,
    ) -> None:
        """Set typing status for a user.
        
        Args:
            connection_id: The connection
            channel_id: The channel
            is_typing: Whether user is typing
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        user_id = connection.user_id
        
        # Update presence
        if user_id in self._presence:
            self._presence[user_id].is_typing = is_typing
            self._presence[user_id].typing_in_channel = channel_id if is_typing else None
            self._presence[user_id].typing_started = datetime.now(timezone.utc) if is_typing else None
        
        # Broadcast typing event
        event_type = ChatEventType.TYPING_START if is_typing else ChatEventType.TYPING_STOP
        await self.broadcast(
            channel_id=channel_id,
            event_type=event_type,
            data={
                "user_id": user_id,
                "user_type": connection.user_type,
            },
            exclude_connection=connection_id,
        )
        
        # Set timeout to auto-clear typing
        if is_typing:
            timeout_key = f"{user_id}:{channel_id}"
            
            # Cancel existing timeout
            if timeout_key in self._typing_timeouts:
                self._typing_timeouts[timeout_key].cancel()
            
            # Create new timeout
            async def clear_typing():
                await asyncio.sleep(self.config.typing_timeout_seconds)
                await self.set_typing(connection_id, channel_id, False)
            
            self._typing_timeouts[timeout_key] = asyncio.create_task(clear_typing())
    
    async def set_agent_status(
        self,
        agent_id: str,
        channel_id: str,
        status: str,
        detail: Optional[str] = None,
    ) -> None:
        """Set agent thinking/status indicator.
        
        Args:
            agent_id: The agent ID
            channel_id: The channel
            status: Status (thinking, analyzing, debating, etc.)
            detail: Optional detail text
        """
        # Update presence
        if agent_id in self._presence:
            self._presence[agent_id].agent_status = status
            self._presence[agent_id].agent_status_detail = detail
        
        # Broadcast agent status
        await self.broadcast(
            channel_id=channel_id,
            event_type=ChatEventType.AGENT_THINKING,
            data={
                "agent_id": agent_id,
                "status": status,
                "detail": detail,
            },
        )
    
    async def broadcast_presence(self, channel_id: str) -> None:
        """Broadcast current presence for all users in a channel."""
        presence_list = []
        
        for conn_id in self._channel_connections.get(channel_id, set()):
            connection = self._connections.get(conn_id)
            if not connection:
                continue
            
            presence = self._presence.get(connection.user_id)
            if presence:
                presence_list.append({
                    "participant_id": presence.participant_id,
                    "participant_type": presence.participant_type,
                    "status": presence.status,
                    "is_typing": presence.is_typing and presence.typing_in_channel == channel_id,
                    "agent_status": presence.agent_status,
                    "agent_status_detail": presence.agent_status_detail,
                })
        
        await self.broadcast(
            channel_id=channel_id,
            event_type=ChatEventType.PRESENCE_UPDATE,
            data={"presence": presence_list},
        )
    
    def get_channel_presence(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get current presence info for a channel."""
        presence_list = []
        
        for conn_id in self._channel_connections.get(channel_id, set()):
            connection = self._connections.get(conn_id)
            if not connection:
                continue
            
            presence = self._presence.get(connection.user_id)
            if presence:
                presence_list.append({
                    "participant_id": presence.participant_id,
                    "participant_type": presence.participant_type,
                    "status": presence.status,
                    "is_typing": presence.is_typing and presence.typing_in_channel == channel_id,
                    "agent_status": presence.agent_status,
                    "last_seen": presence.last_seen.isoformat(),
                })
        
        return presence_list
    
    # -------------------------------------------------------------------------
    # Message Handling
    # -------------------------------------------------------------------------
    
    async def handle_client_message(
        self,
        connection_id: str,
        raw_message: str,
    ) -> Optional[ChatEvent]:
        """Handle an incoming message from a client.
        
        Args:
            connection_id: The sending connection
            raw_message: Raw JSON message
        
        Returns:
            Response event if any
        """
        connection = self._connections.get(connection_id)
        if not connection:
            return None
        
        try:
            event = ChatEvent.from_json(raw_message)
        except Exception as e:
            logger.warning(f"Invalid message from {connection_id}: {e}")
            return ChatEvent(
                event_type=ChatEventType.ERROR,
                data={"error": "Invalid message format"},
            )
        
        # Handle different event types
        if event.event_type == ChatEventType.PING:
            connection.last_ping = datetime.now(timezone.utc)
            return ChatEvent(event_type=ChatEventType.PONG)
        
        elif event.event_type == ChatEventType.TYPING_START:
            await self.set_typing(connection_id, event.channel_id, True)
            return None
        
        elif event.event_type == ChatEventType.TYPING_STOP:
            await self.set_typing(connection_id, event.channel_id, False)
            return None
        
        elif event.event_type == ChatEventType.NEW_MESSAGE:
            # Process new message through chat service
            return await self._process_new_message(connection, event)
        
        # Send acknowledgment
        return ChatEvent(
            event_type=ChatEventType.ACK,
            data={"event_id": event.event_id},
        )
    
    async def _process_new_message(
        self,
        connection: ChatConnection,
        event: ChatEvent,
    ) -> Optional[ChatEvent]:
        """Process a new message from a client."""
        try:
            from api.chat_api import ChatService
            from api.database import get_db_session
            
            with get_db_session() as session:
                service = ChatService(session)
                message = service.send_message(
                    channel_id=event.channel_id,
                    sender_id=connection.user_id,
                    sender_type=connection.user_type,
                    content=event.data.get("content", ""),
                    message_type=event.data.get("message_type", "text"),
                    metadata=event.data.get("metadata"),
                    thread_id=event.data.get("thread_id"),
                    reply_to_id=event.data.get("reply_to_id"),
                    mentions=event.data.get("mentions"),
                )
                
                if message:
                    # Broadcast to channel
                    await self.broadcast_message(event.channel_id, message.to_dict())
                    
                    # Process for agent responses
                    await self._trigger_agent_responses(event.channel_id, message.to_dict())
                    
                    return ChatEvent(
                        event_type=ChatEventType.ACK,
                        data={"message_id": message.message_id},
                    )
                
                return ChatEvent(
                    event_type=ChatEventType.ERROR,
                    data={"error": "Failed to send message"},
                )
                
        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            return ChatEvent(
                event_type=ChatEventType.ERROR,
                data={"error": str(e)},
            )
    
    async def _trigger_agent_responses(
        self,
        channel_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Trigger agent responses to a message."""
        try:
            from api.chat_agent_participation import AgentWebSocketHandler, AgentChatManager
            
            # Get agents in channel (from participants)
            from api.chat_api import ChatService
            from api.database import get_db_session
            
            with get_db_session() as session:
                service = ChatService(session)
                channel_agents = service.get_channel_agents(channel_id)
                agent_ids = [a.participant_id for a in channel_agents]
            
            if not agent_ids:
                return
            
            # Create handler and process
            handler = AgentWebSocketHandler()
            
            async def broadcast_callback(ch_id: str, event_type: str, data: Dict[str, Any]):
                await self.broadcast(ch_id, event_type, data)
            
            await handler.handle_new_message(
                message=message,
                channel_id=channel_id,
                channel_agents=agent_ids,
                broadcast_callback=broadcast_callback,
            )
            
        except Exception as e:
            logger.warning(f"Agent response trigger failed: {e}")
    
    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------
    
    def _get_next_sequence(self, channel_id: str) -> int:
        """Get next sequence number for a channel."""
        self._sequences[channel_id] += 1
        return self._sequences[channel_id]
    
    def _buffer_message(self, channel_id: str, event: ChatEvent) -> None:
        """Buffer a message for reconnection."""
        buffer = self._message_buffer[channel_id]
        buffer.append(event)
        
        # Trim old messages
        if len(buffer) > self.config.message_buffer_size:
            buffer.pop(0)
    
    async def _replay_missed_messages(
        self,
        connection_id: str,
        last_sequences: Dict[str, int],
    ) -> None:
        """Replay messages missed during disconnect."""
        connection = self._connections.get(connection_id)
        if not connection:
            return
        
        for channel_id, last_seq in last_sequences.items():
            if channel_id not in self._message_buffer:
                continue
            
            for event in self._message_buffer[channel_id]:
                if event.sequence > last_seq:
                    try:
                        await self._send_event(connection.websocket, event)
                    except Exception as e:
                        logger.warning(f"Failed to replay message: {e}")
                        break
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        return {
            **self.stats,
            "active_connections": len(self._connections),
            "active_channels": len(self._channel_connections),
            "users_online": sum(1 for p in self._presence.values() if p.status == "online"),
        }


# =============================================================================
# FastAPI Router
# =============================================================================

def create_chat_websocket_router(manager: Optional[ChatWebSocketManager] = None) -> "APIRouter":
    """Create FastAPI router for chat WebSocket endpoints."""
    if not HAS_FASTAPI:
        raise ImportError("FastAPI required for WebSocket router")
    
    router = APIRouter()
    ws_manager = manager or ChatWebSocketManager()
    
    @router.websocket("/ws/chat/{channel_id}")
    async def chat_websocket(
        websocket: WebSocket,
        channel_id: str,
        user_id: str = Query(...),
        user_type: str = Query(default="user"),
        last_sequence: int = Query(default=0),
    ):
        """WebSocket endpoint for chat channels.
        
        Query Parameters:
            user_id: User or agent ID
            user_type: 'user' or 'agent'
            last_sequence: Last received sequence for reconnection
        """
        # Connect
        connection_id = await ws_manager.connect(
            websocket=websocket,
            user_id=user_id,
            user_type=user_type,
            initial_channels=[channel_id],
            last_sequences={channel_id: last_sequence} if last_sequence > 0 else None,
        )
        
        if not connection_id:
            return
        
        try:
            while True:
                # Receive message
                raw_message = await websocket.receive_text()
                
                # Handle and respond
                response = await ws_manager.handle_client_message(connection_id, raw_message)
                
                if response:
                    await websocket.send_text(response.to_json())
                    
        except WebSocketDisconnect:
            ws_manager.disconnect(connection_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            ws_manager.disconnect(connection_id)
    
    @router.websocket("/ws/chat")
    async def multi_channel_websocket(
        websocket: WebSocket,
        user_id: str = Query(...),
        user_type: str = Query(default="user"),
    ):
        """WebSocket endpoint for multi-channel chat.
        
        Client can join/leave channels dynamically via messages.
        """
        connection_id = await ws_manager.connect(
            websocket=websocket,
            user_id=user_id,
            user_type=user_type,
        )
        
        if not connection_id:
            return
        
        try:
            while True:
                raw_message = await websocket.receive_text()
                
                # Parse for channel operations
                try:
                    event = ChatEvent.from_json(raw_message)
                    
                    if event.event_type == "join_channel":
                        await ws_manager.join_channel(connection_id, event.channel_id)
                        response = ChatEvent(
                            event_type=ChatEventType.ACK,
                            data={"joined": event.channel_id},
                        )
                        await websocket.send_text(response.to_json())
                        continue
                    
                    elif event.event_type == "leave_channel":
                        await ws_manager.leave_channel(connection_id, event.channel_id)
                        response = ChatEvent(
                            event_type=ChatEventType.ACK,
                            data={"left": event.channel_id},
                        )
                        await websocket.send_text(response.to_json())
                        continue
                        
                except Exception:
                    pass
                
                # Regular message handling
                response = await ws_manager.handle_client_message(connection_id, raw_message)
                
                if response:
                    await websocket.send_text(response.to_json())
                    
        except WebSocketDisconnect:
            ws_manager.disconnect(connection_id)
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            ws_manager.disconnect(connection_id)
    
    return router
