from batou.environment import Environment
from batou.host import (
    Host,
    LocalHost,
    RemoteHost,
)
from batou.lib.cron import (
    CronTab,
    DebianInstallCrontab,
    FCInstallCrontab,
)
from batou.lib.debian import (
    LogrotateCronjob,
    RebootCronjob,
    Supervisor as DebianSupervisor,
)
from batou.lib.file import (
    File,
    Mode,
    Presence,
)
from batou.lib.logrotate import GoceptNetRotatedLogrotate
from batou.lib.service import Service
from batou.lib.supervisor import Supervisor
from batou.utils import Address
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Optional,
    Tuple,
    Type,
    Union,
)

class ConfigString(str):
    """A string value that will be handled as if it was read from a config file."""

class Attribute:
    def __get__(self, obj: Optional[Any], objtype: Optional[Type] = ...) -> Any: ...
    def __init__(
        self,
        conversion: Union[Type[int], str, Type[Address], Type[str], Callable] = ...,
        default: Any = ...,
        expand: bool = ...,
        map: bool = ...,
    ): ...
    def __set__(self, obj: Any, value: Any): ...
    def __set_name__(self, owner: Type, name: str): ...
    def convert_list(self, value: str) -> List[str]: ...
    def convert_literal(self, value: str) -> Any: ...
    def from_config_string(self, obj: Any, value: ConfigString) -> Any: ...

class Component:
    namevar: Optional[str]
    workdir: Optional[str]
    _: Optional["Component"]
    changed: bool
    _prepared: bool
    parent: Union["Component", "RootComponent"]
    sub_components: List["Component"]
    timer: Any

    def __add__(self, component: Optional["Component"]) -> "Component": ...
    def __enter__(self): ...
    def __exit__(self, exc_type: None, exc_value: None, tb: None): ...
    def __init__(self, namevar: Optional[Union[str, Path]] = ..., **kw): ...
    def __or__(self, component: Optional["Component"]) -> "Component": ...
    def __repr__(self) -> str: ...
    def __setup_event_handlers__(self): ...
    def __trigger_event__(self, event: str, predict_only: bool): ...
    @classmethod
    def _add_platform(cls, name: str, platform: Type): ...
    @property
    def _breadcrumb(self) -> str: ...
    @property
    def _breadcrumbs(self) -> str: ...
    def _get_platform(self) -> Optional["Component"]: ...
    def _overrides(self, overrides: Dict[str, Any] = ...): ...
    def _template_args(
        self, component: Optional["Component"] = ..., **kw
    ) -> Dict[str, Any]: ...
    def assert_cmd(self, *args, **kw): ...
    def assert_component_is_current(
        self, requirements: Union["Component", List["Component"]] = ..., **kw
    ): ...
    def assert_file_is_current(
        self, reference: str, requirements: List[str] = ..., **kw
    ): ...
    def assert_no_changes(self): ...
    def assert_no_subcomponent_changes(self): ...
    def chdir(self, path: str): ...
    def checksum(self, value: Optional[bytes] = ...) -> str: ...
    def cmd(
        self,
        cmd: str,
        silent: bool = ...,
        ignore_returncode: bool = ...,
        communicate: bool = ...,
        env: Optional[Dict[str, str]] = ...,
        expand: bool = ...,
    ) -> Tuple[str, str]: ...
    def configure(self): ...
    @property
    def defdir(self) -> str: ...
    def deploy(self, predict_only: bool = ...): ...
    @property
    def environment(self) -> Environment: ...
    def expand(
        self, string: str, component: Optional["Component"] = ..., **kw
    ) -> str: ...
    @property
    def host(self) -> Host: ...
    def last_updated(self, **kw): ...
    def map(self, path: Union[Path, str]) -> str: ...
    @property
    def namevar_for_breadcrumb(self) -> Optional[str]: ...
    def prepare(self, parent: Union["Component", "RootComponent"]): ...
    def provide(self, key: str, value: Any): ...
    @property
    def recursive_sub_components(self) -> Iterator["Component"]: ...
    def require(
        self,
        key: str,
        host: Optional[Host] = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...,
    ) -> List[Any]: ...
    def require_one(
        self,
        key: str,
        host: Optional[Host] = ...,
        strict: bool = ...,
        reverse: bool = ...,
        dirty: bool = ...,
    ) -> Any: ...
    @property
    def root(self) -> "RootComponent": ...

class HookComponent(Component):
    key: str

    def configure(self): ...

class RootComponent:
    name: str
    environment: Environment
    host: Host
    features: Optional[List[str]]
    ignore: bool
    defdir: str
    workdir: str
    overrides: Dict[str, Any]
    factory: Callable[[], Component]
    component: Component
    _logs: Optional[List[Tuple[str, Tuple]]]

    def __init__(
        self,
        name: str,
        environment: Environment,
        host: Host,
        features: Optional[List[str]],
        ignore: bool,
        factory: Callable[[], Component],
        defdir: str,
        workdir: str,
        overrides: Optional[Dict[str, Any]] = ...,
    ): ...
    def __repr__(self) -> str: ...
    @property
    def _breadcrumbs(self) -> str: ...
    def log(self, msg: str, *args): ...
    def log_finish_configure(self): ...
    def prepare(self): ...
