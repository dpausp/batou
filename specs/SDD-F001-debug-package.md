# SDD-F001: Debug Package Refactoring

**Status:** Design
**Feature:** F001 - Debug Package Refactoring
**Date:** 2026-02-07

---

## 1. Introduction

### 1.1 Purpose
This Software Design Document (SDD) describes the architectural refactoring of batou's debug features into a structured `src/batou/debug/` package. The refactoring extracts all debug-related functionality from scattered modules (`utils.py`, `remote_core.py`, `_settings.py`, `debug.py`, `check.py`) into a cohesive, testable package.

### 1.2 Scope
- Create `src/batou/debug/` package with modular structure
- Extract and reorganize debug features from existing modules
- Establish public API for debug functionality
- Ensure comprehensive test coverage for each module
- Maintain backward compatibility and behavior preservation

### 1.3 Design Goals
- **Separation of Concerns:** Debug features isolated in dedicated package
- **Testability:** Each module with independent test suite
- **Maintainability:** Clear module boundaries and responsibilities
- **Public API:** Clean, documented interface for debug features
- **Zero Functional Change:** Behavior-preserving refactoring

---

## 2. Architectural Overview

### 2.1 Current State
Debug features are scattered across multiple modules:
- `batou._settings.py`: `DebugSettings` class
- `batou.debug.py`: `batou debug` CLI command
- `batou.utils.py`: `Timer`, `TemplateStats`, `FileDescriptorTracker`
- `batou.remote_core.py`: Remote profiling logic, FD tracking hooks
- `batou.check.py`: Local consistency check command

### 2.2 Target Structure
```
src/batou/debug/
├── __init__.py           # Public API exports
├── settings.py           # DebugSettings class
├── cli.py                # batou debug CLI command
├── fd_tracker.py         # FileDescriptorTracker
├── profiling.py          # Remote profiling logic
├── template_stats.py     # TemplateStats
├── timer.py              # Timer class
└── tests/                # Debug-specific tests
    ├── __init__.py
    ├── test_settings.py
    ├── test_fd_tracker.py
    ├── test_cli.py
    ├── test_profiling.py
    ├── test_template_stats.py
    └── test_timer.py
```

### 2.3 Module Responsibilities

| Module | Responsibility | Source Location |
|--------|---------------|-----------------|
| `settings.py` | DebugSettings class with environment variable configuration | `_settings.py` |
| `cli.py` | `batou debug` command implementation | `debug.py` |
| `fd_tracker.py` | File descriptor tracking for leak detection | `utils.py`, `remote_core.py` |
| `profiling.py` | Remote profiling with cProfile integration | `remote_core.py` |
| `template_stats.py` | Template cache statistics tracking | `utils.py` |
| `timer.py` | Performance timing context manager | `utils.py` |

---

## 3. Module Design

### 3.1 Public API (`__init__.py`)

**D-001:** Export public debug API for external use

```python
# Public API exports
from batou.debug.settings import DebugSettings
from batou.debug.fd_tracker import FileDescriptorTracker
from batou.debug.profiling import RemoteProfiler
from batou.debug.template_stats import TemplateStats
from batou.utils import Timer

__all__ = [
    "DebugSettings",
    "FileDescriptorTracker",
    "RemoteProfiler",
    "TemplateStats",
    "Timer",
]
```

**Rationale:**
- Single import point for all debug features
- Explicit public API documentation
- Prevents accidental import of internals

---

### 3.2 Settings Module (`settings.py`)

**D-002:** DebugSettings class with Pydantic BaseSettings

**Functionality:**
- Environment variable configuration with `BATOU_` prefix
- Fields: `show_diff`, `show_secret_diffs`, `track_fds`, `profile`, `profile_lines`
- Type validation with Literal types
- `describe()` method returns structured settings information
- `show()` method displays active debug flags

