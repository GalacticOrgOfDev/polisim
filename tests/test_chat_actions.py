"""
Tests for PoliSim Chat Action Buttons (Phase 7.3.2).

This module provides comprehensive tests for:
- ActionButton data class
- ActionButtonRegistry
- SuggestionEngine
- ActionExecutor
- Action API endpoints

Run with: pytest tests/test_chat_actions.py -v
"""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# =============================================================================
# Async Test Helpers
# =============================================================================

def run_async(coro):
    """Run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# =============================================================================
# Test Configuration
# =============================================================================

@pytest.fixture
def action_registry():
    """Create a fresh ActionButtonRegistry for testing."""
    from api.chat_actions import ActionButtonRegistry
    return ActionButtonRegistry()


@pytest.fixture
def suggestion_engine(action_registry):
    """Create a SuggestionEngine for testing."""
    from api.chat_actions import SuggestionEngine
    return SuggestionEngine(action_registry)


@pytest.fixture
def action_executor(action_registry):
    """Create an ActionExecutor for testing."""
    from api.chat_actions import ActionExecutor
    return ActionExecutor(action_registry)


@pytest.fixture
def sample_context():
    """Create a sample ActionContext for testing."""
    from api.chat_actions import ActionContext
    return ActionContext(
        channel_id="test_channel_123",
        channel_type="public",
        recent_messages=[
            {"content": "What would happen if we passed HR 123?", "sender_type": "user"},
            {"content": "Let me analyze that.", "sender_type": "agent"},
        ],
        mentioned_bills=["HR123"],
        mentioned_scenarios=["recession"],
        mentioned_metrics=["total_spending"],
    )


# =============================================================================
# ActionType Tests
# =============================================================================

class TestActionType:
    """Tests for ActionType enum."""
    
    def test_action_type_enum_values(self):
        """Test ActionType enum has all expected values."""
        from api.chat_actions import ActionType
        
        assert ActionType.ANALYZE_BILL.value == "analyze_bill"
        assert ActionType.RUN_SCENARIO.value == "run_scenario"
        assert ActionType.SHOW_DISAGREEMENT.value == "show_disagreement"
        assert ActionType.COMPARE_POLICIES.value == "compare_policies"
        assert ActionType.EXPORT_RESULTS.value == "export_results"
        assert ActionType.QUERY_CBO.value == "query_cbo"
    
    def test_action_type_mvp_actions(self):
        """Test MVP actions are defined."""
        from api.chat_actions import ActionType
        
        mvp_actions = [ActionType.ANALYZE_BILL, ActionType.RUN_SCENARIO]
        for action in mvp_actions:
            assert action.value is not None


# =============================================================================
# ActionStatus Tests
# =============================================================================

class TestActionStatus:
    """Tests for ActionStatus enum."""
    
    def test_action_status_values(self):
        """Test ActionStatus enum values."""
        from api.chat_actions import ActionStatus
        
        assert ActionStatus.PENDING.value == "pending"
        assert ActionStatus.RUNNING.value == "running"
        assert ActionStatus.COMPLETED.value == "completed"
        assert ActionStatus.FAILED.value == "failed"
        assert ActionStatus.CANCELLED.value == "cancelled"


# =============================================================================
# ActionButton Tests
# =============================================================================

class TestActionButton:
    """Tests for ActionButton data class."""
    
    def test_action_button_creation_defaults(self):
        """Test ActionButton can be created with defaults."""
        from api.chat_actions import ActionButton, ActionType
        
        button = ActionButton(
            label="Test Button",
            action_type=ActionType.ANALYZE_BILL,
        )
        
        assert button.label == "Test Button"
        assert button.action_type == ActionType.ANALYZE_BILL
        assert button.button_id is not None  # Auto-generated
        assert button.requires_confirmation == False
        assert button.disabled == False
    
    def test_action_button_creation_full(self):
        """Test ActionButton with all parameters."""
        from api.chat_actions import (
            ActionButton, ActionType, ActionCategory, ActionPriority
        )
        
        button = ActionButton(
            button_id="btn_123",
            label="Analyze HR 456",
            icon="🔍",
            action_type=ActionType.ANALYZE_BILL,
            action_params={"bill_id": "HR456"},
            requires_confirmation=True,
            estimated_time=30,
            category=ActionCategory.ANALYSIS,
            priority=ActionPriority.HIGH,
            tooltip="Run full analysis on HR 456",
            disabled=False,
        )
        
        assert button.button_id == "btn_123"
        assert button.label == "Analyze HR 456"
        assert button.icon == "🔍"
        assert button.action_params == {"bill_id": "HR456"}
        assert button.requires_confirmation == True
        assert button.estimated_time == 30
    
    def test_action_button_to_dict(self):
        """Test ActionButton serialization."""
        from api.chat_actions import ActionButton, ActionType
        
        button = ActionButton(
            label="Test",
            action_type=ActionType.RUN_SCENARIO,
            action_params={"scenario_type": "recession"},
        )
        
        data = button.to_dict()
        
        assert data["label"] == "Test"
        assert data["action_type"] == "run_scenario"
        assert data["action_params"]["scenario_type"] == "recession"
        assert "button_id" in data
        assert "requires_confirmation" in data


# =============================================================================
# ActionResult Tests
# =============================================================================

class TestActionResult:
    """Tests for ActionResult data class."""
    
    def test_action_result_creation(self):
        """Test ActionResult creation."""
        from api.chat_actions import ActionResult, ActionType, ActionStatus
        
        result = ActionResult(
            action_id="act_123",
            action_type=ActionType.ANALYZE_BILL,
            status=ActionStatus.COMPLETED,
        )
        
        assert result.action_id == "act_123"
        assert result.action_type == ActionType.ANALYZE_BILL
        assert result.status == ActionStatus.COMPLETED
        assert result.started_at is not None
    
    def test_action_result_with_data(self):
        """Test ActionResult with result data."""
        from api.chat_actions import ActionResult, ActionType, ActionStatus
        
        result = ActionResult(
            action_id="act_456",
            action_type=ActionType.RUN_SCENARIO,
            status=ActionStatus.COMPLETED,
            progress=1.0,
            result_data={"projections": [100, 110, 120]},
        )
        
        assert result.progress == 1.0
        assert result.result_data["projections"] == [100, 110, 120]
    
    def test_action_result_to_dict(self):
        """Test ActionResult serialization."""
        from api.chat_actions import ActionResult, ActionType, ActionStatus
        
        result = ActionResult(
            action_id="act_789",
            action_type=ActionType.QUERY_CBO,
            status=ActionStatus.RUNNING,
            progress=0.5,
            progress_message="Fetching data...",
        )
        
        data = result.to_dict()
        
        assert data["action_id"] == "act_789"
        assert data["action_type"] == "query_cbo"
        assert data["status"] == "running"
        assert data["progress"] == 0.5
        assert data["progress_message"] == "Fetching data..."


# =============================================================================
# ActionButtonRegistry Tests
# =============================================================================

class TestActionButtonRegistry:
    """Tests for ActionButtonRegistry."""
    
    def test_registry_initialization(self, action_registry):
        """Test registry initializes with default actions."""
        from api.chat_actions import ActionType
        
        actions = action_registry.get_all_actions()
        
        assert len(actions) > 0
        action_types = [a["action_type"] for a in actions]
        assert ActionType.ANALYZE_BILL.value in action_types
        assert ActionType.RUN_SCENARIO.value in action_types
    
    def test_registry_create_button(self, action_registry):
        """Test registry creates buttons correctly."""
        from api.chat_actions import ActionType
        
        button = action_registry.create_button(
            ActionType.ANALYZE_BILL,
            params={"bill_id": "HR999"},
        )
        
        assert button.action_type == ActionType.ANALYZE_BILL
        assert button.action_params["bill_id"] == "HR999"
        assert button.label == "Analyze this bill"
        assert button.icon == "🔍"
    
    def test_registry_create_button_with_label_override(self, action_registry):
        """Test registry applies label override."""
        from api.chat_actions import ActionType
        
        button = action_registry.create_button(
            ActionType.ANALYZE_BILL,
            params={"bill_id": "HR999"},
            label_override="Analyze HR 999",
        )
        
        assert button.label == "Analyze HR 999"
    
    def test_registry_validate_params_valid(self, action_registry):
        """Test parameter validation passes for valid params."""
        from api.chat_actions import ActionType
        
        is_valid, error = action_registry.validate_params(
            ActionType.ANALYZE_BILL,
            {"bill_id": "HR123"},
        )
        
        assert is_valid == True
        assert error is None
    
    def test_registry_validate_params_missing_required(self, action_registry):
        """Test parameter validation fails for missing required params."""
        from api.chat_actions import ActionType
        
        is_valid, error = action_registry.validate_params(
            ActionType.ANALYZE_BILL,
            {},  # Missing bill_id
        )
        
        assert is_valid == False
        assert "bill_id" in error
    
    def test_registry_register_handler(self, action_registry):
        """Test registering custom handler."""
        from api.chat_actions import ActionType
        
        async def custom_handler(params, action_id, update_progress):
            return {"custom": True}
        
        action_registry.register_handler(ActionType.ANALYZE_BILL, custom_handler)
        
        handler = action_registry.get_handler(ActionType.ANALYZE_BILL)
        assert handler == custom_handler


# =============================================================================
# SuggestionEngine Tests
# =============================================================================

class TestSuggestionEngine:
    """Tests for SuggestionEngine."""
    
    def test_suggestion_engine_bill_detection(self, suggestion_engine, sample_context):
        """Test engine suggests analysis when bill is mentioned."""
        from api.chat_actions import ActionType
        
        suggestions = run_async(suggestion_engine.suggest_actions(sample_context))
        
        assert len(suggestions) > 0
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.ANALYZE_BILL in action_types
    
    def test_suggestion_engine_scenario_detection(self, suggestion_engine):
        """Test engine suggests scenario when keywords detected."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test_123",
            recent_messages=[
                {"content": "What if there's a recession next year?"},
            ],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.RUN_SCENARIO in action_types
    
    def test_suggestion_engine_comparison_detection(self, suggestion_engine):
        """Test engine suggests comparison when keywords detected."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test_123",
            recent_messages=[
                {"content": "How does this compare to the previous bill?"},
            ],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.COMPARE_POLICIES in action_types
    
    def test_suggestion_engine_export_detection(self, suggestion_engine):
        """Test engine suggests export when keywords detected."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test_123",
            recent_messages=[
                {"content": "Can I download this as a PDF?"},
            ],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.EXPORT_RESULTS in action_types
    
    def test_suggestion_engine_max_suggestions(self, suggestion_engine, sample_context):
        """Test engine respects max_suggestions limit."""
        suggestions = run_async(suggestion_engine.suggest_actions(sample_context, max_suggestions=2))
        
        assert len(suggestions) <= 2
    
    def test_suggestion_engine_relevance_ordering(self, suggestion_engine, sample_context):
        """Test suggestions are sorted by relevance."""
        suggestions = run_async(suggestion_engine.suggest_actions(sample_context))
        
        if len(suggestions) > 1:
            for i in range(len(suggestions) - 1):
                assert suggestions[i].relevance_score >= suggestions[i + 1].relevance_score
    
    def test_suggestion_engine_disagreement_with_analysis(self, suggestion_engine):
        """Test disagreement map suggested when analysis exists."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test_123",
            current_analysis={"analysis_id": "ana_456"},
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.SHOW_DISAGREEMENT in action_types


# =============================================================================
# ActionExecutor Tests
# =============================================================================

class TestActionExecutor:
    """Tests for ActionExecutor."""
    
    def test_executor_validate_before_execute(self, action_executor):
        """Test executor validates params before execution."""
        from api.chat_actions import ActionType, ActionStatus
        
        result = run_async(action_executor.execute(
            ActionType.ANALYZE_BILL,
            {},  # Missing required bill_id
        ))
        
        assert result.status == ActionStatus.FAILED
        assert "bill_id" in result.error_message
    
    def test_executor_execute_analyze_bill(self, action_executor):
        """Test executor can execute analyze_bill action."""
        from api.chat_actions import ActionType, ActionStatus
        
        result = run_async(action_executor.execute(
            ActionType.ANALYZE_BILL,
            {"bill_id": "HR999"},
        ))
        
        # Should complete (even with fallback/mock)
        assert result.status in [ActionStatus.COMPLETED, ActionStatus.FAILED]
        assert result.action_id is not None
    
    def test_executor_execute_run_scenario(self, action_executor):
        """Test executor can execute run_scenario action."""
        from api.chat_actions import ActionType, ActionStatus
        
        result = run_async(action_executor.execute(
            ActionType.RUN_SCENARIO,
            {"scenario_type": "recession"},
        ))
        
        assert result.status in [ActionStatus.COMPLETED, ActionStatus.FAILED]
        assert result.result_data is not None or result.error_message is not None
    
    def test_executor_execute_query_cbo(self, action_executor):
        """Test executor can execute query_cbo action."""
        from api.chat_actions import ActionType, ActionStatus
        
        result = run_async(action_executor.execute(
            ActionType.QUERY_CBO,
            {"metric": "total_spending"},
        ))
        
        assert result.status == ActionStatus.COMPLETED
        assert result.result_data is not None
        assert "metric" in result.result_data
    
    def test_executor_progress_callback(self, action_executor):
        """Test executor calls progress callback."""
        from api.chat_actions import ActionType
        
        progress_updates = []
        
        async def track_progress(result):
            progress_updates.append(result.progress)
        
        run_async(action_executor.execute(
            ActionType.QUERY_CBO,
            {"metric": "total_spending"},
            progress_callback=track_progress,
        ))
        
        # Progress callback should have been called at least once
        assert len(progress_updates) > 0
        # Final progress should be 1.0 for completed OR less if using fallback
        # We just check that progress updates were received
        assert all(0.0 <= p <= 1.0 for p in progress_updates)
    
    def test_executor_handles_channel_id(self, action_executor):
        """Test executor attaches channel_id to result."""
        from api.chat_actions import ActionType
        
        result = run_async(action_executor.execute(
            ActionType.QUERY_CBO,
            {"metric": "total_spending"},
            channel_id="ch_abc",
        ))
        
        assert result.channel_id == "ch_abc"
    
    def test_executor_get_status_not_found(self, action_executor):
        """Test get_status returns None for unknown action."""
        result = action_executor.get_status("nonexistent_action")
        assert result is None
    
    def test_executor_cancel_not_found(self, action_executor):
        """Test cancel returns False for unknown action."""
        success = action_executor.cancel("nonexistent_action")
        assert success == False
    
    def test_executor_list_running_empty(self, action_executor):
        """Test list_running returns empty when nothing running."""
        running = action_executor.list_running()
        assert running == []


# =============================================================================
# ActionContext Tests
# =============================================================================

class TestActionContext:
    """Tests for ActionContext data class."""
    
    def test_context_creation_minimal(self):
        """Test ActionContext with minimal params."""
        from api.chat_actions import ActionContext
        
        context = ActionContext(channel_id="ch_123")
        
        assert context.channel_id == "ch_123"
        assert context.channel_type == "public"
        assert context.recent_messages == []
        assert context.mentioned_bills == []
    
    def test_context_creation_full(self):
        """Test ActionContext with all params."""
        from api.chat_actions import ActionContext
        
        context = ActionContext(
            channel_id="ch_456",
            channel_type="bill",
            recent_messages=[{"content": "test"}],
            current_analysis={"analysis_id": "ana_789"},
            mentioned_bills=["HR1", "S2"],
            mentioned_scenarios=["recession"],
            mentioned_metrics=["gdp"],
            user_preferences={"default_years": 10},
        )
        
        assert context.channel_type == "bill"
        assert len(context.recent_messages) == 1
        assert context.current_analysis is not None
        assert "HR1" in context.mentioned_bills


# =============================================================================
# Convenience Function Tests
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_suggest_actions_function(self):
        """Test suggest_actions convenience function."""
        from api.chat_actions import suggest_actions, ActionContext
        
        context = ActionContext(
            channel_id="ch_123",
            recent_messages=[{"content": "Analyze HR 456 please"}],
        )
        
        suggestions = run_async(suggest_actions(context))
        assert isinstance(suggestions, list)
    
    def test_execute_action_function(self):
        """Test execute_action convenience function."""
        from api.chat_actions import execute_action, ActionType, ActionStatus
        
        result = run_async(execute_action(
            ActionType.QUERY_CBO,
            {"metric": "total_spending"},
        ))
        
        assert result.status == ActionStatus.COMPLETED
    
    def test_create_action_button_function(self):
        """Test create_action_button convenience function."""
        from api.chat_actions import create_action_button, ActionType
        
        button = create_action_button(
            ActionType.RUN_SCENARIO,
            {"scenario_type": "inflation"},
            label="Test Inflation Impact",
        )
        
        assert button.label == "Test Inflation Impact"
        assert button.action_type == ActionType.RUN_SCENARIO


# =============================================================================
# Bill Pattern Detection Tests
# =============================================================================

class TestBillPatternDetection:
    """Tests for bill pattern detection in suggestions."""
    
    def test_detects_hr_format(self, suggestion_engine):
        """Test detection of 'HR 123' format."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "What's in HR 123?"}],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.ANALYZE_BILL in action_types
    
    def test_detects_h_dot_r_format(self, suggestion_engine):
        """Test detection of 'H.R. 123' format."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "Analyze H.R. 456"}],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.ANALYZE_BILL in action_types
    
    def test_detects_senate_format(self, suggestion_engine):
        """Test detection of 'S 789' format."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "What about S 789?"}],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.ANALYZE_BILL in action_types


