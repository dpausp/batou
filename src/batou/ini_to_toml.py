"""Convert batou environment.cfg to environment.toml.

This script converts existing INI configuration files to TOML format
with proper type inference for better DX.
"""

import configparser
import re
from pathlib import Path
from typing import Annotated

import rtoml
import typer

app = typer.Typer(
    no_args_is_help=True,
    help="Convert environment.cfg to environment.toml.",
)


class InferMode:
    """Type inference modes for INI → TOML conversion."""

    NONE = "none"  # Keep everything as strings
    SAFE = "safe"  # Only bools and newline-separated lists
    FULL = "full"  # Full type inference (int, float, bool, list)


def infer_type(
    value: str, mode: str = InferMode.NONE
) -> str | int | float | bool | list[str]:
    """Infer the type of a config value and convert it.

    Args:
        value: The string value from INI
        mode: Inference mode - "none", "safe", or "full"

    Returns:
        Converted value based on mode
    """
    if mode == InferMode.NONE:
        # Keep everything as strings, but still handle multiline lists
        # for structural correctness
        if "\n" in value:
            items = [x.strip() for x in value.split("\n") if x.strip()]
            if items:
                return items
        return value

    if mode == InferMode.SAFE:
        # Safe mode: only booleans and newline-separated lists
        # These are "safe" because they don't lose information
        if value.lower() in ("true", "yes", "on"):
            return True
        if value.lower() in ("false", "no", "off"):
            return False

        # Multi-line list (newline separated) - structural, not heuristic
        if "\n" in value:
            items = [x.strip() for x in value.split("\n") if x.strip()]
            if items:
                return items

        return value

    # FULL mode - current behavior
    # Boolean
    if value.lower() in ("true", "yes", "on"):
        return True
    if value.lower() in ("false", "no", "off"):
        return False

    # Integer
    if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
        return int(value)

    # Float
    try:
        if "." in value and not value.startswith("{"):
            return float(value)
    except ValueError:
        pass

    # Multi-line list (newline separated)
    if "\n" in value:
        items = [x.strip() for x in value.split("\n") if x.strip()]
        if items:
            return items

    # Comma-separated list (only if looks like a list)
    if "," in value and not value.startswith("{") and not value.startswith("|"):
        # Heuristic: if it contains commas and looks like a list
        items = [x.strip() for x in value.split(",")]
        # Only convert if all items look like simple values
        if all(re.match(r"^[\w\-\.]+$", x) for x in items):
            return items

    # String (default)
    return value


def parse_multiline_yaml(value: str) -> dict | None:
    """Try to parse pipe-prefixed YAML content."""
    if not value.strip().startswith("|"):
        return None

    try:
        import yaml

        # Remove pipe prefix from each line
        lines = []
        for line in value.split("\n"):
            if line.startswith("|"):
                lines.append(line[1:])
            elif line.strip() == "":
                lines.append("")

        content = "\n".join(lines)
        return yaml.safe_load(content)
    except Exception:
        return None


def convert_config_to_toml(cfg_path: Path, infer_mode: str = InferMode.NONE) -> dict:
    """Convert an INI config file to TOML-compatible dict.

    Args:
        cfg_path: Path to environment.cfg file
        infer_mode: Type inference mode - "none", "safe", or "full"
    """
    config = configparser.ConfigParser()
    config.optionxform = str  # type: ignore[assignment]  # Preserve case
    config.read(cfg_path)

    result: dict = {
        "environment": {},
        "hosts": {},
        "host": {},
        "components": {},
        "resolver": {},
        "provisioner": {},
    }

    for section in config.sections():
        if section == "environment":
            # Environment settings
            for key, value in config.items(section):
                result["environment"][key] = infer_type(value, infer_mode)

        elif section == "hosts":
            # Simple host -> component mapping
            # Can be single component, comma-separated, or newline-separated
            for hostname, component in config.items(section):
                component = component.strip()
                if "\n" in component:
                    # Multi-line: parse as list
                    components = [x.strip() for x in component.split("\n") if x.strip()]
                    if len(components) == 1:
                        result["hosts"][hostname] = components[0]
                    else:
                        # Store as detailed host config
                        if hostname not in result["host"]:
                            result["host"][hostname] = {}
                        result["host"][hostname]["components"] = components
                        # Still add to hosts for simple mapping
                        result["hosts"][hostname] = components[0]
                elif "," in component:
                    # Comma-separated: parse as list
                    components = [x.strip() for x in component.split(",") if x.strip()]
                    if len(components) == 1:
                        result["hosts"][hostname] = components[0]
                    else:
                        # Store as detailed host config
                        if hostname not in result["host"]:
                            result["host"][hostname] = {}
                        result["host"][hostname]["components"] = components
                        result["hosts"][hostname] = components[0]
                else:
                    result["hosts"][hostname] = component

        elif section.startswith("host:"):
            # Detailed host config
            hostname = section[5:]
            host_config = {}

            for key, value in config.items(section):
                if key == "components":
                    # Parse component list
                    if "\n" in value:
                        host_config["components"] = [
                            x.strip() for x in value.split("\n") if x.strip()
                        ]
                    else:
                        host_config["components"] = [value]
                elif key.startswith("data-"):
                    # Data attributes - try to infer type
                    host_config[key] = infer_type(value, infer_mode)
                elif key == "platform":
                    host_config["platform"] = value
                else:
                    host_config[key] = infer_type(value, infer_mode)

            if "components" in host_config:
                result["host"][hostname] = host_config

        elif section.startswith("component:"):
            # Component overrides
            comp_name = section[10:]
            comp_config = {}

            for key, value in config.items(section):
                # Try to parse YAML-in-INI
                yaml_data = parse_multiline_yaml(value)
                if yaml_data is not None:
                    comp_config[key] = yaml_data
                else:
                    comp_config[key] = infer_type(value, infer_mode)

            if comp_config:
                result["components"][comp_name] = comp_config

        elif section.startswith("provisioner:"):
            # Provisioner config
            prov_name = section[12:]
            prov_config = {}

            for key, value in config.items(section):
                prov_config[key] = infer_type(value, infer_mode)

            if prov_config:
                result["provisioner"][prov_name] = prov_config

        elif section == "resolver":
            # DNS overrides
            for hostname, ips in config.items(section):
                if "\n" in ips:
                    result["resolver"][hostname] = [
                        x.strip() for x in ips.split("\n") if x.strip()
                    ]
                else:
                    result["resolver"][hostname] = ips

        elif section == "vfs":
            # VFS config
            result["vfs"] = dict(config.items(section))

    # Clean up empty sections
    result = {k: v for k, v in result.items() if v}

    return result


