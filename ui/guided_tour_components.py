"""
PoliSim Guided Tour UI Components

Streamlit components for rendering guided tours and educational overlays.
Properly integrates with Streamlit session_state for persistence.
"""

import streamlit as st
from typing import Optional, Dict, Any


def _get_teaching_mode_from_session():
    """Get or initialize teaching mode state from session."""
    # Import here to avoid circular imports
    from ui.teaching_mode import TeachingMode, DifficultyLevel
    
    # Initialize session state keys if not present
    if 'teaching_mode_state' not in st.session_state:
        st.session_state.teaching_mode_state = {
            'enabled': True,
            'level': 'beginner',
            'guided_tour_active': False,
            'current_tour_id': None,
            'current_step_index': 0,
            'completed_tours': [],
            'show_explanations': True,
            'show_why_it_matters': True,
        }
    
    # Create instance and restore state
    state = st.session_state.teaching_mode_state
    tm = TeachingMode(
        level=DifficultyLevel(state['level']),
        enabled=state['enabled']
    )
    tm.guided_tour_active = state['guided_tour_active']
    tm.current_step_index = state['current_step_index']
    tm.completed_tours = state['completed_tours'].copy()
    tm.show_explanations = state['show_explanations']
    tm.show_why_it_matters = state['show_why_it_matters']
    
    # Restore current tour if active
    if state['current_tour_id'] and state['current_tour_id'] in tm._tours:
        tm.current_tour = tm._tours[state['current_tour_id']]
    
    return tm


def _save_teaching_mode_to_session(tm):
    """Save teaching mode state back to session."""
    st.session_state.teaching_mode_state = {
        'enabled': tm.enabled,
        'level': tm.level.value,
        'guided_tour_active': tm.guided_tour_active,
        'current_tour_id': tm.current_tour.id if tm.current_tour else None,
        'current_step_index': tm.current_step_index,
        'completed_tours': tm.completed_tours.copy(),
        'show_explanations': tm.show_explanations,
        'show_why_it_matters': tm.show_why_it_matters,
    }


def render_teaching_mode_toggle():
    """Render the teaching mode toggle in sidebar with collapsible content."""
    from ui.teaching_mode import DifficultyLevel
    
    tm = _get_teaching_mode_from_session()
    
    with st.sidebar:
        st.markdown("---")
        
        # Main toggle with expander for settings
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("### 🎓 Learning Mode")
        
        # Enable/disable toggle
        enabled = st.toggle(
            "Enable Teaching Mode",
            value=tm.enabled,
            help="Enable enhanced explanations and guided tours",
            key="teaching_mode_main_toggle"
        )
        
        if enabled != tm.enabled:
            tm.enabled = enabled
            _save_teaching_mode_to_session(tm)
            st.rerun()
        
        # Only show details if enabled - use expander to collapse
        if tm.enabled:
            with st.expander("📖 Learning Settings", expanded=not tm.completed_tours):
                # Difficulty level selector
                level_options = {
                    "Beginner": "beginner",
                    "Intermediate": "intermediate", 
                    "Advanced": "advanced"
                }
                
                current_level = [k for k, v in level_options.items() 
                               if v == tm.level.value][0]
                
                selected = st.selectbox(
                    "Difficulty Level",
                    options=list(level_options.keys()),
                    index=list(level_options.keys()).index(current_level),
                    help="Adjusts the detail level of explanations",
                    key="teaching_mode_level_select"
                )
                
                if level_options[selected] != tm.level.value:
                    tm.set_level(DifficultyLevel(level_options[selected]))
                    _save_teaching_mode_to_session(tm)
                    st.rerun()
                
                # Show available tours
                st.markdown("**📖 Guided Tours**")
                
                tours = tm.get_available_tours()
                for tour in tours:
                    status = "✅" if tour["completed"] else "📚"
                    st.markdown(f"{status} **{tour['name']}**  \n*{tour['estimated_time']} min · {tour['step_count']} steps*")
                    
                    # Use unique key for each button
                    btn_key = f"tour_start_{tour['id']}"
                    if st.button(
                        "▶ Start" if not tour["completed"] else "↻ Restart", 
                        key=btn_key, 
                        disabled=tm.guided_tour_active,
                        use_container_width=True
                    ):
                        tm.start_tour(tour["id"])
                        _save_teaching_mode_to_session(tm)
                        st.rerun()
                
                # Progress summary
                st.markdown("---")
                progress = tm.get_learning_progress()
                st.markdown(f"**Progress:** {progress['tours_completed']}/{progress['tours_available']} tours")
                st.progress(progress['completion_percentage'] / 100)
                
                if progress['suggested_next']:
                    st.info(f"💡 Next: {progress['suggested_next']}")
                
                # Reset button INSIDE expander for better visibility
                st.markdown("---")
                if st.button("🔄 Reset Progress", key="reset_teaching_progress_in_expander", use_container_width=True, type="secondary"):
                    tm.completed_tours = []
                    tm.guided_tour_active = False
                    tm.current_tour = None
                    tm.current_step_index = 0
                    _save_teaching_mode_to_session(tm)
                    st.success("Progress reset!")
                    st.rerun()


