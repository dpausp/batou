---
spec_type: srs
feature_id: F-002-fd-tracking
status: draft
date: 2026-01-26
---

# SRS: File Descriptor Tracking System

## 1. Introduction

### 1.1 Document Purpose
This Software Requirements Specification (SRS) defines requirements for the file descriptor tracking system, a diagnostic feature for batou deployments. The specification follows IEEE 830 standards and addresses the need to diagnose "too many open files" errors that occur during parallel execution of deployments.

### 1.2 Product Scope
The file descriptor tracking system provides opt-in tracking of open file descriptors in both local and remote processes during batou deployments. It follows existing profiling patterns (e.g., BATOU_PROFILE_REMOTE) and integrates with batou's remote execution infrastructure via execnet hooks. The system outputs statistics to temporary files with minimal performance impact when enabled and zero impact when disabled.

### 1.3 Definitions
- **File descriptor (FD)**: Integer handle representing an open file, socket, or pipe in Unix-like systems
- **Execnet**: Remote execution library used by batou for deployment operations
- **Remote hook**: Code executed in remote execnet subprocesses
- **Open count**: Number of times a specific file descriptor has been opened without being closed
- **Stack trace**: Execution path leading to file descriptor allocation
- **Opt-in**: Feature that must be explicitly enabled via environment variable

### 1.4 References
- IEEE Std 830-1998: IEEE Recommended Practice for Software Requirements Specifications
- RFC 2119: Key words for use in RFCs to indicate requirement levels
- batou README.md: Deployment automation framework documentation
- batou CHANGES.md: Version history and feature evolution
- Python 3 documentation: File descriptor handling and resource monitoring

### 1.5 Overview
This document specifies requirements for a file descriptor tracking system that diagnoses "too many open files" errors during parallel deployments. Section 2 provides product overview, Section 3 defines requirements, Section 4 covers verification methods, and Section 5 contains supporting information.

## 2. Product Overview

### 2.1 Product Perspective
The file descriptor tracking system extends batou with diagnostic capabilities for resource monitoring. It operates as an optional feature that:
- Tracks file descriptors in local and remote processes
- Integrates with execnet for remote tracking
- Outputs statistics to temporary files
- Follows existing profiling patterns

**Relationship to existing features**:
- Profiling: Uses similar opt-in pattern as BATOU_PROFILE_REMOTE
- Remote execution: Leverages execnet infrastructure for remote hooks
- Output system: Integrates with existing Timer and output modules

### 2.2 Product Functions
The file descriptor tracking system provides the following functions:
- Track file descriptor open/close events
- Record per-file open counts with optional stack traces
- Aggregate statistics across local and remote processes
- Output results to temporary files
- Provide minimal overhead when enabled
- Maintain zero impact when disabled

### 2.3 Constraints
- **Constraint 1 (MUST)**: FD tracking must be opt-in via environment variable (e.g., BATOU_TRACK_FDS)
- **Constraint 2 (MUST)**: Must track both local and remote file descriptors via execnet hooks
- **Constraint 3 (MUST)**: Must have zero performance impact when disabled
- **Constraint 4 (MUST)**: Output FD statistics to temp files following /tmp/batou_fd_track_*.txt naming convention
- **Constraint 5 (SHOULD)**: Integrate with existing batou infrastructure (Timer class, output system)

### 2.4 User Characteristics
Users of the file descriptor tracking system are:
- DevOps engineers diagnosing "too many open files" errors
- Developers investigating resource leaks in deployments
- System administrators troubleshooting deployment failures
- CI/CD pipelines needing diagnostic data for debugging

### 2.5 Assumptions
- Unix-like operating systems (Linux, macOS) with POSIX file descriptors
- Python 3.8+ runtime is available
- File descriptor limits are configured on target systems
- Temporary directory (/tmp) is writable
- execnet is available for remote execution

