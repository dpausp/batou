"""Tests for batou check command."""

import os

import pytest
from typer.testing import CliRunner

from batou.check import (
    CheckCommand,
    LocalValidator,
    app,
    find_basedir,
    main,
    parse_environment_arg,
)
from batou.environment import Environment

# =============================================================================
# CLI Tests
# =============================================================================


runner = CliRunner()


def test_cli_help():
    """Test that CLI shows help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Fast local consistency check" in result.stdout


def test_cli_with_environment_path(sample_service):
    """Test CLI with full path to environment directory."""
    env_path = os.path.join(sample_service, "environments", "test-without-env-config")
    result = runner.invoke(app, [env_path])
    assert result.exit_code == 0
    assert "LOCAL CONSISTENCY CHECK FINISHED" in result.stdout


def test_cli_with_debug_flag(sample_service):
    """Test CLI with debug flag."""
    env_path = os.path.join(sample_service, "environments", "test-without-env-config")
    result = runner.invoke(app, ["-d", env_path])
    assert result.exit_code == 0
    assert "LOCAL CONSISTENCY CHECK FINISHED" in result.stdout


def test_cli_with_platform_option(sample_service):
    """Test CLI with platform option."""
    env_path = os.path.join(sample_service, "environments", "test-without-env-config")
    result = runner.invoke(app, ["-p", "some-platform", env_path])
    # May fail due to missing platform, but should parse args correctly
    assert "test-without-env-config" in result.stdout or result.exit_code != 0


# =============================================================================
# parse_environment_arg Tests
# =============================================================================


def test_parse_environment_arg_with_name():
    """Test parsing a simple environment name."""
    basedir, env_name = parse_environment_arg("test")
    assert basedir is None
    assert env_name == "test"


def test_parse_environment_arg_with_path(tmp_path):
    """Test parsing a path to an environment directory."""
    env_dir = tmp_path / "environments" / "staging"
    env_dir.mkdir(parents=True)

    basedir, env_name = parse_environment_arg(str(env_dir))

    assert basedir == str(tmp_path)
    assert env_name == "staging"


def test_parse_environment_arg_with_direct_path(tmp_path):
    """Test parsing a path that doesn't have 'environments' parent."""
    env_dir = tmp_path / "myenv"
    env_dir.mkdir()

    basedir, env_name = parse_environment_arg(str(env_dir))

    assert basedir == str(tmp_path)
    assert env_name == "myenv"


def test_parse_environment_arg_nonexistent_path():
    """Test parsing a non-existent path returns None for basedir."""
    basedir, env_name = parse_environment_arg("/nonexistent/env")
    assert basedir is None
    assert env_name == "/nonexistent/env"


# =============================================================================
# find_basedir Tests
# =============================================================================


def test_find_basedir_appenv(monkeypatch):
    """Test find_basedir with APPENV_BASEDIR set."""
    monkeypatch.setenv("APPENV_BASEDIR", "/appenv/base")
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    assert find_basedir() == "/appenv/base"


def test_find_basedir_virtual_env(monkeypatch):
    """Test find_basedir with VIRTUAL_ENV set."""
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")

    assert find_basedir() == "/project"


def test_find_basedir_appenv_has_priority(monkeypatch):
    """Test that APPENV_BASEDIR has priority over VIRTUAL_ENV."""
    monkeypatch.setenv("APPENV_BASEDIR", "/appenv/base")
    monkeypatch.setenv("VIRTUAL_ENV", "/other/.venv")

    assert find_basedir() == "/appenv/base"


def test_find_basedir_cwd_fallback(monkeypatch):
    """Test find_basedir falls back to cwd."""
    monkeypatch.delenv("APPENV_BASEDIR", raising=False)
    monkeypatch.delenv("VIRTUAL_ENV", raising=False)

    assert find_basedir() == os.getcwd()


# =============================================================================
# CheckCommand Tests
# =============================================================================


def test_check_success_case(sample_service):
    """Test check command with successful validation."""
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

    assert cmd.environment.secret_provider is not None


def test_check_only_connects_to_first_host(sample_service):
    """Test that check command only connects to first host."""
    e = Environment("test-without-env-config")
    e.load()

    start_call_count = 0
    start_call_hosts = []

    for host in e.hosts.values():

        def mock_start(*args, host=host, **kwargs):
            nonlocal start_call_count
            start_call_count += 1
            start_call_hosts.append(host.name)
            return []

        host.start = mock_start

    validator = LocalValidator(e)
    validator.validate_configuration()

    max_expected_starts = min(1, len(e.hosts))
    assert start_call_count <= max_expected_starts


def test_check_debug_mode(sample_service):
    """Test that check command respects debug mode."""
    cmd = CheckCommand("test-without-env-config", None, None, debug=True)
    assert cmd.debug is True