def _navigate_to_page(page: str):
    """Navigate to a specific page in the dashboard."""
    if page and page != "---":
        st.session_state["nav_page"] = page


def render_tour_overlay():
    """Render the current tour step overlay if a tour is active."""
    tm = _get_teaching_mode_from_session()
    
    if not tm.guided_tour_active or tm.current_tour is None:
        return
    
    step = tm._get_current_step()
    if not step:
        return
    
    # Navigate to the target page for this step if specified
    target_page = step.get('target_page')
    current_page = st.session_state.get('nav_page', 'Overview')
    
    # Only navigate if we have a target and we're not already there
    if target_page and target_page != current_page and target_page != "---":
        _navigate_to_page(target_page)
        st.rerun()
    
    # Use Streamlit native components for the tour overlay
    # This ensures visibility regardless of theme
    tour_name = step.get('tour_name', 'Tour')
    step_num = step['step_number']
    total_steps = step['total_steps']
    title = step['title']
    content = step['content']
    
    # Create tour display in main area using native Streamlit components
    # Use a container with custom styling
    st.markdown("---")
    
    tour_container = st.container()
    with tour_container:
        # Header row
        hcol1, hcol2 = st.columns([3, 1])
        with hcol1:
            st.markdown(f"### 🎓 {tour_name}")
        with hcol2:
            st.markdown(f"**Step {step_num}/{total_steps}**")
        
        # Show current page indicator
        if target_page:
            st.caption(f"📍 Currently viewing: **{target_page}**")
        
        # Content box with info styling
        st.info(f"**{title}**\n\n{content}")
        
        # Navigation buttons
        nav_col1, nav_col2, nav_col3 = st.columns(3)
        
        with nav_col1:
            if step_num > 1:
                if st.button("← Back", key="tour_back_main", use_container_width=True):
                    tm.previous_step()
                    _save_teaching_mode_to_session(tm)
                    st.rerun()
        
        with nav_col2:
            if st.button("Skip Tour", key="tour_skip_main", use_container_width=True):
                tm.skip_tour()
                _save_teaching_mode_to_session(tm)
                st.rerun()
        
        with nav_col3:
            if step.get('is_last'):
                if st.button("✓ Finish", key="tour_finish_main", type="primary", use_container_width=True):
                    tm.next_step()
                    _save_teaching_mode_to_session(tm)
                    st.success("🎉 Tour completed!")
                    st.rerun()
            else:
                if st.button("Next →", key="tour_next_main", type="primary", use_container_width=True):
                    tm.next_step()
                    _save_teaching_mode_to_session(tm)
                    st.rerun()
    
    st.markdown("---")


