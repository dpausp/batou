# Software Design Description
## For Batou Debug Settings

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

This SDD documents the design decisions for the Debug Settings system in batou, including the `batou debug` command, environment variable-based configuration, and user information integration. The document targets developers and maintainers who need to understand the architecture and design rationale for debugging capabilities.

### 1.2 Subject Scope

The Debug Settings system provides environment variable-based configuration for debugging behavior, a command to inspect available settings, and user feedback during deployment. This SDD covers the `DebugSettings` class, the `batou debug` command architecture, output integration, and RPC-based remote propagation mechanism. The CLI `--debug` flag and secrets encryption debugging are out of scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| MADR | Markdown Architecture Decision Record - A structured format for documenting architectural decisions |
| SRS | Software Requirements Specification - A document that describes intended purpose, requirements, and nature of software |
| SDD | Software Design Document - A document that describes intended purpose, requirements, and nature of software |

### 1.4 References

- SRS: Debug Settings (F-005-debug-settings)
- Pydantic Settings documentation for BaseSettings and model reflection
- batou output system documentation

### 1.5 Document Overview

This SDD follows IEEE 1016 structure with sections for introduction, design overview, design views, and decisions. MADR pattern documents all significant architectural decisions. No complex design views are required as the system follows straightforward patterns.

## 2. Design Overview

### 2.1 Stakeholder Concerns

Developers need to understand how to add new debug settings and how the `batou debug` command discovers them dynamically. Operators need consistent behavior across local and remote deployments. Users need discoverable debugging capabilities without learning CLI flags.

### 2.2 Selected Viewpoints

No detailed design views are required. The system uses straightforward composition (Pydantic Settings model) and interaction (command-line invocation patterns) that do not warrant separate view documentation.

## 3. Design Views

Not required. The system design is sufficiently captured in the MADR decisions below.

## 4. Decisions

### D-001: Use Pydantic Settings for Environment Variable Parsing

**Context:**

The Debug Settings system must read environment variables with prefix `BATOU_`, perform automatic type conversion (bool, int, enum), validate values, and provide sensible defaults. Manual environment variable parsing would be error-prone and duplicate existing framework capabilities.

**Options:**

A. Manual environment variable parsing using `os.environ` with manual type conversion and validation
B. Use Pydantic Settings BaseSettings framework with automatic parsing and validation
C. Use a different configuration framework (e.g., python-dotenv, configargparse)

**Decision:**

Use Pydantic Settings BaseSettings (Option B).

**Consequences:**

**Positive:**
- Automatic type conversion for bool, int, enum types
- Built-in validation with clear error messages
- Declarative field definitions reduce code duplication
- Case-insensitive environment variable names handled automatically
- Model reflection enables dynamic discovery for `batou debug` command

**Negative:**
- Adds pydantic-settings as dependency (already present in project)
- Less control over parsing edge cases compared to manual implementation

---

### D-002: Reflection-Based Settings Discovery for `batou debug` Command

**Context:**

The `batou debug` command must display all available debug settings with their names, environment variable names, possible values, descriptions, and current values. Hardcoding a list of settings would require manual updates whenever a new setting is added.

**Options:**

A. Hardcoded list of settings in command implementation
B. Reflection over Pydantic model fields to discover settings dynamically
C. Maintain a separate registry of settings updated by developers

**Decision:**

Use Pydantic model reflection (Option B).

**Consequences:**

**Positive:**
- Automatic discovery of new settings without code changes in command
- Settings and descriptions remain single-source-of-truth in model definition
- Extensible design supports future settings without maintenance burden
- Follows DRY principle by avoiding duplicate lists

**Negative:**
- Requires understanding of Pydantic model internals for maintenance
- Output format depends on model structure, less manual control

---

### D-003: Int Verbosity Level for FD Tracking

**Context:**

FD tracking configuration should use a single setting to control verbosity instead of multiple interdependent flags.

**Options:**

A. Use two separate boolean flags (track_fds, track_fds_verbose) (considered for backward compatibility)
B. Use enum with values none|simple|verbose
C. Use int verbosity level (0 = disabled, 1 = simple, 2 = verbose)

**Decision:**

Use int verbosity level (Option C).

**Consequences:**

**Positive:**
- Single setting for all verbosity levels
- Clear progression from disabled to simple to verbose
- No dependency between separate settings
- Easier to display in table format (single value column)
- Extensible for future verbosity levels if needed

