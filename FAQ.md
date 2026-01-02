# PoliSim - Frequently Asked Questions (FAQ)

## Accuracy & Validation

### Q: How accurate are your projections?
**A:** Our baseline projections are validated to ±2-5% accuracy compared to CBO projections. All assumptions are expert-reviewed, and we provide Monte Carlo confidence intervals (90% CI) for all key metrics. We document all variances and their explanations in our reconciliation reports.

### Q: How do you compare to CBO/SSA models?
**A:** We use similar methodologies to CBO and SSA but with full transparency. Our baseline reconciliation shows we match CBO's 10-year projections within acceptable variance ranges. Key differences are documented in [ASSUMPTIONS.md](documentation/ASSUMPTIONS.md). We are not a replacement for official government projections but provide comparable analysis with open-source transparency.

### Q: Can I use this to make policy decisions?
**A:** PoliSim is designed for policy analysis, education, and research. While our models are rigorous and validated, always consult official CBO, SSA, and other government agencies for final policy decisions. We recommend using PoliSim for initial exploration, scenario comparison, and understanding policy trade-offs.

### Q: Who has validated your model?
**A:** Our models undergo expert review by economists, actuaries, and policy researchers. Validation includes assumption reviews, baseline reconciliation, and methodology assessments. See our [Technical Methodology Paper](documentation/TECHNICAL_METHODOLOGY.md) for details on our validation process and expert panel.

---

## Data & Methodology

### Q: Where does the data come from?
**A:** All data comes from official government sources:
- **CBO (Congressional Budget Office):** Economic projections, budget baselines
- **SSA (Social Security Administration):** Trust fund data, actuarial reports
- **Treasury:** Historical revenue and spending data
- **OMB (Office of Management and Budget):** Budget details
- **CMS (Centers for Medicare & Medicaid Services):** Healthcare spending data

### Q: How fresh is the data?
**A:** Data is updated automatically via our CBO scraper. A freshness indicator on the dashboard shows the last update time. Most data sources are updated monthly or quarterly. You can manually trigger updates or view data history in the admin panel.

### Q: Can I change the assumptions?
**A:** Yes! The custom policy builder lets you modify 50+ parameters including:
- Economic assumptions (GDP growth, interest rates, inflation)
- Tax elasticities and behavioral responses
- Healthcare cost drivers
- Demographics (population growth, life expectancy)
- Policy levers (tax rates, spending levels, program parameters)

### Q: What assumptions are baked in?
**A:** See [ASSUMPTIONS.md](documentation/ASSUMPTIONS.md) for the complete list. Key assumptions include:
- GDP growth: 2.2% annual baseline
- Healthcare cost elasticity: -0.2 to -0.5
- Tax behavioral responses: wage elasticity 0.1-0.3
- Interest rates: 4.5% baseline
- Inflation: 2.5% annual
All assumptions are documented with sources and confidence levels.

### Q: How do you model uncertainty?
**A:** We use Monte Carlo simulation (1,000-10,000 iterations) to account for uncertainty. Each iteration randomly varies key assumptions within plausible ranges. Results include:
- Mean/median projections
- 90% confidence intervals (P5-P95)
- Probability distributions for key metrics
- Scenario analysis (optimistic, baseline, pessimistic)

---

## API & Integration

### Q: How do I access the API?
**A:** See [API_QUICK_START.md](documentation/API_QUICK_START.md) for a 5-minute tutorial. Steps:
1. Register an account: `POST /api/auth/register`
2. Create an API key: `POST /api/auth/api-keys`
3. Run simulations: `POST /api/v1/simulate`

### Q: What are the rate limits?
**A:** Rate limits by tier:
- **Unauthenticated:** 100 requests/minute
- **Authenticated (free):** 1,000 requests/minute
- **Research/Nonprofit:** 10,000 requests/minute (request via email)
- **Enterprise:** Custom limits

Simulation endpoints have additional limits: 10 simulations/minute (to manage compute resources).

### Q: Can I use PoliSim in my application?
**A:** Yes! PoliSim is MIT licensed—free for any use including commercial. The REST API is available for integration. We provide:
- Python SDK (official)
- REST API (any language)
- Example integrations (Jupyter notebooks, web apps)

