"""
PoliSim Teaching Mode Module

Provides educational enhancements to the dashboard:
- Enhanced tooltips for beginners
- Guided tours through features
- Educational overlays and callouts
- Difficulty-level adaptive content
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
import json
from pathlib import Path


class DifficultyLevel(Enum):
    """Learning difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


@dataclass
class TooltipContent:
    """Enhanced tooltip with educational content."""
    short: str  # Brief description
    detailed: str  # Full explanation
    why_it_matters: str  # Real-world relevance
    learn_more_link: Optional[str] = None  # Link to documentation
    glossary_terms: List[str] = field(default_factory=list)  # Related glossary entries


@dataclass
class TourStep:
    """A single step in a guided tour."""
    element_id: str  # UI element to highlight
    title: str
    content: str
    position: str = "bottom"  # top, bottom, left, right
    action: Optional[str] = None  # Optional action to demonstrate
    wait_for: Optional[str] = None  # Wait for user action before proceeding
    target_page: Optional[str] = None  # Page to navigate to for this step


@dataclass
class GuidedTour:
    """A complete guided tour through a feature."""
    id: str
    name: str
    description: str
    steps: List[TourStep]
    estimated_time: int  # minutes
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER


class TeachingMode:
    """
    Enhanced UI mode for educational contexts.
    
    Provides context-aware educational content that adapts to
    the user's expertise level.
    """
    
    def __init__(
        self, 
        level: DifficultyLevel = DifficultyLevel.BEGINNER,
        enabled: bool = True
    ):
        self.level = level
        self.enabled = enabled
        self.show_explanations = True
        self.show_why_it_matters = True
        self.guided_tour_active = False
        self.current_tour: Optional[GuidedTour] = None
        self.current_step_index: int = 0
        self.completed_tours: List[str] = []
        
        # Load content
        self._tooltips: Dict[str, TooltipContent] = {}
        self._tours: Dict[str, GuidedTour] = {}
        self._load_default_content()
    
    def _load_default_content(self):
        """Load default educational content."""
        self._load_tooltips()
        self._load_tours()
    
    def _load_tooltips(self):
        """Load enhanced tooltips for all UI elements."""
        self._tooltips = {
            # Budget Components
            "revenue_total": TooltipContent(
                short="Total federal revenue collected",
                detailed="The sum of all taxes and fees collected by the federal government, "
                        "including individual income taxes, payroll taxes, corporate taxes, "
                        "excise taxes, and other sources.",
                why_it_matters="Revenue determines how much the government can spend without borrowing. "
                              "When revenue falls short of spending, deficits occur.",
                learn_more_link="/docs/GLOSSARY.md#revenue",
                glossary_terms=["revenue", "taxes", "fiscal year"]
            ),
            "spending_total": TooltipContent(
                short="Total federal spending (outlays)",
                detailed="All federal government expenditures, including mandatory programs "
                        "(Social Security, Medicare, Medicaid), discretionary spending "
                        "(defense, agencies), and interest on the national debt.",
                why_it_matters="Spending levels affect every American through services, benefits, "
                              "and the economy. Uncontrolled spending growth strains future budgets.",
                learn_more_link="/docs/GLOSSARY.md#spending",
                glossary_terms=["outlays", "mandatory", "discretionary"]
            ),
            "deficit": TooltipContent(
                short="Annual budget deficit (spending - revenue)",
                detailed="The difference between what the government spends and what it collects "
                        "in a single fiscal year. A deficit means the government must borrow.",
                why_it_matters="Deficits add to the national debt. Persistent large deficits can "
                              "lead to higher interest rates and crowding out of private investment.",
                learn_more_link="/docs/GLOSSARY.md#deficit",
                glossary_terms=["deficit", "surplus", "balanced budget"]
            ),
            "debt_total": TooltipContent(
                short="Total national debt (accumulated deficits)",
                detailed="The total amount the federal government owes to creditors, accumulated "
                        "over many years of deficits. Includes debt held by the public and "
                        "intragovernmental holdings (like Social Security trust funds).",
                why_it_matters="High debt levels mean more tax dollars go to interest payments "
                              "instead of services. It also limits fiscal flexibility in crises.",
                learn_more_link="/docs/GLOSSARY.md#debt",
                glossary_terms=["debt", "debt ceiling", "interest"]
            ),
            "debt_to_gdp": TooltipContent(
                short="Debt as a percentage of the economy",
                detailed="The ratio of national debt to Gross Domestic Product (GDP). This metric "
                        "normalizes debt by the size of the economy, making comparisons across "
                        "time and countries more meaningful.",
                why_it_matters="A debt-to-GDP ratio above 100% means the government owes more than "
                              "the entire economy produces in a year. Historical US average is ~40%.",
                learn_more_link="/docs/GLOSSARY.md#debt-to-gdp",
                glossary_terms=["GDP", "debt sustainability", "fiscal space"]
            ),
            
            # Healthcare Module
            "medicare_spending": TooltipContent(
                short="Federal health insurance for seniors (65+)",
                detailed="Medicare provides health coverage for ~65 million Americans aged 65+ "
                        "and younger people with disabilities. It has four parts: A (hospital), "
                        "B (outpatient), C (Medicare Advantage), and D (prescription drugs).",
                why_it_matters="Medicare is the second-largest federal program and growing rapidly "
                              "due to aging population. Reform options are politically contentious.",
                learn_more_link="/docs/GLOSSARY.md#medicare",
                glossary_terms=["Medicare", "Part A", "Part B", "Part D"]
            ),
            "medicaid_spending": TooltipContent(
                short="Health coverage for low-income Americans",
                detailed="Medicaid is a joint federal-state program providing health coverage to "
                        "~85 million low-income Americans, including children, pregnant women, "
                        "elderly, and disabled individuals. States administer with federal funding.",
                why_it_matters="Medicaid is the largest insurer in America and pays for most "
                              "nursing home care. ACA expansion significantly increased enrollment.",
                learn_more_link="/docs/GLOSSARY.md#medicaid",
                glossary_terms=["Medicaid", "FMAP", "expansion"]
            ),
            "healthcare_policy": TooltipContent(
                short="Healthcare system reform options",
                detailed="PoliSim models 8 healthcare policy scenarios from status quo to "
                        "single-payer systems. Each has different coverage levels, costs, "
                        "funding mechanisms, and transition challenges.",
                why_it_matters="Healthcare is ~18% of GDP and the largest driver of long-term "
                              "fiscal challenges. Policy choices affect millions of lives.",
                learn_more_link="/notebooks/03_healthcare_policy_analysis.ipynb",
                glossary_terms=["M4A", "public option", "single-payer"]
            ),
            
            # Social Security
            "social_security": TooltipContent(
                short="Retirement and disability benefits program",
                detailed="Social Security provides benefits to ~70 million Americans: retirees, "
                        "disabled workers, and survivors. Funded by 12.4% payroll tax split "
                        "between employers and employees, with a taxable maximum (~$168,600 in 2024).",
                why_it_matters="Social Security is the largest federal program and primary income "
                              "source for most retirees. Trust funds face depletion around 2034.",
                learn_more_link="/docs/GLOSSARY.md#social-security",
                glossary_terms=["OASI", "DI", "trust fund", "payroll tax"]
            ),
            "trust_fund_balance": TooltipContent(
                short="Social Security trust fund reserves",
                detailed="The OASI (retirement) and DI (disability) trust funds hold reserves "
                        "accumulated when payroll taxes exceeded benefits. These reserves are "
                        "invested in special Treasury securities.",
                why_it_matters="When trust funds are depleted, benefits must be cut to match "
                              "incoming revenue (~77% of scheduled benefits) unless reforms enacted.",
                learn_more_link="/notebooks/04_social_security_deep_dive.ipynb",
                glossary_terms=["trust fund", "depletion", "solvency"]
            ),
            
            # Monte Carlo
            "monte_carlo": TooltipContent(
                short="Probabilistic simulation method",
                detailed="Monte Carlo simulation runs thousands of scenarios with randomly varied "
                        "economic assumptions (GDP growth, inflation, interest rates). This produces "
                        "probability distributions instead of single-point estimates.",
                why_it_matters="Point estimates hide uncertainty. Monte Carlo reveals the range of "
                              "possible outcomes and helps identify tail risks.",
                learn_more_link="/notebooks/05_monte_carlo_uncertainty.ipynb",
                glossary_terms=["Monte Carlo", "probability distribution", "confidence interval"]
            ),
            "confidence_interval": TooltipContent(
                short="Range containing likely outcomes",
                detailed="A 90% confidence interval means 90% of Monte Carlo simulations produced "
                        "results within this range. The remaining 10% were more extreme (5% above, "
                        "5% below).",
                why_it_matters="Confidence intervals communicate uncertainty honestly. Policy decisions "
                              "should account for the full range, not just the central estimate.",
                learn_more_link="/docs/GLOSSARY.md#confidence-interval",
                glossary_terms=["confidence interval", "percentile", "uncertainty"]
            ),
            
            # Simulation Controls
            "simulation_years": TooltipContent(
                short="Projection time horizon",
                detailed="How many years into the future to project. Longer horizons show long-term "
                        "trends but have greater uncertainty. CBO typically uses 10-year and 30-year windows.",
                why_it_matters="Short-term projections (1-5 years) are more reliable. Long-term "
                              "(30+ years) reveal structural issues but should be interpreted cautiously.",
                glossary_terms=["projection", "baseline", "extrapolation"]
            ),
            "iteration_count": TooltipContent(
                short="Number of Monte Carlo simulations",
                detailed="More iterations = more stable probability estimates, but longer runtime. "
                        "1,000 iterations is minimum for rough estimates; 10,000+ for publication-quality.",
                why_it_matters="Too few iterations produce unstable results. Law of large numbers "
                              "ensures convergence with sufficient runs.",
                glossary_terms=["iterations", "convergence", "sampling"]
            ),
            
            # Policy Comparison
            "policy_selector": TooltipContent(
                short="Choose policies to simulate",
                detailed="Select from predefined policy scenarios or create custom configurations. "
                        "Each policy has different revenue, spending, and programmatic assumptions.",
                why_it_matters="Comparing policies side-by-side reveals trade-offs that aren't "
                              "obvious from examining each in isolation.",
                learn_more_link="/notebooks/09_custom_policy_design.ipynb",
                glossary_terms=["policy", "scenario", "baseline"]
            ),
        }
    
    def _load_tours(self):
        """Load guided tours for major features."""
        self._tours = {
            "dashboard_intro": GuidedTour(
                id="dashboard_intro",
                name="Dashboard Introduction",
                description="Learn the basics of the PoliSim dashboard",
                estimated_time=5,
                difficulty=DifficultyLevel.BEGINNER,
                steps=[
                    TourStep(
                        element_id="header",
                        title="Welcome to PoliSim! 👋",
                        content="This dashboard lets you simulate federal fiscal policy. "
                               "Let's take a quick tour of the key features. We'll start on the Overview page.",
                        position="bottom",
                        target_page="Overview"
                    ),
                    TourStep(
                        element_id="healthcare_tab",
                        title="Healthcare Analysis",
                        content="The Healthcare page lets you explore different healthcare policy scenarios, "
                               "from the current system to Medicare-for-All. You can see coverage levels, "
                               "costs, and fiscal impacts.",
                        position="right",
                        target_page="Healthcare"
                    ),
                    TourStep(
                        element_id="social_security_tab",
                        title="Social Security",
                        content="The Social Security page shows trust fund projections and lets you test "
                               "reform options like raising the retirement age or adjusting the payroll tax cap.",
                        position="right",
                        target_page="Social Security"
                    ),
                    TourStep(
                        element_id="policy_comparison",
                        title="Policy Comparison",
                        content="The Policy Comparison page lets you compare multiple scenarios side-by-side. "
                               "See how different policies affect deficits, debt, and program outcomes.",
                        position="right",
                        target_page="Policy Comparison"
                    ),
                    TourStep(
                        element_id="combined_outlook",
                        title="Combined Fiscal Outlook",
                        content="The Combined Outlook shows the big picture - total revenues, spending, "
                               "deficits, and debt projections. This is where everything comes together.",
                        position="right",
                        target_page="Combined Outlook"
                    ),
                    TourStep(
                        element_id="teaching_toggle",
                        title="Teaching Mode (You're Using It!)",
                        content="Teaching mode provides extra explanations like this tour. "
                               "You can toggle it off in the sidebar when you're comfortable. "
                               "Check out Settings for more options!",
                        position="left",
                        target_page="⚙️ Settings"
                    ),
                ]
            ),
            "first_simulation": GuidedTour(
                id="first_simulation",
                name="Your First Simulation",
                description="Run a baseline simulation step-by-step",
                estimated_time=3,
                difficulty=DifficultyLevel.BEGINNER,
                steps=[
                    TourStep(
                        element_id="overview_page",
                        title="Step 1: Start at Overview",
                        content="The Overview page shows a summary of current fiscal conditions. "
                               "From here you can see key metrics and select policies to simulate.",
                        position="bottom",
                        target_page="Overview"
                    ),
                    TourStep(
                        element_id="scenario_explorer",
                        title="Step 2: Explore Scenarios",
                        content="The Scenario Explorer lets you adjust economic assumptions and see "
                               "how they affect outcomes. Try changing GDP growth or inflation rates.",
                        position="right",
                        target_page="Scenario Explorer"
                    ),
                    TourStep(
                        element_id="advanced_scenarios",
                        title="Step 3: Monte Carlo Analysis",
                        content="Advanced Scenarios runs thousands of simulations to show you the "
                               "range of possible outcomes. The shaded areas show uncertainty bands.",
                        position="top",
                        target_page="Advanced Scenarios"
                    ),
                    TourStep(
                        element_id="report_generation",
                        title="Step 4: Generate Reports",
                        content="Once you've run simulations, you can generate professional reports "
                               "with charts and analysis. Great for sharing your findings!",
                        position="top",
                        target_page="Report Generation"
                    ),
                ]
            ),
            "healthcare_comparison": GuidedTour(
                id="healthcare_comparison",
                name="Healthcare Policy Comparison",
                description="Compare different healthcare reform scenarios",
                estimated_time=7,
                difficulty=DifficultyLevel.INTERMEDIATE,
                steps=[
                    TourStep(
                        element_id="healthcare_tab",
                        title="Healthcare Module",
                        content="PoliSim includes 8 different healthcare policy models. "
                               "Let's start by exploring the Healthcare page.",
                        position="bottom",
                        target_page="Healthcare"
                    ),
                    TourStep(
                        element_id="medicare_medicaid",
                        title="Medicare & Medicaid Details",
                        content="This page shows detailed projections for Medicare and Medicaid. "
                               "You can see enrollment, costs, and trust fund status.",
                        position="right",
                        target_page="Medicare/Medicaid"
                    ),
                    TourStep(
                        element_id="comparison_view",
                        title="Side-by-Side Comparison",
                        content="The Policy Comparison page lets you compare multiple scenarios. "
                               "Notice how costs and coverage levels differ between policies.",
                        position="top",
                        target_page="Policy Comparison"
                    ),
                    TourStep(
                        element_id="recommendations",
                        title="Policy Recommendations",
                        content="Based on your simulations, PoliSim can suggest policy options "
                               "that meet your goals for coverage, cost, and fiscal sustainability.",
                        position="left",
                        target_page="Recommendations"
                    ),
                ]
            ),
            "monte_carlo_deep_dive": GuidedTour(
                id="monte_carlo_deep_dive",
                name="Understanding Monte Carlo Results",
                description="Learn to interpret probabilistic projections",
                estimated_time=10,
                difficulty=DifficultyLevel.INTERMEDIATE,
                steps=[
                    TourStep(
                        element_id="scenario_explorer",
                        title="Scenario Explorer",
                        content="Start by exploring different economic scenarios. You can adjust "
                               "GDP growth, inflation, and other key variables.",
                        position="right",
                        target_page="Scenario Explorer"
                    ),
                    TourStep(
                        element_id="advanced_scenarios",
                        title="Monte Carlo Settings",
                        content="PoliSim uses Monte Carlo simulation to quantify uncertainty. "
                               "Economic variables like GDP growth and inflation are randomized "
                               "thousands of times to show the range of possible outcomes.",
                        position="right",
                        target_page="Advanced Scenarios"
                    ),
                    TourStep(
                        element_id="impact_calculator",
                        title="Impact Calculator",
                        content="The Impact Calculator shows how policy changes affect specific metrics. "
                               "Try adjusting tax rates or spending levels to see the effects.",
                        position="top",
                        target_page="Impact Calculator"
                    ),
                    TourStep(
                        element_id="combined_outlook",
                        title="Combined Fiscal Outlook",
                        content="The Combined Outlook brings everything together. The shaded areas "
                               "show uncertainty bands from Monte Carlo simulation.",
                        position="left",
                        target_page="Combined Outlook"
                    ),
                    TourStep(
                        element_id="real_data",
                        title="Real CBO Data",
                        content="The Real Data Dashboard shows actual CBO projections for comparison. "
                               "Use this to validate PoliSim's baseline against official estimates.",
                        position="right",
                        target_page="Real Data Dashboard"
                    ),
                ]
            ),
        }
    
    # ==================== Public API ====================
    
    def set_level(self, level: DifficultyLevel):
        """Change the difficulty level."""
        self.level = level
        self._adjust_for_level()
    
    def _adjust_for_level(self):
        """Adjust settings based on difficulty level."""
        if self.level == DifficultyLevel.BEGINNER:
            self.show_explanations = True
            self.show_why_it_matters = True
        elif self.level == DifficultyLevel.INTERMEDIATE:
            self.show_explanations = True
            self.show_why_it_matters = False
        else:  # ADVANCED
            self.show_explanations = False
            self.show_why_it_matters = False
    
    def get_tooltip(self, element_id: str) -> Dict[str, Any]:
        """
        Get tooltip content appropriate for current level.
        
        Returns:
            Dictionary with tooltip content, adapted for difficulty level.
        """
        if not self.enabled or element_id not in self._tooltips:
            return {"content": ""}
        
        tooltip = self._tooltips[element_id]
        
        if self.level == DifficultyLevel.ADVANCED:
            return {
                "content": tooltip.short,
                "glossary_terms": tooltip.glossary_terms
            }
        elif self.level == DifficultyLevel.INTERMEDIATE:
            return {
                "content": tooltip.detailed,
                "learn_more": tooltip.learn_more_link,
                "glossary_terms": tooltip.glossary_terms
            }
        else:  # BEGINNER
            return {
                "content": tooltip.detailed,
                "why_it_matters": tooltip.why_it_matters,
                "learn_more": tooltip.learn_more_link,
                "glossary_terms": tooltip.glossary_terms
            }
    
    def get_all_tooltips(self) -> Dict[str, Dict[str, Any]]:
        """Get all tooltips for bulk loading."""
        return {
            element_id: self.get_tooltip(element_id)
            for element_id in self._tooltips
        }
    
    # ==================== Guided Tours ====================
    
    def get_available_tours(self) -> List[Dict[str, Any]]:
        """Get list of available tours with completion status."""
        tours = []
        for tour_id, tour in self._tours.items():
            # Filter by difficulty
            if self._tour_appropriate_for_level(tour):
                tours.append({
                    "id": tour.id,
                    "name": tour.name,
                    "description": tour.description,
                    "estimated_time": tour.estimated_time,
                    "difficulty": tour.difficulty.value,
                    "completed": tour_id in self.completed_tours,
                    "step_count": len(tour.steps)
                })
        return tours
    
    def _tour_appropriate_for_level(self, tour: GuidedTour) -> bool:
        """Check if tour is appropriate for current level."""
        level_order = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]
        user_level_idx = level_order.index(self.level)
        tour_level_idx = level_order.index(tour.difficulty)
        return tour_level_idx <= user_level_idx
    
    def start_tour(self, tour_id: str) -> Optional[Dict[str, Any]]:
        """
        Start a guided tour.
        
        Returns:
            First step of the tour, or None if tour not found.
        """
        if tour_id not in self._tours:
            return None
        
        self.current_tour = self._tours[tour_id]
        self.current_step_index = 0
        self.guided_tour_active = True
        
        return self._get_current_step()
    
    def next_step(self) -> Optional[Dict[str, Any]]:
        """
        Advance to next tour step.
        
        Returns:
            Next step, or None if tour complete.
        """
        if not self.guided_tour_active or self.current_tour is None:
            return None
        
        self.current_step_index += 1
        
        if self.current_step_index >= len(self.current_tour.steps):
            self._complete_tour()
            return None
        
        return self._get_current_step()
    
    def previous_step(self) -> Optional[Dict[str, Any]]:
        """Go back one step."""
        if not self.guided_tour_active or self.current_tour is None:
            return None
        
        if self.current_step_index > 0:
            self.current_step_index -= 1
        
        return self._get_current_step()
    
    def skip_tour(self):
        """Skip/cancel the current tour."""
        self.guided_tour_active = False
        self.current_tour = None
        self.current_step_index = 0
    
    def _get_current_step(self) -> Dict[str, Any]:
        """Get current step as dictionary."""
        if self.current_tour is None:
            return {}
        
        step = self.current_tour.steps[self.current_step_index]
        return {
            "tour_id": self.current_tour.id,
            "tour_name": self.current_tour.name,
            "step_number": self.current_step_index + 1,
            "total_steps": len(self.current_tour.steps),
            "element_id": step.element_id,
            "title": step.title,
            "content": step.content,
            "position": step.position,
            "action": step.action,
            "wait_for": step.wait_for,
            "target_page": step.target_page,
            "is_last": self.current_step_index == len(self.current_tour.steps) - 1
        }
    
    def _complete_tour(self):
        """Mark current tour as complete."""
        if self.current_tour:
            self.completed_tours.append(self.current_tour.id)
        self.guided_tour_active = False
        self.current_tour = None
        self.current_step_index = 0
    
    # ==================== Educational Callouts ====================
    
    def get_callout(self, context: str) -> Optional[Dict[str, str]]:
        """
        Get an educational callout for the current context.
        
        Args:
            context: The current UI context (e.g., "viewing_debt_chart")
            
        Returns:
            Callout with title and content, or None.
        """
        if not self.enabled or self.level == DifficultyLevel.ADVANCED:
            return None
        
        callouts = {
            "viewing_debt_chart": {
                "title": "📊 Understanding This Chart",
                "content": "The shaded area shows the range of likely outcomes (90% confidence). "
                          "The center line is the median projection."
            },
            "high_debt_warning": {
                "title": "⚠️ Debt-to-GDP Above 100%",
                "content": "When debt exceeds GDP, it doesn't mean bankruptcy—but it does mean "
                          "higher interest costs and reduced fiscal flexibility."
            },
            "trust_fund_depletion": {
                "title": "📉 Trust Fund Projected to Deplete",
                "content": "Depletion doesn't mean Social Security ends—it means benefits would "
                          "be automatically cut to match incoming payroll tax revenue (~77%)."
            },
            "monte_carlo_running": {
                "title": "🎲 Monte Carlo in Progress",
                "content": "PoliSim is running thousands of simulations with different economic "
                          "assumptions to show you the range of possible outcomes."
            },
            "policy_comparison": {
                "title": "⚖️ Comparing Policies",
                "content": "Remember: no policy is 'right' or 'wrong'. Each represents different "
                          "values and priorities. Focus on trade-offs, not winners."
            },
        }
        
        return callouts.get(context)
    
    # ==================== Progress Tracking ====================
    
    def get_learning_progress(self) -> Dict[str, Any]:
        """Get user's learning progress summary."""
        total_tours = len([t for t in self._tours.values() 
                          if self._tour_appropriate_for_level(t)])
        completed = len(self.completed_tours)
        
        return {
            "tours_completed": completed,
            "tours_available": total_tours,
            "completion_percentage": (completed / total_tours * 100) if total_tours > 0 else 0,
            "current_level": self.level.value,
            "suggested_next": self._suggest_next_activity()
        }
    
    def _suggest_next_activity(self) -> str:
        """Suggest next learning activity."""
        if "dashboard_intro" not in self.completed_tours:
            return "Take the Dashboard Introduction tour"
        elif "first_simulation" not in self.completed_tours:
            return "Complete the First Simulation tour"
        elif self.level == DifficultyLevel.BEGINNER:
            return "Try the Healthcare Comparison tour"
        elif "monte_carlo_deep_dive" not in self.completed_tours:
            return "Learn about Monte Carlo with the deep dive tour"
        else:
            return "Explore the Jupyter notebooks for deeper learning"
    
    # ==================== Serialization ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize teaching mode state."""
        return {
            "enabled": self.enabled,
            "level": self.level.value,
            "show_explanations": self.show_explanations,
            "show_why_it_matters": self.show_why_it_matters,
            "completed_tours": self.completed_tours,
            "guided_tour_active": self.guided_tour_active,
            "current_tour_id": self.current_tour.id if self.current_tour else None,
            "current_step_index": self.current_step_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TeachingMode":
        """Deserialize teaching mode state."""
        level = DifficultyLevel(data.get("level", "beginner"))
        instance = cls(level=level, enabled=data.get("enabled", True))
        instance.show_explanations = data.get("show_explanations", True)
        instance.show_why_it_matters = data.get("show_why_it_matters", True)
        instance.completed_tours = data.get("completed_tours", [])
        
        # Restore active tour if any
        if data.get("guided_tour_active") and data.get("current_tour_id"):
            instance.start_tour(data["current_tour_id"])
            instance.current_step_index = data.get("current_step_index", 0)
        
        return instance


# ==================== Singleton Instance ====================

_teaching_mode_instance: Optional[TeachingMode] = None


def get_teaching_mode() -> TeachingMode:
    """
    Get the global TeachingMode instance.
    
    NOTE: This creates a fresh instance and does NOT persist state.
    For Streamlit apps, use ui.guided_tour_components._get_teaching_mode_from_session() instead.
    """
    global _teaching_mode_instance
    if _teaching_mode_instance is None:
        _teaching_mode_instance = TeachingMode()
    return _teaching_mode_instance


def configure_teaching_mode(
    enabled: bool = True,
    level: str = "beginner"
) -> TeachingMode:
    """
    Configure and return the teaching mode instance.
    
    NOTE: This function is deprecated for Streamlit use. State should be 
    managed via session_state using ui.guided_tour_components helpers.
    """
    global _teaching_mode_instance
    _teaching_mode_instance = TeachingMode(
        enabled=enabled,
        level=DifficultyLevel(level)
    )
    return _teaching_mode_instance


def _get_tm_from_session_or_global() -> TeachingMode:
    """
    Helper to get TeachingMode from session state if available, else global.
    This allows the helper functions to work in both Streamlit and non-Streamlit contexts.
    """
    try:
        import streamlit as st
        if 'teaching_mode_state' in st.session_state:
            # Import and use the session-based helper
            from ui.guided_tour_components import _get_teaching_mode_from_session
            return _get_teaching_mode_from_session()
    except Exception:
        pass
    # Fall back to global instance for non-Streamlit use
    return get_teaching_mode()


# ==================== Dashboard Integration Helpers ====================

def teaching_tooltip(element_id: str) -> str:
    """
    Get HTML-formatted tooltip for a UI element.
    
    Usage in Streamlit/Dash:
        st.metric("Debt", value, help=teaching_tooltip("debt_total"))
    """
    tm = _get_tm_from_session_or_global()
    if not tm.enabled:
        return ""
    
    tooltip_data = tm.get_tooltip(element_id)
    if not tooltip_data.get("content"):
        return ""
    
    parts = [tooltip_data["content"]]
    
    if tooltip_data.get("why_it_matters"):
        parts.append(f"\n\n💡 **Why it matters:** {tooltip_data['why_it_matters']}")
    
    if tooltip_data.get("learn_more"):
        parts.append(f"\n\n📚 [Learn more]({tooltip_data['learn_more']})")
    
    return "".join(parts)


def should_show_callout(context: str) -> bool:
    """Check if a callout should be shown for context."""
    tm = _get_tm_from_session_or_global()
    return tm.enabled and tm.get_callout(context) is not None


def get_callout_content(context: str) -> Optional[Dict[str, str]]:
    """Get callout content for rendering."""
    return _get_tm_from_session_or_global().get_callout(context)
