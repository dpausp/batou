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
    List,
    Optional,
    Set,
    Tuple,
    Union,
)
from collections.abc import Iterator

def parse_host_components(components: list[str]) -> dict[str, dict[str, Any]]: ...

class Config:
    def __contains__(self, section: str) -> bool: ...
    def __getitem__(self, section: str) -> ConfigSection: ...
    def __init__(self, path: Path | None): ...
    def __iter__(self) -> Iterator[str]: ...
    def get(
        self, section: str, default: Optional[ConfigSection] = ...
    ) -> Optional[ConfigSection]: ...

class ConfigSection(dict):
    def as_list(self, option: str) -> list[str]: ...

class Environment:
    name: str
    hosts: dict[str, Host]
    resources: Any
    overrides: dict[str, dict[str, str]]
    secret_data: set[str]
    exceptions: list[Exception]
    timeout: int | None
    platform: str | None
    provision_rebuild: bool
    check_and_predict_local: bool
    hostname_mapping: dict[str, str]
    components: dict[str, ComponentDefinition]
    root_components: list[RootComponent]
    base_dir: str
    workdir_base: str
    secret_files: dict[str, str]
    provisioners: dict[str, Any]
    template_stats: Any
    service_user: str | None
    require_sudo: bool | None
    host_domain: str | None
    branch: str | None
    connect_method: str | None
    update_method: str | None
    vfs_sandbox: Any
    target_directory: str | None
    jobs: int | None
    require_v4: bool | str
    require_v6: bool | str
    repository_url: str | None
    repository_root: str | None
    host_factory: type
    repository: Any
    deployment_base: str
    secret_provider: Any

    def __init__(
        self,
        name: str,
        timeout: int | None = ...,
        platform: str | None = ...,
        basedir: str = ...,
        provision_rebuild: bool = ...,
        check_and_predict_local: bool = ...,
    ): ...
    def _environment_path(self, path: str = ...) -> str: ...
    def _host_data(self) -> dict[str, dict[str, Any]]: ...
    def _load_host_components(self, host: Host, component_list: list[str]): ...
    def _load_hosts_multi_section(self, config: Config): ...
    def _load_hosts_single_section(self, config: Config): ...
    def _set_defaults(self): ...
    def add_root(
        self,
        component_name: str,
        host: Host,
        features: list[str] | tuple[()] = ...,
        ignore: bool = ...,
    ) -> RootComponent: ...
    @classmethod
    def all(cls) -> Iterator[Environment]: ...
    def components_for(self, host: Host) -> dict[str, RootComponent]: ...
    def configure(self) -> list[Exception]: ...
    @classmethod
    def filter(cls, filter: str | None) -> list[Environment]: ...
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
        self, host: str | None = ...
    ) -> DefaultDict[RootComponent, set[RootComponent]]: ...

class UnknownEnvironmentError(ValueError):
    names: list

    def __init__(self, names: list): ...
    def __str__(self) -> str: ...
