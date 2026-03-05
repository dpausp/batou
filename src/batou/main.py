import argparse
import os
import os.path
import sys
import textwrap

from rich.console import Console

import batou
import batou.debug.cli
import batou.deploy
import batou.migrate
import batou.secrets.edit
import batou.secrets.encryption
import batou.secrets.manage
from batou._output import TerminalBackend, output
from batou.utils import find_basedir
from batou.version import format_version, get_version, is_dev_version


def ssh_main(
    environment: str, host: str, command: str, check_hostkey: bool = True
) -> None:
    """Execute SSH command on remote host (experimental)."""
    from pathlib import Path

    from batou.environment import Environment
    from batou.ssh import SSHClient, SSHConfig, SSHError

    try:
        # Load environment
        env = Environment(environment)
        env.load()

        # Get target host
        target_host = env.get_host(host)

        # Build SSH config
        ssh_config_path = None
        env_ssh_config = Path(f"ssh_config_{environment}")
        if env_ssh_config.exists():
            ssh_config_path = str(env_ssh_config)

        ssh_config = SSHConfig(
            hostname=target_host.fqdn, ssh_config_path=ssh_config_path
        )

        # Create client
        client = SSHClient(ssh_config)

        # Check host key if requested
        if check_hostkey:
            if not client.ensure_known_host():
                output.error(f"Failed to verify host key for {target_host.fqdn}")
                sys.exit(1)

        # Execute command
        result = client.run(command)

        # Show output
        if result["stdout"]:
            output.line(result["stdout"])
        if result["stderr"]:
            output.line(result["stderr"], red=True)

        output.tabular("Exit code", str(result["returncode"]))

        if result["returncode"] != 0:
            sys.exit(result["returncode"])

        # Close connection
        client.close()

    except SSHError as e:
        output.error(f"SSH error: {e}")
        sys.exit(1)
    except Exception as e:
        output.error(f"Unexpected error: {e}")
        sys.exit(1)


# Backwards compatibility aliases
_get_version = get_version
_format_version = format_version
_is_dev_version = is_dev_version


def print_version() -> None:
    """Print formatted version with git rev and timestamp."""
    console = Console()
    formatted = _format_version(color=True)
    console.print(formatted, no_wrap=True)
    sys.exit(0)