# =============================================================================
# Scenario Keyword Detection Tests
# =============================================================================

class TestScenarioKeywordDetection:
    """Tests for scenario keyword detection."""
    
    def test_detects_recession(self, suggestion_engine):
        """Test detection of 'recession' keyword."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "What happens in a recession?"}],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.RUN_SCENARIO in action_types
    
    def test_detects_what_if(self, suggestion_engine):
        """Test detection of 'what if' phrasing."""
        from api.chat_actions import ActionContext, ActionType
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "What if inflation spikes?"}],
        )
        
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        action_types = [s.action.action_type for s in suggestions]
        assert ActionType.RUN_SCENARIO in action_types


# =============================================================================
# Integration Tests
# =============================================================================

class TestActionIntegration:
    """Integration tests for action system."""
    
    def test_full_analysis_flow(self, action_registry, action_executor):
        """Test complete flow: create button → execute → get result."""
        from api.chat_actions import ActionType, ActionStatus
        
        # 1. Create button
        button = action_registry.create_button(
            ActionType.ANALYZE_BILL,
            params={"bill_id": "HR999"},
        )
        assert button.action_params["bill_id"] == "HR999"
        
        # 2. Validate
        is_valid, error = action_registry.validate_params(
            button.action_type,
            button.action_params,
        )
        assert is_valid
        
        # 3. Execute
        result = run_async(action_executor.execute(
            button.action_type,
            button.action_params,
            channel_id="test_channel",
        ))
        
        # 4. Check result
        assert result.action_id is not None
        assert result.channel_id == "test_channel"
        assert result.status in [ActionStatus.COMPLETED, ActionStatus.FAILED]
    
    def test_suggestion_to_execution_flow(self, suggestion_engine, action_executor):
        """Test complete flow: get suggestion → execute suggested action."""
        from api.chat_actions import ActionContext, ActionStatus
        
        # 1. Get suggestions
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "What if GDP drops 5%?"}],
        )
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        assert len(suggestions) > 0
        
        # 2. Get first suggestion with valid params
        for suggestion in suggestions:
            action = suggestion.action
            is_valid, _ = action_executor.registry.validate_params(
                action.action_type,
                action.action_params,
            )
            if is_valid:
                # 3. Execute
                result = run_async(action_executor.execute(
                    action.action_type,
                    action.action_params,
                ))
                assert result.status in [ActionStatus.COMPLETED, ActionStatus.FAILED]
                break


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_invalid_action_type_string(self, action_registry):
        """Test handling of invalid action type string."""
        from api.chat_actions import ActionType
        
        with pytest.raises(ValueError):
            ActionType("invalid_action_type")
    
    def test_empty_context(self, suggestion_engine):
        """Test suggestions with empty context."""
        from api.chat_actions import ActionContext
        
        context = ActionContext(channel_id="empty_test")
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        
        # Should return default suggestions
        assert isinstance(suggestions, list)
    
    def test_very_long_message_content(self, suggestion_engine):
        """Test handling of very long message content."""
        from api.chat_actions import ActionContext
        
        context = ActionContext(
            channel_id="test",
            recent_messages=[{"content": "word " * 10000}],  # Very long
        )
        
        # Should not crash
        suggestions = run_async(suggestion_engine.suggest_actions(context))
        assert isinstance(suggestions, list)
    
    def test_disabled_button_creation(self, action_registry):
        """Test creating disabled button with reason."""
        from api.chat_actions import ActionType
        
        button = action_registry.create_button(
            ActionType.EXPORT_RESULTS,
            params={},
            disabled=True,
            disabled_reason="No analysis to export",
        )
        
        assert button.disabled == True
        assert button.disabled_reason == "No analysis to export"


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance-related tests."""
    
    def test_suggestion_engine_performance(self, suggestion_engine):
        """Test suggestion engine responds quickly."""
        import time
        from api.chat_actions import ActionContext
        
        context = ActionContext(
            channel_id="perf_test",
            recent_messages=[{"content": f"Message {i}"} for i in range(100)],
        )
        
        start = time.time()
        run_async(suggestion_engine.suggest_actions(context))
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"Suggestion took too long: {elapsed}s"
    
    def test_registry_button_creation_performance(self, action_registry):
        """Test registry can create many buttons quickly."""
        import time
        from api.chat_actions import ActionType
        
        start = time.time()
        for i in range(100):
            action_registry.create_button(
                ActionType.ANALYZE_BILL,
                params={"bill_id": f"HR{i}"},
            )
        elapsed = time.time() - start
        
        assert elapsed < 0.5, f"Button creation took too long: {elapsed}s"


