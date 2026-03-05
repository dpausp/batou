# Software Design Description
## For Batou SSH Feature

## Table of Contents
* [1. Introduction](#1-introduction)
  * [1.1 Document Purpose](#11-document-purpose)
  * [1.2 Subject Scope](#12-subject-scope)
  * [1.3 Definitions, Acronyms, and Abbreviations](#13-definitions-acronyms-and-abbreviations)
  * [1.4 References](#14-references)
  * [1.5 Document Overview](#15-document-overview)
* [2. Design Overview](#2-design-overview)
  * [2.1 Stakeholder Concerns](#21-stakeholder-concerns)
  * [2.2 Selected Viewpoints](#22-selected-viewpoints)
* [3. Design Views](#3-design-views)
* [4. Decisions](#4-decisions)
* [5. Appendixes](#5-appendixes)

## 1. Introduction

### 1.1 Document Purpose

This SDD documents design decisions for the experimental SSH feature in batou, including paramiko integration, host key management, and command execution. The document targets developers evaluating paramiko as potential replacement for execnet.

### 1.2 Subject Scope

The SSH feature provides host key pre-flight checking and remote command execution using paramiko. This SDD covers the SSHClient class, CLI command architecture, and integration with existing SSH configuration. Integration with execnet deployment code is out of scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| MADR | Markdown Architecture Decision Record - structured format for documenting architectural decisions |
| SSHClient | Primary class providing SSH connectivity and command execution |
| Paramiko | Python implementation of SSHv2 protocol |

### 1.4 References

- SRS: SSH Feature
- Paramiko documentation
- OpenSSH configuration specification

### 1.5 Document Overview

This SDD follows IEEE 1016 structure with sections for introduction, design overview, design views, and decisions. MADR pattern documents all significant architectural decisions. No complex design views are required as the system follows straightforward patterns.

## 2. Design Overview

### 2.1 Stakeholder Concerns

Developers need to understand paramiko integration patterns and evaluate whether paramiko is suitable for production deployments. Operators need reliable host key management that prevents garbled console output. The feature must remain experimental without affecting existing deployments.

### 2.2 Selected Viewpoints

No detailed design views are required. The system uses straightforward composition (paramiko SSHClient wrapper) and interaction (command-line invocation) that do not warrant separate view documentation.

## 3. Design Views

Not required. The system design is sufficiently captured in the MADR decisions below.

## 4. Decisions

### ssh-library-choice

**Context:**

Need SSH library for host key management and command execution. Current batou deployment uses execnet for SSH connectivity. Multiple SSH libraries are available with different abstraction levels and dependency profiles.

**Options:**

A. Use paramiko directly for low-level SSH control
B. Use Fabric as high-level wrapper around paramiko
C. Extend execnet with additional features
D. Use different SSH library (asyncssh, ssh2-python)

**Decision:**

Use paramiko directly (Option A).

**Consequences:**

**Positive:**
- Simpler dependency tree (paramiko only, no Fabric)
- Direct control over SSH operations
- Easier to understand and debug
- Lower-level access for host key management
- No abstraction layer overhead

**Negative:**
- More manual implementation required
- No Fabric convenience features (context managers, task composition)
- Developers must understand paramiko API directly

---

### integration-strategy

**Context:**

batou already has execnet for SSH-based deployments. Want to test paramiko integration without risking production deployments. Need strategy for coexistence or replacement.

**Options:**

A. Build experimental `batou ssh` command as separate feature, don't touch execnet code
B. Replace execnet with paramiko in existing deployment code
C. Create parallel implementation that can be toggled
D. Extend execnet with paramiko integration

**Decision:**

Build experimental `batou ssh` command as separate feature (Option A).

**Consequences:**

**Positive:**
- Safe experimentation without production risk
- Can be removed if approach doesn't work
- No impact on existing deployments
- Clear separation of concerns
- Easy to evaluate paramiko independently

**Negative:**
- Code duplication with execnet (acceptable for experimental feature)
- Users must use separate command for SSH operations
- No migration path defined (intentional for experimental feature)

---

### host-key-management

**Context:**

Unknown host keys cause interactive prompts during SSH connections. These prompts cannot be answered in automated deployment contexts and garble console output. Need strategy for handling host key verification.

**Options:**

A. Implement pre-flight host key check with auto-add capability
B. Disable host key checking entirely (insecure)
C. Require manual host key management before deployment
D. Use SSH proxy command that handles host keys

**Decision:**

Implement pre-flight host key check with auto-add capability (Option A).

**Consequences:**

**Positive:**
- Fail-fast with clear error if hostkey verification fails
- Avoids garbled console output from interactive prompts
- Maintains security through host key verification
- Supports both strict checking and auto-add modes
- Clear error messages guide users to resolution

**Negative:**
- Additional connection step before command execution
- Requires known_hosts file management
- Auto-add mode reduces security if misconfigured

---

### module-structure

**Context:**

Need to organize SSH functionality in batou codebase. Feature is experimental and may be removed. Should follow batou's existing module organization patterns.

**Options:**

A. Create new `src/batou/ssh.py` module with SSHClient class
B. Add SSH functionality to existing `src/batou/remote.py` module
C. Create `src/batou/lib/ssh/` package with multiple modules
D. Implement in `src/batou/main.py` alongside CLI commands

**Decision:**

Create new `src/batou/ssh.py` module with SSHClient class (Option A).

**Consequences:**

**Positive:**
- Clear module boundaries for experimental feature
- Easy to remove if needed
- Follows batou's flat module structure
- Self-contained implementation
- Simple import path

**Negative:**
- Adds new top-level module (acceptable for experimental feature)

---

### sshclient-interface

**Context:**

SSHClient class needs methods for host key management and command execution. Interface should be simple, pythonic, and cover the requirements.

**Options:**

A. Two methods: `ensure_known_host()` and `run(command, check=True)`
B. Single method that handles both host key check and command execution
C. Context manager pattern with automatic host key checking
D. Multiple fine-grained methods for each operation

**Decision:**

Two methods: `ensure_known_host()` and `run(command, check=True)` (Option A).

**Consequences:**

**Positive:**
- Clear separation of concerns
- Explicit host key management
- Flexible execution (check parameter for error handling)
- Simple, pythonic interface
- Easy to test individual methods

**Negative:**
- Two-step process (check then run)
- User must call `ensure_known_host()` before `run()` (documented in docstring)

---

### error-handling

**Context:**

SSH operations can fail in multiple ways: host key mismatch, connection failures, authentication errors, command execution failures. Need consistent error handling strategy.

**Options:**

A. Use batou's ReportingException for user-facing errors
B. Use standard Python exceptions (paramiko exceptions)
C. Wrap all errors in custom SSHException hierarchy
D. Let paramiko exceptions propagate directly

**Decision:**

Use batou's ReportingException for user-facing errors (Option A).

**Consequences:**

**Positive:**
- Consistent with batou's error handling patterns
- Clear error messages for users
- Integration with batou's output system
- Familiar error handling for batou developers

**Negative:**
- Requires exception wrapping layer
- Additional code for error message formatting

---

### ssh-config-parsing

**Context:**

batou environments already have SSH configuration in ssh_config files. Need to decide whether to parse these files directly or use paramiko's SSHConfig parsing.

**Options:**

A. Use paramiko's SSHConfig parser directly
B. Reuse batou's existing SSH config parsing code
C. Parse SSH config files manually with custom logic
D. Require users to duplicate SSH configuration

**Decision:**

Use paramiko's SSHConfig parser directly (Option A).

**Consequences:**

**Positive:**
- Standard OpenSSH configuration parsing
- No code duplication with batou's config parsing
- Paramiko handles edge cases and newer directives
- Well-tested implementation

**Negative:**
- Different config parsing than batou's execnet (acceptable for experimental feature)
- May have subtle differences in directive support

---

### cli-command-integration

**Context:**

Need to add `batou ssh` command to CLI. Command must access environment configuration and host information. Should follow existing CLI command patterns.

**Options:**

A. Add ssh command in `src/batou/main.py` using existing CLI patterns
B. Create separate CLI module for SSH commands
C. Use click/typer subcommand pattern
D. Make SSH functionality library-only, no CLI

**Decision:**

Add ssh command in `src/batou/main.py` using existing CLI patterns (Option A).

**Consequences:**

**Positive:**
- Consistent with existing batou CLI structure
- Simple command registration
- Follows established patterns
- Easy to discover via `batou --help`

**Negative:**
- Adds experimental command to main CLI (acceptable, clearly marked experimental)

---

## 5. Appendixes

### 5.1 Module Structure

```
src/batou/
├── ssh.py              # New SSHClient class
├── main.py             # Add ssh command
└── ...
```

### 5.2 SSHClient Interface

Methods:
- `ensure_known_host()` - Pre-flight host key verification
- `run(command, check=True)` - Execute remote command

### 5.3 CLI Command Signature

```bash
batou ssh <environment> <host> <command>
```

### 5.4 Dependencies

Add to pyproject.toml:
- paramiko>=3.0.0

### 5.5 Out of Scope

- Integration with execnet deployment code
- Replacement of execnet in production
- Parallel command execution
- Interactive sessions
- File transfer (SFTP)
- Port forwarding
