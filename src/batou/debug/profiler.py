"""Profiling support for remote host deployment performance tracking."""

from batou import output


class Profiler(object):
    """Track and report profiling results for remote hosts.

    Following the same pattern as FileDescriptorTracker, this class
    collects profiling data from remote hosts and generates reports.
    """

    def __init__(self, debug_settings):
        """Initialize profiler with debug settings.

        Args:
            debug_settings: DebugSettings instance with profile flag
        """
        self.enabled = debug_settings.profile

    def generate_reports(self, hosts):
        """Collect and display profiling results from remote hosts.

        Args:
            hosts: Iterable of Host objects to collect profiling from
        """
        if not self.enabled:
            return

        for host in hosts:
            if getattr(host, "gateway", None):
                profile = host.rpc.get_profiling_results()
                if profile:
                    output.annotate(
                        f"Profiling for {profile['host']}: {profile['profile_path']}"
                    )
