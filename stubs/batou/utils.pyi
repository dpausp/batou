from batou.component import RootComponent
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


def call_with_optional_args(func: Callable, **kw) -> None: ...


def cmd(
    cmd: Union[str, List[str]],
    silent: bool = ...,
    ignore_returncode: bool = ...,
    communicate: bool = ...,
    env: None = ...,
    acceptable_returncodes: List[int] = ...,
    encoding: Optional[str] = ...
) -> Union[Tuple[bytes, bytes], Tuple[str, str]]: ...


def dict_merge(
    a: Dict[str, Union[str, Dict[str, str]]],
    b: Dict[str, Union[str, Dict[str, str]]]
) -> Dict[str, Union[str, Dict[str, str]]]: ...


def ensure_graph_data(
    graph: Union[DefaultDict[RootComponent, Set[RootComponent]], DefaultDict[RootComponent, Union[Set[RootComponent], Set[Any]]], DefaultDict[RootComponent, Set[Any]]]
) -> Union[DefaultDict[RootComponent, Set[RootComponent]], DefaultDict[RootComponent, Union[Set[RootComponent], Set[Any]]], DefaultDict[RootComponent, Set[Any]]]: ...


def escape_macosx_string(s: str) -> str: ...


def flatten(list_of_lists: List[Any]) -> List[Any]: ...


def format_duration(duration: Optional[float]) -> str: ...


def hash(path: str, function: str = ...) -> str: ...


def locked(filename: str, exit_on_failure: bool = ...): ...


def notify_macosx(title: str, description: str): ...


def remove_nodes_without_outgoing_edges(
    graph: DefaultDict[RootComponent, Set[RootComponent]]
): ...


def resolve(host: str, port: int = ..., resolve_override: Dict[str, str] = ...) -> str: ...


def resolve_v6(host: str, port: int = ..., resolve_override: Dict[str, str] = ...) -> str: ...


def revert_graph(
    graph: Union[DefaultDict[RootComponent, Set[RootComponent]], DefaultDict[RootComponent, Union[Set[RootComponent], Set[Any]]], DefaultDict[RootComponent, Set[Any]]]
) -> Union[DefaultDict[RootComponent, Set[RootComponent]], DefaultDict[RootComponent, Union[Set[RootComponent], Set[Any]]], DefaultDict[RootComponent, Set[Any]]]: ...


def self_id() -> str: ...


def topological_sort(
    graph: Union[DefaultDict[RootComponent, Set[RootComponent]], DefaultDict[RootComponent, Union[Set[RootComponent], Set[Any]]], DefaultDict[RootComponent, Set[Any]]]
) -> List[RootComponent]: ...


class Address:
    def __init__(self, connect_address: str, port: None = ..., require_v4: object = ..., require_v6: object = ...): ...


class CmdExecutionError:
    def __init__(self, cmd: str, returncode: int, stdout: str, stderr: str): ...
    def __str__(self) -> str: ...


class CycleError:
    def __str__(self) -> str: ...


class NetLoc:
    def __init__(self, host: str, port: Optional[str] = ...): ...


class Timer:
    def __init__(self, tag: Optional[str] = ...): ...
    def above_threshold(self, **thresholds) -> Union[Tuple[bool, List[str]], Tuple[bool, List[Any]]]: ...
    def humanize(self, *steps) -> str: ...
    def step(self, note: str) -> Timer.TimerContext: ...


class Timer.TimerContext:
    def __enter__(self): ...
    def __exit__(self, exc_type: None, exc_value: None, traceback: None): ...
    def __init__(self, timer: Timer, note: str): ...
