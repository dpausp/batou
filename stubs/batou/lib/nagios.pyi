from typing import Any, Literal, override

from batou.component import Component, HookComponent

# Note: ServiceCheck follows batou naming convention (not PEP8)
def ServiceCheck(description: str, **kw: Any) -> Service | NRPEService: ...  # noqa: N802

class Service(HookComponent):
    namevar: Literal["description"]
    description: str
    key: str
    command: str | None
    args: str
    notes_url: str
    servicegroups: str
    contact_groups: str | None
    depend_on: tuple

    @property
    def check_command(self) -> str: ...
    @override
    def configure(self) -> None: ...

class NRPEService(Service):
    name: str | None
    servicegroups: str

    @property
    @override
    def check_command(self) -> str: ...
    @override
    def configure(self) -> None: ...
    @property
    def nrpe_command(self) -> str: ...

class NagiosServer(Component):
    nagios_cfg: str
    static: str
    services: list[Service]

    @override
    def configure(self) -> None: ...

class NRPEHost(Component):
    nrpe_cfg: str
    services: list[NRPEService]

    @override
    def configure(self) -> None: ...
