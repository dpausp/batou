# Development Guide for Agents

## Development Environment Setup

### Using uv (recommended)
```bash
./develop.sh [python version]  # Defaults to 3.14
source .venv/bin/activate
# Or: uv run pytest, uv run batou deploy dev
```

### Manual Setup
```bash
uv venv --python 3.14
uv sync --all-extras --all-groups
```

## Build, Lint, and Test Commands

### Testing
```bash
pytest                                          # Run all tests
pytest src/batou/tests/test_file.py::test_func  # Run single test (most common)
pytest src/batou/tests/test_file.py::TestClass  # Run test class
pytest src/batou/tests/test_file.py             # Run tests in file
pytest -m slow                                  # Only slow tests
pytest -m "not slow"                            # Skip slow tests
pytest -m "not debug"                           # Default (excludes debug)
pytest --cov=src --cov-report=html              # With coverage
pytest -n auto                                  # Parallel execution
```

### Multi-Python Version Testing
```bash
tox                    # All Python versions (3.10-3.14)
tox -e py312          # Specific version
tox -e pre-commit     # Linters only
```

### Linting & Formatting
```bash
pre-commit run --all-files --show-diff-on-failure  # Run all hooks
pre-commit install                                  # Auto-run before commits
ruff check src/       # Lint
ruff format src/      # Format
ruff check --fix src/ # Auto-fix
```

## Code Style Guidelines

### Formatting
- **Line length**: 80 characters (enforced by ruff)
- **Formatter**: ruff format (black-compatible)
- **Import sorting**: ruff (isort-compatible)
- **Target Python**: 3.10+ (modern type hint syntax)

### Import Organization
```python
# Standard library imports first
import os
import sys
from pathlib import Path

# Third-party imports second
import execnet
import pytest
from pydantic import BaseModel

# Local imports last (relative imports within package)
from batou import DeploymentError, output
from .environment import Environment
```

### Naming Conventions
- **Classes**: `PascalCase` (`Deployment`, `RemoteHost`)
- **Functions/Methods**: `snake_case` (`deploy_component`)
- **Variables**: `snake_case` (`host_name`)
- **Private members**: `_leading_underscore` (`_name`)
- **Constants**: `UPPER_SNAKE_CASE` (`REMOTE_OS_ENV_KEYS`)
- **Exceptions**: `*Exception` or `*Error` suffix (`ConfigurationError`, `ReportingException`)

### Type Hints
- Optional but encouraged
- Use Python 3.10+ syntax: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- Simple return hints: `def git_main_branch() -> str:`
- No `from __future__ import annotations`

### Error Handling
```python
# Base exception for user-facing errors
class ReportingException(Exception):
    def report(self):
        """Custom error reporting with context"""

# Specific exceptions inherit from ReportingException
class ConfigurationError(ReportingException):
    pass

# Silent errors (no user output)
class SilentConfigurationError(Exception):
    pass

# Raise with context
if not self.connections:
    raise ConfigurationError.from_context("No host found.")
```

### Component Lifecycle
```python
class MyComponent(Component):
    def configure(self):
        """Called multiple times. Declarative only. No side effects."""
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

# Autouse fixtures for environment setup
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

# Use tmp_path for temporary directories
def test_file_operations(tmp_path):
    config_file = tmp_path / "config.cfg"
    config_file.write_text("[section]\nkey = value")
```

## Important Constraints

### Bootstrap Requirement
- `src/batou/__init__.py` must **not** import non-stdlib modules at module level
- Required for self-bootstrapping without dependencies
- Only stdlib imports: `importlib.metadata`, `os`, `socket`, `traceback`, etc.
- Exception: `import jinja2` (required for template loading)

### Python Version Support
- **Minimum**: Python 3.10
- **Tested**: 3.10, 3.11, 3.12, 3.13, 3.14
- **Default dev**: Python 3.14

### Test Configuration
- **Timeout**: 120s per test
- **Coverage**: Required, branch coverage enabled
- **Warnings**: Treated as errors (`-W error`)
- **Traceback**: Native format (`--tb=native`)
- **Parallel**: xdist enabled (use `-n auto`)

## Project Structure

### Source Code
- Main package: `src/batou/`
- Entry points: `src/batou/main.py`, `src/batou/batommel/__init__.py`
- Components: `src/batou/component.py`, `src/batou/lib/`
- Secrets: `src/batou/secrets/`

### Test Locations
- Main tests: `src/batou/tests/test_*.py`
- Component tests: `src/batou/component/tests/`
- Secret tests: `src/batou/secrets/tests/test_*.py`
- Fixtures: `src/batou/conftest.py`, `src/batou/secrets/tests/fixture/`

### Configuration Files
- `pyproject.toml`: Project metadata, dependencies, tool configs
- `uv.lock`: Dependency lockfile
- `.pre-commit-config.yaml`: Git hooks configuration

## Secrets & Encryption

### Test Fixture Secrets
- GPG home: `src/batou/secrets/tests/fixture/gnupg/`
- Age keys: `src/batou/secrets/tests/fixture/age/`
- Re-encrypt fixtures: `./re-encrypt-fixture-secrets.sh`

### Environment Variables (auto-set by conftest.py)
- `GNUPGHOME`: GPG home directory
- `BATOU_AGE_IDENTITIES`: Age identity file
- `GIT_CONFIG_GLOBAL`: Isolated git config

## Development Workflow

### Before Committing
```bash
pytest                                    # Run tests
pre-commit run --all-files               # Run linters
# OR: git commit (auto-runs hooks if installed)
```

### Release Process
```bash
./changelog.sh      # Create changelog entry
./release-this.sh   # Run full release (must be on main)
```

### Common Commands
```bash
uv run batou deploy dev              # Deploy locally
uv run batou check dev               # Fast local validation
uv run ./update-appenv-lockfiles.py  # Update example lockfiles
```
