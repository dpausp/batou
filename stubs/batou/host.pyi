from batou.component import RootComponent
from batou.environment import (
    ConfigSection,
    Environment,
)
from execnet.xspec import XSpec
from mock.mock import Mock
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Union,
)


def new_ssh_args(spec: XSpec) -> List[str]: ...


class Host:
    def __init__(
        self,
        name: str,
        environment: Union[Environment, Mock],
        config: Union[ConfigSection, Dict[str, str]] = ...
    ): ...
    @property
    def components(self) -> Dict[str, RootComponent]: ...
    @property
    def fqdn(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def provisioner(self) -> Optional[Mock]: ...


class LocalHost:
    def connect(self): ...
    def disconnect(self): ...
    def start(self) -> bytes: ...


class RPCWrapper:
    def __getattr__(self, name: str) -> Callable: ...
    def __init__(self, host: Union[LocalHost, Host, Mock, RemoteHost]): ...


class RemoteHost:
    def _makegateway(self, interpreter: str): ...
    def connect(self, interpreter: str = ...): ...
    def start(self) -> Mock: ...
