"""Tests for LLM Client and Execution Strategies.

These tests verify:
1. LLM client configuration and mock responses
2. Execution strategy behaviors
3. Resource management
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from core.agents.llm_client import (
    LLMClient,
    LLMConfig,
    LLMResponse,
    LLMProvider,
    LLMMessage,
    StreamChunk,
    get_llm_client,
    configure_llm_client,
)
from core.agents.execution_strategies import (
    ExecutionStrategy,
    ExecutionStrategyType,
    ExecutionResult,
    ExecutionStats,
    ResourceBudget,
    AllAtOnceStrategy,
    StagedStrategy,
    AdaptiveStrategy,
    PriorityStrategy,
    create_execution_strategy,
)
from core.agents import (
    AgentType,
    FiscalAgent,
    EconomicAgent,
    HealthcareAgent,
    AgentConfig,
)
from core.agents.base_agent import AnalysisContext


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def llm_config():
    """Create test LLM config."""
    return LLMConfig(
        provider=LLMProvider.LOCAL,
        model="test-model",
        temperature=0.5,
        max_tokens=1000,
    )


@pytest.fixture
def sample_context():
    """Create a sample analysis context."""
    return AnalysisContext(
        bill_id="TEST-001",
        bill_text="Test bill text for analysis",
        bill_sections={"sec1": "Section 1 content"},
        extracted_mechanisms={"tax": [{"name": "Tax change"}]},
        baseline_data={"revenue": 1000},
    )


@pytest.fixture
def sample_agents():
    """Create sample agents for testing."""
    return {
        "fiscal": FiscalAgent(),
        "economic": EconomicAgent(),
        "healthcare": HealthcareAgent(),
    }


# =============================================================================
# LLM Client Tests
# =============================================================================

class TestLLMConfig:
    """Test LLM configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = LLMConfig()
        
        assert config.provider == LLMProvider.ANTHROPIC
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.3
        assert config.max_tokens == 4096
        assert config.timeout_seconds == 60.0
        assert config.retry_attempts == 3
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="custom-model",
            temperature=0.7,
        )
        
        assert config.provider == LLMProvider.LOCAL
        assert config.model == "custom-model"
        assert config.temperature == 0.7


class TestLLMClient:
    """Test LLM client."""
    
    def test_client_creation(self, llm_config):
        """Test client initialization."""
        client = LLMClient(llm_config)
        
        assert client.config == llm_config
        assert client._total_input_tokens == 0
        assert client._request_count == 0
    
    def test_usage_stats(self, llm_config):
        """Test usage statistics tracking."""
        client = LLMClient(llm_config)
        
        stats = client.get_usage_stats()
        
        assert stats["total_input_tokens"] == 0
        assert stats["total_output_tokens"] == 0
        assert stats["request_count"] == 0
    
    def test_reset_usage_stats(self, llm_config):
        """Test resetting usage stats."""
        client = LLMClient(llm_config)
        client._total_input_tokens = 100
        client._request_count = 5
        
        client.reset_usage_stats()
        
        assert client._total_input_tokens == 0
        assert client._request_count == 0
    
    def test_mock_response_generation(self, llm_config):
        """Test mock response content generation."""
        client = LLMClient(llm_config)
        
        # Test analysis mock
        content = client._generate_mock_content(
            "You are an analyst",
            "Analyze this policy",
        )
        
        assert "findings" in content or "response" in content
    
    def test_mock_critique_response(self, llm_config):
        """Test mock critique response."""
        client = LLMClient(llm_config)
        
        content = client._generate_mock_content(
            "You are a critic",
            "Critique this analysis",
        )
        
        assert "critiques" in content or "response" in content


class TestLLMResponse:
    """Test LLM response model."""
    
    def test_response_creation(self):
        """Test response model."""
        response = LLMResponse(
            content="Test response",
            model="test-model",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
        )
        
        assert response.content == "Test response"
        assert response.total_tokens == 150
    
    def test_stream_chunk(self):
        """Test stream chunk model."""
        chunk = StreamChunk(
            content="Hello",
            is_final=False,
            accumulated_content="Hello",
        )
        
        assert chunk.content == "Hello"
        assert not chunk.is_final


# =============================================================================
# Execution Strategy Tests
# =============================================================================

class TestResourceBudget:
    """Test resource budget management."""
    
    def test_default_budget(self):
        """Test default budget values."""
        budget = ResourceBudget()
        
        assert budget.max_concurrent == 8
        assert budget.max_tokens_total == 100000
        assert budget.tokens_used == 0
        assert budget.agents_active == 0
    
    def test_can_start_agent(self):
        """Test agent start check."""
        budget = ResourceBudget(max_concurrent=2)
        
        assert budget.can_start_agent()
        
        budget.agents_active = 2
        assert not budget.can_start_agent()
    
    def test_register_agent_lifecycle(self):
        """Test agent registration."""
        budget = ResourceBudget()
        
        budget.register_agent_start()
        assert budget.agents_active == 1
        
        budget.register_agent_complete(100)
        assert budget.agents_active == 0
        assert budget.tokens_used == 100


