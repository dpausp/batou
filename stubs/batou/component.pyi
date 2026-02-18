import contextlib
import types
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any, Literal, Self
from weakref import WeakKeyDictionary

from batou.environment import Environment
from batou.host import Host
from batou.utils import Timer

# Sentinel object for no default
NO_DEFAULT: object

class ConfigString(str):
    """A string value that will be handled as if it was read from a config file."""

class ComponentDefinition:
    filename: str
    name: str
    factory: Callable[[], Component]
    defdir: str

    def __init__(
        self,
        factory: Callable[[], Component],
        filename: str | None = ...,
        defdir: str | None = ...,
    ): ...

class Attribute[T]:
    conversion: type[T] | str | Callable[..., T]
    default: T
    expand: bool
    map: bool
    instances: WeakKeyDictionary
    names: dict[type, str]

    def __get__(self, obj: Any, objtype: type | None = ...) -> T: ...
    def __init__(
        self,
        conversion: type[T] | str | Callable[..., T] = ...,
        default: T = ...,
        expand: bool = ...,
        map: bool = ...,  # noqa: A002
    ): ...
    def __set__(self, obj: Any, value: T) -> None: ...
    def __set_name__(self, owner: type, name: str) -> None: ...
    def convert_list(self, value: str) -> list[str]: ...
    def convert_literal(self, value: str) -> Any: ...
    def from_config_string(self, obj: Any, value: ConfigString) -> Any: ...

class Component:
    namevar: str | None
    workdir: str | None
    _: Component | None
    changed: bool
    _prepared: bool
    parent: Component | RootComponent
    sub_components: list[Component]
    timer: Timer
    _instances: list[Component]
    _template_engine: Any
    _platform_component: Component | None
    _event_handlers: dict[str, list[Callable]]
    _init_file_path: str
    _init_line_number: int
    _init_breadcrumbs: list[str]

    def __repr__(self) -> str: ...  # noqa: PYI029
    def __add__(self, component: Component | None) -> Self: ...
    def __iadd__(self, component: Component | None) -> Self: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        type: type[BaseException] | None,
        value: BaseException | None,
        tb: types.TracebackType | None,
    ) -> bool | None: ...
    def __init__(self, namevar: str | Path | None = ..., **kw: Any) -> None: ...
    def __or__(self, component: Component | None) -> Self: ...
    def __setup_event_handlers__(self) -> None: ...
    def __trigger_event__(self, event: str, predict_only: bool) -> None: ...
    @classmethod
    def _add_platform(cls, name: str, platform: type[Component]) -> None: ...
    @property
    def _breadcrumb(self) -> str: ...
    @property
    def _breadcrumbs(self) -> str: ...
    def _get_platform(self) -> Component | None: ...
    def _overrides(self, overrides: dict[str, Any] = ...) -> None: ...
    def _template_args(
        self,
        component: Component | None = ...,
        **kw: Any,
    ) -> dict[str, Any]: ...
    def assert_cmd(self, *args: str, **kw: Any) -> None: ...
    def assert_component_is_current(
        self,
        requirements: Component | list[Component] = ...,
        **kw: Any,
    ) -> None: ...
    def assert_file_is_current(
        self,
        reference: str,
        requirements: list[str] = ...,
        **kw: Any,
    ) -> None: ...
    def assert_no_changes(self) -> None: ...
    def assert_no_subcomponent_changes(self) -> None: ...
    def chdir(self, path: str) -> contextlib.AbstractContextManager[None]: ...
    def checksum(self, value: bytes | None = ...) -> str: ...
    def cmd(
        self,
        cmd: str,
        silent: bool = ...,
        ignore_returncode: bool = ...,
        communicate: bool = ...,
        env: dict[str, str] | None = ...,
        expand: bool = ...,
    ) -> tuple[str, str]: ...
    def configure(self) -> None: ...
    @property
    def defdir(self) -> str: ...
    def deploy(self, predict_only: bool = ...) -> None: ...
    @property
    def environment(self) -> Environment: ...
    def expand(
        self,
        string: str,
        component: Component | None = ...,
        **kw: Any,
    ) -> str: ...
    @property
    def host(self) -> Host: ...
    def last_updated(self) -> float | None: ...
    def log(self, msg: str, *args: Any) -> None: ...
    def map(self, path: Path | str) -> str: ...
    @property
    def namevar_for_breadcrumb(self) -> str | None: ...
    def prepare(self, parent: Component | RootComponent) -> None: ...
    def provide(self, key: str, value: Any) -> None: ...
    @property
    def recursive_sub_components(self) -> Iterator[Component]: ...
    def require(
        self,
        key: str,
        host: Host | None = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...,
    ) -> list[Any]: ...
    def require_one(
        self,
        key: str,
        host: Host | None = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...,
    ) -> Any: ...
    @property
    def root(self) -> RootComponent: ...
    def template(self, filename: str, component: Component | None = ...) -> str: ...
    def touch(self, path: str) -> None: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...

class HookComponent(Component):
    key: str

    def configure(self) -> None: ...

class RootComponent:
    name: str
    environment: Environment
    host: Host
    features: list[str] | None
    ignore: bool
    defdir: str
    workdir: str
    overrides: dict[str, Any]
    factory: Callable[[], Component]
    component: Component
    _logs: list[tuple[str, tuple]] | None

    def __repr__(self) -> str: ...  # noqa: PYI029
    def __init__(
        self,
        name: str,
        environment: Environment,
        host: Host,
        features: list[str] | None,
        ignore: bool,
        factory: Callable[[], Component],
        defdir: str,
        workdir: str,
        overrides: dict[str, Any] | None = ...,
    ) -> None: ...
    @property
    def _breadcrumbs(self) -> str: ...
    def log(self, msg: str, *args: Any) -> None: ...
    def log_finish_configure(self) -> None: ...
    def prepare(self) -> None: ...

def platform(name: str, component: type[Component]) -> Callable[[type], type]: ...
def handle_event(event: str, scope: str = ...) -> Callable[[Callable], Callable]: ...
def check_event_scope(
    scope: Literal["*", "precursor"],
    source: Component,
    target: Component,
) -> bool: ...
def load_components_from_file(filename: str) -> dict[str, ComponentDefinition]: ...
def batou_generated_header(component: Component) -> str: ...
