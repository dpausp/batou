
import asyncio
import threading
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor

from batou.debug.fd_tracker import FileDescriptorTracker
from batou.debug.profiler import Profiler
from batou.debug.settings import DebugSettings
from batou.environment import Environment
from batou.host import Host
from batou.utils import Timer

def main(
    environment: str,
    platform: str | None,
    timeout: int | None,
    dirty: bool,
    consistency_only: bool,
    predict_only: bool,
    check_and_predict_local: bool,
    jobs: int | None,
    provision_rebuild: bool,
): ...

class Connector(threading.Thread):
    host: Host
    deployment: Deployment
    exc_info: tuple[type, Exception, object] | None
    errors: bytes

    def __init__(self, host: Host, sem: threading.Semaphore): ...
    def join(self, timeout: float | None = ...): ...
    def run(self): ...

class ConfigureErrors(Exception):
    errors: list[tuple[set[str], set[str] | None, Exception]]
    all_reporting_hostnames: set[str]

    def __init__(
        self,
        errors: list[tuple[set[str], set[str] | None, Exception]],
        all_reporting_hostnames: set[str],
    ): ...
    def report(self): ...

class Deployment:
    environment: Environment
    dirty: bool
    consistency_only: bool
    predict_only: bool
    jobs: int | None
    timer: Timer
    debug_settings: DebugSettings
    fd_tracker: FileDescriptorTracker | None
    profiler: Profiler
    taskpool: ThreadPoolExecutor | None
    loop: asyncio.AbstractEventLoop | None
    connections: list[Connector]
    _upstream: str | None

    def __init__(
        self,
        environment: Environment | str,
        platform: str | None,
        timeout: int | None,
        dirty: bool,
        jobs: int | None,
        consistency_only: bool = ...,
        predict_only: bool = ...,
        check_and_predict_local: bool = ...,
        provision_rebuild: bool = ...,
    ): ...
    def _connections(self) -> Iterator[Connector]: ...
    def connect(self): ...
    def deploy(self) -> None: ...
    def disconnect(self): ...
    def load(self): ...
    @property
    def local_consistency_check(self) -> bool: ...
    def provision(self): ...
    def summarize(self) -> None: ...