**Public Interface:**
```python
class DebugSettings(BaseSettings):
    show_diff: Literal["full", "summary", "none"] = "full"
    show_secret_diffs: bool = False
    track_fds: Literal[0, 1, 2] = 0  # 0=disabled, 1=simple, 2=verbose
    profile: bool = False
    profile_lines: int = 30

    def describe(self) -> List[Dict[str, Any]]: ...
    def show(self) -> None: ...
```

**Migration Path:**
- Move `DebugSettings` from `batou._settings` to `batou.debug.settings`
- Maintain backward compatibility: `batou._settings.debug_settings` imports from new location
- Singleton pattern preserved

**Rationale:**
- Centralizes all debug configuration
- Clear environment variable mapping
- Type-safe settings validation

---

### 3.3 CLI Module (`cli.py`)

**D-003:** Typer-based CLI command for debug settings

**Functionality:**
- `batou debug` command displays all debug settings
- Rich table output with columns: Field Name, Environment Variable, Possible Values, Description, Current Value
- No-args-is-help pattern for discoverability

**Public Interface:**
```python
app = typer.Typer(no_args_is_help=True)

@app.command()
def main() -> None:
    """Display all available debug settings."""
```

**Migration Path:**
- Move content from `batou.debug` to `batou.debug.cli`
- CLI entry point remains `batou.debug` (backward compatible)
- Imports DebugSettings from new location

**Rationale:**
- Separates CLI logic from settings logic
- Allows CLI-specific testing
- Maintains `batou debug` command interface

---

### 3.4 FD Tracker Module (`fd_tracker.py`)

**D-004:** File descriptor tracking for leak detection

**Functionality:**
- Singleton pattern for global tracking
- Hooks `builtins.open()` for local tracking
- Installs remote hook via `gateway.remote_exec()`
- Tracks opens/closes with timestamps and stack traces
- Verbose mode with full stack traces
- Leak detection with configurable threshold (default: 200)
- Report generation to `/tmp/batou_fd_track_*.txt`

**Public Interface:**
```python
class FileDescriptorTracker:
    def __init__(self):
        self.enabled: bool  # From DebugSettings.track_fds
        self.verbose: bool  # track_fds == 2
        self.fd_records: Dict[str, Dict]
        self.total_opens: int
        self.total_closes: int
        self.remote_opens: Dict[str, int]
        self._open_fds: Dict[int, Tuple[str, str, str]]
        self._fd_tracking_logs: List[Tuple]

    @classmethod
    def get_instance(cls) -> FileDescriptorTracker: ...

    def install_local_hook(self) -> None: ...
    def install_remote_hook(self, gateway) -> None: ...
    def get_remote_logs(self, gateway) -> Optional[Dict]: ...
    def report(self, location: str, env_name: Optional[str] = None) -> None: ...
    def get_fd_tracking_stats(self) -> Dict: ...

    def _track_open(self, fd: int, path: str, mode: str = "r") -> None: ...
    def _track_close(self, fd: int) -> None: ...
```

**Migration Path:**
- Move `FileDescriptorTracker` from `batou.utils` to `batou.debug.fd_tracker`
- Extract remote FD tracking hooks from `batou.remote_core` into module
- Maintain backward compatibility: `batou.utils.FileDescriptorTracker` imports from new location
- Update `batou.remote_core` to use new module

**Rationale:**
- Concentrates FD tracking logic
- Enables comprehensive testing of tracking behavior
- Supports both local and remote tracking scenarios

---

### 3.5 Profiling Module (`profiling.py`)

**D-005:** Remote profiling with cProfile integration

**Functionality:**
- cProfile wrapper for remote execution
- Configurable output lines via `profile_lines` setting
- Statistics sorted by cumulative time
- Profile output to `/tmp/batou_remote_profile_*.txt`
- Retrieval of profiling results from remote hosts

**Public Interface:**
```python
class RemoteProfiler:
    def __init__(self, host_name: str, profile_lines: int = 30):
        self.host_name = host_name
        self.profile_lines = profile_lines

    def profile_execution(self, func: Callable) -> Any:
        """Execute function with profiling enabled."""
        ...

    def get_profiling_results(self) -> Optional[Dict[str, Any]]:
        """Retrieve profiling results from remote host."""
        ...

def enable_profiling(
    host_name: str,
    profile_lines: int,
    func: Callable
) -> Any:
    """Context-aware profiling wrapper."""
```