### Q: Is there an SDK?
**A:** We provide an official Python SDK. JavaScript and other language SDKs are welcome as community contributions. See [API_CLIENT.md](documentation/API_CLIENT.md) for SDK documentation.

### Q: Can I run simulations offline?
**A:** Yes! Clone the repository and run locally:
```bash
git clone https://github.com/GalacticOrgOfDev/polisim.git
cd polisim
pip install -r requirements.txt
python launcher.py
```

### Q: What's the difference between the API and dashboard?
**A:** The **dashboard** (Streamlit UI) is for interactive exploration, visualization, and scenario comparison. The **API** is for programmatic access, automation, and integration into other applications. Both use the same underlying simulation engine.

---

## Privacy & Data

### Q: Is my data stored? For how long?
**A:** We store minimal data:
- **Account info:** Email, username (encrypted)
- **Usage data:** API calls, simulations run (anonymized)
- **Retention:** 30 days for usage logs, indefinitely for account data (unless deleted)

We do NOT store:
- Simulation results (discarded after response)
- Custom policies (unless you explicitly save them)
- Personal information beyond email

### Q: Can I delete my account?
**A:** Yes. Request deletion via:
- Settings page (dashboard)
- Email: galacticorgofdev@gmail.com
All data is deleted within 7 business days.

### Q: Is this GDPR compliant?
**A:** Yes. We provide:
- Privacy policy (see [PRIVACY.md](PRIVACY.md))
- Right to access your data
- Right to deletion (within 7 days)
- Data portability (JSON export)
- Minimal data collection

### Q: Can I use PoliSim for commercial purposes?
**A:** Yes! MIT license permits commercial use with no restrictions. We only ask that you:
- Cite PoliSim in publications
- Share improvements back to the community (encouraged but not required)

---

## Technical Questions

### Q: What programming languages are used?
**A:** PoliSim is primarily **Python 3.11+**. Key libraries:
- **Pandas/NumPy:** Data processing
- **Streamlit:** Dashboard UI
- **FastAPI:** REST API
- **PostgreSQL:** Database
- **Redis:** Caching/rate limiting
- **Docker:** Deployment

### Q: Can I contribute?
**A:** Yes! We welcome contributions. See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Areas where we need help

### Q: Can I fork and modify?
**A:** Yes! MIT license allows forking and modification. If you build something cool, let us know—we'd love to feature it!

### Q: What are the system requirements?
**A:** 
- **Development:** 8GB RAM, 2 CPU cores, 5GB disk space
- **Production:** 16GB RAM, 4 CPU cores, 20GB disk space
- **Large simulations:** 32GB+ RAM recommended

### Q: Does this work on Windows/Mac/Linux?
**A:** Yes! PoliSim is cross-platform. Docker deployment works on all platforms. Native installation requires Python 3.11+.

---

## Troubleshooting

### Q: The API is returning an error. What do I do?
**A:** Check the error message (we provide descriptive messages):
- **401 Unauthorized:** Invalid API key
- **429 Rate Limit:** Wait 60 seconds or upgrade tier
- **400 Bad Request:** Invalid parameters (check JSON syntax)
- **404 Not Found:** Policy/scenario doesn't exist
- **500 Server Error:** Contact support with request ID

See [API_QUICK_START.md](documentation/API_QUICK_START.md) for common errors and solutions.

### Q: My simulation is taking too long. How do I speed it up?
**A:** Options to reduce runtime:
1. **Reduce iterations:** 100 instead of 10,000 (faster, less precise)
2. **Reduce years:** 10 instead of 30 (shorter projection window)
3. **Use pre-built scenarios:** Avoid custom policies for quick results
4. **Increase compute resources:** More CPU cores = faster Monte Carlo

Typical runtimes:
- Simple policy, 10 years, 1,000 iterations: 2-5 seconds
- Complex policy, 30 years, 10,000 iterations: 30-60 seconds

### Q: I found an inaccuracy. What should I do?
**A:** Report via GitHub Issues with:
- Scenario/policy details
- Expected value (with source: CBO, SSA, etc.)
- Actual value from PoliSim
- Steps to reproduce

We investigate all accuracy reports and update models as needed.