### 2.6 Apportioning
The following features are out of scope for this specification:
- Automatic file descriptor limit adjustment
- Real-time monitoring/alerting during deployment
- Integration with external monitoring systems
- File descriptor leak prevention or automatic cleanup
- Windows operating system support

## 3. Requirements

### 3.1 External Interfaces

#### REQ-INTF-001: Environment Variable Control
The system shall enable file descriptor tracking via BATOU_TRACK_FDS environment variable.

**Acceptance Criteria**:
- System checks BATOU_TRACK_FDS on initialization
- Any non-empty value enables tracking
- Unset or empty value disables tracking
- No errors occur when variable is set or unset
- Value can be optionally parsed for tracking level (e.g., "1" for basic, "2" with stack traces)

**Verification Method**: Test, Analysis

**More Information**: See SDD Section 3.4 for interface design view.

#### REQ-INTF-003: Verbose Output Control
The system shall support BATOU_TRACK_FDS_VERBOSE environment variable for detailed FD operation logging.

**Acceptance Criteria**:
- System checks BATOU_TRACK_FDS_VERBOSE on deployment end
- Any non-empty value enables verbose FD operation logging
- Verbose mode shows individual FD open/close events with timestamps
- Verbose mode shows mode (r, w, a+, etc.) for each operation
- Verbose mode limits output to first 10 operations per host
- No verbose output when variable is unset or empty

**Verification Method**: Test, Analysis

#### REQ-INTF-002: Temporary File Output
The system shall output FD statistics to files following the pattern /tmp/batou_fd_track_*.txt.

**Acceptance Criteria**:
- Output file names match pattern /tmp/batou_fd_track_*.txt
- Filename includes process ID for uniqueness (e.g., batou_fd_track_12345.txt)
- Separate files for local and remote processes (e.g., batou_fd_track_remote_6789.txt)
- Files are created with appropriate permissions (user-readable only)
- Files are created in /tmp directory

**Verification Method**: Test, Inspection

### 3.2 Functional Requirements

#### REQ-FUNC-002-001: Local File Descriptor Tracking
The system shall track file descriptor open/close events in the local process when tracking is enabled.

**Rationale**: Tracking local file descriptors is necessary to understand resource usage on the deployment controller, especially when running parallel operations.

**Acceptance Criteria**:
- System intercepts file descriptor open operations (open, socket, pipe, etc.)
- System intercepts file descriptor close operations
- Each file descriptor is tracked by its integer value
- Open counts are maintained per file descriptor
- Stack traces can optionally be captured when tracking level is "2"

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-002: Remote File Descriptor Tracking via Execnet Hooks
The system shall track file descriptors in remote execnet subprocesses using execnet hooks.

**Rationale**: Remote processes can also leak file descriptors during parallel deployments. Execnet hooks allow injecting tracking code into remote subprocesses.

**Acceptance Criteria**:
- Tracking code is injected via execnet's hook mechanism
- Hooks are registered before remote execution begins
- Remote tracking follows same interface as local tracking
- Remote statistics are collected and merged with local statistics
- Hook injection does not interfere with normal remote execution

**Verification Method**: Test, Analysis

**More Information**: See REQ-FUNC-002-001 for tracking interface.

#### REQ-FUNC-002-003: Per-File Open Count Recording
The system shall record number of times each file descriptor is opened.

**Rationale**: Per-file open counts help identify which file descriptors are being opened multiple times without being properly closed, a common source of "too many open files" errors.

**Acceptance Criteria**:
- Each file descriptor has an associated open count
- Open count increments on open operation
- Open count decrements on close operation
- Statistics include file descriptor number and current open count
- File descriptors with open count > 0 at deployment end are reported as potentially leaked

**Verification Method**: Test

#### REQ-FUNC-002-009: File Descriptor Close Tracking
The system shall track file descriptor close operations in addition to open operations.

**Rationale**: Tracking close operations allows detection of leaks by comparing opens vs. closes and provides complete FD lifecycle visibility.

