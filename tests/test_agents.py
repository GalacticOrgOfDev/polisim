"""Tests for the Multi-Agent Swarm system.

These tests verify:
1. Agent creation and configuration
2. Agent analysis capabilities
3. Swarm coordination and pipeline
4. Consensus building
5. Debate mechanics
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from core.agents import (
    # Types
    AgentType,
    PipelineState,
    FindingCategory,
    ImpactMagnitude,
    ConsensusLevel,
    CritiqueSeverity,
    CritiqueType,
    # Models
    AgentConfig,
    AgentAnalysis,
    Finding,
    FiscalImpact,
    Evidence,
    Position,
    Critique,
    SwarmAnalysis,
    ConsensusReport,
    # Agents
    BaseAgent,
    FiscalAgent,
    EconomicAgent,
    HealthcareAgent,
    SocialSecurityAgent,
    JudgeAgent,
    SwarmCoordinator,
    # Factory
    create_agent,
    AgentFactory,
)
from core.agents.base_agent import AnalysisContext


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_bill_text():
    """Sample bill text for testing."""
    return """
    H.R. 1234 - The Test Policy Act of 2025
    
    SECTION 1. SHORT TITLE.
    This Act may be cited as the "Test Policy Act of 2025".
    
    SECTION 2. TAX PROVISIONS.
    (a) The corporate tax rate shall be increased from 21% to 28%.
    (b) The individual income tax brackets shall be adjusted as follows:
        - 10% bracket: $0 - $20,000
        - 22% bracket: $20,001 - $80,000
        - 32% bracket: $80,001 - $200,000
        - 37% bracket: $200,001 and above
    
    SECTION 3. HEALTHCARE PROVISIONS.
    (a) Medicare shall be expanded to cover individuals age 60 and above.
    (b) A public option shall be established on the ACA marketplace.
    
    SECTION 4. SOCIAL SECURITY.
    (a) The Social Security payroll tax cap shall be removed for incomes above $400,000.
    (b) Benefits shall increase by 5% for beneficiaries with income below the poverty line.
    
    SECTION 5. APPROPRIATIONS.
    (a) $50 billion is appropriated for infrastructure improvements.
    (b) $20 billion is appropriated for healthcare expansion.
    
    SECTION 6. EFFECTIVE DATE.
    This Act shall take effect on January 1, 2026.
    """


@pytest.fixture
def analysis_context(sample_bill_text):
    """Create an AnalysisContext for testing."""
    return AnalysisContext(
        bill_id="HR1234",
        bill_text=sample_bill_text,
        bill_sections={"section_1": "Short Title", "section_2": "Tax Provisions"},
        extracted_mechanisms={
            "tax_changes": [{"type": "corporate_rate", "value": 28}],
            "healthcare_changes": [{"type": "medicare_expansion", "age": 60}],
        },
        baseline_data={"baseline_revenue": 4500, "baseline_spending": 5000},
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for agent analysis."""
    return {
        "findings": [
            {
                "category": "revenue",
                "description": "Corporate tax increase expected to raise $200B over 10 years",
                "confidence": 0.85,
                "magnitude": "major",
            },
            {
                "category": "fiscal_impact",
                "description": "Individual tax bracket changes expected to raise $100B over 10 years",
                "confidence": 0.75,
                "magnitude": "major",
            },
        ],
        "overall_confidence": 0.8,
        "executive_summary": "This bill would significantly increase federal revenue through tax increases.",
        "key_takeaways": [
            "Corporate tax increase from 21% to 28%",
            "Net revenue increase of $300B over 10 years",
        ],
    }


# =============================================================================
# Type Tests
# =============================================================================

