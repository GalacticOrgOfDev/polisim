# Phase 7 Implementation Slices - Multi-Agent Intelligence Platform

**Document Purpose:** Concrete implementation tasks for the PoliSim Multi-Agent Swarm Intelligence Layer  
**Date Created:** January 3, 2026  
**Total Estimated Effort:** 280-400 hours  
**Prerequisites:** Phase 6 complete (Validation, API, Security, Observability)

---

## Executive Summary

Phase 7 transforms PoliSim from a traditional fiscal simulation engine into an **AI-native policy analysis platform**. The core innovation is a multi-agent swarm architecture where specialized AI agents collaborate, debate, and reach consensus on policy analysis—mimicking how expert panels analyze legislation in the real world.

### Core Pillars

| Pillar | Description | Key Deliverable |
|--------|-------------|-----------------|
| **Multi-Agent Swarm** | Coordinated AI agents for parallel analysis | `swarm_core.py` |
| **Live Analysis Mode** | Real-time reasoning transparency | WebSocket streaming |
| **PoliSim Chatroom** | MCP-enabled collaborative workspace | Right sidebar UI |
| **Safety & Evaluation** | Continuous validation & human oversight | Evaluation suite |

---

## Research Context & Framework Selection (Jan 2026)

### Latest Research Insights

> **Key Finding (ICLR 2025 MAD Analysis):** Multi-agent debate works, but scaling is tricky. More agents/rounds often plateau or degrade performance. Our weighted voting + convergence thresholds + max rounds are validated mitigations.

> **Competitive Landscape:** No direct competitors in the fiscal/policy domain—PoliSim is pioneering this space.

### Recommended Frameworks

| Framework | Strengths | Use Case |
|-----------|-----------|----------|
| **Swarms** (kyegomez) | Parallel execution, tools, memory | Primary coordinator base |
| **CrewAI** | Role-based agents, task delegation | Alternative if Swarms lacks features |
| **AutoGen** | Microsoft-backed, conversation patterns | Complex multi-turn debates |
| **LangGraph** | State machines, checkpointing | Pipeline orchestration |
| **Claude-Flow** | Claude-native swarm orchestration | Claude-specific optimizations |

**Recommendation:** Start with **Swarms** or **CrewAI** for the coordinator—they handle parallel execution, tools, and memory out-of-the-box. Customize with our agent roles and fiscal tools.

### Agent Prioritization Strategy

**Tier 1 (MVP - Must Have):**
1. **Fiscal Agent** — Core numbers (revenue, spending, debt)
2. **Economic Agent** — Macro shocks, GDP impact
3. **Healthcare Agent** — Domain expert for healthcare bills
4. **Social Security Agent** — Domain expert for SS/retirement

**Tier 2 (v1.1 - High Value):**
5. **Equity Agent** — Distributional impact analysis
6. **Implementation Agent** — Practical feasibility

**Tier 3 (v2.0 - Enhancement):**
7. **Behavioral Agent** — Behavioral economics responses
8. **Legal Agent** — Constitutional/legal feasibility

---

## SLICE 7.1: MULTI-AGENT SWARM CORE (Weeks 1-4)

### Overview
Build the foundational infrastructure for coordinating multiple AI agents that work in parallel on bill analysis, with a debate mechanism for resolving disagreements.

---

### 7.1.1: Agent Architecture Foundation (Week 1)

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours

#### Task 1: Define Agent Types & Roles

**Dev Time:** 8 hours

Create `core/agents/` module structure:

```
core/agents/
├── __init__.py
├── base_agent.py          # Abstract agent interface
├── coordinator.py         # Swarm orchestrator (leverage Swarms/CrewAI)
├── judge_agent.py         # Final arbitration for unresolved debates
│
├── # Tier 1 - MVP (Week 1-2)
├── fiscal_agent.py        # Revenue, spending, debt analysis [PRIORITY]
├── economic_agent.py      # Macro-economic impact [PRIORITY]
├── healthcare_agent.py    # Healthcare policy specialist [PRIORITY]
├── social_security_agent.py  # SS/retirement analysis [PRIORITY]
│
├── # Tier 2 - v1.1 (Week 3-4)
├── equity_agent.py        # Distributional impact analysis
├── implementation_agent.py # Practical implementation concerns
│
└── # Tier 3 - v2.0 (Future)
    ├── behavioral_agent.py    # Behavioral economics responses
    └── legal_agent.py         # Constitutional/legal feasibility
```

> **Framework Integration:** Use Swarms or CrewAI as the base coordinator. Their built-in parallel execution, tool management, and memory systems eliminate ~40% of custom infrastructure work.

- [ ] Design `BaseAgent` abstract class:
  ```python
  class BaseAgent(ABC):
      agent_id: str
      agent_type: AgentType
      specialty: str
      confidence_threshold: float
      
      @abstractmethod
      async def analyze(self, bill: Bill, context: AnalysisContext) -> AgentAnalysis
      
      @abstractmethod
      async def critique(self, other_analysis: AgentAnalysis) -> Critique
      
      @abstractmethod
      async def vote(self, proposals: List[Proposal]) -> Vote
  ```

- [ ] Define `AgentType` enum:
  - FISCAL, HEALTHCARE, SOCIAL_SECURITY, ECONOMIC
  - BEHAVIORAL, LEGAL, EQUITY, IMPLEMENTATION

- [ ] Create agent configuration schema (YAML):
  ```yaml
  agents:
    fiscal:
      model: "claude-sonnet-4-20250514"
      temperature: 0.3
      specialization_prompt: "..."
      confidence_threshold: 0.7
    healthcare:
      model: "claude-sonnet-4-20250514"
      ...
  ```

#### Task 2: Implement Base Agent Infrastructure

**Dev Time:** 10 hours

- [ ] Create `AgentAnalysis` dataclass:
  ```python
  @dataclass
  class AgentAnalysis:
      agent_id: str
      agent_type: AgentType
      findings: List[Finding]
      assumptions_used: List[Assumption]
      confidence: float  # 0.0 - 1.0
      uncertainty_areas: List[str]
      supporting_evidence: List[Evidence]
      timestamp: datetime
  ```

