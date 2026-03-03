from typing import Any, Literal

import typer
from rich.console import Console

from batou.config_toml import ConfigLoadError
from batou.environment import Environment

app: typer.Typer
console: Console

def parse_environment_arg(env_arg: str) -> tuple[str | None, str]: ...
def check(
    environment: str,
    platform: str | None = ...,
    timeout: str | None = ...,
    debug: bool = ...,
    show_override_values: Literal["true", "oneline", "none"] = ...,
) -> None: ...
def main(environment: str, platform: str | None, timeout: str | None): ...
def main_cli(args: list[Any] | None = ...) -> None: ...

class CheckCommand:
    environment_name: str
    platform: str | None
    timeout: str | None
    debug: bool
    show_override_values: Literal["true", "oneline", "none"]
    environment: Environment
    errors: list[Any]
    start_time: float | None
    toml_config: Any
    _component_colors: dict[str, str]
    _config_error: ConfigLoadError | None

    def __init__(
        self,
        environment: str,
        platform: str | None,
        timeout: str | None,
        debug: bool = ...,
        show_override_values: Literal["true", "oneline", "none"] = ...,
    ): ...
    def execute(self) -> int: ...
    def load_environment(self) -> None: ...
    def load_secrets(self) -> None: ...
    def report_results(self) -> None: ...
    def validate_configuration(self) -> None: ...
    def _load_toml_config(self) -> Any: ...
    def show_config_error(self, error: ConfigLoadError) -> None: ...
    def _get_component_colors(self) -> dict[str, str]: ...
    def _format_components(self, components: list[str]) -> str: ...
    def _format_override_values(self, comp_config: dict[str, Any]) -> str: ...
    def show_configuration(self) -> None: ...

class LocalValidator:
    environment: Environment

    def __init__(self, environment: Environment): ...
    def validate_configuration(self) -> list[Any]: ...
