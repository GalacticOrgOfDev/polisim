"""Tests for the Consensus Engine (Phase 7.1.4).

This module provides comprehensive tests for:
- ConsensusEngine core functionality
- Weighted voting system
- Agent weight calculation
- Consensus level detection
- Dissent tracking
- Report generation
"""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Optional, Any
from unittest.mock import AsyncMock, MagicMock, patch

from core.agents.consensus_engine import (
    ConsensusEngine,
    ConsensusConfig,
    AgentWeight,
    AgentHistoricalPerformance,
    VotingRound,
    DissentRecord,
    SPECIALTY_MAP,
    calculate_weighted_mean,
    calculate_weighted_confidence_band,
    get_specialty_match_score,
)
from core.agents.models import (
    AgentAnalysis,
    Finding,
    FiscalImpact,
    Assumption,
    Evidence,
    Vote,
    Proposal,
    ConsensusFinding,
    Disagreement,
    MinorityView,
    Uncertainty,
    ConsensusResult,
    ConsensusReport,
    ConfidenceBand,
)
from core.agents.types import (
    AgentType,
    FindingCategory,
    ImpactMagnitude,
    VoteType,
    ConsensusLevel,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def consensus_config():
    """Create a test consensus configuration."""
    return ConsensusConfig(
        strong_consensus_threshold=0.90,
        consensus_threshold=0.75,
        majority_threshold=0.60,
        divided_threshold=0.40,
        minimum_votes_required=2,
        specialty_weight_multiplier=1.5,
    )


@pytest.fixture
def consensus_engine(consensus_config):
    """Create a test consensus engine."""
    return ConsensusEngine(config=consensus_config)


@pytest.fixture
def sample_analyses():
    """Create sample agent analyses for testing."""
    analyses = []
    
    # Fiscal agent analysis - high confidence
    fiscal = AgentAnalysis(
        agent_id="fiscal_001",
        agent_type=AgentType.FISCAL,
        bill_id="test_bill_001",
        overall_confidence=0.85,
        executive_summary="The bill will increase deficit spending by $500B over 10 years.",
        key_takeaways=[
            "Estimated $500B in new spending",
            "Limited revenue offsets",
            "Deficit increase of $400B"
        ],
        uncertainty_areas=["Long-term behavioral responses", "Economic growth assumptions"],
        findings=[
            Finding(
                finding_id="f1",
                category=FindingCategory.SPENDING,
                description="New mandatory spending of $50B annually",
                impact_magnitude=ImpactMagnitude.HIGH,
                confidence=0.9,
                time_horizon="10-year",
                fiscal_impact=FiscalImpact(
                    amount_billions=500.0,
                    time_period="10-year",
                    confidence_low=450.0,
                    confidence_mid=500.0,
                    confidence_high=550.0,
                    is_revenue=False,
                ),
            ),
            Finding(
                finding_id="f2",
                category=FindingCategory.DEFICIT,
                description="Deficit increase of approximately $40B annually",
                impact_magnitude=ImpactMagnitude.HIGH,
                confidence=0.85,
                time_horizon="10-year",
            ),
        ],
    )
    analyses.append(fiscal)
    
    # Healthcare agent analysis
    healthcare = AgentAnalysis(
        agent_id="healthcare_001",
        agent_type=AgentType.HEALTHCARE,
        bill_id="test_bill_001",
        overall_confidence=0.80,
        executive_summary="Healthcare provisions will expand coverage to 5M uninsured.",
        key_takeaways=[
            "5M additional insured",
            "Cost savings from preventive care",
            "Quality improvements expected"
        ],
        uncertainty_areas=["Enrollment rates", "Provider capacity"],
        findings=[
            Finding(
                finding_id="f3",
                category=FindingCategory.COVERAGE,
                description="Coverage expansion to 5 million currently uninsured",
                impact_magnitude=ImpactMagnitude.HIGH,
                confidence=0.85,
                time_horizon="5-year",
            ),
            Finding(
                finding_id="f4",
                category=FindingCategory.SPENDING,
                description="Healthcare spending increase of $45B annually",
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.75,
                time_horizon="10-year",
                fiscal_impact=FiscalImpact(
                    amount_billions=450.0,
                    time_period="10-year",
                    confidence_low=400.0,
                    confidence_mid=450.0,
                    confidence_high=520.0,
                    is_revenue=False,
                ),
            ),
        ],
    )
    analyses.append(healthcare)
    
    # Economic agent analysis
    economic = AgentAnalysis(
        agent_id="economic_001",
        agent_type=AgentType.ECONOMIC,
        bill_id="test_bill_001",
        overall_confidence=0.70,
        executive_summary="GDP impact expected to be slightly positive due to healthcare investment.",
        key_takeaways=[
            "0.1-0.3% GDP boost",
            "Job creation in healthcare sector",
            "Long-term productivity gains"
        ],
        uncertainty_areas=["Multiplier effects", "Labor market response"],
        findings=[
            Finding(
                finding_id="f5",
                category=FindingCategory.GDP,
                description="Modest GDP increase of 0.1-0.3% from healthcare investment",
                impact_magnitude=ImpactMagnitude.LOW,
                confidence=0.65,
                time_horizon="10-year",
            ),
            Finding(
                finding_id="f6",
                category=FindingCategory.EMPLOYMENT,
                description="Creation of approximately 200,000 healthcare jobs",
                impact_magnitude=ImpactMagnitude.MEDIUM,
                confidence=0.70,
                time_horizon="5-year",
            ),
        ],
    )
    analyses.append(economic)
    
    return analyses


@pytest.fixture
def sample_votes():
    """Create sample votes for testing."""
    return [
        Vote(
            voter_id="fiscal_001",
            proposal_id="prop_001",
            support=VoteType.SUPPORT,
            confidence=0.85,
            reasoning="Fiscal analysis supports this finding",
        ),
        Vote(
            voter_id="healthcare_001",
            proposal_id="prop_001",
            support=VoteType.STRONGLY_SUPPORT,
            confidence=0.90,
            reasoning="Healthcare analysis strongly supports this finding",
        ),
        Vote(
            voter_id="economic_001",
            proposal_id="prop_001",
            support=VoteType.SUPPORT,
            confidence=0.70,
            reasoning="Economic analysis supports with reservations",
        ),
    ]


@pytest.fixture
def sample_proposals():
    """Create sample proposals for testing."""
    return [
        Proposal(
            proposal_id="prop_001",
            proposer_id="fiscal_001",
            topic="spending",
            description="New mandatory spending of $50B annually",
            confidence=0.85,
        ),
        Proposal(
            proposal_id="prop_002",
            proposer_id="healthcare_001",
            topic="coverage",
            description="Coverage expansion to 5 million uninsured",
            confidence=0.85,
        ),
    ]


# =============================================================================
# ConsensusConfig Tests
# =============================================================================

class TestConsensusConfig:
    """Test ConsensusConfig dataclass."""
    
    def test_default_values(self):
        """Test default configuration values."""
        config = ConsensusConfig()
        
        assert config.strong_consensus_threshold == 0.90
        assert config.consensus_threshold == 0.75
        assert config.majority_threshold == 0.60
        assert config.divided_threshold == 0.40
        assert config.minimum_votes_required == 2
        assert config.specialty_weight_multiplier == 1.5
        assert config.include_minority_views is True
    
    def test_custom_values(self):
        """Test custom configuration."""
        config = ConsensusConfig(
            strong_consensus_threshold=0.95,
            minimum_votes_required=3,
            specialty_weight_multiplier=2.0,
        )
        
        assert config.strong_consensus_threshold == 0.95
        assert config.minimum_votes_required == 3
        assert config.specialty_weight_multiplier == 2.0


# =============================================================================
# Agent Weight Calculation Tests
# =============================================================================

class TestAgentWeightCalculation:
    """Test agent weight calculation."""
    
    def test_base_weight_is_one(self, consensus_engine):
        """Test that base weight starts at 1.0."""
        weight = consensus_engine._calculate_agent_weight(
            agent_id="test_agent",
            agent_type=AgentType.FISCAL,
            topic="other",  # Non-matching topic
            analysis_confidence=0.8,
        )
        
        assert weight.base_weight == 1.0
    
    def test_specialty_bonus_for_matching_topic(self, consensus_engine):
        """Test specialty bonus when agent matches topic."""
        # Fiscal agent on spending topic
        weight = consensus_engine._calculate_agent_weight(
            agent_id="fiscal_001",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.8,
        )
        
        assert weight.specialty_bonus > 0
        assert weight.final_weight > 1.0
    
    def test_no_specialty_bonus_for_non_matching_topic(self, consensus_engine):
        """Test no specialty bonus when agent doesn't match topic."""
        # Fiscal agent on coverage topic (healthcare specialty)
        weight = consensus_engine._calculate_agent_weight(
            agent_id="fiscal_001",
            agent_type=AgentType.FISCAL,
            topic="coverage",
            analysis_confidence=0.8,
        )
        
        assert weight.specialty_bonus == 0
    
    def test_confidence_affects_weight(self, consensus_engine):
        """Test that confidence level affects final weight."""
        high_conf = consensus_engine._calculate_agent_weight(
            agent_id="test",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.95,
        )
        
        low_conf = consensus_engine._calculate_agent_weight(
            agent_id="test",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.5,
        )
        
        assert high_conf.final_weight > low_conf.final_weight
    
    def test_historical_accuracy_affects_weight(self):
        """Test that historical accuracy affects weight."""
        # Engine with historical performance data
        history = {
            "accurate_agent": AgentHistoricalPerformance(
                agent_id="accurate_agent",
                total_analyses=100,
                accurate_predictions=90,
                accuracy_rate=0.9,
            ),
            "inaccurate_agent": AgentHistoricalPerformance(
                agent_id="inaccurate_agent",
                total_analyses=100,
                accurate_predictions=40,
                accuracy_rate=0.4,
            ),
        }
        
        engine = ConsensusEngine(historical_performance=history)
        
        accurate_weight = engine._calculate_agent_weight(
            agent_id="accurate_agent",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.8,
        )
        
        inaccurate_weight = engine._calculate_agent_weight(
            agent_id="inaccurate_agent",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.8,
        )
        
        assert accurate_weight.final_weight > inaccurate_weight.final_weight
    
    def test_weight_calculation_breakdown(self, consensus_engine):
        """Test that weight calculation breakdown is recorded."""
        weight = consensus_engine._calculate_agent_weight(
            agent_id="test",
            agent_type=AgentType.FISCAL,
            topic="spending",
            analysis_confidence=0.8,
        )
        
        assert "base" in weight.calculation_breakdown
        assert "confidence" in weight.calculation_breakdown
        assert "historical_accuracy" in weight.calculation_breakdown


# =============================================================================
# Vote Generation Tests
# =============================================================================

class TestVoteGeneration:
    """Test vote generation from analyses."""
    
    def test_generate_vote_for_matching_finding(self, consensus_engine, sample_analyses, sample_proposals):
        """Test vote generation when agent has matching finding."""
        fiscal_analysis = sample_analyses[0]
        spending_proposal = sample_proposals[0]
        
        vote = consensus_engine._generate_vote(fiscal_analysis, spending_proposal)
        
        assert vote.voter_id == "fiscal_001"
        assert vote.proposal_id == "prop_001"
        assert vote.support in [VoteType.SUPPORT, VoteType.STRONGLY_SUPPORT]
    
    def test_generate_votes_from_all_analyses(self, consensus_engine, sample_analyses, sample_proposals):
        """Test generating votes from all analyses."""
        votes = consensus_engine._generate_votes_from_analyses(
            sample_analyses, sample_proposals
        )
        
        # Should have votes from each agent for each proposal
        expected_vote_count = len(sample_analyses) * len(sample_proposals)
        assert len(votes) == expected_vote_count
    
    def test_vote_confidence_matches_finding(self, consensus_engine, sample_analyses, sample_proposals):
        """Test that vote confidence relates to finding confidence."""
        fiscal_analysis = sample_analyses[0]
        spending_proposal = sample_proposals[0]
        
        vote = consensus_engine._generate_vote(fiscal_analysis, spending_proposal)
        
        # Vote confidence should be reasonable (0.5-1.0)
        assert 0.5 <= vote.confidence <= 1.0


# =============================================================================
# Consensus Result Calculation Tests
# =============================================================================

class TestConsensusResultCalculation:
    """Test consensus result calculation."""
    
    def test_strong_consensus_with_unanimous_support(self, consensus_engine):
        """Test strong consensus when all agents strongly support."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
            Vote(voter_id="a3", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
        ]
        weights = {
            "a1": AgentWeight(agent_id="a1", final_weight=1.0),
            "a2": AgentWeight(agent_id="a2", final_weight=1.0),
            "a3": AgentWeight(agent_id="a3", final_weight=1.0),
        }
        
        result = consensus_engine._calculate_consensus_result(proposal, votes, weights)
        
        assert result.consensus_level == ConsensusLevel.STRONG_CONSENSUS
        assert result.passed is True
    
    def test_divided_with_mixed_votes(self, consensus_engine):
        """Test divided result with mixed support/oppose votes."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.STRONGLY_OPPOSE, confidence=0.9),
            Vote(voter_id="a3", proposal_id="p1", support=VoteType.NEUTRAL, confidence=0.5),
        ]
        weights = {
            "a1": AgentWeight(agent_id="a1", final_weight=1.0),
            "a2": AgentWeight(agent_id="a2", final_weight=1.0),
            "a3": AgentWeight(agent_id="a3", final_weight=1.0),
        }
        
        result = consensus_engine._calculate_consensus_result(proposal, votes, weights)
        
        # With one strong support, one strong oppose, and one neutral,
        # the result should be divided
        assert result.consensus_level in [ConsensusLevel.DIVIDED, ConsensusLevel.MAJORITY]
    
    def test_abstentions_are_excluded(self, consensus_engine):
        """Test that abstentions don't affect the result."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.SUPPORT, confidence=0.8),
            Vote(voter_id="a3", proposal_id="p1", support=VoteType.ABSTAIN, confidence=0.5),
        ]
        weights = {
            "a1": AgentWeight(agent_id="a1", final_weight=1.0),
            "a2": AgentWeight(agent_id="a2", final_weight=1.0),
            "a3": AgentWeight(agent_id="a3", final_weight=1.0),
        }
        
        result = consensus_engine._calculate_consensus_result(proposal, votes, weights)
        
        # Should still have high consensus from the two supporting votes
        assert result.consensus_level in [ConsensusLevel.STRONG_CONSENSUS, ConsensusLevel.CONSENSUS]
        assert result.passed is True
    
    def test_insufficient_votes_returns_no_consensus(self, consensus_engine):
        """Test that insufficient votes returns no consensus."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.SUPPORT, confidence=0.9),
        ]
        weights = {"a1": AgentWeight(agent_id="a1", final_weight=1.0)}
        
        # Minimum votes required is 2
        result = consensus_engine._calculate_consensus_result(proposal, votes, weights)
        
        assert result.consensus_level == ConsensusLevel.NO_CONSENSUS
        assert result.passed is False
    
    def test_weight_affects_consensus(self, consensus_engine):
        """Test that higher-weighted agents have more influence."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.STRONGLY_SUPPORT, confidence=0.9),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.OPPOSE, confidence=0.9),
        ]
        
        # When weights are equal, result is divided
        equal_weights = {
            "a1": AgentWeight(agent_id="a1", final_weight=1.0),
            "a2": AgentWeight(agent_id="a2", final_weight=1.0),
        }
        result_equal = consensus_engine._calculate_consensus_result(proposal, votes, equal_weights)
        
        # When a1 has much higher weight, result tilts toward support
        unequal_weights = {
            "a1": AgentWeight(agent_id="a1", final_weight=3.0),
            "a2": AgentWeight(agent_id="a2", final_weight=1.0),
        }
        result_unequal = consensus_engine._calculate_consensus_result(proposal, votes, unequal_weights)
        
        # Unequal should have higher support score
        assert result_unequal.weighted_support > result_equal.weighted_support


# =============================================================================
# Consensus Level Detection Tests
# =============================================================================

class TestConsensusLevelDetection:
    """Test consensus level detection from support scores."""
    
    def test_strong_consensus_threshold(self, consensus_engine):
        """Test strong consensus at 0.90+."""
        level = consensus_engine._determine_consensus_level(0.95)
        assert level == ConsensusLevel.STRONG_CONSENSUS
    
    def test_consensus_threshold(self, consensus_engine):
        """Test consensus at 0.75-0.89."""
        level = consensus_engine._determine_consensus_level(0.80)
        assert level == ConsensusLevel.CONSENSUS
    
    def test_majority_threshold(self, consensus_engine):
        """Test majority at 0.60-0.74."""
        level = consensus_engine._determine_consensus_level(0.65)
        assert level == ConsensusLevel.MAJORITY
    
    def test_divided_threshold(self, consensus_engine):
        """Test divided at 0.40-0.59."""
        level = consensus_engine._determine_consensus_level(0.50)
        assert level == ConsensusLevel.DIVIDED
    
    def test_minority_threshold(self, consensus_engine):
        """Test minority below 0.40."""
        level = consensus_engine._determine_consensus_level(0.30)
        assert level == ConsensusLevel.MINORITY


# =============================================================================
# Proposal Creation Tests
# =============================================================================

class TestProposalCreation:
    """Test proposal creation from findings."""
    
    def test_create_proposals_from_findings(self, consensus_engine, sample_analyses):
        """Test creating proposals from agent findings."""
        proposals = consensus_engine._create_proposals_from_findings(sample_analyses)
        
        # Should have proposals for various categories
        assert len(proposals) > 0
        
        # Each proposal should have required fields
        for prop in proposals:
            assert prop.proposal_id
            assert prop.topic
            assert prop.description
    
    def test_deduplicates_similar_findings(self, consensus_engine):
        """Test that similar findings are deduplicated."""
        analyses = [
            AgentAnalysis(
                agent_id="a1",
                agent_type=AgentType.FISCAL,
                findings=[
                    Finding(
                        category=FindingCategory.SPENDING,
                        description="New spending of $50 billion",
                        confidence=0.9,
                    ),
                ],
            ),
            AgentAnalysis(
                agent_id="a2",
                agent_type=AgentType.ECONOMIC,
                findings=[
                    Finding(
                        category=FindingCategory.SPENDING,
                        description="New spending of $50 billion expected",
                        confidence=0.85,
                    ),
                ],
            ),
        ]
        
        proposals = consensus_engine._create_proposals_from_findings(analyses)
        
        # Similar descriptions should be consolidated
        spending_proposals = [p for p in proposals if p.topic == "spending"]
        # Should be fewer proposals than total findings due to deduplication
        assert len(spending_proposals) <= 2


# =============================================================================
# Dissent Tracking Tests
# =============================================================================

class TestDissentTracking:
    """Test dissent tracking and minority view capture."""
    
    def test_extract_minority_view(self, consensus_engine):
        """Test extracting minority view from voting."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test spending")
        result = ConsensusResult(
            proposal_id="p1",
            consensus_level=ConsensusLevel.MAJORITY,
            weighted_support=0.65,
        )
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.SUPPORT, reasoning="Agree"),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.SUPPORT, reasoning="Agree"),
            Vote(voter_id="a3", proposal_id="p1", support=VoteType.OPPOSE, reasoning="Disagree on methodology"),
        ]
        
        minority = consensus_engine._extract_minority_view(proposal, result, votes)
        
        assert minority is not None
        assert "a3" in minority.agents
        assert "methodology" in minority.reasoning.lower()
    
    def test_no_minority_when_unanimous(self, consensus_engine):
        """Test no minority view when consensus is unanimous."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        result = ConsensusResult(
            proposal_id="p1",
            consensus_level=ConsensusLevel.STRONG_CONSENSUS,
        )
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.SUPPORT, reasoning="Agree"),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.SUPPORT, reasoning="Agree"),
        ]
        
        minority = consensus_engine._extract_minority_view(proposal, result, votes)
        
        assert minority is None
    
    def test_dissent_reasons_captured(self, consensus_engine):
        """Test that dissent reasons are captured in ConsensusFinding."""
        proposal = Proposal(proposal_id="p1", topic="spending", description="Test")
        result = ConsensusResult(
            proposal_id="p1",
            consensus_level=ConsensusLevel.MAJORITY,
            weighted_support=0.65,
        )
        votes = [
            Vote(voter_id="a1", proposal_id="p1", support=VoteType.SUPPORT, reasoning="Agree"),
            Vote(voter_id="a2", proposal_id="p1", support=VoteType.OPPOSE, reasoning="Methodology concerns"),
        ]
        
        finding = consensus_engine._result_to_consensus_finding(proposal, result, votes)
        
        assert "a2" in finding.dissenting_agents
        assert "a2" in finding.dissent_reasons


# =============================================================================
# Report Generation Tests
# =============================================================================

class TestReportGeneration:
    """Test consensus report generation."""
    
    @pytest.mark.asyncio
    async def test_build_consensus_returns_report(self, consensus_engine, sample_analyses):
        """Test that build_consensus returns a complete report."""
        report = await consensus_engine.build_consensus(sample_analyses)
        
        assert isinstance(report, ConsensusReport)
        assert report.bill_id == "test_bill_001"
        assert report.participating_agents
    
    @pytest.mark.asyncio
    async def test_report_includes_agreed_findings(self, consensus_engine, sample_analyses):
        """Test that report includes consensus findings."""
        report = await consensus_engine.build_consensus(sample_analyses)
        
        # Should have some agreed findings
        assert len(report.agreed_findings) > 0 or len(report.unresolved_disputes) > 0
    
    @pytest.mark.asyncio
    async def test_report_includes_caveats(self, consensus_engine, sample_analyses):
        """Test that report includes appropriate caveats."""
        report = await consensus_engine.build_consensus(sample_analyses)
        
        assert isinstance(report.caveats, list)
    
    @pytest.mark.asyncio
    async def test_report_includes_recommendation(self, consensus_engine, sample_analyses):
        """Test that report includes a primary recommendation."""
        report = await consensus_engine.build_consensus(sample_analyses)
        
        assert report.primary_recommendation
        assert len(report.primary_recommendation) > 0
    
    def test_generate_bill_summary(self, consensus_engine, sample_analyses):
        """Test bill summary generation."""
        summary = consensus_engine._generate_bill_summary(sample_analyses)
        
        assert summary
        assert len(summary) > 0
    
    def test_generate_caveats_with_disagreements(self, consensus_engine):
        """Test caveat generation when there are disagreements."""
        disagreements = [
            Disagreement(topic="spending", agents_involved=["a1", "a2"]),
            Disagreement(topic="coverage", agents_involved=["a1", "a3"]),
        ]
        
        caveats = consensus_engine._generate_caveats(
            disagreements=disagreements,
            minority_views=[],
            uncertainties=[],
        )
        
        assert len(caveats) > 0
        assert "disagreement" in caveats[0].lower()
    
    def test_identify_research_needs(self, consensus_engine):
        """Test research needs identification."""
        disagreements = [
            Disagreement(topic="spending"),
            Disagreement(topic="coverage"),
        ]
        uncertainties = [
            Uncertainty(
                description="Economic growth rates",
                data_needed_to_resolve=["Historical growth data", "Model validation"],
            ),
        ]
        
        needs = consensus_engine._identify_research_needs(disagreements, uncertainties)
        
        assert len(needs) > 0


# =============================================================================
# Uncertainty Extraction Tests
# =============================================================================

class TestUncertaintyExtraction:
    """Test uncertainty extraction from analyses."""
    
    def test_extract_uncertainties_from_analyses(self, consensus_engine, sample_analyses):
        """Test extracting uncertainties from analyses."""
        uncertainties = consensus_engine._extract_uncertainties(sample_analyses)
        
        assert len(uncertainties) > 0
        
        # Should deduplicate across analyses
        descriptions = [u.description.lower() for u in uncertainties]
        assert len(descriptions) == len(set(descriptions))
    
    def test_uncertainty_limit(self, consensus_engine, sample_analyses):
        """Test that uncertainties are limited to configured max."""
        # Modify config to have low limit
        consensus_engine.config.max_uncertainties_in_report = 2
        
        uncertainties = consensus_engine._extract_uncertainties(sample_analyses)
        
        assert len(uncertainties) <= 2


# =============================================================================
# Utility Function Tests
# =============================================================================

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_calculate_weighted_mean(self):
        """Test weighted mean calculation."""
        values = [10, 20, 30]
        weights = [1, 2, 3]
        
        result = calculate_weighted_mean(values, weights)
        
        # (10*1 + 20*2 + 30*3) / (1+2+3) = 140/6 = 23.33
        assert abs(result - 23.33) < 0.1
    
    def test_calculate_weighted_mean_empty(self):
        """Test weighted mean with empty inputs."""
        result = calculate_weighted_mean([], [])
        assert result == 0.0
    
    def test_calculate_weighted_mean_zero_weights(self):
        """Test weighted mean with zero weights falls back to unweighted."""
        values = [10, 20, 30]
        weights = [0, 0, 0]
        
        result = calculate_weighted_mean(values, weights)
        
        # Should fall back to simple mean
        assert result == 20.0
    
    def test_specialty_match_score_primary(self):
        """Test specialty match for primary specialist."""
        score = get_specialty_match_score(AgentType.FISCAL, FindingCategory.SPENDING)
        assert score == 1.0
    
    def test_specialty_match_score_secondary(self):
        """Test specialty match for secondary specialist."""
        # TRUST_FUND has both FISCAL (primary) and SOCIAL_SECURITY (secondary)
        score = get_specialty_match_score(AgentType.SOCIAL_SECURITY, FindingCategory.TRUST_FUND)
        assert score == 0.8
    
    def test_specialty_match_score_non_specialist(self):
        """Test specialty match for non-specialist."""
        score = get_specialty_match_score(AgentType.ECONOMIC, FindingCategory.COVERAGE)
        assert score == 0.5
    
    def test_calculate_weighted_confidence_band(self):
        """Test confidence band calculation."""
        estimates = [100, 150, 200, 180, 120]
        confidences = [0.9, 0.8, 0.7, 0.85, 0.75]
        weights = [1.0, 1.0, 1.0, 1.0, 1.0]
        
        band = calculate_weighted_confidence_band(estimates, confidences, weights)
        
        assert band.p10 <= band.p50 <= band.p90
    
    def test_calculate_weighted_confidence_band_empty(self):
        """Test confidence band with empty inputs."""
        band = calculate_weighted_confidence_band([], [], [])
        
        assert band.p10 == 0.0
        assert band.p50 == 0.0
        assert band.p90 == 0.0


# =============================================================================
# Specialty Map Tests
# =============================================================================

class TestSpecialtyMap:
    """Test specialty mapping."""
    
    def test_fiscal_categories_map_to_fiscal_agent(self):
        """Test that fiscal categories map to fiscal agent."""
        fiscal_categories = [
            FindingCategory.REVENUE,
            FindingCategory.SPENDING,
            FindingCategory.DEBT,
            FindingCategory.DEFICIT,
        ]
        
        for category in fiscal_categories:
            specialists = SPECIALTY_MAP.get(category, [])
            assert AgentType.FISCAL in specialists
    
    def test_healthcare_categories_map_to_healthcare_agent(self):
        """Test that healthcare categories map to healthcare agent."""
        healthcare_categories = [
            FindingCategory.COVERAGE,
            FindingCategory.QUALITY,
            FindingCategory.ACCESS,
        ]
        
        for category in healthcare_categories:
            specialists = SPECIALTY_MAP.get(category, [])
            assert AgentType.HEALTHCARE in specialists
    
    def test_economic_categories_map_to_economic_agent(self):
        """Test that economic categories map to economic agent."""
        economic_categories = [
            FindingCategory.GDP,
            FindingCategory.EMPLOYMENT,
            FindingCategory.INFLATION,
            FindingCategory.PRODUCTIVITY,
        ]
        
        for category in economic_categories:
            specialists = SPECIALTY_MAP.get(category, [])
            assert AgentType.ECONOMIC in specialists


# =============================================================================
# Integration Tests
# =============================================================================

class TestConsensusEngineIntegration:
    """Integration tests for the consensus engine."""
    
    @pytest.mark.asyncio
    async def test_full_consensus_pipeline(self, consensus_engine, sample_analyses):
        """Test full consensus building pipeline."""
        # Run complete consensus building
        report = await consensus_engine.build_consensus(sample_analyses)
        
        # Verify report structure
        assert isinstance(report, ConsensusReport)
        assert report.analysis_id
        assert report.bill_id
        
        # Verify we have either findings or disagreements
        total_results = len(report.agreed_findings) + len(report.unresolved_disputes)
        assert total_results > 0
        
        # Verify participating agents tracked
        assert len(report.participating_agents) == len(sample_analyses)
    
    @pytest.mark.asyncio
    async def test_event_callback_called(self, consensus_engine, sample_analyses):
        """Test that event callback is called during consensus."""
        events = []
        
        async def capture_event(event):
            events.append(event)
        
        await consensus_engine.build_consensus(
            sample_analyses,
            event_callback=capture_event,
        )
        
        # Should have at least stage change and consensus reached events
        assert len(events) >= 2
    
    @pytest.mark.asyncio
    async def test_handles_single_analysis(self, consensus_engine):
        """Test handling of single agent analysis."""
        single_analysis = [
            AgentAnalysis(
                agent_id="fiscal_001",
                agent_type=AgentType.FISCAL,
                overall_confidence=0.85,
                findings=[
                    Finding(
                        category=FindingCategory.SPENDING,
                        description="Test finding",
                        confidence=0.9,
                    ),
                ],
            ),
        ]
        
        # Should not crash with single analysis
        report = await consensus_engine.build_consensus(single_analysis)
        
        assert report is not None
    
    @pytest.mark.asyncio
    async def test_handles_empty_findings(self, consensus_engine):
        """Test handling of analyses with no findings."""
        empty_analyses = [
            AgentAnalysis(
                agent_id="a1",
                agent_type=AgentType.FISCAL,
                findings=[],
            ),
            AgentAnalysis(
                agent_id="a2",
                agent_type=AgentType.ECONOMIC,
                findings=[],
            ),
        ]
        
        # Should not crash with empty findings
        report = await consensus_engine.build_consensus(empty_analyses)
        
        assert report is not None
        assert len(report.agreed_findings) == 0


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_description_similarity_with_empty_strings(self, consensus_engine):
        """Test description similarity with empty strings."""
        result = consensus_engine._descriptions_similar("", "")
        assert result is False
    
    def test_description_similarity_with_stop_words_only(self, consensus_engine):
        """Test description similarity with only stop words."""
        result = consensus_engine._descriptions_similar("the and is", "a an the")
        assert result is False
    
    def test_description_similarity_with_matching_content(self, consensus_engine):
        """Test description similarity with matching content."""
        desc1 = "New mandatory spending of $50 billion annually"
        desc2 = "Mandatory spending increase of $50 billion per year"
        
        result = consensus_engine._descriptions_similar(desc1, desc2)
        # Should recognize these as similar
        assert result is True
    
    def test_weight_calculation_with_unknown_category(self, consensus_engine):
        """Test weight calculation with unknown category."""
        weight = consensus_engine._calculate_agent_weight(
            agent_id="test",
            agent_type=AgentType.FISCAL,
            topic="unknown_category_xyz",
            analysis_confidence=0.8,
        )
        
        # Should still work, just no specialty bonus
        assert weight.specialty_bonus == 0
        assert weight.final_weight > 0


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_consensus_completes_in_reasonable_time(self, consensus_engine, sample_analyses):
        """Test that consensus building completes quickly."""
        import time
        
        start = time.time()
        await consensus_engine.build_consensus(sample_analyses)
        elapsed = time.time() - start
        
        # Should complete in under 1 second for 3 agents
        assert elapsed < 1.0
    
    def test_weight_calculation_performance(self, consensus_engine):
        """Test that weight calculation is fast."""
        import time
        
        start = time.time()
        for _ in range(100):
            consensus_engine._calculate_agent_weight(
                agent_id="test",
                agent_type=AgentType.FISCAL,
                topic="spending",
                analysis_confidence=0.8,
            )
        elapsed = time.time() - start
        
        # 100 calculations should complete in under 0.1 seconds
        assert elapsed < 0.1