def render_educational_callout(context: str):
    """
    Render an educational callout if appropriate for context.
    
    Args:
        context: The current UI context (e.g., "viewing_debt_chart")
    """
    if not should_show_callout(context):
        return
    
    callout = get_callout_content(context)
    if callout:
        st.info(f"**{callout['title']}**\n\n{callout['content']}")


def enhanced_metric(
    label: str,
    value: str,
    delta: Optional[str] = None,
    element_id: Optional[str] = None,
    **kwargs
):
    """
    Wrapper around st.metric with teaching mode support.
    
    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        element_id: ID for teaching mode tooltip lookup
        **kwargs: Additional arguments passed to st.metric
    """
    help_text = teaching_tooltip(element_id) if element_id else None
    st.metric(label, value, delta=delta, help=help_text, **kwargs)


def render_welcome_banner():
    """Render welcome banner for first-time users."""
    tm = _get_teaching_mode_from_session()
    
    if not tm.enabled:
        return
    
    # Check if user has completed any tours
    if not tm.completed_tours:
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 20px;
            color: white;
            margin-bottom: 20px;
        ">
            <h3 style="margin: 0 0 10px 0;">👋 Welcome to PoliSim!</h3>
            <p style="margin: 0 0 15px 0;">
                New here? Teaching Mode is enabled to help you learn. 
                Take a guided tour to get started!
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Dashboard Tour", key="welcome_start_tour", type="primary"):
            tm.start_tour("dashboard_intro")
            _save_teaching_mode_to_session(tm)
            st.rerun()


def render_concept_explainer(concept: str, expanded: bool = False):
    """
    Render an expandable concept explanation.
    
    Args:
        concept: The concept to explain (must be in tooltips)
        expanded: Whether to start expanded
    """
    tm = _get_teaching_mode_from_session()
    if not tm.enabled:
        return
    
    tooltip_data = tm.get_tooltip(concept)
    if not tooltip_data.get("content"):
        return
    
    with st.expander(f"📚 What is {concept.replace('_', ' ').title()}?", expanded=expanded):
        st.markdown(tooltip_data["content"])
        
        if tooltip_data.get("why_it_matters"):
            st.markdown(f"**💡 Why it matters:** {tooltip_data['why_it_matters']}")
        
        if tooltip_data.get("glossary_terms"):
            st.markdown("**Related terms:** " + ", ".join(tooltip_data["glossary_terms"]))
        
        if tooltip_data.get("learn_more"):
            st.markdown(f"[📖 Learn more]({tooltip_data['learn_more']})")


def render_learning_progress_card():
    """Render a card showing learning progress."""
    tm = _get_teaching_mode_from_session()
    if not tm.enabled:
        return
    
    progress = tm.get_learning_progress()
    
    st.markdown("""
    <div style="
        background: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    ">
    """, unsafe_allow_html=True)
    
    st.markdown("### 📊 Your Learning Progress")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tours Completed", f"{progress['tours_completed']}/{progress['tours_available']}")
    with col2:
        st.metric("Level", progress['current_level'].title())
    
    st.progress(progress['completion_percentage'] / 100)
    
    if progress['suggested_next']:
        st.markdown(f"**Next step:** {progress['suggested_next']}")
    
    st.markdown("</div>", unsafe_allow_html=True)


# ==================== Quick Actions ====================

def quick_tour_buttons():
    """Render quick-access tour buttons."""
    tm = _get_teaching_mode_from_session()
    if not tm.enabled or tm.guided_tour_active:
        return
    
    st.markdown("#### 🎯 Quick Start Tours")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🏠 Dashboard Intro", key="quick_tour_dashboard", use_container_width=True):
            tm.start_tour("dashboard_intro")
            _save_teaching_mode_to_session(tm)
            st.rerun()
    
    with col2:
        if st.button("▶️ First Simulation", key="quick_tour_sim", use_container_width=True):
            tm.start_tour("first_simulation")
            _save_teaching_mode_to_session(tm)
            st.rerun()
