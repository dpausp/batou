"""Test version consistency across sources."""

from importlib.metadata import version as get_metadata_version

import batou
from batou.main import _get_version


def test_version_consistency():
    """Ensure __version__, importlib.metadata and _get_version() match."""
    metadata_version = get_metadata_version("batou")
    init_version = batou.__version__
    main_version = _get_version()

    assert metadata_version == init_version == main_version, (
        f"Version mismatch: metadata={metadata_version}, "
        f"__version__={init_version}, _get_version()={main_version}"
    )


def test_version_not_unknown():
    """Ensure version is properly resolved (not 'unknown')."""
    version = _get_version()

    assert version != "unknown", (
        "Version is 'unknown' - package not properly installed. "
        "Run 'pip install -e .' first."
    )
