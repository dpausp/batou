---
spec_type: sdd
feature_id: F-004-templatestats-class
status: draft
date: 2026-02-03
---

# SDD: TemplateStats Class Refactoring

## 1. Introduction

### 1.1 Document Purpose
This Software Design Document (SDD) describes the refactoring of template cache statistics tracking from Environment class counters to a separate TemplateStats class in utils.py. The specification follows IEEE 1016 standards and provides prescriptive architecture for a behavior-preserving refactoring that improves code organization and reusability.

### 1.2 Subject Scope
This document covers the design of the TemplateStats class refactoring, including:
- Migration of template cache statistics from Environment class to TemplateStats class
- TemplateStats class following Timer pattern from utils.py
- Required methods: record_hit(), record_miss(), get_stats(), humanize()
- Integration points with Environment class and deploy module
- Behavior preservation: same stats output, same integration

The design assumes existing batou infrastructure (Timer class, Environment class, deploy module) and refactors template cache statistics tracking without changing any observable behavior.

### 1.3 Definitions
- **TemplateStats**: New class for tracking template cache statistics
- **Timer pattern**: Existing pattern in utils.py for tracking performance metrics
- **Template cache**: LRU cache for compiled Jinja2 templates
- **Hit/Miss**: Cache hit occurs when template is found in cache, miss when compilation is required
- **Behavior preservation**: Refactoring must not change observable system behavior

### 1.4 References
- IEEE Std 1016-2009: IEEE Recommended Practice for Software Design Descriptions
- batou source code: src/batou/environment.py, src/batou/utils.py, src/batou/deploy.py, src/batou/template.py
- Python 3 documentation: functools.lru_cache, dataclasses
- Timer class: src/batou/utils.py (lines 514-567) - Pattern reference

### 1.5 Overview
This document is organized as follows:
- Section 2: Design overview with stakeholder concerns and selected viewpoints
- Section 3: Design views covering relevant IEEE 1016 architectural viewpoints
- Section 4: Architectural decisions using MADR pattern
- Section 5: Appendixes with supporting information

Key design principles:
- **Behavior preservation principle**: No changes to observable output or behavior
- **Pattern consistency principle**: Follow existing Timer class pattern from utils.py
- **Separation of concerns principle**: Statistics tracking separated from Environment class
- **Minimal change principle**: Only refactor statistics tracking, no other changes
- **Test compatibility principle**: Existing tests continue to pass without modification

## 2. Design Overview

### 2.1 Stakeholder Concerns

| Stakeholder | Concerns | Priority | Addressed in View |
|-------------|----------|----------|-------------------|
| Developers | Cleaner code organization, reusable statistics class | High | Structure, Composition, Patterns |
| Maintainers | Easier to maintain, follows existing patterns | High | Structure, Patterns, Deployment |
| DevOps Engineers | No changes to deployment behavior or output | High | Interaction, Interface, Concurrency |
| CI/CD Pipelines | All existing tests continue to pass | High | Deployment, Test |
| End Users | Same template cache statistics output | High | Interface, Interaction |

### 2.2 Selected Viewpoints

Based on stakeholder concerns, the following viewpoints are most relevant:

| Viewpoint | Purpose | Stakeholder Coverage |
|-----------|---------|---------------------|
| Composition | Internal structure and component relationships | Maintainers, Developers |
| Interface | Public API of TemplateStats class | All stakeholders |
| Interaction | Statistics collection and reporting workflows | DevOps, Developers |
| Algorithm | Statistics tracking logic | Developers, Maintainers |
| State Dynamics | Statistics state lifecycle | Maintainers |
| Deployment | Integration with existing code | Maintainers, CI/CD |
| Decisions | Refactoring rationale | Maintainers |

## 3. Design Views

### 3.1 Composition View

#### Viewpoint
Composition viewpoint defines the internal structure and component relationships.

#### Representation

**Component Hierarchy**:

```
batou/
├── __init__.py                    [UNCHANGED]
│
├── utils.py                       [MODIFIED: Add TemplateStats class]
│   ├── Timer                      [EXISTING: Performance timing pattern]
│   ├── TemplateStats               [NEW: Template cache statistics]
│   │   ├── __init__()             # Initialize statistics counters
│   │   ├── record_hit()           # Record cache hit
│   │   ├── record_miss()          # Record cache miss
│   │   ├── get_stats()            # Get current statistics
│   │   └── humanize()            # Format statistics for display
│   │
│   └── [other utilities...]        [UNCHANGED]
│
├── environment.py                 [MODIFIED: Use TemplateStats]
│   ├── Environment                [MODIFIED: Replace counters with TemplateStats]
│   │   ├── __init__()             [MODIFIED: Initialize TemplateStats instance]
│   │   └── _collect_template_cache_stats()  [MODIFIED: Use TemplateStats methods]
│   │
│   └── [other Environment code...] [UNCHANGED]
│
├── deploy.py                      [MODIFIED: Update integration with TemplateStats]
│   ├── Deployment                 [MODIFIED: Call TemplateStats.get_stats()]
│   └── [other deploy code...]     [UNCHANGED]
│
├── template.py                    [UNCHANGED]
│   ├── TemplateEngine             [UNCHANGED: Existing get_cache_stats()]
│   └── [other template code...]    [UNCHANGED]
│
└── [other modules...]             [UNCHANGED]
```

