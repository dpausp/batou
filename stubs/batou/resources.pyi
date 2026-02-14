from batou.component import RootComponent
from batou.host import (
    Host,
    RemoteHost,
)
from typing import (
    Any,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

class Resources:
    subscribers: Dict[str, Set["Subscription"]]
    dirty_dependencies: Set[RootComponent]
    resources: Dict[str, Dict[RootComponent, List[Any]]]

    def __init__(self): ...
    def _subscriptions(
        self, key: str, host: Optional[Host]
    ) -> List["Subscription"]: ...
    def copy_resources(self) -> Dict[str, Dict[RootComponent, List[Any]]]: ...
    def get(self, key: str, host: Optional[Host] = ...) -> List[Any]: ...
    def get_dependency_graph(
        self,
    ) -> DefaultDict[RootComponent, Set[RootComponent]]: ...
    def provide(self, root: RootComponent, key: str, value: Any): ...
    def require(
        self,
        root: RootComponent,
        key: str,
        host: Optional[Host] = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...,
    ) -> List[Any]: ...
    def reset_component_resources(self, root: RootComponent): ...
    @property
    def strict_subscribers(self): ...
    @property
    def unsatisfied(self) -> Set[Tuple[str, Optional[str]]]: ...
    @property
    def unsatisfied_components(self) -> Set[RootComponent]: ...
    @property
    def unsatisfied_keys_and_components(
        self,
    ) -> Dict[Tuple[str, Optional[str]], Set[RootComponent]]: ...
    @property
    def unused(self) -> Dict[str, Dict[RootComponent, List[Any]]]: ...

class Subscription:
    root: RootComponent
    strict: bool
    host: Optional[Host]
    reverse: bool
    dirty: bool

    def __hash__(self) -> int: ...
    def __init__(
        self,
        root: RootComponent,
        strict: bool,
        host: Optional[Host],
        reverse: bool,
        dirty: bool,
    ): ...