class TestTypes:
    """Test type definitions and enums."""
    
    def test_agent_types(self):
        """Verify all expected agent types exist."""
        assert AgentType.FISCAL.value == "fiscal"
        assert AgentType.ECONOMIC.value == "economic"
        assert AgentType.HEALTHCARE.value == "healthcare"
        assert AgentType.SOCIAL_SECURITY.value == "social_security"
        assert AgentType.JUDGE.value == "judge"
    
    def test_pipeline_states(self):
        """Verify pipeline state machine."""
        states = [
            PipelineState.INITIALIZED,
            PipelineState.INGESTING,
            PipelineState.ANALYZING,
            PipelineState.CROSS_REVIEWING,
            PipelineState.DEBATING,
            PipelineState.VOTING,
            PipelineState.SYNTHESIZING,
            PipelineState.COMPLETE,
            PipelineState.ERROR,
        ]
        assert len(states) == 9
    
    def test_finding_categories(self):
        """Verify finding categories cover key policy areas."""
        categories = [
            FindingCategory.REVENUE,
            FindingCategory.SPENDING,
            FindingCategory.DEFICIT,
            FindingCategory.COVERAGE,
            FindingCategory.TRUST_FUND,
            FindingCategory.GDP,
        ]
        assert all(isinstance(c, FindingCategory) for c in categories)
    
    def test_consensus_levels(self):
        """Verify consensus levels."""
        assert ConsensusLevel.STRONG_CONSENSUS.value == "strong_consensus"
        assert ConsensusLevel.CONSENSUS.value == "consensus"
        assert ConsensusLevel.MAJORITY.value == "majority"
        assert ConsensusLevel.DIVIDED.value == "divided"
        assert ConsensusLevel.NO_CONSENSUS.value == "no_consensus"


# =============================================================================
# Model Tests
# =============================================================================

class TestModels:
    """Test data models."""
    
    def test_agent_config_defaults(self):
        """Test AgentConfig has sensible defaults."""
        config = AgentConfig(agent_type=AgentType.FISCAL)
        
        assert config.model == "claude-sonnet-4-20250514"
        assert config.temperature == 0.3
        assert config.max_tokens == 4096
        assert config.confidence_threshold == 0.7
        assert config.timeout_seconds == 60.0
        assert config.retry_attempts == 3
    
    def test_finding_creation(self):
        """Test Finding dataclass."""
        finding = Finding(
            category=FindingCategory.REVENUE,
            description="Tax increase raises $100B",
            impact_magnitude=ImpactMagnitude.HIGH,
            confidence=0.85,
            time_horizon="10-year",
        )
        
        assert finding.category == FindingCategory.REVENUE
        assert finding.confidence == 0.85
        assert finding.finding_id  # Auto-generated
    
    def test_fiscal_impact_creation(self):
        """Test FiscalImpact dataclass."""
        impact = FiscalImpact(
            amount_billions=100.0,
            time_period="10-year",
            confidence_low=80.0,
            confidence_mid=100.0,
            confidence_high=120.0,
            is_revenue=True,
        )
        
        assert impact.amount_billions == 100.0
        assert impact.is_revenue is True
    
    def test_critique_creation(self):
        """Test Critique dataclass."""
        critique = Critique(
            critic_id="agent_fiscal",
            target_id="agent_economic",
            critique_type=CritiqueType.METHODOLOGY,
            severity=CritiqueSeverity.MODERATE,
            argument="GDP multiplier estimate appears too high",
        )
        
        assert critique.critic_id == "agent_fiscal"
        assert critique.severity == CritiqueSeverity.MODERATE
    
    def test_agent_analysis_creation(self):
        """Test AgentAnalysis dataclass."""
        analysis = AgentAnalysis(
            agent_id="fiscal_001",
            agent_type=AgentType.FISCAL,
            bill_id="HR1234",
            overall_confidence=0.8,
            executive_summary="Revenue-positive bill",
        )
        
        assert analysis.agent_id == "fiscal_001"
        assert analysis.findings == []  # Default empty list


# =============================================================================
# Agent Tests
# =============================================================================

class TestFiscalAgent:
    """Test FiscalAgent implementation."""
    
    def test_agent_creation(self):
        """Test FiscalAgent instantiation."""
        agent = FiscalAgent()
        
        assert agent.agent_type == AgentType.FISCAL
        assert "fiscal" in agent.agent_id.lower()
        assert agent.config.model == "claude-sonnet-4-20250514"
    
    def test_agent_with_custom_config(self):
        """Test FiscalAgent with custom config."""
        config = AgentConfig(
            agent_type=AgentType.FISCAL,
            temperature=0.5,
            max_tokens=8192,
        )
        agent = FiscalAgent(config=config)
        
        assert agent.config.temperature == 0.5
        assert agent.config.max_tokens == 8192
    
    def test_system_prompt_content(self):
        """Test that system prompt contains key instructions."""
        agent = FiscalAgent()
        prompt = agent._get_system_prompt()
        
        assert "revenue" in prompt.lower() or "fiscal" in prompt.lower()
        assert "analysis" in prompt.lower() or "analyze" in prompt.lower()
    
    def test_topic_relevance(self):
        """Test that agent correctly identifies relevant topics."""
        agent = FiscalAgent()
        
        # Should have specialty topics
        assert hasattr(agent, "SPECIALTY_TOPICS")
        assert "revenue" in agent.SPECIALTY_TOPICS or "tax" in agent.SPECIALTY_TOPICS