**Component Responsibilities**:

| Component | Responsibility | Dependencies |
|-----------|----------------|---------------|
| `TemplateStats` | Track template cache statistics (hits, misses, size) | None (standalone utility class) |
| `Timer` | Pattern reference for TemplateStats implementation | None |
| `Environment` | Use TemplateStats to track template cache statistics | TemplateStats |
| `Deployment` | Report template cache statistics using TemplateStats | Environment, TemplateStats |
| `TemplateEngine` | Provide cache statistics (unchanged) | None |

**Data Flow**:

```
Deployment Initialization
   └─> Environment.__init__()
        └─> TemplateStats()

Deployment Execution
   └─> TemplateEngine.compile_template()
        ├─> Cache hit ──────────────────> TemplateStats.record_hit()
        └─> Cache miss ─────────────────> TemplateStats.record_miss()

Statistics Collection (before instance clear)
   └─> Environment._collect_template_cache_stats()
        ├─> TemplateEngine.get_cache_stats() for each component
        ├─> TemplateStats.record_hit() for accumulated hits
        └─> TemplateStats.record_miss() for accumulated misses

Deployment Completion
   └─> Deployment.deploy()
        └─> TemplateStats.get_stats() from Environment
             └─> TemplateStats.humanize() for display
```

**Interfaces**:

```python
# TemplateStats interface (new class in utils.py)
class TemplateStats:
    """Track template cache statistics following Timer pattern."""

    def __init__(self):
        """Initialize template cache statistics counters."""

    def record_hit(self):
        """Record a template cache hit event."""

    def record_miss(self):
        """Record a template cache miss event."""

    def update_size(self, size: int):
        """Update current cache size (maximum across all components)."""

    def get_stats(self) -> Dict[str, int]:
        """
        Return current statistics.

        Returns:
            Dict with keys: hits, misses, size
        """

    def humanize(self) -> str:
        """
        Format statistics for human-readable display.

        Returns:
            Formatted string with hits, misses, size, and hit rate
        """
```

**Traceability**: Addresses refactoring constraint 001 (TemplateStats class in utils.py), constraint 002 (behavior preservation), constraint 003 (Timer methods)

---

### 3.2 Interface View

#### Viewpoint
Interface viewpoint specifies system interfaces including APIs and protocols.

#### Representation

**TemplateStats Public Interface**:

```python
class TemplateStats:
    """
    Template cache statistics tracker following Timer pattern.

    Tracks template cache hits, misses, and size for deployment reporting.
    Follows the same design pattern as Timer class in utils.py.
    """

    def __init__(self):
        """
        Initialize template cache statistics counters.

        All counters start at zero.
        """

    def record_hit(self):
        """
        Record a template cache hit event.

        Increments the hits counter by 1.
        """

    def record_miss(self):
        """
        Record a template cache miss event.

        Increments the misses counter by 1.
        """

    def update_size(self, size: int):
        """
        Update current cache size.

        The cache size represents the maximum number of cached templates
        across all components (lru_cache currsize).

        Args:
            size: Current cache size (from lru_cache.currsize)
        """

    def get_stats(self) -> Dict[str, int]:
        """
        Return current statistics as a dictionary.

        Returns:
            Dictionary with keys:
            - hits: Total cache hits
            - misses: Total cache misses
            - size: Current cache size (maximum across all components)

        Example:
            >>> stats.get_stats()
            {'hits': 42, 'misses': 8, 'size': 10}
        """

    def humanize(self) -> str:
        """
        Format statistics for human-readable display.

        Returns formatted string with:
        - Total hits
        - Total misses
        - Cached template count
        - Hit rate percentage

        If no cache activity (hits + misses == 0), returns empty string.

        Returns:
            Human-readable statistics string.

        Example:
            >>> stats.humanize()
            'Template cache: 42 hits, 8 misses, 10 cached templates (84.0% hit rate)'
        """
```

**Environment Class Integration**:

```python
# Modified Environment class (environment.py)
class Environment(object):
    def __init__(self, name):
        # ... existing initialization ...

        # OLD CODE (to be removed):
        # self._template_cache_hits = 0
        # self._template_cache_misses = 0
        # self._template_cache_size = 0

        # NEW CODE:
        from batou.utils import TemplateStats
        self._template_stats = TemplateStats()

    def _collect_template_cache_stats(self):
        """
        Collect template cache statistics from all components.

        Uses TemplateStats instance to accumulate statistics.
        """
        for component in Component._instances:
            if hasattr(component, "_template_engine"):
                stats = component._template_engine.retrieve_cache_stats()
                # OLD CODE (to be removed):
                # self._template_cache_hits += stats["hits"]
                # self._template_cache_misses += stats["misses"]
                # self._template_cache_size = max(
                #     self._template_cache_size, stats["currsize"]
                # )

                # NEW CODE:
                self._template_stats.record_hit(stats["hits"])
                self._template_stats.record_miss(stats["misses"])
                self._template_stats.update_size(stats["currsize"])
```

**Deployment Module Integration**:

