"""Local consistency check command without execnet overhead."""

import os
import pathlib
import sys
import time
import traceback
from typing import Annotated, Any, Literal

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.table import Table

import batou
from batou import ConfigurationError, SilentConfigurationError
from batou._output import TerminalBackend, output
from batou.config_toml import ConfigLoadError, load_toml_config
from batou.environment import Environment
from batou.utils import Timer, find_basedir, self_id

app = typer.Typer(
    no_args_is_help=True,
    help="Fast local consistency check without execnet overhead.",
)
console = Console()


def parse_environment_arg(env_arg: str) -> tuple[str | None, str]:
    """Parse environment argument and return (basedir, environment_name).

    If env_arg is an existing path to an environment directory:
    - If path ends with 'environments/<name>', basedir = parent of environments
    - Otherwise basedir = parent of the path

    Otherwise treat it as an environment name relative to basedir.
    """
    if os.path.exists(env_arg):
        abs_path = os.path.abspath(env_arg)
        environment_name = os.path.basename(abs_path)
        parent_dir = os.path.dirname(abs_path)

        # If parent is 'environments', go up one more level to project root
        if os.path.basename(parent_dir) == "environments":
            basedir = os.path.dirname(parent_dir)
        else:
            basedir = parent_dir

        return basedir, environment_name
    return None, env_arg


class LocalValidator:
    """Validate configuration locally without execnet."""

    def __init__(self, environment: Environment):
        self.environment = environment

    def validate_configuration(self):
        """Validate all aspects of configuration."""
        errors = []

        if not self.environment.hosts:
            errors.append(
                ConfigurationError.from_context("No host found in environment.")
            )
            return errors

        hostnames = sorted(self.environment.hosts)[:1]
        for hostname in hostnames:
            host = self.environment.hosts[hostname]
            if host.ignore:
                continue

            try:
                host.connect()
                host.start()
            except Exception as e:
                errors.append(e)

        return errors


