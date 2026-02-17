"""File descriptor tracking for leak detection."""

import builtins
import datetime
import os
import socket

from batou import output


class FileDescriptorTracker:
    """File descriptor tracking for leak detection."""

    from batou.debug.settings import DebugSettings

    _instance = None

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
        self._open_fds = {}  # fd -> (path, mode, open_time) for leak detection
        self._fd_tracking_logs = []  # Structured logging tuples

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
            self.fd_records[path] = {"open_count": 0, "modes": {}, "stack_traces": []}

        self.fd_records[path]["open_count"] += 1

        # Track modes
        if mode not in self.fd_records[path]["modes"]:
            self.fd_records[path]["modes"][mode] = 0
        self.fd_records[path]["modes"][mode] += 1

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
                self.fd_records[path]["stack_traces"].append(filtered_stack)

        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Track in _open_fds for leak detection (like remote)
        self._open_fds[fd] = (path, mode, now)

        # Structured logging (like remote)
        self._fd_tracking_logs.append((now, self.total_opens, path, mode, "open"))

    def _track_close(self, fd):
        if not self.enabled:
            return

        now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

        if fd in self._open_fds:
            path, mode, open_time = self._open_fds.pop(fd)
            self.total_closes += 1
            # Structured logging (like remote)
            self._fd_tracking_logs.append((now, self.total_opens, path, mode, "close"))
        else:
            # Low-level fd (like from mkstemp) - log it
            self.total_closes += 1
            self._fd_tracking_logs.append(
                (
                    now,
                    self.total_opens,
                    f"fd:{fd} (low-level)",
                    "low-level",
                    "close",
                )
            )

    def install_remote_hook(self, gateway):
        if not self.enabled:
            return

        gateway.remote_exec(
            """
import builtins
import os
import sys
import traceback
import datetime
import batou._settings as batou_settings

_fd_records = {}
_total_opens = 0

def track_open(fd, path, mode="r"):
    global _total_opens
    _total_opens += 1
    if fd not in _fd_records:
        _fd_records[fd] = {"open_count": 0, "modes": {}, "stack_traces": []}
    _fd_records[fd]["open_count"] += 1
    if mode not in _fd_records[fd]["modes"]:
        _fd_records[fd]["modes"][mode] = 0
    _fd_records[fd]["modes"][mode] += 1
    if batou_settings.get_debug_settings().track_fds == 2:
        stack = traceback.extract_stack()[-3:]
        _fd_records[fd]["stack_traces"].append(stack)
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print("[{}] FD #{} Opening: {}".format(now, _total_opens, path))
    print("[{}] FD #{} Total open: {}".format(now, _total_opens, _total_opens))

def get_statistics():
    return {
        "fd_records": _fd_records,
        "total_opens": _total_opens,
    }

_original_open = builtins.open
def tracked_open(path, mode="r", *args, **kwargs):
    fd = _original_open(path, mode, *args, **kwargs)
    track_open(fd.fileno(), path, mode)
    return fd

builtins.open = tracked_open
"""
        )

    def get_remote_logs(self, gateway):
        if not self.enabled:
            return None

        return gateway.remote_exec(
            """
import builtins
import os
import sys
import traceback
import datetime
import batou._settings as batou_settings

_fd_records = {}
_total_opens = 0

def track_open(fd, path, mode="r"):
    global _total_opens
    _total_opens += 1
    if fd not in _fd_records:
        _fd_records[fd] = {"open_count": 0, "modes": {}, "stack_traces": []}
    _fd_records[fd]["open_count"] += 1
    if mode not in _fd_records[fd]["modes"]:
        _fd_records[fd]["modes"][mode] = 0
    _fd_records[fd]["modes"][mode] += 1
    if batou_settings.get_debug_settings().track_fds == 2:
        stack = traceback.extract_stack()[-3:]
        _fd_records[fd]["stack_traces"].append(stack)
    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    print("[{}] FD #{} Opening: {}".format(now, _total_opens, path))
    print("[{}] FD #{} Total open: {}".format(now, _total_opens, _total_opens))

def get_statistics():
    return {
        "fd_records": _fd_records,
        "total_opens": _total_opens,
    }

_original_open = builtins.open
def tracked_open(path, mode="r", *args, **kwargs):
    fd = _original_open(path, mode, *args, **kwargs)
    track_open(fd.fileno(), path, mode)
    return fd

builtins.open = tracked_open
stats = get_statistics()
"""
        ).receive()

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
                key=lambda x: x[1]["open_count"],
                reverse=True,
            )

            if self.verbose:
                f.write("\n")
                f.write("Stack Traces (grouped by trace):\n")
                f.write("-" * 80 + "\n")

                # Collect all traces from all files and group by stack trace
                traces_by_key = {}  # stack_key -> [(path, count), ...]

                for path, record in items:
                    if record["stack_traces"]:
                        for stack in record["stack_traces"]:
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
                            traces_by_key[stack_key].append(
                                (path, record["open_count"])
                            )

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
                open_count = record["open_count"]
                bar_length = min(open_count, 50)
                bar = "*" * bar_length
                f.write(f"  {open_count:4d}x {path}\n")
                f.write(f"       |{bar}\n")

            # Show remaining files compactly
            if len(items) > 20:
                f.write(f"\nRemaining {len(items) - 20} files:\n")
                for path, record in items[20:]:
                    open_count = record["open_count"]
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

    def get_fd_tracking_stats(self):
        """Get FD tracking statistics (same structure as remote)."""
        return {
            "total_opens": self.total_opens,
            "total_closes": self.total_closes,
            "open_fds": len(self._open_fds),
            "fd_leak": len(self._open_fds) > 200,
            "leaked_fds": [
                (fd, path, mode, open_time)
                for fd, (path, mode, open_time) in self._open_fds.items()
            ],
            "logs": self._fd_tracking_logs,
        }

    @classmethod
    def cleanup(cls):
        """Clean up the singleton instance and reset builtins.open."""
        if cls._instance is not None:
            builtins.open = cls._instance.original_open
            cls._instance = None

    def generate_reports(self, hosts):

        if not self.enabled:
            return

        # First, collect all remote stats
        for host in hosts:
            if getattr(host, "gateway", None):
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
                                self.fd_records[host_path] = {
                                    "open_count": 0,
                                    "modes": {},
                                    "stack_traces": [],
                                }
                            self.fd_records[host_path]["open_count"] += record[
                                "open_count"
                            ]
                            # Merge modes
                            for mode, count in record.get("modes", {}).items():
                                if mode not in self.fd_records[host_path]["modes"]:
                                    self.fd_records[host_path]["modes"][mode] = 0
                                self.fd_records[host_path]["modes"][mode] += count
                            # Merge stack traces
                            for stack in record.get("stack_traces", []):
                                self.fd_records[host_path]["stack_traces"].append(stack)
                    # Show verbose logs if available
                    if "logs" in remote_stats and self.verbose:
                        output.line(f"  FD opens for {host.name}:")
                        for now, count, path, mode, _action in remote_stats["logs"][:10]:
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
            f"{local_stats.get('open_fds', 0)} still open",
        )

        # Show leaked FDs if any (local)
        if local_stats.get("fd_leak", False):
            output.annotate(
                f"Local FD leak warning: "
                f"{local_stats.get('open_fds', 0)} FDs still open",
                red=True,
            )
            if "leaked_fds" in local_stats:
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
            key=lambda x: x[1]["open_count"],
            reverse=True,
        )
        for path, record in items[:10]:
            open_count = record["open_count"]
            if open_count <= 1:
                continue
            bar_length = min(open_count, 20)
            bar = "█" * bar_length
            # Format modes for display
            modes_str = ", ".join(
                [f"{mode}:{count}" for mode, count in sorted(record["modes"].items())]
            )
            # Shorten path for display
            path_str = str(path)
            if len(path_str) > 60:
                display_path = "..." + path_str[-57:]
            else:
                display_path = path_str
            output.line(f"  {open_count:4d}x {display_path}")
            output.line(f"       |{bar} [{modes_str}]")
