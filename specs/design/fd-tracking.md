---
spec_type: sdd
feature_id: F-002-fd-tracking
status: draft
date: 2026-01-26
---

# SDD: File Descriptor Tracking System

## 1. Introduction

### 1.1 Document Purpose
This Software Design Document (SDD) describes the architecture and design for the file descriptor tracking system in batou. The specification follows IEEE 1016 standards and provides prescriptive architecture for implementing the diagnostic feature for identifying file descriptor leaks.

### 1.2 Subject Scope
This document covers the design of the file descriptor tracking system, including:
- Environment variable-based opt-in control
- Local file descriptor tracking mechanism
- Remote file descriptor tracking via execnet hooks
- Per-file open count recording
- Optional stack trace capture
- Statistics aggregation and output
- Integration with existing batou infrastructure

The design assumes existing batou infrastructure (execnet, Timer, output module) and extends it with new tracking capabilities while maintaining full backward compatibility and zero overhead when disabled.

### 1.3 Definitions
- **FDTracker**: Main class managing file descriptor tracking
- **Execnet hook**: Code executed in remote execnet subprocesses
- **FDRecord**: Data structure storing file descriptor information
- **Tracking level**: Basic tracking (1) vs. stack trace tracking (2)
- **Interceptor**: Code that intercepts file descriptor operations
- **Aggregator**: Component that combines local and remote statistics