**Migration Path:**
- Extract profiling logic from `batou.remote_core.Deployment.load()`
- Move to `batou.debug.profiling`
- Update `batou.remote_core` to use new module
- Maintain profile output format and location

**Rationale:**
- Separates profiling concerns from deployment logic
- Enables isolated testing of profiling behavior
- Allows profiling as standalone feature

---

### 3.6 Template Stats Module (`template_stats.py`)

**D-006:** Template cache statistics tracking

**Functionality:**
- Singleton pattern for global collection
- Tracks cache hits, misses, and size
- Thread-safe statistics updates
- Human-readable output formatting
- Integration with remote execution output

**Public Interface:**
```python
class TemplateStats:
    def __init__(self):
        self.hits: int
        self.misses: int
        self.size: int

    def reset(self) -> None: ...
    def record_hit(self, count: int = 1) -> None: ...
    def record_miss(self, count: int = 1) -> None: ...
    def update_size(self, size: int) -> None: ...
    def get_stats(self) -> Dict[str, int]: ...
    def humanize(self) -> str: ...
```

**Migration Path:**
- Move `TemplateStats` from `batou.utils` to `batou.debug.template_stats`
- Maintain backward compatibility: `batou.utils.TemplateStats` imports from new location
- Update `batou.remote_core` to import from new location

**Rationale:**
- Encapsulates template cache statistics
- Enables focused testing of stats collection
- Separates stats logic from template rendering

---

### 3.7 Timer Module (`timer.py`)

**D-007:** Performance timing context manager

**Functionality:**
- Context manager for timing code blocks
- Accumulates durations by named steps
- Threshold-based slow operation detection
- Human-readable duration formatting

**Public Interface:**
```python
class Timer:
    def __init__(self, tag: Optional[str] = None):
        self.tag: Optional[str]
        self.durations: Dict[str, float]

    def step(self, note: str) -> TimerContext:
        """Create timing context for a step."""
        ...

    def above_threshold(self, **thresholds: float) -> Tuple[bool, List[str]]:
        """Check if any step exceeded threshold."""
        ...

    def humanize(self, *steps: str) -> str:
        """Format steps as human-readable duration string."""
        ...

class TimerContext:
    def __enter__(self) -> TimerContext: ...
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...
```

**Migration Path:**
- Move `Timer` from `batou.utils` to `batou.debug.timer`
- Maintain backward compatibility: `batou.utils.Timer` imports from new location
- Update `batou.check` to import from new location

**Rationale:**
- Concentrates timing functionality
- Enables comprehensive timing behavior testing
- Clear separation from utility functions

---

## 4. Test Design

### 4.1 Test Requirements

**D-008:** Each debug module requires comprehensive test coverage

| Module | Test File | Test Coverage Requirements |
|--------|-----------|---------------------------|
| `settings.py` | `test_settings.py` | Existing 460 lines, move to `debug/tests/` |
| `fd_tracker.py` | `test_fd_tracker.py` | Local/remote hook installation, leak detection, report generation |
| `cli.py` | `test_cli.py` | Existing 94 lines, move to `debug/tests/` |
| `profiling.py` | `test_profiling.py` | Profile execution, result retrieval, output format |
| `template_stats.py` | `test_template_stats.py` | Hit/miss tracking, size updates, singleton behavior |
| `timer.py` | `test_timer.py` | Context manager, step timing, thresholds, humanize |

### 4.2 Test Structure

```
src/batou/debug/tests/
├── __init__.py
├── test_settings.py      # (existing, move from tests/test_settings.py)
├── test_cli.py           # (existing, move from tests/test_debug.py)
├── test_fd_tracker.py    # (new)
├── test_profiling.py     # (new)
├── test_template_stats.py # (new)
└── test_timer.py         # (new)
```

