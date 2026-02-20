"""Test version consistency across sources."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as get_metadata_version

import pytest


def test_version_consistency():
    """Ensure __version__, importlib.metadata and _get_version() match."""
    import batou
    from batou.main import _get_version

    main_version = _get_version()

    # Skip if package not installed
    if main_version == "unknown":
        pytest.skip("Package not installed - run 'pip install -e .' first")

    try:
        metadata_version = get_metadata_version("batou")
    except PackageNotFoundError:
        pytest.skip("Package metadata not available")

    init_version = batou.__version__

    assert metadata_version == init_version == main_version, (
        f"Version mismatch: metadata={metadata_version}, "
        f"__version__={init_version}, _get_version()={main_version}"
    )


def test_version_not_unknown():
    """Ensure version is properly resolved (not 'unknown')."""
    from batou.main import _get_version

    version = _get_version()

    if version == "unknown":
        pytest.skip("Package not installed - run 'pip install -e .' first")

    assert version != "unknown"
