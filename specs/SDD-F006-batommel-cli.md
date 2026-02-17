# SDD-F006: Batommel CLI Consolidation

**Status:** Design
**Feature:** F-006 - Batommel CLI Consolidation
**Date:** 2026-02-17
**Mode:** Refactor (behavior-preserving)

---

## 1. Introduction

### 1.1 Purpose

This Software Design Document (SDD) describes the consolidation of batou's standalone maintenance CLIs (`batou-check`, `batou-migrate-toml`) into a unified `batommel` CLI with subcommands. This refactoring improves discoverability and reduces entry point proliferation while maintaining all existing functionality.

### 1.2 Scope

- Create new `batommel` top-level CLI command
- Convert `migrate_toml.py` from argparse to Typer CLI framework
- Consolidate `check` and `migrate-toml` as subcommands
- Remove standalone entry points from pyproject.toml
- Preserve all existing functionality and UX

### 1.3 Design Goals

- **Unified Interface:** Single entry point for operational tooling
- **Discoverability:** Subcommands automatically listed in help output
- **Consistency:** Both subcommands use Typer patterns with Rich integration
- **Zero Functional Change:** Behavior-preserving refactoring
- **Clean Break:** No backward compatibility shims per CODEX Article 4

---

## 2. Architectural Overview

### 2.1 Current State

Two standalone CLI entry points with inconsistent frameworks:

| Entry Point | Module | Framework | Lines |
|-------------|--------|-----------|-------|
| `batou-check` | `batou.check` | Typer | 592 |
| `batou-migrate-toml` | `batou.migrate_toml` | argparse | 331 |

Current pyproject.toml:
```toml
[project.scripts]
batou = "batou.main:main"
batou-check = "batou.check:main_cli"
batou-migrate-toml = "batou.migrate_toml:main"
```

### 2.2 Target Structure

```toml
[project.scripts]
batou = "batou.main:main"
batommel = "batou.batommel:app"
```

Target file structure:
```
src/batou/
├── batommel/
│   └── __init__.py       # Main app with subcommand registration
├── check.py              # Remains, provides app for subcommand
├── migrate_toml.py       # Converted to Typer, provides app
└── toml_to_ini.py        # New: TOML → INI conversion subcommand
```

### 2.3 Module Responsibilities

| Module | Responsibility | Change Type |
|--------|---------------|-------------|
| `batommel/__init__.py` | Main Typer app with subcommand registration | New |
| `check.py` | Provides `app` for check subcommand | No change |
| `migrate_toml.py` | Convert argparse to Typer, provide `app` | Convert |
| `toml_to_ini.py` | TOML → INI reverse conversion subcommand | New |

---

## 3. Design Views

### 3.1 Composition View

**Viewpoint:** Composition - System assembly from constituent parts

The `batommel` CLI is a thin dispatcher that delegates to existing subcommand implementations:

```
batommel (entry point)
    │
    └── batou.batommel:app (main Typer app)
            │
            ├── batou.check:app (check subcommand)
            │       └── CheckCommand class
            │
            ├── batou.migrate_toml:app (migrate-toml subcommand)
            │       └── Migration functions
            │
            └── batou.toml_to_ini:app (toml-to-ini subcommand)
                    └── Reuses config_toml.to_legacy_format()
```

**Key Design Decision:** Existing modules remain self-contained. The batommel package only handles registration, not implementation.

### 3.2 Interface View

**Viewpoint:** Interface - Externally visible interfaces

| Interface | Type | Contract |
|-----------|------|----------|
| `batommel` | CLI entry | `batommel [OPTIONS] COMMAND [ARGS]` |
| `batommel check` | Subcommand | Same as former `batou-check` |
| `batommel migrate-toml` | Subcommand | Same as former `batou-migrate-toml` |
| `batommel toml-to-ini` | Subcommand | Converts environment.toml → environment.cfg |

---

## 4. Decisions

### D-001: Use Typer CLI Framework

**Context:** The check.py module already uses Typer with Rich integration. The migrate_toml.py module uses argparse, creating inconsistency.

**Options:**

