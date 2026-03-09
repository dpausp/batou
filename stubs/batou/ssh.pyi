"""Type stubs for experimental SSH feature.

This is an experimental feature and may change without notice.
Uses paramiko for SSH client operations.
"""

import types
from pathlib import Path
from typing import Self, TypedDict

from batou import ReportingException

class SSHError(ReportingException):
    """SSH-related errors."""

    message: str

    @classmethod
    def from_context(cls, message: str) -> SSHError: ...
    def report(self) -> None: ...

class SSHConfig:
    """Configuration for SSH connection."""

    hostname: str
    ssh_config_path: str | None
    user: str | None
    port: int
    identity_file: str | None
    strict_host_key_check: bool

    def __init__(
        self,
        hostname: str,
        ssh_config_path: str | None = ...,
    ) -> None: ...
    def load_from_file(self, config_path: str) -> None: ...
    @property
    def known_hosts_file(self) -> Path: ...

class CommandResult(TypedDict):
    """Result of SSH command execution."""

    stdout: str
    stderr: str
    returncode: int
    success: bool

class SSHClient:
    """Experimental SSH client using paramiko."""

    config: SSHConfig

    def __init__(self, config: SSHConfig) -> None: ...
    def ensure_known_host(self) -> bool: ...
    def run(
        self,
        command: str,
        check: bool = ...,
    ) -> CommandResult: ...
    def close(self) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None: ...
