"""File descriptor tracking for leak detection."""

import builtins
import datetime
import os
import socket
import traceback
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict

from batou import output

try:
    from typing import NotRequired
except ImportError:
    from typing_extensions import NotRequired


class FDTrackingLogEntry(NamedTuple):
    """A single FD tracking log entry."""

    time: str
    fd_count: int  # Renamed to avoid conflict with tuple.count() method
    path: str
    mode: str
    action: str


@dataclass(slots=True)
class FDRecord:
    """Record for tracking file open operations."""

    open_count: int = 0
    modes: dict[str, int] = field(default_factory=dict)
    stack_traces: list = field(default_factory=list)


class FileDescriptorState(NamedTuple):
    """State of an open file for leak detection."""

    path: str
    mode: str
    open_time: str


class FDTrackingStats(TypedDict):
    """File descriptor tracking statistics snapshot."""

    total_opens: int
    total_closes: int
    leaked_fds: list[tuple[int, str, str, str]]
    logs: list[FDTrackingLogEntry]


# Type for fd_records dictionary
FDRecordDict = dict[str, FDRecord]  # path -> FDRecord


class RemoteFDTrackingStats(TypedDict):
    """File descriptor tracking statistics from remote side."""

    total_opens: int
    total_closes: int
    leaked_fds: list[tuple[int, str, str, str]]
    logs: list[FDTrackingLogEntry]
    fd_records: NotRequired[FDRecordDict]


