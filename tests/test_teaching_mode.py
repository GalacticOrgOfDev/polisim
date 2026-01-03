"""
Tests for Teaching Mode UI Module

Tests the educational enhancement features including:
- Tooltip content
- Guided tours
- Difficulty levels
- Progress tracking
"""

import pytest
from ui.teaching_mode import (
    TeachingMode,
    DifficultyLevel,
    TooltipContent,
    TourStep,
    GuidedTour,
    get_teaching_mode,
    configure_teaching_mode,
    teaching_tooltip,
    should_show_callout,
    get_callout_content,
)


class TestDifficultyLevel:
    """Test difficulty level enumeration."""
    
    def test_difficulty_levels_exist(self):
        """Verify all expected difficulty levels exist."""
        assert DifficultyLevel.BEGINNER.value == "beginner"
        assert DifficultyLevel.INTERMEDIATE.value == "intermediate"
        assert DifficultyLevel.ADVANCED.value == "advanced"
    
    def test_difficulty_from_string(self):
        """Test creating difficulty from string value."""
        assert DifficultyLevel("beginner") == DifficultyLevel.BEGINNER
        assert DifficultyLevel("intermediate") == DifficultyLevel.INTERMEDIATE
        assert DifficultyLevel("advanced") == DifficultyLevel.ADVANCED


class TestTooltipContent:
    """Test tooltip content dataclass."""
    
    def test_tooltip_creation(self):
        """Test creating a tooltip with all fields."""
        tooltip = TooltipContent(
            short="Brief description",
            detailed="Full explanation here",
            why_it_matters="Real-world relevance",
            learn_more_link="/docs/test.md",
            glossary_terms=["term1", "term2"]
        )
        
        assert tooltip.short == "Brief description"
        assert tooltip.detailed == "Full explanation here"
        assert tooltip.why_it_matters == "Real-world relevance"
        assert tooltip.learn_more_link == "/docs/test.md"
        assert len(tooltip.glossary_terms) == 2
    
    def test_tooltip_optional_fields(self):
        """Test tooltip with only required fields."""
        tooltip = TooltipContent(
            short="Brief",
            detailed="Details",
            why_it_matters="Importance"
        )
        
        assert tooltip.learn_more_link is None
        assert tooltip.glossary_terms == []


class TestTourStep:
    """Test guided tour step dataclass."""
    
    def test_tour_step_creation(self):
        """Test creating a tour step."""
        step = TourStep(
            element_id="test_element",
            title="Step Title",
            content="Step content goes here",
            position="bottom"
        )
        
        assert step.element_id == "test_element"
        assert step.title == "Step Title"
        assert step.content == "Step content goes here"
        assert step.position == "bottom"
        assert step.action is None
        assert step.wait_for is None


class TestTeachingMode:
    """Test TeachingMode class."""
    
    def test_initialization(self):
        """Test default initialization."""
        tm = TeachingMode()
        
        assert tm.enabled is True
        assert tm.level == DifficultyLevel.BEGINNER
        assert tm.show_explanations is True
        assert tm.show_why_it_matters is True
        assert tm.guided_tour_active is False
        assert tm.current_tour is None
        assert tm.completed_tours == []
    
    def test_initialization_with_params(self):
        """Test initialization with custom parameters."""
        tm = TeachingMode(
            level=DifficultyLevel.ADVANCED,
            enabled=False
        )
        
        assert tm.enabled is False
        assert tm.level == DifficultyLevel.ADVANCED
    
    def test_set_level(self):
        """Test changing difficulty level."""
        tm = TeachingMode()
        
        tm.set_level(DifficultyLevel.INTERMEDIATE)
        assert tm.level == DifficultyLevel.INTERMEDIATE
        assert tm.show_explanations is True
        assert tm.show_why_it_matters is False
        
        tm.set_level(DifficultyLevel.ADVANCED)
        assert tm.level == DifficultyLevel.ADVANCED
        assert tm.show_explanations is False
        assert tm.show_why_it_matters is False
    
    def test_get_tooltip_beginner(self):
        """Test tooltip content for beginner level."""
        tm = TeachingMode(level=DifficultyLevel.BEGINNER)
        
        tooltip = tm.get_tooltip("debt_total")
        
        assert "content" in tooltip
        assert "why_it_matters" in tooltip
        assert len(tooltip["content"]) > 0
    
    def test_get_tooltip_advanced(self):
        """Test tooltip content for advanced level (minimal)."""
        tm = TeachingMode(level=DifficultyLevel.ADVANCED)
        
        tooltip = tm.get_tooltip("debt_total")
        
        assert "content" in tooltip
        assert "why_it_matters" not in tooltip
    
    def test_get_tooltip_disabled(self):
        """Test tooltip when teaching mode is disabled."""
        tm = TeachingMode(enabled=False)
        
        tooltip = tm.get_tooltip("debt_total")
        
        assert tooltip == {"content": ""}
    
    def test_get_tooltip_unknown_element(self):
        """Test tooltip for unknown element ID."""
        tm = TeachingMode()
        
        tooltip = tm.get_tooltip("nonexistent_element")
        
        assert tooltip == {"content": ""}
    
    def test_get_all_tooltips(self):
        """Test getting all tooltips."""
        tm = TeachingMode()
        
        all_tooltips = tm.get_all_tooltips()
        
        assert isinstance(all_tooltips, dict)
        assert len(all_tooltips) > 0
        assert "debt_total" in all_tooltips
        assert "revenue_total" in all_tooltips