### 1.4 References
- IEEE Std 1016-2009: IEEE Recommended Practice for Software Design Descriptions
- SRS: specs/requirements/fd-tracking.md (Software Requirements Specification)
- batou source code: src/batou/*.py (Existing implementation)
- Python 3 documentation: File descriptor handling, trace module
- Execnet documentation: Hook mechanism and remote execution

### 1.5 Overview
This document is organized as follows:
- Section 2: Design overview with stakeholder concerns and selected viewpoints
- Section 3: Design views covering 15 IEEE 1016 architectural viewpoints
- Section 4: Architectural decisions using MADR pattern
- Section 5: Appendixes with supporting information

Key design principles:
- **Opt-in principle**: Tracking is only active when explicitly enabled
- **Zero-overhead principle**: No performance impact when disabled
- **Isolation principle**: Tracking code is isolated and non-intrusive
- **Reuse principle**: Leverages existing batou infrastructure
- **Consistency principle**: Follows existing patterns (e.g., BATOU_PROFILE_REMOTE)

## 2. Design Overview

### 2.1 Stakeholder Concerns

| Stakeholder | Concerns | Priority | Addressed in View |
|-------------|----------|----------|-------------------|
| DevOps Engineers | Accurate FD leak detection | High | Interface, Algorithm, State Dynamics |
| Developers | Minimal code changes, easy debugging | High | Structure, Deployment, Patterns |
| CI/CD Pipelines | No performance impact on production | High | Resource, Performance, Concurrency |
| Maintainers | Code maintainability, testability | Medium | Composition, Dependency, Structure |
| End Users | Clear output, easy to understand | Medium | Interface, Interaction |

### 2.2 Selected Viewpoints

Based on stakeholder concerns, the following viewpoints are most relevant:

| Viewpoint | Purpose | Stakeholder Coverage |
|-----------|---------|---------------------|
| Context | System boundaries and interactions | All stakeholders |
| Composition | Internal structure and components | Maintainers, Developers |
| Interface | Environment variable and output interfaces | DevOps, CI/CD |
| Interaction | User workflows and tracking lifecycle | DevOps, Developers |
| Algorithm | FD tracking and aggregation logic | Maintainers, Developers |
| State Dynamics | Tracking state and lifecycle | Maintainers |
| Performance | Overhead minimization strategies | CI/CD, Developers |
| Deployment | Integration with existing batou | Maintainers |
| Decisions | Architectural rationale | Maintainers |

## 3. Design Views

### 3.1 Context View

#### Viewpoint
Context viewpoint defines the system boundaries and interactions with external entities.

#### Representation

**System Boundary**:
```
┌─────────────────────────────────────────────────────────────┐
│              File Descriptor Tracking System                 │
├─────────────────────────────────────────────────────────────┤
│  - Check BATOU_TRACK_FDS environment variable              │
│  - Track local FD operations (open/close)                  │
│  - Inject tracking code into remote execnet processes       │
│  - Aggregate statistics from all processes                  │
│  - Output statistics to temporary files                    │
└─────────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │  BATOU_  │  │  POSIX   │  │  Execnet │  │  /tmp/    │
   │  TRACK_  │  │  FD API  │  │  Remote  │  │  Files   │
   │  FDS     │  │          │  │  Hooks   │  │          │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

**External Entities**:

| Entity | Type | Interaction | Protocol |
|--------|------|------------|----------|
| BATOU_TRACK_FDS env var | Configuration | Enable/disable tracking | Environment variable |
| BATOU_TRACK_FDS_VERBOSE env var | Configuration | Enable verbose FD logging | Environment variable |
| POSIX FD API | System API | Intercept open/close operations | Python file/socket/pipe operations |
| Execnet | Remote execution | Inject tracking code | Execnet hook API |
| /tmp directory | File system | Write statistics output | File I/O (/tmp/batou_fd_track_*.txt) |
| Timer class | Existing infrastructure | Measure tracking overhead | Timer.step() context |
| Output module | Existing infrastructure | Debug messages | output.annotate() |

**Interaction Flows**:

1. **Initialization**:
   - Check BATOU_TRACK_FDS environment variable
   - Parse tracking level (1 for basic, 2 for stack traces)
   - Initialize FDTracker if enabled

2. **Local Tracking**:
   - Intercept open operations (open, socket, pipe, etc.)
   - Intercept close operations
   - Record FD statistics locally

3. **Remote Tracking**:
   - Register execnet hook before remote execution
   - Inject tracking code into remote subprocesses
   - Remote subprocesses track FD operations

4. **Aggregation**:
   - Collect statistics from local process
   - Collect statistics from remote processes
   - Merge statistics into unified report

5. **Output**:
   - Write local statistics to /tmp/batou_fd_track_<pid>.txt
   - Write remote statistics to /tmp/batou_fd_track_remote_<pid>.txt
   - Include timestamp, process info, and optional stack traces

**Constraints**:
- Tracking only active when BATOU_TRACK_FDS is set
- Zero overhead when disabled (no interception, no hooks)
- Temporary files only created when tracking is enabled
- Stack traces only captured when tracking level is "2"

**Traceability**: Addresses SRS requirements REQ-INTF-001, REQ-INTF-002, REQ-FUNC-002-001, REQ-FUNC-002-002, REQ-FUNC-002-007

---

### 3.2 Composition View

#### Viewpoint
Composition viewpoint defines the internal structure and component relationships.

#### Representation

**Component Hierarchy**:

```
batou/
├── __init__.py                    [MODIFIED: Export FDTracker if enabled]
│
├── fd_tracking.py                 [NEW: File descriptor tracking module]
│   ├── FDTracker                  [NEW: Main tracking manager]
│   │   ├── __init__()           # Initialize tracker
│   │   ├── is_enabled()          # Check if tracking enabled
│   │   ├── get_tracking_level()  # Get tracking level (1 or 2)
│   │   ├── track_open()          # Record FD open
│   │   ├── track_close()         # Record FD close
│   │   ├── get_statistics()      # Get FD statistics
│   │   └── write_report()       # Write statistics to file
│   │
│   ├── FDRecord                   [NEW: FD data structure]
│   │   ├── fd_number            # FD integer value
│   │   ├── open_count           # Number of times opened
│   │   ├── stack_traces         # List of stack traces (optional)
│   │   └── is_leaked()         # Check if FD is leaked
│   │
│   ├── Interceptor                [NEW: Intercept FD operations]
│   │   ├── install_hooks()      # Install interception hooks
│   │   ├── uninstall_hooks()     # Remove interception hooks
│   │   ├── intercept_open()     # Intercept open operations
│   │   └── intercept_close()    # Intercept close operations
│   │
│   ├── RemoteTracker              [NEW: Remote process tracking]
│   │   ├── create_hook_code()   # Create tracking hook code
│   │   ├── register_execnet_hook()  # Register with execnet
│   │   └── merge_remote_stats()  # Merge remote statistics
│   │
│   └── StatisticsAggregator       [NEW: Aggregate statistics]
│       ├── aggregate_local()     # Aggregate local statistics
│       ├── aggregate_remote()    # Aggregate remote statistics
│       └── format_report()      # Format output report
│
├── deploy.py                      [MODIFIED: Initialize FDTracker]
├── remote_core.py                 [MODIFIED: Register execnet hook]
├── host.py                        [UNCHANGED]
├── component.py                    [UNCHANGED]
├── utils.py                       [MINOR CHANGE: Add tracking to Timer]
└── _output.py                     [UNCHANGED]
```

**Component Responsibilities**:

| Component | Responsibility | Dependencies |
|-----------|----------------|---------------|
| `FDTracker` | Main tracking coordinator, statistics management | FDRecord, Interceptor, StatisticsAggregator |
| `FDRecord` | Store FD information with open count and optional stack traces | None |
| `Interceptor` | Intercept FD operations (open/close) in current process | FDTracker, FDRecord |
| `RemoteTracker` | Manage tracking in remote execnet subprocesses | FDTracker, execnet API |
| `StatisticsAggregator` | Aggregate and format statistics for output | FDRecord, FDTracker |

**Data Flow**:

```
Deployment Start
   └─> Check BATOU_TRACK_FDS environment variable
        ├─> If disabled: No tracking, zero overhead
        └─> If enabled:
             └─> FDTracker.initialize()
                  ├─> Interceptor.install_hooks()
                  ├─> RemoteTracker.register_execnet_hook()
                  └─> Timer.step("fd_tracking_init")
               
Deployment Execution
   └─> FD operations occur
        ├─> Local: Interceptor intercepts open/close
        │    └─> FDTracker.track_open()/track_close()
        └─> Remote: Execnet hook intercepts FD operations
             └─> Remote tracking code runs in remote process

Deployment End
   └─> FDTracker.write_report()
        ├─> StatisticsAggregator.aggregate_local()
        ├─> StatisticsAggregator.aggregate_remote()
        ├─> StatisticsAggregator.format_report()
        └─> Write to /tmp/batou_fd_track_*.txt
```

**Interfaces**:

```python
# FDTracker interface
class FDTracker:
    def __init__(self):
        """Initialize FD tracker, check environment variable."""

    @property
    def is_enabled(self) -> bool:
        """Return True if tracking is enabled."""

    @property
    def tracking_level(self) -> int:
        """Return tracking level (1 for basic, 2 for stack traces)."""

    def track_open(self, fd: int, path: str, mode: str, stack_trace: Optional[str] = None):
        """Record file descriptor open event."""

    def track_close(self, fd: int, path: Optional[str] = None, mode: Optional[str] = None):
        """Record file descriptor close event."""

    def get_statistics(self) -> Dict[int, FDRecord]:
        """Return current FD statistics."""

    def write_report(self, filepath: str):
        """Write statistics report to file."""

    def get_leaked_fds(self, threshold: int = 200) -> List[Tuple[int, str, str, str]]:
        """Return list of leaked FDs exceeding threshold."""

# FDRecord interface
@dataclass
class FDRecord:
    fd_number: int
    open_count: int
    close_count: int
    stack_traces: List[str]  # Optional, only at level 2
    modes: Dict[str, int]  # Mode counts: {"r": 5, "w": 3, "a+": 2}
    open_time: Optional[str]  # Timestamp of first open

    @property
    def is_leaked(self) -> bool:
        """Check if FD is potentially leaked (open_count > close_count)."""

# Interceptor interface
class Interceptor:
    def install_hooks(self):
        """Install interception hooks for FD operations."""

    def uninstall_hooks(self):
        """Remove interception hooks."""

# RemoteTracker interface
class RemoteTracker:
    def create_hook_code(self) -> str:
        """Create tracking hook code for execnet injection."""

    def register_execnet_hook(self):
        """Register tracking hook with execnet."""

    def merge_remote_stats(self, remote_stats: Dict[int, FDRecord]):
        """Merge remote process statistics into main tracker."""

    def get_remote_statistics(self) -> Dict[str, Any]:
        """Get aggregated remote statistics including total_opens, total_closes, open_fds."""

# StatisticsAggregator interface
class StatisticsAggregator:
    def aggregate_local(self, tracker: FDTracker) -> Dict[str, Any]:
        """Aggregate local process statistics."""

    def aggregate_remote(self, trackers: List[FDTracker]) -> Dict[str, Any]:
        """Aggregate remote process statistics."""

    def format_report(self, stats: Dict[str, Any]) -> str:
        """Format statistics as human-readable report."""

    def check_leak_threshold(self, open_fds: int, threshold: int = 200) -> bool:
        """Check if open FD count exceeds threshold."""

    def format_leaked_fds(self, leaked: List[Tuple[int, str, str, str]], limit: int = 10) -> List[str]:
        """Format leaked FD details for output."""
```

**Traceability**: Addresses SRS requirements REQ-FUNC-002-001 through REQ-FUNC-002-006, REQ-DES-002-001, REQ-DES-002-003

---

### 3.3 Logical View

#### Viewpoint
Logical viewpoint describes the functional decomposition and data structures.

#### Representation

**Logical Components**:

```
┌────────────────────────────────────────────────────────────┐
│                    FDTracker (Main)                      │
├────────────────────────────────────────────────────────────┤
│  Tracking coordinator and statistics manager             │
│  - Check BATOU_TRACK_FDS environment variable           │
│  - Manage tracking lifecycle (init/track/report)        │
│  - Delegate to Interceptor and RemoteTracker            │
└────────────────────────────────────────────────────────────┘
                           │
                           ├─────────────────┬──────────────────┐
                           ▼                 ▼                  ▼
┌──────────────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│    Interceptor       │ │  RemoteTracker  │ │ StatisticsAggregator │
├──────────────────────┤ ├─────────────────┤ ├─────────────────────┤
│  Local FD tracking   │ │ Remote tracking │ │  Report generation  │
│  - Install hooks    │ │ - Execnet hooks │ │  - Format data      │
│  - Intercept opens  │ │ - Merge stats   │ │  - Write to file    │
│  - Intercept closes │ │                │ │                     │
└──────────────────────┘ └─────────────────┘ └─────────────────────┘
         │
         ▼
┌──────────────────────┐
│     FDRecord        │
├──────────────────────┤
│  FD data structure  │
│  - fd_number       │
│  - open_count      │
│  - stack_traces    │
│  - is_leaked()     │
└──────────────────────┘
```

**Data Structures**:

```python
# FD record with open/close counts, modes, and optional stack traces
@dataclass
class FDRecord:
    fd_number: int
    open_count: int = 0
    close_count: int = 0
    stack_traces: List[str] = field(default_factory=list)
    modes: Dict[str, int] = field(default_factory=dict)
    open_time: Optional[str] = None

    def increment(self, stack_trace: Optional[str] = None, mode: str = "r"):
        """Increment open count, optionally record stack trace and mode."""
        self.open_count += 1
        if stack_trace:
            self.stack_traces.append(stack_trace)
        if mode:
            self.modes[mode] = self.modes.get(mode, 0) + 1
        if self.open_time is None:
            import datetime
            self.open_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    def decrement(self):
        """Decrement open count and increment close count."""
        if self.open_count > 0:
            self.open_count -= 1
        self.close_count += 1

    @property
    def is_leaked(self) -> bool:
        """Check if FD is potentially leaked."""
        return self.open_count > self.close_count


# Tracking configuration
@dataclass
class TrackingConfig:
    enabled: bool = False
    level: int = 1  # 1 for basic, 2 for stack traces
    verbose: bool = False
    leak_threshold: int = 200
    output_dir: str = "/tmp"


# Remote statistics structure
@dataclass
class RemoteStatistics:
    total_opens: int = 0
    total_closes: int = 0
    open_fds: int = 0
    fd_leak: bool = False
    leaked_fds: List[Tuple[int, str, str, str]] = field(default_factory=list)  # (fd, path, mode, open_time)
    logs: List[Tuple[str, int, str, str, str]] = field(default_factory=list)  # (now, total_opens, path, mode, action)


# Statistics report
@dataclass
class StatisticsReport:
    timestamp: str
    process_id: int
    host: str
    is_remote: bool = False
    fd_records: Dict[int, FDRecord] = field(default_factory=dict)
    total_opens: int = 0
    total_closes: int = 0

    @property
    def active_fds(self) -> int:
        """Count of currently open FDs."""
        return sum(1 for record in self.fd_records.values() if record.is_leaked)

    @property
    def leaked_fds(self) -> List[int]:
        """List of potentially leaked FD numbers."""
        return [fd for fd, record in self.fd_records.items() if record.is_leaked]


# Global tracker instance (singleton pattern)
_tracker: Optional[FDTracker] = None

def get_tracker() -> Optional[FDTracker]:
    """Get global FD tracker instance."""
    return _tracker

def initialize_tracker() -> Optional[FDTracker]:
    """Initialize global FD tracker if enabled."""
    global _tracker
    if _tracker is None:
        _tracker = FDTracker()
    return _tracker
```

**Tracking Logic Flow**:

```
1. Initialization (deployment start)
   ├─ Check BATOU_TRACK_FDS environment variable
   ├─ Parse tracking level (1 or 2)
   ├─ Create FDTracker instance if enabled
   ├─ Install Interceptor hooks
   └─ Register RemoteTracker execnet hook

2. FD Open Event
   ├─ Interceptor intercepts open operation
   ├─ Extract FD number from return value
   ├─ If tracking level 2: Capture stack trace
   ├─ FDTracker.track_open(fd, stack_trace)
   └─ FDRecord.increment(open_count)

3. FD Close Event
   ├─ Interceptor intercepts close operation
   ├─ Extract FD number from argument
   ├─ FDTracker.track_close(fd)
   └─ FDRecord.decrement(open_count)

4. Remote FD Events
   ├─ Execnet hook intercepts FD operations in remote process
   ├─ Remote tracker records FD events locally
   ├─ Remote stats serialized and sent back
   └─ RemoteTracker.merge_remote_stats(remote_stats)

5. Report Generation (deployment end)
   ├─ Collect all FD records
   ├─ Calculate statistics (opens, closes, leaks)
   ├─ Format report with human-readable output
   ├─ Include stack traces if tracking level 2
   └─ Write to /tmp/batou_fd_track_<pid>.txt
```

**Traceability**: Addresses SRS requirements REQ-FUNC-002-003, REQ-FUNC-002-004, REQ-FUNC-002-005, REQ-FUNC-002-006

---

### 3.4 Interface View

#### Viewpoint
Interface viewpoint specifies system interfaces including APIs and protocols.

#### Representation

**Environment Variable Interface**:

```bash
# Disable tracking (default)
unset BATOU_TRACK_FDS

# Enable basic tracking (no stack traces)
export BATOU_TRACK_FDS=1

# Enable stack trace tracking
export BATOU_TRACK_FDS=2
# or
export BATOU_TRACK_FDS=stacktrace
```

**Programmatic Interface**:

```python
# Main entry point (in batou/__init__.py)
def initialize_fd_tracking() -> Optional['FDTracker']:
    """
    Initialize FD tracker if BATOU_TRACK_FDS is set.

    Returns:
        FDTracker instance if enabled, None otherwise
    """
    tracking_value = os.environ.get('BATOU_TRACK_FDS', '').strip()
    if not tracking_value:
        return None

    level = 1
    if tracking_value == '2' or 'stacktrace' in tracking_value.lower():
        level = 2

    return FDTracker(level=level)


# FDTracker public interface
class FDTracker:
    def __init__(self, level: int = 1, output_dir: str = "/tmp"):
        """
        Initialize FD tracker.

        Args:
            level: Tracking level (1=basic, 2=stack traces)
            output_dir: Directory for output files
        """

    def track_open(self, fd: int, stack_trace: Optional[str] = None):
        """
        Record file descriptor open event.

        Args:
            fd: File descriptor number
            stack_trace: Optional stack trace string (only at level 2)
        """

    def track_close(self, fd: int):
        """
        Record file descriptor close event.

        Args:
            fd: File descriptor number
        """

    def get_statistics(self) -> Dict[int, FDRecord]:
        """Return current FD statistics."""

    def write_report(self, filepath: Optional[str] = None):
        """
        Write statistics report to file.

        Args:
            filepath: Optional custom output path
        """
```

**Execnet Hook Interface**:

```python
# Hook code template (string that gets serialized)
REMOTE_HOOK_CODE = """
import os
import sys

# Minimal tracking implementation for remote process
class RemoteFDTracker:
    def __init__(self, level):
        self.level = level
        self.fd_records = {}

    def track_open(self, fd):
        if fd not in self.fd_records:
            self.fd_records[fd] = {'open_count': 0, 'stack_traces': []}
        self.fd_records[fd]['open_count'] += 1
        if self.level >= 2:
            import traceback
            self.fd_records[fd]['stack_traces'].append(traceback.format_stack())

    def track_close(self, fd):
        if fd in self.fd_records and self.fd_records[fd]['open_count'] > 0:
            self.fd_records[fd]['open_count'] -= 1

    def get_statistics(self):
        return self.fd_records

# Initialize tracker (receives level from main process)
_tracker = None

def init_tracker(level):
    global _tracker
    _tracker = RemoteFDTracker(level)

def track_fd_open(fd):
    if _tracker:
        _tracker.track_open(fd)

def track_fd_close(fd):
    if _tracker:
        _tracker.track_close(fd)

def get_fd_statistics():
    if _tracker:
        return _tracker.get_statistics()
    return {}
"""

# Hook registration (in batou/remote_core.py or deploy.py)
def register_fd_tracking_hook(execnet_gateway):
    """
    Register FD tracking hook with execnet gateway.

    Args:
        execnet_gateway: Execnet gateway object
    """
    if not get_tracker():
        return  # Tracking not enabled

    tracking_level = get_tracker().tracking_level

    # Initialize remote tracker
    execnet_gateway.remote_exec(
        f"""
        from batou.fd_tracking import RemoteFDTracker
        _remote_tracker = RemoteFDTracker({tracking_level})
        """
    )

    # Install tracking hooks on remote side
    execnet_gateway.remote_exec(
        """
        # Hook into built-in open function
        _original_open = open
        def _tracked_open(*args, **kwargs):
            fd = _original_open(*args, **kwargs)
            track_fd_open(fd.fileno())
            return fd
        open = _tracked_open

        # Hook into socket.socket
        import socket
        _original_socket = socket.socket
        def _tracked_socket(*args, **kwargs):
            s = _original_socket(*args, **kwargs)
            track_fd_open(s.fileno())
            return s
        socket.socket = _tracked_socket
        """
    )
```

**Output File Format**:

```
File Descriptor Tracking Report
=================================
Timestamp: 2026-01-26T10:30:45.123456
Process ID: 12345
Host: localhost
Tracking Level: 2 (with stack traces)

File Descriptor Statistics:
------------------------------------------------------------
FD  | Open Count | Status | Stack Traces
----+------------+--------+--------------------------------------------------
3   | 2          | LEAKED | /usr/lib/python3.11/socket.py:232 in create_connection
    |            |        |   /usr/lib/python3.11/http/client.py:1234 in connect
    |            |        |   src/batou/remote_core.py:456 in connect_remote
    |            |        |   src/batou/host.py:789 in deploy_component
    |            |        |
    |            |        | /usr/lib/python3.11/socket.py:232 in create_connection
    |            |        |   /usr/lib/python3.11/http/client.py:1234 in connect
    |            |        |   src/batou/remote_core.py:456 in connect_remote
    |            |        |   src/batou/host.py:789 in deploy_component

4   | 1          | LEAKED | /usr/lib/python3.11/subprocess.py:1023 in __init__
    |            |        |   src/batou/lib/python.py:345 in install_package
    |            |        |   src/batou/component.py:567 in configure

5   | 0          | Closed |
6   | 0          | Closed |

------------------------------------------------------------
Summary:
Total Open Events: 10
Total Close Events: 8
Active FDs: 2
Potentially Leaked: 2

Leaked File Descriptors: [3, 4]
```

**Traceability**: Addresses SRS requirements REQ-INTF-001, REQ-INTF-002, REQ-USE-002-001

---

### 3.5 Interaction View

#### Viewpoint
Interaction viewpoint describes dynamic behavior and user workflows.

#### Representation

**Sequence Diagram: Basic Tracking (BATOU_TRACK_FDS=1)**:

```
User      EnvVar    FDTracker    Interceptor   POSIX FD API   FDRecord
 │           │            │              │              │           │
 │ Set BATOU_│            │              │              │           │
 │ TRACK_FDS=│            │              │              │           │
 └──────────>│            │              │              │           │
 │           │ Init FDTracker              │              │           │
 │           └───────────>│              │              │           │
 │                        │ Install hooks │              │           │
 │                        │─────────────>│              │           │
 │                                      │ Intercept open│           │
 │ Deployment opens FD ──────────────────>open()─────────>│           │
 │                                      │ Extract FD   │           │           │
 │                                      │─────────────>track_open()           │
 │                                                  │──────────────>increment()
 │                                                  │              │           │
 │ Deployment closes FD────────────────────────>close()──>────────────────>decrement()
 │                        │              │              │           │
 │ Deployment ends           │ Get stats   │              │           │
 │                        │<─────────────│              │           │
 │                        │ Write report │              │           │
 │                        │─────────────>│              │           │
```

**Sequence Diagram: Stack Trace Tracking (BATOU_TRACK_FDS=2)**:

```
User      FDTracker    Interceptor   FDRecord    traceback module   Output File
 │            │              │             │               │               │
 │ Set BATOU_│              │             │               │               │
 │ TRACK_FDS=│              │             │               │               │
 │ =2         │              │             │               │               │
 └───────────>│              │             │               │               │
 │            │ Install hooks │             │               │               │
 │            │─────────────>│             │               │               │
 │ Deployment opens FD       │             │               │               │
 └──────────────────────────>open()       │               │               │
 │                          │ Capture stack trace          │               │
 │                          │───────────────────────────────>format_stack()
 │                          │<───────────────────────────────stack trace
 │                          │─────────────>track_open()─────────────────────>
 │                                        │───>increment(open_count, stack)
 │                                        │               │               │
 │ Deployment ends        │ Get stats     │               │               │
 │                        │<─────────────│               │               │
 │                        │ Write report with stack traces │               │
 │                        │───────────────────────────────────────────────>
```

**Sequence Diagram: Remote Tracking via Execnet**:

```
Main      FDTracker    RemoteTracker   Execnet    Remote Process   Remote FDTracker
 │            │               │           │              │                  │
 │ Init       │               │           │              │                  │
 │            │ Register hook │           │              │                  │
 │            │──────────────>│           │              │                  │
 │                            │ Create hook code        │                  │
 │                            │──────────────────────────>│                  │
 │                            │                       │ Init RemoteTracker  │
 │                            │                       │───────────────────>│
 │ Deployment runs             │                       │                  │
 │ Remote opens FD            │──────────────────────────>│ open()          │
 │                            │                       │───────────────────>track_open()
 │                            │                       │                  │
 │ Deployment ends             │ Get remote stats        │                  │
 │                            │<──────────────────────────│ get_statistics() │
 │                            │                       │<───────────────────remote stats
 │                            │ Merge remote stats      │                  │
 │            │<──────────────│                       │                  │
 │ Write local+remote reports │                       │                  │
```

**State Machine: FDTracker Lifecycle**:

```
             [Not Initialized]
                      │
                      ▼
             Check BATOU_TRACK_FDS
                      │
           ┌──────────┴──────────┐
           │                     │
    Disabled              Enabled (level 1 or 2)
           │                     │
           ▼                     ▼
    [No Tracking]         [Initialized]
                                 │
           ┌───────────────────────┴───────────────────────┐
           │                                       │
    Tracking enabled (hooks installed)       Tracking disabled (no hooks)
           │                                       │
           ▼                                       ▼
    [Tracking Active]                        [No Tracking]
           │
           ├───> FD Open Event ────> [Record FD Open]
           │                            │
           │                            └───> [Record Stack Trace if level 2]
           │
           ├───> FD Close Event ────> [Record FD Close]
           │
           └───> Deployment End ────> [Generate Report]
                                         │
                                         ▼
                                   [Report Written]
                                         │
                                         ▼
                                   [Cleanup]
```

**Workflow: Diagnosing File Descriptor Leak**:

```
1. Deployment fails with "too many open files" error
   ↓
2. Set BATOU_TRACK_FDS=1 (or =2 for stack traces)
   ↓
3. Run deployment again
   ↓
4. System tracks FD operations in local and remote processes
   ↓
5. Deployment completes (or fails again)
   ↓
6. Check /tmp/batou_fd_track_*.txt files
   ↓
7. Identify leaked file descriptors (open_count > 0)
   ↓
8. If tracking level 2, examine stack traces
   ↓
9. Fix leak in identified code location
   ↓
10. Re-run deployment to verify fix
```

**Traceability**: Addresses SRS requirements REQ-FUNC-002-001, REQ-FUNC-002-002, REQ-FUNC-002-005, REQ-FUNC-002-006

---

### 3.6 Algorithm View

#### Viewpoint
Algorithm viewpoint describes key algorithms and their complexity.

#### Representation

**Algorithm: File Descriptor Interception**

```
INTERCEPT_FD_OPEN(level, original_open_function)
    """Intercept file descriptor open operations."""

    def tracked_open(*args, **kwargs):
        # Call original open function
        fd = original_open_function(*args, **kwargs)

        # Get FD number
        fd_number = fd.fileno()

        # Capture stack trace if level 2
        stack_trace = None
        if level >= 2:
            import traceback
            stack_trace = ''.join(traceback.format_stack())

        # Record FD open
        get_tracker().track_open(fd_number, stack_trace)

        return fd

    return tracked_open


INTERCEPT_FD_CLOSE(level, original_close_function)
    """Intercept file descriptor close operations."""

    def tracked_close(fd):
        # Get FD number
        fd_number = fd.fileno()

        # Record FD close
        get_tracker().track_close(fd_number)

        # Call original close function
        return original_close_function(fd)

    return tracked_close
```

**Algorithm: Statistics Aggregation**

```
AGGREGATE_STATISTICS(local_tracker, remote_trackers)
    """Aggregate statistics from local and remote processes."""

    report = StatisticsReport(
        timestamp=datetime.now().isoformat(),
        process_id=os.getpid(),
        host=socket.gethostname(),
        is_remote=False
    )

    # Aggregate local statistics
    local_records = local_tracker.get_statistics()
    for fd, record in local_records.items():
        report.fd_records[fd] = record

    # Aggregate remote statistics
    for remote_tracker in remote_trackers:
        remote_records = remote_tracker.get_statistics()
        for fd, record in remote_records.items():
            # Merge remote FD records with local
            # Use suffix _remote_<host> to distinguish
            remote_key = f"{fd}_remote_{remote_tracker.host}"
            report.fd_records[remote_key] = record

    # Calculate totals
    report.total_opens = sum(r.open_count for r in report.fd_records.values())
    report.total_closes = report.total_opens - report.active_fds

    return report
```

**Algorithm: Report Formatting**

```
FORMAT_REPORT(report, include_stack_traces)
    """Format statistics report as human-readable text."""

    lines = []
    lines.append("File Descriptor Tracking Report")
    lines.append("=" * 50)
    lines.append(f"Timestamp: {report.timestamp}")
    lines.append(f"Process ID: {report.process_id}")
    lines.append(f"Host: {report.host}")

    if report.is_remote:
        lines.append("Type: Remote Process")

    lines.append("")
    lines.append("File Descriptor Statistics:")
    lines.append("-" * 80)
    lines.append("FD  | Open Count | Status" + (" | Stack Traces" if include_stack_traces else ""))
    lines.append("----+------------+--------" + ("-" * 60 if include_stack_traces else ""))

    for fd, record in sorted(report.fd_records.items()):
        status = "LEAKED" if record.is_leaked else "Closed"
        fd_display = str(fd)
        if isinstance(fd, str) and "_remote_" in fd:
            fd_display = f"{fd} (remote)"

        line = f"{fd_display:20} | {record.open_count:10} | {status:6}"
        lines.append(line)

        if include_stack_traces and record.stack_traces:
            for stack in record.stack_traces:
                lines.append("    |            |        | " + stack.replace("\n", "\n    |            |        | "))
            lines.append("    |            |        |")

    lines.append("-" * 80)
    lines.append("")
    lines.append("Summary:")
    lines.append(f"Total Open Events: {report.total_opens}")
    lines.append(f"Total Close Events: {report.total_closes}")
    lines.append(f"Active FDs: {report.active_fds}")
    lines.append(f"Potentially Leaked: {len(report.leaked_fds)}")

    if report.leaked_fds:
        lines.append(f"Leaked File Descriptors: {report.leaked_fds}")

    return "\n".join(lines)
```

**Complexity Analysis**:

| Algorithm | Time Complexity | Space Complexity | Notes |
|-----------|-----------------|------------------|-------|
| INTERCEPT_FD_OPEN | O(S) | O(S) | S = stack trace depth (only at level 2) |
| INTERCEPT_FD_CLOSE | O(1) | O(1) | Constant time, no stack trace |
| AGGREGATE_STATISTICS | O(N) | O(N) | N = total FD records |
| FORMAT_REPORT | O(N * S) | O(N * S) | N = FD records, S = stack traces |

**Traceability**: Addresses SRS requirements REQ-FUNC-002-003, REQ-FUNC-002-004, REQ-FUNC-002-005, REQ-FUNC-002-006

---

### 3.7 State Dynamics View

#### Viewpoint
State dynamics viewpoint describes system state transitions.

#### Representation

**FDTracker States**:

```
State: UNINITIALIZED
  Entry: None (tracker not yet created)
  Events:
    - initialize() -> DISABLED (if BATOU_TRACK_FDS not set)
    - initialize() -> INITIALIZED (if BATOU_TRACK_FDS set)
  Exit: None

State: DISABLED
  Entry: BATOU_TRACK_FDS not set or empty
  Events:
    - (No events - tracking disabled)
  Exit: None

State: INITIALIZED
  Entry: FDTracker.__init__() called
  Events:
    - install_hooks() -> TRACKING_ACTIVE
    - (Direct FD tracking calls allowed)
  Exit: None

State: TRACKING_ACTIVE
  Entry: Interceptor.install_hooks() called
  Events:
    - track_open(fd) -> [Update FDRecord]
    - track_close(fd) -> [Update FDRecord]
    - write_report() -> REPORT_GENERATED
  Exit: Interceptor.uninstall_hooks()

State: REPORT_GENERATED
  Entry: Statistics written to file
  Events:
    - cleanup() -> TERMINATED
  Exit: Cleanup temporary data

State: TERMINATED
  Entry: Cleanup complete
  Events: None
  Exit: Process termination
```

**FDRecord States**:

```
State: CLOSED
  Entry: FDRecord created with open_count = 0
  Events:
    - increment() -> OPEN (open_count = 1)
  Exit: None

State: OPEN
  Entry: increment() called (open_count >= 1)
  Events:
    - increment() -> OPEN (open_count increased)
    - decrement() -> CLOSED if open_count = 1
    - decrement() -> OPEN if open_count > 1
  Exit: None
```

**Tracking Lifecycle**:

```
Process Startup
  └─> Check BATOU_TRACK_FDS
       ├─> Not set: DISABLED (no tracking)
       └─> Set: INITIALIZED
            └─> Install hooks: TRACKING_ACTIVE
                 ├─> Track FD events
                 ├─> Update FDRecords
                 └─> Deployment end: REPORT_GENERATED
                      └─> Write to file: TERMINATED

Process Termination
  └─> Cleanup (automatic)
```

**Error State**:

```
Normal Operation:
  - FD events tracked successfully
  - Reports generated successfully

Error Conditions:
  - Hook installation fails: Log warning, continue without tracking
  - Output file write fails: Log error, keep stats in memory
  - FD number extraction fails: Skip that FD event, log warning

Error Recovery:
  - Hooks can be uninstalled if tracking causes issues
  - Tracking can be disabled mid-deployment via env var check
```

**Traceability**: Addresses SRS requirements REQ-FUNC-002-003, REQ-FUNC-002-004, REQ-FUNC-002-006

---

### 3.8 Resource View

#### Viewpoint
Resource viewpoint describes computational resources and constraints.

#### Representation

**Resource Consumption**:

| Resource | Usage Pattern | Limits | Notes |
|----------|---------------|--------|-------|
| CPU | Minimal when disabled | < 1% overhead | Only environment variable check |
| CPU | Low when enabled (level 1) | < 5% overhead | Simple counter increment |
| CPU | Medium when enabled (level 2) | < 15% overhead | Stack trace capture |
| Memory | Negligible when disabled | < 1KB | Only tracker reference |
| Memory | Low when enabled (level 1) | < 5MB | FD records with counters |
| Memory | Medium when enabled (level 2) | < 10MB | FD records with stack traces |
| Disk I/O | None when disabled | 0 bytes | No output files |
| Disk I/O | Low when enabled | < 100KB | Single text output file |
| Network | None | 0 bytes | Tracking is local to each process |

**Resource Optimization**:

1. **Memory**:
   - FD records stored in dictionary: O(N) where N = open FDs
   - Stack traces stored as strings: O(N * S) where S = average stack depth
   - Cleanup on deployment end: memory freed automatically
   - No persistent data between deployments

2. **CPU**:
   - Hook interception: O(1) per FD operation
   - Stack trace capture: O(S) where S = stack depth (only level 2)
   - Report generation: O(N * S) where N = FDs, S = stack traces
   - No background threads or polling

3. **Disk I/O**:
   - Single write operation at deployment end
   - No real-time file writes
   - Output file size: < 100KB typical
   - File created with restrictive permissions (0600)

4. **Zero Overhead When Disabled**:
   - Environment variable check: O(1) once at startup
   - No hook installation
   - No FD interception
   - No memory allocation for tracking

**Performance Targets**:

```
When Disabled:
  - CPU overhead: < 0.01% (only env var check)
  - Memory overhead: < 1KB
  - Disk usage: 0 bytes
  - Deployment time impact: < 1% (measurement noise)

When Enabled (Level 1):
  - CPU overhead: < 5% of deployment time
  - Memory overhead: < 5MB
  - Disk usage: < 100KB output file
  - Deployment time impact: < 5%

When Enabled (Level 2):
  - CPU overhead: < 15% of deployment time
  - Memory overhead: < 10MB
  - Disk usage: < 200KB output file (with stack traces)
  - Deployment time impact: < 15%
```

**Traceability**: Addresses SRS requirements REQ-PERF-002-001, REQ-PERF-002-002, REQ-FUNC-002-007, REQ-FUNC-002-008

---

### 3.9 Concurrency View

#### Viewpoint
Concurrency viewpoint describes parallel execution and synchronization.

#### Representation

**Concurrency Model**:

The file descriptor tracking system is **single-threaded per process** because:

1. FD operations occur in the same thread that opened/closes them
2. Dictionary access for FD records is thread-safe in CPython
3. No shared state between local and remote processes
4. No background threads or async operations required

**Local Process Execution**:

```
Main Thread (Single):
  ├─ Check BATOU_TRACK_FDS
  ├─ Install FD interception hooks
  ├─ Deployment execution (may be multi-threaded)
  │   ├─ Thread A: Track FD events
  │   ├─ Thread B: Track FD events
  │   └─ Thread C: Track FD events
  ├─ Generate report
  └─ Write output file
```

**Remote Process Execution**:

```
Local Process          Execnet Channel        Remote Process
     │                         │                    │
     ├─ Register hook ─────────>                    │
     │                         └───────────────────> Init RemoteTracker
     │                                             │
     ├─ Deployment commands ───────────────────────> Execute components
     │                                             │
     │<───────────────────────────────────────────── Return stats
     │                                             │
     └─ Merge remote stats                         │
```

**Synchronization**:

**No synchronization required** because:
- Local FD records are accessed from same thread that creates them
- Dictionary operations in CPython are thread-safe (GIL)
- Remote processes have independent tracking state
- Stats are merged after deployment completes (no concurrent modification)

**Thread Safety Considerations**:

1. **Dictionary Access**:
   - Python dict operations are atomic under GIL
   - No race conditions for FDRecord access
   - Each FD is tracked independently

2. **Hook Installation**:
   - Hooks installed once at startup
   - No dynamic hook changes during execution
   - Thread-safe module-level variable for tracker reference

3. **Report Generation**:
   - Occurs after deployment completes
   - All FD events finished
   - Single-threaded aggregation

**Traceability**: Addresses design simplicity requirement (implicit from REQ-DES-002-001)

---

### 3.10 Deployment View

#### Viewpoint
Deployment viewpoint describes installation and deployment aspects.

#### Representation

**Installation**:

The file descriptor tracking system is installed as part of the batou package:

1. **Module location**: `src/batou/fd_tracking.py`
2. **Entry point**: Called from `batou/__init__.py` on initialization
3. **No external dependencies**: Uses only Python stdlib
4. **No configuration required**: Works via environment variable only

**Integration Points**:

```python
# In batou/__init__.py (modified)
from batou.fd_tracking import initialize_fd_tracking

# Initialize tracker on module import (early in deployment)
_tracker = initialize_fd_tracking()


# In batou/deploy.py (modified)
from batou.fd_tracking import get_tracker

def deploy(...):
    # ... existing deployment code ...

    tracker = get_tracker()
    if tracker:
        with timer.step("fd_tracking_report"):
            tracker.write_report()
```

```python
# In batou/remote_core.py (modified)
from batou.fd_tracking import get_tracker, RemoteTracker

def connect_to_remote(host):
    # ... existing connection code ...

    tracker = get_tracker()
    if tracker:
        remote_tracker = RemoteTracker(tracker.tracking_level)
        remote_tracker.register_execnet_hook(gateway)
```

**Backward Compatibility**:

1. **No changes to existing functionality**:
   - All existing deployments work without modification
   - Tracking only active when explicitly enabled
   - Zero overhead when disabled

2. **No changes to existing interfaces**:
   - Environment configuration format unchanged
   - Component API unchanged
   - Command-line arguments unchanged

3. **No breaking changes**:
   - New module is optional
   - Existing tests continue to pass
   - No migration path needed

**Testing Deployment**:

```bash
# Unit tests
pytest src/batou/tests/test_fd_tracking.py

# Integration tests
pytest src/batou/tests/test_deploy.py::test_fd_tracking

# Manual testing
# Disable tracking (default)
./batou deploy dev

# Enable basic tracking
BATOU_TRACK_FDS=1 ./batou deploy dev
cat /tmp/batou_fd_track_*.txt

# Enable stack trace tracking
BATOU_TRACK_FDS=2 ./batou deploy dev
cat /tmp/batou_fd_track_*.txt
```

**Traceability**: Addresses SRS requirements REQ-COMP-002-001, REQ-COMP-002-002, REQ-COMP-002-003, REQ-DES-002-001

---

### 3.11 Patterns View

#### Viewpoint
Patterns viewpoint describes design patterns used in the architecture.

#### Representation

**Design Patterns Applied**:

1. **Singleton Pattern**:
   - `FDTracker` instance is global singleton
   - Single tracker per process
   - Accessed via `get_tracker()` function
   - Ensures consistent tracking state

2. **Strategy Pattern**:
   - `Interceptor` implements interception strategy
   - Can be extended for different FD operation types
   - Different tracking levels (1 vs. 2) use same interface

3. **Observer Pattern**:
   - Hooks observe FD operations
   - Interceptor notifies tracker on events
   - Tracker updates state based on notifications

4. **Template Method Pattern** (reused):
   - `Component.configure()` is template method
   - Existing pattern, not modified

5. **Decorator Pattern**:
   - Hook functions decorate original FD operations
   - `tracked_open()` decorates built-in `open()`
   - `tracked_socket()` decorates `socket.socket()`

**Architectural Styles**:

1. **Hook-based Architecture**:
   ```
   Application Layer
         ↓
   Hook Layer (Interceptor)
         ↓
   System Layer (POSIX FD API)
   ```
   - Hooks intercept operations between layers
   - Transparent to application code
   - Minimal code changes

2. **Layered Architecture** (reused):
   ```
   Presentation Layer (CLI)
         ↓
   Application Layer (Deployment)
         ↓
   Tracking Layer (FDTracker)
         ↓
   Infrastructure Layer (POSIX, Execnet)
   ```

**Anti-Patterns Avoided**:

1. **No Global Mutable State**: Tracker state is encapsulated
2. **No Tight Coupling**: Tracking is isolated via hooks
3. **No Code Duplication**: Reuses existing infrastructure
4. **No Premature Optimization**: Simple design with proven patterns
5. **No Magic Numbers**: Constants defined and documented

**Traceability**: Addresses SRS requirements REQ-DES-002-001, REQ-DES-002-003

---

### 3.12 Structure View

#### Viewpoint
Structure viewpoint describes code organization and module relationships.

#### Representation

**Module Structure**:

```
batou/
├── __init__.py                    [MODIFIED: Initialize FDTracker]
├── fd_tracking.py                  [NEW: Main tracking module]
│   ├── FDTracker                  [Class: Main tracker]
│   ├── FDRecord                   [Class: FD data structure]
│   ├── Interceptor                [Class: FD interception]
│   ├── RemoteTracker              [Class: Remote tracking]
│   └── StatisticsAggregator       [Class: Report generation]
│
├── deploy.py                      [MODIFIED: Write report]
├── remote_core.py                 [MODIFIED: Register execnet hook]
├── environment.py                 [UNCHANGED]
├── component.py                   [UNCHANGED]
├── host.py                        [UNCHANGED]
├── utils.py                       [MINOR CHANGE: Timer integration]
├── _output.py                     [UNCHANGED]
└── tests/
    ├── test_fd_tracking.py        [NEW: FD tracking tests]
    └── test_deploy.py             [MODIFIED: Add FD tracking tests]
```

**Module Dependencies**:

```
__init__.py
  ├─> fd_tracking (new)
  └─> (existing imports)

fd_tracking.py
  ├─> os (stdlib)
  ├─> sys (stdlib)
  ├─> socket (stdlib)
  ├─> traceback (stdlib)
  ├─> time (stdlib)
  ├─> dataclasses (stdlib)
  └─> batou._output (reuse)

deploy.py
  ├─> fd_tracking (new)
  └─> (existing imports)

remote_core.py
  ├─> fd_tracking (new)
  └─> (existing imports)

utils.py
  └─> (unchanged, Timer used by fd_tracking)
```

**Code Organization Principles**:

1. **Single Responsibility**: Each module has one clear purpose
2. **Minimal Changes**: New code isolated to fd_tracking.py
3. **Reuse**: Leverages existing infrastructure
4. **Testability**: Modules designed for unit testing

**File Size Estimates**:

| File | Lines | Notes |
|------|-------|-------|
| fd_tracking.py | ~400-500 lines | Four main classes + helpers |
| test_fd_tracking.py | ~300-400 lines | Unit and integration tests |
| __init__.py | +10 lines | Initialize tracker |
| deploy.py | +5 lines | Write report |
| remote_core.py | +15 lines | Register execnet hook |

**Traceability**: Addresses SRS requirements REQ-DES-002-001, REQ-DES-002-003

---

### 3.13 Dependency View

#### Viewpoint
Dependency viewpoint describes internal and external dependencies.

#### Representation

**External Dependencies**:

| Dependency | Version | Usage | Required? |
|------------|---------|-------|-----------|
| Python | 3.8+ | Runtime | Yes |
| os | stdlib | Environment variables, FD operations | Yes |
| sys | stdlib | System information | Yes |
| socket | stdlib | Socket operations (intercepted) | Yes |
| traceback | stdlib | Stack trace capture | Yes |
| time | stdlib | Timestamps | Yes |
| dataclasses | stdlib | Data structures | Yes |
| execnet | existing | Remote execution hook registration | Yes |

**Internal Dependencies** (batou modules):

```
fd_tracking.py depends on:
  ├─ batou._output (for debug messages)
  └─ batou.utils (Timer class, optional)

__init__.py depends on:
  ├─ batou.fd_tracking (new)
  └─ (existing dependencies)

deploy.py depends on:
  ├─ batou.fd_tracking (new)
  └─ (existing dependencies)

remote_core.py depends on:
  ├─ batou.fd_tracking (new)
  └─ (existing dependencies)
```

**Dependency Graph**:

```
fd_tracking.py (NEW)
    │
    ├── os (stdlib)
    ├── sys (stdlib)
    ├── socket (stdlib)
    ├── traceback (stdlib)
    ├── time (stdlib)
    ├── dataclasses (stdlib)
    └── batou._output
            └── batou._output.TerminalBackend

__init__.py (MODIFIED)
    │
    ├── fd_tracking (NEW)
    └── (existing dependencies)

deploy.py (MODIFIED)
    │
    ├── fd_tracking (NEW)
    └── (existing dependencies)

remote_core.py (MODIFIED)
    │
    ├── fd_tracking (NEW)
    └── (existing dependencies)
```

**Dependency Constraints**:

1. **No new external dependencies**: Uses only Python stdlib
2. **Minimal coupling to batou**: Only uses output module
3. **Optional execnet**: Only used when tracking enabled
4. **Backward compatible**: Doesn't break existing dependencies

**Dependency Management**:

- No new external dependencies required
- Reuses all existing batou dependencies
- Python version compatibility: 3.8-3.12
- No version conflicts with existing packages

**Traceability**: Addresses SRS requirements REQ-COMP-002-001, REQ-COMP-002-002, REQ-DES-002-003

---

### 3.14 Information View

#### Viewpoint
Information viewpoint describes information flow and data structures.

#### Representation

**Information Flow**:

```
Initialization Flow:
  Environment Variable
    → os.environ['BATOU_TRACK_FDS']
    → FDTracker.__init__()
    → TrackingConfig object

FD Open Flow:
  POSIX FD API (open, socket, etc.)
    → Interceptor.intercept_open()
    → FDTracker.track_open()
    → FDRecord.increment()
    → FDRecord data structure

FD Close Flow:
  POSIX FD API (close, shutdown, etc.)
    → Interceptor.intercept_close()
    → FDTracker.track_close()
    → FDRecord.decrement()
    → FDRecord data structure

Remote Tracking Flow:
  Execnet Hook Registration
    → RemoteTracker.register_execnet_hook()
    → Remote process receives hook code
    → Remote FDTracker initializes
    → Remote FD events tracked
    → Remote statistics serialized
    → Remote statistics sent back
    → RemoteTracker.merge_remote_stats()

Report Generation Flow:
  FDTracker.get_statistics()
    → StatisticsAggregator.aggregate_local()
    → StatisticsAggregator.aggregate_remote()
    → StatisticsAggregator.format_report()
    → File write (/tmp/batou_fd_track_*.txt)
```

**Data Structures**:

```python
# FD record with tracking data
@dataclass
class FDRecord:
    fd_number: int
    open_count: int = 0
    stack_traces: List[str] = field(default_factory=list)

    def increment(self, stack_trace: Optional[str] = None):
        self.open_count += 1
        if stack_trace:
            self.stack_traces.append(stack_trace)

    def decrement(self):
        if self.open_count > 0:
            self.open_count -= 1


# Tracking configuration
@dataclass
class TrackingConfig:
    enabled: bool = False
    level: int = 1
    output_dir: str = "/tmp"


# Statistics report
@dataclass
class StatisticsReport:
    timestamp: str
    process_id: int
    host: str
    is_remote: bool = False
    fd_records: Dict[int, FDRecord] = field(default_factory=dict)
    total_opens: int = 0
    total_closes: int = 0
    active_fds: int = 0
    leaked_fds: List[int] = field(default_factory=list)


# Remote statistics transfer
RemoteStats = Dict[str, Dict[str, Any]]
# Format: {fd_number: {'open_count': int, 'stack_traces': List[str]}}
```

**Information Lifecycle**:

1. **Initialization Phase**:
   - Read environment variable (immutable)
   - Parse tracking level (immutable)
   - Create FDTracker instance (persistent until deployment end)

2. **Tracking Phase**:
   - Record FD open events (accumulating)
   - Record FD close events (accumulating)
   - Store stack traces if level 2 (accumulating)
   - FDRecords updated in memory (transient)

3. **Aggregation Phase**:
   - Collect local statistics (read)
   - Collect remote statistics (read)
   - Merge statistics (transform)
   - Calculate totals (compute)

4. **Output Phase**:
   - Format report (transform)
   - Write to file (persist)
   - Cleanup memory (discard)

**Information Constraints**:

- Stack traces do not include secret values
- Output files contain only FD numbers and stack traces
- No sensitive deployment data in output
- FD records discarded after report generation
- Temporary files created with restrictive permissions

**Traceability**: Addresses SRS requirements REQ-FUNC-002-003, REQ-FUNC-002-004, REQ-FUNC-002-005, REQ-SEC-002-001

---

### 3.15 Patterns View (Extended)

#### Viewpoint
Extended patterns view with implementation patterns.

#### Representation

**Hook Installation Pattern**:

```python
# Hook installation with monkey patching
class Interceptor:
    def install_hooks(self):
        """Install interception hooks for FD operations."""

        # Hook built-in open function
        self._original_open = builtins.open
        builtins.open = self.create_tracked_open()

        # Hook socket.socket
        self._original_socket = socket.socket
        socket.socket = self.create_tracked_socket()

        # Hook subprocess.Popen
        self._original_popen = subprocess.Popen
        subprocess.Popen = self.create_tracked_popen()

    def create_tracked_open(self):
        """Create tracked version of open function."""
        def tracked_open(*args, **kwargs):
            fd = self._original_open(*args, **kwargs)
            get_tracker().track_open(fd.fileno(), self.capture_stack_trace())
            return fd
        return tracked_open

    def uninstall_hooks(self):
        """Remove interception hooks."""
        builtins.open = self._original_open
        socket.socket = self._original_socket
        subprocess.Popen = self._original_popen
```

**Tracking Level Pattern**:

```python
# Level-based tracking with conditional stack trace capture
class FDTracker:
    def track_open(self, fd: int, stack_trace: Optional[str] = None):
        """Record FD open event."""
        if fd not in self.fd_records:
            self.fd_records[fd] = FDRecord(fd_number=fd)

        record = self.fd_records[fd]

        # Always increment open count
        record.increment()

        # Optionally record stack trace at level 2
        if self.tracking_level >= 2 and stack_trace is None:
            stack_trace = self.capture_stack_trace()

        if self.tracking_level >= 2 and stack_trace:
            record.stack_traces.append(stack_trace)

        # Debug output
        output.annotate(f"FD {fd} opened (count: {record.open_count})", debug=True)
```

**Report Generation Pattern**:

```python
# Deferred report generation at deployment end
class FDTracker:
    def write_report(self, filepath: Optional[str] = None):
        """Write statistics report to file."""
        if not self.is_enabled:
            return

        # Aggregate statistics
        stats = self._aggregate_statistics()

        # Format report
        report = self._format_report(stats)

        # Determine output file
        if filepath is None:
            pid = os.getpid()
            filepath = f"/tmp/batou_fd_track_{pid}.txt"

        # Write to file
        with open(filepath, 'w') as f:
            f.write(report)

        # Set restrictive permissions
        os.chmod(filepath, 0o600)

        output.annotate(f"FD tracking report written to {filepath}", debug=True)
```

**Remote Tracking Pattern**:

```python
# Remote tracking via execnet hook injection
class RemoteTracker:
    def register_execnet_hook(self, gateway):
        """Register tracking hook with execnet gateway."""

        # Initialize remote tracker
        gateway.remote_exec(f"""
        from batou.fd_tracking import RemoteFDTracker
        _remote_tracker = RemoteFDTracker({self.tracking_level})
        """)

        # Install tracking hooks on remote side
        hook_code = self._create_hook_code()
        gateway.remote_exec(hook_code)

        # Get remote statistics at end
        remote_stats = gateway.remote_exec(
            "get_fd_statistics()",
            self._serialize_remote_stats
        )

        # Merge into main tracker
        self._merge_remote_stats(remote_stats)
```

**Traceability**: Addresses SRS requirements REQ-DES-002-002, REQ-DES-002-003

---

## 4. Decisions

### 4.1 ADR-001: Monkey Patching vs. Wrapper Functions

**Context**: Implementing file descriptor operation interception

**Problem**: Should we use monkey patching (replacing built-in functions) or wrapper functions (custom wrappers)?

**Options**:

| Option | Description | Pros | Cons |
|--------|-------------|-------|------|
| A. Monkey patching | Replace built-in open, socket.socket, etc. | Transparent, catches all operations, minimal code changes | Non-standard, may interfere with other code, harder to debug |
| B. Wrapper functions | Provide custom wrapper functions for tracking | Explicit, controlled, easier to debug | Requires code changes, may miss operations |

**Decision**: **Option A - Monkey patching**

**Rationale**:
1. **Transparency**: Catches all FD operations without code changes
2. **Minimal changes**: No modification to existing batou code
3. **Complete coverage**: Intercepts all FD operations, even in libraries
4. **Reversibility**: Hooks can be uninstalled if needed
5. **Isolation**: Tracking code isolated to fd_tracking module

**Consequences**:
- Non-standard technique but well-documented in Python
- Must ensure hooks don't interfere with normal operations
- Easier to accidentally intercept unintended operations
- May cause issues with other monkey-patching code

**Related Requirements**: REQ-FUNC-002-001 (Local Tracking), REQ-FUNC-002-002 (Remote Tracking), REQ-DES-002-001 (Minimal Changes)

---

### 4.2 ADR-002: Global Singleton vs. Dependency Injection

**Context**: Managing FDTracker instance across the codebase

**Problem**: Should we use a global singleton tracker or dependency injection?

**Options**:

| Option | Description | Pros | Cons |
|--------|-------------|-------|------|
| A. Global singleton | Single tracker instance via module-level variable | Simple, easy to access, minimal code changes | Global state, harder to test, implicit dependencies |
| B. Dependency injection | Pass tracker to functions that need it | Explicit, testable, no global state | Requires code changes, more boilerplate |

**Decision**: **Option A - Global singleton**

**Rationale**:
1. **Simplicity**: Easy to access from anywhere
2. **Minimal changes**: No modification to existing function signatures
3. **Transparent**: Tracking is opt-in, zero impact when disabled
4. **Fits hook model**: Hooks need access to tracker instance
5. **Follows existing patterns**: Similar to Timer class usage

**Consequences**:
- Global mutable state (but only when tracking enabled)
- Harder to test (but testable via environment variable)
- Implicit dependencies on tracker instance
- Easier to access from interceptors and remote code

**Related Requirements**: REQ-FUNC-002-007 (Zero Overhead When Disabled), REQ-DES-002-001 (Minimal Changes)

---

### 4.3 ADR-003: Stack Trace Capture at Open vs. On Demand

**Context**: When should stack traces be captured for FD operations?

**Problem**: Should we capture stack traces at FD open time or on-demand when generating report?

**Options**:

| Option | Description | Pros | Cons |
|--------|-------------|-------|------|
| A. Capture at open | Capture stack trace when FD is opened | Accurate capture location, simpler implementation | Higher overhead, may not be needed |
| B. On-demand capture | Capture when report is generated | Lower overhead if not needed | May miss original location, complex |

**Decision**: **Option A - Capture at open time**

**Rationale**:
1. **Accuracy**: Stack trace shows actual code location of FD open
2. **Simplicity**: Straightforward implementation
3. **Complete coverage**: All FD events have context
4. **Predictable performance**: Overhead is consistent per FD operation
5. **Level 2 opt-in**: Only enabled when explicitly requested

**Consequences**:
- Higher overhead at level 2 (as documented)
- Stack traces may be redundant for multiple opens
- Memory usage increases with number of FD operations
- But still within acceptable limits (< 15% overhead)

**Related Requirements**: REQ-FUNC-002-004 (Optional Stack Trace Capture), REQ-PERF-002-002 (Minimal Overhead)

---

### 4.4 ADR-004: Separate Output Files vs. Merged Output

**Context**: How should statistics from local and remote processes be output?

**Problem**: Should we write separate files for each process or merge into a single file?

**Options**:

| Option | Description | Pros | Cons |
|--------|-------------|-------|------|
| A. Separate files | One file per process (local and each remote) | Simple, process isolation, easy to parse | Multiple files, harder to get full picture |
| B. Merged output | Single file with all process statistics | Complete view, single file | Complex, potential conflicts |

**Decision**: **Option A - Separate files**

**Rationale**:
1. **Simplicity**: Straightforward implementation
2. **Process isolation**: Each process writes its own file
3. **No synchronization needed**: Remote processes write independently
4. **Clear ownership**: Obvious which process contributed which statistics
5. **Familiar pattern**: Matches existing profiling output pattern

**Consequences**:
- Multiple output files (but predictable naming)
- Users need to check multiple files for full picture
- Simpler implementation and debugging
- Easier to identify which process has leaks

**Related Requirements**: REQ-INTF-002 (Temporary File Output), REQ-FUNC-002-006 (Statistics Output)

---

### 4.5 ADR-005: Execnet Hook vs. Manual Remote Tracking

**Context**: How should tracking be implemented in remote processes?

**Problem**: Should we use execnet's hook mechanism or manually inject tracking code?

**Options**:

| Option | Description | Pros | Cons |
|--------|-------------|-------|------|
| A. Execnet hook | Use execnet's official hook mechanism | Supported API, proper integration, reliable | Requires understanding of execnet hooks |
| B. Manual injection | Manually inject tracking code | More control, no execnet dependency | Fragile, may break with execnet updates |

**Decision**: **Option A - Execnet hook**

**Rationale**:
1. **Official API**: execnet provides hook mechanism for this purpose
2. **Integration**: Properly integrated with execnet lifecycle
3. **Reliability**: Less likely to break with execnet updates
4. **Best practices**: Follows execnet documentation
5. **Consistency**: Similar to other execnet-based features

**Consequences**:
- Requires understanding of execnet hook API
- Limited by execnet hook capabilities
- But well-documented and reliable
- Aligns with existing batou execnet usage

**Related Requirements**: REQ-FUNC-002-002 (Remote Tracking via Execnet Hooks), REQ-DES-002-002 (Execnet Hook Integration)

---

## 5. Appendixes

### 5.1 Glossary

| Term | Definition |
|------|------------|
| File descriptor (FD) | Integer handle representing an open file, socket, or pipe in Unix-like systems |
| Execnet | Remote execution library used by batou for deployment |
| Hook | Code injected into remote subprocesses or used to intercept local operations |
| Open count | Number of times a file descriptor has been opened |
| Stack trace | Execution path showing code location of file descriptor operation |
| Opt-in | Feature enabled only when explicitly requested |
| POSIX | Portable Operating System Interface (Unix-like systems) |
| Monkey patching | Runtime modification of code (e.g., replacing built-in functions) |
| Singleton | Design pattern ensuring only one instance of a class exists |
| FDRecord | Data structure storing file descriptor information |
| FDTracker | Main class managing file descriptor tracking |

### 5.2 Code Examples

#### Example 1: Basic Usage
```bash
# Disable tracking (default)
./batou deploy dev

# Enable basic tracking (no stack traces)
BATOU_TRACK_FDS=1 ./batou deploy dev

# Check output
cat /tmp/batou_fd_track_*.txt
```

#### Example 2: Stack Trace Tracking
```bash
# Enable stack trace tracking
BATOU_TRACK_FDS=2 ./batou deploy dev

# Check output with stack traces
cat /tmp/batou_fd_track_*.txt | grep -A 20 "LEAKED"
```

#### Example 3: Diagnosing Remote Leaks
```bash
# Enable tracking for parallel deployment
BATOU_TRACK_FDS=1 ./batou deploy production

# Check local and remote statistics
cat /tmp/batou_fd_track_*.txt
ls -la /tmp/batou_fd_track_*.txt

# Identify which remote host has leaks
grep "LEAKED" /tmp/batou_fd_track_remote_*.txt
```

### 5.3 Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-01-26 | SPEC Agent | Initial SDD |

### 5.4 References to SRS

This SDD implements all requirements from SRS specs/requirements/fd-tracking.md:

- **Interface Requirements**: Sections 3.4 (Interface View), 3.5 (Interaction View)
- **Functional Requirements**: Sections 3.3 (Logical View), 3.6 (Algorithm View)
- **Quality Requirements**: Sections 3.8 (Resource View), 3.13 (Dependency View)
- **Compliance Requirements**: Section 3.10 (Deployment View)
- **Design Requirements**: Sections 3.2 (Composition View), 3.11 (Patterns View)

### 5.5 Traceability Matrix

| SRS Requirement | SDD Section | Design Element |
|----------------|-------------|----------------|
| REQ-INTF-001 | 3.4, 3.5 | Environment variable interface |
| REQ-INTF-002 | 3.4, 3.5 | Temporary file output interface |
| REQ-FUNC-002-001 | 3.3, 3.6 | Local FD tracking via Interceptor |
| REQ-FUNC-002-002 | 3.3, 3.6 | Remote FD tracking via RemoteTracker |
| REQ-FUNC-002-003 | 3.3, 3.14 | Per-file open count recording in FDRecord |
| REQ-FUNC-002-004 | 3.3, 3.6, 3.14 | Stack trace capture at open time |
| REQ-FUNC-002-005 | 3.3, 3.14 | Statistics aggregation in StatisticsAggregator |
| REQ-FUNC-002-006 | 3.3, 3.14 | Output formatting and file writing |
| REQ-FUNC-002-007 | 3.1, 3.8 | Zero overhead when disabled |
| REQ-FUNC-002-008 | 3.8, 3.13 | Minimal overhead when enabled |
| REQ-PERF-002-001 | 3.8 | Zero overhead measurement |
| REQ-PERF-002-002 | 3.8, 3.13 | Minimal overhead targets |
| REQ-REL-002-001 | 3.3, 3.6 | Tracking accuracy algorithms |
| REQ-SEC-002-001 | 3.10, 3.14 | Secure file permissions and data handling |
| REQ-OBS-002-001 | 3.10, 3.12 | Timer integration |
| REQ-USE-002-001 | 3.4, 3.5 | Help documentation and output format |
| REQ-COMP-002-001 | 3.10 | Backward compatibility |
| REQ-COMP-002-002 | 3.13 | Python version support |
| REQ-COMP-002-003 | 3.10 | POSIX compliance |
| REQ-DES-002-001 | 3.2, 3.12 | Minimal code changes |
| REQ-DES-002-002 | 3.10, 3.12 | Execnet hook integration |
| REQ-DES-002-003 | 3.2, 3.13 | Reuse existing infrastructure |

### 5.6 Implementation Notes

**Key Implementation Considerations**:

1. **Zero-Overhead Enforcement**:
   - Early return in `initialize_fd_tracking()` if BATOU_TRACK_FDS not set
   - No module-level code that runs when tracking disabled
   - Add test: Verify no performance impact when disabled

2. **Hook Installation Safety**:
   - Store original functions before patching
   - Provide uninstall method for cleanup
   - Handle exceptions during hook installation gracefully

3. **Thread Safety**:
   - Rely on CPython GIL for dict atomicity
   - No explicit locking needed
   - Document thread-safety guarantees

4. **Stack Trace Optimization**:
   - Only capture at level 2
   - Use `traceback.format_stack()` not `extract_stack()`
   - Limit stack depth if needed (e.g., 50 frames)

5. **Remote Tracking Considerations**:
   - Serialize remote stats as JSON or pickle
   - Handle connection failures gracefully
   - Merge stats after all remote processes complete

6. **Output File Management**:
   - Use restrictive permissions (0600)
   - Include PID and timestamp in filename
   - Create files in /tmp directory
   - Cleanup old files if needed (optional)

**File Changes Summary**:

| File | Change Type | Lines | Description |
|------|-------------|-------|-------------|
| fd_tracking.py | New | +450 | Main tracking module |
| __init__.py | Modified | +10 | Initialize tracker |
| deploy.py | Modified | +5 | Write report |
| remote_core.py | Modified | +15 | Register execnet hook |
| test_fd_tracking.py | New | +350 | Unit and integration tests |
| README.md | Modified | +50 | Add documentation |
| Total | ~880 | lines of new/modified code |

**Testing Strategy**:

1. **Unit Tests**:
   - Test FDRecord operations
   - Test Interceptor hook installation
   - Test statistics aggregation
   - Test report formatting

2. **Integration Tests**:
   - Test local tracking end-to-end
   - Test remote tracking via execnet
   - Test zero overhead when disabled
   - Test minimal overhead when enabled

3. **Performance Tests**:
   - Benchmark overhead when disabled
   - Benchmark overhead when enabled (level 1)
   - Benchmark overhead when enabled (level 2)
   - Verify no memory leaks in tracking code

4. **Regression Tests**:
    - Ensure existing functionality unchanged
    - Test backward compatibility
    - Test all supported Python versions

## 5. Appendixes

### 5.1 Revision History
| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.1 | 2026-02-02 | ASSI | Update interfaces for close tracking, mode tracking, leak detection. Add RemoteStatistics data structure, leak_threshold, verbose mode support. Update external entities to include BATOU_TRACK_FDS_VERBOSE. |
| 1.0 | 2026-01-26 | SPEC Agent | Initial design specification |