**Negative:**
- Users must understand numeric levels (0, 1, 2) instead of self-documenting boolean names
- Less clear at a glance what level 2 does compared to verbose flag

---

### D-004: `describe()` Method for Setting Information

**Context:**

The `batou debug` command needs structured information about all settings including field names, environment variable names, descriptions, possible values, and current values. Direct reflection in the command implementation would mix concerns.

**Options:**

A. Perform reflection directly in `batou debug` command implementation
B. Add `describe()` method to DebugSettings class that returns structured data
C. Create separate SettingsDescriptor class to extract and format information

**Decision:**

Add `describe()` method to DebugSettings class (Option B).

**Consequences:**

**Positive:**
- Clear separation between settings model and display logic
- Testable unit for setting information extraction
- Method can be reused in other contexts (e.g., documentation generation)
- Settings class remains self-contained

**Negative:**
- Adds method to model class (minor concern, stays within single responsibility)

---

### D-005: Pydantic Field Docstrings for Setting Descriptions

**Context:**

Setting descriptions must be one-liners displayed in `batou debug` command output. Storing descriptions separately would require synchronization with field definitions.

**Options:**

A. Store descriptions in separate data structure (dict, list)
B. Use Pydantic field docstrings as description source
C. Generate descriptions from field names automatically

**Decision:**

Use Pydantic field docstrings (Option B).

**Consequences:**

**Positive:**
- Descriptions co-located with field definitions
- Single source of truth for setting metadata
- Standard Pydantic pattern, idiomatic usage
- Accessible via reflection for `describe()` method

**Negative:**
- Descriptions embedded in code, less accessible for documentation tools
- Requires maintaining docstring quality and consistency

---

### D-006: Tabular Output for `batou debug` Command

**Context:**

The `batou debug` command must display all debug settings with field name, environment variable name, possible values, and current values. Multiple formats are possible (tables, sections, lists).

**Options:**

A. Tabular format with columns for each attribute
B. Sectioned format with one section per setting
C. List format with key-value pairs per setting

**Decision:**

Tabular format (Option A).

**Consequences:**

**Positive:**
- Easy to scan and compare settings
- Consistent alignment improves readability
- Efficient use of vertical space
- Familiar CLI table format for users

**Negative:**
- May wrap on narrow terminals
- Less space for longer descriptions (mitigated by one-liner requirement)

---

### D-007: Method Name is `show()`

**Context:**

DebugSettings class needs a method to display debug settings information and command hint. The method name should be clear, concise, and without outdated terminology.

**Options:**

A. `log_expert_flags()` (considered for historical context)
B. `show_debug_settings()`
C. `show()`
D. `log_debug_output()`

**Decision:**

Method name is `show()` (Option C).

**Consequences:**

**Positive:**
- Short, clear name matches action
- Generic enough to cover both flags display and command hint
- Follows simplicity principle

**Negative:**
- Less descriptive than `show_debug_settings()` (mitigated by context in DebugSettings class)

---

### D-008: Command Hint Integration in Deployment Output

**Context:**

The `batou deploy` output must show a hint to the `batou debug` command at an appropriate location. The hint should indicate the command's purpose without being verbose.

**Options:**

A. Show hint always at deployment start
B. Show hint only when no debug flags are active
C. Show hint only when debug flags are active
D. Show hint only on deployment errors

**Decision:**

Show hint always at deployment start (Option A).

**Consequences:**

**Positive:**
- Users always aware of `batou debug` command existence
- Consistent behavior regardless of deployment state
- Meets requirement for discoverability
- Simple implementation, no conditional logic

**Negative:**
- May add noise for experienced users who already know the command (minor concern)

---

### D-009: Severity of Command Hint Based on Debug State

**Context:**

The command hint should use appropriate severity level (info vs warning) based on whether debug settings are active. Active debug settings signal expert mode and deserve warning visibility.

**Options:**

A. Always use info severity
B. Always use warning severity
C. Warning when debug settings active, info otherwise
D. Warning when debug settings active, no hint otherwise

**Decision:**

Warning when debug settings active, info otherwise (Option C).

**Consequences:**

**Positive:**
- Warning visibility when debug mode is enabled (important for production)
- Less intrusive info level for normal operation
- Provides visual distinction between debug and normal modes
- Matches existing pattern of "WARNING EXPERT/DEBUG FLAGS ENABLED"

