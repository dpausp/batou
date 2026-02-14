from batou.component import RootComponent
from batou.host import (
    Host,
    RemoteHost,
)
from batou.tests.test_dependencies import (
    Circular1,
    Circular2,
    DirtySingularCircularReverse,
)
from mock.mock import (
    Mock,
    _SentinelObject,
)
from typing import (
    Any,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


class Resources:
    def __init__(self): ...
    def _subscriptions(
        self,
        key: Union[_SentinelObject, str],
        host: Any
    ) -> List[Union[Any, Subscription]]: ...
    def copy_resources(
        self
    ) -> Dict[str, Union[Dict[RootComponent, List[DirtySingularCircularReverse]], Dict[RootComponent, List[Circular1]], Dict[RootComponent, List[str]], Dict[RootComponent, List[int]], Dict[RootComponent, List[Circular2]]]]: ...
    def get(
        self,
        key: Union[_SentinelObject, str],
        host: Optional[Union[Host, RemoteHost]] = ...
    ) -> List[Any]: ...
    def get_dependency_graph(self) -> DefaultDict[RootComponent, Set[RootComponent]]: ...
    def provide(
        self,
        root: Union[RootComponent, Mock],
        key: Union[_SentinelObject, str],
        value: Any
    ): ...
    def require(
        self,
        root: Union[RootComponent, Mock],
        key: Union[_SentinelObject, str],
        host: Optional[Union[Host, RemoteHost]] = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...
    ) -> List[Any]: ...
    def reset_component_resources(self, root: Union[RootComponent, Mock]): ...
    @property
    def unsatisfied(
        self
    ) -> Union[Set[Union[Tuple[str, str], Tuple[str, None]]], Set[Tuple[str, str]], Set[Tuple[str, None]]]: ...
    @property
    def unsatisfied_components(self) -> Set[RootComponent]: ...
    @property
    def unsatisfied_keys_and_components(
        self
    ) -> Union[Dict[Tuple[str, None], Set[RootComponent]], Dict[Tuple[str, str], Set[RootComponent]], Dict[Union[Tuple[str, str], Tuple[str, None]], Set[RootComponent]]]: ...
    @property
    def unused(self) -> Dict[str, Dict[RootComponent, List[int]]]: ...


class Subscription:
    def __hash__(self) -> int: ...
    def __init__(
        self,
        root: Union[RootComponent, Mock],
        strict: bool,
        host: Optional[Union[RemoteHost, Host]],
        reverse: bool,
        dirty: bool
    ): ...