class FileDescriptorTracker:
    """File descriptor tracking for leak detection."""

    from batou.debug.settings import DebugSettings

    def __init__(self, environment_name: str, debug_settings: DebugSettings):
        self.enabled = debug_settings.track_fds > 0
        self.verbose = debug_settings.track_fds > 1
        self.debug_settings = debug_settings
        self.environment_name = environment_name

        self.fd_records = {}
        self.original_open = builtins.open
        self.total_opens = 0
        self.total_closes = 0
        self.remote_opens = {}  # Track FD opens per remote host
        self._open_fds: dict[int, FileDescriptorState] = {}  # fd -> FileDescriptorState
        self._fd_tracking_logs: list[FDTrackingLogEntry] = []  # Structured logs

        # Install local FD tracking hook during initialization
        self._install_local_hook()

    def _install_local_hook(self):
        if not self.enabled:
            return

        self.original_open = builtins.open

        def open_hook(path, mode="r", *args, **kwargs):
            import traceback

            # Check if call is from batou code to avoid tracking
            # internal Python opens (e.g., ast.literal_eval)
            full_stack = traceback.extract_stack()
            is_batou_call = False

            # Only check first half of stack (avoid going too deep)
            for frame in full_stack[: len(full_stack) // 2]:
                # Track if caller is from batou code (not stdlib)
                if "/batou/" in frame.filename:
                    is_batou_call = True
                    break

            # Only track batou opens, not internal Python opens
            if not is_batou_call:
                return self.original_open(path, mode, *args, **kwargs)

            fd = self.original_open(path, mode, *args, **kwargs)
            self._track_open(fd.fileno(), path, mode)

            # Wrap close() to track FD closes
            # Use weakref to avoid reference cycle that prevents GC
            import weakref

            original_close = fd.close
            tracker_ref = weakref.ref(self)
            fd_num = fd.fileno()

            def close_hook(
                tracker_ref=tracker_ref, original_close=original_close, fd_num=fd_num
            ):
                tracker = tracker_ref()
                if tracker is not None:
                    tracker._track_close(fd_num)
                return original_close()

            fd.close = close_hook
            return fd

        builtins.open = open_hook  # type: ignore[assignment]

    def _track_open(self, fd, path, mode="r"):
        if not self.enabled:
            return

        self.total_opens += 1

        if path not in self.fd_records:
            self.fd_records[path] = FDRecord()

        self.fd_records[path].open_count += 1

        # Track modes
        if mode not in self.fd_records[path].modes:
            self.fd_records[path].modes[mode] = 0
        self.fd_records[path].modes[mode] += 1

        if self.verbose:
            import traceback

            # Collect full stack trace and filter out tracking code
            full_stack = traceback.extract_stack()
            # Filter out frames from tracking code and convert to serializable format
            filtered_stack = []
            for frame in full_stack:
                # Skip tracking code frames
                if "batou/utils.py" in frame.filename and (
                    "open_hook" in frame.name or "_track_open" in frame.name
                ):
                    continue
                # Convert FrameSummary to tuple for consistency with remote
                filtered_stack.append((frame.filename, frame.lineno, frame.name))
                # Stop after we have enough frames (excluding tracking code)
                if len(filtered_stack) >= 10:
                    break
            if filtered_stack:
                self.fd_records[path].stack_traces.append(filtered_stack)

        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Track in _open_fds for leak detection (like remote)
        self._open_fds[fd] = FileDescriptorState(path, mode, now)

        # Structured logging (like remote)
        self._fd_tracking_logs.append(
            FDTrackingLogEntry(now, self.total_opens, path, mode, "open")
        )

    def _track_close(self, fd):
        if not self.enabled:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if fd in self._open_fds:
            path, mode, open_time = self._open_fds.pop(fd)
            self.total_closes += 1
            # Structured logging (like remote)
            self._fd_tracking_logs.append(
                FDTrackingLogEntry(now, self.total_opens, path, mode, "close")
            )
        else:
            # Low-level fd (like from mkstemp) - log it
            self.total_closes += 1
            self._fd_tracking_logs.append(
                FDTrackingLogEntry(
                    now,
                    self.total_opens,
                    f"fd:{fd} (low-level)",
                    "low-level",
                    "close",
                )
            )

    def report(self, location="local", env_name=None):
        if not self.enabled:
            return

        pid = os.getpid()
        host = socket.gethostname()
        timestamp = datetime.datetime.now().isoformat()

        # For local, use current directory name as deployment name
        if location == "local":
            deployment_name = os.path.basename(os.getcwd())
            filename = os.path.join(
                self.debug_settings.fd_output_dir,
                f"batou_fd_track_{env_name}_{deployment_name}_{pid}.txt",
            )
        else:
            filename = os.path.join(
                self.debug_settings.fd_output_dir,
                f"batou_fd_track_remote_{pid}.txt",
            )

        with open(filename, "w") as f:
            f.write("File Descriptor Tracking Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Process ID: {pid}\n")
            f.write(f"Host: {host}\n")
            f.write(f"Location: {location}\n")
            f.write(f"Deployment: {env_name}\n")
            f.write("\n")

            f.write("Summary:\n")
            f.write(f"Total Open Events: {self.total_opens}\n")
            f.write("\n")

            # Show breakdown by host if available
            if self.remote_opens:
                f.write("Opens by Host:\n")
                f.write("-" * 80 + "\n")
                f.write(
                    f"  Local: {self.total_opens - sum(self.remote_opens.values())} opens\n"
                )
                for host_name, opens in sorted(self.remote_opens.items()):
                    f.write(f"  {host_name}: {opens} opens\n")
                f.write("\n")

            f.write("=" * 80 + "\n")

            # Sort items for use in stack traces and file listing
            items = sorted(
                self.fd_records.items(),
                key=lambda x: x[1].open_count,
                reverse=True,
            )

            if self.verbose:
                f.write("\n")
                f.write("Stack Traces (grouped by trace):\n")
                f.write("-" * 80 + "\n")

                # Collect all traces from all files and group by stack trace
                traces_by_key = {}  # stack_key -> [(path, count), ...]

                for path, record in items:
                    if record.stack_traces:
                        for stack in record.stack_traces:
                            # Stack may be tuples (from remote) or FrameSummary objects (from local)
                            # Normalize to tuple format
                            if stack and isinstance(stack[0], tuple):
                                # Already tuples (from remote)
                                stack_key = tuple(stack)
                            else:
                                # FrameSummary objects (from local)
                                stack_key = tuple(
                                    (frame.filename, frame.lineno, frame.name)
                                    for frame in stack
                                )
                            if stack_key not in traces_by_key:
                                traces_by_key[stack_key] = []
                            traces_by_key[stack_key].append((path, record.open_count))

                # Sort traces by total open count (descending)
                sorted_traces = sorted(
                    traces_by_key.items(),
                    key=lambda x: sum(count for path, count in x[1]),
                    reverse=True,
                )

                # Show top 20 traces
                for i, (stack_key, files) in enumerate(sorted_traces[:20], 1):
                    total_opens = sum(count for path, count in files)
                    f.write(
                        f"\nStack Trace #{i} (called {total_opens} time{'s' if total_opens > 1 else ''}):\n"
                    )
                    # Show stack trace
                    for frame in stack_key:
                        f.write(
                            f'  File "{frame[0]}", line {frame[1]}, in {frame[2]}\n'
                        )
                    # Show files with this trace
                    f.write(
                        f"\n  Files with this trace ({len(files)} file{'s' if len(files) > 1 else ''}, top 10 shown):\n"
                    )
                    for path, count in files[:10]:
                        f.write(
                            f"    - {path} ({count} open{'s' if count > 1 else ''})\n"
                        )
                    if len(files) > 10:
                        f.write(f"    ... and {len(files) - 10} more files\n")

            # All files listing at the end
            f.write("\n")
            f.write("All Files:\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total unique files: {len(self.fd_records)}\n")
            f.write(
                f"Total open events: {sum(r['open_count'] for r in self.fd_records.values())}\n"
            )
            f.write("\n")

            # Show top 20 files with full details
            f.write("Top 20 Files:\n")
            for path, record in items[:20]:
                open_count = record.open_count
                bar_length = min(open_count, 50)
                bar = "*" * bar_length
                f.write(f"  {open_count:4d}x {path}\n")
                f.write(f"       |{bar}\n")

            # Show remaining files compactly
            if len(items) > 20:
                f.write(f"\nRemaining {len(items) - 20} files:\n")
                for path, record in items[20:]:
                    open_count = record.open_count
                    f.write(f"  {open_count:4d}x {path}\n")

            # Leak detection at end of report (like remote)
            if len(self._open_fds) > 200:
                f.write("\n")
                f.write("FD LEAK WARNING:\n")
                f.write("-" * 80 + "\n")
                f.write(f"  {len(self._open_fds)} FDs still open (threshold: 200)\n")
                f.write("\n")
                f.write("  Leaked FD details (first 10):\n")
                for fd, (path, mode, open_time) in list(self._open_fds.items())[:10]:
                    f.write(f"    FD {fd}: {path} ({mode}) since {open_time}\n")
                if len(self._open_fds) > 10:
                    f.write(f"    ... and {len(self._open_fds) - 10} more\n")
                f.write("\n")

    def get_fd_tracking_stats(self) -> FDTrackingStats:
        """Get FD tracking statistics (same structure as remote)."""
        return {
            "total_opens": self.total_opens,
            "total_closes": self.total_closes,
            "leaked_fds": [
                (fd, path, mode, open_time)
                for fd, (path, mode, open_time) in self._open_fds.items()
            ],
            "logs": self._fd_tracking_logs,
        }

    @classmethod
    def cleanup(cls):
        """Clean up the FD tracker instance and reset builtins.open.

        This class method delegates to the factory function for backward compatibility.
        """
        cleanup_fd_tracker()

    def generate_reports(self, hosts):
        if not self.enabled:
            return

        # First, collect all remote stats
        for host in hosts:
            if host.gateway:
                remote_stats = host.rpc.get_fd_tracking_stats()
                if remote_stats and remote_stats.get("total_opens", 0) > 0:
                    output.annotate(
                        f"Remote FD tracking for {host.name}: "
                        f"{remote_stats.get('total_opens', 0)} opens",
                    )
                    self.total_opens += remote_stats.get("total_opens", 0)
                    # Track opens per host
                    self.remote_opens[host.name] = remote_stats.get("total_opens", 0)
                    # Merge remote fd_records into local fd_records
                    if "fd_records" in remote_stats:
                        for path, record in remote_stats["fd_records"].items():
                            # Prefix with hostname to distinguish between hosts
                            host_path = f"[{host.name}] {path}"
                            if host_path not in self.fd_records:
                                self.fd_records[host_path] = FDRecord()
                            self.fd_records[host_path].open_count += record[
                                "open_count"
                            ]
                            # Merge modes
                            for mode, count in record.get("modes", {}).items():
                                if mode not in self.fd_records[host_path].modes:
                                    self.fd_records[host_path].modes[mode] = 0
                                self.fd_records[host_path].modes[mode] += count
                            # Merge stack traces
                            for stack in record.get("stack_traces", []):
                                self.fd_records[host_path].stack_traces.append(stack)
                    # Show verbose logs if available
                    if "logs" in remote_stats and self.verbose:
                        output.line(f"  FD opens for {host.name}:")
                        for now, count, path, _mode, _action in remote_stats["logs"][
                            :10
                        ]:
                            output.line(f"    [{now}] FD #{count} Opening: {path}")
                        if len(remote_stats["logs"]) > 10:
                            output.line(
                                f"    ... and {len(remote_stats['logs']) - 10} more"
                            )

        # Now generate the /tmp file with all stats (local + remote)
        self.report("local", self.environment_name)

    def show_summary(self):
        if not self.enabled:
            return

        output.line("")
        output.line("FD Tracking Summary:")
        output.line("-" * 40)

        # Local FD tracking stats
        local_stats = self.get_fd_tracking_stats()
        output.annotate(
            f"Local FD tracking: "
            f"{local_stats.get('total_opens', 0)} opens, "
            f"{local_stats.get('total_closes', 0)} closes, "
            f"{len(local_stats['leaked_fds'])} still open",
        )

        # Show leaked FDs if any (local)
        if len(local_stats["leaked_fds"]) > 200:
            output.annotate(
                f"Local FD leak warning: "
                f"{len(local_stats['leaked_fds'])} FDs still open",
                red=True,
            )
            for fd, path, mode, open_time in local_stats["leaked_fds"][:5]:
                output.line(f"  FD {fd}: {path} ({mode}) since {open_time}")
            if len(local_stats["leaked_fds"]) > 5:
                output.line(f"  ... and {len(local_stats['leaked_fds']) - 5} more")

        if self.remote_opens:
            local_opens = self.total_opens - sum(self.remote_opens.values())
            output.line(f"  Local: {local_opens} opens")
            for host_name, opens in sorted(self.remote_opens.items()):
                output.line(f"  {host_name}: {opens} opens")

        # Show where output files are written
        output.line("")
        output.line("FD Tracking Files:")
        output.line("-" * 40)
        import os

        pid = os.getpid()
        deployment_name = os.path.basename(os.getcwd())
        env_name = self.environment_name
        output.line(
            f"  {os.path.join(self.debug_settings.fd_output_dir, f'batou_fd_track_{env_name}_{deployment_name}_{pid}.txt')}"
        )
        if self.verbose:
            output.line("  (with stack traces)")

        # Show trend graph
        output.line("")
        output.line("Top Files (by open count):")
        items = sorted(
            self.fd_records.items(),
            key=lambda x: x[1].open_count,
            reverse=True,
        )
        for path, record in items[:10]:
            open_count = record.open_count
            if open_count <= 1:
                continue
            bar_length = min(open_count, 20)
            bar = "█" * bar_length
            # Format modes for display
            modes_str = ", ".join(
                [f"{mode}:{count}" for mode, count in sorted(record.modes.items())]
            )
            # Shorten path for display
            path_str = str(path)
            if len(path_str) > 60:
                display_path = "..." + path_str[-57:]
            else:
                display_path = path_str
            output.line(f"  {open_count:4d}x {display_path}")
            output.line(f"       |{bar} [{modes_str}]")


class RemoteFDTracker:
    """Remote FD tracking for use in remote_core.py.

    Simple FD tracking without batou code filtering - tracks ALL opens.
    Uses module-level state for RPC serialization compatibility.
    """

    def __init__(self, track_fds_level: int):
        """Initialize remote FD tracking with verbosity level.

        Args:
            track_fds_level: 0=disabled, 1=enabled, 2=verbose
        """
        self.enabled = track_fds_level > 0
        self.verbose = track_fds_level > 1

        # Instance-level tracking state (like FileDescriptorTracker)
        self.total_opens = 0
        self.total_closes = 0
        self._open_fds: dict[int, FileDescriptorState] = {}
        self._fd_tracking_logs: list[FDTrackingLogEntry] = []
        self._fd_records: FDRecordDict = {}

    def _track_fd_open(self, fd: int, path: str, mode: str = "r"):
        """Track file descriptor opens."""
        if not self.enabled:
            return

        self.total_opens += 1
        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        self._open_fds[fd] = FileDescriptorState(path, mode, now)
        self._fd_tracking_logs.append(
            FDTrackingLogEntry(now, self.total_opens, path, mode, "open")
        )

        # Track in fd_records for detailed analysis
        if path not in self._fd_records:
            self._fd_records[path] = FDRecord()
        self._fd_records[path].open_count += 1
        if mode not in self._fd_records[path].modes:
            self._fd_records[path].modes[mode] = 0
        self._fd_records[path].modes[mode] += 1

        # Collect stack traces if verbose mode is enabled
        if self.verbose:
            full_stack = traceback.extract_stack()
            filtered_stack = []
            for frame in full_stack:
                # Skip tracking code frames
                if "batou/remote_core.py" in frame.filename and (
                    "tracked_open" in frame.name or "_track_fd_open" in frame.name
                ):
                    continue
                # Convert FrameSummary to tuple for serialization
                filtered_stack.append((frame.filename, frame.lineno, frame.name))
                if len(filtered_stack) >= 10:
                    break
            if filtered_stack:
                self._fd_records[path].stack_traces.append(filtered_stack)

        # Warn if we have too many FDs open
        fd_warning_threshold = 200
        if len(self._open_fds) > fd_warning_threshold:
            self._fd_tracking_logs.append(
                FDTrackingLogEntry(
                    now,
                    self.total_opens,
                    f"WARNING: {len(self._open_fds)} FDs open (threshold: {fd_warning_threshold})",
                    "warning",
                    "leak",
                )
            )

    def _track_fd_close(self, fd: int):
        """Track file descriptor closes."""
        if not self.enabled:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if fd in self._open_fds:
            path, mode, open_time = self._open_fds.pop(fd)
            self.total_closes += 1
            self._fd_tracking_logs.append(
                FDTrackingLogEntry(now, self.total_opens, path, mode, "close")
            )
        else:
            # Low-level fd (like from mkstemp) - log it
            self.total_closes += 1
            self._fd_tracking_logs.append(
                FDTrackingLogEntry(
                    now,
                    self.total_opens,
                    f"fd:{fd} (low-level)",
                    "low-level",
                    "close",
                )
            )

    def install_hook(self):
        """Install builtins.open hook for FD tracking."""
        if not self.enabled:
            return

        _original_open = builtins.open

        def tracked_open(path, mode="r", *args, **kwargs):
            fd = _original_open(path, mode, *args, **kwargs)
            self._track_fd_open(fd.fileno(), path, mode)

            # Wrap close() to track it
            original_close = fd.close

            def tracked_close():
                self._track_fd_close(fd.fileno())
                return original_close()

            fd.close = tracked_close
            return fd

        builtins.open = tracked_open  # type: ignore[assignment]

        # Track os.close() for low-level FD operations like mkstemp()
        _original_os_close = os.close

        def tracked_os_close(fd):
            self._track_fd_close(fd)
            return _original_os_close(fd)

        os.close = tracked_os_close  # type: ignore[assignment]

    def get_stats(self) -> RemoteFDTrackingStats:
        """Get FD tracking statistics from remote side."""
        stats: RemoteFDTrackingStats = {
            "total_opens": self.total_opens,
            "total_closes": self.total_closes,
            "leaked_fds": [
                (fd, path, mode, open_time)
                for fd, (path, mode, open_time) in self._open_fds.items()
            ],
            "logs": self._fd_tracking_logs,
        }
        if self._fd_records:
            stats["fd_records"] = self._fd_records
        return stats


# Module-level factory functions (replacing singletons)

_fd_tracker_instance: FileDescriptorTracker | None = None
_remote_fd_tracker_instance: RemoteFDTracker | None = None


def get_fd_tracker(
    environment_name: str | None = None, debug_settings=None
) -> FileDescriptorTracker:
    """Get or create the FD tracker instance.

    This factory function replaces the singleton pattern.
    Tests should call cleanup_fd_tracker() to reset state.
    """
    global _fd_tracker_instance
    if _fd_tracker_instance is None:
        from batou.debug.settings import get_debug_settings

        if debug_settings is None:
            debug_settings = get_debug_settings()
        if environment_name is None:
            environment_name = "default"
        _fd_tracker_instance = FileDescriptorTracker(environment_name, debug_settings)
    return _fd_tracker_instance


def cleanup_fd_tracker():
    """Clean up the FD tracker instance and reset builtins.open.

    This replaces FileDescriptorTracker.cleanup() class method.
    """
    global _fd_tracker_instance
    if _fd_tracker_instance is not None:
        builtins.open = _fd_tracker_instance.original_open
        _fd_tracker_instance = None


def get_remote_fd_tracker(track_fds_level: int = 0) -> RemoteFDTracker:
    """Get or create the remote FD tracker instance.

    This factory function is used by remote_core.py.
    """
    global _remote_fd_tracker_instance
    if _remote_fd_tracker_instance is None:
        _remote_fd_tracker_instance = RemoteFDTracker(track_fds_level)
    return _remote_fd_tracker_instance


def init_remote_fd_tracking(track_fds_level: int) -> RemoteFDTracker:
    """Initialize remote FD tracking with verbosity level.

    This is the main entry point for remote_core.py.
    Creates a fresh tracker and installs the hook.
    """
    global _remote_fd_tracker_instance
    _remote_fd_tracker_instance = RemoteFDTracker(track_fds_level)
    _remote_fd_tracker_instance.install_hook()
    return _remote_fd_tracker_instance


def get_remote_fd_tracking_stats() -> RemoteFDTrackingStats:
    """RPC function to get FD tracking stats from remote side.

    This is called by remote_core.py via RPC.
    """
    global _remote_fd_tracker_instance
    if _remote_fd_tracker_instance is None:
        # Return empty stats if tracking was never initialized
        return {
            "total_opens": 0,
            "total_closes": 0,
            "leaked_fds": [],
            "logs": [],
        }
    return _remote_fd_tracker_instance.get_stats()
