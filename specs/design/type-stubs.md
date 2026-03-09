# type-stubs-synchronization

## Context

Batou requires comprehensive type stubs for Python 3.14+ compatibility with `ty` type checker. Current implementation achieves 98.5% file coverage (65 stub files, 3,024 lines) but has critical security vulnerabilities and missing stubs for experimental features and third-party dependencies. Type checking uses 25 override blocks with 70 rules, where 90-92% are necessary due to dynamic architecture (RPC via execnet, runtime component construction).

## Decisions

### yaml-security-fix
- Context: `host.py` uses `yaml.load()` which is vulnerable to arbitrary code execution through YAML deserialization attacks
- Decision: Replace `yaml.load()` with `yaml.safe_load()` in host.py configuration parsing
- Consequences: Eliminates security vulnerability, no functional impact as batou configuration doesn't use YAML object types

### ssh-stub-creation
- Context: Experimental SSH feature in `src/batou/ssh.py` lacks type stub, preventing type safety for new development
- Decision: Create `stubs/batou/ssh.pyi` with Python 3.14+ type syntax for SSH client interfaces
- Consequences: Enables type-safe SSH development, catches runtime errors during type checking

### batommel-deploy-stub
- Context: Public CLI `batommel deploy` command defined in `src/batou/batommel/deploy.py` lacks type stub
- Decision: Create `stubs/batou/batommel/deploy.pyi` for deployment CLI interfaces
- Consequences: Type safety for public CLI commands, improves developer experience

### vfs-sandbox-types
- Context: Virtual filesystem sandbox uses `Any` for 3-4 core operations due to complex dynamic paths
- Decision: Replace `Any` occurrences in vfs_sandbox with proper `Path` and `Protocol` types where feasible
- Consequences: Better type safety, reduced reliance on ty overrides

### service-component-types
- Context: Service component has 5-8 occurrences of `Any` for dynamic configuration and dependencies
- Decision: Define explicit `Protocol` types for service interfaces and configuration schemas
- Consequences: More precise typing, easier refactoring, catches configuration errors earlier

### deployment-types
- Context: Deployment orchestration uses `Any` for multi-host scenarios and dynamic dependency resolution
- Decision: Create `DeploymentHost` and `DependencyGraph` protocols to eliminate `Any` in core deployment logic
- Consequences: Type-safe multi-host deployments, better dependency management

### root-dependencies-types
- Context: Root dependency resolution uses `Any` for dynamic component tree traversal
- Decision: Implement `ComponentTree` protocol with typed parent/child relationships
- Consequences: Type-safe dependency graph operations, clearer deployment model

### ty-override-optimization
- Context: 25 override blocks with 70 rules contain 5-8 unnecessary overrides that could be eliminated through better typing
- Decision: Audit and reduce ty overrides by improving type precision in vfs_sandbox, service, deployment, and root_dependencies modules
- Consequences: Cleaner type configuration, easier maintenance, but requires careful testing to avoid false positives

### execnet-stubs-priority
- Context: RPC calls via execnet channels require pickle-serializable arguments but execnet lacks official stubs
- Decision: Prioritize third-party stub creation for execnet (core RPC mechanism), paramiko (SSH transport), and rich (CLI output)
- Consequences: Enables type-safe RPC development, catches serialization errors during type checking, but requires maintenance of external stub packages

### third-party-stubs-scope
- Context: Batou depends on 20+ third-party packages, most without official stubs
- Decision: Create or source stubs only for packages used in public APIs and type-checking boundaries (execnet, paramiko, rich, pytest, setuptools)
- Consequences: Focused effort on high-impact packages, avoids maintaining stubs for internal-use-only dependencies

### incremental-phasing
- Context: 65 existing stub files with 212 `Any` occurrences require systematic improvement across large codebase
- Decision: Implement in 5 phases: security fix, missing stubs, quality improvements, third-party stubs, ty optimization
- Consequences: Manageable risk, incremental value delivery, but extends timeline to completion

### python-314-type-syntax
- Context: Type stubs must support Python 3.14+ syntax while remaining compatible with ty type checker
- Decision: Use modern type syntax (PEP 695 unions, `type` statement, generic type aliases) in all new and updated stubs
- Consequences: Future-proof stubs, cleaner type definitions, requires ty compatibility verification