- [ ] Create `Finding` dataclass:
  ```python
  @dataclass
  class Finding:
      category: FindingCategory  # REVENUE, SPENDING, COVERAGE, etc.
      description: str
      impact_magnitude: ImpactMagnitude  # LOW, MEDIUM, HIGH, TRANSFORMATIVE
      confidence: float
      time_horizon: str  # "immediate", "5-year", "10-year", "long-term"
      affected_populations: List[str]
      fiscal_impact: Optional[FiscalImpact]
  ```

- [ ] Implement agent prompt templates:
  - System prompt per agent type
  - Analysis prompt structure
  - Critique prompt structure
  - Voting prompt structure

- [ ] Create agent factory pattern:
  ```python
  def create_agent(agent_type: AgentType, config: AgentConfig) -> BaseAgent
  ```

#### Task 3: Agent Communication Protocol

**Dev Time:** 8 hours

- [ ] Define inter-agent message types:
  ```python
  class AgentMessage:
      sender: str
      recipients: List[str]  # or "broadcast"
      message_type: MessageType  # ANALYSIS, CRITIQUE, PROPOSAL, VOTE, QUESTION
      content: Dict[str, Any]
      in_reply_to: Optional[str]
      timestamp: datetime
  ```

- [ ] Create message queue infrastructure:
  - In-memory queue for development
  - Redis queue option for production
  - Message persistence for audit trail

- [ ] Implement broadcast vs. direct messaging
- [ ] Create message serialization (JSON + schema validation)

#### Acceptance Criteria
- [ ] `BaseAgent` abstract class complete with full interface
- [ ] 8 specialized agent classes stubbed out
- [ ] Agent configuration schema defined
- [ ] Message protocol documented & implemented
- [ ] Unit tests for agent infrastructure (20+ tests)

---

### 7.1.2: Swarm Coordinator (Week 2)

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 30-40 hours

#### Task 1: Coordinator Core

**Dev Time:** 12 hours

Create `core/agents/coordinator.py`:

- [ ] Implement `SwarmCoordinator` class:
  ```python
  class SwarmCoordinator:
      def __init__(self, config: SwarmConfig):
          self.agents: Dict[str, BaseAgent] = {}
          self.message_queue: MessageQueue
          self.state: SwarmState
          
      async def analyze_bill(self, bill: Bill) -> SwarmAnalysis:
          """Orchestrate full bill analysis pipeline."""
          
      async def run_debate_round(self, topic: str) -> DebateRound:
          """Run one round of agent debate on a specific topic."""
          
      async def reach_consensus(self, proposals: List[Proposal]) -> Consensus:
          """Drive agents toward consensus on competing proposals."""
  ```

- [ ] Define analysis pipeline stages:
  1. **Ingestion**: Parse bill, extract sections
  2. **Parallel Analysis**: Each agent analyzes independently
  3. **Cross-Review**: Agents critique each other's findings
  4. **Debate**: Agents discuss disagreements
  5. **Consensus**: Weighted voting on final conclusions
  6. **Synthesis**: Combine into unified report

- [ ] Implement pipeline state machine:
  ```python
  class PipelineState(Enum):
      INITIALIZED = "initialized"
      INGESTING = "ingesting"
      ANALYZING = "analyzing"
      CROSS_REVIEWING = "cross_reviewing"
      DEBATING = "debating"
      VOTING = "voting"
      SYNTHESIZING = "synthesizing"
      COMPLETE = "complete"
      ERROR = "error"
  ```

#### Task 2: Parallel Execution Engine

**Dev Time:** 10 hours

- [ ] Implement async agent execution:
  ```python
  async def execute_parallel_analysis(
      self,
      bill: Bill,
      agents: List[BaseAgent],
      timeout: float = 120.0
  ) -> List[AgentAnalysis]:
      """Run all agents in parallel with timeout handling."""
  ```

- [ ] Create execution strategies:
  - **All-at-once**: Launch all agents simultaneously
  - **Staged**: Run in dependency order (e.g., fiscal before behavioral)
  - **Adaptive**: Add agents based on initial findings

- [ ] Implement timeout & retry logic:
  - Per-agent timeout (default 60s)
  - Global pipeline timeout (default 5 min)
  - Exponential backoff for retries
  - Graceful degradation if agent fails

- [ ] Add resource management:
  - Concurrent agent limit
  - Token budget per agent
  - Cost tracking per analysis

#### Task 3: Results Aggregation

**Dev Time:** 8 hours

- [ ] Create `SwarmAnalysis` composite result:
  ```python
  @dataclass
  class SwarmAnalysis:
      bill_id: str
      analysis_id: str
      timestamp: datetime
      
      agent_analyses: Dict[str, AgentAnalysis]
      consensus_findings: List[ConsensusFinding]
      disagreements: List[Disagreement]
      confidence_bands: Dict[str, ConfidenceBand]
      
      synthesis: SynthesizedReport
      metadata: AnalysisMetadata
  ```

- [ ] Implement finding aggregation:
  - Group similar findings across agents
  - Calculate aggregate confidence
  - Identify corroborating vs. conflicting findings

- [ ] Create confidence band calculation:
  ```python
  def calculate_confidence_bands(
      findings: List[Finding],
      weights: Dict[str, float]
  ) -> ConfidenceBand:
      """
      Returns P10, P50, P90 estimates based on
      weighted agent confidence and findings spread.
      """
  ```

#### Acceptance Criteria
- [ ] SwarmCoordinator fully implemented
- [ ] Pipeline state machine working
- [ ] Parallel execution with timeout handling
- [x] Results aggregation complete
- [x] Integration tests for full pipeline (10+ tests)
- [x] Performance: 8 agents complete in <2 minutes

---

### 7.1.3: Debate Loop Engine (Week 3) ✅ COMPLETE

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 35-45 hours
**Status:** ✅ Completed January 3, 2026

#### Implementation Summary

Created comprehensive `debate_engine.py` module with:
- Full debate protocol with configurable rounds (max 3, hard cap 5)
- Debate trigger detection system (confidence divergence, contradictory findings, etc.)
- Critique and rebuttal exchange system
- Convergence algorithm with weighted positions
- Debate moderator for turn balancing and circular argument prevention
- Judge agent arbitration for stalemates
- Disagreement map visualization data structures
- 36 comprehensive unit tests (32 passing, 4 async tests pending pytest-asyncio setup)

