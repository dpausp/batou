from pathlib import Path

import typer
from batou.config_toml import EnvironmentConfig

app: typer.Typer

def format_ini(legacy: dict[str, dict[str, str]]) -> str: ...
def convert_toml_to_ini(toml_path: Path) -> str: ...
def convert_environment(
    env_path: Path,
    output_path: Path | None = ...,
    dry_run: bool = ...,
    force: bool = ...,
) -> bool: ...
def convert(
    path: str = ...,
    output: str | None = ...,
    dry_run: bool = ...,
    force: bool = ...,
) -> None: ...