**Negative:**
- Requires conditional logic to determine current state
- Inconsistent severity for same hint message (acceptable given context)

---

### D-010: Integration with `batou check` Command

**Context:**

The `batou check` command performs local consistency checks without execnet overhead. The question is whether debug settings information should be displayed during `batou check` similar to `batou deploy`.

**Options:**

A. Show debug settings only in `batou deploy`
B. Show debug settings in both `batou deploy` and `batou check`
C. Show debug settings only in `batou check`
D. Make debug settings display configurable per command

**Decision:**

Show debug settings in both `batou deploy` and `batou check` (Option B).

**Consequences:**

**Positive:**
- Consistent user experience across deployment commands
- Debug settings visibility even during local validation
- Users can verify debug configuration before full deployment

**Negative:**
- Additional output in `batou check` command (minor concern, useful information)

---

### D-011: No Additional Flags for `batou debug` Command

**Context:**

The `batou debug` command could provide optional flags for formatting (e.g., `--json`, `--verbose`, `--export`). The SRS specifies no extra flags.

**Options:**

A. Implement with no additional flags
B. Add `--json` flag for machine-readable output
C. Add `--verbose` flag for extended descriptions
D. Add `--export` flag to generate environment variable declarations

**Decision:**

No additional flags (Option A).

**Consequences:**

**Positive:**
- Simple, focused command interface
- No flag proliferation (anti-pattern)
- Future extension points remain available
- Matches SRS requirement precisely

**Negative:**
- No machine-readable format for scripts (future enhancement if needed)
- Less flexibility for advanced use cases (acceptable for MVP)

---

### D-012: Error Handling Strategy for Invalid Environment Variables

**Context:**

Invalid environment variable values should be detected and reported to users. Pydantic provides validation, but the question is how and when to surface these errors.

**Options:**

A. Fail fast with clear error message at startup
B. Use default values silently and log warning
C. Continue with partial configuration and warn only for invalid values
D. Attempt automatic correction with fallback

**Decision:**

Fail fast with clear error message at startup (Option A).

**Consequences:**

**Positive:**
- Prevents deployment with invalid configuration
- Clear error messages guide users to correct values
- No silent failures or unexpected behavior
- Matches reliability requirement (REQ-FUNC-001-003)

**Negative:**
- Blocks deployment for any invalid value (desired behavior for reliability)

---

### D-013: Remote Propagation via RPC

**Context:**

Debug settings must be applied consistently on remote hosts. Settings are configured locally but must influence remote deployment behavior. The local host serializes debug settings and transmits them via RPC to remote hosts for reconstruction.

**Options:**

A. Propagate all debug settings via RPC (model_dump + reconstruction) to remote hosts
B. Propagate only non-default settings to remote hosts via RPC
C. Do not propagate, require manual remote configuration
D. Use separate configuration file for remote hosts

**Decision:**

Propagate all debug settings via RPC to remote hosts (Option A).

**Consequences:**

**Positive:**
- Consistent debugging behavior across all hosts
- Automatic propagation without manual intervention
- Ensures identical settings on all hosts including defaults
- Type-safe serialization and reconstruction via Pydantic model_dump
- Remote hosts receive complete settings state without environment variable dependencies

**Negative:**
- Adds RPC call overhead for settings propagation (minor)
- Requires remote hosts to reconstruct settings from serialized data

---

## 5. Appendixes

### 5.1 Pydantic Field Example

Example Pydantic field definition with docstring for `describe()` method:

```python
track_fds: Literal[0, 1, 2] = 0  # FD tracking verbosity level (0=disabled, 1=simple, 2=verbose)
```

### 5.2 Environment Variable Value Formats

Supported value formats:

- Boolean: `true`/`false`, `TRUE`/`FALSE`, `1`/`0`
- Integer: numeric values
- Enum: specific string values defined per setting (e.g., `full`|`summary`|`none` for `show_diff`)

### 5.3 User Output Text

- Warning header: "WARNING EXPERT/DEBUG FLAGS ENABLED"
- Default state message: "No expert/debug flags enabled"
- Command hint: "Use `batou debug` command to see all available debug settings"

### 5.4 Out of Scope

The CLI `--debug` / `-d` flag is out of scope for this design. Secrets encryption debugging is out of scope.