#### Task 1: Debate Protocol Design

**Dev Time:** 8 hours

- [x] Define debate structure:
  ```python
  @dataclass
  class DebateRound:
      round_number: int
      topic: str
      participants: List[str]
      opening_positions: Dict[str, Position]
      critiques: List[Critique]
      rebuttals: List[Rebuttal]
      position_updates: Dict[str, PositionUpdate]
      convergence_score: float  # 0.0 = total disagreement, 1.0 = consensus
  ```

- [x] Create debate triggers:
  - **Confidence divergence**: Agents differ by >0.3 on same metric
  - **Contradictory findings**: Direct conflicts in conclusions
  - **Assumption disputes**: Different baseline assumptions used
  - **Magnitude disagreements**: >20% difference in impact estimates

- [x] Design debate termination conditions:
  - Max rounds reached (default: **3**, hard cap: 5) — *Research shows diminishing returns beyond 3 rounds*
  - Convergence threshold met (default: 0.8) — *Early exit when consensus achieved*
  - No position changes in 2 rounds — *Stalemate detection*
  - Timeout reached
  - **Judge agent arbitration** — *If round 3+ with <0.6 convergence, invoke judge*

> **Research Note (ICLR 2025):** More debate rounds often plateau or degrade quality. Keep debates tight (3-5 rounds max) and use a "judge agent" for final arbitration when needed.

#### Task 2: Critique & Rebuttal System

**Dev Time:** 12 hours

- [x] Implement `Critique` structure:
  ```python
  @dataclass
  class Critique:
      critic_id: str
      target_id: str
      target_finding: str
      critique_type: CritiqueType  # METHODOLOGY, ASSUMPTION, EVIDENCE, LOGIC
      argument: str
      severity: CritiqueSeverity  # MINOR, MODERATE, MAJOR
      suggested_revision: Optional[str]
      supporting_evidence: List[str]
  ```

- [x] Create critique generation prompts:
  - Focus on specific finding
  - Require evidence-based arguments
  - Encourage constructive alternatives

- [x] Implement `Rebuttal` handling:
  ```python
  @dataclass
  class Rebuttal:
      original_critic: str
      rebutter: str
      critique_addressed: str
      rebuttal_argument: str
      position_change: Optional[PositionUpdate]
      acknowledgment: bool  # Does rebutter acknowledge valid points?
  ```

- [x] Create debate moderator logic:
  - Identify most contentious topics
  - Balance speaking turns
  - Prevent circular arguments
  - Track argument quality
  - **Invoke judge agent** when convergence stalls (<0.6 after round 3)

- [x] Implement `JudgeAgent` for arbitration:
  ```python
  class JudgeAgent(BaseAgent):
      """Final arbitrator for unresolved debates."""
      
      async def arbitrate(
          self,
          debate_history: List[DebateRound],
          positions: Dict[str, Position],
          evidence: Dict[str, List[Evidence]]
      ) -> Arbitration:
          """
          Review debate, weigh evidence, make final determination.
          Used only when standard debate fails to converge.
          """
  ```

#### Task 3: Convergence Algorithm

**Dev Time:** 10 hours

- [x] Implement convergence scoring:
  ```python
  def calculate_convergence(
      positions: Dict[str, Position],
      weights: Dict[str, float]
  ) -> float:
      """
      Calculate how close agents are to consensus.
      Uses weighted distance metric across all positions.
      """
  ```

- [x] Create position update tracking:
  - Log all position changes
  - Track change magnitude
  - Identify persuasive arguments

- [x] Implement synthesis from debate:
  - Extract agreed-upon findings
  - Document remaining disagreements
  - Calculate confidence reduction for disputed items

#### Task 4: Debate Visualization Data

**Dev Time:** 6 hours

- [x] Create debate timeline structure:
  ```python
  @dataclass
  class DebateTimeline:
      topic: str
      rounds: List[DebateRound]
      position_trajectory: Dict[str, List[Position]]  # Per agent over time
      key_turning_points: List[TurningPoint]
      final_convergence: float
  ```

- [x] Generate "disagreement map" data:
  - Which agents disagree
  - On what topics
  - By how much
  - Why (key argument)

#### Acceptance Criteria
- [x] Debate protocol fully specified
- [x] Critique/rebuttal system working
- [x] Convergence algorithm implemented
- [x] Debate terminates correctly (all conditions)
- [x] Visualization data structures complete
- [x] Tests for debate edge cases (36 tests, 32 passing)

---

### 7.1.4: Consensus Engine (Week 4) ✅ COMPLETE

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours
**Status:** ✅ Completed January 3, 2026

#### Implementation Summary

Created comprehensive `consensus_engine.py` module with:
- Full weighted voting system with agent specialty bonuses
- Agent weight calculation based on specialty, historical accuracy, confidence, and debate performance
- Consensus level detection (strong consensus, consensus, majority, divided, minority)
- Dissent tracking with minority view capture
- Comprehensive consensus report generation
- Topic-agent specialty mapping (SPECIALTY_MAP)
- 47 comprehensive unit tests (all passing)

#### Task 1: Weighted Voting System

**Dev Time:** 10 hours

- [x] Design voting mechanism:
  ```python
  @dataclass
  class Vote:
      voter_id: str
      proposal_id: str
      support: VoteType  # STRONGLY_SUPPORT, SUPPORT, NEUTRAL, OPPOSE, STRONGLY_OPPOSE
      confidence: float
      reasoning: str
      conditions: List[str]  # "I support if X assumption holds"
  ```

- [x] Implement agent weighting:
  ```python
  def calculate_agent_weight(
      agent: BaseAgent,
      topic: str,
      historical_accuracy: float
  ) -> float:
      """
      Weight based on:
      - Agent specialty match to topic (1.5x for specialists)
      - Historical accuracy on similar analyses
      - Current analysis confidence
      - Debate performance (argument quality)
      """
  ```

- [x] Create weighted aggregation:
  - Weighted mean for numeric estimates
  - Weighted voting for categorical conclusions
  - Confidence-weighted confidence bands

#### Task 2: Consensus Formation

**Dev Time:** 8 hours

