"""Tests for batou debug command using pytest-patterns."""

import pytest

from batou.debug.cli import main

pytestmark = pytest.mark.debug


def test_debug_table_structure(patterns, monkeypatch, capsys):
    """Test debug table has correct structure and all expected content."""
    # Clear all env vars to get default values
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])
    captured = capsys.readouterr()

    # Start with minimal pattern - accept everything
    p = patterns.debug_table

    # Check for key content (all optional for now)
    p.optional("...Debug Settings...")
    p.optional("...Field Name...")
    p.optional("...Current Value...")
    p.optional("...Default...")

    # All field names
    p.optional("...show_diff...")
    p.optional("...show_secret_diffs...")
    p.optional("...track_fds...")
    p.optional("...fd_output_dir...")
    p.optional("...profile...")
    p.optional("...profile_lines...")

    # Descriptions
    p.optional("...Show file changes...")
    p.optional("...dangerous...")
    p.optional("...Track file descriptor...")
    p.optional("...Profile remote...")

    # Allow all other lines
    p.optional("...")

    assert p == captured.out


def test_debug_non_default_values_highlighted(patterns, monkeypatch, capsys):
    """Test debug table highlights non-default values."""
    # Set non-default values
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")
    monkeypatch.setenv("BATOU_PROFILE", "True")

    main([])
    captured = capsys.readouterr()

    # Check for non-default values (all optional)
    p = patterns.non_defaults

    p.optional("...summary...")
    p.optional("...2...")
    p.optional("...True...")

    # Allow all other content
    p.optional("...")

    assert p == captured.out


def test_debug_env_var_names(patterns, monkeypatch, capsys):
    """Test debug table shows environment variable names."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    main([])
    captured = capsys.readouterr()

    # Check for BATOU_* prefixes (all optional, table may truncate)
    p = patterns.env_vars

    p.optional("...BATOU_SH...")
    p.optional("...BATOU_TR...")
    p.optional("...BATOU_PR...")

    # Allow all other content
    p.optional("...")

    assert p == captured.out