### 4.3 Test Strategy

**D-009:** Test design principles for debug modules

1. **Unit Testing:** Test each module in isolation
2. **Mock Dependencies:** Use mocks for external dependencies (e.g., execnet gateway)
3. **Fixture Reuse:** Share fixtures across test modules (e.g., debug settings)
4. **Behavior Preservation:** Tests verify identical behavior to original implementation
5. **Coverage:** Minimum 80% line coverage per module

**Shared Fixtures:**
```python
# conftest.py for debug tests
@pytest.fixture
def debug_settings():
    """Provide DebugSettings instance for tests."""
    from batou.debug.settings import DebugSettings
    return DebugSettings()

@pytest.fixture
def mock_gateway():
    """Mock execnet gateway for remote tracking tests."""
    from unittest.mock import MagicMock
    gateway = MagicMock()
    gateway.remote_exec.return_value.receive.return_value = {}
    return gateway
```

---

## 5. Backward Compatibility

**NOTE:** Original specification included backward compatibility shims (D-010). These have been removed in favor of breaking the import pattern and migrating all code to new locations.

### 5.1 Behavioral Compatibility

**D-011:** Preserve existing behavior

- All debug settings environment variables remain unchanged
- `batou debug` command interface unchanged (new entry point: `batou debug.cli`)
- FD tracking behavior identical (verbose modes, thresholds)
- Profiling output format and location unchanged
- Template stats integration with remote output unchanged
- Timer interface and debug output unchanged

---

## 6. Implementation Sequence

**D-012:** Recommended implementation order to minimize risk

1. **Phase 1: Create Package Structure**
   - Create `src/batou/debug/` package
   - Add `__init__.py` with public API exports
   - Create test directory structure

2. **Phase 2: Move Settings Module**
   - Move `DebugSettings` to `settings.py`
   - Move `test_settings.py` to `debug/tests/`
   - Add backward compatibility shim in `_settings.py`
   - Verify all existing tests pass

3. **Phase 3: Move CLI Module**
   - Move CLI implementation to `cli.py`
   - Move `test_debug.py` to `debug/tests/test_cli.py`
   - Update `batou.debug.py` as entry point shim
   - Verify CLI command works

4. **Phase 4: Move Timer Module**
   - Move `Timer` to `timer.py`
   - Create `test_timer.py` with comprehensive tests
   - Add backward compatibility shim in `utils.py`
   - Verify timer usage in `check.py`

5. **Phase 5: Move TemplateStats Module**
   - Move `TemplateStats` to `template_stats.py`
   - Create `test_template_stats.py`
   - Add backward compatibility shim in `utils.py`
   - Verify stats output in `remote_core.py`

6. **Phase 6: Move FD Tracker Module**
   - Extract `FileDescriptorTracker` to `fd_tracker.py`
   - Extract remote FD hooks from `remote_core.py`
   - Create comprehensive `test_fd_tracker.py`
   - Add backward compatibility shim in `utils.py`
   - Update `remote_core.py` to use new module

7. **Phase 7: Move Profiling Module**
   - Extract profiling logic to `profiling.py`
   - Create `test_profiling.py`
   - Update `remote_core.py` to use new module
   - Verify profiling output and retrieval

8. **Phase 8: Cleanup**
   - Remove backward compatibility shims after verification
   - Update all internal imports to use new locations
   - Run full test suite
   - Update documentation

---

## 7. Dependencies and Constraints

### 7.1 External Dependencies
- `typer`: CLI framework (already used)
- `pydantic`: Settings validation (already used)
- `rich`: Table formatting (already used)

### 7.2 Internal Dependencies
- `batou._output`: Output system for debug messages
- `batou.settings`: Deployment settings integration
- `execnet`: Remote execution gateway (for FD tracking, profiling)

### 7.3 Constraints
- No new dependencies
- Must work with existing execnet remote execution model
- Maintain thread-safety for singleton instances
- Preserve performance characteristics (no measurable slowdown)