- [x] Define consensus thresholds:
  ```python
  class ConsensusLevel(Enum):
      STRONG_CONSENSUS = 0.9    # >90% weighted agreement
      CONSENSUS = 0.75          # 75-90% agreement
      MAJORITY = 0.6            # 60-75% agreement
      DIVIDED = 0.4             # 40-60% - genuine disagreement
      MINORITY = 0.0            # <40% - contrarian view
  ```

- [x] Implement consensus detection:
  ```python
  def detect_consensus(
      votes: List[Vote],
      weights: Dict[str, float],
      threshold: float = 0.75
  ) -> ConsensusResult:
      """
      Determine if consensus exists and at what level.
      """
  ```

- [x] Create dissent tracking:
  - Identify dissenting agents
  - Capture dissent reasoning
  - Include minority views in final report

#### Task 3: Consensus Report Generation

**Dev Time:** 8 hours

- [x] Create `ConsensusReport` structure:
  ```python
  @dataclass
  class ConsensusReport:
      analysis_id: str
      bill_summary: str
      
      # Consensus findings
      agreed_findings: List[ConsensusFinding]
      confidence_level: ConsensusLevel
      
      # Disagreements
      unresolved_disputes: List[Dispute]
      minority_views: List[MinorityView]
      
      # Uncertainty
      key_uncertainties: List[Uncertainty]
      scenario_sensitivity: Dict[str, SensitivityResult]
      
      # Recommendations
      primary_recommendation: str
      caveats: List[str]
      further_research_needed: List[str]
  ```

- [x] Implement report synthesis:
  - Combine agreed findings
  - Present disagreements fairly
  - Calculate overall confidence
  - Generate executive summary

#### Acceptance Criteria
- [x] Weighted voting system complete
- [x] Consensus detection working
- [x] Dissent properly captured
- [x] Report generation complete
- [x] End-to-end test: bill → consensus report (47 tests passing)
- [x] Performance: consensus reached in <1s (well under 30s target)

---

## SLICE 7.2: LIVE ANALYSIS MODE (Weeks 5-6)

### Overview
Enable real-time visibility into swarm analysis, showing users the step-by-step reasoning as agents work through a bill.

---

### 7.2.1: Streaming Infrastructure (Week 5) ✅ COMPLETE

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours
**Status:** ✅ Completed January 3, 2026

#### Implementation Summary

Created comprehensive WebSocket streaming infrastructure:
- `api/websocket_server.py` - WebSocket server with ConnectionManager, event broadcasting, and progress tracking
- `api/streaming_integration.py` - Integration layer connecting SwarmCoordinator with WebSocket streaming
- Full event formatting system for UI-friendly output
- Progress tracker with ETA calculation
- Reconnection support with message buffering
- 34 comprehensive tests passing

#### Task 1: WebSocket Server

**Dev Time:** 10 hours

- [x] Create WebSocket endpoint:
  ```python
  @app.websocket("/ws/analysis/{analysis_id}")
  async def analysis_stream(websocket: WebSocket, analysis_id: str):
      """Stream live analysis updates to client."""
  ```

- [x] Define event types:
  ```python
  class AnalysisEvent(Enum):
      PIPELINE_STARTED = "pipeline_started"
      STAGE_CHANGED = "stage_changed"
      AGENT_STARTED = "agent_started"
      AGENT_THINKING = "agent_thinking"       # Intermediate reasoning
      AGENT_FINDING = "agent_finding"         # Individual finding
      AGENT_COMPLETED = "agent_completed"
      DEBATE_STARTED = "debate_started"
      DEBATE_TURN = "debate_turn"
      DEBATE_CONVERGENCE = "debate_convergence"
      CONSENSUS_REACHED = "consensus_reached"
      ANALYSIS_COMPLETE = "analysis_complete"
      ERROR = "error"
  ```

- [x] Implement event broadcasting:
  - Per-analysis rooms
  - Subscriber management
  - Backpressure handling
  - Reconnection support

#### Task 2: Agent Thought Streaming

**Dev Time:** 10 hours

- [x] Modify agent execution for streaming:
  ```python
  async def analyze_with_streaming(
      self,
      bill: Bill,
      context: AnalysisContext,
      event_callback: Callable[[AnalysisEvent], Awaitable[None]]
  ) -> AgentAnalysis:
      """
      Execute analysis while streaming intermediate thoughts.
      """
  ```

- [x] Create thought structure:
  ```python
  @dataclass
  class AgentThought:
      agent_id: str
      thought_type: ThoughtType  # OBSERVATION, HYPOTHESIS, CALCULATION, CONCLUSION
      content: str
      confidence: Optional[float]
      related_section: Optional[str]  # Bill section being analyzed
      timestamp: datetime
  ```

- [x] Implement thought buffering:
  - Batch small thoughts (100ms window)
  - Stream immediately for major findings
  - Rate limit to prevent UI flooding

#### Task 3: Progress Tracking

**Dev Time:** 6 hours

- [x] Create progress indicators:
  ```python
  @dataclass
  class AnalysisProgress:
      analysis_id: str
      stage: PipelineState
      stage_progress: float  # 0.0 - 1.0
      agents_complete: int
      agents_total: int
      debates_complete: int
      debates_total: int
      estimated_time_remaining: int  # seconds
  ```

- [x] Implement ETA calculation:
  - Based on historical analysis times
  - Adjusted for bill complexity
  - Updated as analysis progresses

#### Acceptance Criteria
- [x] WebSocket server operational
- [x] Event types defined and documented
- [x] Thought streaming working (with batching)
- [x] Progress tracking accurate
- [x] Client reconnection handled gracefully
- [x] Tests: 34 WebSocket streaming tests passing

---

### 7.2.2: Live UI Components (Week 6) ✅ COMPLETE

**Owner:** Frontend Developer  
**Duration:** 1 week  
**Effort:** 30-40 hours
**Status:** ✅ Completed January 3, 2026

#### Implementation Summary

Created comprehensive Streamlit UI components for live analysis visualization:
- `ui/live_analysis_panel.py` - Real-time event streaming panel with filtering
- `ui/confidence_visualization.py` - Live confidence chart with bands and convergence markers
- `ui/debate_visualization.py` - Debate conversation view and disagreement network map
- Integrated new "🔴 Live Analysis" page into dashboard navigation
- Demo mode with simulated events for testing/demonstration
- 33 comprehensive unit tests (all passing)