class TestEconomicAgent:
    """Test EconomicAgent implementation."""
    
    def test_agent_creation(self):
        """Test EconomicAgent instantiation."""
        agent = EconomicAgent()
        
        assert agent.agent_type == AgentType.ECONOMIC
        assert "economic" in agent.agent_id.lower()
    
    def test_system_prompt_content(self):
        """Test that system prompt covers economic topics."""
        agent = EconomicAgent()
        prompt = agent._get_system_prompt()
        
        assert any(term in prompt.lower() for term in ["gdp", "economic", "growth", "employment"])


class TestHealthcareAgent:
    """Test HealthcareAgent implementation."""
    
    def test_agent_creation(self):
        """Test HealthcareAgent instantiation."""
        agent = HealthcareAgent()
        
        assert agent.agent_type == AgentType.HEALTHCARE
        assert "healthcare" in agent.agent_id.lower()
    
    def test_system_prompt_content(self):
        """Test that system prompt covers healthcare topics."""
        agent = HealthcareAgent()
        prompt = agent._get_system_prompt()
        
        assert any(term in prompt.lower() for term in ["medicare", "medicaid", "healthcare", "coverage"])


class TestSocialSecurityAgent:
    """Test SocialSecurityAgent implementation."""
    
    def test_agent_creation(self):
        """Test SocialSecurityAgent instantiation."""
        agent = SocialSecurityAgent()
        
        assert agent.agent_type == AgentType.SOCIAL_SECURITY
        assert "social" in agent.agent_id.lower() or "ss" in agent.agent_id.lower()
    
    def test_system_prompt_content(self):
        """Test that system prompt covers SS topics."""
        agent = SocialSecurityAgent()
        prompt = agent._get_system_prompt()
        
        assert any(term in prompt.lower() for term in [
            "social security", "trust fund", "oasi", "benefits", "retirement"
        ])


class TestJudgeAgent:
    """Test JudgeAgent implementation."""
    
    def test_agent_creation(self):
        """Test JudgeAgent instantiation."""
        agent = JudgeAgent()
        
        assert agent.agent_type == AgentType.JUDGE
        assert "judge" in agent.agent_id.lower()
    
    def test_judge_has_arbitrate_method(self):
        """Test JudgeAgent has arbitrate capability."""
        agent = JudgeAgent()
        
        assert hasattr(agent, "arbitrate")
        assert callable(agent.arbitrate)


# =============================================================================
# Factory Tests
# =============================================================================

class TestAgentFactory:
    """Test agent factory functionality."""
    
    def test_create_agent_function(self):
        """Test create_agent convenience function."""
        agent = create_agent(AgentType.FISCAL)
        
        assert isinstance(agent, FiscalAgent)
        assert agent.agent_type == AgentType.FISCAL
    
    def test_create_all_tier1_agents(self):
        """Test creating all Tier 1 agents."""
        factory = AgentFactory()
        agents = factory.create_tier1_agents()
        
        # Should create 4 agents
        assert len(agents) == 4
        
        # Verify types
        agent_types = {a.agent_type for a in agents.values()}
        assert AgentType.FISCAL in agent_types
        assert AgentType.ECONOMIC in agent_types
        assert AgentType.HEALTHCARE in agent_types
        assert AgentType.SOCIAL_SECURITY in agent_types
    
    def test_factory_with_config(self):
        """Test factory with config file."""
        factory = AgentFactory()
        agent = factory.create_agent(AgentType.FISCAL)
        
        assert agent.agent_type == AgentType.FISCAL


# =============================================================================
# SwarmCoordinator Tests
# =============================================================================