1. Keep argparse for migrate_toml.py - minimizes changes but creates inconsistent UX
2. Convert migrate_toml.py to Typer - provides consistent interface and help formatting
3. Use click directly - more verbose than Typer, less alignment with existing patterns

**Decision:** Convert migrate_toml.py to Typer.

**Consequences:**

- (+) Consistent CLI patterns across all subcommands
- (+) Rich-formatted help output automatically
- (+) Annotated type hints for better IDE support
- (-) Requires converting argparse to Typer patterns

**Constraint Mapping:** C-001-typer-pattern (MUST)

---

### D-002: Subcommand Registration via add_typer()

**Context:** Typer supports multiple patterns for subcommand registration. Need to choose the most maintainable approach.

**Options:**

1. `app.add_typer()` with explicit naming - clear control over subcommand names
2. `app.command()` decorator on each function - simpler but less flexible
3. `typer.Typer()` in each module with app import - circular dependency risk

**Decision:** Use `app.add_typer()` pattern with explicit naming.

**Implementation:**
```python
# batommel/__init__.py
import typer
from batou.check import app as check_app
from batou.migrate_toml import app as migrate_app
from batou.toml_to_ini import app as toml_to_ini_app

app = typer.Typer(
    no_args_is_help=True,
    help="Batou operational maintenance and migration tooling.",
)

app.add_typer(check_app, name="check")
app.add_typer(migrate_app, name="migrate-toml")
app.add_typer(toml_to_ini_app, name="toml-to-ini")
```

**Consequences:**

- (+) Clear separation between registration and implementation
- (+) Subcommand names explicitly controlled (kebab-case: `migrate-toml`)
- (+) Each module remains independently testable
- (+) No circular dependencies

**Constraint Mapping:** C-002-subcommands (MUST)

---

### D-003: Remove Old Entry Points (No Backward Compatibility)

**Context:** CODEX Article 4 mandates no backward compatibility - clean break from legacy patterns.

**Options:**

1. Keep old entry points with deprecation warnings - violates CODEX Article 4
2. Remove old entry points completely - clean break, no transitional support

**Decision:** Remove `batou-check` and `batou-migrate-toml` entry points completely.

**Consequences:**

- (+) Clean pyproject.toml with no duplicate functionality
- (+) Users migrate immediately or don't
- (+) No maintenance burden for deprecated paths
- (-) Users must update scripts/docs referencing old commands

**Constraint Mapping:** C-003-backward-compat-entry-points (MUST)

---

### D-004: Keep Source Files as Subcommand Modules

**Context:** Could move implementation into batommel package or keep files in original locations.

**Options:**

1. Move check.py and migrate_toml.py into batommel/ package - more file movement, larger diff
2. Keep files in place, only create batommel/ package for registration - minimal code movement

**Decision:** Keep files in place with minimal changes.

**Rationale:**
- check.py requires no changes (already provides `app`)
- migrate_toml.py only needs argparse→Typer conversion
- batommel package is thin registration layer only
- Preserves git history and code ownership

**Consequences:**

- (+) Minimal code movement
- (+) Clear separation of concerns
- (+) Each module independently usable and testable
- (-) Two locations for CLI-related code (batommel/ and root modules)

**Constraint Mapping:** C-004-keep-source-files (MUST)

---

### D-005: Maintain Rich Output Formatting

**Context:** check.py uses Rich tables for configuration display. migrate_toml.py uses plain print statements.

**Options:**

1. Add Rich formatting to migrate_toml.py - enhanced UX
2. Keep migrate_toml.py with print statements - minimal changes

**Decision:** Keep migrate_toml.py with print statements (no Rich addition).

**Rationale:**
- Refactor mode = behavior preservation
- Adding Rich would be enhancement, not refactoring
- Current output is functional for migration tooling
- Future enhancement if UX feedback indicates need

**Consequences:**

- (+) Strict behavior preservation
- (+) Smaller change scope
- (-) Inconsistent output formatting across subcommands

**Constraint Mapping:** C-005-rich-output (MUST - for check subcommand)

---

### D-009: Add toml-to-ini Subcommand for Reverse Conversion