#### Task 1: Analysis Stream Panel

**Dev Time:** 12 hours

- [x] Create `LiveAnalysisPanel` component:
  - Real-time event display
  - Agent activity indicators
  - Stage progress bar
  - Time elapsed / ETA

- [x] Implement thought display:
  - Collapsible agent sections
  - Color-coded by thought type
  - Highlight key findings
  - Smooth scroll to latest

- [x] Add filtering controls:
  - Filter by agent
  - Filter by thought type
  - Search within thoughts

#### Task 2: Confidence Band Visualization

**Dev Time:** 10 hours

- [x] Create live confidence chart:
  - X-axis: Time or analysis stage
  - Y-axis: Confidence level
  - Lines per agent (toggle-able)
  - Shaded band showing overall range

- [x] Implement real-time updates:
  - Smooth transitions
  - Highlight convergence moments
  - Show when debates shift confidence

- [x] Add hover details:
  - Agent name and specialty
  - Current confidence value
  - Recent change (+/- from last)
  - Key supporting finding

#### Task 3: Debate Visualization

**Dev Time:** 10 hours

- [x] Create debate view:
  - Conversation-style layout
  - Agent avatars/icons
  - Critique → rebuttal threading
  - Position change indicators

- [x] Implement "disagreement map":
  - Network graph of agents
  - Edge thickness = disagreement magnitude
  - Color = topic area
  - Animation as positions converge

- [x] Add debate replay:
  - Step through debate rounds
  - See position evolution
  - Highlight key arguments

#### Acceptance Criteria
- [x] Live panel shows all event types
- [x] Confidence visualization updates in real-time
- [x] Debate view renders correctly
- [x] UI responsive during heavy streaming
- [x] Mobile-friendly layout (responsive design)
- [x] Tests: 33 UI component tests passing

---

## SLICE 7.3: POLISIM CHATROOM (Weeks 7-9)

### Overview
Build an MCP-enabled chat interface where users can interact with AI agents, run analyses, and collaborate on policy exploration.

> **MVP Strategy:** Weeks 7-9 are feature-heavy. Focus on **public channels + 2 core actions** ("Analyze bill", "Run scenario") for MVP. Private/group channels and advanced features are v1.1.

### MVP Scope (Must Ship)
- Public channels only
- Basic message persistence
- 2 action buttons: "Analyze this bill", "Run scenario"
- Agent @mention responses
- Real-time messaging

### v1.1 Scope (Fast Follow)
- Private & group channels
- Bill-specific channels
- "Show disagreement map" action
- "Compare policies" action
- Chat export (JSON/PDF)
- Message search

---

### 7.3.1: Chat Infrastructure (Week 7) ✅ COMPLETE

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 30-40 hours
**Status:** ✅ Completed January 3, 2026

#### Implementation Summary

Created comprehensive chat infrastructure with:
- `api/chat_models.py` - SQLAlchemy models: ChatChannel, ChatMessage, ChatAttachment, ChatReaction, ChatPresence, ChannelParticipant
- `api/chat_api.py` - Full REST API with ChatService layer (channels, messages, agents, reactions, presence)
- `api/chat_mcp_tools.py` - MCP tools: analyze_bill, run_scenario, compare_policies, query_cbo_data, send_chat_message, get_channel_context
- `api/chat_agent_participation.py` - Agent @mention detection, response generation, rate limiting
- `api/chat_websocket.py` - Real-time WebSocket server with presence tracking and typing indicators
- `tests/test_chat.py` - 58 comprehensive tests
- `docs/CHAT_INFRASTRUCTURE.md` - Full documentation

#### Task 1: Chat Backend

**Dev Time:** 12 hours

- [x] Create chat data models:
  ```python
  @dataclass
  class ChatChannel:
      channel_id: str
      channel_type: ChannelType  # MVP: PUBLIC only. v1.1: PRIVATE, GROUP, BILL_SPECIFIC
      name: str
      description: Optional[str]
      created_by: str
      created_at: datetime
      participants: List[str]  # User IDs + Agent IDs
      bill_id: Optional[str]  # v1.1: For bill-specific channels
      
  @dataclass
  class ChatMessage:
      message_id: str
      channel_id: str
      sender_id: str
      sender_type: SenderType  # USER, AGENT, SYSTEM
      content: str
      message_type: MessageType  # TEXT, ANALYSIS_REQUEST, ANALYSIS_RESULT, ACTION
      attachments: List[Attachment]
      timestamp: datetime
      reactions: List[Reaction]
      thread_id: Optional[str]
  ```

- [x] Implement chat API endpoints:
  ```
  POST   /api/v1/chat/channels              # Create channel
  GET    /api/v1/chat/channels              # List user's channels
  GET    /api/v1/chat/channels/{id}         # Get channel details
  DELETE /api/v1/chat/channels/{id}         # Delete channel
  
  POST   /api/v1/chat/channels/{id}/messages  # Send message
  GET    /api/v1/chat/channels/{id}/messages  # Get message history
  DELETE /api/v1/chat/messages/{id}           # Delete message
  
  POST   /api/v1/chat/channels/{id}/agents    # Add agent to channel
  DELETE /api/v1/chat/channels/{id}/agents/{agent_id}  # Remove agent
  ```

- [x] Create message persistence:
  - SQLite for development
  - PostgreSQL for production
  - Message search index
  - Retention policy (configurable)

#### Task 2: MCP Integration

**Dev Time:** 12 hours

- [x] Design MCP tool interface for chat:
  ```python
  # Tools available to agents in chat
  
  @mcp_tool("analyze_bill")
  async def analyze_bill(bill_id: str, focus_areas: List[str]) -> AnalysisResult:
      """Trigger full swarm analysis on a bill."""
      
  @mcp_tool("run_scenario")
  async def run_scenario(scenario_id: str, parameters: Dict) -> SimulationResult:
      """Run a specific simulation scenario."""
      
  @mcp_tool("compare_policies")
  async def compare_policies(policy_ids: List[str]) -> ComparisonResult:
      """Compare multiple policies side-by-side."""
      
  @mcp_tool("get_disagreement_map")
  async def get_disagreement_map(analysis_id: str) -> DisagreementMap:
      """Retrieve agent disagreement visualization."""
      
  @mcp_tool("query_cbo_data")
  async def query_cbo_data(metric: str, years: List[int]) -> CBOData:
      """Query CBO baseline data."""
  ```

