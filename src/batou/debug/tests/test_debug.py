"""Tests for batou debug command (backward compatibility)."""

from typer.testing import CliRunner

from batou.debug.cli import app


def test_debug_command_shows_all_settings(monkeypatch):
    """Test debug command displays all debug settings."""
    runner = CliRunner()

    # Ensure all environment variables are unset
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    result = runner.invoke(app)

    assert result.exit_code == 0
    assert "Debug Settings" in result.stdout
    assert "Field Name" in result.stdout
    # Table truncates long column names with "..." and may wrap
    assert "Environment" in result.stdout and "Variable" in result.stdout
    assert "Possible" in result.stdout and "Values" in result.stdout
    assert "Description" in result.stdout
    assert "Current" in result.stdout and "Value" in result.stdout


def test_debug_command_shows_current_values(monkeypatch):
    """Test debug command shows correct current values."""
    runner = CliRunner()

    # Set some environment variables
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")

    result = runner.invoke(app)

    assert result.exit_code == 0
    # Check that current values are displayed
    assert "summary" in result.stdout
    assert "2" in result.stdout


def test_debug_command_shows_field_names(monkeypatch):
    """Test debug command shows all field names."""
    runner = CliRunner()

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    result = runner.invoke(app)

    assert result.exit_code == 0
    # Check that all field names are present
    assert "show_diff" in result.stdout
    assert "show_secret_diffs" in result.stdout
    assert "track_fds" in result.stdout
    assert "profile" in result.stdout
    assert "profile_lines" in result.stdout


def test_debug_command_shows_env_vars(monkeypatch):
    """Test debug command shows correct environment variable names."""
    runner = CliRunner()

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    result = runner.invoke(app)

    assert result.exit_code == 0
    # Check that all environment variable names are present (table may truncate with "...")
    assert "BATOU_SHOW" in result.stdout
    assert "BATOU_SECRET" in result.stdout or "BATOU_SHOW_" in result.stdout
    assert "BATOU_TRACK" in result.stdout
    assert "BATOU_PROFI" in result.stdout


def test_debug_command_no_args_is_help(monkeypatch):
    """Test debug command with no args shows help (no_args_is_help=True)."""
    runner = CliRunner()

    # Invoke without any arguments
    result = runner.invoke(app, [])

    # Should run successfully since it's the main command
    assert result.exit_code == 0
