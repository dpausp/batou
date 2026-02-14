from pydantic_settings import BaseSettings
from typing import (
    Annotated,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Union,
)

def _int_to_literal(value: int | str) -> int | str: ...
def get_debug_settings() -> DebugSettings: ...
def reset_debug_settings(): ...
def set_debug_settings(value: Optional[DebugSettings]): ...

class DebugSettings(BaseSettings):
    """Batou expert/debug configuration settings from environment variables."""

    # Diff control
    show_diff: Literal["full", "summary", "none"]
    show_secret_diffs: bool

    # FD tracking
    track_fds: Annotated[Literal[0, 1, 2], Any]
    fd_output_dir: str

    # Profiling
    profile: bool
    profile_lines: int

    def describe(self) -> list[dict[str, Any]]: ...
    def show(self): ...
