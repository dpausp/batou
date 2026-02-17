"""TOML + Pydantic configuration for batou environments.

This module provides type-safe configuration loading with excellent error messages.
It converts TOML to the legacy INI-style format for backwards compatibility.

TOML Format Examples:

    # Simple host mapping (like INI)
    [hosts]
    localhost = "hello"
    host2 = "myapp"

    # Detailed host config
    [host.localhost]
    components = ["hello", "other"]
    data-ram = 4
    data-roles = ["web", "db"]

    # Component overrides
    [components.myapp]
    database_host = "db.example.com"
    database_port = 5432
"""

from ipaddress import AddressValueError, IPv4Address, IPv6Address
from typing import Annotated, Any, Literal

import rtoml
from pydantic import BaseModel, BeforeValidator, Field, ValidationError, field_validator


class EnvironmentSettings(BaseModel):
    """[environment] section - global environment settings."""

    model_config = {"extra": "forbid"}

    host_domain: str | None = None
    platform: str | None = None
    service_user: str | None = None
    update_method: Literal[
        "rsync", "rsync-ext", "git-bundle", "git-pull", "hg-bundle", "hg-pull"
    ] = "rsync"
    connect_method: Literal["local", "ssh", "vagrant", "kitchen"] = "ssh"
    branch: str | None = None
    timeout: int = 120
    target_directory: str | None = None
    require_sudo: bool | None = None
    jobs: int = 1
    repository_url: str | None = None
    repository_root: str | None = None

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v: int) -> int:
        if v < 1:
            raise ValueError("timeout must be a positive integer")
        return v


class HostConfig(BaseModel):
    """Detailed host configuration - [host.hostname] sections."""

    model_config = {"extra": "allow"}  # Allow data-* attributes

    components: list[str] = []
    platform: str | None = None

    def get_data_attributes(self) -> dict[str, str]:
        """Get all data-* attributes for legacy format."""
        result = {}
        for key, value in self.model_dump(
            exclude={"components", "platform"}, exclude_none=True
        ).items():
            result[key] = _value_to_legacy_string(value)
        return result


def _normalize_hosts(v: dict[str, Any]) -> dict[str, HostConfig]:
    """Normalize hosts from TOML format to HostConfig.

    Supports two formats:
    1. Simple: {"hostname": "component_name"} -> {"hostname": HostConfig(components=["component_name"])}
    2. Detailed: {"hostname": {"components": [...]}} -> preserved
    """
    result = {}
    for hostname, value in v.items():
        if isinstance(value, str):
            # Simple format: hostname = "component"
            result[hostname] = HostConfig(components=[value])
        elif isinstance(value, dict):
            # Detailed format
            result[hostname] = HostConfig.model_validate(value)
        else:
            raise ValueError(
                f"Invalid host config for '{hostname}': expected string or dict"
            )
    return result


# Annotated type for flexible hosts parsing
HostsDict = Annotated[dict[str, HostConfig], BeforeValidator(_normalize_hosts)]