class TestExecutionStrategies:
    """Test execution strategy implementations."""
    
    def test_create_all_at_once_strategy(self):
        """Test creating all-at-once strategy."""
        strategy = create_execution_strategy(ExecutionStrategyType.ALL_AT_ONCE)
        
        assert isinstance(strategy, AllAtOnceStrategy)
    
    def test_create_staged_strategy(self):
        """Test creating staged strategy."""
        strategy = create_execution_strategy(ExecutionStrategyType.STAGED)
        
        assert isinstance(strategy, StagedStrategy)
    
    def test_create_adaptive_strategy(self):
        """Test creating adaptive strategy."""
        strategy = create_execution_strategy(ExecutionStrategyType.ADAPTIVE)
        
        assert isinstance(strategy, AdaptiveStrategy)
    
    def test_create_priority_strategy(self):
        """Test creating priority strategy."""
        strategy = create_execution_strategy(ExecutionStrategyType.PRIORITY)
        
        assert isinstance(strategy, PriorityStrategy)
    
    def test_strategy_with_custom_budget(self):
        """Test creating strategy with custom budget."""
        budget = ResourceBudget(max_concurrent=4)
        strategy = create_execution_strategy(
            ExecutionStrategyType.ALL_AT_ONCE,
            budget=budget,
        )
        
        assert strategy.budget.max_concurrent == 4


class TestStagedStrategy:
    """Test staged execution strategy."""
    
    def test_stage_ordering(self):
        """Test that stages are properly ordered."""
        # Fiscal should be in stage 1, Economic in stage 2
        stages = StagedStrategy.STAGES
        
        # Stage 1 should have FISCAL
        assert AgentType.FISCAL in stages[0]
        
        # Stage 2 should have ECONOMIC
        assert AgentType.ECONOMIC in stages[1]
        
        # Stage 3 should have HEALTHCARE and SOCIAL_SECURITY
        assert AgentType.HEALTHCARE in stages[2]


class TestAdaptiveStrategy:
    """Test adaptive execution strategy."""
    
    def test_trigger_keywords(self):
        """Test that trigger keywords are defined."""
        keywords = AdaptiveStrategy.TRIGGER_KEYWORDS
        
        assert AgentType.HEALTHCARE in keywords
        assert AgentType.SOCIAL_SECURITY in keywords
        assert "medicare" in keywords[AgentType.HEALTHCARE]
        assert "social security" in keywords[AgentType.SOCIAL_SECURITY]


class TestPriorityStrategy:
    """Test priority execution strategy."""
    
    def test_priority_ordering(self):
        """Test that priorities are defined."""
        priorities = PriorityStrategy.PRIORITIES
        
        # Fiscal should have highest priority (lowest number)
        assert priorities[AgentType.FISCAL] == 1
        
        # Economic next
        assert priorities[AgentType.ECONOMIC] == 2
        
        # Healthcare and SS same priority
        assert priorities[AgentType.HEALTHCARE] == 3
        assert priorities[AgentType.SOCIAL_SECURITY] == 3


class TestExecutionResult:
    """Test execution result model."""
    
    def test_result_creation(self):
        """Test result model creation."""
        result = ExecutionResult(
            agent_id="test_agent",
            agent_type=AgentType.FISCAL,
            success=True,
            execution_time_seconds=1.5,
        )
        
        assert result.agent_id == "test_agent"
        assert result.success
        assert result.execution_time_seconds == 1.5
    
    def test_failed_result(self):
        """Test failed result."""
        result = ExecutionResult(
            agent_id="test_agent",
            agent_type=AgentType.FISCAL,
            success=False,
            error="Test error",
        )
        
        assert not result.success
        assert result.error == "Test error"


class TestExecutionStats:
    """Test execution statistics model."""
    
    def test_stats_creation(self):
        """Test stats model creation."""
        stats = ExecutionStats(
            total_agents=4,
            successful=3,
            failed=1,
        )
        
        assert stats.total_agents == 4
        assert stats.successful == 3
        assert stats.failed == 1
    
    def test_stats_with_results(self):
        """Test stats with result list."""
        results = [
            ExecutionResult(agent_id="a1", agent_type=AgentType.FISCAL, success=True),
            ExecutionResult(agent_id="a2", agent_type=AgentType.ECONOMIC, success=False),
        ]
        
        stats = ExecutionStats(
            total_agents=2,
            results=results,
        )
        
        assert len(stats.results) == 2


# =============================================================================
# Integration Tests (Mocked)
# =============================================================================

class TestLLMClientIntegration:
    """Integration tests for LLM client."""
    
    def test_global_client(self):
        """Test global client access."""
        client = get_llm_client()
        
        assert isinstance(client, LLMClient)
    
    def test_configure_client(self):
        """Test configuring global client."""
        config = LLMConfig(
            provider=LLMProvider.LOCAL,
            model="configured-model",
        )
        
        client = configure_llm_client(config)
        
        assert client.config.model == "configured-model"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