class CheckCommand:
    """Main check command implementation."""

    def __init__(
        self,
        environment: str,
        platform: str | None,
        timeout: str | None,
        debug: bool = False,
        show_override_values: Literal["true", "oneline", "none"] = "true",
    ):
        self.environment_name = environment
        self.platform = platform
        self.timeout = timeout
        self.debug = debug
        self.show_override_values = show_override_values
        self.errors: list = []
        self.start_time: float | None = None
        self.toml_config = None
        self._component_colors: dict[str, str] = {}

    def execute(self) -> int:
        """Execute check command and return exit code."""
        output.backend = TerminalBackend()
        output.line(self_id())

        self.start_time = time.time()

        try:
            self.load_environment()
            self.load_secrets()
            self.validate_configuration()
        except ConfigurationError as e:
            self.errors.append(e)
        except SilentConfigurationError:
            pass
        except Exception:
            output.error("Unexpected exception")
            traceback.print_exc()
            sys.exit(1)

        self.report_results()
        return 0 if not self.errors else 1

    def load_environment(self):
        """Load environment configuration."""
        output.section("Preparing")

        output.step(
            "main",
            f"Loading environment `{self.environment_name}`...",
            icon="📦",
        )
        self.environment = Environment(
            self.environment_name,
            self.timeout,
            self.platform,
            check_and_predict_local=True,
        )

        # Try to load and display TOML config first
        self.toml_config = self._load_toml_config()
        if self.toml_config:
            self.show_configuration()

        self.environment.load()

        output.step("main", "Verifying repository ...", icon="🔍")
        self.environment.repository.verify()

    def _load_toml_config(self):
        """Load TOML configuration if available."""
        toml_file = (
            pathlib.Path(self.environment.base_dir)
            / "environments"
            / self.environment.name
            / "environment.toml"
        )
        if not toml_file.exists():
            return None

        try:
            content = toml_file.read_text()
            return load_toml_config(content, str(toml_file))
        except ConfigLoadError as e:
            # Re-raise as ConfigurationError for proper error handling
            raise ConfigurationError.from_context(str(e)) from e

    def _get_component_colors(self) -> dict[str, str]:
        """Assign consistent unique colors to components with overrides.

        Uses a deterministic color assignment based on component name.
        Each component gets a unique color.
        """
        if not self.toml_config or not self.toml_config.components:
            return {}

        # Extended color palette for uniqueness
        colors = [
            "yellow",
            "magenta",
            "cyan",
            "red",
            "green",
            "blue",
            "bright_yellow",
            "bright_magenta",
            "bright_cyan",
            "bright_red",
            "bright_green",
            "bright_blue",
            "orange1",
            "orange3",
            "gold1",
            "gold3",
            "dark_orange",
            "coral1",
            "salmon1",
            "light_salmon1",
            "pink1",
            "plum1",
            "mediumpurple1",
            "slate_blue1",
            "royal_blue1",
            "dodger_blue1",
            "steel_blue1",
            "light_steel_blue1",
            "aquamarine1",
            "dark_sea_green1",
            "light_green1",
            "pale_green1",
            "spring_green1",
            "chartreuse1",
            "khaki1",
            "light_goldenrod1",
        ]

        # Assign colors deterministically based on sorted component names
        color_map = {}
        sorted_components = sorted(self.toml_config.components.keys())
        for i, comp_name in enumerate(sorted_components):
            color_map[comp_name] = colors[i % len(colors)]

        return color_map

    def _format_components(self, components: list[str]) -> str:
        """Format component list with consistent color coding.

        Each component with overrides gets a unique color that matches
        across all tables.
        """
        if not components:
            return "[dim]-[/dim]"

        color_map = self._get_component_colors()
        formatted = []
        for comp in components:
            # Split component:feature
            if ":" in comp:
                base, feature = comp.split(":", 1)
                if base in color_map:
                    color = color_map[base]
                    formatted.append(f"[{color}]{base}[/{color}]:{feature}")
                else:
                    formatted.append(comp)
            else:
                if comp in color_map:
                    color = color_map[comp]
                    formatted.append(f"[{color}]{comp}[/{color}]")
                else:
                    formatted.append(comp)

        return ", ".join(formatted)

    def _format_override_values(self, comp_config: dict[str, Any]) -> str:
        """Format component override key=value pairs based on show_override_values setting."""
        if not comp_config:
            return "[dim]-[/dim]"

        def format_value(value: Any) -> str:
            """Format a single value based on its type."""
            if isinstance(value, bool):
                return f"[blue]{value}[/blue]"
            elif isinstance(value, int):
                return f"[yellow]{value}[/yellow]"
            elif isinstance(value, float):
                return f"[yellow]{value}[/yellow]"
            elif isinstance(value, list):
                return f"[magenta]{value}[/magenta]"
            elif isinstance(value, str):
                # Handle multiline strings - put content on new line
                if "\n" in value:
                    return f'[green]"""\n{value}"""[/green]'
                return f'[green]"{value}"[/green]'
            else:
                return str(value)

        if self.show_override_values == "none":
            # Only show keys, no values
            return ", ".join(f"[blue]{k}[/blue]" for k in sorted(comp_config.keys()))

        if self.show_override_values == "oneline":
            # All on one line: key=value, key=value
            parts = []
            for key in sorted(comp_config.keys()):
                value = comp_config[key]
                parts.append(f"[blue]{key}[/blue]={format_value(value)}")
            return ", ".join(parts)

        # Default: "true" - multi-line
        lines = []
        for key in sorted(comp_config.keys()):
            value = comp_config[key]
            lines.append(f"[blue]{key}[/blue] = {format_value(value)}")

        return "\n".join(lines)

    def show_configuration(self):
        """Display configuration summary from TOML config."""
        if not self.toml_config:
            return

        console.print()

        # Environment settings table
        env_table = Table(
            box=ROUNDED,
            padding=(0, 2),
            border_style="dim",
        )
        env_table.add_column("Setting", style="dim")
        env_table.add_column("Value", style="bold")
        env_table.add_column("Type", style="cyan")

        # Type info for environment settings (use parentheses to avoid Rich bracket issues)
        type_info = {
            "connect_method": "Literal(local, ssh, vagrant, kitchen)",
            "update_method": "Literal(rsync, rsync-ext, git-bundle, git-pull, hg-bundle, hg-pull)",
            "timeout": "int",
            "jobs": "int",
            "require_sudo": "bool",
            "branch": "str",
            "host_domain": "str",
            "platform": "str",
            "service_user": "str",
            "target_directory": "str",
            "repository_url": "str",
            "repository_root": "str",
        }

        env = self.toml_config.environment
        env_table.add_row("Name", f"[green]{self.environment_name}[/green]", "str")
        env_table.add_row(
            "Connect",
            f"[blue]{env.connect_method}[/blue]",
            type_info.get("connect_method", ""),
        )
        env_table.add_row(
            "Update",
            f"[blue]{env.update_method}[/blue]",
            type_info.get("update_method", ""),
        )
        if env.platform:
            env_table.add_row(
                "Platform",
                f"[yellow]{env.platform}[/yellow]",
                type_info.get("platform", "str"),
            )
        if env.service_user:
            env_table.add_row(
                "User", env.service_user, type_info.get("service_user", "str")
            )
        env_table.add_row("Timeout", f"{env.timeout}s", type_info.get("timeout", "int"))
        if env.branch:
            env_table.add_row("Branch", env.branch, type_info.get("branch", "str"))
        if env.jobs != 1:
            env_table.add_row("Jobs", str(env.jobs), type_info.get("jobs", "int"))

        console.print(env_table)

        # DNS Resolver table (right after environment)
        if self.toml_config.resolver:
            resolver_table = Table(
                box=ROUNDED,
                padding=(0, 2),
                border_style="dim",
            )
            resolver_table.add_column("DNS Name", style="bold green")
            resolver_table.add_column("IP Address", style="yellow")

            for hostname, ips in sorted(self.toml_config.resolver.items()):
                if isinstance(ips, list):
                    ips_str = ", ".join(ips)
                else:
                    ips_str = ips
                resolver_table.add_row(hostname, ips_str)

            console.print()
            console.print(resolver_table)

        # Hosts table
        all_hosts = self.toml_config.get_all_hosts()
        if all_hosts:
            host_table = Table(
                box=ROUNDED,
                padding=(0, 2),
                border_style="dim",
            )
            host_table.add_column("Host", style="bold green")
            host_table.add_column("Components", style="white")

            for hostname, hostcfg in sorted(all_hosts.items()):
                components = hostcfg.components if hostcfg.components else []
                comp_str = self._format_components(components)
                host_table.add_row(hostname, comp_str)

            console.print()
            console.print(host_table)

        # Component overrides table
        if self.toml_config.components:
            overrides_table = Table(
                box=ROUNDED,
                padding=(0, 2),
                border_style="dim",
                show_lines=True,
            )
            overrides_table.add_column("Component", style="bold green")
            overrides_table.add_column("Settings", style="white")

            color_map = self._get_component_colors()
            for comp_name, comp_config in sorted(self.toml_config.components.items()):
                # Use same color as in hosts table
                if comp_name in color_map:
                    color = color_map[comp_name]
                    colored_name = f"[{color}]{comp_name}[/{color}]"
                else:
                    colored_name = comp_name

                settings = self._format_override_values(comp_config)
                overrides_table.add_row(colored_name, settings)

            console.print()
            console.print(overrides_table)

        console.print()

    def load_secrets(self):
        """Load and decrypt secrets."""
        output.step("main", "Loading secrets ...", icon="🔑")
        self.environment.load_secrets()

    def validate_configuration(self):
        """Validate configuration locally."""
        output.section("LOCAL CONSISTENCY CHECK")

        validator = LocalValidator(self.environment)

        timer = Timer("check")
        with timer.step("check"):
            errors = validator.validate_configuration()
            self.errors.extend(errors)

        self.errors = list(
            filter(
                lambda e: not isinstance(e, SilentConfigurationError),
                self.errors,
            )
        )

        self.errors.sort(key=lambda x: getattr(x, "sort_key", (-99,)))

    def report_results(self):
        """Report validation results."""
        if self.errors:
            for error in self.errors:
                output.line("")
                if hasattr(error, "report"):
                    error.report()
                else:
                    tb = traceback.TracebackException.from_exception(error)
                    for line in tb.format():
                        output.line("\t" + line.strip(), red=True)

            output.section(
                f"{len(self.errors)} ERRORS - CONFIGURATION FAILED",
                red=True,
            )
        else:
            output.section("Summary")
            if self.start_time:
                duration = time.time() - self.start_time
                output.annotate(f"Local consistency check took {duration:.2f}s")
            output.section("LOCAL CONSISTENCY CHECK FINISHED", cyan=True)