### Q: The dashboard won't start. What's wrong?
**A:** Common fixes:
1. **Check Python version:** Requires 3.11+
2. **Install dependencies:** `pip install -r requirements.txt`
3. **Check ports:** Default ports 8501 (dashboard), 5000 (API)
4. **Use launcher:** `python launcher.py` (handles setup automatically)
5. **Check logs:** `logs/` directory for error details

### Q: I'm getting import errors. How do I fix this?
**A:** Ensure you're in the virtual environment:
```bash
# Activate venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

---

## License & Legal

### Q: What's the license?
**A:** MIT License—free for any use including:
- Commercial applications
- Academic research
- Government use
- Modifications and derivatives

See [LICENSE](LICENSE) for full text.

### Q: How do I cite PoliSim?
**A:** Use this citation:
```
PoliSim: Open-Source Fiscal Policy Simulator
GalacticOrgOfDev (2025-2026)
https://github.com/GalacticOrgOfDev/polisim
```

For academic papers, also cite our technical methodology paper (see [documentation/](documentation/)).

### Q: Can I use this for my thesis/research paper?
**A:** Yes! Many researchers use PoliSim for:
- Policy analysis
- Economic forecasting
- Healthcare reform studies
- Budget impact analysis

We can provide additional support for academic use—email us.

### Q: How do I report security issues?
**A:** See [SECURITY.md](SECURITY.md). DO NOT create public GitHub issues for security vulnerabilities. Email galacticorgofdev@gmail.com with:
- Description of vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

Response timeline:
- **24 hours:** Initial acknowledgment
- **48 hours:** Assessment complete
- **7 days:** Fix deployed

---

## Policy & Economics

### Q: What policies can I model?
**A:** PoliSim supports modeling:
- **Tax policy:** Income, payroll, corporate, capital gains, carbon taxes
- **Healthcare:** Medicare for All, public option, ACA expansion
- **Social Security:** Benefit changes, retirement age, COLA adjustments
- **Spending:** Discretionary, mandatory, infrastructure
- **Economic policy:** GDP impacts, interest rate scenarios

### Q: How do I model a specific bill (e.g., H.R. 1234)?
**A:** Options:
1. **Use policy builder:** Manually configure parameters to match bill text
2. **Upload PDF:** Our PDF parser extracts policy parameters (beta)
3. **Request addition:** Email us bill details—we can add as a scenario

### Q: Why don't my results match CBO's score?
**A:** Possible reasons:
- **Timing:** CBO may use more recent data
- **Assumptions:** Slightly different economic or behavioral assumptions
- **Scope:** CBO may include effects we don't model (e.g., macroeconomic feedback)
- **Methodology:** CBO has access to proprietary data and models

Check our reconciliation document for known variances.

### Q: Can I model state/local policies?
**A:** Currently, PoliSim focuses on **federal policy**. State/local integration is planned for future releases. You can approximate state impacts using custom parameters.

---

## Community & Support

### Q: How do I get help?
**A:** Resources:
1. **Documentation:** [docs/](docs/) and [documentation/](documentation/)
2. **GitHub Discussions:** Ask questions, share ideas
3. **GitHub Issues:** Report bugs, request features
4. **Email:** galacticorgofdev@gmail.com

### Q: Is there a user community?
**A:** Yes! Join us:
- **GitHub Discussions:** Project Q&A
- **Issue tracker:** Bug reports and features
- **Email list:** Announcements (low volume)

### Q: Can I request a feature?
**A:** Yes! Create a GitHub issue with:
- Feature description
- Use case (why you need it)
- Proposed solution (if you have ideas)

We review all feature requests and prioritize based on community need.

### Q: How often is PoliSim updated?
**A:** 
- **Data updates:** Monthly (automated)
- **Bug fixes:** As needed (usually within 1 week)
- **Feature releases:** Quarterly (major releases)
- **Phase milestones:** See [PHASES.md](documentation/PHASES.md)

---

## Questions Not Answered Here?

- Check [documentation/](documentation/) for detailed guides
- Ask on [GitHub Discussions](https://github.com/GalacticOrgOfDev/polisim/discussions)
- Email: galacticorgofdev@gmail.com

---

*Last updated: January 2, 2026*
