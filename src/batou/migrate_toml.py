"""Migrate batou environment.cfg to environment.toml.

This script converts existing INI configuration files to TOML format
with proper type inference for better DX.
"""

import argparse
import configparser
import re
import sys
from pathlib import Path

import rtoml


def infer_type(value: str) -> str | int | float | bool | list[str]:
    """Infer the type of a config value and convert it."""
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


def convert_config_to_toml(cfg_path: Path) -> dict:
    """Convert an INI config file to TOML-compatible dict."""
    config = configparser.ConfigParser()
    config.optionxform = lambda x: x  # Preserve case
    config.read(cfg_path)

    result: dict = {
        "environment": {},
        "hosts": {},
        "host": {},
        "components": {},
        "resolver": {},
    }

    # Known sections that aren't components
    special_sections = {"environment", "hosts", "vfs", "resolver"}

    for section in config.sections():
        if section == "environment":
            # Environment settings
            for key, value in config.items(section):
                result["environment"][key] = infer_type(value)

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
                    host_config[key] = infer_type(value)
                elif key == "platform":
                    host_config["platform"] = value
                else:
                    host_config[key] = infer_type(value)

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
                    comp_config[key] = infer_type(value)

            if comp_config:
                result["components"][comp_name] = comp_config

        elif section.startswith("provisioner:"):
            # Provisioner config - store as-is for now
            prov_name = section[12:]
            # Skip for now, add support later if needed
            pass

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
    env_path: Path, output_path: Path | None = None, dry_run: bool = False
):
    """Migrate a single environment."""
    cfg_path = env_path / "environment.cfg"
    toml_path = env_path / "environment.toml"

    if not cfg_path.exists():
        print(f"  ⚠️  No environment.cfg found in {env_path}")
        return False

    if toml_path.exists() and not dry_run:
        print(f"  ⚠️  environment.toml already exists in {env_path}")
        return False

    try:
        data = convert_config_to_toml(cfg_path)
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


def main():
    parser = argparse.ArgumentParser(
        description="Migrate batou environment.cfg to environment.toml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Migrate all environments in the current directory
  batou-migrate-toml

  # Migrate specific environment
  batou-migrate-toml environments/prod

  # Dry run (show what would be converted)
  batou-migrate-toml --dry-run

  # Custom output location
  batou-migrate-toml environments/dev --output /tmp/dev.toml
""",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="environments",
        help="Path to environments directory or specific environment (default: environments/)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file path (only for single environment)",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Show what would be converted without writing files",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Overwrite existing environment.toml files",
    )

    args = parser.parse_args()
    path = Path(args.path)

    if args.dry_run:
        print("🔍 Dry run mode - no files will be modified\n")

    # Single environment or directory?
    if path.is_file() and path.name == "environment.cfg":
        # Single environment.cfg file
        env_path = path.parent
        migrate_environment(
            env_path, Path(args.output) if args.output else None, args.dry_run
        )

    elif (path / "environment.cfg").exists():
        # Single environment directory
        migrate_environment(
            path, Path(args.output) if args.output else None, args.dry_run
        )

    elif path.is_dir():
        # Environments directory - find all environments
        envs = sorted(
            [
                d
                for d in path.iterdir()
                if d.is_dir() and (d / "environment.cfg").exists()
            ]
        )

        if not envs:
            print(f"No environments found in {path}")
            sys.exit(1)

        print(f"Found {len(envs)} environment(s) to migrate:\n")

        success = 0
        for env_path in envs:
            print(f"📁 {env_path.name}")
            if migrate_environment(env_path, None, args.dry_run):
                success += 1

        print(
            f"\n{'Would convert' if args.dry_run else 'Converted'} {success}/{len(envs)} environment(s)"
        )

    else:
        print(f"Path not found: {path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
