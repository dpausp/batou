from collections.abc import Callable
from typing import Any

import execnet
from execnet.xspec import XSpec

from batou.component import RootComponent
from batou.environment import ConfigSection, Environment
from batou.provision import Provisioner
from batou.utils import BagOfAttributes

def new_ssh_args(spec: XSpec) -> list[str]: ...

class Host:
    service_user: str | None
    require_sudo: bool | None
    ignore: bool
    platform: str | None
    _provisioner: str | None
    _provision_info: dict[str, Any]
    remap: bool
    _name: str
    aliases: BagOfAttributes
    data: dict[str, Any]
    rpc: RPCWrapper
    environment: Environment

    @property
    def _aliases(self) -> list[str]: ...
    def __init__(
        self,
        name: str,
        environment: Environment,
        config: ConfigSection = ...,
    ) -> None: ...
    @property
    def components(self) -> dict[str, RootComponent]: ...
    def deploy_component(self, component: str, predict_only: bool) -> None: ...
    @property
    def fqdn(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def provisioner(self) -> Provisioner | None: ...
    def root_dependencies(self) -> Any: ...
    def summarize(self) -> None: ...

class LocalHost(Host):
    gateway: execnet.Gateway
    channel: Any
    remote_repository: Any
    remote_base: str

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def start(self) -> str: ...

class RPCWrapper:
    host: Host

    def __getattr__(self, name: str) -> Callable: ...
    def __init__(self, host: Host) -> None: ...

class RemoteHost(Host):
    gateway: execnet.Gateway | None
    channel: Any
    remote_repository: Any
    remote_base: str

    def _makegateway(self, interpreter: str) -> Any: ...
    def connect(self, interpreter: str = ...) -> None: ...
    def disconnect(self) -> None: ...
    def start(self) -> str: ...
