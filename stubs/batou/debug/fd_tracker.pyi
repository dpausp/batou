from collections.abc import Iterable
from typing import Any, NamedTuple, TypedDict

from batou.debug.settings import DebugSettings
from batou.host import Host

class FDTrackingLogEntry(NamedTuple):
    """A single FD tracking log entry."""

    time: str
    count: int
    path: str
    mode: str
    action: str

class FileDescriptorState(NamedTuple):
    """State of an open file for leak detection."""

    path: str
    mode: str
    open_time: str

class FDTrackingStats(TypedDict):
    """File descriptor tracking statistics snapshot."""

    total_opens: int
    total_closes: int
    leaked_fds: list[tuple[int, str, str, str]]
    logs: list[FDTrackingLogEntry]

class FileDescriptorTracker:
    enabled: bool
    verbose: bool
    debug_settings: DebugSettings
    environment_name: str
    fd_records: dict[str, dict[str, Any]]
    original_open: Any
    total_opens: int
    total_closes: int
    remote_opens: dict[str, int]
    _open_fds: dict[int, tuple[str, str, str]]
    _fd_tracking_logs: list[tuple[str, int, str, str, str]]
    _instance: FileDescriptorTracker | None

    def __init__(
        self,
        environment_name: str,
        debug_settings: DebugSettings,
    ) -> None: ...
    def _install_local_hook(self) -> None: ...
    def _track_close(self, fd: int) -> None: ...
    def _track_open(self, fd: int, path: str, mode: str = ...) -> None: ...
    @classmethod
    def cleanup(cls) -> None: ...
    def generate_reports(self, hosts: Iterable[Host]) -> None: ...
    def get_fd_tracking_stats(self) -> dict[str, Any]: ...
    def get_remote_logs(self, gateway: Any) -> dict[str, int] | None: ...
    def install_remote_hook(self, gateway: Any) -> None: ...
    def report(self, location: str = ..., env_name: str | None = ...) -> None: ...
    def show_summary(self) -> None: ...
