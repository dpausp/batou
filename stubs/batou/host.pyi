from collections.abc import Callable
from typing import Any

from execnet.xspec import XSpec

from batou.component import RootComponent
from batou.environment import (
    ConfigSection,
    Environment,
)
from batou.utils import BagOfAttributes

def new_ssh_args(
    spec: XSpec,
) -> list[str]: ...  # spec.type is Literal["vagrant", "kitchen", "ssh"]

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

    def __init__(
        self, name: str, environment: Environment, config: ConfigSection = ...
    ): ...
    @property
    def components(self) -> dict[str, RootComponent]: ...
    def deploy_component(self, component: str, predict_only: bool): ...
    @property
    def fqdn(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def provisioner(self) -> Any | None: ...
    def root_dependencies(self): ...
    def summarize(self): ...

class LocalHost(Host):
    gateway: Any
    channel: Any
    remote_repository: Any
    remote_base: str

    def connect(self): ...
    def disconnect(self): ...
    def start(self) -> str: ...

class RPCWrapper:
    host: Host

    def __getattr__(self, name: str) -> Callable: ...
    def __init__(self, host: Host): ...

class RemoteHost(Host):
    gateway: Any | None
    channel: Any
    remote_repository: Any
    remote_base: str

    def _makegateway(self, interpreter: str): ...
    def connect(self, interpreter: str = ...): ...
    def disconnect(self): ...
    def start(self) -> str: ...
