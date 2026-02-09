"""Local consistency check command without execnet overhead."""

import sys
import traceback

import batou
from batou import ConfigurationError, SilentConfigurationError
from batou._output import TerminalBackend, output
from batou.environment import Environment
from batou.utils import Timer
from batou.utils import self_id


class LocalValidator(object):
    """Validate configuration locally without execnet."""

    def __init__(self, environment: Environment):
        self.environment = environment
        # Set minimal deployment reference for host_data filtering
        # This enables host.py to filter host_data to only first host
        # when consistency_only and check_and_predict_local are set
        from unittest.mock import MagicMock

        deployment = MagicMock()
        deployment.consistency_only = True
        # check_and_predict_local is already set on environment by check command
        # (see CheckCommand.load_environment line 99)
        # Host filtering relies on this combination

    def validate_configuration(self):
        """Validate all aspects of configuration."""
        errors = []

        # Validate component configuration
        # This happens during environment.load() and host.start()
        # We need to trigger host.start() locally without connection

        # Get first host to validate against
        if not self.environment.hosts:
            errors.append(
                ConfigurationError.from_context("No host found in environment.")
            )
            return errors

        # Validate hosts configuration by instantiating root components
        # This triggers component configuration without remote connection
        # Only connect to first host to avoid redundant configuration
        # (same logic as deploy.py consistency-only mode)
        hostnames = sorted(self.environment.hosts)[:1]
        for hostname in hostnames:
            host = self.environment.hosts[hostname]
            if host.ignore:
                continue

            try:
                # For local validation, we still need to connect
                # to create the RPC channel, but it's a local connection
                host.connect()
                # This validates all components for this host
                host.start()
            except Exception as e:
                errors.append(e)

        return errors


class CheckCommand(object):
    """Main check command implementation."""

    def __init__(self, environment, platform, timeout):
        self.environment_name = environment
        self.platform = platform
        self.timeout = timeout
        self.debug = batou.output.enable_debug
        self.errors = []
        self.start_time = None

    def execute(self) -> int:
        """Execute check command and return exit code."""
        import time

        # Setup terminal backend for output
        output.backend = TerminalBackend()
        output.line(self_id())

        self.start_time = time.time()

        try:
            self.load_environment()
            self.load_secrets()
            self.validate_configuration()
        except ConfigurationError as e:
            self.errors.append(e)
        except SilentConfigurationError:
            # Suppressed from output
            pass
        except Exception:
            # Unexpected error
            output.error("Unexpected exception")
            traceback.print_exc()
            sys.exit(1)

        self.report_results()
        return 0 if not self.errors else 1

    def load_environment(self):
        """Load environment configuration."""
        output.section("Preparing")

        output.step(
            "main",
            "Loading environment `{}`...".format(self.environment_name),
            icon="📦",
        )
        self.environment = Environment(
            self.environment_name,
            self.timeout,
            self.platform,
            check_and_predict_local=True,  # Enable local mode
        )

        self.environment.load()

        # This is located here to avoid duplicating the verification check
        # when loading the repository on the remote environment object.
        output.step("main", "Verifying repository ...", icon="🔍")
        self.environment.repository.verify()

    def load_secrets(self):
        """Load and decrypt secrets."""
        output.step("main", "Loading secrets ...", icon="🔑")
        self.environment.load_secrets()

    def validate_configuration(self):
        """Validate configuration locally."""
        output.section("LOCAL CONSISTENCY CHECK")

        validator = LocalValidator(self.environment)

        timer = Timer("check")
        with timer.step("check"):
            errors = validator.validate_configuration()
            self.errors.extend(errors)

        # Filter out SilentConfigurationErrors
        self.errors = list(
            filter(
                lambda e: not isinstance(e, SilentConfigurationError),
                self.errors,
            )
        )

        # Sort errors by sort_key
        self.errors.sort(key=lambda x: getattr(x, "sort_key", (-99,)))

    def report_results(self):
        """Report validation results."""
        if self.errors:
            # Display errors
            for error in self.errors:
                output.line("")
                if hasattr(error, "report"):
                    error.report()
                else:
                    output.error("Unexpected error:")
                    tb = traceback.TracebackException.from_exception(error)
                    for line in tb.format():
                        output.line("\t" + line.strip(), red=True)

            output.section(
                "{} ERRORS - CONFIGURATION FAILED".format(len(self.errors)),
                red=True,
            )
        else:
            output.section("Summary")
            # Show check duration
            import time

            duration = time.time() - self.start_time
            output.annotate(f"Local consistency check took {duration:.2f}s")
            output.section("LOCAL CONSISTENCY CHECK FINISHED", cyan=True)


def main(environment, platform, timeout):
    """Entry point for check command."""
    command = CheckCommand(environment, platform, timeout)
    exit_code = command.execute()
    sys.exit(exit_code)
