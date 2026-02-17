"""Convert batou environment.toml to environment.cfg (INI format).

This script converts TOML configuration files back to INI format
for backward compatibility scenarios.
"""

import configparser
import io
from pathlib import Path
from typing import Annotated

import typer

from batou.config_toml import load_toml_config, to_legacy_format

app = typer.Typer(
    no_args_is_help=True,
    help="Convert environment.toml to environment.cfg (INI format).",
)


def format_ini(legacy: dict[str, dict[str, str]]) -> str:
    """Format legacy dict as INI using ConfigParser."""
    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore[assignment]  # Preserve case
    for section, options in legacy.items():
        config[section] = options
    output = io.StringIO()
    config.write(output)
    return output.getvalue()


def convert_toml_to_ini(toml_path: Path) -> str:
    """Convert a TOML file to INI format."""
    content = toml_path.read_text()
    config = load_toml_config(content, str(toml_path))
    legacy = to_legacy_format(config)
    return format_ini(legacy)


def convert_environment(
    env_path: Path,
    output_path: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Convert a single environment.toml to environment.cfg."""
    toml_path = env_path / "environment.toml"
    cfg_path = output_path or (env_path / "environment.cfg")

    if not toml_path.exists():
        print(f"  ⚠️  No environment.toml found in {env_path}")
        return False

    if cfg_path.exists() and not dry_run and not force:
        print(f"  ⚠️  environment.cfg already exists in {env_path}")
        print("     Use --force to overwrite")
        return False

    try:
        ini_content = convert_toml_to_ini(toml_path)

        if dry_run:
            print(f"  📝 Would convert {toml_path} -> {cfg_path}")
            print(ini_content)
            return True

        cfg_path.write_text(ini_content)
        print(f"  ✅ Converted {toml_path} -> {cfg_path}")
        return True

    except Exception as e:
        print(f"  ❌ Error converting {toml_path}: {e}")
        return False


@app.command()
def convert(
    path: Annotated[
        str,
        typer.Argument(help="Path to environments directory or specific environment"),
    ] = "environments",
    output: Annotated[
        str | None,
        typer.Option("-o", "--output", help="Output file path"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("-n", "--dry-run", help="Show what would be converted"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("-f", "--force", help="Overwrite existing environment.cfg files"),
    ] = False,
):
    """Convert environment.toml to environment.cfg (INI format)."""
    target_path = Path(path)

    if dry_run:
        print("🔍 Dry run mode - no files will be modified\n")

    # Single environment.toml file?
    if target_path.is_file() and target_path.name == "environment.toml":
        # Single TOML file
        env_path = target_path.parent
        output_path = Path(output) if output else None
        convert_environment(env_path, output_path, dry_run, force)

    elif (target_path / "environment.toml").exists():
        # Single environment directory
        output_path = Path(output) if output else None
        convert_environment(target_path, output_path, dry_run, force)

    elif target_path.is_dir():
        # Environments directory - find all environments with TOML
        envs = sorted(
            [
                d
                for d in target_path.iterdir()
                if d.is_dir() and (d / "environment.toml").exists()
            ]
        )

        if not envs:
            print(f"No environments with environment.toml in {target_path}")
            raise typer.Exit(1)

        print(f"Found {len(envs)} environment(s) to convert:\n")

        success = 0
        for env_path in envs:
            print(f"📁 {env_path.name}")
            if convert_environment(env_path, None, dry_run, force):
                success += 1

        print(
            f"\n{'Would convert' if dry_run else 'Converted'} "
            f"{success}/{len(envs)} environment(s)"
        )

    else:
        print(f"Path not found: {target_path}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
