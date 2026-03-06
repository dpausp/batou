"""Consolidated tests for diff control environment variables.

This test suite covers REQ-FUNC-003 requirements for diff output control
through environment variables BATOU_SHOW_DIFF and BATOU_SHOW_SECRET_DIFFS.
"""

import pytest

import batou
from batou.debug.settings import DebugSettings
from batou.lib.file import Content

# REQ-FUNC-003-001: BATOU_SHOW_DIFF Environment Variable


def test_batou_show_diff_full(monkeypatch, output, root):
    # REQ-FUNC-003-001: BATOU_SHOW_DIFF=full shows complete unified diffs
    """Test default mode shows complete unified diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new content\nline 2\n")
    root.component += p

    with open(p.path, "w") as f:
        f.write("old content\nline 2\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # Show full diff
    assert "  path ---" in output.backend.output
    assert "  path +++" in output.backend.output
    assert "  path -old content" in output.backend.output
    assert "  path +new content" in output.backend.output


def test_batou_show_diff_summary(monkeypatch, output, root):
    # REQ-FUNC-003-001: BATOU_SHOW_DIFF=summary shows file list only
    """Test summary mode shows only changed file list."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new content\nline 2\nline 3\n")
    root.component += p

    with open(p.path, "w") as f:
        f.write("old content\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # Only show summary, not diff lines
    assert f"changed: {p.path}" in output.backend.output
    assert "  path ---" not in output.backend.output
    assert "  path +++" not in output.backend.output
    assert "  path -old" not in output.backend.output
    assert "  path +new" not in output.backend.output


def test_batou_show_diff_none(monkeypatch, output, root):
    # REQ-FUNC-003-001: BATOU_SHOW_DIFF=none suppresses all diff output
    """Test none mode suppresses all diff output."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "none")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new content\n")
    root.component += p

    with open(p.path, "w") as f:
        f.write("old content\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # No diff output, only the component header
    assert "  path ---" not in output.backend.output
    assert "  path +++" not in output.backend.output


def test_batou_show_diff_invalid(monkeypatch, capsys):
    # REQ-FUNC-003-001: Invalid values fall back to full with warning
    """Test invalid BATOU_SHOW_DIFF value raises validation error."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "invalid_value")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Pydantic will raise validation error for invalid literal
    with pytest.raises(Exception):
        DebugSettings()


# REQ-FUNC-003-002: BATOU_SHOW_SECRET_DIFFS Override


def test_batou_show_secret_diffs_enabled(monkeypatch, output, root):
    # REQ-FUNC-003-002: BATOU_SHOW_SECRET_DIFFS=1 overrides sensitive_data flag
    """Test BATOU_SHOW_SECRET_DIFFS=1 shows diff for sensitive data."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "1")

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new secret\n", sensitive_data=True)
    root.component += p

    with open(p.path, "w") as f:
        f.write("old secret\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # Diff shown despite sensitive_data flag
    assert "  path ---" in output.backend.output
    assert "  path +++" in output.backend.output
    assert "  path -old secret" in output.backend.output
    assert "  path +new secret" in output.backend.output


def test_batou_show_secret_diffs_disabled(monkeypatch, output, root):
    # REQ-FUNC-003-002: BATOU_SHOW_SECRET_DIFFS=0 respects sensitive_data flag
    """Test BATOU_SHOW_SECRET_DIFFS=0 respects sensitive_data flag."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "0")

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new secret\n", sensitive_data=True)
    root.component += p

    with open(p.path, "w") as f:
        f.write("old secret\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # No diff shown
    assert "Not showing diff as it contains sensitive data." in output.backend.output
    assert "  path ---" not in output.backend.output


# REQ-FUNC-003-003: Startup Logging


def test_startup_logging_shows_env_vars(monkeypatch, output):
    # REQ-FUNC-003-003: Display behavior-changing env vars at startup
    """Test show() outputs for BATOU_SHOW_DIFF=summary."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert (
        "BATOU_SHOW_DIFF=summary - diff output reduced to file list" in backend.output
    )


def test_startup_logging_format(monkeypatch, output):
    # REQ-FUNC-003-003: Format: [INFO] ENV_VAR=value - description
    """Test show() outputs format for BATOU_SHOW_DIFF=none."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.setenv("BATOU_SHOW_DIFF", "none")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert "BATOU_SHOW_DIFF=none - diff output suppressed" in backend.output


# REQ-FUNC-003-004: File Component Integration


def test_file_component_respects_show_diff(monkeypatch, output, root):
    # REQ-FUNC-003-004: File.verify() respects BATOU_SHOW_DIFF setting
    """Test File component respects BATOU_SHOW_DIFF=none."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "none")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "test.txt"
    p = Content(path, content="new content\n")
    root.component += p

    with open(p.path, "w") as f:
        f.write("old content\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # No diff output when BATOU_SHOW_DIFF=none
    assert "  test.txt ---" not in output.backend.output
    assert "  test.txt +++" not in output.backend.output


def test_file_component_secret_override(monkeypatch, output, root):
    # REQ-FUNC-003-004: Interaction with sensitive_data flag
    """Test BATOU_SHOW_DIFF=summary with BATOU_SHOW_SECRET_DIFFS=1."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "1")

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new secret\n", sensitive_data=True)
    root.component += p

    with open(p.path, "w") as f:
        f.write("old secret\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # Summary shown despite sensitive_data flag due to override
    assert f"changed: {p.path}" in output.backend.output
    assert "  path ---" not in output.backend.output
    assert "  path +++" not in output.backend.output


# REQ-FUNC-003-005: Backward Compatibility


def test_backward_compatibility(monkeypatch, output, root):
    # REQ-FUNC-003-005: Default behavior unchanged from pre-implementation
    """Test default behavior (no env vars) shows full diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)

    # Patch file.py's debug_settings to pick up new environment variables
    import batou.lib.file as file_module

    file_module.debug_settings = DebugSettings()

    path = "path"
    p = Content(path, content="new content\nline 2\n")
    root.component += p

    with open(p.path, "w") as f:
        f.write("old content\nline 2\n")

    with pytest.raises(batou.UpdateNeeded):
        p.verify()

    # Default behavior: show full diff
    assert "  path ---" in output.backend.output
    assert "  path +++" in output.backend.output
    assert "  path -old content" in output.backend.output
    assert "  path +new content" in output.backend.output