@app.command()
def check(
    environment: Annotated[
        str,
        typer.Argument(
            help="Environment to check. Can be a name (e.g., 'test') or an existing path to an environment directory."
        ),
    ],
    platform: Annotated[
        str | None,
        typer.Option(
            "--platform",
            "-p",
            help="Alternative platform to choose. Empty for no platform.",
        ),
    ] = None,
    timeout: Annotated[
        str | None,
        typer.Option(
            "--timeout",
            "-t",
            help="Override the environment's timeout setting.",
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Enable debug mode."),
    ] = False,
    show_override_values: Annotated[
        Literal["true", "oneline", "none"],
        typer.Option(
            "--show-override-values",
            help="How to display component override values: true=multi-line, oneline=single line, none=keys only.",
        ),
    ] = "true",
):
    """Fast local consistency check without execnet overhead."""
    batou.output.enable_debug = debug

    basedir, environment_name = parse_environment_arg(environment)

    if basedir:
        os.chdir(basedir)
    else:
        os.chdir(find_basedir())

    command = CheckCommand(
        environment_name, platform, timeout, debug, show_override_values
    )
    exit_code = command.execute()
    raise typer.Exit(exit_code)


def main(environment, platform, timeout):
    """Entry point for check command (called from batou main CLI)."""
    command = CheckCommand(environment, platform, timeout)
    exit_code = command.execute()
    sys.exit(exit_code)


def main_cli(args: list | None = None) -> None:
    """Standalone CLI entry point for batou-check."""
    app(args)


if __name__ == "__main__":
    app()
