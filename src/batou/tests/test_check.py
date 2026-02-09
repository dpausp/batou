"""Tests for batou check command."""

import pytest

from batou.check import CheckCommand, LocalValidator
from batou.environment import Environment


def test_check_success_case(sample_service):
    """Test check command with successful validation."""
    from batou.check import main

    # Should succeed with exit code 0
    with pytest.raises(SystemExit) as r:
        main(environment="test-without-env-config", platform=None, timeout=None)
    assert r.value.code == 0


def test_check_loads_environment(sample_service):
    """Test that check command loads environment correctly."""
    cmd = CheckCommand("test-without-env-config", None, None)
    cmd.load_environment()

    assert cmd.environment is not None
    assert cmd.environment.name == "test-without-env-config"


def test_check_loads_secrets(sample_service):
    """Test that check command loads secrets correctly."""
    cmd = CheckCommand("test-without-env-config", None, None)
    cmd.load_environment()
    cmd.load_secrets()

    # Secrets should be loaded (even if empty)
    assert cmd.environment.secret_provider is not None


def test_check_only_connects_to_first_host(sample_service):
    """Test that check command only connects to first host when multiple hosts exist."""
    # Create environment with multiple hosts
    e = Environment("test-without-env-config")
    e.load()

    # Track how many hosts get start() called on them
    start_call_count = 0
    start_call_hosts = []

    original_start = None
    for host in e.hosts.values():
        # Store the original start method from the first host
        if original_start is None:
            original_start = host.start

        # Patch start() to just track calls without doing anything
        def mock_start(*args, **kwargs):
            nonlocal start_call_count
            start_call_count += 1
            start_call_hosts.append(host.name)
            # Return empty list like real start() would
            return []

        host.start = mock_start

    # Validate configuration
    validator = LocalValidator(e)
    errors = validator.validate_configuration()

    # Should start() only on first host (or at most 1 if there's only 1 host)
    max_expected_starts = min(1, len(e.hosts))
    assert start_call_count <= max_expected_starts, (
        f"Expected at most {max_expected_starts} start() calls, got {start_call_count} on hosts: {start_call_hosts}"
    )


def test_check_debug_mode(sample_service):
    """Test that check command respects debug mode."""
    import batou

    original_debug = batou.output.enable_debug

    try:
        batou.output.enable_debug = True
        cmd = CheckCommand("test-without-env-config", None, None)
        assert cmd.debug is True
    finally:
        batou.output.enable_debug = original_debug
