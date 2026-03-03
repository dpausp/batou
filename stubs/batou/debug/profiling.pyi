from collections.abc import Callable
from typing import Any

def enable_profiling(host_name: str, profile_lines: int, func: Callable) -> Any: ...

class RemoteProfiler:
    def __init__(
        self,
        host_name: str,
        profile_lines: int = ...,
        output_dir: str = ...,
    ): ...
    def get_profiling_results(self) -> dict[str, str] | None: ...
    def profile_execution(self, func: Callable) -> Any: ...