class TestGuidedTours:
    """Test guided tour functionality."""
    
    def test_get_available_tours(self):
        """Test listing available tours."""
        tm = TeachingMode(level=DifficultyLevel.BEGINNER)
        
        tours = tm.get_available_tours()
        
        assert isinstance(tours, list)
        assert len(tours) > 0
        
        # Check tour structure
        tour = tours[0]
        assert "id" in tour
        assert "name" in tour
        assert "description" in tour
        assert "estimated_time" in tour
        assert "completed" in tour
        assert "step_count" in tour
    
    def test_start_tour(self):
        """Test starting a guided tour."""
        tm = TeachingMode()
        
        step = tm.start_tour("dashboard_intro")
        
        assert step is not None
        assert tm.guided_tour_active is True
        assert tm.current_tour is not None
        assert step["step_number"] == 1
        assert "title" in step
        assert "content" in step
    
    def test_start_invalid_tour(self):
        """Test starting a non-existent tour."""
        tm = TeachingMode()
        
        step = tm.start_tour("nonexistent_tour")
        
        assert step is None
        assert tm.guided_tour_active is False
    
    def test_tour_navigation(self):
        """Test navigating through tour steps."""
        tm = TeachingMode()
        
        # Start tour
        step1 = tm.start_tour("dashboard_intro")
        assert step1["step_number"] == 1
        
        # Next step
        step2 = tm.next_step()
        assert step2 is not None
        assert step2["step_number"] == 2
        
        # Previous step
        step1_again = tm.previous_step()
        assert step1_again["step_number"] == 1
        
        # Previous at start doesn't go below 1
        tm.previous_step()
        current = tm._get_current_step()
        assert current["step_number"] == 1
    
    def test_skip_tour(self):
        """Test skipping/canceling a tour."""
        tm = TeachingMode()
        
        tm.start_tour("dashboard_intro")
        assert tm.guided_tour_active is True
        
        tm.skip_tour()
        assert tm.guided_tour_active is False
        assert tm.current_tour is None
    
    def test_tour_completion(self):
        """Test completing a tour."""
        tm = TeachingMode()
        
        tm.start_tour("dashboard_intro")
        tour = tm.current_tour
        
        # Navigate through all steps
        for _ in range(len(tour.steps)):
            tm.next_step()
        
        # Tour should be completed
        assert tm.guided_tour_active is False
        assert "dashboard_intro" in tm.completed_tours
    
    def test_tour_filtering_by_level(self):
        """Test that tours are filtered by difficulty level."""
        tm_beginner = TeachingMode(level=DifficultyLevel.BEGINNER)
        tm_advanced = TeachingMode(level=DifficultyLevel.ADVANCED)
        
        beginner_tours = tm_beginner.get_available_tours()
        advanced_tours = tm_advanced.get_available_tours()
        
        # Advanced users should see all tours (including beginner ones)
        assert len(advanced_tours) >= len(beginner_tours)


class TestCallouts:
    """Test educational callout functionality."""
    
    def test_get_callout(self):
        """Test getting a callout for a context."""
        tm = TeachingMode(level=DifficultyLevel.BEGINNER)
        
        callout = tm.get_callout("viewing_debt_chart")
        
        assert callout is not None
        assert "title" in callout
        assert "content" in callout
    
    def test_get_callout_unknown_context(self):
        """Test callout for unknown context."""
        tm = TeachingMode()
        
        callout = tm.get_callout("unknown_context")
        
        assert callout is None
    
    def test_get_callout_advanced_level(self):
        """Test that advanced users don't see callouts."""
        tm = TeachingMode(level=DifficultyLevel.ADVANCED)
        
        callout = tm.get_callout("viewing_debt_chart")
        
        assert callout is None


