"""Batommel deploy command - TOML-based deployment wrapper.

Converts TOML configuration to INI before delegating to batou deploy.

Error Handling Strategy:
-------------------------
This module follows spec-first exception handling per CODEX Article 1:

1. ConfigLoadError (SPEC: REQ-FUNC-DEPLOY-001):
   Catches TOML parsing/validation errors, displays error to user,
   and exits with status 1. Prevents deployment with invalid configuration.

2. SystemExit (SPEC: REQ-FUNC-DEPLOY-002):
   Preserves batou's exit status when delegating to batou.main:main().
   Re-raises immediately to ensure correct exit code propagates.
   Cleanup (sys.argv restoration) happens in finally block.

All exceptions are handled to provide clear user feedback and maintain
deployment integrity. No silent failures.
"""

import difflib
import sys
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.syntax import Syntax

from batou.config_toml import ConfigLoadError, load_toml_config, to_legacy_format
from batou.toml_to_ini import format_ini

app = typer.Typer(
    no_args_is_help=True,
    help="Deploy using TOML configuration (converts to INI first).",
)
console = Console()


def _generate_diff(old_content: str, new_content: str, filename: str) -> str:
    """Generate unified diff between old and new content."""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"{filename} (current)",
        tofile=f"{filename} (from TOML)",
    )
    return "".join(diff_lines)


def _display_diff(diff_text: str) -> None:
    """Display diff with Rich syntax highlighting."""
    if not diff_text.strip():
        console.print("[dim]No changes - INI already up to date[/dim]")
        return

    syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=False)
    console.print(syntax)


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True}
)
def deploy(
    ctx: typer.Context,
    environment: Annotated[
        str,
        typer.Argument(help="Environment to deploy"),
    ],
    timeout: Annotated[
        str | None,
        typer.Option(
            "--timeout", "-t", help="Override the environment's timeout setting"
        ),
    ] = None,
    platform: Annotated[
        str | None,
        typer.Option("--platform", "-p", help="Alternative platform to choose"),
    ] = None,
    dirty: Annotated[
        bool,
        typer.Option("--dirty", "-D", help="Allow deploying with dirty working copy"),
    ] = False,
    consistency_only: Annotated[
        bool,
        typer.Option("--consistency-only", "-c", help="Only perform consistency check"),
    ] = False,
    predict_only: Annotated[
        bool,
        typer.Option(
            "--predict-only", "-P", help="Only predict what updates would happen"
        ),
    ] = False,
    check_and_predict_local: Annotated[
        bool,
        typer.Option("--local", "-L", help="Check/predict using local host state"),
    ] = False,
    jobs: Annotated[
        int | None,
        typer.Option("--jobs", "-j", help="Number of parallel jobs"),
    ] = None,
    provision_rebuild: Annotated[
        bool,
        typer.Option("--provision-rebuild", help="Rebuild provisioned resources"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress diff output"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite INI without confirmation"),
    ] = False,
) -> None:
    """Deploy using TOML configuration (converts to INI first).

    The TOML file (environment.toml) is the source of truth.
    INI file (environment.cfg) is regenerated on each deployment.
    """
    # Find environment directory
    env_dir = Path("environments") / environment

    if not env_dir.exists():
        console.print(f"[red]Error: Environment directory not found: {env_dir}[/red]")
        raise typer.Exit(1)

    toml_path = env_dir / "environment.toml"
    cfg_path = env_dir / "environment.cfg"

    # REQ-FUNC-DEPLOY-004: Fail if environment.toml not found
    if not toml_path.exists():
        console.print(f"[red]Error: TOML configuration not found: {toml_path}[/red]")
        console.print(
            "[dim]Run 'batommel ini-to-toml' to create TOML from existing INI[/dim]"
        )
        raise typer.Exit(1)

    # REQ-FUNC-DEPLOY-001: Convert TOML to INI
    # SPEC: REQ-FUNC-DEPLOY-001-toml-conversion - Handle TOML parsing errors
    try:
        content = toml_path.read_text()
        config = load_toml_config(content, str(toml_path))
        legacy = to_legacy_format(config)
        ini_content = format_ini(legacy)
    except ConfigLoadError as e:
        console.print("[red]Error loading TOML configuration:[/red]")
        console.print(str(e))
        raise typer.Exit(1)

    # REQ-FUNC-DEPLOY-005: Show diff before overwriting (unless --force or --quiet)
    if cfg_path.exists() and not force and not quiet:
        old_content = cfg_path.read_text()
        diff_text = _generate_diff(old_content, ini_content, "environment.cfg")
        console.print("\n[bold]Changes to environment.cfg:[/bold]\n")
        _display_diff(diff_text)

    # REQ-FUNC-DEPLOY-003: Write to standard location
    # REQ-FUNC-DEPLOY-006: TOML precedence - always overwrite
    cfg_path.write_text(ini_content)

    if not quiet:
        console.print(f"[green]✓[/green] Converted {toml_path} -> {cfg_path}")

    # REQ-FUNC-DEPLOY-002: Call batou deploy with same arguments
    # Build argument list for batou deploy
    deploy_args = ["deploy", environment]

    if timeout is not None:
        deploy_args.extend(["--timeout", timeout])
    if platform is not None:
        deploy_args.extend(["--platform", platform])
    if dirty:
        deploy_args.append("--dirty")
    if consistency_only:
        deploy_args.append("--consistency-only")
    if predict_only:
        deploy_args.append("--predict-only")
    if check_and_predict_local:
        deploy_args.append("--local")
    if jobs is not None:
        deploy_args.extend(["--jobs", str(jobs)])
    if provision_rebuild:
        deploy_args.append("--provision-rebuild")

    # Pass through any extra arguments from context
    if ctx.args:
        deploy_args.extend(ctx.args)

    if not quiet:
        console.print(f"[dim]Running: batou {' '.join(deploy_args)}[/dim]\n")

    # Delegate to batou.main:main
    from batou.main import main

    # Override sys.argv for batou's argparse-based CLI
    original_argv = sys.argv
    sys.argv = ["batou"] + deploy_args

    # SPEC: REQ-FUNC-DEPLOY-002-deploy-delegation - Preserve batou's exit status
    try:
        main()
    except SystemExit:
        raise
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    app()