class EnvironmentConfig(BaseModel):
    """Complete environment configuration from TOML."""

    model_config = {"extra": "forbid"}

    environment: EnvironmentSettings = Field(default_factory=EnvironmentSettings)
    hosts: HostsDict = {}
    host: dict[str, HostConfig] = {}  # Alternative: [host.hostname] sections
    components: dict[str, dict[str, Any]] = {}
    resolver: dict[str, str | list[str]] = {}
    vfs: dict[str, str] | None = None
    provisioners: dict[str, dict[str, Any]] = {}

    @field_validator("resolver")
    @classmethod
    def validate_resolver_ips(
        cls, v: dict[str, str | list[str]]
    ) -> dict[str, str | list[str]]:
        """Validate that resolver values are valid IPv4 or IPv6 addresses."""
        for hostname, ips in v.items():
            ip_list = [ips] if isinstance(ips, str) else ips
            for ip in ip_list:
                if not cls._is_valid_ip(ip):
                    raise ValueError(
                        f"Invalid IP address '{ip}' for host '{hostname}': "
                        f"must be a valid IPv4 or IPv6 address"
                    )
        return v

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Check if string is a valid IPv4 or IPv6 address."""
        try:
            IPv4Address(ip)
            return True
        except AddressValueError:
            pass
        try:
            IPv6Address(ip)
            return True
        except AddressValueError:
            pass
        return False

    def get_all_hosts(self) -> dict[str, HostConfig]:
        """Merge hosts and host sections."""
        result = dict(self.hosts)
        result.update(self.host)
        return result


class ConfigLoadError(Exception):
    """Error loading TOML configuration."""

    def __init__(
        self,
        message: str,
        details: str | None = None,
        errors: list[dict] | None = None,
        source_file: str | None = None,
    ):
        self.message = message
        self.details = details
        self.errors = errors or []
        self.source_file = source_file
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\n{self.details}"
        return self.message


def load_toml_config(content: str, source: str = "<toml>") -> EnvironmentConfig:
    """Load and validate TOML configuration.

    Args:
        content: TOML string content
        source: Source identifier for error messages

    Returns:
        Validated EnvironmentConfig

    Raises:
        ConfigLoadError: If TOML is invalid or validation fails
    """
    # Parse TOML
    try:
        data = rtoml.loads(content)
    except Exception as e:
        raise ConfigLoadError(f"Invalid TOML syntax in {source}", str(e))

    # Validate with Pydantic
    try:
        return EnvironmentConfig.model_validate(data)
    except ValidationError as e:
        errors = _collect_validation_errors(e, content)
        details = _format_validation_errors_from_list(errors)
        raise ConfigLoadError(
            f"Configuration validation failed in {source}",
            details,
            errors=errors,
            source_file=source,
        )


def _find_line_for_key(content: str, location: str) -> int | None:
    """Find the line number for a given location path.

    Args:
        content: Original TOML content
        location: Dot-separated path like "environment.update_method"

    Returns:
        1-indexed line number or None if not found
    """
    parts = location.split(".")
    if not parts:
        return None

    lines = content.split("\n")
    current_section = None
    target_section = None
    target_key = None

    # Determine what we're looking for
    if len(parts) == 1:
        # Top-level key (rare in our schema)
        target_key = parts[0]
    elif len(parts) == 2:
        # Section.key like "environment.update_method"
        target_section = parts[0]
        target_key = parts[1]
    elif len(parts) >= 3:
        # Nested like "hosts.localhost" or deeper
        target_section = parts[0]
        target_key = parts[-1]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track current section
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            # Handle quoted section names
            if section_name.startswith('"') and section_name.endswith('"'):
                section_name = section_name[1:-1]
            current_section = section_name.split(".")[0]  # Get first part for nested

        # Check for key match
        if "=" in stripped:
            key_part = stripped.split("=", 1)[0].strip()
            # Remove quotes from key if present
            if key_part.startswith('"') and key_part.endswith('"'):
                key_part = key_part[1:-1]

            if key_part == target_key:
                # Check if we're in the right section
                if target_section is None or current_section == target_section:
                    return i

    # If not found with exact section match, try to find key in matching section
    # This handles cases where the key is nested (e.g., resolver."hostname")
    if target_section:
        in_target_section = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track section changes
            if stripped.startswith("[") and stripped.endswith("]"):
                section_name = stripped[1:-1].strip()
                if section_name.startswith('"') and section_name.endswith('"'):
                    section_name = section_name[1:-1]
                in_target_section = section_name == target_section
                continue

            # Check for key in target section
            if in_target_section and "=" in stripped:
                key_part = stripped.split("=", 1)[0].strip()
                if key_part.startswith('"') and key_part.endswith('"'):
                    key_part = key_part[1:-1]
                if key_part == target_key:
                    return i

    return None


def _collect_validation_errors(
    e: ValidationError, content: str
) -> list[dict[str, Any]]:
    """Collect validation errors as structured data.

    Args:
        e: The ValidationError from Pydantic
        content: Original TOML content for line number lookup

    Returns:
        List of error dicts with 'line', 'message', 'location', 'source_line'
    """
    import re

    errors = []
    for error in e.errors():
        loc = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]
        line_num = None
        source_line = None

        # Special handling for resolver errors - extract hostname from message
        if loc == "resolver" and "for host '" in msg:
            match = re.search(r"for host '([^']+)'", msg)
            if match:
                hostname = match.group(1)
                line_num = _find_resolver_host_line(content, hostname)
                if line_num:
                    source_lines = content.split("\n")
                    if line_num <= len(source_lines):
                        source_line = source_lines[line_num - 1].strip()

        # Try to find line number for other errors
        if line_num is None:
            line_num = _find_line_for_key(content, loc)
            if line_num:
                source_lines = content.split("\n")
                if line_num <= len(source_lines):
                    source_line = source_lines[line_num - 1].strip()

        errors.append(
            {
                "line": line_num,
                "message": msg,
                "location": loc,
                "source_line": source_line,
            }
        )

    return errors


def _format_validation_errors_from_list(errors: list[dict[str, Any]]) -> str:
    """Format structured errors as string (for non-Rich output).

    Args:
        errors: List of error dicts from _collect_validation_errors

    Returns:
        Formatted error string
    """
    lines = []
    for error in errors:
        if error["line"] and error["source_line"]:
            lines.append(f"  line {error['line']}: {error['message']}")
            lines.append(f"    {error['source_line']}")
        else:
            lines.append(f"  {error['location']}: {error['message']}")
    return "\n".join(lines)


def _format_validation_errors(e: ValidationError, content: str = "") -> str:
    """Format Pydantic validation errors with line numbers.

    Args:
        e: The ValidationError from Pydantic
        content: Original TOML content for line number lookup

    Returns:
        Formatted error string
    """
    import re

    lines = []
    for error in e.errors():
        loc = ".".join(str(x) for x in error["loc"])
        msg = error["msg"]

        # Special handling for resolver errors - extract hostname from message
        if loc == "resolver" and "for host '" in msg:
            # Extract hostname from error message like:
            # "Invalid IP address 'x' for host 'invalid.example.com': ..."
            match = re.search(r"for host '([^']+)'", msg)
            if match:
                hostname = match.group(1)
                # Look for the hostname key in [resolver] section
                line_num = _find_resolver_host_line(content, hostname)
                if line_num:
                    source_lines = content.split("\n")
                    if line_num <= len(source_lines):
                        line_content = source_lines[line_num - 1].strip()
                        lines.append(f"  line {line_num}: {msg}")
                        lines.append(f"    {line_content}")
                        continue

        # Try to find line number
        line_num = _find_line_for_key(content, loc) if content else None

        if line_num:
            # Show error with line number and content
            source_lines = content.split("\n")
            if line_num <= len(source_lines):
                line_content = source_lines[line_num - 1].strip()
                lines.append(f"  line {line_num}: {msg}")
                lines.append(f"    {line_content}")
            else:
                lines.append(f"  {loc}: {msg}")
        else:
            lines.append(f"  {loc}: {msg}")

    return "\n".join(lines)


def _find_resolver_host_line(content: str, hostname: str) -> int | None:
    """Find the line number for a hostname in the resolver section.

    Args:
        content: Original TOML content
        hostname: The hostname to find (e.g., 'api.example.com')

    Returns:
        1-indexed line number or None if not found
    """
    lines = content.split("\n")
    in_resolver = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Track section changes
        if stripped.startswith("[") and stripped.endswith("]"):
            section_name = stripped[1:-1].strip()
            if section_name.startswith('"') and section_name.endswith('"'):
                section_name = section_name[1:-1]
            in_resolver = section_name == "resolver"
            continue

        # Look for hostname key in resolver section
        if in_resolver and "=" in stripped:
            key_part = stripped.split("=", 1)[0].strip()
            # Remove quotes from key if present
            if key_part.startswith('"') and key_part.endswith('"'):
                key_part = key_part[1:-1]
            if key_part == hostname:
                return i

    return None


def to_legacy_format(config: EnvironmentConfig) -> dict[str, dict[str, str]]:
    """Convert Pydantic config to legacy INI-style format.

    Returns a dict compatible with the Config class interface:
    {
        "environment": {"host_domain": "...", ...},
        "hosts": {"host1": "component1", ...},
        "component:myapp": {"setting": "value", ...},
        "host:host1": {"data-ram": "4", "components": "comp1\\ncomp2"},
        "resolver": {"hostname": "1.2.3.4\\n::1"},
    }
    """
    legacy: dict[str, dict[str, str]] = {}

    # [environment]
    env_dict = config.environment.model_dump(exclude_none=True, exclude_unset=True)
    if env_dict:
        legacy["environment"] = {k: str(v) for k, v in env_dict.items()}

    # Get merged hosts
    all_hosts = config.get_all_hosts()

    # [hosts] - simple hostname -> component mapping (first component only)
    hosts_section: dict[str, str] = {}
    for hostname, hostcfg in all_hosts.items():
        if hostcfg.components:
            hosts_section[hostname] = hostcfg.components[0]
    if hosts_section:
        legacy["hosts"] = hosts_section

    # [host:hostname] - detailed host config
    for hostname, hostcfg in all_hosts.items():
        host_section: dict[str, str] = {}

        # Components as newline-separated string
        if hostcfg.components:
            host_section["components"] = "\n".join(hostcfg.components)

        # Platform if set
        if hostcfg.platform:
            host_section["platform"] = hostcfg.platform

        # All other fields (including data-*)
        for key, value in hostcfg.get_data_attributes().items():
            host_section[key] = value

        if (
            len(host_section) > 1
            or "components" not in host_section
            or len(hostcfg.components) > 1
        ):
            # Only add [host:xxx] section if there's more than just the first component
            legacy[f"host:{hostname}"] = host_section

    # [component:name] - component overrides
    for comp_name, comp_config in config.components.items():
        if comp_config:
            legacy[f"component:{comp_name}"] = {
                k: _value_to_legacy_string(v) for k, v in comp_config.items()
            }

    # [resolver] - DNS overrides
    if config.resolver:
        resolver_section: dict[str, str] = {}
        for hostname, ips in config.resolver.items():
            if isinstance(ips, list):
                resolver_section[hostname] = "\n".join(ips)
            else:
                resolver_section[hostname] = ips
        legacy["resolver"] = resolver_section

    # [vfs]
    if config.vfs:
        legacy["vfs"] = config.vfs

    # [provisioner:name]
    for prov_name, prov_config in config.provisioners.items():
        if prov_config:
            legacy[f"provisioner:{prov_name}"] = {
                k: _value_to_legacy_string(v) for k, v in prov_config.items()
            }

    return legacy


def _value_to_legacy_string(value: Any) -> str:
    """Convert a value to legacy INI-style string format."""
    if isinstance(value, bool):
        return "True" if value else "False"
    elif isinstance(value, list):
        return "\n".join(str(v) for v in value)
    elif isinstance(value, dict):
        # Nested dict - convert to YAML for the horror show
        # (users should prefer proper TOML structure)
        import yaml

        return yaml.dump(value, default_flow_style=False)
    else:
        return str(value)


class DictConfigSection(dict):
    """A dict that also supports as_list() like ConfigSection."""

    def as_list(self, option: str) -> list[str]:
        """Parse a value as a list (comma or newline separated)."""
        result = self[option]
        if "," in result:
            result = [x.strip() for x in result.split(",")]
        elif "\n" in result:
            result = [x.strip() for x in result.split("\n")]
            result = [x for x in result if x]
        else:
            result = [result]
        return result


class DictConfig:
    """Config-like interface for legacy dict format.

    Compatible with the existing Config class interface.
    """

    def __init__(self, data: dict[str, dict[str, str]]):
        self._data = {k: DictConfigSection(v) for k, v in data.items()}

    def __contains__(self, section: str) -> bool:
        return section in self._data

    def __getitem__(self, section: str) -> DictConfigSection:
        return self._data[section]

    def __iter__(self):
        return iter(self._data.keys())

    def get(
        self, section: str, default: dict[str, str] | None = None
    ) -> DictConfigSection | dict[str, str]:
        return self._data.get(section, default or {})

    def options(self, section: str) -> list[str]:
        """Return keys in a section (for ConfigParser compatibility)."""
        return list(self._data.get(section, {}).keys())
