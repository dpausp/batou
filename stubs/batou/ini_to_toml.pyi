from pathlib import Path
from typing import Any

import typer

app: typer.Typer

class InferMode:
    """Type inference modes for INI -> TOML conversion."""

    NONE: str
    SAFE: str
    FULL: str

def infer_type(value: str, mode: str = ...) -> str | int | float | bool | list[str]: ...
def parse_multiline_yaml(value: str) -> dict | None: ...
def convert_config_to_toml(cfg_path: Path, infer_mode: str = ...) -> dict[str, Any]: ...
def format_toml(data: dict) -> str: ...
def migrate_environment(
    env_path: Path,
    output_path: Path | None = ...,
    dry_run: bool = ...,
    force: bool = ...,
    infer_mode: str = ...,
) -> bool: ...
def migrate(
    path: str = ...,
    output: str | None = ...,
    dry_run: bool = ...,
    force: bool = ...,
    infer_types: str = ...,
) -> None: ...
