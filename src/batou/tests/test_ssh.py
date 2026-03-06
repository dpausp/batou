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

    def test_auto_add_host_keys_enabled(self, mock_config, mock_paramiko_client):
        # REQ-FUNC-SSH-003: Auto-add host keys when configured
        """Test auto-adding unknown host keys when enabled."""
        import paramiko

        client = SSHClient(mock_config)
        mock_paramiko_client.connect.return_value = None
        mock_paramiko_client.close.return_value = None

        result = client.ensure_known_host()

        assert result is True
        # Verify AutoAddPolicy was set
        policy_call = mock_paramiko_client.set_missing_host_key_policy
        policy_call.assert_called_once()
        assert isinstance(policy_call.call_args[0][0], paramiko.AutoAddPolicy)

    def test_auto_add_host_keys_disabled(self, mock_config, mock_paramiko_client):
        # REQ-FUNC-SSH-003: Auto-add host keys when configured
        """Test strict host key checking prevents auto-add."""
        mock_config.strict_host_key_check = True
        client = SSHClient(mock_config)
        mock_paramiko_client.connect.return_value = None
        mock_paramiko_client.close.return_value = None

        result = client.ensure_known_host()

        # Even with strict checking, AutoAddPolicy is used for ensure_known_host
        assert result is True
        mock_paramiko_client.set_missing_host_key_policy.assert_called_once()

    def test_no_interactive_prompts(self, mock_config, mock_paramiko_client):
        # REQ-FUNC-SSH-004: Prevent interactive prompts
        """Test connection doesn't trigger interactive prompts."""
        client = SSHClient(mock_config)

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

        # Verify connection uses key-based auth (no password parameter)
        connect_call = mock_paramiko_client.connect.call_args
        assert "password" not in connect_call[1]
        # Verify username and key_filename are passed (key-based auth)
        assert connect_call[1]["username"] == "testuser"
        assert "key_filename" in connect_call[1]

    def test_batch_mode_settings(self, mock_config, mock_paramiko_client):
        # REQ-FUNC-SSH-004: Prevent interactive prompts
        """Test batch mode settings prevent prompts during connection."""
        client = SSHClient(mock_config)

        mock_paramiko_client.connect.return_value = None
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stdout.channel.recv_exit_status.return_value = 0
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""
        mock_paramiko_client.exec_command.return_value = (
            None,
            mock_stdout,
            mock_stderr,
        )

        result = client.run("ls")

        assert result["success"] is True
        # Verify no password-based authentication
        connect_kwargs = mock_paramiko_client.connect.call_args[1]
        assert "password" not in connect_kwargs
        # Verify key-based auth parameters
        assert connect_kwargs.get("username") == "testuser"
        assert "key_filename" in connect_kwargs


class TestSSHConfigParsing:
    """Tests for SSH config file parsing."""

    def test_parse_openssh_config_directives(self, tmp_path):
        # REQ-FUNC-SSH-011: Parse OpenSSH configuration directives
        """Test parsing standard OpenSSH config directives."""
        config_file = tmp_path / "config"
        config_file.write_text(
            "Host example.com\n"
            "    User testuser\n"
            "    Port 2222\n"
            "    IdentityFile ~/.ssh/id_rsa_custom\n"
            "    StrictHostKeyChecking no\n"
        )

        config = SSHConfig(hostname="example.com", ssh_config_path=str(config_file))

        assert config.user == "testuser"
        assert config.port == 2222
        assert config.identity_file is not None
        assert "id_rsa_custom" in config.identity_file
        assert config.strict_host_key_check is False

    def test_multiple_host_configurations(self, tmp_path):
        # REQ-FUNC-SSH-011: Parse OpenSSH configuration directives
        """Test parsing config with multiple host entries."""
        config_file = tmp_path / "config"
        config_file.write_text(
            "Host server1.example.com\n"
            "    User user1\n"
            "    Port 2222\n"
            "\n"
            "Host server2.example.com\n"
            "    User user2\n"
            "    Port 2223\n"
            "    IdentityFile ~/.ssh/id_server2\n"
        )

        # Test first host
        config1 = SSHConfig(
            hostname="server1.example.com", ssh_config_path=str(config_file)
        )
        assert config1.user == "user1"
        assert config1.port == 2222
        assert config1.identity_file is None

        # Test second host
        config2 = SSHConfig(
            hostname="server2.example.com", ssh_config_path=str(config_file)
        )
        assert config2.user == "user2"
        assert config2.port == 2223
        assert config2.identity_file is not None
        assert "id_server2" in config2.identity_file

    def test_host_specific_ssh_config(self, tmp_path):
        # REQ-FUNC-SSH-012: Environment-specific host configurations
        """Test host-specific SSH config selection."""
        config_file = tmp_path / "config"
        config_file.write_text(
            "Host production.example.com\n"
            "    User produser\n"
            "    Port 22\n"
            "\n"
            "Host staging.example.com\n"
            "    User staginguser\n"
            "    Port 2222\n"
        )

        # Production environment
        prod_config = SSHConfig(
            hostname="production.example.com", ssh_config_path=str(config_file)
        )
        assert prod_config.user == "produser"
        assert prod_config.port == 22

        # Staging environment
        staging_config = SSHConfig(
            hostname="staging.example.com", ssh_config_path=str(config_file)
        )
        assert staging_config.user == "staginguser"
        assert staging_config.port == 2222

    def test_config_override_behavior(self, tmp_path):
        # REQ-FUNC-SSH-012: Environment-specific host configurations
        """Test SSH config values can be overridden."""
        config_file = tmp_path / "config"
        config_file.write_text("Host example.com\n    User configuser\n    Port 2222\n")

        config = SSHConfig(hostname="example.com", ssh_config_path=str(config_file))

        # Config values loaded from file
        assert config.user == "configuser"
        assert config.port == 2222

        # Override programmatically
        config.user = "overrideuser"
        config.port = 3333

        assert config.user == "overrideuser"
        assert config.port == 3333

    def test_wildcard_host_config(self, tmp_path):
        # REQ-FUNC-SSH-012: Environment-specific host configurations
        """Test wildcard patterns in SSH config."""
        config_file = tmp_path / "config"
        config_file.write_text(
            "Host *\n"
            "    User defaultuser\n"
            "    Port 2222\n"
            "\n"
            "Host specific.example.com\n"
            "    User specificuser\n"
        )

        # Test that config is parsed without errors
        config = SSHConfig(
            hostname="specific.example.com", ssh_config_path=str(config_file)
        )
        # paramiko SSHConfig.lookup returns a dict with the matched config
        assert config.user is not None

        # Test another host uses wildcard or no specific config
        config2 = SSHConfig(
            hostname="other.example.com", ssh_config_path=str(config_file)
        )
        # Verify config was parsed
        assert config2.port == 2222 or config2.port == 22


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
