# 1-Hour Introduction to PoliSim

**Quick Start Workshop**

---

## Workshop Overview

| Detail | Information |
|--------|-------------|
| **Duration** | 60 minutes |
| **Level** | Beginner |
| **Prerequisites** | None (Python helpful) |
| **Materials** | Laptops with PoliSim installed |
| **Outcome** | Run first simulation, understand basics |

---

## Agenda

| Time | Topic | Activity |
|------|-------|----------|
| 0:00-0:05 | Welcome & Overview | Intro slides |
| 0:05-0:15 | What is Fiscal Policy? | Mini-lecture |
| 0:15-0:25 | PoliSim Demo | Live walkthrough |
| 0:25-0:45 | Hands-On Exercise | Students run Notebook 01 |
| 0:45-0:55 | Q&A & Discussion | Open forum |
| 0:55-1:00 | Wrap-up & Next Steps | Resources |

---

## Detailed Guide

### Opening (0:00-0:05)

**Instructor Script:**

> "Welcome to PoliSim! Today you'll learn how to simulate federal fiscal policy. By the end of this hour, you'll have run your first policy simulation and understand the basics of the federal budget."

**Key Points:**
- PoliSim = Open-source fiscal policy simulator
- Educational tool, not prediction engine
- Hands-on learning approach

### Mini-Lecture: Fiscal Policy Basics (0:05-0:15)

**Cover These Topics:**

1. **The Federal Budget**
   - Revenue: ~$5T (taxes)
   - Spending: ~$7T (programs + interest)
   - Deficit: ~$2T (annual gap)
   - Debt: ~$35T (cumulative)

2. **Why It Matters**
   - Affects everyone through taxes and services
   - Long-term sustainability questions
   - Policy trade-offs are real

3. **What PoliSim Does**
   - Projects fiscal trajectories
   - Compares policy scenarios
   - Quantifies uncertainty

**Visual Aid:**
Draw or display a simple budget pie chart showing revenue sources and spending categories.

### Live Demo (0:15-0:25)

**Walk Through These Steps:**

1. Open Jupyter Notebook 01
2. Run the setup cell
3. Load a policy configuration
4. Run a 10-year simulation
5. Show the debt trajectory chart
6. Highlight key outputs

**Talking Points During Demo:**
- "Notice how we import the core modules..."
- "The simulation takes about X seconds..."
- "This chart shows debt growing from A to B..."
- "The confidence interval tells us..."

### Hands-On Exercise (0:25-0:45)

**Student Instructions:**

1. Open `notebooks/01_welcome_to_polisim.ipynb`
2. Run each cell in order (Shift+Enter)
3. Observe the outputs
4. Try changing one parameter (e.g., years)
5. Re-run and compare results

**Instructor Actions:**
- Circulate to help with technical issues
- Answer individual questions
- Note common problems for Q&A

**Common Issues:**
| Problem | Solution |
|---------|----------|
| Kernel not starting | Restart kernel |
| Import error | Check sys.path cell |
| Slow execution | Normal first time |

### Discussion (0:45-0:55)

**Discussion Questions:**

1. "What surprised you about the federal budget?"
2. "Why do we show ranges instead of single numbers?"
3. "What policy questions would you want to explore?"

**Encourage:**
- Multiple perspectives
- Critical thinking
- Curiosity about methodology

### Wrap-Up (0:55-1:00)

**Next Steps:**
- Complete Notebook 02 on your own
- Join the PoliSim community
- Explore the documentation

**Resources:**
- Full notebook curriculum (10 notebooks)
- Documentation in `/docs/`
- FAQ and troubleshooting

**Closing Script:**

> "Great work today! You've taken your first step into fiscal policy simulation. The full curriculum has 10 notebooks that go much deeper. Questions? Feel free to reach out."

---

## Facilitator Checklist

### Before Workshop
- [ ] Test all notebooks on workshop machines
- [ ] Prepare slides (optional)
- [ ] Print handouts if desired
- [ ] Set up display/projector
- [ ] Have backup plan if tech fails

### During Workshop
- [ ] Start on time
- [ ] Keep to schedule
- [ ] Engage quiet participants
- [ ] Note questions for follow-up
- [ ] Leave time for Q&A

### After Workshop
- [ ] Collect feedback (optional survey)
- [ ] Share follow-up resources
- [ ] Document any issues encountered

---

## Handout: Quick Reference

### Key Commands

```python
# Run a cell
Shift + Enter

# Restart kernel
Kernel menu → Restart

# Clear outputs
Cell menu → All Output → Clear
```

### Key Concepts

| Term | Definition |
|------|------------|
| Deficit | Annual spending - revenue |
| Debt | Total accumulated borrowing |
| Projection | Future estimate under assumptions |
| Monte Carlo | Many random simulations |

### Next Steps

1. Complete Notebook 02 (30-40 min)
2. Explore healthcare policy (Notebook 03)
3. Try the capstone project (Notebook 10)

---

*Workshop materials for PoliSim educational curriculum*
