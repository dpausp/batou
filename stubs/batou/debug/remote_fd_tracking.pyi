from pathlib import Path
from posix import DirEntry
from typing import Any, TypedDict

class FDTrackingStats(TypedDict, total=False):
    total_opens: int
    total_closes: int
    open_fds: int
    fd_leak: bool
    leaked_fds: list[tuple[int, str, str, str]]
    logs: list[str]
    fd_records: list[Any]

def _track_fd_close(fd: int) -> None: ...
def _track_fd_open(fd: int, path: DirEntry | str | Path, mode: str = ...) -> None: ...
def get_remote_fd_tracking_stats() -> FDTrackingStats: ...
def init_remote_fd_tracking(track_fds_level: int) -> None: ...
def install_remote_fd_tracking_hook() -> None: ...