```python
# Modified Deployment class (deploy.py)
def deploy(self):
    # ... existing deployment code ...

    # Template cache statistics
    # OLD CODE (to be removed):
    # total_hits = self.environment._template_cache_hits
    # total_misses = self.environment._template_cache_misses
    # total_size = self.environment._template_cache_size

    # NEW CODE:
    stats = self.environment.template_stats.get_stats()
    total_hits = stats["hits"]
    total_misses = stats["misses"]
    total_size = stats["size"]

    if total_hits + total_misses > 0:
        hit_rate = 100 * total_hits / (total_hits + total_misses)
        output.annotate(
            f"Template cache: {total_hits} hits, {total_misses} misses, "
            f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
        )
```

**Behavior Preservation Constraints**:

The refactoring must preserve existing behavior:
1. **Output format**: Must match exactly: "Template cache: X hits, Y misses, Z cached templates (N% hit rate)"
2. **Hit rate calculation**: 100 * hits / (hits + misses)
3. **Statistics collection timing**: Before clearing component instances
4. **Size semantics**: Maximum currsize across all components
5. **Conditional output**: Only display if total_hits + total_misses > 0

**Traceability**: Addresses refactoring constraint 002 (behavior preservation), constraint 003 (Timer methods: record_hit, record_miss, get_stats, humanize)

---

### 3.3 Interaction View

#### Viewpoint
Interaction viewpoint describes dynamic behavior and workflows.

#### Representation

**Sequence Diagram: Template Statistics Tracking**:

```
Environment   TemplateStats   TemplateEngine   LRUCache
    │              │               │              │
    │ Init         │               │              │
    │ ────────────>│               │              │
    │              │ hits=0        │              │
    │              │ misses=0      │              │
    │              │ size=0        │              │
    │              │               │              │
    │              │               │              │
    │ Deployment starts              │              │
    │              │               │              │
    │              │               │ Compile template (cached)
    │              │               │ ────────────>│
    │              │               │ Cache hit
    │              │               │<─────────────│
    │              │               │              │
    │              │ Record hit   │              │
    │              │<─────────────│              │
    │              │ hits=1        │              │
    │              │               │              │
    │              │               │ Compile template (not cached)
    │              │               │ ────────────>│
    │              │               │ Cache miss
    │              │               │<─────────────│
    │              │               │              │
    │              │ Record miss  │              │
    │              │<─────────────│              │
    │              │ misses=1      │              │
    │              │               │              │
    │ Collect stats               │              │
    │              │               │              │
    │ ────────────>│ get_stats() from each component
    │              │               │ ────────────>│
    │              │               │ hits, misses, currsize
    │              │               │<─────────────│
    │              │               │              │
    │              │ record_hit()  │              │
    │              │ record_miss() │              │
    │              │ update_size() │              │
    │              │               │              │
    │              │               │ ... (repeat for each component)
    │              │               │              │
    │ Deployment ends               │              │
    │              │               │              │
    │ ────────────>│ get_stats()  │              │
    │<─────────────│ dict         │              │
    │              │               │              │
    │ ────────────>│ humanize()   │              │
    │<─────────────│ formatted    │              │
    │              │               │              │
    │ Output to user              │              │
    │ "Template cache: X hits, Y misses, Z cached templates (N% hit rate)"
```

**State Machine: TemplateStats Lifecycle**:

```
              [Uninitialized]
                       │
                       ▼
              TemplateStats.__init__()
                       │
                       ▼
              [Initialized]
                       │
                       ▼
           ┌───────────┴───────────┐
           │                       │
       record_hit()            record_miss()
           │                       │
           ▼                       ▼
    [hits incremented]     [misses incremented]
           │                       │
           └───────────┬───────────┘
                       │
                       ▼
              update_size()
                       │
                       ▼
          [size updated to max]
                       │
                       ▼
              get_stats()
                       │
                       ▼
         [Return statistics dict]
                       │
                       ▼
              humanize()
                       │
                       ▼
        [Return formatted string]
```

**Workflow: Template Statistics Collection and Reporting**:

```
1. Deployment Initialization
   ├─ Environment.__init__() creates TemplateStats instance
   └─ TemplateStats counters initialized to zero

2. Template Compilation (during deployment)
   ├─ TemplateEngine._compile_template() called
   ├─ Check lru_cache
   ├─ If cache hit:
   │   └─ TemplateStats.record_hit()
   └─ If cache miss:
       └─ TemplateStats.record_miss()

3. Statistics Collection (before instance clear)
   ├─ Environment._collect_template_cache_stats() called
   ├─ Iterate over all Component._instances
   ├─ For each component with _template_engine:
   │   ├─ Get cache stats: hits, misses, currsize
   │   ├─ TemplateStats.record_hit(hits) - accumulate
   │   ├─ TemplateStats.record_miss(misses) - accumulate
   │   └─ TemplateStats.update_size(currsize) - max
   └─ Statistics ready for reporting

4. Deployment Completion
   ├─ Get stats from TemplateStats.get_stats()
   ├─ Calculate hit rate: 100 * hits / (hits + misses)
   ├─ Format output using TemplateStats.humanize()
   └─ Display to user (if hits + misses > 0)
```

**Timer Pattern Comparison**:

```
Timer Class (existing pattern):
    __init__(tag=None)         → TemplateStats.__init__()
    step(note) context          → Not applicable (no context manager)
    durations (dict)           → hits, misses, size (counters)
    above_threshold(**kwargs)   → Not applicable
    humanize(*steps)           → TemplateStats.humanize()

TemplateStats (new class):
    __init__()                 → Same pattern: initialize counters
    record_hit()               → Timer equivalent: increment duration counter
    record_miss()              → Timer equivalent: increment duration counter
    update_size()              → Template-specific: track max size
    get_stats()                → Timer equivalent: access durations dict
    humanize()                 → Same pattern: format for display
```

**Traceability**: Addresses refactoring constraint 002 (behavior preservation), constraint 003 (Timer methods: record_hit, record_miss, get_stats, humanize)

---

### 3.4 Algorithm View

#### Viewpoint
Algorithm viewpoint describes key algorithms and their complexity.

#### Representation

**Algorithm: record_hit()**

```
RECORD_HIT(stats)
    """Increment template cache hit counter."""
    stats.hits += 1
```

**Complexity**: O(1) time, O(1) space

---

**Algorithm: record_miss()**

```
RECORD_MISS(stats)
    """Increment template cache miss counter."""
    stats.misses += 1
```

**Complexity**: O(1) time, O(1) space

---

**Algorithm: update_size()**

```
UPDATE_SIZE(stats, size)
    """Update cache size to maximum of current and new size."""
    if size > stats.size:
        stats.size = size
```

**Complexity**: O(1) time, O(1) space

---

**Algorithm: get_stats()**

```
GET_STATS(stats)
    """Return current statistics as dictionary."""
    return {
        'hits': stats.hits,
        'misses': stats.misses,
        'size': stats.size
    }
```

**Complexity**: O(1) time, O(1) space

---

**Algorithm: humanize()**

```
HUMANIZE(stats)
    """Format statistics for human-readable display."""
    total_hits = stats.hits
    total_misses = stats.misses
    total_size = stats.size

    # Only display if there was cache activity
    if total_hits + total_misses == 0:
        return ""

    # Calculate hit rate
    hit_rate = 100 * total_hits / (total_hits + total_misses)

    # Format output (MUST match existing format exactly)
    return (
        f"Template cache: {total_hits} hits, {total_misses} misses, "
        f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
    )
```

**Complexity**: O(1) time, O(1) space

---

**Algorithm: _collect_template_cache_stats() (Environment)**

```
COLLECT_TEMPLATE_CACHE_STATS(environment)
    """Collect template cache statistics from all components."""
    for component in Component._instances:
        if hasattr(component, "_template_engine"):
            engine_stats = component._template_engine.get_cache_stats()
            # Accumulate hits and misses
            environment._template_stats.record_hit(engine_stats["hits"])
            environment._template_stats.record_miss(engine_stats["misses"])
            # Track maximum cache size
            environment._template_stats.update_size(engine_stats["currsize"])
```

**Complexity**: O(N) time, O(1) space, where N = number of components with template engines

---

**Complexity Analysis**:

| Algorithm | Time Complexity | Space Complexity | Notes |
|-----------|-----------------|------------------|-------|
| record_hit() | O(1) | O(1) | Simple counter increment |
| record_miss() | O(1) | O(1) | Simple counter increment |
| update_size() | O(1) | O(1) | Max comparison |
| get_stats() | O(1) | O(1) | Dictionary construction |
| humanize() | O(1) | O(1) | String formatting |
| _collect_template_cache_stats() | O(N) | O(1) | N = number of components |

**Traceability**: Addresses refactoring constraint 003 (Timer methods: record_hit, record_miss, get_stats, humanize)

---

### 3.5 State Dynamics View

#### Viewpoint
State dynamics viewpoint describes system state transitions.

#### Representation

**TemplateStats States**:

```
State: UNINITIALIZED
  Entry: TemplateStats class defined but not instantiated
  Events:
    - __init__() -> INITIALIZED
  Exit: None

State: INITIALIZED
  Entry: TemplateStats.__init__() called
  Events:
    - record_hit() -> [hits += 1]
    - record_miss() -> [misses += 1]
    - update_size() -> [size = max(size, new_size)]
    - get_stats() -> [Return statistics dict]
    - humanize() -> [Return formatted string]
  Exit: None
```

**Counter State Transitions**:

```
hits counter (integer):
  0 ──record_hit()──> 1 ──record_hit()──> 2 ──record_hit()──> 3 ──> ...
  (monotonically increasing during deployment)

misses counter (integer):
  0 ──record_miss()──> 1 ──record_miss()──> 2 ──record_miss()──> 3 ──> ...
  (monotonically increasing during deployment)

size counter (integer):
  0 ──update_size(10)──> 10 ──update_size(5)──> 10 ──update_size(15)──> 15
  (maximum value, can increase or stay same, never decreases)
```

**TemplateStats Lifecycle**:

