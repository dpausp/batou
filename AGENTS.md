# Project-Specific Dev Guide for Agents

Tools are configured in @pyproject.toml, read it!

## Before Commit
- `uv run tox p` MUST pass (includes ruff, ty, tests)
- ruff may auto-fix code - review changes before committing!

## Code Style

### Type Hints
- Type stubs (.pyi) go to `stubs/` directory
- Types in implementation code ONLY if external libraries need it (pydantic, typer, dataclasses)
- Type stubs should use modern Python 3.14+ syntax, modernize existing old-style type hints
- No `from __future__ import annotations`

## Project-Specific Constraints

### Project Structure
- Tests and implementation both live in `src/`

### Bootstrap Requirement
`src/batou/__init__.py` must not import non-stdlib at module level (self-bootstrapping).
Exception: jinja2

### RPC / Remote Methods
Methods in `remote_core.py` can be called remotely via `host.rpc.method_name()` using execnet channels.
All arguments and return values MUST be pickle-serializable (no file handles, no local objects, no closures).
Exceptions are caught remotely and re-raised locally as RuntimeError with generic message.
Output from remote execution is sent back via channel and displayed locally.
Remote methods execute in isolated Python process on target host - no shared state with local deployment.
Debugging RPC issues: check pickle serialization, remote exception tracebacks in deployment logs.

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

### Secrets Testing
- GPG/Age fixtures: `src/batou/secrets/tests/fixture/`
- Environment auto-set by conftest.py
