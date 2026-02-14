from batou.component import RootComponent
from batou.environment import (
    ConfigSection,
    Environment,
)
from batou.utils import BagOfAttributes
from execnet.xspec import XSpec
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

def new_ssh_args(spec: XSpec) -> List[str]: ...

class Host:
    service_user: Optional[str]
    require_sudo: Optional[bool]
    ignore: bool
    platform: Optional[str]
    _provisioner: Optional[str]
    _provision_info: Dict[str, Any]
    remap: bool
    _name: str
    aliases: BagOfAttributes
    data: Dict[str, Any]
    rpc: "RPCWrapper"
    environment: Environment

    def __init__(
        self, name: str, environment: Environment, config: ConfigSection = ...
    ): ...
    @property
    def components(self) -> Dict[str, RootComponent]: ...
    def deploy_component(self, component: str, predict_only: bool): ...
    @property
    def fqdn(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def provisioner(self) -> Optional[Any]: ...
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
    gateway: Optional[Any]
    channel: Any
    remote_repository: Any
    remote_base: str

    def _makegateway(self, interpreter: str): ...
    def connect(self, interpreter: str = ...): ...
    def disconnect(self): ...
    def start(self) -> str: ...