```
Environment Initialization
  └─> TemplateStats.__init__()
       └─> INITIALIZED (hits=0, misses=0, size=0)
            └─> Deployment execution
                 ├─> Template cache hit events
                 │   └─> record_hit()
                 │       └─> hits counter increments
                 ├─> Template cache miss events
                 │   └─> record_miss()
                 │       └─> misses counter increments
                 ├─> Cache size updates
                 │   └─> update_size()
                 │       └─> size counter tracks max
                 └─> Deployment completion
                      ├─> get_stats()
                      │   └─> Return current counters
                      └─> humanize()
                           └─> Format and display
```

**State Invariants**:

1. **Counter non-negativity**: hits >= 0, misses >= 0, size >= 0
2. **Monotonic counters**: hits and misses only increase during deployment
3. **Maximum size semantics**: size is always the maximum currvalue seen
4. **Total activity**: hits + misses = total template compilation attempts
5. **Hit rate**: 0% <= hit_rate <= 100% (when total > 0)

**Error State**:

```
Normal Operation:
  - All counter operations succeed
  - get_stats() always returns valid dictionary
  - humanize() always returns valid string (possibly empty)

No Error Conditions:
  - No invalid inputs possible (record_hit/miss take no arguments)
  - No resource constraints (counters are integers)
  - No dependencies on external state
```

**Traceability**: Addresses refactoring constraint 002 (behavior preservation - state invariants maintained)

---

### 3.6 Deployment View

#### Viewpoint
Deployment viewpoint describes installation and deployment aspects.

#### Representation

**Installation**:

The TemplateStats class is added to existing batou package:

1. **Module location**: `src/batou/utils.py` (new class at end of file)
2. **No new dependencies**: Uses only Python stdlib (no imports needed)
3. **No configuration required**: Internal utility class
4. **No entry point changes**: Class instantiated by Environment only

**Integration Points**:

```python
# Location 1: TemplateStats class definition (src/batou/utils.py)
# Add after Timer class (line 567+)

class TemplateStats:
    """Track template cache statistics following Timer pattern."""
    # ... implementation ...


# Location 2: Environment.__init__() (src/batou/environment.py, line 164)
# Replace existing counter initialization with TemplateStats

from batou.utils import TemplateStats


class Environment(object):
    def __init__(self, name):
        # ... existing code ...
        self._template_stats = TemplateStats()


# Location 3: Environment._collect_template_cache_stats() (src/batou/environment.py, line 600)
# Update to use TemplateStats methods

def _collect_template_cache_stats(self):
    """Collect template cache statistics from all components."""
    for component in Component._instances:
        if hasattr(component, "_template_engine"):
            stats = component._template_engine.retrieve_cache_stats()
            self.template_stats.record_hit(stats["hits"])
            self.template_stats.record_miss(stats["misses"])
            self.template_stats.update_size(stats["currsize"])


# Location 4: Deployment.deploy() (src/batou/deploy.py, line 446)
# Update to use TemplateStats.get_stats()

def deploy(self):
    # ... existing deployment code ...

    # Template cache statistics
    stats = self.environment.template_stats.get_stats()
    total_hits = stats["hits"]
    total_misses = stats["misses"]
    total_size = stats["size"]

    if total_hits + total_misses > 0:
        hit_rate = 100 * total_hits / (total_hits + total_misses)
        output.annotate(
            f"Template cache: {total_hits} hits, {total_misses} misses, "
            f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
        )
```

**Backward Compatibility**:

1. **No changes to public API**:
   - Environment class external interface unchanged
   - Deployment class external interface unchanged
   - Command-line behavior unchanged

2. **No changes to observable behavior**:
   - Template cache statistics output format unchanged
   - Statistics calculation logic unchanged
   - Collection timing unchanged (before instance clear)

3. **No breaking changes**:
   - All existing deployments work without modification
   - Existing tests continue to pass
   - No migration path needed

**Testing Strategy**:

```bash
# Unit tests for TemplateStats class
pytest src/batou/tests/test_utils.py::test_template_stats

# Integration tests for Environment integration
pytest src/batou/tests/test_environment.py::test_template_stats_collection

# Regression tests for deploy output
pytest src/batou/tests/test_deploy.py::test_template_cache_stats_output

# Manual verification
./batou deploy dev
# Expected output (example):
# Template cache: 42 hits, 8 misses, 10 cached templates (84.0% hit rate)
```

**Verification Steps**:

1. **Verify TemplateStats implementation**:
   - All four methods implemented: record_hit, record_miss, get_stats, humanize
   - Methods follow Timer pattern (similar design philosophy)
   - Class location: src/batou/utils.py

2. **Verify Environment integration**:
   - __init__() creates TemplateStats instance
   - _collect_template_cache_stats() uses TemplateStats methods
   - Old counter variables removed

3. **Verify Deployment integration**:
   - deploy() uses TemplateStats.get_stats()
   - Output format matches existing: "Template cache: X hits, Y misses, Z cached templates (N% hit rate)"
   - Conditional display: only if hits + misses > 0

4. **Verify behavior preservation**:
   - Output identical to pre-refactoring
   - Statistics calculation identical
   - Collection timing identical

**Traceability**: Addresses refactoring constraint 001 (TemplateStats in utils.py), constraint 002 (behavior preservation - same integration points), constraint 003 (Timer methods)

---

## 4. Decisions

### 4.1 Architecture Decision: Separate TemplateStats Class in utils.py