## Implementation Sequence

### Phase 1: Security Critical
- Fix yaml.load() → yaml.safe_load() in host.py
- Run full test suite to verify no functional regression
- Update type stub if host.py signature changes

### Phase 2: Missing Public Stubs
- Create `stubs/batou/ssh.pyi` for experimental SSH feature
- Create `stubs/batou/batommel/deploy.pyi` for public CLI
- Verify `ty` passes with new stubs
- Document experimental status for SSH stub

### Phase 3: Core Quality Improvements
- Improve vfs_sandbox types (eliminate 3-4 `Any` occurrences)
- Improve service component types (eliminate 5-8 `Any` occurrences)
- Improve deployment types (add DeploymentHost, DependencyGraph protocols)
- Improve root_dependencies types (add ComponentTree protocol)
- Run `uv run tox p` to verify test and type checking passes

### Phase 4: Third-Party Stubs
- Create or source execnet stubs (RPC serialization boundaries)
- Create or source paramiko stubs (SSH transport)
- Create or source rich stubs (CLI output formatting)
- Verify ty override rules for external packages

### Phase 5: Ty Configuration Optimization
- Audit 25 override blocks for reducible rules
- Remove 5-8 unnecessary overrides through better typing
- Document remaining 90-92% necessary overrides (RPC, dynamic architecture)
- Final `uv run tox p` verification

## Verification Matrix

| Component | Stub Coverage | Any Occurrences | Ty Overrides | Priority |
|-----------|---------------|-----------------|--------------|----------|
| Core API | 98.5% | 212 | 25 blocks | High |
| SSH (experimental) | 0% | Unknown | Unknown | Medium |
| batommel/deploy | 0% | Unknown | Unknown | High |
| vfs_sandbox | Complete | 3-4 | Part of core | Medium |
| service | Complete | 5-8 | Part of core | Medium |
| deployment | Complete | Dynamic | Part of core | High |
| root_dependencies | Complete | Dynamic | Part of core | High |
| Third-party | 0% | N/A | N/A | Medium |

## Current State Analysis

### Stub Inventory
- **Total stub files**: 65
- **Total lines**: 3,024
- **File coverage**: 98.5% (core implementation)
- **Type syntax**: Python 3.14+ (modern PEP 695 features)
- **Location**: `stubs/` directory with package structure mirroring `src/batou/`

### Type Configuration
- **Type checker**: `ty` (not mypy)
- **Override blocks**: 25 (70 total rules)
- **Necessary overrides**: 90-92% (RPC serialization, dynamic component construction)
- **Reducible overrides**: 5-8 (better typing possible)
- **Configuration**: `.ty.toml` with project-wide rules

### Quality Issues
- **`Any` occurrences**: 212 across codebase
- **High-priority `Any`**: vfs_sandbox (3-4), service (5-8), deployment, root_dependencies
- **Missing public stubs**: ssh.py, batommel/deploy.py
- **Third-party gaps**: execnet, paramiko, rich, pytest, setuptools

### Architecture Constraints
- **RPC via execnet**: All remote method arguments must be pickle-serializable (no file handles, no local objects)
- **Dynamic components**: Component tree built at runtime via `configure()`, `verify()`, `update()` lifecycle
- **Multi-host deployment**: Dependency resolution crosses host boundaries, requires dynamic graph traversal
- **Bootstrap requirement**: `src/batou/__init__.py` cannot import non-stdlib at module level (except jinja2)

## Security Considerations

### Critical Vulnerability
- **File**: `host.py` configuration parsing
- **Issue**: Uses `yaml.load()` instead of `yaml.safe_load()`
- **Risk**: Arbitrary code execution via YAML deserialization
- **Fix**: Replace with `yaml.safe_load()` (no functional impact, batou config doesn't use YAML object types)
- **Priority**: Phase 1 (immediate)

## References

- Python 3.14 type syntax (PEP 695): https://peps.python.org/pep-0695/
- YAML security advisory: https://pyyaml.org/wiki/PyYAMLDocumentation
- Ty type checker: https://github.com/microsoft/ty
- Execnet serialization: https://execnet.readthedocs.io/
