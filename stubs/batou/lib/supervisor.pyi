from typing import Any, Literal, override

from batou.component import Component
from batou.utils import Address

class Program(Component):
    name: str
    deployment: Literal["hot", "cold"]
    command: str | None
    command_absolute: bool
    options: dict[str, Any]
    args: str
    priority: int
    directory: str | None
    dependencies: tuple[Component, ...] | None
    enable: bool
    supervisor: Supervisor
    config: str
    _evaded: bool

    @override
    def configure(self) -> None: ...
    def ctl(self, args: str, **kw: Any) -> tuple[str, str]: ...
    def evade(self, component: RunningSupervisor) -> None: ...
    def is_running(self) -> bool: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

class Eventlistener(Program):
    events: str | tuple[str, ...]

    @override
    def configure(self) -> None: ...

class Supervisor(Component):
    address: Address
    buildout_version: str
    setuptools_version: str
    wheel_version: str
    pip_version: str
    buildout_cfg: str
    supervisor_conf: str
    program_config_dir: Component | None
    logdir: Component | None
    loglevel: Literal["info", "debug", "warn", "error", "critical"]
    logrotate: bool | str
    nagios: bool | str
    enable: bool | str
    deployment_mode: str  # "hot" or "cold"
    max_startup_delay: int | str
    wait_for_running: bool | str
    pidfile: str
    socketpath: str
    check_contact_groups: str | None

    @override
    def configure(self) -> None: ...

class RunningHelper(Component):
    def is_running(self) -> bool: ...

class RunningSupervisor(RunningHelper):
    action: str | None
    reload_timeout: int
    service: Any

    def reload_supervisor(self) -> None: ...
    @override
    def update(self) -> None: ...
    @override
    def verify(self) -> None: ...

class StoppedSupervisor(RunningHelper):
    @override
    def verify(self) -> None: ...
    @override
    def update(self) -> None: ...
