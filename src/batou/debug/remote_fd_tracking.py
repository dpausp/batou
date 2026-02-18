"""Remote FD tracking code for leak detection."""

import os
import traceback

# FD Tracking
_fd_tracking_enabled = False
_fd_tracking_verbose = False
_total_fd_opens = 0
_total_fd_closes = 0
_open_fds = {}  # fd -> (path, mode, open_time)
_fd_tracking_logs = []
_fd_records = {}  # path -> {"open_count": int, "modes": {}, "stack_traces": []}


def _track_fd_open(fd, path, mode="r"):
    """Track file descriptor opens and send to local channel."""
    global \
        _total_fd_opens, \
        _fd_tracking_enabled, \
        _fd_tracking_verbose, \
        _fd_tracking_logs, \
        _open_fds, \
        _fd_records

    _total_fd_opens += 1
    import datetime

    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    _open_fds[fd] = (path, mode, now)
    _fd_tracking_logs.append((now, _total_fd_opens, path, mode, "open"))

    # Track in fd_records for detailed analysis (like local)
    if path not in _fd_records:
        _fd_records[path] = {"open_count": 0, "modes": {}, "stack_traces": []}
    _fd_records[path]["open_count"] += 1
    if mode not in _fd_records[path]["modes"]:
        _fd_records[path]["modes"][mode] = 0
    _fd_records[path]["modes"][mode] += 1
    # Collect stack traces if verbose mode is enabled
    if _fd_tracking_verbose:
        # Collect full stack trace and filter out tracking code
        full_stack = traceback.extract_stack()
        # Filter out frames from tracking code and convert to serializable format
        filtered_stack = []
        for frame in full_stack:
            # Skip tracking code frames
            if "batou/remote_core.py" in frame.filename and (
                "tracked_open" in frame.name or "_track_fd_open" in frame.name
            ):
                continue
            # Convert FrameSummary to tuple for serialization
            filtered_stack.append((frame.filename, frame.lineno, frame.name))
            # Stop after we have enough frames (excluding tracking code)
            if len(filtered_stack) >= 10:
                break
        if filtered_stack:
            _fd_records[path]["stack_traces"].append(filtered_stack)

    # Warn if we have too many FDs open
    FD_WARNING_THRESHOLD = 200  # Common default limit is 256
    if len(_open_fds) > FD_WARNING_THRESHOLD:
        _fd_tracking_logs.append(
            (
                now,
                _total_fd_opens,
                f"WARNING: {len(_open_fds)} FDs open (threshold: {FD_WARNING_THRESHOLD})",
                "warning",
                "leak",
            )
        )


def _track_fd_close(fd):
    """Track file descriptor closes."""
    global _total_fd_closes, _fd_tracking_logs, _open_fds

    import datetime

    now = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]

    if fd in _open_fds:
        path, mode, open_time = _open_fds.pop(fd)
        _total_fd_closes += 1
        _fd_tracking_logs.append((now, _total_fd_opens, path, mode, "close"))
    else:
        # Low-level fd (like from mkstemp) - log it
        _total_fd_closes += 1
        _fd_tracking_logs.append(
            (
                now,
                _total_fd_opens,
                f"fd:{fd} (low-level)",
                "low-level",
                "close",
            )
        )


def install_remote_fd_tracking_hook():
    """Install builtins.open hook for FD tracking."""
    import builtins

    _original_open = builtins.open

    def tracked_open(path, mode="r", *args, **kwargs):
        fd = _original_open(path, mode, *args, **kwargs)
        _track_fd_open(fd.fileno(), path, mode)

        # Wrap close() to track it
        original_close = fd.close

        def tracked_close():
            _track_fd_close(fd.fileno())
            return original_close()

        fd.close = tracked_close
        return fd

    builtins.open = tracked_open  # type: ignore[method-assign]

    # Track os.close() for low-level FD operations like mkstemp()
    _original_os_close = os.close

    def tracked_os_close(fd):
        _track_fd_close(fd)
        return _original_os_close(fd)

    os.close = tracked_os_close  # type: ignore[method-assign]


def init_remote_fd_tracking(track_fds_level: int):
    """Initialize remote FD tracking with verbosity level."""
    global _fd_tracking_enabled, _fd_tracking_verbose
    _fd_tracking_enabled = track_fds_level > 0
    _fd_tracking_verbose = track_fds_level > 1


def get_remote_fd_tracking_stats():
    """Get FD tracking statistics from remote side."""
    stats = {
        "total_opens": _total_fd_opens,
        "total_closes": _total_fd_closes,
        "open_fds": len(_open_fds),
        "fd_leak": len(_open_fds) > 200,  # Same threshold as warning
    }
    if _open_fds:
        stats["leaked_fds"] = [
            (fd, path, mode, open_time)
            for fd, (path, mode, open_time) in _open_fds.items()
        ]
    if _fd_tracking_logs:
        stats["logs"] = _fd_tracking_logs
    if _fd_records:
        stats["fd_records"] = _fd_records
    return stats