def main(args: list | None = None) -> None:
    os.chdir(find_basedir())
    version = _format_version(color=False)
    parser = argparse.ArgumentParser(
        description=(
            f"batou v{version}: multi-(host|component|environment|version|platform) deployment"
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(func=parser.print_usage)

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode.")

    subparsers = parser.add_subparsers()

    # Deploy
    p = subparsers.add_parser("deploy", help="Deploy an environment.")
    p.set_defaults(func=p.print_usage)

    p.add_argument(
        "-p",
        "--platform",
        default=None,
        help="Alternative platform to choose. Empty for no platform.",
    )
    p.add_argument(
        "-t",
        "--timeout",
        default=None,
        help="Override the environment's timeout setting",
    )
    p.add_argument(
        "-D",
        "--dirty",
        action="store_true",
        help="Allow deploying with dirty working copy or outgoing changes.",
    )
    p.add_argument(
        "-c",
        "--consistency-only",
        action="store_true",
        help="Only perform a deployment model and environment "
        "consistency check. Only connects to a single host. "
        "Does not touch anything.",
    )
    p.add_argument(
        "-P",
        "--predict-only",
        action="store_true",
        help="Only predict what updates would happen. Do not change anything.",
    )
    p.add_argument(
        "-L",
        "--local",
        action="store_true",
        dest="check_and_predict_local",
        help="When running in consistency-only or predict-only mode, "
        "do not connect to the remote host, but check and predict "
        "using the local host's state.",
    )
    p.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Defines number of jobs running parallel to deploy. "
        "The default results in a serial deployment "
        "of components. Will override the environment settings "
        "for operational flexibility.",
    )
    p.add_argument(
        "--provision-rebuild",
        action="store_true",
        help="Rebuild provisioned resources from scratch. "
        "DANGER: this is potentially destructive.",
    )
    p.add_argument(
        "environment",
        help="Environment to deploy.",
        type=lambda x: x.replace(".cfg", ""),
    )
    p.set_defaults(func=batou.deploy.main)

    # DEBUG
    p = subparsers.add_parser("debug", help="Display all available debug settings.")
    p.set_defaults(func=batou.debug.cli.main)

    # VERSION
    p = subparsers.add_parser("version", help="Print the batou version.")
    p.set_defaults(func=print_version)

    # SECRETS
    secrets = subparsers.add_parser(
        "secrets",
        help=textwrap.dedent(
            """
            Manage encrypted secret files. Relies on age (or GPG) being installed and
            configured correctly. """
        ),
    )
    secrets.set_defaults(func=secrets.print_usage)

    sp = secrets.add_subparsers()

    p = sp.add_parser(
        "edit",
        help=textwrap.dedent(
            """
            Encrypted secrets file editor utility. Decrypts file,
            invokes the editor, and encrypts the file again. If called with a
            non-existent file name, a new encrypted file is created.
        """
        ),
    )
    p.set_defaults(func=p.print_usage)

    p.add_argument(
        "--editor",
        "-e",
        metavar="EDITOR",
        default=os.environ.get("EDITOR", "vi"),
        help="Invoke EDITOR to edit (default: $EDITOR or vi)",
    )
    p.add_argument("environment", help="Environment to edit secrets for.", type=str)
    p.add_argument(
        "edit_file",
        nargs="?",
        help="Sub-file to edit. (i.e. secrets/{environment}-{subfile}",
    )
    p.set_defaults(func=batou.secrets.edit.main)

    p = sp.add_parser(
        "summary", help="Give a summary of secret files and who has access."
    )
    p.set_defaults(func=batou.secrets.manage.summary)

    p = sp.add_parser("add", help="Add a user's key to one or more secret files.")
    p.set_defaults(func=p.print_usage)
    p.add_argument("keyid", help="The user's key ID or email address")
    p.add_argument(
        "--environments",
        default="",
        help="The environments to update. Update all if not specified.",
    )
    p.set_defaults(func=batou.secrets.manage.add_user)

    p = sp.add_parser(
        "remove", help="Remove a user's key from one or more secret files."
    )
    p.set_defaults(func=p.print_usage)
    p.add_argument("keyid", help="The user's key ID or email address")
    p.add_argument(
        "--environments",
        default="",
        help="The environments to update. Update all if not specified.",
    )
    p.set_defaults(func=batou.secrets.manage.remove_user)

    p = sp.add_parser(
        "reencrypt",
        help="Re-encrypt all secret files with the current members.",
    )
    p.set_defaults(func=p.print_usage)
    p.add_argument(
        "--environments",
        default="",
        help="The environments to update. Update all if not specified.",
    )
    p.set_defaults(func=batou.secrets.manage.reencrypt)

    p = sp.add_parser(
        "decrypttostdout",
        help="Decrypt a secret file to stdout, useful for git diff.",
    )
    p.set_defaults(func=p.print_usage)
    p.add_argument(
        "file",
        help="The secret file to decrypt, should be contained in an environment.",
    )
    p.set_defaults(func=batou.secrets.manage.decrypt_to_stdout)

    # migrate
    migrate = subparsers.add_parser(
        "migrate",
        help=textwrap.dedent(
            """
            Migrate the configuration to be compatible with the batou version
            used. Requires to commit the changes afterwards. Might show some
            additional upgrade steps which cannot be performed automatically.
        """
        ),
    )
    migrate.set_defaults(func=migrate.print_usage)
    migrate.add_argument(
        "--bootstrap",
        default=False,
        action="store_true",
        help="Used internally when bootstrapping a new batou project.",
    )
    migrate.set_defaults(func=batou.migrate.main)

    # SSH (experimental)
    p = subparsers.add_parser(
        "ssh",
        help="Execute SSH command on remote host (experimental).",
    )
    p.set_defaults(func=p.print_usage)
    p.add_argument("environment", help="Environment name")
    p.add_argument("host", help="Host name")
    p.add_argument("command", help="Command to execute")
    p.add_argument(
        "--check-hostkey",
        action="store_true",
        default=True,
        help="Check host key before connection",
    )
    p.set_defaults(func=ssh_main)

    args: argparse.Namespace = parser.parse_args(args)

    # Consume global arguments
    batou.output.enable_debug = args.debug
    batou.secrets.encryption.debug = args.debug
    if hasattr(batou.secrets.manage, "debug"):
        batou.secrets.manage.debug = args.debug

    # Pass over to function
    if args.func.__name__ == "print_usage":
        args.func()
        sys.exit(1)

    if args.func not in (batou.migrate.main, print_version):
        output.backend = TerminalBackend()
        batou.migrate.assert_up_to_date()

    func_args = dict(args._get_kwargs())
    del func_args["func"]
    del func_args["debug"]
    try:
        return args.func(**func_args)
    except batou.FileLockedError as e:
        # Nicer error reporting for non-deployment commands.
        print(e)
