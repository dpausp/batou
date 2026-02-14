from batou.component import (
    Component,
    ComponentDefinition,
    RootComponent,
)
from batou.host import (
    Host,
    LocalHost,
    RemoteHost,
)
from pathlib import Path
from typing import (
    Any,
    DefaultDict,
    Dict,
    Iterator,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

def parse_host_components(components: List[str]) -> Dict[str, Dict[str, Any]]: ...

class Config:
    def __contains__(self, section: str) -> bool: ...
    def __getitem__(self, section: str) -> "ConfigSection": ...
    def __init__(self, path: Optional[Path]): ...
    def __iter__(self) -> Iterator[str]: ...
    def get(
        self, section: str, default: Optional["ConfigSection"] = ...
    ) -> Optional["ConfigSection"]: ...

class ConfigSection(dict):
    def as_list(self, option: str) -> List[str]: ...

class Environment:
    name: str
    hosts: Dict[str, Host]
    resources: Any
    overrides: Dict[str, Dict[str, str]]
    secret_data: Set[str]
    exceptions: List[Exception]
    timeout: Optional[int]
    platform: Optional[str]
    provision_rebuild: bool
    check_and_predict_local: bool
    hostname_mapping: Dict[str, str]
    components: Dict[str, ComponentDefinition]
    root_components: List[RootComponent]
    base_dir: str
    workdir_base: str
    secret_files: Dict[str, str]
    provisioners: Dict[str, Any]
    template_stats: Any
    service_user: Optional[str]
    require_sudo: Optional[bool]
    host_domain: Optional[str]
    branch: Optional[str]
    connect_method: Optional[str]
    update_method: Optional[str]
    vfs_sandbox: Any
    target_directory: Optional[str]
    jobs: Optional[int]
    require_v4: Union[bool, str]
    require_v6: Union[bool, str]
    repository_url: Optional[str]
    repository_root: Optional[str]
    host_factory: type
    repository: Any
    deployment_base: str
    secret_provider: Any

    def __init__(
        self,
        name: str,
        timeout: Optional[int] = ...,
        platform: Optional[str] = ...,
        basedir: str = ...,
        provision_rebuild: bool = ...,
        check_and_predict_local: bool = ...,
    ): ...
    def _environment_path(self, path: str = ...) -> str: ...
    def _host_data(self) -> Dict[str, Dict[str, Any]]: ...
    def _load_host_components(self, host: Host, component_list: List[str]): ...
    def _load_hosts_multi_section(self, config: Config): ...
    def _load_hosts_single_section(self, config: Config): ...
    def _set_defaults(self): ...
    def add_root(
        self,
        component_name: str,
        host: Host,
        features: Union[List[str], Tuple[()]] = ...,
        ignore: bool = ...,
    ) -> RootComponent: ...
    @classmethod
    def all(cls) -> Iterator["Environment"]: ...
    def components_for(self, host: Host) -> Dict[str, RootComponent]: ...
    def configure(self) -> List[Exception]: ...
    @classmethod
    def filter(cls, filter: Optional[str]) -> List["Environment"]: ...
    def get_host(self, hostname: str) -> Host: ...
    def get_root(self, component_name: str, host: Host) -> RootComponent: ...
    def load(self): ...
    def load_environment(self, config: Config): ...
    def load_hosts(self, config: Config): ...
    def load_provisioners(self, config: Config): ...
    def load_resolver(self, config: Config): ...
    def load_secrets(self): ...
    def map(self, path: str) -> str: ...
    def prepare_connect(self): ...
    def root_dependencies(
        self, host: Optional[str] = ...
    ) -> DefaultDict[RootComponent, Set[RootComponent]]: ...

class UnknownEnvironmentError(ValueError):
    names: list

    def __init__(self, names: list): ...
    def __str__(self) -> str: ...
