from pathlib import Path
from posix import DirEntry
from typing import Any, NotRequired, TypedDict

from batou.debug.fd_tracker import FDTrackingLogEntry

# Type for fd_records dictionary
FDRecordDict = dict[
    str, dict[str, Any]
]  # path -> {"open_count": int, "modes": {}, "stack_traces": []}

class RemoteFDTrackingStats(TypedDict):
    """File descriptor tracking statistics from remote side."""

    total_opens: int
    total_closes: int
    leaked_fds: list[tuple[int, str, str, str]]
    logs: list[FDTrackingLogEntry]
    fd_records: NotRequired[FDRecordDict]

def _track_fd_close(fd: int) -> None: ...
def _track_fd_open(fd: int, path: DirEntry | str | Path, mode: str = ...) -> None: ...
def get_remote_fd_tracking_stats() -> RemoteFDTrackingStats: ...
def init_remote_fd_tracking(track_fds_level: int) -> None: ...
def install_remote_fd_tracking_hook() -> None: ...
