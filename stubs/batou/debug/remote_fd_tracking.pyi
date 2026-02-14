from pathlib._local import PosixPath
from posix import DirEntry
from typing import (
    Dict,
    Union,
)


def _track_fd_close(fd: int): ...


def _track_fd_open(fd: int, path: Union[DirEntry, str, PosixPath], mode: str = ...): ...


def get_remote_fd_tracking_stats() -> Dict[str, Union[int, bool]]: ...


def init_remote_fd_tracking(track_fds_level: int): ...


def install_remote_fd_tracking_hook(): ...
