"""Tests for SSH client module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from batou.ssh import SSHClient, SSHConfig, SSHError


class TestSSHConfig:
    """Tests for SSHConfig class."""

    def test_init(self):
        config = SSHConfig(hostname="example.com", ssh_config_path="/path/to/config")
        assert config.hostname == "example.com"
        assert config.ssh_config_path == "/path/to/config"
        assert config.user is None
        assert config.port == 22
        assert config.strict_host_key_check is True

    def test_init_no_config_path(self):
        config = SSHConfig(hostname="example.com")
        assert config.hostname == "example.com"
        assert config.ssh_config_path is None
        assert config.user is None
        assert config.port == 22

    def test_known_hosts_file_default(self):
        config = SSHConfig(hostname="example.com", ssh_config_path=None)
        expected_path = Path.home() / ".ssh" / "known_hosts"
        assert config.known_hosts_file == expected_path

    def test_str(self):
        config = SSHConfig(hostname="example.com", ssh_config_path=None)
        assert str(config) == "SSHConfig(hostname=example.com)"


class TestSSHClient:
    """Tests for SSHClient class."""

    @pytest.fixture
    def mock_config(self):
        config = SSHConfig(hostname="example.com", ssh_config_path=None)
        config.user = "testuser"
        return config

    @pytest.fixture
    def mock_paramiko_client(self):
        with patch("batou.ssh.paramiko.SSHClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client
            yield mock_client

    def test_init(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)
        assert client.config == mock_config
        assert client._connected is False

    def test_ensure_known_host_success(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # Mock successful connection
        mock_paramiko_client.connect.return_value = None
        mock_paramiko_client.close.return_value = None

        result = client.ensure_known_host()

        assert result is True
        mock_paramiko_client.load_system_host_keys.assert_called_once()
        mock_paramiko_client.set_missing_host_key_policy.assert_called_once()
        mock_paramiko_client.connect.assert_called_once()
        mock_paramiko_client.close.assert_called_once()

    def test_ensure_known_host_failure(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # Mock SSH exception
        import paramiko

        mock_paramiko_client.connect.side_effect = paramiko.SSHException(
            "Host key verification failed"
        )

        result = client.ensure_known_host()

        assert result is False

    def test_run_success(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # Mock successful command execution
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stdout.channel.recv_exit_status.return_value = 0

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"errors"

        mock_paramiko_client.exec_command.return_value = (
            None,
            mock_stdout,
            mock_stderr,
        )

        result = client.run("ls -la")

        assert result["stdout"] == "output"
        assert result["stderr"] == "errors"
        assert result["returncode"] == 0
        assert result["success"] is True
        mock_paramiko_client.connect.assert_called_once()
        mock_paramiko_client.exec_command.assert_called_once()

    def test_run_failure_with_check(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # Mock failed command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stdout.channel.recv_exit_status.return_value = 1

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"error"

        mock_paramiko_client.exec_command.return_value = (
            None,
            mock_stdout,
            mock_stderr,
        )

        with pytest.raises(SSHError):
            client.run("ls -la", check=True)

    def test_run_failure_without_check(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # Mock failed command
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stdout.channel.recv_exit_status.return_value = 1

        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b"error"

        mock_paramiko_client.exec_command.return_value = (
            None,
            mock_stdout,
            mock_stderr,
        )

        result = client.run("ls -la", check=False)

        assert result["returncode"] == 1
        assert result["success"] is False

    def test_run_ssh_exception(self, mock_config, mock_paramiko_client):
        import paramiko

        client = SSHClient(mock_config)

        # Mock SSH exception during connect
        mock_paramiko_client.connect.side_effect = paramiko.SSHException(
            "Connection failed"
        )

        with pytest.raises(SSHError) as exc_info:
            client.run("ls -la")

        assert "SSH error" in str(exc_info.value)

    def test_close(self, mock_config, mock_paramiko_client):
        client = SSHClient(mock_config)

        # First connect
        mock_paramiko_client.connect.return_value = None
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b""
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_paramiko_client.exec_command.return_value = (
            None,
            mock_stdout,
            mock_stderr,
        )

        client.run("echo test")
        assert client._connected is True

        # Now close
        client.close()
        assert client._connected is False
        mock_paramiko_client.close.assert_called()

    def test_context_manager(self, mock_config, mock_paramiko_client):
        """Test context manager properly closes connection."""
        client = SSHClient(mock_config)

        # Simulate a connected client
        client._connected = True

        # Test context manager exit
        with client:
            pass

        # Connection should be closed on exit
        mock_paramiko_client.close.assert_called_once()
        assert client._connected is False


class TestSSHError:
    """Tests for SSHError exception class."""

    def test_from_context(self):
        error = SSHError.from_context("Test error message")
        assert error.message == "Test error message"

    def test_str(self):
        error = SSHError.from_context("Test error message")
        assert str(error) == "Test error message"

    def test_report(self):
        error = SSHError.from_context("Test error message")
        # Should not raise - just verify it has the method
        assert hasattr(error, "report")