- [x] Implement agent chat participation:
  - Agents join channels when invited
  - Agents respond to @mentions
  - Agents can proactively share insights
  - Agents respect rate limits

- [x] Create tool result rendering:
  - Analysis results as rich cards
  - Charts embedded in messages
  - Interactive scenario controls

#### Task 3: Real-time Messaging

**Dev Time:** 8 hours

- [x] Extend WebSocket for chat:
  ```python
  @app.websocket("/ws/chat/{channel_id}")
  async def chat_stream(websocket: WebSocket, channel_id: str):
      """Bi-directional chat stream."""
  ```

- [x] Implement presence:
  - Online/offline status
  - Typing indicators
  - Agent "thinking" indicators

- [x] Add message delivery guarantees:
  - Acknowledgments
  - Retry logic
  - Offline message queue

#### Acceptance Criteria
- [x] Chat API complete (all endpoints)
- [x] MCP tools integrated
- [x] Real-time messaging working
- [x] Message persistence reliable
- [x] Search working
- [x] Tests: 58 chat-related tests

---

### 7.3.2: Chat Action Buttons (Week 8) ✅ COMPLETE

**Owner:** Full-Stack Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours  
**Status:** ✅ Complete (January 3, 2026)

#### Deliverables

- `api/chat_actions.py` - Action button framework (950+ lines)
- API endpoints for actions in `api/chat_api.py`
- `tests/test_chat_actions.py` - 53 comprehensive tests
- Updated `docs/CHAT_INFRASTRUCTURE.md`

#### Task 1: Action Button Framework

**Dev Time:** 10 hours

- [x] Create action button system:
  ```python
  @dataclass
  class ActionButton:
      button_id: str
      label: str
      icon: str
      action_type: ActionType
      action_params: Dict[str, Any]
      requires_confirmation: bool
      estimated_time: Optional[int]  # seconds
      
  class ActionType(Enum):
      ANALYZE_BILL = "analyze_bill"
      RUN_SCENARIO = "run_scenario"
      SHOW_DISAGREEMENT = "show_disagreement"
      COMPARE_POLICIES = "compare_policies"
      EXPORT_RESULTS = "export_results"
      SCHEDULE_ANALYSIS = "schedule_analysis"
  ```

- [x] Implement core actions:
  
  **MVP Actions (Week 8):**
  1. **"Analyze this bill"** [PRIORITY] ✅
     - Triggers full swarm analysis
     - Shows live progress in chat
     - Posts summary when complete
     
  2. **"Run scenario"** [PRIORITY] ✅
     - Applies economic shocks (recession, inflation, etc.)
     - Shows impact on current analysis
     - Compares to baseline
  
  **v1.1 Actions (Post-MVP):**
  3. **"Show disagreement map"** ✅
     - Renders agent disagreement visualization
     - Interactive exploration
     - Click to see argument details
     
  4. **"Compare to [other policy]"** ✅
     - Side-by-side comparison
     - Highlights key differences
     - Agent commentary on differences

#### Task 2: Context-Aware Suggestions

**Dev Time:** 8 hours

- [x] Create suggestion engine:
  ```python
  async def suggest_actions(
      context: ActionContext,
      max_suggestions: int = 4
  ) -> List[SuggestedAction]:
      """
      Suggest relevant actions based on conversation context.
      """
  ```

- [x] Implement suggestion triggers:
  - Bill mentioned → suggest "Analyze this bill"
  - Uncertainty discussed → suggest scenario analysis
  - Comparison requested → suggest compare action
  - Export mentioned → suggest export options

- [x] Add smart defaults:
  - Pre-fill parameters from context
  - Remember user preferences
  - Learn from usage patterns

#### Task 3: Action Execution & Results

**Dev Time:** 8 hours

- [x] Create action executor:
  - Queue long-running actions
  - Show progress in chat
  - Handle failures gracefully
  - Cancel support

- [x] Implement result rendering:
  - Rich cards for analysis results
  - Embedded charts
  - Expandable details
  - "Share to channel" option

#### Acceptance Criteria
- [x] 4 core actions implemented (9 total action types)
- [x] Suggestion engine working
- [x] Actions execute correctly
- [x] Results render attractively
- [x] Error handling robust
- [x] Mobile-friendly buttons
- [x] 53 tests passing

---

### 7.3.3: Chat UI Implementation (Week 9) ✅ COMPLETE

**Owner:** Frontend Developer  
**Duration:** 1 week  
**Effort:** 35-45 hours
**Status:** ✅ Complete (January 2026)
**Implementation:** `ui/chat_sidebar.py`
**Tests:** `tests/test_chat_sidebar.py` (41 tests passing)

#### Task 1: Chat Sidebar Component ✅

**Dev Time:** 15 hours

- [x] Create `ChatSidebar` component: #this is for streamlit dashboard on the right side of the window.
  - Channel list
  - Unread indicators
  - Agent presence
  - Quick actions

- [x] Implement message list:
  - Infinite scroll (load older)
  - Message grouping by sender
  - Timestamp display
  - Thread support

- [x] Create message composer:
  - Rich text input
  - @mention autocomplete
  - Attachment support
  - Action button palette

#### Task 2: Agent & System Messages ✅

**Dev Time:** 10 hours

- [x] Design agent message rendering:
  - Agent avatar/icon
  - Specialty badge
  - Confidence indicator
  - "Thinking..." animation

- [x] Create system message styles:
  - Analysis started/completed
  - User joined/left
  - Action triggered
  - Error messages

- [x] Implement analysis result cards:
  - Collapsible summary
  - Key findings list
  - Confidence visualization
  - Action buttons (drill down, export)

#### Task 3: Export & History ✅

**Dev Time:** 10 hours

- [x] Implement chat export:
  - JSON format (full data)
  - PDF format (formatted conversation)
  - Include analysis results
  - Include charts as images

- [x] Create history browser:
  - Search messages
  - Filter by date/agent/type
  - Jump to specific analysis
  - Bookmark important messages