**Status**: Accepted

**Context**:
Current implementation stores template cache statistics as three separate counter attributes in the Environment class:
- `_template_cache_hits`
- `_template_cache_misses`
- `_template_cache_size`

This approach mixes statistics tracking concerns with Environment class responsibilities, making the code harder to test, reuse, and maintain. Similar statistics classes (e.g., Timer) already exist in utils.py, establishing a pattern for separating utility classes from core domain logic.

**Decision**:
Create a separate `TemplateStats` class in `src/batou/utils.py` following the Timer class pattern. The class will encapsulate template cache statistics tracking with four methods: `record_hit()`, `record_miss()`, `get_stats()`, and `humanize()`.

**Consequences**:

**Positive**:
- **Separation of concerns**: Statistics tracking logic isolated from Environment class
- **Reusability**: TemplateStats can be reused elsewhere if needed
- **Testability**: TemplateStats can be tested independently without Environment
- **Consistency**: Follows existing Timer class pattern in utils.py
- **Maintainability**: Statistics logic is easier to understand and modify

**Negative**:
- **Slightly more code**: Additional class definition (minimal impact)
- **Indirect access**: Statistics accessed through TemplateStats instance vs. direct attributes (minor inconvenience)

**Neutral**:
- **No performance impact**: Counter operations are O(1) regardless of implementation
- **No behavioral change**: Refactoring preserves exact same output and behavior

**Alternatives Considered**:

1. **Keep existing counters in Environment** (rejected)
   - Rationale: Doesn't improve code organization or testability
   - Pros: No code changes needed
   - Cons: Violates single responsibility principle, harder to test

2. **Create TemplateStats in environment.py** (rejected)
   - Rationale: Doesn't leverage existing utils.py pattern
   - Pros: Keeps statistics near usage in Environment
   - Cons: Doesn't follow Timer pattern, clutters environment.py

3. **Merge into Timer class** (rejected)
   - Rationale: Timer is for timing metrics, TemplateStats is for cache statistics
   - Pros: Reduces number of utility classes
   - Cons: Violates single responsibility principle, Timer becomes confusing

**Traceability**: Addresses refactoring constraint 001 (separate class in utils.py)

---

### 4.2 Architecture Decision: Follow Timer Class Pattern

**Status**: Accepted

**Context**:
The Timer class in utils.py (lines 514-567) establishes a pattern for tracking metrics in batou. Key pattern elements:
- Simple counter-based tracking (durations dict with defaultdict)
- Methods for recording metrics (step context manager)
- Methods for retrieving metrics (implicitly via durations attribute)
- Methods for formatting output (humanize)

Timer pattern is well-established, tested, and understood by developers. Following this pattern ensures consistency and reduces learning curve.

**Decision**:
TemplateStats class should follow Timer class pattern with these adaptations:
- Use simple integer counters (not defaultdict, as we have fixed metrics)
- Explicit methods for recording metrics (record_hit, record_miss) instead of context manager
- get_stats() method for retrieving current statistics (similar to accessing durations dict)
- humanize() method for formatted output (same as Timer.humanize)

**Consequences**:

**Positive**:
- **Consistency**: Follows existing pattern, easier for developers to understand
- **Familiarity**: Developers familiar with Timer will immediately understand TemplateStats
- **Testability**: Similar testing approach as Timer
- **Documentation**: Timer pattern serves as precedent for TemplateStats usage

**Negative**:
- **Minor adaptation needed**: TemplateStats doesn't need defaultdict (fixed metrics), but pattern still applies conceptually
- **No context manager**: TemplateStats doesn't use context manager like Timer.step() (not applicable for simple counters)

**Neutral**:
- **Implementation details**: Internal structure differs (counters vs. dict) but public interface follows same pattern

**Alternatives Considered**:

1. **Use dict-based storage like Timer** (rejected)
   - Rationale: Overkill for fixed three metrics (hits, misses, size)
   - Pros: More flexible if new metrics added later
   - Cons: More complex than needed, no clear benefit

2. **Use dataclass** (rejected)
   - Rationale: Doesn't follow Timer pattern
   - Pros: Automatic __init__, __repr__, etc.
   - Cons: Doesn't match Timer pattern, less consistent with existing code

3. **Custom unique pattern** (rejected)
   - Rationale: Inconsistent with existing code
   - Pros: Can optimize for specific use case
   - Cons: Increases cognitive load, harder to maintain

**Traceability**: Addresses refactoring constraint 003 (Timer pattern requirement)

---

### 4.3 Architecture Decision: Preserve Exact Behavior

**Status**: Accepted

**Context**:
This is a refactoring task (not a feature addition), which means behavior must be preserved. Current behavior:
1. Output format: `"Template cache: X hits, Y misses, Z cached templates (N% hit rate)"`
2. Hit rate calculation: `100 * hits / (hits + misses)`
3. Collection timing: Before clearing component instances
4. Size semantics: Maximum currsize across all components
5. Conditional display: Only if total_hits + total_misses > 0

Any deviation from this behavior would be a breaking change and violate the refactoring principle.

**Decision**:
TemplateStats implementation must preserve exact existing behavior. The refactoring only changes code structure (counters moved to separate class), not observable behavior. All existing tests must pass without modification.

