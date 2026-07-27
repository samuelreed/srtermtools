# Add targeted tests

Add or update tests for a behavior change in one tool.

Requirements:
- Use `unittest`
- Keep tests deterministic (prefer local fixtures/server over external network)
- Assert stdout/stderr and exit code for CLI behavior where relevant
- Name test files `*_test.py`

Validation:
- Run specific changed tests first, then full suite
