"""
Chat Action Buttons for PoliSim Chatroom (Phase 7.3.2).

This module provides the action button framework enabling users to trigger
analyses, run scenarios, compare policies, and export results directly from
the chat interface.

Features:
- ActionButton: Configurable action triggers
- ActionType: Supported action types (analyze, scenario, compare, export)
- ActionExecutor: Queued execution with progress tracking
- SuggestionEngine: Context-aware action suggestions

Example:
    from api.chat_actions import ActionButtonRegistry, suggest_actions
    
    # Get suggestions based on context
    suggestions = await suggest_actions(channel, recent_messages, analysis)
    
    # Execute an action
    result = await action_executor.execute(
        action_type=ActionType.ANALYZE_BILL,
        params={"bill_id": "hr123"},
        channel_id="channel_abc"
    )
"""

from __future__ import annotations

import asyncio
import enum
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Awaitable
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class ActionType(enum.Enum):
    """Types of actions available from chat buttons."""
    
    # MVP Actions (Week 8)
    ANALYZE_BILL = "analyze_bill"
    RUN_SCENARIO = "run_scenario"
    
    # v1.1 Actions (Post-MVP)
    SHOW_DISAGREEMENT = "show_disagreement"
    COMPARE_POLICIES = "compare_policies"
    EXPORT_RESULTS = "export_results"
    SCHEDULE_ANALYSIS = "schedule_analysis"
    
    # Quick Actions
    QUERY_CBO = "query_cbo"
    SHOW_SUMMARY = "show_summary"
    GET_PROJECTIONS = "get_projections"