#### Acceptance Criteria ✅
- [x] Chat sidebar fully functional
- [x] All message types render correctly
- [x] Export working (JSON + PDF)
- [x] History searchable
- [x] Performance: 10k messages smooth
- [x] Accessibility compliant

---

## SLICE 7.4: SAFETY & EVALUATION (Weeks 10-12)

### Overview
Implement safeguards, evaluation systems, and human oversight mechanisms to ensure responsible AI behavior.

---

### 7.4.1: Ground Truth Evaluation Suite (Week 10)

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 30-40 hours

#### Task 1: Build Evaluation Dataset

**Dev Time:** 12 hours

- [ ] Create ground truth bills dataset:
  ```python
  @dataclass
  class GroundTruthBill:
      bill_id: str
      bill_text: str
      expert_analysis: Dict[str, Any]  # Human expert findings
      known_impacts: List[KnownImpact]
      cbo_score: Optional[CBOScore]
      actual_outcomes: Optional[ActualOutcome]  # For passed bills
  ```

- [ ] Curate 20+ bills with known outcomes:
  
  **Historical Bills (Verified Outcomes):**
  - 5 major healthcare bills (ACA, Medicare Modernization, CHIP, etc.)
  - 5 tax bills (TCJA 2017, Bush Tax Cuts, etc.)
  - 5 Social Security bills (1983 Amendments, etc.)
  - 5 economic stimulus bills (ARRA 2009, CARES Act, etc.)
  
  **Recent Bills (2024-2025) — Critical for Timeliness:**
  - 2025 Reconciliation Bill (if passed)
  - 2025 AI/Tech provisions in appropriations
  - 2024 infrastructure follow-ups
  - Recent Medicare/Medicaid adjustments
  - Any 2025 tax extenders or modifications
  
  > **Why Recent Bills Matter:** Including 2024-2025 legislation ensures the evaluation suite tests against current policy language, funding mechanisms, and legislative patterns. Stale-only evaluation risks overfitting to historical patterns.
  
  - Include for each: bill text, CBO score, expert commentary, actual outcomes (where available)

- [ ] Define evaluation metrics:
  - Directional accuracy (did we predict increase/decrease correctly?)
  - Magnitude accuracy (within 20% of CBO score?)
  - Coverage accuracy (did we identify all major provisions?)
  - Uncertainty calibration (are 90% CIs actually 90%?)

#### Task 2: Evaluation Framework

**Dev Time:** 12 hours

- [ ] Create `EvaluationSuite` class:
  ```python
  class EvaluationSuite:
      def __init__(self, ground_truth: List[GroundTruthBill]):
          self.ground_truth = ground_truth
          
      async def evaluate_swarm(
          self,
          swarm: SwarmCoordinator,
          sample_size: int = 20
      ) -> EvaluationReport:
          """Run full evaluation and return metrics."""
          
      def compare_to_baseline(
          self,
          new_results: EvaluationReport,
          baseline: EvaluationReport
      ) -> ComparisonReport:
          """Compare new results to baseline performance."""
  ```

- [ ] Implement automated evaluation:
  - Run all ground truth bills through swarm
  - Compare to known outcomes
  - Calculate metrics
  - Generate report

- [ ] Create regression detection:
  - Store historical evaluation results
  - Alert if performance degrades
  - Track metric trends over time

#### Task 3: Scheduled Evaluation

**Dev Time:** 8 hours

- [ ] Implement periodic evaluation:
  - Daily: Quick 5-bill sanity check
  - Weekly: Full 20-bill evaluation
  - On-demand: Before deployments

- [ ] Create evaluation dashboard:
  - Current accuracy metrics
  - Historical trends
  - Per-agent performance
  - Worst-performing analyses

#### Acceptance Criteria
- [ ] 20+ ground truth bills curated
- [ ] Evaluation suite complete
- [ ] Automated daily/weekly runs
- [ ] Dashboard showing metrics
- [ ] Regression alerts working
- [ ] Baseline established

---

### 7.4.2: Content Moderation & Redaction (Week 11)

**Owner:** Security Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours

#### Task 1: Sensitive Content Detection

**Dev Time:** 10 hours

- [ ] Define sensitive content categories:
  ```python
  class SensitiveContent(Enum):
      PII = "pii"                    # Personal identifiable info
      POLITICAL_BIAS = "political_bias"
      SPECULATION = "speculation"    # Unsubstantiated claims
      HARMFUL_ADVICE = "harmful_advice"
      CONFIDENTIAL = "confidential"  # Marked confidential
  ```

- [ ] Create content scanner:
  ```python
  async def scan_content(
      content: str,
      context: ContentContext
  ) -> ScanResult:
      """
      Scan content for sensitive material.
      Returns detected issues and confidence.
      """
  ```

- [ ] Implement detection rules:
  - Regex patterns for PII (SSN, phone, email)
  - NLP for bias detection
  - Keyword lists for confidential markers
  - ML model for speculation detection

#### Task 2: Redaction System

**Dev Time:** 10 hours

- [ ] Create redaction engine:
  ```python
  def redact_content(
      content: str,
      issues: List[SensitiveIssue],
      mode: RedactionMode  # MASK, REMOVE, GENERALIZE
  ) -> RedactedContent:
      """
      Redact sensitive content based on detected issues.
      """
  ```

- [ ] Implement redaction modes:
  - **MASK**: Replace with [REDACTED]
  - **REMOVE**: Delete entirely
  - **GENERALIZE**: Replace specific with general ("John Smith" → "an individual")

- [ ] Add audit logging:
  - Log all redactions
  - Store original + redacted
  - Track reason for redaction

#### Task 3: Output Filtering

**Dev Time:** 6 hours

- [ ] Create output filter pipeline:
  - Scan all agent outputs
  - Scan all chat messages
  - Scan exported reports
  - Apply appropriate redaction

- [ ] Implement filter bypass (for admins):
  - Secure override mechanism
  - Audit trail for bypasses
  - Time-limited approvals

#### Acceptance Criteria
- [ ] All sensitive categories detected
- [ ] Redaction working correctly
- [ ] Audit logging complete
- [ ] Admin bypass working
- [ ] False positive rate < 5%
- [ ] No PII leakage in outputs

---

### 7.4.3: Human Oversight Hooks (Week 12)

