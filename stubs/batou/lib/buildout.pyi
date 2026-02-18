from typing import Any

from batou.component import Component
from batou.lib.file import File

def safe_environment(environment: dict[Any, Any]): ...

class Buildout(Component):
    timeout: int | None
    use_default: bool
    config: File | list[Component] | None
    additional_config: tuple[Component, ...]
    config_file_name: str
    python: str | None
    executable: str | None
    distribute: str | None
    setuptools: str | None
    wheel: str | None
    pip: str | None
    version: str | None
    build_env: dict[str, str]

    def configure(self) -> None: ...
    def update(self) -> None: ...
    def verify(self) -> None: ...
