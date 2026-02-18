from typing import Any

from batou.component import HookComponent

# Note: ServiceCheck follows batou naming convention (not PEP8)
def ServiceCheck(description: str, **kw: Any) -> Service | NRPEService: ...  # noqa: N802

class Service(HookComponent):
    description: str
    command: str | None
    args: str
    notes_url: str
    servicegroups: str
    contact_groups: str | None
    depend_on: tuple

    @property
    def check_command(self) -> str: ...
    def configure(self) -> None: ...

class NRPEService(Service):
    name: str | None

    @property
    def check_command(self) -> str: ...
    def configure(self) -> None: ...
    @property
    def nrpe_command(self) -> str: ...

class NagiosServer(HookComponent):
    nagios_cfg: str
    static: str
    services: list[Service]

    def configure(self) -> None: ...

class NRPEHost(HookComponent):
    nrpe_cfg: str
    services: list[NRPEService]

    def configure(self) -> None: ...
