"""DebugSettings configuration from environment variables."""

from typing import Annotated, Any, Literal, TypedDict

from pydantic import BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DebugSettingInfo(TypedDict):
    """Structured information about a single debug setting field."""

    field_name: str
    env_var: str
    possible_values: str | list[Any]
    description: str
    current_value: Any
    default_value: Any


def _int_to_literal(value):
    """Convert string environment variable to int for Literal types."""
    if isinstance(value, str):
        # SPEC: SDD-F001 - Environment variable type conversion
        # Allow string-to-int conversion for numeric Literal types, preserving original value on failure
        try:
            return int(value)
        except ValueError:
            return value
    return value


class DebugSettings(BaseSettings):
    """Batou expert/debug configuration settings from environment variables."""

    # Diff control
    show_diff: Literal["full", "summary", "none"] = Field(
        default="full",
        description="Show file changes during deployment",
    )
    show_secret_diffs: bool = Field(
        default=False,
        description="Show diffs for encrypted/secret files (⚠️ dangerous)",
    )

    # FD tracking
    track_fds: Annotated[Literal[0, 1, 2], BeforeValidator(_int_to_literal)] = Field(
        default=0,
        description="Track file descriptor usage to detect leaks",
    )
    fd_output_dir: str = Field(
        default="/tmp",
        description="Output directory for FD tracking logs",
    )

    # Profiling
    profile: bool = Field(
        default=False,
        description="Profile remote execution for performance analysis",
    )
    profile_lines: int = Field(
        default=30,
        description="Number of profiling output lines to show",
    )

    model_config = SettingsConfigDict(
        env_prefix="BATOU_",
        case_sensitive=False,
        env_file=None,
        extra="ignore",
    )

    def describe(self) -> list[DebugSettingInfo]:
        """Return structured information about all debug settings.

        Returns a list of dictionaries with field name, environment variable name,
        possible values, description, current value, and default value.
        """
        settings_info = []

        for field_name, field_info in DebugSettings.model_fields.items():
            # Build environment variable name (e.g., track_fds -> BATOU_TRACK_FDS)
            env_var = f"BATOU_{field_name.upper()}"

            # Get possible values from the field
            possible_values = "Any"
            if field_info.annotation == Literal:
                # Extract literal values if annotation is Literal
                from typing import get_args

                possible_values = list(get_args(field_info.annotation))
            elif (
                hasattr(field_info.annotation, "__origin__")
                and field_info.annotation.__origin__ is Literal
            ):
                # Handle Literal type differently
                from typing import get_args

                possible_values = list(get_args(field_info.annotation))
            elif field_name == "show_diff":
                possible_values = ["full", "summary", "none"]
            elif field_name in ["show_secret_diffs", "profile"]:
                possible_values = [True, False]
            elif field_name == "track_fds":
                possible_values = [0, 1, 2]

            # Get current value
            current_value = getattr(self, field_name)

            # Get default value from field
            default_value = field_info.default

            # Get description from field (Pydantic V2 uses description attribute)
            description = field_info.description or ""

            settings_info.append(
                {
                    "field_name": field_name,
                    "env_var": env_var,
                    "possible_values": possible_values,
                    "description": description,
                    "current_value": current_value,
                    "default_value": default_value,
                }
            )

        return settings_info

    def show(self):
        """Display debug settings information with command hint."""
        from batou._output import output

        flags = []

        if self.show_diff != "full":
            mode_desc = {
                "summary": "diff output reduced to file list",
                "none": "diff output suppressed",
            }.get(self.show_diff, self.show_diff)
            flags.append(f"BATOU_SHOW_DIFF={self.show_diff} - {mode_desc}")

        if self.show_secret_diffs:
            flags.append("BATOU_SHOW_SECRET_DIFFS=1 - sensitive data diffs enabled")

        if self.track_fds > 0:
            if self.track_fds == 1:
                flags.append("BATOU_TRACK_FDS=1 - FD tracking enabled (simple)")
            elif self.track_fds == 2:
                flags.append("BATOU_TRACK_FDS=2 - FD tracking enabled (verbose)")

        if self.profile:
            flags.append("BATOU_PROFILE=1 - Profiling enabled")

        if flags:
            output.sep("=", "WARNING EXPERT/DEBUG FLAGS ENABLED", yellow=True)
            for flag in flags:
                output.annotate(flag)
        else:
            output.annotate("No expert/debug flags enabled")

        # Always show command hint (SDD D-008)
        output.annotate("Use `batou debug` command to see all available debug settings")


# Lazy initialization of debug_settings singleton
# This allows test fixtures to monkeypatch environment variables before first access
_debug_settings_singleton = None


def get_debug_settings():
    """Get or create the debug_settings singleton (lazy initialization).

    Always call this function instead of importing debug_settings directly
    to ensure you get the current singleton value with fresh environment variables.

    If reset_debug_settings() was called, singleton is None, so create
    new instance from CURRENT environment variables. Pydantic BaseSettings
    reads environment variables at instance creation time, not at class level.
    """
    global _debug_settings_singleton
    if _debug_settings_singleton is None:
        # Create fresh instance - Pydantic reads current os.environ here
        _debug_settings_singleton = DebugSettings()
    return _debug_settings_singleton
