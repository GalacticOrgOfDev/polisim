"""Agent Factory for creating and managing agents.

This module provides factory functions and classes for creating agents
based on configuration, enabling dynamic agent instantiation.
"""

import logging
from typing import Dict, List, Optional, Type
from pathlib import Path
import yaml

from core.agents.types import AgentType
from core.agents.models import AgentConfig, SwarmConfig
from core.agents.base_agent import BaseAgent
from core.agents.fiscal_agent import FiscalAgent
from core.agents.economic_agent import EconomicAgent
from core.agents.healthcare_agent import HealthcareAgent
from core.agents.social_security_agent import SocialSecurityAgent
from core.agents.judge_agent import JudgeAgent


logger = logging.getLogger(__name__)


# Registry mapping AgentType to implementation class
AGENT_REGISTRY: Dict[AgentType, Type[BaseAgent]] = {
    AgentType.FISCAL: FiscalAgent,
    AgentType.ECONOMIC: EconomicAgent,
    AgentType.HEALTHCARE: HealthcareAgent,
    AgentType.SOCIAL_SECURITY: SocialSecurityAgent,
    AgentType.JUDGE: JudgeAgent,
    # Tier 2 agents (stubs for now)
    # AgentType.EQUITY: EquityAgent,
    # AgentType.IMPLEMENTATION: ImplementationAgent,
    # Tier 3 agents (future)
    # AgentType.BEHAVIORAL: BehavioralAgent,
    # AgentType.LEGAL: LegalAgent,
}


def create_agent(
    agent_type: AgentType,
    config: Optional[AgentConfig] = None
) -> BaseAgent:
    """Create an agent of the specified type.
    
    Args:
        agent_type: The type of agent to create
        config: Optional configuration. If not provided, uses defaults.
    
    Returns:
        Instantiated agent
    
    Raises:
        ValueError: If agent_type is not supported
    """
    if agent_type not in AGENT_REGISTRY:
        raise ValueError(
            f"Unsupported agent type: {agent_type}. "
            f"Supported types: {list(AGENT_REGISTRY.keys())}"
        )
    
    agent_class = AGENT_REGISTRY[agent_type]
    
    if config is None:
        config = AgentConfig(agent_type=agent_type)
    elif config.agent_type != agent_type:
        logger.warning(
            f"Config agent_type ({config.agent_type}) doesn't match "
            f"requested type ({agent_type}). Using requested type."
        )
        config.agent_type = agent_type
    
    logger.info(f"Creating {agent_type.value} agent with model {config.model}")
    
    return agent_class(config)