**Acceptance Criteria**:
- System intercepts file descriptor close operations
- Close count is maintained separate from open count
- Close operations are logged with timestamp, FD number, and file path
- Total close count is reported in statistics
- Low-level close operations (os.close()) are also tracked

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-010: File Mode Tracking
The system shall track file mode (r, w, a+, etc.) for each file descriptor operation.

**Rationale**: File mode information helps identify patterns in FD usage and distinguishes between read/write operations that may have different leak characteristics.

**Acceptance Criteria**:
- File mode is captured on open operations
- Mode is stored with FD record
- Modes are aggregated per file path
- Statistics include mode breakdown per file
- Low-level FD operations are tagged as "low-level" mode

**Verification Method**: Test

#### REQ-FUNC-002-011: Leak Detection with Threshold
The system shall detect potential file descriptor leaks when number of open FDs exceeds warning threshold.

**Rationale**: Proactive leak detection helps identify issues before "too many open files" errors occur and provides actionable diagnostic information.

**Acceptance Criteria**:
- Warning threshold is configurable (default: 200 FDs)
- Warning is triggered when number of open FDs exceeds threshold
- Warning is displayed with count of open FDs
- Leaked FD details are shown (FD number, path, mode, open time)
- Details are limited to first 5 leaked FDs with summary for additional FDs
- Warning is displayed in red to indicate severity
- Leak detection works for both local and remote processes

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-012: Leaked FD Report
The system shall report detailed information about leaked file descriptors at deployment end.

**Rationale**: Detailed information about leaked FDs helps developers identify and fix leaks by showing which files are still open and when they were opened.

**Acceptance Criteria**:
- Leaked FDs are reported with FD number, file path, mode, and open timestamp
- Report includes total count of leaked FDs
- Report is displayed in output after deployment completes
- Leaked FD list is limited to avoid overwhelming output (e.g., 10 entries)
- Summary shows count of additional FDs beyond displayed limit
- Leaked FD information is included in aggregated statistics

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-004: Optional Stack Trace Capture
The system shall optionally capture stack traces for file descriptor operations when tracking level is "2".

**Rationale**: Stack traces provide context about where file descriptors are being opened, helping identify the source of leaks.

**Acceptance Criteria**:
- Stack traces are captured only when BATOU_TRACK_FDS value is "2" or contains "stacktrace"
- Stack traces are captured at file descriptor open time
- Stack traces are stored with file descriptor record
- Stack traces are output with file descriptor statistics
- Stack trace capture does not significantly impact performance

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-005: Statistics Aggregation
The system shall aggregate statistics from local and remote processes into a unified report.

**Rationale**: Aggregated statistics provide a complete view of file descriptor usage across the entire deployment, including parallel remote operations.

**Acceptance Criteria**:
- Local process statistics are collected
- Remote process statistics are collected from each remote host
- Statistics are merged into a single report
- Report identifies which process (local or remote) contributed each statistic
- Report includes process ID and host (if remote) for each entry

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-006: Statistics Output to Temporary Files
The system shall write aggregated statistics to temporary files following the naming convention.

**Rationale**: Outputting to temporary files allows post-deployment analysis and preserves diagnostic data after deployment completes.

**Acceptance Criteria**:
- Statistics are written to /tmp/batou_fd_track_<pid>.txt for local process
- Remote statistics are written to /tmp/batou_fd_track_remote_<pid>.txt for each remote process
- Output includes timestamp and process information
- Output includes file descriptor number, open count, and optional stack traces
- Output is human-readable plain text format

**Verification Method**: Test, Inspection

#### REQ-FUNC-002-007: Zero Overhead When Disabled
The system shall have no performance impact when BATOU_TRACK_FDS is not set or empty.

**Rationale**: Tracking file descriptors involves interception operations that can impact performance. Zero overhead ensures production deployments are not affected when diagnostics are not needed.