def format_toml(data: dict) -> str:
    """Format dict as TOML with nice structure."""
    # Use rtoml for serialization
    return rtoml.dumps(data, pretty=True)


def migrate_environment(
    env_path: Path,
    output_path: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    infer_mode: str = InferMode.NONE,
):
    """Migrate a single environment."""
    cfg_path = env_path / "environment.cfg"
    toml_path = output_path or (env_path / "environment.toml")

    if not cfg_path.exists():
        print(f"  ⚠️  No environment.cfg found in {env_path}")
        return False

    if toml_path.exists() and not dry_run and not force:
        print(f"  ⚠️  environment.toml already exists in {env_path}")
        print("     Use --force to overwrite")
        return False

    try:
        data = convert_config_to_toml(cfg_path, infer_mode)
        toml_content = format_toml(data)

        if dry_run:
            print(f"  📝 Would convert {cfg_path} -> {toml_path}")
            print(toml_content)
            return True

        toml_path.write_text(toml_content)
        print(f"  ✅ Converted {cfg_path} -> {toml_path}")
        return True

    except Exception as e:
        print(f"  ❌ Error converting {cfg_path}: {e}")
        return False


def migrate(
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
        typer.Option("-f", "--force", help="Overwrite existing files"),
    ] = False,
    infer_types: Annotated[
        str,
        typer.Option(
            help="Type inference mode: 'none' (strings only), "
            "'safe' (bools+lists), 'full' (all types)"
        ),
    ] = InferMode.NONE,
):
    """Convert environment.cfg to environment.toml."""
    # Validate infer_types mode
    valid_modes = [InferMode.NONE, InferMode.SAFE, InferMode.FULL]
    if infer_types not in valid_modes:
        print(f"Invalid --infer-types value: {infer_types}")
        print(f"Valid options: {', '.join(valid_modes)}")
        raise typer.Exit(1)

    target_path = Path(path)

    if dry_run:
        print("🔍 Dry run mode - no files will be modified\n")

    if infer_types != InferMode.NONE:
        print(f"📊 Type inference mode: {infer_types}\n")

    # Single environment or directory?
    if target_path.is_file() and target_path.name == "environment.cfg":
        # Single environment.cfg file
        env_path = target_path.parent
        migrate_environment(
            env_path,
            Path(output) if output else None,
            dry_run,
            force,
            infer_types,
        )

    elif (target_path / "environment.cfg").exists():
        # Single environment directory
        migrate_environment(
            target_path, Path(output) if output else None, dry_run, force, infer_types
        )

    elif target_path.is_dir():
        # Environments directory - find all environments
        envs = sorted(
            [
                d
                for d in target_path.iterdir()
                if d.is_dir() and (d / "environment.cfg").exists()
            ]
        )

        if not envs:
            print(f"No environments found in {target_path}")
            raise typer.Exit(1)

        print(f"Found {len(envs)} environment(s) to migrate:\n")

        success = 0
        for env_path in envs:
            print(f"📁 {env_path.name}")
            if migrate_environment(env_path, None, dry_run, force, infer_types):
                success += 1

        print(
            f"\n{'Would convert' if dry_run else 'Converted'} "
            f"{success}/{len(envs)} environment(s)"
        )

    else:
        print(f"Path not found: {target_path}")
        raise typer.Exit(1)


# Register with local app for standalone execution
app.command()(migrate)


if __name__ == "__main__":
    app()
