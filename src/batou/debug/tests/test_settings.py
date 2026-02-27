import pytest

from batou.debug.settings import DebugSettings

pytestmark = pytest.mark.debug


def test_default_settings(monkeypatch):
    """Test default values for DebugSettings when ENV vars not set."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is False
    assert settings.track_fds == 0
    assert settings.profile is False


def test_show_diff_summary(monkeypatch):
    """Test BATOU_SHOW_DIFF=summary sets correct value."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "summary"
    assert settings.show_secret_diffs is False


def test_show_diff_none(monkeypatch):
    """Test BATOU_SHOW_DIFF=none sets correct value."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "none")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "none"
    assert settings.show_secret_diffs is False


def test_show_diff_invalid_defaults_to_full(monkeypatch):
    """Test BATOU_SHOW_DIFF with invalid value defaults to 'full'."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "invalid_value")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    # Pydantic will raise validation error for invalid literal
    with pytest.raises(Exception):
        DebugSettings()


def test_show_secret_diffs_true(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS=true enables secret diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "true")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is True


def test_show_secret_diffs_TRUE(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS=TRUE (case insensitive) enables secret diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "TRUE")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is True


def test_show_secret_diffs_1(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS=1 enables secret diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "1")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is True


def test_show_secret_diffs_false(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS=false disables secret diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "false")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is False


def test_show_secret_diffs_0(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS=0 disables secret diffs."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "0")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "full"
    assert settings.show_secret_diffs is False


def test_show_secret_diffs_invalid(monkeypatch):
    """Test BATOU_SHOW_SECRET_DIFFS with invalid value raises validation error."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "invalid")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    # Pydantic raises validation error for invalid bool values
    with pytest.raises(Exception):
        DebugSettings()


def test_both_env_vars_set(monkeypatch):
    """Test both BATOU_SHOW_DIFF and BATOU_SHOW_SECRET_DIFFS set."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "true")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.show_diff == "summary"
    assert settings.show_secret_diffs is True


def test_track_fds_enabled(monkeypatch):
    """Test BATOU_TRACK_FDS=1 enables simple FD tracking."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.setenv("BATOU_TRACK_FDS", "1")
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.track_fds == 1


def test_track_fds_verbose(monkeypatch):
    """Test BATOU_TRACK_FDS=2 enables verbose FD tracking."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    assert settings.track_fds == 2


def test_profile_enabled(monkeypatch):
    """Test BATOU_PROFILE=1 enables profiling."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.setenv("BATOU_PROFILE", "1")

    settings = DebugSettings()

    assert settings.profile is True


def test_show_no_flags(monkeypatch, output):
    """Test show() outputs message for default settings (no flags)."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings.show()

    assert "No expert/debug flags enabled" in backend.output
    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" not in backend.output
    assert (
        "Use `batou debug` command to see all available debug settings"
        in backend.output
    )


def test_show_show_diff_summary(monkeypatch, output):
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


def test_show_show_diff_none(monkeypatch, output):
    """Test show() outputs for BATOU_SHOW_DIFF=none."""
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


def test_show_show_secret_diffs_enabled(monkeypatch, output):
    """Test show() outputs warning for BATOU_SHOW_SECRET_DIFFS=1."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "1")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert "BATOU_SHOW_SECRET_DIFFS=1 - sensitive data diffs enabled" in backend.output


def test_show_both_diff_settings(monkeypatch, output):
    """Test show() outputs for both diff ENV vars set."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.setenv("BATOU_SHOW_DIFF", "none")
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "true")
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert "BATOU_SHOW_DIFF=none - diff output suppressed" in backend.output
    assert "BATOU_SHOW_SECRET_DIFFS=1 - sensitive data diffs enabled" in backend.output