---

## 8. Open Questions and Risks

### 8.1 Open Questions

1. **FD Tracking Thread Safety:** Current implementation uses global state. Should FD tracker be thread-safe?

2. **TemplateStats Singleton:** Global singleton across environments may cause stats bleed. Should stats be per-deployment?

3. **Profiling Output Location:** Current output to `/tmp/`. Should this be configurable?

### 8.2 Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing imports | High | Backward compatibility shims, phased migration |
| FD tracking hooks interfere with production code | Medium | Comprehensive testing, feature flag control |
| Profiling overhead affects deployment performance | Low | Profiling already optional, overhead minimal |
| Test coverage gaps for new modules | Medium | Create comprehensive tests before moving code |

---

## 9. Verification Matrix

| Requirement | Module | Test | Implementation |
|-------------|--------|------|----------------|
| D-001: Public API | `__init__.py` | Import tests | Export all public classes |
| D-002: DebugSettings | `settings.py` | test_settings.py | Pydantic validation, describe(), show() |
| D-003: CLI command | `cli.py` | test_cli.py | Typer app, table output |
| D-004: FD tracking | `fd_tracker.py` | test_fd_tracker.py | Local/remote hooks, leak detection |
| D-005: Profiling | `profiling.py` | test_profiling.py | cProfile wrapper, result retrieval |
| D-006: Template stats | `template_stats.py` | test_template_stats.py | Hit/miss tracking, singleton |
| D-007: Timer | `timer.py` | test_timer.py | Context manager, thresholds |
| D-008: Test coverage | All modules | pytest --cov | 80%+ coverage per module |
| D-009: Test principles | All tests | Code review | Unit tests, mocks, fixtures |
| D-010: Backward compatibility | All modules | Import tests | Shim imports work |
| D-011: Behavioral preservation | All modules | Integration tests | Identical behavior |
| D-012: Implementation sequence | Migration | Phased rollout | 8 phases with verification |

---

## 10. References

- [CODEX Article 5: "Let It Crash" Principles](AGENTS.md#article-5-quality-is-non-negotiable)
- [Python Development Guidelines](AGENTS.md#python-development)
- [Batou Debug Skill](/Users/rovodev/.config/opencode/skill/batou-debug/SKILL.md)
- [IEEE 1016-2009: Recommended Practice for Software Design Descriptions](/Users/rovodev/.config/opencode/skill/spec-sdd-template/SKILL.md)

---

## Appendix A: Environment Variable Reference

| Variable | Type | Values | Default | Description |
|----------|------|--------|---------|-------------|
| `BATOU_SHOW_DIFF` | Literal | `"full"`, `"summary"`, `"none"` | `"full"` | Diff output verbosity |
| `BATOU_SHOW_SECRET_DIFFS` | bool | `true`, `false`, `1`, `0` | `false` | Show sensitive data diffs |
| `BATOU_TRACK_FDS` | Literal | `0`, `1`, `2` | `0` | FD tracking: disabled, simple, verbose |
| `BATOU_PROFILE` | bool | `true`, `false`, `1`, `0` | `false` | Enable remote profiling |
| `BATOU_PROFILE_LINES` | int | Positive integer | `30` | Profile output lines (negative = all) |

---

## Appendix B: Module Cross-Reference

| Original Location | New Location | Backward Shim |
|------------------|--------------|---------------|
| `batou._settings.DebugSettings` | `batou.debug.settings.DebugSettings` | `batou._settings.py` |
| `batou.debug` (CLI) | `batou.debug.cli.app` | `batou.debug.py` |
| `batou.utils.FileDescriptorTracker` | `batou.debug.fd_tracker.FileDescriptorTracker` | `batou.utils.py` |
| `batou.utils.TemplateStats` | `batou.debug.template_stats.TemplateStats` | `batou.utils.py` |
| `batou.utils.Timer` | `batou.debug.timer.Timer` | `batou.utils.py` |

---

**Document End**