**Acceptance Criteria**:
- No file descriptor interception occurs when tracking is disabled
- No temporary files are created when tracking is disabled
- No hook injection occurs when tracking is disabled
- No memory or CPU overhead when tracking is disabled
- Deployment performance is identical with and without tracking disabled

**Verification Method**: Test, Analysis

#### REQ-FUNC-002-008: Minimal Overhead When Enabled
The system shall have minimal performance impact when tracking is enabled at basic level.

**Rationale**: While some overhead is expected for tracking, it should not significantly impact deployment speed to avoid discouraging use.

**Acceptance Criteria**:
- Basic tracking overhead (level "1") is < 5% of total deployment time
- Stack trace tracking overhead (level "2") is < 15% of total deployment time
- Tracking does not cause additional "too many open files" errors
- Memory overhead for tracking is < 10MB

**Verification Method**: Test, Analysis

### 3.3 Quality of Service

#### REQ-PERF-002-001: Zero Overhead When Disabled
File descriptor tracking shall have no measurable performance impact when disabled.

**Acceptance Criteria**:
- Deployment time difference with tracking disabled is < 1% (measurement noise)
- No additional memory allocation when disabled
- No additional CPU usage when disabled
- Benchmark tests show identical performance with and without tracking disabled

**Verification Method**: Test, Analysis

**More Information**: Performance baseline established in REQ-FUNC-002-007.

#### REQ-PERF-002-002: Minimal Overhead When Enabled
File descriptor tracking shall have minimal overhead when enabled.

**Acceptance Criteria**:
- Basic tracking overhead is < 5% of total deployment time
- Stack trace tracking overhead is < 15% of total deployment time
- Overhead is linear with number of file descriptor operations (not exponential)
- Overhead does not increase over time (no memory leaks in tracking code)

**Verification Method**: Test, Analysis

#### REQ-REL-002-001: Tracking Accuracy
File descriptor tracking shall accurately record all open/close operations.

**Acceptance Criteria**:
- All file descriptor opens are recorded when tracking is enabled
- All file descriptor closes are recorded when tracking is enabled
- Open counts match actual system state
- No false positives or false negatives in tracking
- Remote tracking matches local tracking accuracy

**Verification Method**: Test, Analysis

#### REQ-SEC-002-001: Secure Temporary File Creation
Temporary files shall be created with appropriate security settings.

**Acceptance Criteria**:
- Output files are created with mode 0600 (user-readable/writable only)
- Files are created in /tmp directory
- No sensitive deployment data is written to output files (only FD numbers and stack traces)
- Stack traces do not include secret values (passwords, keys, tokens)

**Verification Method**: Analysis, Inspection

#### REQ-OBS-002-001: Integration with Timer Class
Tracking shall integrate with existing Timer class for performance measurement.

**Acceptance Criteria**:
- Tracking overhead is measurable using Timer class
- Timer annotations show tracking duration in debug mode
- Tracking steps are recorded in Timer.durations dictionary

**Verification Method**: Test, Inspection

#### REQ-USE-002-001: Help and Documentation
File descriptor tracking usage shall be documented in help and README.

**Acceptance Criteria**:
- README.md documents BATOU_TRACK_FDS environment variable
- Help output mentions diagnostic features including FD tracking
- Examples show how to enable and use tracking
- Output format is documented with examples

**Verification Method**: Inspection

### 3.4 Compliance

#### REQ-COMP-002-001: Backward Compatibility
All existing batou functionality shall remain unchanged when tracking is disabled.

**Acceptance Criteria**:
- Existing deployments work without modification
- No changes to existing environment or component configurations
- No changes to existing command-line interfaces
- Deploy command behavior is unchanged when tracking is disabled

**Verification Method**: Test, Regression

#### REQ-COMP-002-002: Python Version Support
System shall support Python 3.8 through 3.12.