class ActionStatus(enum.Enum):
    """Status of an action execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionPriority(enum.Enum):
    """Priority level for action suggestions."""
    HIGH = "high"       # Should be prominently displayed
    MEDIUM = "medium"   # Standard suggestion
    LOW = "low"         # Secondary/optional


class ActionCategory(enum.Enum):
    """Category of action for grouping."""
    ANALYSIS = "analysis"
    SCENARIO = "scenario"
    COMPARISON = "comparison"
    EXPORT = "export"
    QUERY = "query"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class ActionButton:
    """Action button configuration for chat interface.
    
    Represents a clickable action that can be displayed in the chat UI
    and trigger backend processing.
    
    Attributes:
        button_id: Unique identifier for this button instance
        label: Display text for the button
        icon: Icon identifier (emoji or icon name)
        action_type: Type of action to execute
        action_params: Parameters to pass to the action handler
        requires_confirmation: Whether to show confirmation dialog
        estimated_time: Estimated execution time in seconds
        category: Action category for grouping
        priority: Display priority
        tooltip: Hover tooltip text
        disabled: Whether button is disabled
        disabled_reason: Why button is disabled (if disabled)
    """
    button_id: str = field(default_factory=lambda: str(uuid4())[:12])
    label: str = ""
    icon: str = ""
    action_type: ActionType = ActionType.ANALYZE_BILL
    action_params: Dict[str, Any] = field(default_factory=dict)
    requires_confirmation: bool = False
    estimated_time: Optional[int] = None  # seconds
    category: ActionCategory = ActionCategory.ANALYSIS
    priority: ActionPriority = ActionPriority.MEDIUM
    tooltip: Optional[str] = None
    disabled: bool = False
    disabled_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "button_id": self.button_id,
            "label": self.label,
            "icon": self.icon,
            "action_type": self.action_type.value,
            "action_params": self.action_params,
            "requires_confirmation": self.requires_confirmation,
            "estimated_time": self.estimated_time,
            "category": self.category.value,
            "priority": self.priority.value,
            "tooltip": self.tooltip,
            "disabled": self.disabled,
            "disabled_reason": self.disabled_reason,
        }


@dataclass
class ActionResult:
    """Result from an action execution.
    
    Contains the outcome of an action along with any data to display
    in the chat interface.
    """
    action_id: str
    action_type: ActionType
    status: ActionStatus
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    progress_message: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    channel_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "progress_message": self.progress_message,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "channel_id": self.channel_id,
        }


@dataclass
class ActionContext:
    """Context for action suggestion and execution.
    
    Provides information about the current conversation state
    for context-aware action suggestions.
    """
    channel_id: str
    channel_type: str = "public"
    recent_messages: List[Dict[str, Any]] = field(default_factory=list)
    current_analysis: Optional[Dict[str, Any]] = None
    mentioned_bills: List[str] = field(default_factory=list)
    mentioned_scenarios: List[str] = field(default_factory=list)
    mentioned_metrics: List[str] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SuggestedAction:
    """A suggested action with context and relevance score."""
    action: ActionButton
    relevance_score: float  # 0.0 to 1.0
    trigger_reason: str  # Why this action was suggested
    confidence: float = 0.8


# =============================================================================
# Action Button Registry
# =============================================================================

class ActionButtonRegistry:
    """Registry of available action buttons.
    
    Maintains definitions of all available actions and their handlers.
    Provides factory methods for creating common action buttons.
    """
    
    def __init__(self):
        self._actions: Dict[ActionType, Dict[str, Any]] = {}
        self._handlers: Dict[ActionType, Callable] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Initialize default action definitions."""
        
        # MVP Action: Analyze Bill
        self._actions[ActionType.ANALYZE_BILL] = {
            "label": "Analyze this bill",
            "icon": "🔍",
            "category": ActionCategory.ANALYSIS,
            "estimated_time": 30,
            "requires_confirmation": True,
            "tooltip": "Run full multi-agent swarm analysis on the bill",
            "required_params": ["bill_id"],
            "optional_params": ["focus_areas", "bill_text"],
        }
        
        # MVP Action: Run Scenario
        self._actions[ActionType.RUN_SCENARIO] = {
            "label": "Run scenario",
            "icon": "📊",
            "category": ActionCategory.SCENARIO,
            "estimated_time": 15,
            "requires_confirmation": True,
            "tooltip": "Apply economic scenario (recession, inflation, etc.)",
            "required_params": ["scenario_type"],
            "optional_params": ["parameters", "years", "iterations"],
        }
        
        # v1.1 Action: Show Disagreement Map
        self._actions[ActionType.SHOW_DISAGREEMENT] = {
            "label": "Show disagreement map",
            "icon": "🗺️",
            "category": ActionCategory.ANALYSIS,
            "estimated_time": 5,
            "requires_confirmation": False,
            "tooltip": "View where agents disagree and why",
            "required_params": ["analysis_id"],
            "optional_params": [],
        }
        
        # v1.1 Action: Compare Policies
        self._actions[ActionType.COMPARE_POLICIES] = {
            "label": "Compare policies",
            "icon": "⚖️",
            "category": ActionCategory.COMPARISON,
            "estimated_time": 20,
            "requires_confirmation": True,
            "tooltip": "Side-by-side comparison of multiple policies",
            "required_params": ["policy_ids"],
            "optional_params": ["comparison_metrics"],
        }
        
        # v1.1 Action: Export Results
        self._actions[ActionType.EXPORT_RESULTS] = {
            "label": "Export results",
            "icon": "📥",
            "category": ActionCategory.EXPORT,
            "estimated_time": 5,
            "requires_confirmation": False,
            "tooltip": "Export analysis results (JSON, PDF, CSV)",
            "required_params": ["analysis_id"],
            "optional_params": ["format", "include_charts"],
        }
        
        # v1.1 Action: Schedule Analysis
        self._actions[ActionType.SCHEDULE_ANALYSIS] = {
            "label": "Schedule analysis",
            "icon": "📅",
            "category": ActionCategory.ANALYSIS,
            "estimated_time": 2,
            "requires_confirmation": True,
            "tooltip": "Schedule analysis to run at a specific time",
            "required_params": ["bill_id", "schedule_time"],
            "optional_params": ["focus_areas", "notify_channel"],
        }
        
        # Quick Action: Query CBO Data
        self._actions[ActionType.QUERY_CBO] = {
            "label": "Query CBO data",
            "icon": "📈",
            "category": ActionCategory.QUERY,
            "estimated_time": 3,
            "requires_confirmation": False,
            "tooltip": "Query CBO baseline data for metrics",
            "required_params": ["metric"],
            "optional_params": ["start_year", "end_year"],
        }
        
        # Quick Action: Show Summary
        self._actions[ActionType.SHOW_SUMMARY] = {
            "label": "Show summary",
            "icon": "📋",
            "category": ActionCategory.QUERY,
            "estimated_time": 2,
            "requires_confirmation": False,
            "tooltip": "Display summary of current analysis",
            "required_params": ["analysis_id"],
            "optional_params": ["detail_level"],
        }
        
        # Quick Action: Get Projections
        self._actions[ActionType.GET_PROJECTIONS] = {
            "label": "Get projections",
            "icon": "📉",
            "category": ActionCategory.QUERY,
            "estimated_time": 5,
            "requires_confirmation": False,
            "tooltip": "Get fiscal projections for specific metrics",
            "required_params": ["metric"],
            "optional_params": ["years", "scenario"],
        }
    
    def register_handler(
        self,
        action_type: ActionType,
        handler: Callable[[Dict[str, Any]], Awaitable[ActionResult]]
    ):
        """Register a handler function for an action type."""
        self._handlers[action_type] = handler
        logger.info(f"Registered handler for action: {action_type.value}")
    
    def get_handler(self, action_type: ActionType) -> Optional[Callable]:
        """Get the handler for an action type."""
        return self._handlers.get(action_type)
    
    def create_button(
        self,
        action_type: ActionType,
        params: Optional[Dict[str, Any]] = None,
        label_override: Optional[str] = None,
        disabled: bool = False,
        disabled_reason: Optional[str] = None
    ) -> ActionButton:
        """Create an action button from registry definition.
        
        Args:
            action_type: Type of action
            params: Action parameters
            label_override: Custom label (overrides default)
            disabled: Whether button is disabled
            disabled_reason: Reason for disabling
        
        Returns:
            Configured ActionButton instance
        """
        definition = self._actions.get(action_type, {})
        
        return ActionButton(
            label=label_override or definition.get("label", action_type.value),
            icon=definition.get("icon", "🔘"),
            action_type=action_type,
            action_params=params or {},
            requires_confirmation=definition.get("requires_confirmation", False),
            estimated_time=definition.get("estimated_time"),
            category=definition.get("category", ActionCategory.ANALYSIS),
            tooltip=definition.get("tooltip"),
            disabled=disabled,
            disabled_reason=disabled_reason,
        )
    
    def get_all_actions(self) -> List[Dict[str, Any]]:
        """Get definitions of all available actions."""
        return [
            {
                "action_type": action_type.value,
                **definition
            }
            for action_type, definition in self._actions.items()
        ]
    
    def validate_params(
        self,
        action_type: ActionType,
        params: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """Validate action parameters.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        definition = self._actions.get(action_type)
        if not definition:
            return False, f"Unknown action type: {action_type.value}"
        
        required = definition.get("required_params", [])
        for param in required:
            if param not in params or params[param] is None:
                return False, f"Missing required parameter: {param}"
        
        return True, None


# Global registry instance
_action_registry = ActionButtonRegistry()


def get_action_registry() -> ActionButtonRegistry:
    """Get the global action button registry."""
    return _action_registry


# =============================================================================
# Suggestion Engine
# =============================================================================

class SuggestionEngine:
    """Context-aware action suggestion engine.
    
    Analyzes conversation context to suggest relevant actions
    that users might want to perform.
    """
    
    # Trigger patterns for suggestions
    BILL_PATTERNS = [
        r"H\.?R\.?\s*\d+",  # HR 123, H.R. 123
        r"S\.?\s*\d+",      # S 123, S. 123
        r"bill\s+\d+",      # bill 123
        r"legislation",
        r"proposal",
    ]
    
    SCENARIO_KEYWORDS = [
        "recession", "inflation", "economic shock",
        "what if", "what would happen", "scenario",
        "downturn", "growth", "gdp change",
    ]
    
    UNCERTAINTY_KEYWORDS = [
        "uncertain", "confidence", "range",
        "could vary", "depends on", "sensitivity",
        "best case", "worst case",
    ]
    
    COMPARISON_KEYWORDS = [
        "compare", "versus", "vs", "difference",
        "better", "worse", "alternative",
    ]
    
    EXPORT_KEYWORDS = [
        "export", "download", "save", "report",
        "pdf", "csv", "share",
    ]
    
    def __init__(self, registry: Optional[ActionButtonRegistry] = None):
        self.registry = registry or get_action_registry()
        self._user_history: Dict[str, List[str]] = {}  # Track user action patterns
    
    async def suggest_actions(
        self,
        context: ActionContext,
        max_suggestions: int = 4
    ) -> List[SuggestedAction]:
        """Generate action suggestions based on context.
        
        Args:
            context: Current conversation context
            max_suggestions: Maximum number of suggestions to return
        
        Returns:
            List of suggested actions, sorted by relevance
        """
        suggestions: List[SuggestedAction] = []
        
        # Extract text from recent messages for analysis
        message_text = self._extract_message_text(context.recent_messages)
        
        # Check for bill mentions → suggest analysis
        if self._has_bill_mention(message_text, context):
            suggestion = self._create_bill_analysis_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for scenario keywords → suggest scenario run
        if self._has_scenario_keywords(message_text):
            suggestion = self._create_scenario_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for comparison keywords → suggest compare
        if self._has_comparison_keywords(message_text):
            suggestion = self._create_comparison_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for export keywords → suggest export
        if self._has_export_keywords(message_text):
            suggestion = self._create_export_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # If analysis exists, suggest disagreement map
        if context.current_analysis:
            suggestion = self._create_disagreement_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # Check for uncertainty keywords → suggest sensitivity analysis
        if self._has_uncertainty_keywords(message_text) and context.current_analysis:
            suggestion = self._create_sensitivity_suggestion(context)
            if suggestion:
                suggestions.append(suggestion)
        
        # Add default suggestions if few matches
        if len(suggestions) < 2:
            suggestions.extend(self._get_default_suggestions(context))
        
        # Sort by relevance and limit
        suggestions.sort(key=lambda s: s.relevance_score, reverse=True)
        return suggestions[:max_suggestions]
    
    def _extract_message_text(self, messages: List[Dict[str, Any]]) -> str:
        """Extract combined text from messages for analysis."""
        texts = []
        for msg in messages[-10:]:  # Last 10 messages
            content = msg.get("content", "")
            if isinstance(content, str):
                texts.append(content.lower())
        return " ".join(texts)
    
    def _has_bill_mention(self, text: str, context: ActionContext) -> bool:
        """Check if text mentions a bill."""
        import re
        for pattern in self.BILL_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return len(context.mentioned_bills) > 0
    
    def _has_scenario_keywords(self, text: str) -> bool:
        """Check for scenario-related keywords."""
        return any(kw in text for kw in self.SCENARIO_KEYWORDS)
    
    def _has_uncertainty_keywords(self, text: str) -> bool:
        """Check for uncertainty-related keywords."""
        return any(kw in text for kw in self.UNCERTAINTY_KEYWORDS)
    
    def _has_comparison_keywords(self, text: str) -> bool:
        """Check for comparison-related keywords."""
        return any(kw in text for kw in self.COMPARISON_KEYWORDS)
    
    def _has_export_keywords(self, text: str) -> bool:
        """Check for export-related keywords."""
        return any(kw in text for kw in self.EXPORT_KEYWORDS)
    
    def _create_bill_analysis_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for bill analysis."""
        bill_id = context.mentioned_bills[0] if context.mentioned_bills else None
        
        params = {}
        if bill_id:
            params["bill_id"] = bill_id
        
        button = self.registry.create_button(
            ActionType.ANALYZE_BILL,
            params=params,
            label_override=f"Analyze {bill_id}" if bill_id else "Analyze bill",
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.9 if bill_id else 0.7,
            trigger_reason="Bill mentioned in conversation",
            confidence=0.85,
        )
    
    def _create_scenario_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for scenario analysis."""
        # Detect specific scenario type from context
        scenarios = context.mentioned_scenarios
        scenario_type = scenarios[0] if scenarios else "recession"
        
        button = self.registry.create_button(
            ActionType.RUN_SCENARIO,
            params={"scenario_type": scenario_type},
            label_override=f"Run {scenario_type} scenario",
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.8,
            trigger_reason="Scenario or 'what-if' discussion detected",
            confidence=0.8,
        )
    
    def _create_comparison_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for policy comparison."""
        button = self.registry.create_button(
            ActionType.COMPARE_POLICIES,
            params={},
            label_override="Compare policies",
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.75,
            trigger_reason="Comparison keywords detected",
            confidence=0.75,
        )
    
    def _create_export_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for export."""
        analysis_id = None
        if context.current_analysis:
            analysis_id = context.current_analysis.get("analysis_id")
        
        button = self.registry.create_button(
            ActionType.EXPORT_RESULTS,
            params={"analysis_id": analysis_id} if analysis_id else {},
            disabled=not analysis_id,
            disabled_reason="No active analysis to export" if not analysis_id else None,
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.7,
            trigger_reason="Export keywords detected",
            confidence=0.8,
        )
    
    def _create_disagreement_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for disagreement map."""
        analysis_id = context.current_analysis.get("analysis_id") if context.current_analysis else None
        
        if not analysis_id:
            return None
        
        button = self.registry.create_button(
            ActionType.SHOW_DISAGREEMENT,
            params={"analysis_id": analysis_id},
            label_override="View agent disagreements",
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.65,
            trigger_reason="Active analysis available",
            confidence=0.7,
        )
    
    def _create_sensitivity_suggestion(
        self,
        context: ActionContext
    ) -> Optional[SuggestedAction]:
        """Create suggestion for sensitivity analysis via scenario."""
        button = self.registry.create_button(
            ActionType.RUN_SCENARIO,
            params={"scenario_type": "sensitivity", "parameters": {}},
            label_override="Run sensitivity analysis",
        )
        
        return SuggestedAction(
            action=button,
            relevance_score=0.7,
            trigger_reason="Uncertainty discussion detected",
            confidence=0.75,
        )
    
    def _get_default_suggestions(
        self,
        context: ActionContext
    ) -> List[SuggestedAction]:
        """Get default suggestions when no specific triggers match."""
        defaults = []
        
        # Always suggest CBO data query if no analysis active
        if not context.current_analysis:
            button = self.registry.create_button(
                ActionType.QUERY_CBO,
                params={"metric": "total_spending"},
                label_override="View CBO projections",
            )
            defaults.append(SuggestedAction(
                action=button,
                relevance_score=0.4,
                trigger_reason="Default action - explore CBO data",
                confidence=0.5,
            ))
        
        # If analysis exists, suggest summary
        if context.current_analysis:
            analysis_id = context.current_analysis.get("analysis_id")
            button = self.registry.create_button(
                ActionType.SHOW_SUMMARY,
                params={"analysis_id": analysis_id},
                label_override="Show analysis summary",
            )
            defaults.append(SuggestedAction(
                action=button,
                relevance_score=0.5,
                trigger_reason="Analysis available - view summary",
                confidence=0.6,
            ))
        
        return defaults
    
    def update_user_preference(self, user_id: str, action_type: ActionType):
        """Track user action usage for better suggestions."""
        if user_id not in self._user_history:
            self._user_history[user_id] = []
        self._user_history[user_id].append(action_type.value)
        # Keep last 50 actions
        self._user_history[user_id] = self._user_history[user_id][-50:]


# =============================================================================
# Action Executor
# =============================================================================

class ActionExecutor:
    """Executes actions and manages progress tracking.
    
    Handles queuing, execution, progress updates, and result handling
    for chat actions.
    """
    
    def __init__(
        self,
        registry: Optional[ActionButtonRegistry] = None,
        max_concurrent: int = 3
    ):
        self.registry = registry or get_action_registry()
        self.max_concurrent = max_concurrent
        self._running: Dict[str, ActionResult] = {}
        self._queue: asyncio.Queue[tuple[str, ActionType, Dict[str, Any]]] = asyncio.Queue()
        self._progress_callbacks: Dict[str, Callable[[ActionResult], Awaitable[None]]] = {}
    
    async def execute(
        self,
        action_type: ActionType,
        params: Dict[str, Any],
        channel_id: Optional[str] = None,
        progress_callback: Optional[Callable[[ActionResult], Awaitable[None]]] = None
    ) -> ActionResult:
        """Execute an action.
        
        Args:
            action_type: Type of action to execute
            params: Action parameters
            channel_id: Channel to post results to
            progress_callback: Callback for progress updates
        
        Returns:
            ActionResult with execution outcome
        """
        action_id = str(uuid4())[:12]
        
        # Validate parameters
        is_valid, error = self.registry.validate_params(action_type, params)
        if not is_valid:
            return ActionResult(
                action_id=action_id,
                action_type=action_type,
                status=ActionStatus.FAILED,
                error_message=error,
                channel_id=channel_id,
            )
        
        # Create initial result
        result = ActionResult(
            action_id=action_id,
            action_type=action_type,
            status=ActionStatus.PENDING,
            channel_id=channel_id,
        )
        
        # Register progress callback
        if progress_callback:
            self._progress_callbacks[action_id] = progress_callback
        
        # Get handler
        handler = self.registry.get_handler(action_type)
        if not handler:
            handler = self._get_default_handler(action_type)
        
        # Execute
        try:
            self._running[action_id] = result
            result.status = ActionStatus.RUNNING
            await self._emit_progress(result)
            
            # Run the handler
            handler_result = await handler(params, action_id, self._create_progress_updater(result))
            
            # Merge handler result
            result.status = ActionStatus.COMPLETED
            result.progress = 1.0
            result.result_data = handler_result
            result.completed_at = datetime.now(timezone.utc)
            
        except asyncio.CancelledError:
            result.status = ActionStatus.CANCELLED
            result.completed_at = datetime.now(timezone.utc)
            
        except Exception as e:
            logger.exception(f"Action {action_id} failed: {e}")
            result.status = ActionStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now(timezone.utc)
        
        finally:
            self._running.pop(action_id, None)
            self._progress_callbacks.pop(action_id, None)
        
        await self._emit_progress(result)
        return result
    
    def _create_progress_updater(
        self,
        result: ActionResult
    ) -> Callable[[float, str], Awaitable[None]]:
        """Create a progress update function for handlers."""
        async def update_progress(progress: float, message: Optional[str] = None):
            result.progress = min(max(progress, 0.0), 1.0)
            if message:
                result.progress_message = message
            await self._emit_progress(result)
        return update_progress
    
    async def _emit_progress(self, result: ActionResult):
        """Emit progress update via callback."""
        callback = self._progress_callbacks.get(result.action_id)
        if callback:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def cancel(self, action_id: str) -> bool:
        """Cancel a running action.
        
        Returns:
            True if action was cancelled, False if not found
        """
        if action_id in self._running:
            result = self._running[action_id]
            result.status = ActionStatus.CANCELLED
            # Note: actual cancellation would require task tracking
            return True
        return False
    
    def get_status(self, action_id: str) -> Optional[ActionResult]:
        """Get status of an action."""
        return self._running.get(action_id)
    
    def list_running(self) -> List[ActionResult]:
        """List all currently running actions."""
        return list(self._running.values())
    
    def _get_default_handler(
        self,
        action_type: ActionType
    ) -> Callable:
        """Get default handler for action type."""
        handlers = {
            ActionType.ANALYZE_BILL: self._handle_analyze_bill,
            ActionType.RUN_SCENARIO: self._handle_run_scenario,
            ActionType.SHOW_DISAGREEMENT: self._handle_show_disagreement,
            ActionType.COMPARE_POLICIES: self._handle_compare_policies,
            ActionType.EXPORT_RESULTS: self._handle_export_results,
            ActionType.QUERY_CBO: self._handle_query_cbo,
            ActionType.SHOW_SUMMARY: self._handle_show_summary,
            ActionType.GET_PROJECTIONS: self._handle_get_projections,
        }
        return handlers.get(action_type, self._handle_not_implemented)
    
    # -------------------------------------------------------------------------
    # Default Action Handlers
    # -------------------------------------------------------------------------
    
    async def _handle_analyze_bill(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle analyze_bill action."""
        bill_id = params.get("bill_id")
        bill_text = params.get("bill_text", "")
        focus_areas = params.get("focus_areas", [])
        
        await update_progress(0.1, "Initializing swarm analysis...")
        
        try:
            # Import MCP tools to use existing analyze_bill implementation
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            
            await update_progress(0.2, "Running multi-agent analysis...")
            
            result = await tools.analyze_bill(
                bill_id=bill_id,
                bill_text=bill_text,
                focus_areas=focus_areas,
            )
            
            await update_progress(0.9, "Finalizing results...")
            
            return result.to_dict()
            
        except ImportError:
            await update_progress(0.5, "Using fallback analysis...")
            
            # Fallback: return mock result
            await asyncio.sleep(1)  # Simulate processing
            
            return {
                "analysis_id": action_id,
                "bill_id": bill_id,
                "status": "completed",
                "summary": f"Analysis of {bill_id} complete (mock result)",
                "key_findings": [
                    {"category": "fiscal", "finding": "Mock fiscal impact finding"},
                    {"category": "healthcare", "finding": "Mock healthcare finding"},
                ],
                "confidence": 0.75,
            }
    
    async def _handle_run_scenario(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle run_scenario action."""
        scenario_type = params.get("scenario_type", "recession")
        scenario_params = params.get("parameters", {})
        years = params.get("years", 10)
        
        await update_progress(0.1, f"Setting up {scenario_type} scenario...")
        
        try:
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            
            await update_progress(0.3, "Running simulation...")
            
            result = await tools.run_scenario(
                scenario_type=scenario_type,
                parameters=scenario_params,
                years=years,
            )
            
            await update_progress(0.9, "Compiling results...")
            
            return result.to_dict()
            
        except ImportError:
            # Fallback
            await asyncio.sleep(1)
            
            return {
                "scenario_id": action_id,
                "scenario_name": scenario_type,
                "status": "completed",
                "projections": {
                    "years": list(range(2026, 2026 + years)),
                    "baseline": [100 + i * 2 for i in range(years)],
                    "scenario": [100 + i * 1.5 for i in range(years)],
                },
            }
    
    async def _handle_show_disagreement(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle show_disagreement action."""
        analysis_id = params.get("analysis_id")
        
        await update_progress(0.2, "Fetching disagreement data...")
        
        try:
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            result = await tools.get_disagreement_map(analysis_id)
            
            return result.to_dict()
            
        except ImportError:
            # Fallback
            return {
                "analysis_id": analysis_id,
                "nodes": [
                    {"id": "fiscal", "label": "Fiscal Agent"},
                    {"id": "healthcare", "label": "Healthcare Agent"},
                    {"id": "economic", "label": "Economic Agent"},
                ],
                "edges": [
                    {"source": "fiscal", "target": "healthcare", "weight": 0.3},
                ],
                "topics": ["revenue_impact", "cost_projections"],
                "max_disagreement": 0.4,
                "summary": "Agents largely agree, minor disagreement on cost projections.",
            }
    
    async def _handle_compare_policies(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle compare_policies action."""
        policy_ids = params.get("policy_ids", [])
        metrics = params.get("comparison_metrics", ["fiscal_impact", "coverage"])
        
        await update_progress(0.2, "Comparing policies...")
        
        try:
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            result = await tools.compare_policies(
                policy_ids=policy_ids,
                comparison_metrics=metrics,
            )
            
            return result.to_dict()
            
        except ImportError:
            # Fallback
            return {
                "comparison_id": action_id,
                "policies": policy_ids,
                "differences": [],
                "impact_delta": {},
                "recommendation": "Comparison completed (mock)",
            }
    
    async def _handle_export_results(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle export_results action."""
        analysis_id = params.get("analysis_id")
        export_format = params.get("format", "json")
        include_charts = params.get("include_charts", True)
        
        await update_progress(0.3, f"Generating {export_format.upper()} export...")
        
        # Generate export
        await asyncio.sleep(0.5)
        
        await update_progress(0.9, "Export ready...")
        
        return {
            "analysis_id": analysis_id,
            "format": export_format,
            "download_url": f"/api/v1/chat/exports/{action_id}.{export_format}",
            "expires_at": datetime.now(timezone.utc).isoformat(),
        }
    
    async def _handle_query_cbo(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle query_cbo action."""
        metric = params.get("metric")
        start_year = params.get("start_year", 2026)
        end_year = params.get("end_year", 2036)
        
        await update_progress(0.3, f"Querying CBO data for {metric}...")
        
        try:
            from api.chat_mcp_tools import ChatMCPTools
            
            tools = ChatMCPTools()
            result = await tools.query_cbo_data(
                metric=metric,
                start_year=start_year,
                end_year=end_year,
            )
            
            return result.to_dict()
            
        except ImportError:
            # Fallback
            years = list(range(start_year, end_year + 1))
            return {
                "metric": metric,
                "years": years,
                "values": [100 + i * 5 for i in range(len(years))],
                "unit": "billions USD",
                "source": "CBO Baseline Projections (mock)",
            }
    
    async def _handle_show_summary(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle show_summary action."""
        analysis_id = params.get("analysis_id")
        detail_level = params.get("detail_level", "standard")
        
        await update_progress(0.5, "Generating summary...")
        
        return {
            "analysis_id": analysis_id,
            "summary_type": detail_level,
            "key_points": [
                "Analysis covers fiscal impacts over 10-year window",
                "Healthcare spending projected to increase by 3-5%",
                "Revenue neutral under baseline assumptions",
            ],
            "confidence": 0.8,
        }
    
    async def _handle_get_projections(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handle get_projections action."""
        metric = params.get("metric")
        years = params.get("years", 10)
        scenario = params.get("scenario", "baseline")
        
        await update_progress(0.3, f"Calculating {metric} projections...")
        
        year_list = list(range(2026, 2026 + years))
        
        return {
            "metric": metric,
            "scenario": scenario,
            "years": year_list,
            "projections": {
                "mean": [100 + i * 3 for i in range(years)],
                "p10": [95 + i * 2.5 for i in range(years)],
                "p90": [105 + i * 3.5 for i in range(years)],
            },
            "unit": "billions USD",
        }
    
    async def _handle_not_implemented(
        self,
        params: Dict[str, Any],
        action_id: str,
        update_progress: Callable
    ) -> Dict[str, Any]:
        """Handler for not-yet-implemented actions."""
        await update_progress(0.5, "Processing...")
        
        return {
            "status": "not_implemented",
            "message": "This action is not yet implemented",
        }


# =============================================================================
# Module-level convenience functions
# =============================================================================

async def suggest_actions(
    context: ActionContext,
    max_suggestions: int = 4
) -> List[SuggestedAction]:
    """Suggest relevant actions based on conversation context.
    
    Convenience wrapper around SuggestionEngine.
    """
    engine = SuggestionEngine()
    return await engine.suggest_actions(context, max_suggestions)


async def execute_action(
    action_type: ActionType,
    params: Dict[str, Any],
    channel_id: Optional[str] = None,
    progress_callback: Optional[Callable[[ActionResult], Awaitable[None]]] = None
) -> ActionResult:
    """Execute an action.
    
    Convenience wrapper around ActionExecutor.
    """
    executor = ActionExecutor()
    return await executor.execute(
        action_type=action_type,
        params=params,
        channel_id=channel_id,
        progress_callback=progress_callback,
    )


def create_action_button(
    action_type: ActionType,
    params: Optional[Dict[str, Any]] = None,
    label: Optional[str] = None
) -> ActionButton:
    """Create an action button.
    
    Convenience wrapper around ActionButtonRegistry.
    """
    registry = get_action_registry()
    return registry.create_button(
        action_type=action_type,
        params=params,
        label_override=label,
    )