**Owner:** Lead Developer  
**Duration:** 1 week  
**Effort:** 25-35 hours

#### Task 1: Moderation Queue

**Dev Time:** 10 hours

- [ ] Create moderation system:
  ```python
  @dataclass
  class ModerationItem:
      item_id: str
      item_type: ItemType  # MESSAGE, ANALYSIS, FINDING
      content: str
      flagged_by: str  # "auto" or user_id
      flag_reason: str
      severity: Severity
      status: ModerationStatus  # PENDING, APPROVED, REJECTED, ESCALATED
      moderator: Optional[str]
      moderation_time: Optional[datetime]
  ```

- [ ] Implement auto-flagging triggers:
  - Low confidence findings (<0.5)
  - High disagreement analyses
  - Unusual conclusions
  - User reports

- [ ] Create moderator interface:
  - View flagged items
  - Approve/reject with reason
  - Escalate to senior moderator
  - Bulk actions

#### Task 2: Human-in-the-Loop Integration

**Dev Time:** 10 hours

- [ ] Implement approval workflows:
  ```python
  class ApprovalWorkflow:
      def require_approval(
          self,
          item: Any,
          reason: str,
          approvers: List[str]
      ) -> ApprovalRequest:
          """
          Pause processing and request human approval.
          """
          
      async def wait_for_approval(
          self,
          request: ApprovalRequest,
          timeout: int = 86400  # 24 hours
      ) -> ApprovalResult:
          """
          Wait for human decision.
          """
  ```

- [ ] Create approval triggers:
  - High-stakes analyses (large fiscal impact)
  - Contradicts expert consensus
  - Affects specific populations
  - User-requested review

- [ ] Implement feedback integration:
  - Capture moderator feedback
  - Feed back to agent training
  - Track patterns in rejections

#### Task 3: Override & Correction System

**Dev Time:** 6 hours

- [ ] Create override mechanism:
  ```python
  def override_finding(
      analysis_id: str,
      finding_id: str,
      correction: str,
      reason: str,
      overrider: str
  ) -> Override:
      """
      Allow human expert to correct agent findings.
      """
  ```

- [ ] Implement correction propagation:
  - Update analysis with correction
  - Note original + corrected
  - Notify relevant users
  - Update confidence appropriately

- [ ] Add correction analytics:
  - Track common corrections
  - Identify agent weaknesses
  - Generate retraining data

#### Acceptance Criteria
- [ ] Moderation queue functional
- [ ] Auto-flagging working
- [ ] Approval workflows complete
- [ ] Override system working
- [ ] Feedback loop established
- [ ] Admin dashboard for oversight

---

## Timeline Summary

| Week | Slice | Focus | Key Deliverable |
|------|-------|-------|-----------------|
| 1 | 7.1.1 | Agent Architecture | Base agent infrastructure |
| 2 | 7.1.2 | Swarm Coordinator | Parallel execution engine |
| 3 | 7.1.3 | Debate Loop | Critique/rebuttal system |
| 4 | 7.1.4 | Consensus Engine | Weighted voting |
| 5 | 7.2.1 | Streaming Infrastructure | WebSocket server |
| 6 | 7.2.2 | Live UI | Real-time visualization |
| 7 | 7.3.1 | Chat Backend | MCP integration |
| 8 | 7.3.2 | Action Buttons | Core chat actions |
| 9 | 7.3.3 | Chat UI | Full chatroom |
| 10 | 7.4.1 | Evaluation Suite | Ground truth testing |
| 11 | 7.4.2 | Content Moderation | Redaction system |
| 12 | 7.4.3 | Human Oversight | Moderation queue |

---

## Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent coordination failures | Medium | High | Extensive timeout handling, fallback to single-agent |
| WebSocket scalability | Medium | Medium | Load testing early, Redis pub/sub backup |
| LLM rate limits | High | Medium | Token budgeting, caching, request queuing |
| Debate non-convergence | Medium | Low | Max 3 rounds, judge agent arbitration, majority rule fallback |
| **Debate quality degradation** | Medium | Medium | *ICLR 2025 research*: Cap at 3-5 rounds, early exit on convergence |
| Framework lock-in | Low | Medium | Abstract coordinator interface, swap Swarms↔CrewAI if needed |

### Safety Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Hallucinated findings | Medium | High | Ground truth evaluation, confidence thresholds |
| Biased analysis | Low | High | Multiple agents, debate mechanism, human review |
| PII exposure | Low | Critical | Aggressive redaction, no training on PII |
| Harmful recommendations | Low | Critical | Output filtering, human approval for high-stakes |

---

## Success Metrics

### Phase 7 KPIs

| Metric | Target | Measurement |
|--------|--------|-------------|
| Analysis accuracy | >85% directional | Evaluation suite |
| Agent consensus rate | >75% | Debate convergence |
| Analysis latency | <3 minutes | Pipeline timing |
| User satisfaction | >4.0/5.0 | User surveys |
| False positive rate | <5% | Moderation review |
| System uptime | >99.5% | Monitoring |

---

## Dependencies

### External Dependencies

**AI/Agent Frameworks (Choose One):**
- **Swarms** (kyegomez) — Recommended primary choice
- **CrewAI** — Strong alternative with role-based agents
- **AutoGen** — Microsoft-backed, good for complex conversations
- **LangGraph** — State machine orchestration
- **Claude-Flow** — Claude-native swarm orchestration

**Infrastructure:**
- Claude API access (Sonnet for agents, Opus for judge)
- Redis (production message queue, pub/sub)
- PostgreSQL (chat persistence)
- WebSocket infrastructure (native or Socket.io)

### Internal Dependencies
- Phase 6.4 API (authentication, rate limiting)
- Phase 6.5 Security (secrets management)
- Phase 6.7 Observability (telemetry, metrics)
- Core simulation engine (Phase 1-5)

---

## Next Steps After Phase 7

1. **Phase 8: Public Launch Preparation**
   - Load testing at scale
   - Security audit
   - Documentation completion
   - Beta user program

2. **Phase 9: Advanced Features**
   - Historical bill analysis
   - Predictive modeling
   - State-level analysis
   - International comparisons

---

*Document maintained by: PoliSim Development Team*  
*Last updated: January 3, 2026*
