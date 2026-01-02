# PoliSim Documentation Index

**Last Updated:** January 2, 2026  
**Status:** Phase 6.2.5 — Security Hardening Complete, Policy Extraction Active

---

## 🚀 Quick Start

**New to PoliSim?** Start here:
1. **[00_START_HERE.md](00_START_HERE.md)** - Project overview and quick start guide
2. **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - API and usage examples
3. **[README.md](../README.md)** - Main project README with installation

---

## 📚 Core Documentation

### Project Status & History
  - Latest: Dec 31, 2025 - Documentation consolidation (roadmap move, theme rollup, link cleanup)
  - Dec 27, 2025 - Sprint 5.4 hardening (launcher/bootstrap and dashboard polish)
  - Dec 25, 2025 - Comprehensive audit complete (A+ grade, 14/14 issues resolved)
  - All major releases and bug fixes documented

- **[phase 5 slices.md](../docs/phase%205%20slices.md)** - Slice plan to complete Phase 5
  - Slices 5.4–5.7 with objectives, exit criteria, risks
  - Completion checklist for Phase 5 exit

**Phase Planning:** ../docs/PHASES.md, ../docs/phase%205%20slices.md, EXHAUSTIVE_INSTRUCTION_MANUAL.md
  - **Purpose:** Working document for AI agents to document analysis findings
  - **Usage:** Agents log step-by-step debugging walkthroughs to avoid losing progress
  - **Lifecycle:** Emptied by user after completion when findings are moved to permanent docs
  - **Current Status:** Active only during live investigations (see file header for latest session)

### Development Guides
- **[EXHAUSTIVE_INSTRUCTION_MANUAL.md](EXHAUSTIVE_INSTRUCTION_MANUAL.md)** - Complete development roadmap
  - Detailed task breakdowns with time estimates
  - Module-by-module implementation guides
  - Testing strategies and validation criteria

- **[PHASES.md](../docs/PHASES.md)** - Project phases and roadmap (Phases 1-18)
  - Current: Phase 5.4 in progress; Phase 6 planned
  - Milestones, exit criteria, risks, and dependencies

### Technical References
- **[CONTEXT_FRAMEWORK.md](CONTEXT_FRAMEWORK.md)** - Policy extraction system guide
  - 16 concept categories for mechanism detection
  - Context-aware percentage extraction
  - GDP estimation algorithms

- **[CONTEXT_FRAMEWORK_INDEX.md](CONTEXT_FRAMEWORK_INDEX.md)** - Framework quick reference
  - Pattern matching examples
  - Taxonomy overview
  - Common extraction scenarios

### Code Quality Standards
- **[NAMING_CONVENTIONS.md](NAMING_CONVENTIONS.md)** - Coding standards guide
  - Function, variable, constant naming rules
  - Module organization patterns
  - Established December 24, 2025

- **[TYPE_HINTS_GUIDE.md](TYPE_HINTS_GUIDE.md)** - Type annotation standards
  - Required type hints for all new functions
  - Common patterns and examples
  - Integration with mypy

### UI/UX Documentation
- **[THEME_SYSTEM.md](THEME_SYSTEM.md)** - Consolidated theme reference (available themes, fixes, usage, testing)
  - Supersedes legacy theme audit/testing/quick-reference docs

- **[TOOLTIP_SYSTEM.md](TOOLTIP_SYSTEM.md)** - Educational tooltip implementation
  - System architecture and usage
  - Adding tooltips to new pages
  - Comprehensive glossary management

- **[DEMO_SCRIPT_USAGE.md](DEMO_SCRIPT_USAGE.md)** - Demo script guide
  - Running demonstration scenarios
  - Presentation tips and workflows

---

## 📋 Documentation Maintenance

### Adding New Documentation
1. Create file in `documentation/` directory
2. Add entry to this INDEX.md
3. Update CHANGELOG.md with significant additions
4. Cross-reference in related documents

### Removing Old Documentation
**Policy:** Delete outdated files instead of archiving. Keep only current, relevant documentation.
- Historical information goes in CHANGELOG.md
- Phase status goes in docs/PHASES.md
- Agent analysis findings are moved from debug.md to permanent docs when complete

### debug.md Special Usage
**debug.md is NOT permanent documentation.** It's a workspace for AI agents:
- Agents document step-by-step analysis and debugging findings
- Prevents losing progress during complex debugging sessions
- After completion testing and verification, findings are moved to appropriate permanent docs (VALIDATION_REPORT, CHANGELOG, etc.)
- File is then emptied by the userfor next analysis session
- Think of it as a "scratch pad" or "lab notebook" for agent work with user verifications for completion

### Current Documentation Standards
- **Markdown format** for all documentation
- **Clear headings** with emoji indicators (🚀, ✅, 📊, etc.)
- **Date stamps** on all versioned documents
- **Status indicators** (✅ Complete, 🟡 In Progress, 📋 Planned)
- **Cross-references** using relative links
- **Code examples** with syntax highlighting

---

## 🔍 Finding Information

### By Topic
- **Getting Started:** 00_START_HERE.md, QUICK_REFERENCE.md
- **Validation & Quality:** VALIDATION_REPORT_DEC26.md, CHANGELOG.md
- **Phase Planning:** ../docs/PHASES.md, EXHAUSTIVE_INSTRUCTION_MANUAL.md
- **Code Standards:** NAMING_CONVENTIONS.md, TYPE_HINTS_GUIDE.md
- **Policy Extraction:** CONTEXT_FRAMEWORK.md, CONTEXT_FRAMEWORK_INDEX.md
- **UI Features:** TOOLTIP_SYSTEM.md, DEMO_SCRIPT_USAGE.md
- **Agent Workspace:** debug.md (working document, emptied when complete)

### By Audience
- **New Developers:** 00_START_HERE.md → QUICK_REFERENCE.md → ../docs/PHASES.md
- **Contributors:** NAMING_CONVENTIONS.md → TYPE_HINTS_GUIDE.md → VALIDATION_REPORT_DEC26.md
- **Users:** README.md → TOOLTIP_SYSTEM.md → DEMO_SCRIPT_USAGE.md
- **Researchers:** CONTEXT_FRAMEWORK.md → ../docs/PHASES.md
- **AI Agents:** debug.md (workspace for analysis sessions)

---

## 📈 Project Status Summary

**Current Phase:** Phase 5.4 — Web UI + Data Integration (in progress)  
**Overall Progress:** Phase 1 ✅ | Phase 2 ✅ | Phase 3 ✅ | Phase 4 ✅ | Phase 5 🚧 | Phase 6 📋 Planned  
**Quality Bar:** Gold-standard validation maintained (see README badge for current test counts)  
**Current Focus:** Launcher/bootstrap reliability, dashboard overview accuracy, and UI documentation cleanup

**Next Milestones:**
- Finish Sprint 5.4: stabilize Windows bootstrap + Tk launcher and refresh overview copy to Phase 5
- Sprint 5.5: finalize web UI/data integrations and publish updated validation summary
- Phase 6: community validation + public launch readiness

---

**For questions or documentation issues, see project [README.md](../README.md) or open an issue on GitHub.**
