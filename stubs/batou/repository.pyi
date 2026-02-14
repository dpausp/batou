from batou.environment import Environment
from batou.host import RemoteHost
from mock.mock import Mock
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)


def cmd(c: str, *args, **kw) -> Tuple[str, str]: ...


def hg_cmd(hgcmd: str) -> List[Union[Dict[str, Optional[str]], Any, Dict[str, str], Dict[str, Union[str, List[str]]]]]: ...


class MercurialBundleRepository:
    def _ship(self, host: RemoteHost): ...


class MercurialRepository:
    def __init__(self, environment: Mock): ...
    def update(self, host: Union[Mock, RemoteHost]): ...
    @property
    def upstream(self) -> str: ...
    def verify(self): ...


class Repository:
    def __init__(self, environment: Union[Environment, Mock]): ...
    @classmethod
    def from_environment(
        cls,
        environment: Union[Mock, Environment]
    ) -> Union[RSyncRepository, RSyncDevRepository, RSyncExtRepository, NullRepository]: ...
    def update(self, host: RemoteHost): ...
    def verify(self): ...
