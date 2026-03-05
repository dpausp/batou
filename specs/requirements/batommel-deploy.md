# batommel-deploy

## Context

Batou core must have zero TOML dependencies. Users with `batou[batommel]` want to use TOML as source of truth for environment configuration, with automatic conversion to INI format before deployment. This enables TOML-based workflows while keeping batou core lightweight.

## Decisions

### toml-isolation

- Context: TOML configuration support (rtoml dependency) currently in batou core environment.py causes ModuleNotFoundError for users without batommel extra
- Decision: Remove TOML loading from batou core environment.py. TOML handling exclusively in batommel package
- Consequences: Clean separation - batou core = INI only, batommel = TOML wrapper. No TOML imports in core modules

### deploy-wrapper-pattern

- Context: Users with TOML configs need seamless deployment without manual conversion steps
- Decision: batommel deploy command converts TOML to INI then delegates to batou deploy. TOML is source of truth, INI is generated artifact
- Consequences: Single command deployment for TOML users. batommel acts as thin wrapper around batou deploy

### toml-precedence

- Context: When both environment.toml and environment.cfg exist, need clear precedence rules
- Decision: TOML always wins. Manual INI edits are user's responsibility. batommel deploy regenerates INI from TOML on each deployment
- Consequences: Predictable behavior - TOML is configuration source, INI is deployment artifact. Users must edit TOML, not INI

### diff-transparency

- Context: Users need visibility when INI changes before overwriting existing files
- Decision: Show unified diff of changes before writing environment.cfg (unless --force or --quiet flags)
- Consequences: Users see what changed, can review before proceeding. Non-interactive CI/CD can use --quiet to skip diff display

### standard-ini-location

- Context: Generated INI files must be in standard batou locations for compatibility
- Decision: Write environment.cfg to `environments/<env>/environment.cfg` (standard batou location). No temp files
- Consequences: Compatible with existing batou workflows. Generated INI files can be committed to version control if desired

## Requirements

### Functional

**REQ-FUNC-DEPLOY-001**: batommel deploy MUST convert environment.toml to environment.cfg before calling batou deploy

**REQ-FUNC-DEPLOY-002**: batommel deploy MUST call batou deploy with same arguments after generating INI

**REQ-FUNC-DEPLOY-003**: batommel deploy MUST write environment.cfg to `environments/<env>/environment.cfg` (standard location)

**REQ-FUNC-DEPLOY-004**: batommel deploy MUST fail if environment.toml not found in target environment

**REQ-FUNC-DEPLOY-005**: batommel deploy MUST show unified diff before overwriting existing environment.cfg (unless --force or --quiet)

**REQ-FUNC-DEPLOY-006**: batommel deploy MUST overwrite environment.cfg if environment.toml exists (TOML precedence)

### Quality

**NFR-OBS-DEPLOY-001**: Deployment output MUST include conversion status and diff summary

**NFR-USE-DEPLOY-001**: batommel deploy MUST accept same arguments as batou deploy for transparent delegation

## References

- SDD-F006-batommel-cli.md - Batommel CLI architecture
- src/batou/config_toml.py - TOML loading and validation
- src/batou/toml_to_ini.py - TOML to INI conversion implementation
- src/batou/environment.py:206-213 - Current TOML loading (to be removed)