**Acceptance Criteria**:
- Works correctly on Python 3.8, 3.9, 3.10, 3.11, 3.12
- No version-specific features that break compatibility
- Tested across all supported Python versions

**Verification Method**: Test

#### REQ-COMP-002-003: POSIX Compliance
System shall work on POSIX-compliant systems (Linux, macOS).

**Acceptance Criteria**:
- File descriptor tracking works on Linux
- File descriptor tracking works on macOS
- No Linux-specific or macOS-specific code that breaks the other
- Uses standard POSIX file descriptor operations

**Verification Method**: Test, Analysis

### 3.5 Design and Implementation

#### REQ-DES-002-001: Minimal Code Changes
Implementation shall minimize changes to existing code.

**Acceptance Criteria**:
- New tracking code is isolated to dedicated module (fd_tracking.py)
- No changes to core deployment logic
- No changes to existing component infrastructure
- Tracking hooks are optional and non-intrusive
- Existing test coverage remains valid

**Verification Method**: Inspection, Regression Testing

#### REQ-DES-002-002: Execnet Hook Integration
Remote tracking shall use execnet's hook mechanism properly.

**Acceptance Criteria**:
- Hooks are registered using execnet's official hook API
- Hook code is executed in remote subprocesses
- Hook registration does not interfere with other hooks
- Hook code is self-contained and isolated
- Remote tracking uses same interface as local tracking

**Verification Method**: Test, Analysis

#### REQ-DES-002-003: Reuse Existing Infrastructure
Implementation shall reuse existing batou infrastructure where possible.

**Acceptance Criteria**:
- Uses existing output module for debug messages
- Uses existing Timer class for performance measurement
- Follows existing error handling patterns
- Uses existing temporary directory handling if available

**Verification Method**: Inspection

### 3.6 AI/ML
Not applicable to this feature.

## 4. Verification

### 4.1 Verification Matrix

| Requirement ID | Verification Method | Test Coverage |
|----------------|---------------------|---------------|
| REQ-INTF-001 | Test, Analysis | 100% |
| REQ-INTF-002 | Test, Inspection | 100% |
| REQ-INTF-003 | Test, Analysis | 100% |
| REQ-FUNC-002-001 | Test, Analysis | 100% |
| REQ-FUNC-002-002 | Test, Analysis | 100% |
| REQ-FUNC-002-003 | Test | 100% |
| REQ-FUNC-002-004 | Test, Analysis | 100% |
| REQ-FUNC-002-005 | Test, Analysis | 100% |
| REQ-FUNC-002-006 | Test, Inspection | 100% |
| REQ-FUNC-002-007 | Test, Analysis | 100% |
| REQ-FUNC-002-008 | Test, Analysis | 100% |
| REQ-FUNC-002-009 | Test, Analysis | 100% |
| REQ-FUNC-002-010 | Test | 100% |
| REQ-FUNC-002-011 | Test, Analysis | 100% |
| REQ-FUNC-002-012 | Test, Analysis | 100% |
| REQ-PERF-002-001 | Test, Analysis | 100% |
| REQ-PERF-002-002 | Test, Analysis | 100% |
| REQ-REL-002-001 | Test, Analysis | 100% |
| REQ-SEC-002-001 | Analysis, Inspection | 100% |
| REQ-OBS-002-001 | Test, Inspection | 100% |
| REQ-USE-002-001 | Inspection | 100% |
| REQ-COMP-002-001 | Test, Regression | 100% |
| REQ-COMP-002-002 | Test | 100% |
| REQ-COMP-002-003 | Test, Analysis | 100% |
| REQ-DES-002-001 | Inspection, Regression Testing | 100% |
| REQ-DES-002-002 | Test, Analysis | 100% |
| REQ-DES-002-003 | Inspection | 100% |

### 4.2 Verification Methods

