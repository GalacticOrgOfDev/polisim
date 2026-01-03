# PoliSim Instructor Guide

**Teaching Federal Fiscal Policy with PoliSim**

---

## Table of Contents

1. [Overview](#overview)
2. [Curriculum Structure](#curriculum-structure)
3. [Lesson Plans](#lesson-plans)
4. [Assessment Guidelines](#assessment-guidelines)
5. [Common Pitfalls](#common-pitfalls)
6. [Additional Resources](#additional-resources)

---

## Overview

### What is PoliSim?

PoliSim is an open-source federal fiscal policy simulator designed for educational and analytical purposes. It enables students to explore complex budget dynamics through hands-on simulation.

### Educational Philosophy

1. **Learn by Doing** — Concepts become concrete through simulation
2. **Uncertainty Awareness** — All projections have error bounds
3. **Policy Neutrality** — Explore all perspectives objectively
4. **Critical Thinking** — Question assumptions, validate results

### Target Audiences

| Audience | Level | Focus Areas |
|----------|-------|-------------|
| Undergraduates | Introductory | Budget basics, simple simulations |
| Graduate Students | Intermediate | Policy mechanics, Monte Carlo |
| Policy Professionals | Advanced | Custom models, API integration |
| General Public | Varied | Interactive exploration |

---

## Curriculum Structure

### Learning Path Overview

```
Beginner (3-4 hours)
├── Notebook 01: Welcome to PoliSim
├── Notebook 02: Federal Budget Basics
└── Assessment: Basic Budget Quiz

Intermediate (6-8 hours)  
├── Notebook 03: Healthcare Policy
├── Notebook 04: Social Security
├── Notebook 05: Monte Carlo Methods
├── Notebook 06: Tax Policy
└── Assessment: Policy Analysis Report

Advanced (4-6 hours)
├── Notebook 07: Policy Extraction
├── Notebook 08: API Integration
├── Notebook 09: Custom Policy Design
├── Notebook 10: Capstone Project
└── Assessment: Full Research Project
```

### Time Requirements

| Track | Estimated Time | Prerequisites |
|-------|----------------|---------------|
| Quick Start | 1-2 hours | None |
| Standard Course | 8-12 hours | Basic economics |
| Deep Dive | 15-20 hours | Statistics, Python |
| Research Track | 20+ hours | Graduate-level economics |

---

## Lesson Plans

### Lesson 1: Introduction to Federal Budgeting (90 minutes)

**Objectives:**
- Understand revenue sources and spending categories
- Run a basic simulation
- Interpret debt and deficit metrics

**Materials:**
- Notebook 01 & 02
- Budget visualization handout
- Discussion questions

**Procedure:**

| Time | Activity | Notes |
|------|----------|-------|
| 0-15 | Lecture: Budget overview | Use slides |
| 15-40 | Demo: Notebook 01 walkthrough | Live coding |
| 40-70 | Lab: Students run Notebook 02 | Circulate |
| 70-85 | Discussion: Key findings | Socratic method |
| 85-90 | Wrap-up: Assignment preview | |

**Discussion Questions:**
1. What surprised you about the federal budget breakdown?
2. Why is debt-to-GDP ratio more meaningful than raw debt?
3. How do economic assumptions affect projections?

**Assessment:**
- Completion of Notebook 02 exercises
- Short reflection (250 words)

---

### Lesson 2: Healthcare Policy Deep Dive (2 hours)

**Objectives:**
- Compare healthcare policy models
- Understand coverage vs. cost trade-offs
- Analyze long-term fiscal impacts

**Materials:**
- Notebook 03
- Policy comparison matrix handout
- Healthcare spending data

**Procedure:**

| Time | Activity | Notes |
|------|----------|-------|
| 0-20 | Lecture: US healthcare system overview | |
| 20-45 | Demo: Running policy comparisons | |
| 45-90 | Lab: Student analysis exercise | |
| 90-110 | Group presentations | 3-4 groups |
| 110-120 | Synthesis discussion | |

**Group Exercise:**
Divide students into groups, each analyzing a different healthcare policy:
- Group A: Status Quo
- Group B: ACA Expansion
- Group C: Public Option
- Group D: Medicare for All

Each group presents:
1. 30-year cost projection
2. Coverage levels achieved
3. Key trade-offs
4. Political feasibility assessment

---

### Lesson 3: Uncertainty & Monte Carlo (2 hours)

**Objectives:**
- Understand why point estimates are insufficient
- Interpret confidence intervals
- Design Monte Carlo experiments

**Prerequisites:**
- Basic statistics (mean, standard deviation, distributions)
- Notebook 05 familiarity

**Procedure:**

| Time | Activity | Notes |
|------|----------|-------|
| 0-25 | Lecture: Why uncertainty matters | Real-world examples |
| 25-50 | Demo: Monte Carlo basics | |
| 50-80 | Lab: Running simulations | |
| 80-100 | Analysis: Interpreting results | |
| 100-120 | Extension: Custom parameters | |

**Key Concepts to Emphasize:**
1. **Convergence** — More runs = more stable estimates
2. **Input distributions** — Garbage in, garbage out
3. **Confidence intervals** — What 90% confidence means
4. **Sensitivity** — Which parameters matter most

**Common Student Mistakes:**
- Treating mean as certainty
- Ignoring tail risks
- Over-interpreting single runs
- Confusing correlation with causation

---

### Lesson 4: Building Custom Policies (2-3 hours)

**Objectives:**
- Design original policy proposals
- Implement policies in PoliSim
- Validate policy coherence

**Materials:**
- Notebook 09
- Policy design template
- Rubric for policy evaluation

**Procedure:**

| Time | Activity | Notes |
|------|----------|-------|
| 0-30 | Lecture: Policy mechanics | |
| 30-60 | Demo: Building a policy | |
| 60-120 | Lab: Student policy design | |
| 120-150 | Peer review | |
| 150-180 | Presentation (optional) | |

**Policy Design Template:**

```markdown
## Policy Name: [Your Title]

### Problem Statement
[What fiscal challenge does this address?]

### Revenue Mechanisms
1. [Mechanism 1]: $___B/year
2. [Mechanism 2]: $___B/year

### Spending Changes
1. [Change 1]: $___B/year
2. [Change 2]: $___B/year

### Net Impact
- Annual: $___B deficit [increase/reduction]
- 10-year: $___T cumulative

### Assumptions
[List key assumptions]

### Limitations
[What doesn't this policy address?]
```

---

### Lesson 5: Capstone Project (3-4 hours)

**Objectives:**
- Conduct comprehensive policy analysis
- Synthesize learnings from all modules
- Produce professional-quality output

**Materials:**
- Notebook 10
- Capstone rubric
- Example reports

**Project Requirements:**

1. **Baseline Analysis** (25%)
   - 30-year projection
   - Key metric identification
   - Visualization quality

2. **Policy Comparison** (25%)
   - At least 3 policies compared
   - Fair representation
   - Trade-off analysis

3. **Uncertainty Quantification** (20%)
   - Monte Carlo implementation
   - Confidence intervals
   - Sensitivity analysis

4. **Synthesis Report** (30%)
   - Executive summary
   - Clear recommendations
   - Professional presentation

**Grading Rubric:**

| Criterion | Excellent (A) | Good (B) | Satisfactory (C) | Needs Work (D) |
|-----------|---------------|----------|------------------|----------------|
| Technical accuracy | No errors | Minor errors | Some errors | Major errors |
| Visualization | Publication quality | Clear and correct | Adequate | Confusing |
| Analysis depth | Comprehensive | Thorough | Surface-level | Incomplete |
| Writing quality | Professional | Clear | Acceptable | Unclear |
| Creativity | Original insights | Good application | Standard | Minimal effort |

---

## Assessment Guidelines

### Formative Assessments

1. **Notebook Completion Checks**
   - All cells run successfully
   - Exercises completed
   - Reflection questions answered

2. **Discussion Participation**
   - Engagement with material
   - Quality of questions
   - Peer interaction

3. **Quick Quizzes**
   - 5-10 questions after each module
   - Focus on key concepts
   - Immediate feedback

### Summative Assessments

1. **Policy Analysis Report** (Intermediate)
   - 1,500-2,000 words
   - Compare 2+ policies
   - Include visualizations
   - Due after completing Notebooks 03-06

2. **Capstone Project** (Advanced)
   - 3,000-4,000 words
   - Comprehensive analysis
   - Monte Carlo uncertainty
   - Professional presentation

3. **Research Extension** (Graduate)
   - Original research question
   - Novel policy design or model extension
   - Publication-quality output

---

## Common Pitfalls

### Technical Issues

| Problem | Solution |
|---------|----------|
| Import errors | Check sys.path setup in notebooks |
| Missing packages | Run `pip install -r requirements.txt` |
| Kernel issues | Restart kernel, clear outputs |
| Slow simulations | Reduce Monte Carlo runs for demos |

### Conceptual Misunderstandings

1. **"The model predicts..."**
   - Correction: Models project under assumptions, they don't predict

2. **"Policy X costs $Y"**
   - Correction: Policy X is estimated to cost approximately $Y ± uncertainty

3. **"The data proves..."**
   - Correction: The analysis suggests / provides evidence for...

4. **Treating baseline as neutral**
   - Correction: Current law is itself a policy choice

### Pedagogical Tips

1. **Start Simple** — Don't overwhelm with complexity
2. **Build Intuition** — Explain the "why" before the "how"
3. **Encourage Exploration** — Let students break things
4. **Validate Learning** — Check understanding frequently
5. **Connect to Reality** — Use current events as examples

---

## Additional Resources

### For Instructors

- **CBO Reports**: [cbo.gov](https://www.cbo.gov)
- **Tax Policy Center**: [taxpolicycenter.org](https://www.taxpolicycenter.org)
- **CRFB**: [crfb.org](https://www.crfb.org)
- **Federal Budget Interactive**: [national priorities](https://www.nationalpriorities.org)

### For Students

- **Notebooks 01-10**: Core curriculum
- **Glossary**: `/docs/GLOSSARY.md`
- **API Documentation**: `/docs/API_ENDPOINTS.md`
- **FAQ**: `/FAQ.md`

### Extended Reading

1. "The Budget and Economic Outlook" (CBO Annual Report)
2. "Options for Reducing the Deficit" (CBO)
3. "Understanding the Federal Budget" (Tax Policy Center)
4. "The Path to Prosperity" / "People's Budget" (contrasting perspectives)

### Technical References

- Python: [python.org/doc](https://python.org/doc)
- Pandas: [pandas.pydata.org](https://pandas.pydata.org)
- Matplotlib: [matplotlib.org](https://matplotlib.org)
- Jupyter: [jupyter.org](https://jupyter.org)

---

## Contact & Support

- **GitHub Issues**: Report bugs and request features
- **Discussions**: Ask questions and share insights
- **Email**: [project contact email]

---

*Last Updated: 2025*