**Consequences**:

**Positive**:
- **No breaking changes**: Existing deployments continue to work
- **No test changes**: All existing tests pass without modification
- **Predictable output**: Users see exact same output as before
- **Easy rollback**: Can revert if issues arise

**Negative**:
- **Constrained design**: Cannot improve output format or add new features (must wait for feature request)
- **Less flexibility**: Must implement exactly matching logic

**Neutral**:
- **Implementation focus**: Refactoring is purely about code structure, not new capabilities

**Behavior Preservation Checklist**:

- [x] Output format must match exactly: `"Template cache: {hits} hits, {misses} misses, {size} cached templates ({hit_rate:.1f}% hit rate)"`
- [x] Hit rate calculation must be: `100 * hits / (hits + misses)`
- [x] Size must be: Maximum currsize across all components
- [x] Conditional display: Only when `hits + misses > 0`
- [x] Collection timing: Before `Component._instances` is cleared
- [x] Hit rate format: One decimal place with `%` suffix

**Alternatives Considered**:

1. **Improve output format** (rejected)
   - Rationale: Not a refactoring, would be a feature change
   - Pros: Better user experience
   - Cons: Breaking change, violates refactoring principle

2. **Add new metrics** (rejected)
   - Rationale: Not a refactoring, would be a feature addition
   - Pros: More information for users
   - Cons: Breaking change, violates refactoring principle

3. **Change collection timing** (rejected)
   - Rationale: Not a refactoring, would change behavior
   - Pros: Could collect at different point in deployment
   - Cons: Breaking change, violates refactoring principle

**Traceability**: Addresses refactoring constraint 002 (behavior preservation)

---

## 5. Appendixes

### 5.1 Code Comparison: Before and After

#### Before Refactoring (Current Implementation):

```python
# src/batou/environment.py (lines 161-164)
class Environment(object):
    def __init__(self, name):
        # ... existing code ...
        # Template cache statistics
        self._template_cache_hits = 0
        self._template_cache_misses = 0
        self._template_cache_size = 0


# src/batou/environment.py (lines 600-609)
def _collect_template_cache_stats(self):
    """Collect template cache statistics from all components."""
    for component in Component._instances:
        if hasattr(component, "_template_engine"):
            stats = component._template_engine.retrieve_cache_stats()
            self._template_cache_hits += stats["hits"]
            self._template_cache_misses += stats["misses"]
            self._template_cache_size = max(
                self._template_cache_size, stats["currsize"]
            )


# src/batou/deploy.py (lines 445-455)
# Template cache statistics
total_hits = self.environment._template_cache_hits
total_misses = self.environment._template_cache_misses
total_size = self.environment._template_cache_size

if total_hits + total_misses > 0:
    hit_rate = 100 * total_hits / (total_hits + total_misses)
    output.annotate(
        f"Template cache: {total_hits} hits, {total_misses} misses, "
        f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
    )
```

#### After Refactoring:

```python
# src/batou/utils.py (new class)
class TemplateStats:
    """Track template cache statistics following Timer pattern."""

    def __init__(self):
        """Initialize template cache statistics counters."""
        self.hits = 0
        self.misses = 0
        self.size = 0

    def record_hit(self, count: int = 1):
        """Record template cache hit(s)."""
        self.hits += count

    def record_miss(self, count: int = 1):
        """Record template cache miss(es)."""
        self.misses += count

    def update_size(self, size: int):
        """Update cache size to maximum of current and new size."""
        if size > self.size:
            self.size = size

    def get_stats(self) -> Dict[str, int]:
        """Return current statistics as dictionary."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'size': self.size
        }

    def humanize(self) -> str:
        """Format statistics for human-readable display."""
        if self.hits + self.misses == 0:
            return ""
        hit_rate = 100 * self.hits / (self.hits + self.misses)
        return (
            f"Template cache: {self.hits} hits, {self.misses} misses, "
            f"{self.size} cached templates ({hit_rate:.1f}% hit rate)"
        )


# src/batou/environment.py (refactored)
class Environment(object):
    def __init__(self, name):
        # ... existing code ...
        # Template cache statistics
        from batou.utils import TemplateStats
        self._template_stats = TemplateStats()


def _collect_template_cache_stats(self):
    """Collect template cache statistics from all components."""
    for component in Component._instances:
        if hasattr(component, "_template_engine"):
            stats = component._template_engine.retrieve_cache_stats()
            self.template_stats.record_hit(stats["hits"])
            self.template_stats.record_miss(stats["misses"])
            self.template_stats.update_size(stats["currsize"])


# src/batou/deploy.py (refactored)
# Template cache statistics
stats = self.environment.template_stats.get_stats()
total_hits = stats["hits"]
total_misses = stats["misses"]
total_size = stats["size"]

if total_hits + total_misses > 0:
    hit_rate = 100 * total_hits / (total_hits + total_misses)
    output.annotate(
        f"Template cache: {total_hits} hits, {total_misses} misses, "
        f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
    )
```

---

### 5.2 Test Examples

#### Unit Tests for TemplateStats:

