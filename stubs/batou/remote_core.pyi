from typing import Any

from batou._output import NullBackend

deployment: Deployment | None
environment: Any
target_directory: str
deployment_base: str

def _hg_current_id() -> str: ...
def build_batou() -> None: ...
def cmd(c: str, acceptable_returncodes: list[int] = ...) -> tuple[bytes, bytes]: ...
def deploy(root: str, predict_only: bool = ...) -> None: ...
def ensure_base(base: str) -> str: ...
def ensure_repository(target: str, method: str) -> str: ...
def get_fd_tracking_stats() -> dict[str, Any]: ...
def get_profiling_results() -> dict[str, Any] | None: ...
def git_pull_code(upstream: str, branch: str) -> None: ...
def git_unbundle_code() -> None: ...
def git_update_working_copy(branch: str) -> str: ...
def hg_current_heads() -> list[str]: ...
def hg_pull_code(upstream: str) -> None: ...
def hg_unbundle_code() -> None: ...
def hg_update_working_copy(branch: str) -> str: ...
def lock() -> None: ...
def root_dependencies() -> dict[tuple[str, str], dict[str, Any]]: ...
def setup_deployment(*args: Any) -> bytes: ...
def setup_output(debug: bool) -> None: ...
def whoami() -> str: ...

class CmdError(Exception):
    cmd: str
    returncode: int
    stdout: bytes
    stderr: bytes

    def __init__(
        self,
        cmd: str,
        returncode: int,
        stdout: bytes,
        stderr: bytes,
    ) -> None: ...
    def report(self) -> str: ...

class Deployment:
    env_name: str
    host_name: str
    overrides: dict[str, Any]
    resolve_override: dict[str, str]
    resolve_v6_override: dict[str, str]
    host_data: dict[str, dict[str, Any]]
    secret_files: dict[str, str] | None
    secret_data: set[str] | None
    timeout: int | None
    platform: str | None
    debug_settings_dict: dict[str, Any]
    debug_settings: Any | None
    os_env: dict[str, str]
    environment: Any

    def __init__(
        self,
        env_name: str,
        host_name: str,
        overrides: dict[str, Any],
        resolve_override: dict[str, str],
        resolve_v6_override: dict[str, str],
        secret_files: dict[str, str] | None,
        secret_data: set[str] | None,
        host_data: dict[str, dict[str, Any]],
        timeout: int | None,
        platform: str | None,
        debug_settings_dict: dict[str, Any],
        os_env: dict[str, str] | None = ...,
    ) -> None: ...
    def deploy(self, root: str, predict_only: bool) -> None: ...
    def load(self) -> list[Any]: ...

class Output:
    enable_debug: bool
    backend: NullBackend
    _buffer: list[tuple[str, tuple, dict]]
    _flushing: bool

    def __init__(self, backend: NullBackend) -> None: ...
    def annotate(
        self,
        message: str,
        debug: bool = ...,
        icon: bool | str = ...,
        **fmt: Any,
    ) -> None: ...
    def buffer(self, cmd: str, *args: Any, **kw: Any) -> None: ...
    def clear_buffer(self) -> None: ...
    def error(
        self,
        message: str,
        exc_info: tuple | None = ...,
        debug: bool = ...,
    ) -> None: ...
    def flush_buffer(self) -> None: ...
    def line(
        self,
        message: str,
        debug: bool = ...,
        icon: bool | str | None = ...,
        **fmt: Any,
    ) -> None: ...
    def section(
        self,
        title: str,
        debug: bool = ...,
        **fmt: Any,
    ) -> None: ...
    def sep(self, sep: str, title: str, **fmt: Any) -> None: ...
    def step(
        self,
        context: str,
        message: str,
        debug: bool = ...,
        icon: bool | str | None = ...,
        **fmt: Any,
    ) -> None: ...
    def tabular(
        self,
        key: str,
        value: str,
        separator: str = ...,
        debug: bool = ...,
        **kw: Any,
    ) -> None: ...
    def warn(self, message: str, debug: bool = ...) -> None: ...

class ChannelBackend:
    channel: Any

    def __init__(self, channel: Any) -> None: ...
    def _send(self, output_cmd: str, *args: Any, **kw: Any) -> None: ...
    def line(self, message: str, **fmt: Any) -> None: ...
    def sep(self, sep: str, title: str, **fmt: Any) -> None: ...
    def write(self, content: str, **fmt: Any) -> None: ...