#### 4.2.1 Test
Automated tests shall verify:
- Environment variable parsing and tracking enablement
- Local file descriptor tracking accuracy
- Remote file descriptor tracking via execnet hooks
- Per-file open count recording
- Optional stack trace capture
- Statistics aggregation from multiple processes
- Temporary file output and format
- Zero overhead when disabled
- Minimal overhead when enabled

Test approach:
- Unit tests for tracking module functions
- Integration tests for local and remote tracking
- Performance benchmarks for overhead measurement
- Regression tests to ensure no impact on existing functionality

#### 4.2.2 Analysis
Performance analysis shall verify:
- Zero overhead when disabled (via cProfile)
- Minimal overhead when enabled (via cProfile)
- Linear scaling of overhead with FD operations
- No memory leaks in tracking code
- Accuracy of tracking against actual system state

Static analysis shall verify:
- No security issues in stack trace capture
- Proper handling of sensitive data
- Thread safety of tracking data structures

#### 4.2.3 Inspection
Code review and manual testing shall verify:
- Output file format and readability
- Stack trace usefulness and clarity
- Integration with Timer class
- Help and documentation completeness
- Temporary file permissions and security
- Code organization and maintainability

## 5. Appendixes

### 5.1 Use Cases

#### UC-001: Diagnosing Local File Descriptor Leak
**Actor**: DevOps Engineer
**Preconditions**: Deployment fails with "too many open files" error
**Steps**:
1. Engineer sets BATOU_TRACK_FDS=1
2. Engineer runs deployment again
3. System tracks file descriptors locally
4. System writes statistics to /tmp/batou_fd_track_*.txt
5. Engineer analyzes output to identify leaked file descriptors
**Postconditions**: File descriptor leak is identified and can be fixed

#### UC-002: Diagnosing Remote File Descriptor Leak
**Actor**: DevOps Engineer
**Preconditions**: Parallel deployment fails with "too many open files" error
**Steps**:
1. Engineer sets BATOU_TRACK_FDS=1
2. Engineer runs deployment again
3. System tracks file descriptors in local and remote processes
4. System aggregates statistics from all processes
5. System writes separate files for local and remote processes
6. Engineer analyzes remote statistics to identify leaks
**Postconditions**: Remote file descriptor leak is identified and can be fixed

#### UC-003: Identifying Leak Source with Stack Traces
**Actor**: Developer
**Preconditions**: File descriptor leak identified but source unknown
**Steps**:
1. Developer sets BATOU_TRACK_FDS=2
2. Developer runs deployment again
3. System captures stack traces for file descriptor opens
4. System writes statistics with stack traces to output file
5. Developer analyzes stack traces to find leak source
**Postconditions**: Code location causing leak is identified

### 5.2 Output Format Examples

#### Basic Tracking Output (BATOU_TRACK_FDS=1)
```
File Descriptor Tracking Report
=================================
Timestamp: 2026-01-26T10:30:45
Process ID: 12345
Host: localhost

File Descriptor Statistics:
FD  | Open Count | Status
----+------------+--------
3   | 1          | LEAKED
4   | 2          | LEAKED
5   | 0          | Closed
6   | 0          | Closed

Summary:
Total Open Events: 10
Total Close Events: 8
Active FDs: 2
Potentially Leaked: 2
```

#### Stack Trace Tracking Output (BATOU_TRACK_FDS=2)
```
File Descriptor Tracking Report with Stack Traces
=================================================
Timestamp: 2026-01-26T10:30:45
Process ID: 12345
Host: localhost

File Descriptor Statistics with Stack Traces:
FD 3: Open Count = 2 (LEAKED)
  Open at:
    File "/usr/lib/python3.11/socket.py", line 232, in create_connection
    File "/usr/lib/python3.11/http/client.py", line 1234, in connect
    File "src/batou/remote_core.py", line 456, in connect_remote
    File "src/batou/host.py", line 789, in deploy_component

FD 4: Open Count = 1 (LEAKED)
  Open at:
    File "/usr/lib/python3.11/subprocess.py", line 1023, in __init__
    File "src/batou/lib/python.py", line 345, in install_package
    File "src/batou/component.py", line 567, in configure

Summary:
Total Open Events: 10
Total Close Events: 8
Active FDs: 2
Potentially Leaked: 2
```