**Context:** Users may need to generate INI from TOML for backward compatibility scenarios (e.g., sharing configs with environments that haven't migrated yet).

**Options:**

1. Implement new conversion logic from scratch - duplicates existing patterns
2. Reuse existing `to_legacy_format()` from config_toml.py - minimal code, consistent
3. Require users to manually convert - poor UX

**Decision:** Create new `toml_to_ini.py` module that reuses `to_legacy_format()` from `config_toml.py`.

**Consequences:**

- (+) Minimal new code - reuses existing conversion logic
- (+) Consistent with existing TOML handling patterns
- (+) Complete bidirectional conversion capability
- (-) Adds third subcommand to batommel

**Constraint Mapping:** C-006-reuse-legacy-format (MUST)

---

### D-010: Consistent CLI Pattern for toml-to-ini

**Context:** The toml-to-ini command should follow the same CLI pattern as migrate-toml for consistency.

**Options:**

1. Different option names/semantics - confusing for users
2. Same pattern (path, --output, --dry-run, --force) - consistent UX
3. Simpler subset of options - less flexible

**Decision:** Use same CLI pattern as migrate-toml with identical option semantics.

**Consequences:**

- (+) Predictable interface - users familiar with migrate-toml can use toml-to-ini
- (+) Consistent help text and error messages
- (+) Same dry-run and force behaviors

**Constraint Mapping:** C-007-cli-pattern-consistency (MUST)

---

## 5. Module Design

### 5.1 Main App Module (`batommel/__init__.py`)

**D-006:** Create thin registration layer

**Responsibilities:**

- Create main Typer app with `no_args_is_help=True`
- Register check, migrate-toml, and toml-to-ini subcommands
- Provide help text describing batommel purpose

**Public Interface:**
```python
import typer
from batou.check import app as check_app
from batou.migrate_toml import app as migrate_app
from batou.toml_to_ini import app as toml_to_ini_app

app = typer.Typer(
    no_args_is_help=True,
    help="Batou operational maintenance and migration tooling.",
)

app.add_typer(check_app, name="check")
app.add_typer(migrate_app, name="migrate-toml")
app.add_typer(toml_to_ini_app, name="toml-to-ini")
```

**Entry Point:** `batommel = "batou.batommel:app"`

---

### 5.2 Check Subcommand (`check.py`)

**D-007:** No changes required to check.py

The existing check.py already:
- Provides `app = typer.Typer(no_args_is_help=True, ...)`
- Uses `Annotated` type hints throughout
- Integrates Rich tables for configuration display
- Exposes `@app.command()` decorated `check()` function

**No migration needed.** Module is already compliant with target architecture.

---

### 5.3 Migrate-TOML Subcommand (`migrate_toml.py`)

**D-008:** Convert argparse to Typer CLI

**Current State (argparse):**
```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument("path", nargs="?", default="environments", ...)
    parser.add_argument("-o", "--output", ...)
    parser.add_argument("-n", "--dry-run", action="store_true", ...)
    parser.add_argument("-f", "--force", action="store_true", ...)
    args = parser.parse_args()
    # ... implementation
```

**Target State (Typer):**
```python
import typer
from typing import Annotated

app = typer.Typer(
    no_args_is_help=True,
    help="Migrate batou environment.cfg to environment.toml.",
)

@app.command()
def migrate(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to environments directory or specific environment"
        ),
    ] = "environments",
    output: Annotated[
        str | None,
        typer.Option("-o", "--output", help="Output file path"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("-n", "--dry-run", help="Show what would be converted"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Overwrite existing files"),
    ] = False,
):
    """Migrate batou environment.cfg to environment.toml."""
    # ... implementation (unchanged)
```

**Migration Changes:**

| Aspect | Before (argparse) | After (Typer) |
|--------|------------------|---------------|
| Argument parsing | `parser.parse_args()` | Function parameters |
| Type inference | Manual string checks | Annotated type hints |
| Help formatting | argparse default | Typer/Rich automatic |
| Entry point | `main()` function | `app` Typer instance |

**Preserved Elements:**
- All core migration logic (infer_type, convert_config_to_toml, etc.)
- File handling and path resolution
- Error messages and output format
- Exit codes and status reporting

---

### 5.4 TOML-to-INI Subcommand (`toml_to_ini.py`)

**D-011:** New module for reverse conversion

**Responsibilities:**

- Create Typer app for toml-to-ini subcommand
- Load TOML configuration using existing `load_toml_config()` from `config_toml.py`
- Convert to INI format using `to_legacy_format()` and `_value_to_legacy_string()` from `config_toml.py`
- Write output using `configparser.ConfigParser` for proper INI formatting

**Public Interface:**
```python
import typer
from typing import Annotated
from pathlib import Path
import configparser

from batou.config_toml import load_toml_config, to_legacy_format

app = typer.Typer(
    no_args_is_help=True,
    help="Convert batou environment.toml to environment.cfg.",
)

@app.command()
def convert(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to environments directory or specific environment.toml"
        ),
    ] = "environments",
    output: Annotated[
        str | None,
        typer.Option("-o", "--output", help="Output file path"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("-n", "--dry-run", help="Show what would be generated"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Overwrite existing files"),
    ] = False,
):
    """Convert batou environment.toml to environment.cfg."""
    # Implementation uses:
    # - load_toml_config() to parse TOML
    # - to_legacy_format() to convert to legacy structure
    # - configparser.ConfigParser to write INI
```

**Reused Components from config_toml.py:**

| Function | Purpose |
|----------|---------|
| `load_toml_config(content, source_file)` | Parse and validate TOML content |
| `to_legacy_format(config)` | Convert Pydantic config to legacy dict |
| `_value_to_legacy_string(value)` | Convert values to INI-compatible strings |

**Constraint Mapping:** C-006-reuse-legacy-format (MUST), C-007-cli-pattern-consistency (MUST)

---

## 6. Entry Point Changes

### 6.1 pyproject.toml Updates

**Before:**
```toml
[project.scripts]
batou = "batou.main:main"
batou-check = "batou.check:main_cli"
batou-migrate-toml = "batou.migrate_toml:main"
```

**After:**
```toml
[project.scripts]
batou = "batou.main:main"
batommel = "batou.batommel:app"
```

**Removed Entry Points:**
- `batou-check` → Use `batommel check`
- `batou-migrate-toml` → Use `batommel migrate-toml`

---

## 7. Command Interface Mapping

| Old Command | New Command | Behavior |
|-------------|-------------|----------|
| `batou-check test` | `batommel check test` | Identical |
| `batou-check -p linux test` | `batommel check -p linux test` | Identical |
| `batou-migrate-toml` | `batommel migrate-toml` | Identical |
| `batou-migrate-toml --dry-run` | `batommel migrate-toml --dry-run` | Identical |
| `batou-migrate-toml envs/prod` | `batommel migrate-toml envs/prod` | Identical |
| (new) | `batommel toml-to-ini` | Converts environment.toml → environment.cfg |
| (new) | `batommel toml-to-ini --dry-run` | Shows what would be generated |
| (new) | `batommel toml-to-ini -o output.cfg` | Writes to specified output file |

---

## 8. Verification Matrix

| Design Decision | Module | Verification Method |
|-----------------|--------|---------------------|
| D-001: Typer framework | migrate_toml.py | Test CLI invocation, check help output |
| D-002: add_typer() pattern | batommel/__init__.py | Test subcommand registration |
| D-003: Remove old entry points | pyproject.toml | Verify entry point removal |
| D-004: Keep source files | check.py, migrate_toml.py | File location verification |
| D-005: Rich output preserved | check.py | Visual verification of table output |
| D-006: Thin registration layer | batommel/__init__.py | Code review, line count < 25 |
| D-007: No check.py changes | check.py | Diff shows no changes |
| D-008: argparse→Typer conversion | migrate_toml.py | Test all CLI options |
| D-009: toml-to-ini subcommand | toml_to_ini.py | Test INI output matches expected format |
| D-010: Consistent CLI pattern | toml_to_ini.py | Verify options match migrate-toml |
| D-011: Reuse to_legacy_format | toml_to_ini.py | Import verification, unit tests |

---

## 9. Constraints Traceability

| Constraint | Level | Decision | Verification |
|------------|-------|----------|--------------|
| C-001-typer-pattern | MUST | D-001, D-008 | Type hints in migrate_toml.py |
| C-002-subcommands | MUST | D-002 | add_typer() in __init__.py |
| C-003-backward-compat-entry-points | MUST | D-003 | pyproject.toml diff |
| C-004-keep-source-files | MUST | D-004 | File structure unchanged |
| C-005-rich-output | MUST | D-005, D-007 | check.py Rich tables preserved |
| C-006-reuse-legacy-format | MUST | D-009, D-011 | Import from config_toml.py |
| C-007-cli-pattern-consistency | MUST | D-010 | Option names match migrate-toml |

---

## 10. References

- [CODEX Article 4: No Backward Compatibility](AGENTS.md#article-4-death-to-all-legacy-and-compatibility)
- [CODEX Article 5: Quality is Non-Negotiable](AGENTS.md#article-5-quality-is-non-negotiable)
- [SDD-F001: Debug Package Refactoring](specs/SDD-F001-debug-package.md) - Style reference
- [IEEE 1016-2009: Software Design Descriptions](/Users/rovodev/.config/opencode/skill/spec-sdd-template/SKILL.md)

---

## Appendix A: CLI Help Output Comparison

### batou-check (current)
```
Usage: batou-check [OPTIONS] ENVIRONMENT
  Fast local consistency check without execnet overhead.
```

### batommel check (target)
```
Usage: batommel check [OPTIONS] ENVIRONMENT
  Fast local consistency check without execnet overhead.
```

### batou-migrate-toml (current)
```
usage: batou-migrate-toml [-h] [-o OUTPUT] [-n] [-f] [path]
Migrate batou environment.cfg to environment.toml
```

### batommel migrate-toml (target)
```
Usage: batommel migrate-toml [OPTIONS] [PATH]
  Migrate batou environment.cfg to environment.toml.
```

### batommel toml-to-ini (new)
```
Usage: batommel toml-to-ini [OPTIONS] [PATH]
  Convert batou environment.toml to environment.cfg.
```

---

## Appendix B: migrate_toml.py Conversion Checklist

- [ ] Create `app = typer.Typer()` instance
- [ ] Add `no_args_is_help=True` to app
- [ ] Convert `path` positional argument to `Annotated[str, typer.Argument()]`
- [ ] Convert `--output` option to `Annotated[str | None, typer.Option()]`
- [ ] Convert `--dry-run` flag to `Annotated[bool, typer.Option()]`
- [ ] Convert `--force` flag to `Annotated[bool, typer.Option()]`
- [ ] Rename `main()` to `migrate()` with `@app.command()` decorator
- [ ] Add docstring for CLI help text
- [ ] Update function body to use parameters instead of `args` object
- [ ] Remove argparse imports
- [ ] Keep `if __name__ == "__main__": app()` for direct execution

---

## Appendix C: toml_to_ini.py Implementation Checklist

- [ ] Create `app = typer.Typer()` instance
- [ ] Add `no_args_is_help=True` to app
- [ ] Import `load_toml_config`, `to_legacy_format` from `batou.config_toml`
- [ ] Import `configparser.ConfigParser` for INI writing
- [ ] Define `path` positional argument with `Annotated[str, typer.Argument()]`
- [ ] Define `--output` option with `Annotated[str | None, typer.Option()]`
- [ ] Define `--dry-run` flag with `Annotated[bool, typer.Option()]`
- [ ] Define `--force` flag with `Annotated[bool, typer.Option()]`
- [ ] Create `convert()` function with `@app.command()` decorator
- [ ] Implement path resolution (file vs directory)
- [ ] Call `load_toml_config()` to parse TOML
- [ ] Call `to_legacy_format()` to get legacy dict
- [ ] Use `ConfigParser` to write INI output
- [ ] Handle dry-run mode (print to stdout)
- [ ] Handle force mode (overwrite existing)
- [ ] Add `if __name__ == "__main__": app()` for direct execution
- [ ] Register in `batommel/__init__.py` with `app.add_typer(toml_to_ini_app, name="toml-to-ini")`

---

**Document End**