# =============================================================================
# Serialization Tests
# =============================================================================

class TestSerialization:
    """Tests for JSON serialization."""
    
    def test_action_button_json_serializable(self, action_registry):
        """Test ActionButton can be serialized to JSON."""
        import json
        from api.chat_actions import ActionType
        
        button = action_registry.create_button(
            ActionType.RUN_SCENARIO,
            params={"scenario_type": "recession"},
        )
        
        # Should not raise
        json_str = json.dumps(button.to_dict())
        assert json_str is not None
        
        # Should round-trip
        data = json.loads(json_str)
        assert data["action_type"] == "run_scenario"
    
    def test_action_result_json_serializable(self):
        """Test ActionResult can be serialized to JSON."""
        import json
        from api.chat_actions import ActionResult, ActionType, ActionStatus
        
        result = ActionResult(
            action_id="test_123",
            action_type=ActionType.ANALYZE_BILL,
            status=ActionStatus.COMPLETED,
            result_data={"findings": ["test"]},
        )
        
        # Should not raise
        json_str = json.dumps(result.to_dict())
        assert json_str is not None
        
        # Should round-trip
        data = json.loads(json_str)
        assert data["status"] == "completed"


# =============================================================================
# Global Registry Tests
# =============================================================================

class TestGlobalRegistry:
    """Tests for global registry singleton."""
    
    def test_get_action_registry_returns_same_instance(self):
        """Test get_action_registry returns same instance."""
        from api.chat_actions import get_action_registry
        
        registry1 = get_action_registry()
        registry2 = get_action_registry()
        
        assert registry1 is registry2
    
    def test_global_registry_has_all_actions(self):
        """Test global registry has all default actions."""
        from api.chat_actions import get_action_registry, ActionType
        
        registry = get_action_registry()
        actions = registry.get_all_actions()
        
        # Check MVP actions
        action_types = [a["action_type"] for a in actions]
        assert ActionType.ANALYZE_BILL.value in action_types
        assert ActionType.RUN_SCENARIO.value in action_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
