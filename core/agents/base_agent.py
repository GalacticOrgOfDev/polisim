"""Base Agent abstract class for the Multi-Agent Swarm system.

This module defines the abstract interface that all specialized agents must
implement, providing a consistent API for analysis, critique, and voting.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Awaitable, Dict, List, Optional
import logging
import asyncio
from uuid import uuid4

from core.agents.types import (
    AgentType,
    ThoughtType,
    VOTE_WEIGHTS,
)
from core.agents.models import (
    AgentConfig,
    AgentAnalysis,
    Finding,
    Assumption,
    Evidence,
    Critique,
    Vote,
    Position,
    AgentThought,
    AnalysisEvent,
    Proposal,
)


logger = logging.getLogger(__name__)


# LLM client import (lazy to avoid circular imports)
_llm_client = None

def _get_llm_client():
    """Lazy import of LLM client to avoid circular imports."""
    global _llm_client
    if _llm_client is None:
        from core.agents.llm_client import get_llm_client
        _llm_client = get_llm_client()
    return _llm_client


logger = logging.getLogger(__name__)


class AnalysisContext:
    """Context provided to agents during analysis.
    
    Contains the bill being analyzed, supporting data, configuration,
    and methods for agents to access PoliSim's existing models.
    """
    
    def __init__(
        self,
        bill_id: str,
        bill_text: str,
        bill_sections: Dict[str, str],
        extracted_mechanisms: Dict[str, Any],
        baseline_data: Dict[str, Any],
        scenario: str = "baseline",
        projection_years: int = 10,
        additional_context: Dict[str, Any] = None,
    ):
        self.bill_id = bill_id
        self.bill_text = bill_text
        self.bill_sections = bill_sections
        self.extracted_mechanisms = extracted_mechanisms
        self.baseline_data = baseline_data
        self.scenario = scenario
        self.projection_years = projection_years
        self.additional_context = additional_context or {}
        
        # Pre-computed simulation results available to agents
        self.fiscal_projections: Optional[Dict[str, Any]] = None
        self.healthcare_projections: Optional[Dict[str, Any]] = None
        self.ss_projections: Optional[Dict[str, Any]] = None
        self.economic_projections: Optional[Dict[str, Any]] = None
    
    def get_section(self, section_name: str) -> Optional[str]:
        """Get a specific section of the bill."""
        return self.bill_sections.get(section_name)
    
    def get_mechanism(self, mechanism_type: str) -> Optional[Dict[str, Any]]:
        """Get extracted mechanisms of a specific type."""
        return self.extracted_mechanisms.get(mechanism_type)
    
    def get_baseline(self, metric: str) -> Optional[Any]:
        """Get baseline data for a specific metric."""
        return self.baseline_data.get(metric)


class BaseAgent(ABC):
    """Abstract base class for all swarm agents.
    
    Each agent specializes in a particular domain (fiscal, healthcare, etc.)
    and must implement methods for analysis, critique, and voting.
    
    Attributes:
        agent_id: Unique identifier for this agent instance
        agent_type: The agent's specialization type
        config: Agent configuration settings
        specialty: Human-readable specialty description
        confidence_threshold: Minimum confidence for reporting findings
    """
    
    def __init__(self, config: AgentConfig):
        """Initialize the agent with configuration.
        
        Args:
            config: AgentConfig with model settings and thresholds
        """
        self.agent_id = f"{config.agent_type.value}_{str(uuid4())[:8]}"
        self.agent_type = config.agent_type
        self.config = config
        self.specialty = self._get_specialty_description()
        self.confidence_threshold = config.confidence_threshold
        
        # Runtime state
        self._current_analysis_id: Optional[str] = None
        self._event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None
        
        logger.info(f"Initialized {self.agent_type.value} agent: {self.agent_id}")
    
    @abstractmethod
    def _get_specialty_description(self) -> str:
        """Return a description of this agent's specialty."""
        pass
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt for this agent's LLM calls."""
        pass
    
    @abstractmethod
    def _get_analysis_prompt(self, context: AnalysisContext) -> str:
        """Return the analysis prompt for a given context.
        
        Args:
            context: The analysis context with bill and supporting data
        
        Returns:
            Formatted prompt for the LLM to perform analysis
        """
        pass
    
    @abstractmethod
    def _get_critique_prompt(self, analysis: AgentAnalysis) -> str:
        """Return the critique prompt for another agent's analysis.
        
        Args:
            analysis: Another agent's analysis to critique
        
        Returns:
            Formatted prompt for the LLM to generate critiques
        """
        pass
    
    @abstractmethod
    async def _parse_analysis_response(
        self,
        response: str,
        context: AnalysisContext
    ) -> AgentAnalysis:
        """Parse LLM response into structured AgentAnalysis.
        
        Args:
            response: Raw LLM response text
            context: The original analysis context
        
        Returns:
            Structured AgentAnalysis object
        """
        pass
    
    @abstractmethod
    async def _parse_critique_response(
        self,
        response: str,
        target_analysis: AgentAnalysis
    ) -> List[Critique]:
        """Parse LLM response into structured Critiques.
        
        Args:
            response: Raw LLM response text
            target_analysis: The analysis being critiqued
        
        Returns:
            List of Critique objects
        """
        pass
    
    # =========================================================================
    # Public API - Required by all agents
    # =========================================================================
    
    @abstractmethod
    async def analyze(
        self,
        context: AnalysisContext,
        event_callback: Optional[Callable[[AnalysisEvent], Awaitable[None]]] = None
    ) -> AgentAnalysis:
        """Analyze a bill and return findings.
        
        This is the primary method that each agent implements to perform
        domain-specific analysis on legislation.
        
        Args:
            context: AnalysisContext containing bill text, extracted mechanisms,
                    baseline data, and simulation parameters
            event_callback: Optional callback for streaming intermediate thoughts
        
        Returns:
            AgentAnalysis containing findings, assumptions, confidence scores
        """
        pass
    
    @abstractmethod
    async def critique(
        self,
        other_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> List[Critique]:
        """Critique another agent's analysis.
        
        Used during cross-review phase to identify issues with methodology,
        assumptions, or conclusions.
        
        Args:
            other_analysis: Another agent's AgentAnalysis to critique
            context: The original analysis context for reference
        
        Returns:
            List of Critique objects identifying issues
        """
        pass
    
    @abstractmethod
    async def vote(
        self,
        proposals: List[Proposal],
        context: AnalysisContext
    ) -> List[Vote]:
        """Vote on a list of proposals.
        
        Used during consensus phase to determine which conclusions
        the swarm agrees on.
        
        Args:
            proposals: List of proposals to vote on
            context: Analysis context for reference
        
        Returns:
            List of Vote objects with support levels and reasoning
        """
        pass
    
    # =========================================================================
    # Optional methods with default implementations
    # =========================================================================
    
    async def respond_to_critique(
        self,
        critique: Critique,
        my_analysis: AgentAnalysis,
        context: AnalysisContext
    ) -> str:
        """Respond to a critique of this agent's analysis.
        
        Default implementation acknowledges the critique.
        Agents can override for more sophisticated rebuttals.
        
        Args:
            critique: The critique to respond to
            my_analysis: This agent's original analysis
            context: Analysis context
        
        Returns:
            Rebuttal text
        """
        return f"Acknowledged critique regarding {critique.critique_type.value}. " \
               f"Will consider revising analysis based on: {critique.argument}"
    
    async def update_position(
        self,
        current_position: Position,
        new_evidence: List[Evidence],
        critiques: List[Critique]
    ) -> Position:
        """Update position based on new evidence and critiques.
        
        Default implementation maintains current position.
        Agents can override for dynamic position updates during debate.
        
        Args:
            current_position: The agent's current position
            new_evidence: New evidence presented
            critiques: Critiques received
        
        Returns:
            Updated Position (may be same as current)
        """
        return current_position
    
    def get_weight_for_topic(self, topic: str) -> float:
        """Get this agent's weight for a specific topic.
        
        Returns higher weight for topics matching this agent's specialty.
        
        Args:
            topic: The topic being discussed
        
        Returns:
            Weight between 0.5 and 2.0
        """
        # Default: return 1.0, specialized agents override
        return 1.0
    
    # =========================================================================
    # Utility methods
    # =========================================================================
    
    async def emit_thought(
        self,
        thought_type: ThoughtType,
        content: str,
        confidence: Optional[float] = None,
        related_section: Optional[str] = None
    ) -> None:
        """Emit an intermediate thought for streaming.
        
        Args:
            thought_type: Type of thought (observation, hypothesis, etc.)
            content: The thought content
            confidence: Optional confidence level
            related_section: Optional bill section reference
        """
        if self._event_callback is None:
            return
        
        from core.agents.models import AgentThought, AnalysisEvent
        from core.agents.types import AnalysisEventType
        
        thought = AgentThought(
            agent_id=self.agent_id,
            thought_type=thought_type,
            content=content,
            confidence=confidence,
            related_section=related_section,
        )
        
        event = AnalysisEvent(
            event_type=AnalysisEventType.AGENT_THINKING,
            analysis_id=self._current_analysis_id or "",
            agent_id=self.agent_id,
            data={"thought": thought.__dict__},
        )
        
        await self._event_callback(event)
    
    def create_finding(
        self,
        category: str,
        description: str,
        impact_magnitude: str,
        confidence: float,
        **kwargs
    ) -> Finding:
        """Helper to create a Finding with proper typing.
        
        Args:
            category: FindingCategory value
            description: Finding description
            impact_magnitude: ImpactMagnitude value
            confidence: Confidence score 0-1
            **kwargs: Additional Finding fields
        
        Returns:
            Finding object
        """
        from core.agents.types import FindingCategory, ImpactMagnitude
        
        return Finding(
            category=FindingCategory(category) if isinstance(category, str) else category,
            description=description,
            impact_magnitude=ImpactMagnitude(impact_magnitude) if isinstance(impact_magnitude, str) else impact_magnitude,
            confidence=confidence,
            **kwargs
        )
    
    def create_assumption(
        self,
        category: str,
        description: str,
        value: Any = None,
        source: Optional[str] = None,
        confidence: float = 0.8
    ) -> Assumption:
        """Helper to create an Assumption.
        
        Args:
            category: Assumption category
            description: Description of the assumption
            value: The assumed value
            source: Source of the assumption
            confidence: Confidence in the assumption
        
        Returns:
            Assumption object
        """
        return Assumption(
            category=category,
            description=description,
            value=value,
            source=source,
            confidence=confidence,
        )
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id}, type={self.agent_type.value})"
    
    def __str__(self) -> str:
        return f"{self.agent_type.value.title()} Agent ({self.agent_id})"
    
    # =========================================================================
    # LLM Integration Methods
    # =========================================================================
    
    async def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        stream_callback: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> str:
        """Make an LLM call with the agent's configuration.
        
        Args:
            system_prompt: System-level instructions
            user_prompt: User input/query
            stream_callback: Optional callback for streaming text
        
        Returns:
            Generated response text
        """
        client = _get_llm_client()
        
        # Wrap stream callback to emit thoughts
        async def wrapped_callback(chunk):
            if stream_callback:
                await stream_callback(chunk.content)
            # Emit as thought for live streaming
            if self._event_callback and chunk.content:
                await self.emit_thought(
                    ThoughtType.REASONING,
                    chunk.content,
                )
        
        response = await client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream_callback=wrapped_callback if stream_callback or self._event_callback else None,
        )
        
        return response.content
    
    async def call_llm_for_analysis(
        self,
        context: "AnalysisContext",
    ) -> str:
        """Make an LLM call for bill analysis.
        
        Convenience method that uses the agent's configured prompts.
        
        Args:
            context: Analysis context
        
        Returns:
            Generated analysis response
        """
        return await self.call_llm(
            system_prompt=self._get_system_prompt(),
            user_prompt=self._get_analysis_prompt(context),
        )
    
    async def call_llm_for_critique(
        self,
        target_analysis: AgentAnalysis,
    ) -> str:
        """Make an LLM call for critiquing another analysis.
        
        Args:
            target_analysis: The analysis to critique
        
        Returns:
            Generated critique response
        """
        return await self.call_llm(
            system_prompt=self._get_system_prompt(),
            user_prompt=self._get_critique_prompt(target_analysis),
        )
