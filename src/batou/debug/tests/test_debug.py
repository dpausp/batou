"""Tests for batou debug command (argparse-based)."""

from batou.debug.cli import main


def test_debug_command_shows_all_settings(capsys, monkeypatch):
    """Test debug command displays all debug settings."""
    # Ensure all environment variables are unset
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])

    captured = capsys.readouterr()
    assert "Debug Settings" in captured.out
    assert "Field Name" in captured.out
    assert "Environment" in captured.out and "Variable" in captured.out
    assert "Possible" in captured.out and "Values" in captured.out
    assert "Description" in captured.out
    assert "Current" in captured.out and "Value" in captured.out


def test_debug_command_shows_current_values(capsys, monkeypatch):
    """Test debug command shows correct current values."""
    # Set some environment variables
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")

    main([])

    captured = capsys.readouterr()
    # Check that current values are displayed
    assert "summary" in captured.out
    assert "2" in captured.out


def test_debug_command_shows_field_names(capsys, monkeypatch):
    """Test debug command shows all field names."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])

    captured = capsys.readouterr()
    # Check that all field names are present
    assert "show_diff" in captured.out
    assert "show_secret_diffs" in captured.out
    assert "track_fds" in captured.out
    assert "profile" in captured.out
    assert "profile_lines" in captured.out


def test_debug_command_shows_env_vars(capsys, monkeypatch):
    """Test debug command shows correct environment variable names."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])

    captured = capsys.readouterr()
    # Check that all environment variable names are present
    assert "BATOU_SHOW" in captured.out
    assert "BATOU_SECRET" in captured.out or "BATOU_SHOW_" in captured.out
    assert "BATOU_TRACK" in captured.out
    assert "BATOU_PROFI" in captured.out


def test_debug_command_no_args_is_ok(capsys, monkeypatch):
    """Test debug command with no args runs successfully."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])

    captured = capsys.readouterr()
    # Should run successfully
    assert "Debug Settings" in captured.out