def test_show_track_fds_enabled(monkeypatch, output):
    """Test show() outputs for BATOU_TRACK_FDS=1."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.setenv("BATOU_TRACK_FDS", "1")
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    settings.show()
    assert "BATOU_TRACK_FDS=1 - FD tracking enabled (simple)" in backend.output


def test_show_track_fds_verbose_enabled(monkeypatch, output):
    """Test show() outputs for BATOU_TRACK_FDS=2 (verbose)."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()

    settings.show()
    assert "BATOU_TRACK_FDS=2 - FD tracking enabled (verbose)" in backend.output


def test_show_profile_enabled(monkeypatch, output):
    """Test show() outputs for BATOU_PROFILE=1."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)

    monkeypatch.setenv("BATOU_PROFILE", "1")

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert "BATOU_PROFILE=1 - Profiling enabled" in backend.output


def test_show_multiple_flags(monkeypatch, output):
    """Test show() outputs for multiple flags enabled."""
    from batou._output import TestBackend

    backend = TestBackend()
    output.backend = backend

    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_SHOW_SECRET_DIFFS", "true")
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")
    monkeypatch.setenv("BATOU_PROFILE", "1")

    settings = DebugSettings()
    settings.show()

    assert "=== WARNING EXPERT/DEBUG FLAGS ENABLED ===" in backend.output
    assert (
        "BATOU_SHOW_DIFF=summary - diff output reduced to file list" in backend.output
    )
    assert "BATOU_SHOW_SECRET_DIFFS=1 - sensitive data diffs enabled" in backend.output
    assert "BATOU_TRACK_FDS=2 - FD tracking enabled (verbose)" in backend.output
    assert "BATOU_PROFILE=1 - Profiling enabled" in backend.output
    assert (
        "Use `batou debug` command to see all available debug settings"
        in backend.output
    )


def test_describe_returns_all_fields(monkeypatch):
    """Test describe() returns information for all settings fields."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings_info = settings.describe()

    assert isinstance(settings_info, list)
    assert (
        len(settings_info) == 6
    )  # show_diff, show_secret_diffs, track_fds, fd_output_dir, profile, profile_lines

    # Check first item has all required keys
    first = settings_info[0]
    assert "field_name" in first
    assert "env_var" in first
    assert "possible_values" in first
    assert "description" in first
    assert "current_value" in first


def test_describe_field_names(monkeypatch):
    """Test describe() returns correct field names."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings_info = settings.describe()

    field_names = [item["field_name"] for item in settings_info]
    assert "show_diff" in field_names
    assert "show_secret_diffs" in field_names
    assert "track_fds" in field_names
    assert "profile" in field_names
    assert "profile_lines" in field_names


def test_describe_env_var_names(monkeypatch):
    """Test describe() returns correct environment variable names."""
    monkeypatch.delenv("BATOU_SHOW_DIFF", raising=False)
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_TRACK_FDS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings_info = settings.describe()

    env_vars = {item["field_name"]: item["env_var"] for item in settings_info}
    assert env_vars["show_diff"] == "BATOU_SHOW_DIFF"
    assert env_vars["show_secret_diffs"] == "BATOU_SHOW_SECRET_DIFFS"
    assert env_vars["track_fds"] == "BATOU_TRACK_FDS"
    assert env_vars["profile"] == "BATOU_PROFILE"
    assert env_vars["profile_lines"] == "BATOU_PROFILE_LINES"


def test_describe_current_values(monkeypatch):
    """Test describe() returns correct current values."""
    monkeypatch.setenv("BATOU_SHOW_DIFF", "summary")
    monkeypatch.setenv("BATOU_TRACK_FDS", "2")
    monkeypatch.delenv("BATOU_SHOW_SECRET_DIFFS", raising=False)
    monkeypatch.delenv("BATOU_PROFILE", raising=False)

    settings = DebugSettings()
    settings_info = settings.describe()

    current_values = {
        item["field_name"]: item["current_value"] for item in settings_info
    }
    assert current_values["show_diff"] == "summary"
    assert current_values["track_fds"] == 2
    assert current_values["show_secret_diffs"] is False
    assert current_values["profile"] is False
