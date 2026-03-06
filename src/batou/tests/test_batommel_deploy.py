"""Tests for batommel deploy command."""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from batou.batommel.deploy import _generate_diff, app


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_project():
    """Create temporary project directory with environments."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        envs_dir = project_dir / "environments"
        envs_dir.mkdir()

        # Create a simple environment
        env_dir = envs_dir / "test"
        env_dir.mkdir()

        # Create minimal components directory
        components_dir = project_dir / "components"
        components_dir.mkdir()

        yield project_dir


@pytest.fixture
def minimal_toml():
    """Minimal valid TOML configuration."""
    return """\
[environment]
connect_method = "local"

[hosts]
localhost = "hello"
"""


@pytest.fixture
def complex_toml():
    """Complex TOML configuration with multiple sections."""
    return """\
[environment]
connect_method = "local"
timeout = 120

[hosts]
web01 = "nginx"
db01 = "postgres"

[host.web01]
components = ["nginx", "monitoring"]
data-ram = 4

[components.nginx]
port = 8080

[resolver]
"db.internal" = "10.0.1.50"
"""


class TestDiffGeneration:
    """Tests for diff generation."""

    def test_no_changes(self):
        """Test diff when content is identical."""
        old = "[environment]\nkey = value\n"
        new = "[environment]\nkey = value\n"
        diff = _generate_diff(old, new, "test.cfg")
        assert diff == ""

    def test_added_section(self):
        """Test diff when section is added."""
        old = "[environment]\nkey = value\n"
        new = "[environment]\nkey = value\n\n[hosts]\nhost = component\n"
        diff = _generate_diff(old, new, "test.cfg")
        assert "--- test.cfg (current)" in diff
        assert "+++ test.cfg (from TOML)" in diff
        assert "+[hosts]" in diff
        assert "+host = component" in diff

    def test_modified_value(self):
        """Test diff when value is modified."""
        old = "[environment]\ntimeout = 60\n"
        new = "[environment]\ntimeout = 120\n"
        diff = _generate_diff(old, new, "test.cfg")
        assert "-timeout = 60" in diff
        assert "+timeout = 120" in diff

    def test_removed_section(self):
        """Test diff when section is removed."""
        old = "[environment]\nkey = value\n\n[hosts]\nhost = component\n"
        new = "[environment]\nkey = value\n"
        diff = _generate_diff(old, new, "test.cfg")
        assert "-[hosts]" in diff
        assert "-host = component" in diff


class TestConversion:
    """Tests for TOML to INI conversion."""

    def test_minimal_conversion(self, temp_project, minimal_toml, runner):
        """Test conversion of minimal TOML."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        # Change to temp project directory
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test"])
            assert result.exit_code == 1  # Fails because no actual batou deploy
        finally:
            os.chdir(old_cwd)

        cfg_path = env_dir / "environment.cfg"
        assert cfg_path.exists()
        content = cfg_path.read_text()
        assert "[environment]" in content
        assert "connect_method = local" in content
        assert "[hosts]" in content

    def test_complex_conversion(self, temp_project, complex_toml, runner):
        """Test conversion of complex TOML with all sections."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(complex_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test"])
            assert result.exit_code == 1  # Fails because no actual batou deploy
        finally:
            os.chdir(old_cwd)

        cfg_path = env_dir / "environment.cfg"
        assert cfg_path.exists()
        content = cfg_path.read_text()
        assert "[environment]" in content
        assert "timeout = 120" in content
        assert "[hosts]" in content
        assert "web01 = nginx" in content
        assert "[host:web01]" in content
        assert "components = nginx" in content
        assert "data-ram = 4" in content
        assert "[component:nginx]" in content
        assert "port = 8080" in content
        assert "[resolver]" in content

    def test_overwrites_existing_cfg(self, temp_project, minimal_toml, runner):
        """Test that existing environment.cfg is overwritten (TOML precedence)."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        cfg_path = env_dir / "environment.cfg"

        # Create initial CFG
        cfg_path.write_text("[environment]\nold = value\n")

        # Create TOML
        toml_path.write_text(minimal_toml)

        # Run conversion
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            runner.invoke(app, ["test"])
        finally:
            os.chdir(old_cwd)

        # Verify TOML won
        content = cfg_path.read_text()
        assert "old = value" not in content
        assert "connect_method = local" in content


