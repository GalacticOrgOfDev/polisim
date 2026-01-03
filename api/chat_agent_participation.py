"""
Agent Chat Participation for PoliSim Chatroom (Phase 7.3.1).

This module enables AI agents to participate in chat channels,
responding to @mentions, proactively sharing insights, and
triggering analyses based on conversation context.

Features:
- Agent mention detection and response
- Proactive insight sharing
- Rate limiting for agent messages
- Context-aware responses
- Analysis triggering from chat

Example:
    from api.chat_agent_participation import AgentChatManager
    
    manager = AgentChatManager()
    await manager.process_message(message, channel)
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class AgentChatConfig:
    """Configuration for agent chat participation."""
    
    # Rate limiting
    max_messages_per_minute: int = 5
    max_messages_per_hour: int = 50
    cooldown_after_burst_seconds: int = 30
    
    # Response settings
    response_delay_seconds: float = 1.0  # Simulate "typing"
    max_response_length: int = 2000
    
    # Proactive settings
    enable_proactive_insights: bool = True
    insight_frequency_minutes: int = 10
    min_messages_before_insight: int = 5
    
    # Analysis triggers
    auto_analyze_bill_mentions: bool = True
    require_confirmation_for_analysis: bool = True


# =============================================================================
# Agent Definitions
# =============================================================================

@dataclass
class ChatAgent:
    """Definition of an AI agent that can participate in chat."""
    
    agent_id: str
    name: str
    specialty: str
    description: str
    avatar_emoji: str
    response_style: str  # concise, detailed, educational
    expertise_keywords: List[str] = field(default_factory=list)
    
    # Rate limiting state
    messages_this_minute: int = 0
    messages_this_hour: int = 0
    last_message_time: Optional[datetime] = None
    minute_reset_time: Optional[datetime] = None
    hour_reset_time: Optional[datetime] = None


# Default agent roster
DEFAULT_AGENTS: Dict[str, ChatAgent] = {
    "fiscal": ChatAgent(
        agent_id="fiscal",
        name="Fiscal Agent",
        specialty="Revenue and Spending Analysis",
        description="I analyze revenue projections, spending impacts, and debt trajectories.",
        avatar_emoji="💰",
        response_style="detailed",
        expertise_keywords=["revenue", "spending", "deficit", "debt", "budget", "tax", "appropriation"],
    ),
    "healthcare": ChatAgent(
        agent_id="healthcare",
        name="Healthcare Agent", 
        specialty="Healthcare Policy Analysis",
        description="I specialize in Medicare, Medicaid, ACA, and healthcare spending projections.",
        avatar_emoji="🏥",
        response_style="educational",
        expertise_keywords=["medicare", "medicaid", "healthcare", "insurance", "aca", "coverage", "drug", "hospital"],
    ),
    "economic": ChatAgent(
        agent_id="economic",
        name="Economic Agent",
        specialty="Macroeconomic Impact Analysis",
        description="I analyze GDP impacts, employment effects, and economic assumptions.",
        avatar_emoji="📈",
        response_style="detailed",
        expertise_keywords=["gdp", "economic", "growth", "employment", "inflation", "recession", "macro"],
    ),
    "social_security": ChatAgent(
        agent_id="social_security",
        name="Social Security Agent",
        specialty="Social Security and Retirement Analysis",
        description="I analyze Social Security trust funds, benefits, and reform proposals.",
        avatar_emoji="👴",
        response_style="educational",
        expertise_keywords=["social security", "retirement", "oasi", "disability", "benefit", "trust fund", "payroll"],
    ),
    "equity": ChatAgent(
        agent_id="equity",
        name="Equity Agent",
        specialty="Distributional Impact Analysis",
        description="I analyze how policies affect different income groups and demographics.",
        avatar_emoji="⚖️",
        response_style="detailed",
        expertise_keywords=["equity", "distribution", "income", "poverty", "inequality", "fairness", "demographic"],
    ),
    "implementation": ChatAgent(
        agent_id="implementation",
        name="Implementation Agent",
        specialty="Practical Feasibility Analysis",
        description="I assess implementation timelines, administrative requirements, and practical challenges.",
        avatar_emoji="🔧",
        response_style="concise",
        expertise_keywords=["implementation", "timeline", "feasibility", "administrative", "compliance", "rollout"],
    ),
}


# =============================================================================
# Message Analysis
# =============================================================================

@dataclass
class MentionedAgent:
    """An agent mentioned in a message."""
    agent_id: str
    mention_text: str
    position: int


@dataclass
class MessageAnalysis:
    """Analysis of a chat message for agent processing."""
    mentions: List[MentionedAgent]
    is_question: bool
    is_analysis_request: bool
    bill_mentioned: Optional[str]
    topics: List[str]
    sentiment: str  # positive, negative, neutral, questioning
    requires_response: bool


def analyze_message(content: str, agents: Dict[str, ChatAgent]) -> MessageAnalysis:
    """Analyze a message to determine agent response needs."""
    content_lower = content.lower()
    
    # Find @mentions
    mentions = []
    mention_pattern = r'@(\w+)'
    for match in re.finditer(mention_pattern, content):
        agent_id = match.group(1).lower()
        if agent_id in agents:
            mentions.append(MentionedAgent(
                agent_id=agent_id,
                mention_text=match.group(0),
                position=match.start(),
            ))
    
    # Detect questions
    is_question = any([
        '?' in content,
        content_lower.startswith(('what', 'how', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should')),
        'explain' in content_lower,
        'tell me' in content_lower,
    ])
    
    # Detect analysis requests
    analysis_keywords = ['analyze', 'analysis', 'run scenario', 'simulate', 'project', 'compare', 'evaluate']
    is_analysis_request = any(kw in content_lower for kw in analysis_keywords)
    
    # Detect bill mentions
    bill_pattern = r'\b(HR|H\.R\.|S\.|S)\s*(\d+)\b'
    bill_match = re.search(bill_pattern, content, re.IGNORECASE)
    bill_mentioned = f"{bill_match.group(1)}{bill_match.group(2)}" if bill_match else None
    
    # Extract topics based on keywords
    topics = []
    for agent in agents.values():
        for keyword in agent.expertise_keywords:
            if keyword in content_lower:
                if agent.specialty not in topics:
                    topics.append(agent.specialty)
                break
    
    # Determine sentiment
    positive_words = ['good', 'great', 'excellent', 'agree', 'thanks', 'helpful']
    negative_words = ['bad', 'wrong', 'disagree', 'incorrect', 'concern', 'problem']
    
    if is_question:
        sentiment = "questioning"
    elif any(w in content_lower for w in positive_words):
        sentiment = "positive"
    elif any(w in content_lower for w in negative_words):
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    # Determine if response required
    requires_response = bool(mentions) or (is_question and topics) or is_analysis_request
    
    return MessageAnalysis(
        mentions=mentions,
        is_question=is_question,
        is_analysis_request=is_analysis_request,
        bill_mentioned=bill_mentioned,
        topics=topics,
        sentiment=sentiment,
        requires_response=requires_response,
    )


# =============================================================================
# Response Generation
# =============================================================================

@dataclass
class AgentResponse:
    """Response generated by an agent."""
    agent_id: str
    content: str
    message_type: str
    metadata: Optional[Dict[str, Any]] = None
    trigger_action: Optional[str] = None  # analyze_bill, run_scenario, etc.
    action_params: Optional[Dict[str, Any]] = None


async def generate_response(
    agent: ChatAgent,
    message_analysis: MessageAnalysis,
    original_content: str,
    channel_context: List[Dict[str, Any]],
) -> Optional[AgentResponse]:
    """Generate an agent response to a message.
    
    In production, this would call an LLM. For now, we use templates.
    """
    # Check if this agent should respond
    is_mentioned = any(m.agent_id == agent.agent_id for m in message_analysis.mentions)
    is_expert = any(topic == agent.specialty for topic in message_analysis.topics)
    
    if not is_mentioned and not is_expert:
        return None
    
    # Build response based on message type
    if message_analysis.is_analysis_request and message_analysis.bill_mentioned:
        return AgentResponse(
            agent_id=agent.agent_id,
            content=f"I can analyze **{message_analysis.bill_mentioned}** for you. "
                   f"As the {agent.name}, I'll focus on {agent.specialty.lower()}. "
                   f"Would you like me to proceed with the analysis?",
            message_type="text",
            trigger_action="analyze_bill",
            action_params={"bill_id": message_analysis.bill_mentioned},
        )
    
    if message_analysis.is_question:
        # Generate educational response
        topic = message_analysis.topics[0] if message_analysis.topics else "policy analysis"
        return AgentResponse(
            agent_id=agent.agent_id,
            content=f"Great question about {topic}! {agent.description} "
                   f"Based on the current CBO baseline, I can provide detailed analysis. "
                   f"What specific aspect would you like me to focus on?",
            message_type="text",
        )
    
    if is_mentioned:
        # Direct mention response
        return AgentResponse(
            agent_id=agent.agent_id,
            content=f"Thanks for asking me! {agent.description} "
                   f"How can I help with your analysis today?",
            message_type="text",
        )
    
    return None


async def generate_proactive_insight(
    agent: ChatAgent,
    channel_context: List[Dict[str, Any]],
) -> Optional[AgentResponse]:
    """Generate a proactive insight based on channel discussion.
    
    Only triggers if the conversation is relevant to the agent's expertise.
    """
    if not channel_context:
        return None
    
    # Analyze recent messages for relevant topics
    recent_content = " ".join([m.get("content", "") for m in channel_context[-10:]])
    
    # Check if any expertise keywords appear
    matches = [kw for kw in agent.expertise_keywords if kw in recent_content.lower()]
    
    if not matches:
        return None
    
    # Generate insight (in production, this would use LLM)
    topic = matches[0]
    insight = f"💡 **Insight from {agent.name}:** "
    insight += f"I noticed the discussion touches on {topic}. "
    insight += f"Did you know that according to CBO projections, this area shows significant uncertainty? "
    insight += f"I can provide a more detailed analysis if helpful."
    
    return AgentResponse(
        agent_id=agent.agent_id,
        content=insight,
        message_type="text",
        metadata={"proactive": True, "topic": topic},
    )


# =============================================================================
# Agent Chat Manager
# =============================================================================

class AgentChatManager:
    """Manager for agent participation in chat channels.
    
    Coordinates multiple agents, handles rate limiting,
    and manages response generation.
    """
    
    def __init__(
        self,
        config: Optional[AgentChatConfig] = None,
        agents: Optional[Dict[str, ChatAgent]] = None,
    ):
        self.config = config or AgentChatConfig()
        self.agents = agents or DEFAULT_AGENTS.copy()
        self.logger = logging.getLogger(__name__)
        
        # Track agent activity per channel
        self._channel_agent_activity: Dict[str, Dict[str, datetime]] = {}
        self._pending_responses: Dict[str, List[AgentResponse]] = {}
    
    async def process_message(
        self,
        message: Dict[str, Any],
        channel_id: str,
        channel_agents: List[str],
    ) -> List[AgentResponse]:
        """Process a new message and generate agent responses.
        
        Args:
            message: The incoming message dict
            channel_id: ID of the channel
            channel_agents: List of agent IDs in this channel
            
        Returns:
            List of agent responses to send
        """
        content = message.get("content", "")
        sender_type = message.get("sender_type", "user")
        
        # Don't respond to agent or system messages
        if sender_type != "user":
            return []
        
        # Analyze the message
        analysis = analyze_message(content, self.agents)
        
        if not analysis.requires_response:
            return []
        
        # Generate responses from relevant agents
        responses = []
        
        for agent_id in channel_agents:
            if agent_id not in self.agents:
                continue
            
            agent = self.agents[agent_id]
            
            # Check rate limits
            if not self._check_rate_limit(agent):
                self.logger.debug(f"Agent {agent_id} rate limited")
                continue
            
            # Get channel context for response generation
            context = await self._get_channel_context(channel_id)
            
            # Generate response
            response = await generate_response(
                agent=agent,
                message_analysis=analysis,
                original_content=content,
                channel_context=context,
            )
            
            if response:
                # Apply response delay (simulate typing)
                await asyncio.sleep(self.config.response_delay_seconds)
                
                # Update rate limit counters
                self._record_message(agent)
                
                responses.append(response)
        
        return responses
    
    async def check_proactive_insights(
        self,
        channel_id: str,
        channel_agents: List[str],
    ) -> List[AgentResponse]:
        """Check if any agents should share proactive insights.
        
        Called periodically to allow agents to contribute to ongoing discussions.
        """
        if not self.config.enable_proactive_insights:
            return []
        
        responses = []
        context = await self._get_channel_context(channel_id)
        
        if len(context) < self.config.min_messages_before_insight:
            return []
        
        for agent_id in channel_agents:
            if agent_id not in self.agents:
                continue
            
            agent = self.agents[agent_id]
            
            # Check if agent has contributed recently
            if self._recently_active(agent_id, channel_id):
                continue
            
            # Check rate limits
            if not self._check_rate_limit(agent):
                continue
            
            # Generate proactive insight
            response = await generate_proactive_insight(agent, context)
            
            if response:
                self._record_message(agent)
                self._record_activity(agent_id, channel_id)
                responses.append(response)
        
        return responses
    
    async def trigger_analysis(
        self,
        channel_id: str,
        analysis_type: str,
        params: Dict[str, Any],
        requesting_user: str,
    ) -> Optional[AgentResponse]:
        """Trigger an analysis from chat.
        
        Args:
            channel_id: Channel where analysis was requested
            analysis_type: Type of analysis (analyze_bill, run_scenario, etc.)
            params: Analysis parameters
            requesting_user: User who requested the analysis
        """
        self.logger.info(f"Triggering {analysis_type} in channel {channel_id}")
        
        try:
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            
            if analysis_type == "analyze_bill":
                result = await tools.analyze_bill(
                    bill_id=params.get("bill_id", ""),
                    channel_id=channel_id,
                )
                
                return AgentResponse(
                    agent_id="swarm_coordinator",
                    content=f"Analysis started for **{params.get('bill_id')}**. "
                           f"I'll post results here when complete.",
                    message_type="action",
                    metadata={"action": "analysis_started", "analysis_id": result.analysis_id},
                )
            
            elif analysis_type == "run_scenario":
                result = await tools.run_scenario(
                    scenario_type=params.get("scenario_type", "baseline"),
                    parameters=params.get("parameters"),
                    channel_id=channel_id,
                )
                
                return AgentResponse(
                    agent_id="scenario_runner",
                    content=f"Scenario simulation started. Results will appear shortly.",
                    message_type="action",
                    metadata={"action": "scenario_started"},
                )
            
        except Exception as e:
            self.logger.error(f"Analysis trigger failed: {e}")
            return AgentResponse(
                agent_id="system",
                content=f"⚠️ Could not start analysis: {str(e)}",
                message_type="error",
            )
        
        return None
    
    def add_agent_to_channel(
        self,
        agent_id: str,
        channel_id: str,
    ) -> bool:
        """Record that an agent has joined a channel."""
        if agent_id not in self.agents:
            return False
        
        # Initialize channel tracking if needed
        if channel_id not in self._channel_agent_activity:
            self._channel_agent_activity[channel_id] = {}
        
        self.logger.info(f"Agent {agent_id} added to channel {channel_id}")
        return True
    
    def remove_agent_from_channel(
        self,
        agent_id: str,
        channel_id: str,
    ) -> bool:
        """Record that an agent has left a channel."""
        if channel_id in self._channel_agent_activity:
            self._channel_agent_activity[channel_id].pop(agent_id, None)
        
        self.logger.info(f"Agent {agent_id} removed from channel {channel_id}")
        return True
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about an agent."""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "specialty": agent.specialty,
            "description": agent.description,
            "avatar": agent.avatar_emoji,
        }
    
    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agents."""
        return [self.get_agent_info(aid) for aid in self.agents.keys()]
    
    # -------------------------------------------------------------------------
    # Private Helpers
    # -------------------------------------------------------------------------
    
    def _check_rate_limit(self, agent: ChatAgent) -> bool:
        """Check if agent is within rate limits."""
        now = datetime.now(timezone.utc)
        
        # Reset minute counter if needed
        if agent.minute_reset_time is None or now > agent.minute_reset_time:
            agent.messages_this_minute = 0
            agent.minute_reset_time = now + timedelta(minutes=1)
        
        # Reset hour counter if needed
        if agent.hour_reset_time is None or now > agent.hour_reset_time:
            agent.messages_this_hour = 0
            agent.hour_reset_time = now + timedelta(hours=1)
        
        # Check limits
        if agent.messages_this_minute >= self.config.max_messages_per_minute:
            return False
        if agent.messages_this_hour >= self.config.max_messages_per_hour:
            return False
        
        return True
    
    def _record_message(self, agent: ChatAgent) -> None:
        """Record that an agent sent a message."""
        agent.messages_this_minute += 1
        agent.messages_this_hour += 1
        agent.last_message_time = datetime.now(timezone.utc)
    
    def _record_activity(self, agent_id: str, channel_id: str) -> None:
        """Record agent activity in a channel."""
        if channel_id not in self._channel_agent_activity:
            self._channel_agent_activity[channel_id] = {}
        self._channel_agent_activity[channel_id][agent_id] = datetime.now(timezone.utc)
    
    def _recently_active(self, agent_id: str, channel_id: str) -> bool:
        """Check if agent was recently active in channel."""
        if channel_id not in self._channel_agent_activity:
            return False
        
        last_active = self._channel_agent_activity[channel_id].get(agent_id)
        if not last_active:
            return False
        
        threshold = timedelta(minutes=self.config.insight_frequency_minutes)
        return datetime.now(timezone.utc) - last_active < threshold
    
    async def _get_channel_context(
        self,
        channel_id: str,
        message_count: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get recent messages from channel for context."""
        try:
            from api.chat_api import ChatService
            from api.database import get_db_session
            
            with get_db_session() as session:
                service = ChatService(session)
                messages = service.get_messages(
                    channel_id=channel_id,
                    limit=message_count,
                )
                
                return [
                    {
                        "sender_id": m.sender_id,
                        "sender_type": m.sender_type.value,
                        "content": m.content,
                        "timestamp": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in messages
                ]
        except Exception as e:
            self.logger.warning(f"Could not get channel context: {e}")
            return []


# =============================================================================
# Integration with WebSocket
# =============================================================================

class AgentWebSocketHandler:
    """Handle agent responses via WebSocket.
    
    Integrates AgentChatManager with WebSocket streaming
    for real-time agent participation.
    """
    
    def __init__(self, manager: Optional[AgentChatManager] = None):
        self.manager = manager or AgentChatManager()
        self.logger = logging.getLogger(__name__)
    
    async def handle_new_message(
        self,
        message: Dict[str, Any],
        channel_id: str,
        channel_agents: List[str],
        broadcast_callback,
    ) -> None:
        """Handle a new message and broadcast agent responses.
        
        Args:
            message: The incoming message
            channel_id: Channel ID
            channel_agents: Agents in channel
            broadcast_callback: Function to broadcast messages
        """
        # Process message and get responses
        responses = await self.manager.process_message(
            message=message,
            channel_id=channel_id,
            channel_agents=channel_agents,
        )
        
        # Broadcast each response
        for response in responses:
            agent_message = {
                "message_id": str(uuid4()),
                "channel_id": channel_id,
                "sender_id": response.agent_id,
                "sender_type": "agent",
                "sender_name": self.manager.agents[response.agent_id].name,
                "content": response.content,
                "message_type": response.message_type,
                "metadata": response.metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            await broadcast_callback(channel_id, "new_message", agent_message)
            
            # If response triggers an action, execute it
            if response.trigger_action:
                action_response = await self.manager.trigger_analysis(
                    channel_id=channel_id,
                    analysis_type=response.trigger_action,
                    params=response.action_params or {},
                    requesting_user=message.get("sender_id", "unknown"),
                )
                
                if action_response:
                    action_message = {
                        "message_id": str(uuid4()),
                        "channel_id": channel_id,
                        "sender_id": action_response.agent_id,
                        "sender_type": "agent",
                        "content": action_response.content,
                        "message_type": action_response.message_type,
                        "metadata": action_response.metadata,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                    await broadcast_callback(channel_id, "new_message", action_message)
