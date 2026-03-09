"""Type stubs for batommel deploy command.

TOML-based deployment wrapper that converts to INI before delegating to batou deploy.
"""

from typing import Annotated

import typer

app: typer.Typer

def _generate_diff(old_content: str, new_content: str, filename: str) -> str: ...
def _display_diff(diff_text: str) -> None: ...
def deploy(
    ctx: typer.Context,
    environment: Annotated[
        str,
        typer.Argument(help="Environment to deploy"),
    ],
    timeout: Annotated[
        str | None,
        typer.Option(
            "--timeout",
            "-t",
            help="Override the environment's timeout setting",
        ),
    ] = ...,
    platform: Annotated[
        str | None,
        typer.Option("--platform", "-p", help="Alternative platform to choose"),
    ] = ...,
    dirty: Annotated[
        bool,
        typer.Option("--dirty", "-D", help="Allow deploying with dirty working copy"),
    ] = ...,
    consistency_only: Annotated[
        bool,
        typer.Option("--consistency-only", "-c", help="Only perform consistency check"),
    ] = ...,
    predict_only: Annotated[
        bool,
        typer.Option(
            "--predict-only",
            "-P",
            help="Only predict what updates would happen",
        ),
    ] = ...,
    check_and_predict_local: Annotated[
        bool,
        typer.Option("--local", "-L", help="Check/predict using local host state"),
    ] = ...,
    jobs: Annotated[
        int | None,
        typer.Option("--jobs", "-j", help="Number of parallel jobs"),
    ] = ...,
    provision_rebuild: Annotated[
        bool,
        typer.Option("--provision-rebuild", help="Rebuild provisioned resources"),
    ] = ...,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress diff output"),
    ] = ...,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite INI without confirmation"),
    ] = ...,
) -> None: ...