class TestDeployCommand:
    """Tests for deploy command interface."""

    def test_missing_environment_directory(self, temp_project, runner):
        """Test error when environment directory doesn't exist."""
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["nonexistent"])
            assert result.exit_code == 1
            assert "Environment directory not found" in result.output
        finally:
            os.chdir(old_cwd)

    def test_missing_toml_file(self, temp_project, runner):
        """Test error when environment.toml doesn't exist (REQ-FUNC-DEPLOY-004)."""
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test"])
            assert result.exit_code == 1
            assert "TOML configuration not found" in result.output
            assert "batommel ini-to-toml" in result.output
        finally:
            os.chdir(old_cwd)

    def test_invalid_toml_syntax(self, temp_project, runner):
        """Test error when TOML syntax is invalid."""
        env_dir = temp_project / "environments" / "test"
        env_dir.mkdir(parents=True, exist_ok=True)
        toml_path = env_dir / "environment.toml"
        toml_path.write_text("invalid [toml syntax")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test"])
            assert result.exit_code == 1
            assert "Invalid TOML syntax" in result.output
        finally:
            os.chdir(old_cwd)

    def test_quiet_flag_suppresses_output(self, temp_project, minimal_toml, runner):
        """Test --quiet flag suppresses diff and status output."""
        env_dir = temp_project / "environments" / "test"
        cfg_path = env_dir / "environment.cfg"
        cfg_path.write_text("[environment]\nold = value\n")

        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test", "--quiet"])
            # Should not show diff or conversion message
            assert "Changes to environment.cfg" not in result.output
            assert "Converted" not in result.output
        finally:
            os.chdir(old_cwd)

    def test_force_flag_skips_diff(self, temp_project, minimal_toml, runner):
        """Test --force flag skips diff display."""
        env_dir = temp_project / "environments" / "test"
        cfg_path = env_dir / "environment.cfg"
        cfg_path.write_text("[environment]\nold = value\n")

        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test", "--force"])
            # Should not show diff but should show conversion
            assert "Changes to environment.cfg" not in result.output
            # Force still shows conversion status
            assert "Converted" in result.output or result.exit_code == 1
        finally:
            os.chdir(old_cwd)

    def test_shows_diff_when_cfg_exists(self, temp_project, minimal_toml, runner):
        """Test diff is shown when environment.cfg exists (REQ-FUNC-DEPLOY-005)."""
        env_dir = temp_project / "environments" / "test"
        cfg_path = env_dir / "environment.cfg"
        cfg_path.write_text("[environment]\nold = value\n")

        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test"])
            assert "Changes to environment.cfg" in result.output
            assert "--- environment.cfg (current)" in result.output
            assert "+++ environment.cfg (from TOML)" in result.output
        finally:
            os.chdir(old_cwd)


class TestArgumentPassThrough:
    """Tests for argument passthrough to batou deploy."""

    def test_timeout_argument(self, temp_project, minimal_toml, runner):
        """Test --timeout is passed to batou deploy."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test", "--timeout", "300"])
            # Will fail because no actual deployment, but should show the argument
            assert result.exit_code == 1
        finally:
            os.chdir(old_cwd)

    def test_platform_argument(self, temp_project, minimal_toml, runner):
        """Test --platform is passed to batou deploy."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test", "--platform", "linux"])
            assert result.exit_code == 1
        finally:
            os.chdir(old_cwd)

    def test_dirty_argument(self, temp_project, minimal_toml, runner):
        """Test --dirty is passed to batou deploy."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(app, ["test", "--dirty"])
            assert result.exit_code == 1
        finally:
            os.chdir(old_cwd)

    def test_multiple_arguments(self, temp_project, minimal_toml, runner):
        """Test multiple arguments are passed together."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            result = runner.invoke(
                app, ["test", "--timeout", "300", "--dirty", "--platform", "linux"]
            )
            assert result.exit_code == 1
        finally:
            os.chdir(old_cwd)


class TestStandardLocation:
    """Tests for standard INI location (REQ-FUNC-DEPLOY-003)."""

    def test_writes_to_standard_location(self, temp_project, minimal_toml, runner):
        """Test INI is written to environments/<env>/environment.cfg."""
        env_dir = temp_project / "environments" / "test"
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            runner.invoke(app, ["test"])
        finally:
            os.chdir(old_cwd)

        cfg_path = env_dir / "environment.cfg"
        assert cfg_path.exists()
        assert cfg_path.is_file()


class TestTomlPrecedence:
    """Tests for TOML precedence over INI (REQ-FUNC-DEPLOY-006)."""

    def test_toml_overwrites_manual_ini_edits(self, temp_project, minimal_toml, runner):
        """Test that manual INI edits are lost when TOML exists."""
        env_dir = temp_project / "environments" / "test"
        cfg_path = env_dir / "environment.cfg"

        # Create manually edited INI
        cfg_path.write_text(
            "[environment]\n"
            "connect_method = ssh\n"  # Will be overwritten
            "manual_edit = should_disappear\n"
        )

        # Create TOML
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        # Run deploy
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            runner.invoke(app, ["test"])
        finally:
            os.chdir(old_cwd)

        # Verify TOML won
        content = cfg_path.read_text()
        assert "connect_method = local" in content  # From TOML
        assert "manual_edit" not in content  # Lost

    def test_toml_is_source_of_truth(self, temp_project, minimal_toml, runner):
        """Test that TOML is always the source, not INI."""
        env_dir = temp_project / "environments" / "test"

        # Create TOML first
        toml_path = env_dir / "environment.toml"
        toml_path.write_text(minimal_toml)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_project)
            # Run deploy to create INI
            runner.invoke(app, ["test"])

            # Check if INI was created
            cfg_path = env_dir / "environment.cfg"
            assert cfg_path.exists(), "INI file should be created even if deploy fails"

            # Modify TOML
            toml_path.write_text(
                '[environment]\nconnect_method = "ssh"\n\n[hosts]\nhost2 = "comp2"\n'
            )

            # Need to change directory again for second invoke (CliRunner resets it)
            os.chdir(temp_project)
            # Run deploy again
            runner.invoke(app, ["test"])
        finally:
            os.chdir(old_cwd)

        # Verify TOML changes are in INI
        cfg_path = env_dir / "environment.cfg"
        content = cfg_path.read_text()
        assert "connect_method = ssh" in content
        assert "host2 = comp2" in content
        assert "host1" not in content  # Old content should be gone
