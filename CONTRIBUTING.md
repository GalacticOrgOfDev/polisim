# Contributing to PoliSim

We welcome contributions! This guide explains how to report bugs, suggest features, and submit code changes.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork:**
   ```bash
   git clone https://github.com/YOUR-USERNAME/polisim.git
   cd polisim
   ```
3. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
4. **Install development dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```
5. **Run tests to verify setup:**
   ```bash
   python -m pytest tests/ -v
   ```

## Reporting Bugs

### Before Reporting
- Check existing issues (might already be reported)
- Check closed issues (might be fixed in main branch)
- Verify you're using the latest version

### How to Report

Create an issue using the **Bug Report** template:

```
Title: [BUG] Brief description of issue

## Description
What's the problem? What did you expect to happen?

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen?

## Actual Behavior
What actually happened?

## Environment
- OS: (Windows/macOS/Linux)
- Python version: (e.g., 3.11)
- PoliSim version: (e.g., main branch)

## Error Messages
(Paste full traceback if applicable)
```

## Suggesting Features

Create an issue using the **Feature Request** template:

```
Title: [FEATURE] Brief description of feature

## Description
What feature would help you?

## Use Case
Why do you need this? What problem does it solve?

## Proposed Solution
How would this feature work?

## Alternatives Considered
Any other ways to solve this?
```

## Code Style Guidelines

We follow PEP 8 with these conventions:

### 1. Type Hints (Required)
```python
# ✅ Good
def simulate(
    policy: HealthcarePolicyModel,
    years: int = 22,
) -> pd.DataFrame:
    """Run policy simulation."""
    pass

# ❌ Bad
def simulate(policy, years=22):
    pass
```

### 2. Docstrings (Required)
```python
def calculate_coverage(
    spending: float,
    population: int,
) -> float:
    """
    Calculate healthcare coverage percentage.
    
    Args:
        spending: Total healthcare spending (billions)
        population: Total population
        
    Returns:
        Coverage percentage (0-1)
    """
    return min(1.0, spending / (population * 0.01))
```

### 3. Naming Conventions
- Functions & variables: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### 4. Testing (Required)
- Write test for every new function
- Use descriptive test names: `test_calculate_coverage_valid_inputs()`
- Aim for 80%+ code coverage

```python
def test_calculate_coverage_returns_percentage():
    """Verify coverage is returned as percentage."""
    coverage = calculate_coverage(spending=100, population=1000)
    assert 0 <= coverage <= 1
```

### 5. Linting
```bash
# Format code
black src/

# Check style
pylint src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

## Development Workflow

### 1. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
```

Branch naming:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions

### 2. Make Changes
- Write code + tests
- Ensure tests pass: `pytest tests/ -v`
- Ensure code style: `black . && pylint .`

### 3. Commit with Descriptive Message
```
Format: [TYPE] Brief summary (max 50 chars)

[TYPE] can be: FEATURE, FIX, DOCS, REFACTOR, TEST, PERF

Examples:
✅ [FEATURE] Add sensitivity analysis endpoint
✅ [FIX] Resolve division by zero in healthcare simulation
✅ [DOCS] Update CBO data integration guide
✅ [TEST] Add validation tests for edge cases
```

### 4. Push & Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with this template:
```
## Description
What does this PR do?

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
How was this tested?
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guide
- [ ] Type hints added
- [ ] Tests written
- [ ] Documentation updated
- [ ] No breaking changes
```

## Code Review Expectations

- **Response Time:** Within 48 hours
- **Feedback:** Constructive, specific, respectful
- **Approval:** At least 1 maintainer approval required
- **Changes:** Push additional commits to same branch (don't force push)

## Commit Checklist

Before submitting a PR, ensure:
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Code formatted: `black .`
- [ ] Type hints complete: `mypy .`
- [ ] Docstrings present
- [ ] No secrets committed (check .env, config files)
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)

## Areas Where We Need Help

We especially welcome contributions in these areas:

### 1. Healthcare Modeling
- Improve cost elasticity models
- Add state-level healthcare analysis
- Enhance quality metrics

### 2. Tax Policy
- Additional tax policy scenarios
- International tax comparisons
- State/local tax integration

### 3. Economic Forecasting
- Improved GDP growth models
- Better recession probability forecasting
- Labor market integration

### 4. Testing & Validation
- Edge case testing
- Performance testing
- Integration testing

### 5. Documentation
- Tutorial notebooks
- Video walkthroughs
- Translation to other languages

### 6. Data Integration
- Additional data sources (BLS, Fed, etc.)
- Real-time data updates
- Historical data validation

## Community Guidelines

### Be Respectful
- Be patient with new contributors
- Provide constructive feedback
- Assume good intentions
- Celebrate others' contributions

### Be Professional
- Keep discussions on-topic
- Avoid personal attacks
- Respect differing opinions
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)

### Be Helpful
- Answer questions when you can
- Share knowledge generously
- Help others learn
- Welcome newcomers

## Getting Help

- **Documentation:** Check [docs/](docs/) and [documentation/](documentation/)
- **GitHub Discussions:** Ask questions and share ideas
- **Email:** galacticorgofdev@gmail.com
- **Security Issues:** See [SECURITY.md](SECURITY.md)

## Recognition

Contributors are recognized in:
- GitHub contributors page
- CONTRIBUTORS.md file
- Release notes (for significant contributions)
- Research paper acknowledgments (for validation work)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to PoliSim! 🎉