class TestSwarmCoordinator:
    """Test SwarmCoordinator orchestration."""
    
    def test_coordinator_creation(self):
        """Test SwarmCoordinator instantiation."""
        coordinator = SwarmCoordinator()
        
        assert coordinator.state == PipelineState.INITIALIZED
        assert len(coordinator.agents) == 4  # Tier 1 agents
        assert coordinator.judge is not None
    
    def test_coordinator_with_custom_agents(self):
        """Test coordinator with custom agent set."""
        agents = {"fiscal": FiscalAgent()}
        coordinator = SwarmCoordinator(agents=agents)
        
        assert len(coordinator.agents) == 1
        assert "fiscal" in coordinator.agents
    
    def test_pipeline_state_transitions(self):
        """Verify expected pipeline state transitions."""
        coordinator = SwarmCoordinator()
        
        # Initial state
        assert coordinator.state == PipelineState.INITIALIZED
        
        # State should be settable
        coordinator.state = PipelineState.ANALYZING
        assert coordinator.state == PipelineState.ANALYZING
    
    @pytest.mark.asyncio
    async def test_parallel_analysis_timeout_handling(self, analysis_context):
        """Test that parallel analysis handles timeouts."""
        coordinator = SwarmCoordinator()
        
        # Mock agent to timeout
        mock_agent = MagicMock(spec=FiscalAgent)
        mock_agent.agent_id = "test_agent"
        mock_agent.agent_type = AgentType.FISCAL
        mock_agent.analyze = AsyncMock(side_effect=asyncio.TimeoutError())
        
        coordinator.agents = {"test": mock_agent}
        
        # Should not raise, but return empty results
        results = await coordinator._execute_parallel_analysis(analysis_context)
        assert len(results) == 0
    
    def test_convergence_calculation(self):
        """Test convergence score calculation."""
        coordinator = SwarmCoordinator()
        
        # Identical confidences = high convergence
        positions = [
            Position(agent_id="a", topic="test", stance="x", confidence=0.8),
            Position(agent_id="b", topic="test", stance="y", confidence=0.8),
        ]
        convergence = coordinator._calculate_convergence(positions)
        assert convergence >= 0.9
        
        # Divergent confidences = lower convergence
        positions = [
            Position(agent_id="a", topic="test", stance="x", confidence=0.9),
            Position(agent_id="b", topic="test", stance="y", confidence=0.3),
        ]
        convergence = coordinator._calculate_convergence(positions)
        assert convergence < 0.9
    
    def test_debate_topic_identification(self):
        """Test identification of debate topics."""
        coordinator = SwarmCoordinator()
        
        analyses = [
            AgentAnalysis(
                agent_id="fiscal",
                overall_confidence=0.9,
                executive_summary="Positive revenue impact",
            ),
            AgentAnalysis(
                agent_id="economic",
                overall_confidence=0.4,  # Large divergence
                executive_summary="Negative GDP impact",
            ),
        ]
        
        critiques = {
            "fiscal": [],
            "economic": [
                Critique(
                    critic_id="fiscal",
                    target_id="economic",
                    critique_type=CritiqueType.METHODOLOGY,
                    severity=CritiqueSeverity.MAJOR,
                    argument="GDP multiplier too high",
                )
            ],
        }
        
        topics = coordinator._identify_debate_topics(analyses, critiques)
        
        # Should identify at least one topic
        assert len(topics) >= 1


# =============================================================================
# Integration Tests (Mocked LLM)
# =============================================================================

class TestIntegration:
    """Integration tests with mocked LLM calls."""
    
    @pytest.mark.asyncio
    async def test_full_analysis_pipeline_mocked(self, analysis_context, mock_llm_response):
        """Test complete analysis pipeline with mocked LLM."""
        coordinator = SwarmCoordinator()
        
        # Mock all agent analyses to return consistent data
        mock_analysis = AgentAnalysis(
            agent_id="test",
            agent_type=AgentType.FISCAL,
            bill_id=analysis_context.bill_id,
            overall_confidence=0.8,
            executive_summary="Test summary",
            findings=[
                Finding(
                    category=FindingCategory.REVENUE,
                    description="Test finding",
                    confidence=0.8,
                )
            ],
        )
        
        # Mock the parallel analysis method
        coordinator._execute_parallel_analysis = AsyncMock(return_value=[mock_analysis])
        coordinator._execute_cross_review = AsyncMock(return_value={})
        
        # Run analysis
        result = await coordinator.analyze_bill(analysis_context)
        
        # Verify result structure
        assert isinstance(result, SwarmAnalysis)
        assert result.bill_id == "HR1234"
        assert result.metadata.total_execution_time_seconds > 0
    
    @pytest.mark.asyncio
    async def test_event_streaming(self, analysis_context):
        """Test that events are properly streamed."""
        coordinator = SwarmCoordinator()
        events_received = []
        
        async def event_callback(event):
            events_received.append(event)
        
        # Mock fast analysis
        coordinator._execute_parallel_analysis = AsyncMock(return_value=[])
        coordinator._execute_cross_review = AsyncMock(return_value={})
        coordinator._run_debate = AsyncMock(return_value=None)
        coordinator._build_consensus = AsyncMock(return_value=([], []))
        
        await coordinator.analyze_bill(analysis_context, event_callback=event_callback)
        
        # Should have received pipeline events
        event_types = [e.event_type.value for e in events_received]
        assert "pipeline_started" in event_types
        assert "analysis_complete" in event_types


