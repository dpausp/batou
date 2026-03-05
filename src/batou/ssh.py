"""Experimental paramiko-based SSH client for batou."""

from pathlib import Path
from typing import Any

import paramiko

from batou import ReportingException, output


class SSHError(ReportingException):
    """SSH-related errors."""

    message: str

    @classmethod
    def from_context(cls, message: str) -> "SSHError":
        self = cls()
        self.message = message
        return self

    def __str__(self) -> str:
        return self.message

    def report(self) -> None:
        output.error(f"SSH error: {self.message}")


class SSHConfig:
    """Configuration for SSH connection."""

    def __init__(self, hostname: str, ssh_config_path: str | None = None):
        self.hostname = hostname
        self.ssh_config_path = ssh_config_path
        self.user: str | None = None
        self.port: int = 22
        self.identity_file: str | None = None
        self.strict_host_key_check: bool = True

        # Load SSH config if path provided
        if ssh_config_path and Path(ssh_config_path).exists():
            self.load_from_file(ssh_config_path)

    def load_from_file(self, config_path: str) -> None:
        """Load SSH config from file."""
        try:
            ssh_config = paramiko.SSHConfig()
            with Path(config_path).open() as f:
                ssh_config.parse(f)

            # Look up hostname in config
            host_config = ssh_config.lookup(self.hostname)

            # Extract relevant settings
            if "user" in host_config:
                self.user = host_config["user"]
            if "port" in host_config:
                self.port = int(host_config["port"])
            if "identityfile" in host_config and host_config["identityfile"]:
                # identityfile is a list, take the first one
                self.identity_file = host_config["identityfile"][0]
            if (
                "stricthostkeychecking" in host_config
                and host_config["stricthostkeychecking"].lower() == "no"
            ):
                self.strict_host_key_check = False

        except (OSError, ValueError) as e:
            output.annotate(
                f"Warning: Failed to load SSH config from {config_path}: {e}",
                debug=True,
            )

    @property
    def known_hosts_file(self) -> Path:
        """Get path to known_hosts file."""
        if self.ssh_config_path:
            # Try to parse UserKnownHostsFile from ssh_config
            try:
                ssh_config = paramiko.SSHConfig()
                with Path(self.ssh_config_path).open() as f:
                    ssh_config.parse(f)
                host_config = ssh_config.lookup(self.hostname)
                if "userknownhostsfile" in host_config:
                    return Path(host_config["userknownhostsfile"]).expanduser()
            except (OSError, ValueError):
                pass

        # Default location
        return Path.home() / ".ssh" / "known_hosts"

    def __str__(self) -> str:
        return f"SSHConfig(hostname={self.hostname})"


class SSHClient:
    """Experimental SSH client using paramiko."""

    def __init__(self, config: SSHConfig):
        self.config = config
        self.client = paramiko.SSHClient()
        self._connected = False

    def ensure_known_host(self) -> bool:
        """
        Pre-flight check: ensure host key is in known_hosts.

        Returns:
            True if host key was known/added, False otherwise
        """
        try:
            # Load known hosts
            self.client.load_system_host_keys()

            # Set policy to auto-add missing keys
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Try to connect to trigger host key addition
            self.client.connect(
                self.config.hostname,
                port=self.config.port,
                username=self.config.user,
                key_filename=self.config.identity_file,
                timeout=5,
                look_for_keys=True,
            )

            # Close connection
            self.client.close()

            output.annotate(f"Host key verified for {self.config.hostname}", debug=True)
            return True

        except paramiko.SSHException as e:
            output.error(f"Failed to verify host key for {self.config.hostname}: {e}")
            return False
        except Exception as e:
            output.error(
                f"Unexpected error checking host key for {self.config.hostname}: {e}"
            )
            return False

    def run(self, command: str, check: bool = True) -> dict[str, Any]:
        """
        Execute remote command via SSH.

        Args:
            command: Shell command to execute
            check: If True, raise exception on non-zero return code

        Returns:
            Dictionary with stdout, stderr, returncode and success (bool)
        """
        try:
            # Ensure we have a connection
            if not self._connected:
                self.client.load_system_host_keys()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self.client.connect(
                    self.config.hostname,
                    port=self.config.port,
                    username=self.config.user,
                    key_filename=self.config.identity_file,
                )
                self._connected = True

            output.annotate(f"Executing: {command}", debug=True)

            # Execute command
            stdin, stdout, stderr = self.client.exec_command(command)

            # Wait for completion
            exit_code = stdout.channel.recv_exit_status()

            result = {
                "stdout": stdout.read().decode("utf-8", errors="replace"),
                "stderr": stderr.read().decode("utf-8", errors="replace"),
                "returncode": exit_code,
                "success": exit_code == 0,
            }

            if check and exit_code != 0:
                raise SSHError.from_context(
                    f"Command failed with exit code {exit_code}: {command}\n"
                    f"stderr: {result['stderr']}"
                )

            output.annotate(f"Command completed (rc={exit_code})", debug=True)
            return result

        except paramiko.SSHException as e:
            output.error(f"SSH error executing command: {e}")
            raise SSHError.from_context(f"SSH error: {e}")
        except SSHError:
            # Re-raise our own exceptions
            raise
        except Exception as e:
            output.error(f"Unexpected error executing command: {e}")
            raise SSHError.from_context(f"Unexpected error: {e}")

    def close(self) -> None:
        """Close the SSH connection."""
        if self._connected:
            self.client.close()
            self._connected = False

    def __enter__(self) -> "SSHClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - close connection."""
        self.close()