class AgentFactory:
    """Factory for creating and managing agent instances.
    
    Supports creating agents from configuration files, managing
    agent pools, and providing tier-based agent creation.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize the factory.
        
        Args:
            config_path: Optional path to agent configuration YAML file
        """
        self.config_path = config_path
        self._config: Optional[SwarmConfig] = None
        self._agents: Dict[str, BaseAgent] = {}
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: Path) -> SwarmConfig:
        """Load configuration from a YAML file.
        
        Args:
            config_path: Path to configuration file
        
        Returns:
            Loaded SwarmConfig
        """
        logger.info(f"Loading agent configuration from {config_path}")
        
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Parse agent configs
        agents_config = {}
        for agent_name, agent_dict in config_dict.get("agents", {}).items():
            agent_type_str = agent_dict.get("type", agent_name)
            try:
                agent_type = AgentType(agent_type_str)
            except ValueError:
                logger.warning(f"Unknown agent type: {agent_type_str}, skipping")
                continue
            
            agents_config[agent_name] = AgentConfig(
                agent_type=agent_type,
                model=agent_dict.get("model", "claude-sonnet-4-20250514"),
                temperature=agent_dict.get("temperature", 0.3),
                max_tokens=agent_dict.get("max_tokens", 4096),
                specialization_prompt=agent_dict.get("specialization_prompt", ""),
                confidence_threshold=agent_dict.get("confidence_threshold", 0.7),
                timeout_seconds=agent_dict.get("timeout_seconds", 60.0),
                retry_attempts=agent_dict.get("retry_attempts", 3),
                custom_settings=agent_dict.get("custom_settings", {}),
            )
        
        self._config = SwarmConfig(
            agents=agents_config,
            max_parallel_agents=config_dict.get("max_parallel_agents", 8),
            global_timeout_seconds=config_dict.get("global_timeout_seconds", 300.0),
            token_budget_per_analysis=config_dict.get("token_budget_per_analysis", 100000),
            max_debate_rounds=config_dict.get("max_debate_rounds", 3),
            convergence_threshold=config_dict.get("convergence_threshold", 0.8),
            debate_timeout_seconds=config_dict.get("debate_timeout_seconds", 180.0),
            consensus_threshold=config_dict.get("consensus_threshold", 0.75),
            enable_streaming=config_dict.get("enable_streaming", True),
            thought_batch_window_ms=config_dict.get("thought_batch_window_ms", 100),
        )
        
        return self._config
    
    @property
    def config(self) -> SwarmConfig:
        """Get the current configuration."""
        if self._config is None:
            self._config = SwarmConfig()
        return self._config
    
    def create_agent(
        self,
        agent_type: AgentType,
        config_override: Optional[AgentConfig] = None
    ) -> BaseAgent:
        """Create an agent of the specified type.
        
        Args:
            agent_type: Type of agent to create
            config_override: Optional config to override factory config
        
        Returns:
            Created agent instance
        """
        # Get config from factory config or use override
        config = config_override
        
        if config is None and self._config:
            # Look for agent config by type name
            type_name = agent_type.value
            if type_name in self._config.agents:
                config = self._config.agents[type_name]
        
        agent = create_agent(agent_type, config)
        self._agents[agent.agent_id] = agent
        
        return agent
    
    def create_tier1_agents(self) -> Dict[str, BaseAgent]:
        """Create all Tier 1 (MVP) agents.
        
        Returns:
            Dictionary of agent_id -> agent for all Tier 1 agents
        """
        tier1_types = [
            AgentType.FISCAL,
            AgentType.ECONOMIC,
            AgentType.HEALTHCARE,
            AgentType.SOCIAL_SECURITY,
        ]
        
        agents = {}
        for agent_type in tier1_types:
            agent = self.create_agent(agent_type)
            agents[agent.agent_id] = agent
        
        logger.info(f"Created {len(agents)} Tier 1 agents")
        return agents
    
    def create_all_agents(
        self,
        include_judge: bool = True
    ) -> Dict[str, BaseAgent]:
        """Create all available agents.
        
        Args:
            include_judge: Whether to include the Judge agent
        
        Returns:
            Dictionary of agent_id -> agent
        """
        agents = {}
        
        for agent_type in AGENT_REGISTRY.keys():
            if agent_type == AgentType.JUDGE and not include_judge:
                continue
            if agent_type == AgentType.COORDINATOR:
                continue  # Coordinator is not an agent
            
            try:
                agent = self.create_agent(agent_type)
                agents[agent.agent_id] = agent
            except ValueError as e:
                logger.warning(f"Could not create {agent_type} agent: {e}")
        
        logger.info(f"Created {len(agents)} agents")
        return agents
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID.
        
        Args:
            agent_id: The agent's unique identifier
        
        Returns:
            The agent if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[str]:
        """List all created agent IDs.
        
        Returns:
            List of agent IDs
        """
        return list(self._agents.keys())
    
    def clear_agents(self) -> None:
        """Clear all created agents."""
        self._agents.clear()
        logger.info("Cleared all agents from factory")


# Default factory instance
_default_factory: Optional[AgentFactory] = None


def get_default_factory() -> AgentFactory:
    """Get or create the default agent factory.
    
    Returns:
        The default AgentFactory instance
    """
    global _default_factory
    if _default_factory is None:
        _default_factory = AgentFactory()
    return _default_factory


def create_agent_from_config(
    agent_type_str: str,
    **kwargs
) -> BaseAgent:
    """Create an agent from string type and keyword arguments.
    
    This is a convenience function for creating agents without
    explicitly using AgentConfig.
    
    Args:
        agent_type_str: String representation of agent type
        **kwargs: Additional configuration parameters
    
    Returns:
        Created agent
    """
    agent_type = AgentType(agent_type_str)
    
    config = AgentConfig(
        agent_type=agent_type,
        **kwargs
    )
    
    return create_agent(agent_type, config)