# =============================================================================
# Consensus Building Tests
# =============================================================================

class TestConsensusBuilding:
    """Test consensus building logic."""
    
    def test_agreement_assessment_consensus(self):
        """Test agreement assessment when there's consensus."""
        coordinator = SwarmCoordinator()
        
        # Findings with similar confidence = consensus
        findings_list = [
            (
                Finding(
                    category=FindingCategory.REVENUE,
                    description="Revenue increase of $100B",
                    confidence=0.8,
                ),
                "agent_1",
                0.8,
            ),
            (
                Finding(
                    category=FindingCategory.REVENUE,
                    description="Revenue increase of $110B",
                    confidence=0.82,
                ),
                "agent_2",
                0.82,
            ),
        ]
        
        consensus, disagreement = coordinator._assess_agreement("revenue", findings_list)
        
        assert consensus is not None
        assert disagreement is None
        assert len(consensus.supporting_agents) == 2
    
    def test_agreement_assessment_disagreement(self):
        """Test agreement assessment when there's disagreement."""
        coordinator = SwarmCoordinator()
        
        # Findings with very different confidence = disagreement
        findings_list = [
            (
                Finding(
                    category=FindingCategory.REVENUE,
                    description="Revenue increase",
                    confidence=0.9,
                ),
                "agent_1",
                0.9,
            ),
            (
                Finding(
                    category=FindingCategory.REVENUE,
                    description="Revenue decrease",
                    confidence=0.3,
                ),
                "agent_2",
                0.3,
            ),
        ]
        
        consensus, disagreement = coordinator._assess_agreement("revenue", findings_list)
        
        assert disagreement is not None
        assert disagreement.severity in ["moderate", "major"]


# =============================================================================
# Report Generation Tests
# =============================================================================

class TestReportGeneration:
    """Test consensus report generation."""
    
    def test_recommendation_generation(self):
        """Test primary recommendation generation."""
        from core.agents.models import ConsensusFinding
        
        coordinator = SwarmCoordinator()
        
        # High confidence findings
        findings = [
            ConsensusFinding(description="Finding 1", weighted_confidence=0.85),
            ConsensusFinding(description="Finding 2", weighted_confidence=0.75),
            ConsensusFinding(description="Finding 3", weighted_confidence=0.80),
        ]
        
        rec = coordinator._generate_primary_recommendation(findings, [])
        
        assert "Strong analytical support" in rec or "findings" in rec.lower()
    
    def test_caveat_generation(self):
        """Test caveat generation from disagreements."""
        coordinator = SwarmCoordinator()
        
        from core.agents.models import Disagreement
        
        disagreements = [
            Disagreement(
                topic="GDP impact",
                severity="major",
                reason="Test reason",
            ),
        ]
        
        caveats = coordinator._generate_caveats(disagreements)
        
        assert len(caveats) >= 1
        assert "major" in caveats[0].lower() or "disagree" in caveats[0].lower()
    
    def test_research_needs_generation(self):
        """Test further research needs generation."""
        from core.agents.models import ConsensusFinding, Disagreement
        
        coordinator = SwarmCoordinator()
        
        disagreements = [
            Disagreement(
                topic="Revenue estimate",
                reason="Conflicting data sources",
            ),
        ]
        
        low_conf_findings = [
            ConsensusFinding(description="Uncertain", weighted_confidence=0.5),
        ]
        
        needs = coordinator._generate_research_needs(disagreements, low_conf_findings)
        
        assert len(needs) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
