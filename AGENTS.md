# Development Guide for Agents

## Build, Lint, and Test Commands

### Testing
```bash
# Run all tests
pytest

# Run single test (most common usage)
pytest src/batou/tests/test_file.py::test_function_name

# Run tests in specific module
pytest src/batou/tests/test_file.py

# Run tests with verbose output
pytest -v

# Run tests marked as slow
pytest -m slow

# Skip slow tests
pytest -m "not slow"
```

### Multi-Python Version Testing
```bash
# Run tests across all Python versions (uses tox)
tox

# Run tests for specific Python version
tox -e py311

# Run linters and formatters
tox -e pre-commit
```

### Pre-commit Hooks (Linting & Formatting)
```bash
# Run all linters on all files
pre-commit run --all-files --show-diff-on-failure

# Install pre-commit hooks (runs automatically before commits)
pre-commit install

# Run specific hook
pre-commit run black --files src/batou/deploy.py
```

## Code Style Guidelines

### Formatting
- Line length: **80 characters** (strictly enforced by black)
- Use **black** for formatting (auto-runs via pre-commit)
- Use **isort** for import sorting with black profile

### Import Style
```python
# Standard library imports first
import os

# Third-party imports second
import execnet

# Local imports last (use relative imports within package)
from batou import DeploymentError, output
from .environment import Environment

# Group multiple imports from same module when >2 items
from batou import (ConfigurationError, ReportingException)
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `Deployment`, `RemoteHost`)
- **Functions/Methods**: `snake_case` (e.g., `deploy_component`)
- **Variables**: `snake_case` (e.g., `host_name`)
- **Private members**: `_leading_underscore` (e.g., `_name`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `REMOTE_OS_ENV_KEYS`)
- **Exceptions**: `ClassNameError` or `ClassNameException`

### Type Hints
- Type hints are **optional** - use when it improves clarity
- Import from `typing` module: `List`, `Optional`, `Dict`, `Set`
- Simple return type hints: `def git_main_branch() -> str:`
- No `from __future__ import annotations`

### Error Handling Patterns
```python
# Base exception for all reporting errors
class ReportingException(Exception):
    def report(self):
        """Custom error reporting logic"""

# Specific exceptions inherit from ReportingException
class ConfigurationError(ReportingException):
    pass

# Silent errors for internal handling (no user-facing output)
class SilentConfigurationError(Exception):
    pass

# Check and raise exceptions
if not self.connections:
    raise ConfigurationError.from_context("No host found.")
```

### Component Lifecycle Pattern
```python
class MyComponent(Component):
    def configure(self):
        """Called multiple times. No side effects. Declarative only."""
        self += File("path", content="data")

    def verify(self):
        """Called once. Check state. Raise UpdateNeeded() if wrong."""
        if not self.path.exists():
            raise batou.UpdateNeeded()

    def update(self):
        """Called once if verify() raised UpdateNeeded(). Apply changes."""
        self.path.write("data")
```

### Testing Patterns
```python
import pytest

# Autouse fixtures apply to all tests in scope
@pytest.fixture(autouse=True)
def setup_environment(monkeypatch):
    monkeypatch.setitem(os.environ, "KEY", "value")

# Test naming: test_<functionality>
def test_decrypt_with_valid_key(encrypted_file):
    with GPGEncryptedFile(encrypted_file) as secret:
        assert secret.cleartext == expected_value

# Exception testing
def test_missing_key_raises_error():
    with pytest.raises(batou.GPGCallError):
        function_that_raises()
```

### Code Patterns
- Prefer `object` as base class: `class Host(object):`
- Use `execnet` for remote execution (SSH, vagrant)
- Lock files prevent concurrent deployments: `.batou-lock`
- Output through `output` module: `output.step()`, `output.line()`

## Important Notes

- **Coverage enabled** with `--cov=src --cov-report=html`
- **45s timeout** for all tests (`--timeout=45`)
- **Instafail enabled** for fast failure feedback
- **Native traceback** (`--tb=native`)
- **Python 3.10-3.14** supported
- **Bootstrap requirement**: Self-bootstrapping without non-stdlib imports in `batou/__init__.py`

## Test File Locations
- Main tests: `src/batou/tests/test_*.py`
- Component tests: `src/batou/component/tests/`
- Secret tests: `src/batou/secrets/tests/test_*.py`
- Fixtures: `src/batou/conftest.py`, `src/batou/secrets/tests/fixture/`