```python
# src/batou/tests/test_utils.py
import pytest
from batou.utils import TemplateStats


def test_template_stats_initialization():
    """TemplateStats initializes with zero counters."""
    stats = TemplateStats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.size == 0


def test_template_stats_record_hit():
    """record_hit increments hits counter."""
    stats = TemplateStats()
    stats.record_hit()
    assert stats.hits == 1
    stats.record_hit()
    assert stats.hits == 2
    assert stats.misses == 0  # Unchanged


def test_template_stats_record_miss():
    """record_miss increments misses counter."""
    stats = TemplateStats()
    stats.record_miss()
    assert stats.misses == 1
    stats.record_miss()
    assert stats.misses == 2
    assert stats.hits == 0  # Unchanged


def test_template_stats_record_hit_multiple():
    """record_hit can record multiple hits at once."""
    stats = TemplateStats()
    stats.record_hit(5)
    assert stats.hits == 5


def test_template_stats_record_miss_multiple():
    """record_miss can record multiple misses at once."""
    stats = TemplateStats()
    stats.record_miss(3)
    assert stats.misses == 3


def test_template_stats_update_size():
    """update_size tracks maximum size."""
    stats = TemplateStats()
    stats.update_size(10)
    assert stats.size == 10
    stats.update_size(5)  # Smaller, no change
    assert stats.size == 10
    stats.update_size(15)  # Larger, update
    assert stats.size == 15


def test_template_stats_get_stats():
    """get_stats returns dictionary with current counters."""
    stats = TemplateStats()
    stats.record_hit(5)
    stats.record_miss(3)
    stats.update_size(10)

    result = stats.get_stats()
    assert result == {
        'hits': 5,
        'misses': 3,
        'size': 10
    }


def test_template_stats_humanize_with_activity():
    """humanize returns formatted string when there is cache activity."""
    stats = TemplateStats()
    stats.record_hit(42)
    stats.record_miss(8)
    stats.update_size(10)

    result = stats.humanize()
    assert result == "Template cache: 42 hits, 8 misses, 10 cached templates (84.0% hit rate)"


def test_template_stats_humanize_no_activity():
    """humanize returns empty string when there is no cache activity."""
    stats = TemplateStats()
    result = stats.humanize()
    assert result == ""


def test_template_stats_humanize_hit_rate_formatting():
    """humanize formats hit rate with one decimal place."""
    stats = TemplateStats()
    stats.record_hit(33)
    stats.record_miss(67)

    result = stats.humanize()
    assert "33.0% hit rate" in result


def test_template_stats_follows_timer_pattern():
    """TemplateStats follows Timer class pattern."""
    # Like Timer, TemplateStats has methods for recording and retrieving metrics
    stats = TemplateStats()
    stats.record_hit()  # Like Timer.step() context
    result = stats.get_stats()  # Like accessing Timer.durations
    formatted = stats.humanize()  # Like Timer.humanize()

    assert isinstance(result, dict)
    assert isinstance(formatted, str)
```

---

### 5.3 Verification Checklist

#### Implementation Verification:

- [ ] TemplateStats class created in `src/batou/utils.py`
- [ ] TemplateStats has `__init__()` method
- [ ] TemplateStats has `record_hit()` method
- [ ] TemplateStats has `record_miss()` method
- [ ] TemplateStats has `get_stats()` method
- [ ] TemplateStats has `humanize()` method
- [ ] TemplateStats follows Timer class pattern

#### Integration Verification:

- [ ] Environment.__init__() creates TemplateStats instance
- [ ] Environment._collect_template_cache_stats() uses TemplateStats methods
- [ ] Old counter variables removed from Environment class
- [ ] Deployment.deploy() uses TemplateStats.get_stats()
- [ ] Output format matches existing: "Template cache: X hits, Y misses, Z cached templates (N% hit rate)"

#### Behavior Preservation Verification:

- [ ] Template cache statistics output identical to pre-refactoring
- [ ] Hit rate calculation identical: 100 * hits / (hits + misses)
- [ ] Size semantics identical: maximum currsize across components
- [ ] Conditional display identical: only when hits + misses > 0
- [ ] Collection timing identical: before clearing component instances

#### Test Verification:

- [ ] Unit tests for TemplateStats pass
- [ ] Integration tests for Environment pass
- [ ] Regression tests for Deployment pass
- [ ] All existing tests continue to pass without modification

#### Documentation Verification:

- [ ] TemplateStats class has docstring
- [ ] All methods have docstrings
- [ ] Docstrings follow existing code style
- [ ] No changes to external documentation needed (internal refactoring)

---

### 5.4 Glossary

- **Template cache**: LRU cache storing compiled Jinja2 templates to avoid repeated compilation
- **Cache hit**: Template found in cache, no compilation needed
- **Cache miss**: Template not found in cache, requires compilation
- **Hit rate**: Percentage of cache hits: 100 * hits / (hits + misses)
- **LRU cache**: Least Recently Used cache (functools.lru_cache)
- **Timer pattern**: Design pattern established by Timer class for tracking metrics
- **Behavior preservation**: Refactoring principle requiring no changes to observable behavior
- **Refactoring**: Code structure improvement without changing behavior

---

### 5.5 Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-02-03 | SPEC Agent | Initial SDD for TemplateStats refactoring |