#### Verbose Output (BATOU_TRACK_FDS_VERBOSE=1)
```
Remote FD tracking for remote-host-01: 234 opens, 120 closes, 114 still open
  FD operations for remote-host-01:
    [14:23:45.123] FD #1 OPEN: /tmp/tmpXXXX.diff (a+)
    [14:23:45.234] FD #2 OPEN: /home/deployment/.../file.py (r)
    [14:23:45.345] FD #1 CLOSE: /tmp/tmpXXXX.diff (a+)
    [14:23:46.456] FD #3 OPEN: fd:42 (low-level)
    [14:23:46.567] FD #3 CLOSE: fd:42 (low-level)
    ... and 229 more
```

#### Leak Warning Output
```
Remote FD leak warning for remote-host-01: 114 FDs still open
  FD 42: /tmp/tmpXXXX.diff (a+) since 14:23:45.123
  FD 43: /home/deployment/batou_src/src/batou/lib/file.py (r) since 14:23:46.234
  FD 44: /home/deployment/work/config.yaml (w) since 14:23:47.345
  FD 45: /home/deployment/work/.batou-diffs/tmp83tai515.diff (a+) since 14:23:48.456
  FD 46: fd:98 (low-level) since 14:23:49.567
  ... and 109 more
```

#### Remote Process Output
```
File Descriptor Tracking Report (Remote)
========================================
Timestamp: 2026-01-26T10:30:46
Process ID: 6789
Host: remote-host-01.example.com

File Descriptor Statistics:
FD  | Open Count | Status
----+------------+--------
3   | 0          | Closed
7   | 1          | LEAKED
8   | 0          | Closed

Summary:
Total Open Events: 5
Total Close Events: 4
Active FDs: 1
Potentially Leaked: 1
```

### 5.3 Performance Analysis

**Expected Overhead**:

| Tracking Level | Expected Overhead | Notes |
|----------------|------------------|-------|
| Disabled | 0% | No tracking code executed |
| Basic (1) | 2-3% | Intercepts open/close, no stack traces |
| Stack Trace (2) | 8-12% | Intercepts open/close with stack traces |

**Measurement Method**:
```python
# Benchmark script
import time
import os

# Without tracking
os.environ.pop('BATOU_TRACK_FDS', None)
start = time.time()
run_deployment()
time_without_tracking = time.time() - start

# With basic tracking
os.environ['BATOU_TRACK_FDS'] = '1'
start = time.time()
run_deployment()
time_with_basic_tracking = time.time() - start

# With stack traces
os.environ['BATOU_TRACK_FDS'] = '2'
start = time.time()
run_deployment()
time_with_stack_traces = time.time() - start

overhead_basic = (time_with_basic_tracking - time_without_tracking) / time_without_tracking * 100
overhead_stack = (time_with_stack_traces - time_without_tracking) / time_without_tracking * 100
```

### 5.4 Glossary
- **File descriptor (FD)**: Integer handle representing an open file, socket, or pipe
- **Execnet**: Remote execution library used by batou
- **Hook**: Code injected into remote subprocesses via execnet
- **Open count**: Number of times a file descriptor has been opened
- **Stack trace**: Execution path showing code location of file descriptor operation
- **Opt-in**: Feature enabled only when explicitly requested
- **POSIX**: Portable Operating System Interface (Unix-like systems)

### 5.5 Revision History
| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.1 | 2026-02-02 | ASSI | Add REQ-INTF-003 (verbose), REQ-FUNC-002-009 to 002-012 (close tracking, mode tracking, leak detection, leaked FD report), update output examples |
| 1.0 | 2026-01-26 | SPEC Agent | Initial specification |
