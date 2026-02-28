"""Version utilities for batou."""

import importlib.metadata
import re
from datetime import datetime


def get_version() -> str:
    """Get raw version from package metadata."""
    try:
        return importlib.metadata.version("batou")
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def format_version(color: bool = True) -> str:
    """Format version with git rev and timestamp for dev builds.

    Parses hatch-vcs version strings like:
    - With timestamp: 2.6.2.post1.dev145+g36bbe20a3.d20260228190006
    - Without timestamp: 2.6.2.post1.dev147+g3c7bbc6e6

    Returns formatted string:
    - Release: 2.6.2
    - Dev with timestamp: 2.6.2-dev145 (git rev: 36bbe20a3, committed at 2026-02-28 19:00:06)
    - Dev without timestamp: 2.6.2-dev147 (git rev: 3c7bbc6e6)
    """
    version = get_version()

    # Pattern: version+g<sha>[.d<timestamp>][.dirty]
    # 'g' prefix from git describe is stripped from output
    # Timestamp is optional - hatch-vcs may not always include it
    match = re.match(r"^([^+]+)\+([gd][a-f0-9]+)(?:\.d(\d{14}))?(?:\.dirty)?$", version)

    if not match:
        # Not a hatch-vcs local version (release or unknown)
        return version

    base_version = match.group(1)
    git_rev = match.group(2).lstrip("g")  # Remove 'g' prefix from git describe
    timestamp_str = match.group(3)  # May be None

    # Build optional timestamp part
    if timestamp_str:
        try:
            dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
            formatted_time = f", committed at {dt.strftime('%Y-%m-%d %H:%M:%S')}"
        except ValueError:
            formatted_time = f", committed at {timestamp_str}"
    else:
        formatted_time = ""

    # Extract dev number if present (e.g., 2.6.2.post1.dev145 -> dev145)
    dev_match = re.search(r"\.dev(\d+)", base_version)
    dev_suffix = f"-dev{dev_match.group(1)}" if dev_match else ""

    # Clean base version (remove all .postN and .devN suffixes)
    clean_base = re.sub(r"\.(post\d+|dev\d+)", "", base_version)

    formatted = f"{clean_base}{dev_suffix} (git rev: {git_rev}{formatted_time})"

    if color and dev_suffix:
        # Yellow for dev versions using Rich markup
        return f"[yellow]{formatted}[/yellow]"

    return formatted


def is_dev_version() -> bool:
    """Check if current version is a development build."""
    version = get_version()
    return ".dev" in version or "+g" in version
