"""Debug settings inspection command."""

import argparse
import sys

from rich.console import Console
from rich.table import Table

# Import batou._settings with alias to avoid shadowing batou.settings instance
# SPEC: SDD-F001 - Import pattern to prevent namespace collision
from batou.debug.settings import get_debug_settings

debug_settings = get_debug_settings()
console = Console()


def main(args: list[str] | None = None) -> None:
    """Display all available debug settings."""
    parser = argparse.ArgumentParser(
        description="Display all available debug settings."
    )
    parser.parse_args(args)

    settings_info = debug_settings.describe()

    # Create table with columns as specified in SDD D-006
    table = Table(title="Debug Settings")
    table.add_column("Field Name", style="cyan", no_wrap=True)
    table.add_column("Environment Variable", style="green")
    table.add_column("Possible Values", style="yellow")
    table.add_column("Description", style="white")
    table.add_column("Current Value", style="bold")

    for info in settings_info:
        # Format possible values for display
        possible_values = info["possible_values"]
        if possible_values == "Any":
            values_str = "Any"
        elif isinstance(possible_values, list):
            values_str = ", ".join(str(v) for v in possible_values)
        else:
            values_str = str(possible_values)

        # Add row to table
        table.add_row(
            info["field_name"],
            info["env_var"],
            values_str,
            info["description"],
            str(info["current_value"]),
        )

    console.print(table)


if __name__ == "__main__":
    main(sys.argv[1:])
