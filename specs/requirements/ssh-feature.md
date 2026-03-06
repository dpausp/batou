# Software Requirements Specification
## For Batou SSH Feature

## Table of Contents
* [1. Introduction](#1-introduction)
  * [1.1 Document Purpose](#11-document-purpose)
  * [1.2 Product Scope](#12-product-scope)
  * [1.3 Definitions, Acronyms, and Abbreviations](#13-definitions-acronyms-and-abbreviations)
  * [1.4 References](#14-references)
  * [1.5 Document Overview](#15-document-overview)
* [2. Product Overview](#2-product-overview)
  * [2.1 Product Perspective](#21-product-perspective)
  * [2.2 Product Functions](#22-product-functions)
  * [2.3 Product Constraints](#23-product-constraints)
  * [2.4 User Characteristics](#24-user-characteristics)
  * [2.5 Assumptions and Dependencies](#25-assumptions-and-dependencies)
  * [2.6 Apportioning of Requirements](#26-apportioning-of-requirements)
* [3. Requirements](#3-requirements)
  * [3.1 External Interfaces](#31-external-interfaces)
  * [3.2 Functional](#32-functional)
  * [3.3 Quality of Service](#33-quality-of-service)
  * [3.4 Compliance](#34-compliance)
* [4. Verification](#4-verification)
* [5. Appendixes](#5-appendixes)

## 1. Introduction

### 1.1 Document Purpose

This SRS defines requirements for the experimental SSH feature which provides host key management and command execution capabilities. Primary audience: developers evaluating paramiko integration as potential replacement for execnet.

### 1.2 Product Scope

Experimental SSH functionality for host key pre-flight checking and remote command execution. The feature is separate from existing execnet-based deployment code. Integration with existing deployment workflows is out of scope.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| SSH | Secure Shell - cryptographic network protocol for secure data communication |
| Host Key | Cryptographic key used to verify SSH server identity |
| Paramiko | Python implementation of SSHv2 protocol |
| Execnet | Current SSH library used by batou for remote deployments |

### 1.4 References

- batou environment configuration documentation
- SSH config file specification (OpenSSH)
- Paramiko documentation

### 1.5 Document Overview

This SRS follows IEEE 830 structure with sections for introduction, product overview, requirements, verification, and appendixes. Requirements focus on host key management, command execution, and experimental integration. Verification methods map each requirement to test cases.

## 2. Product Overview

### 2.1 Product Perspective

The SSH feature is an experimental subsystem within batou that provides SSH connectivity independent of the existing execnet implementation. The system reads SSH configuration from existing ssh_config files, performs host key verification, and executes remote commands. This feature allows testing paramiko integration without affecting production deployments.

### 2.2 Product Functions

The SSH feature enables:
- Pre-flight host key checking with auto-add capability
- Clear error reporting when hostkey verification fails
- Execution of arbitrary shell commands on remote hosts
- Return of stdout, stderr, and return code from remote commands
- Reuse of existing SSH configuration infrastructure
- CLI command for direct SSH operations

### 2.3 Product Constraints

- Must use paramiko library (no Fabric abstraction layer)
- Must be experimental and separate from execnet deployment code
- Must reuse existing ssh_config file infrastructure
- Must fail-fast on hostkey issues with clear error messages
- May be removed in future if approach proves unsuitable
- Must not affect existing deployment workflows

### 2.4 User Characteristics

Users of the SSH feature are:
- Developers testing paramiko integration
- Operators troubleshooting deployment issues with direct SSH access
- DevOps engineers needing SSH command execution outside deployment context

Users have familiarity with SSH concepts, command-line tools, and batou deployment patterns.

### 2.5 Assumptions and Dependencies

- SSH config files exist and are properly configured
- Paramiko library is available and compatible with target SSH servers
- Host keys are managed through standard OpenSSH known_hosts files
- Remote hosts support SSHv2 protocol

### 2.6 Apportioning of Requirements

All requirements apply to the experimental SSH feature. No integration with existing deployment components is required.

## 3. Requirements

### 3.1 External Interfaces

#### 3.1.1 CLI Interface

The system shall provide `batou ssh <environment> <host> <command>` command for SSH operations.

**CLI Registration Requirements:**
- Command MUST be registered in src/batou/main.py using argparse subparsers
- Help text MUST include "(experimental)" marker
- Command MUST be registered with function ssh_main from main.py

Command arguments:
- environment: batou environment name (required)
- host: target hostname from environment configuration (required)
- command: shell command to execute on remote host (required)
- --check-hostkey: Check host key before connection (default: True)

#### 3.1.2 SSH Configuration Interface

The system shall read SSH configuration from existing ssh_config files used by batou deployments. Configuration includes hostnames, ports, usernames, and identity files.

#### 3.1.3 Host Key Interface

The system shall read and manage host keys through standard OpenSSH known_hosts files. Host key verification shall be performed before command execution.

### 3.2 Functional

#### Host Key Management

**REQ-FUNC-SSH-001**: System shall check host key before establishing SSH connection.

**REQ-FUNC-SSH-002**: System shall fail with clear error if host key verification fails.

**REQ-FUNC-SSH-003**: System shall support auto-adding unknown host keys when configured.

**REQ-FUNC-SSH-004**: System shall prevent interactive prompts that garble console output.

#### Command Execution

**REQ-FUNC-SSH-005**: User shall execute arbitrary shell commands on remote hosts.

**REQ-FUNC-SSH-006**: System shall return stdout from remote command execution.

**REQ-FUNC-SSH-007**: System shall return stderr from remote command execution.

**REQ-FUNC-SSH-008**: System shall return exit code from remote command execution.

**REQ-FUNC-SSH-009**: System shall support optional check parameter to raise exception on non-zero exit codes.

#### SSH Configuration

**REQ-FUNC-SSH-010**: System shall reuse existing ssh_config file infrastructure.

**REQ-FUNC-SSH-011**: System shall parse standard OpenSSH configuration directives.

**REQ-FUNC-SSH-012**: System shall support environment-specific host configurations.

### 3.3 Quality of Service

#### 3.3.1 Reliability

Host key verification failures shall prevent connection establishment with clear error messages. Non-zero exit codes shall be reported to users and optionally raise exceptions.

#### 3.3.2 Observability

Command execution shall provide stdout, stderr, and exit code for debugging. Error messages shall clearly indicate failure cause (host key, connection, command execution).

### 3.4 Compliance

Feature shall follow batou's experimental feature guidelines and be clearly marked as experimental.

## 4. Verification

### 4.1 Test Coverage Requirements

All 12 functional requirements MUST have corresponding test cases with proper traceability.

**Test Traceability Requirements:**
- Each test function MUST include REQ-FUNC-SSH-XXX comment reference
- Test file location: src/batou/tests/test_ssh.py
- Tests MUST cover both success and failure scenarios
- Tests MUST use mocking for paramiko to avoid requiring SSH infrastructure

### 4.2 Verification Matrix

| Requirement ID | Verification Method | Test Function | Test Location | Status |
|----------------|---------------------|---------------|---------------|--------|
| REQ-FUNC-SSH-001 | test | test_host_key_check | test_ssh.py::TestSSHClient::test_ensure_known_host_success | Implemented |
| REQ-FUNC-SSH-002 | test | test_host_key_failure | test_ssh.py::TestSSHClient::test_ensure_known_host_failure | Implemented |
| REQ-FUNC-SSH-003 | test | test_auto_add_host_key | test_ssh.py | **Missing** |
| REQ-FUNC-SSH-004 | test | test_no_interactive_prompt | test_ssh.py | **Missing** |
| REQ-FUNC-SSH-005 | test | test_command_execution | test_ssh.py::TestSSHClient::test_run_success | Implemented |
| REQ-FUNC-SSH-006 | test | test_stdout_capture | test_ssh.py::TestSSHClient::test_run_success | Implemented |
| REQ-FUNC-SSH-007 | test | test_stderr_capture | test_ssh.py::TestSSHClient::test_run_success | Implemented |
| REQ-FUNC-SSH-008 | test | test_exit_code | test_ssh.py::TestSSHClient::test_run_success, test_run_failure_without_check | Implemented |
| REQ-FUNC-SSH-009 | test | test_check_parameter | test_ssh.py::TestSSHClient::test_run_failure_with_check, test_run_failure_without_check | Implemented |
| REQ-FUNC-SSH-010 | test | test_ssh_config_reuse | test_ssh.py::TestSSHConfig::test_init, test_init_no_config_path | Implemented |
| REQ-FUNC-SSH-011 | test | test_openssh_directives | test_ssh.py | **Missing** |
| REQ-FUNC-SSH-012 | test | test_environment_hosts | test_ssh.py | **Missing** |

### 4.3 Missing Test Coverage

The following requirements lack test coverage and MUST be implemented:

1. **REQ-FUNC-SSH-003**: Auto-add host keys when configured
2. **REQ-FUNC-SSH-004**: Prevent interactive prompts that garble console output
3. **REQ-FUNC-SSH-011**: Parse standard OpenSSH configuration directives
4. **REQ-FUNC-SSH-012**: Support environment-specific host configurations

## 5. Appendixes

### 5.1 Experimental Feature Guidelines

**Experimental Marking Requirements:**
- CLI help text MUST include "(experimental)" marker
- Feature MUST be documented as experimental in user-facing documentation
- No backward compatibility guarantees
- Subject to removal if approach proves unsuitable

**Implementation Requirements:**
- Separate from production deployment code (no execnet integration)
- No impact on existing deployment workflows
- Clear separation in codebase (src/batou/ssh.py module)

### 5.2 CLI Command Example

```bash
batou ssh dev webserver1 "uname -a"
```

### 5.3 Out of Scope

- Integration with existing execnet deployment code
- Replacement of execnet in production deployments
- Parallel command execution across multiple hosts
- Interactive SSH sessions