class TestProgressTracking:
    """Test learning progress tracking."""
    
    def test_initial_progress(self):
        """Test initial progress state."""
        tm = TeachingMode()
        
        progress = tm.get_learning_progress()
        
        assert progress["tours_completed"] == 0
        assert progress["completion_percentage"] == 0
        assert progress["current_level"] == "beginner"
        assert "suggested_next" in progress
    
    def test_progress_after_tour(self):
        """Test progress after completing a tour."""
        tm = TeachingMode()
        
        # Complete a tour
        tm.start_tour("dashboard_intro")
        tour = tm.current_tour
        for _ in range(len(tour.steps)):
            tm.next_step()
        
        progress = tm.get_learning_progress()
        
        assert progress["tours_completed"] == 1
        assert progress["completion_percentage"] > 0


class TestSerialization:
    """Test serialization and deserialization."""
    
    def test_to_dict(self):
        """Test serializing teaching mode state."""
        tm = TeachingMode(level=DifficultyLevel.INTERMEDIATE)
        tm.completed_tours = ["dashboard_intro"]
        
        data = tm.to_dict()
        
        assert data["enabled"] is True
        assert data["level"] == "intermediate"
        assert data["completed_tours"] == ["dashboard_intro"]
    
    def test_from_dict(self):
        """Test deserializing teaching mode state."""
        data = {
            "enabled": True,
            "level": "intermediate",
            "completed_tours": ["dashboard_intro", "first_simulation"],
            "guided_tour_active": False
        }
        
        tm = TeachingMode.from_dict(data)
        
        assert tm.level == DifficultyLevel.INTERMEDIATE
        assert len(tm.completed_tours) == 2


class TestGlobalFunctions:
    """Test module-level convenience functions."""
    
    def test_get_teaching_mode(self):
        """Test getting global teaching mode instance."""
        tm = get_teaching_mode()
        
        assert isinstance(tm, TeachingMode)
    
    def test_configure_teaching_mode(self):
        """Test configuring global teaching mode."""
        tm = configure_teaching_mode(enabled=True, level="advanced")
        
        assert tm.enabled is True
        assert tm.level == DifficultyLevel.ADVANCED
    
    def test_teaching_tooltip(self):
        """Test the teaching_tooltip helper function."""
        configure_teaching_mode(enabled=True, level="beginner")
        
        tooltip = teaching_tooltip("debt_total")
        
        assert isinstance(tooltip, str)
        assert len(tooltip) > 0
    
    def test_teaching_tooltip_disabled(self):
        """Test teaching_tooltip when disabled."""
        configure_teaching_mode(enabled=False)
        
        tooltip = teaching_tooltip("debt_total")
        
        assert tooltip == ""
    
    def test_should_show_callout(self):
        """Test should_show_callout helper."""
        configure_teaching_mode(enabled=True, level="beginner")
        
        assert should_show_callout("viewing_debt_chart") is True
        assert should_show_callout("unknown_context") is False
    
    def test_get_callout_content(self):
        """Test get_callout_content helper."""
        configure_teaching_mode(enabled=True, level="beginner")
        
        content = get_callout_content("viewing_debt_chart")
        
        assert content is not None
        assert "title" in content


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_next_step_without_active_tour(self):
        """Test next_step when no tour is active."""
        tm = TeachingMode()
        
        result = tm.next_step()
        
        assert result is None
    
    def test_previous_step_without_active_tour(self):
        """Test previous_step when no tour is active."""
        tm = TeachingMode()
        
        result = tm.previous_step()
        
        assert result is None
    
    def test_multiple_tour_starts(self):
        """Test starting a new tour while one is active."""
        tm = TeachingMode()
        
        tm.start_tour("dashboard_intro")
        step = tm.start_tour("first_simulation")
        
        assert step is not None
        assert tm.current_tour.id == "first_simulation"
    
    def test_empty_glossary_terms(self):
        """Test tooltip with no glossary terms."""
        tm = TeachingMode()
        
        # All tooltips should have glossary_terms key (even if empty)
        for element_id in tm._tooltips:
            tooltip = tm.get_tooltip(element_id)
            if "glossary_terms" in tooltip:
                assert isinstance(tooltip["glossary_terms"], list)
