"""Remote profiling with cProfile integration."""

import io
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProfilingResults:
    """Profiling results from remote host execution."""

    host: str
    profile_path: Path
    content: str


class RemoteProfiler:
    """Remote profiling wrapper for batou deployments."""

    def __init__(
        self, host_name: str, profile_lines: int = 30, output_dir: str = "/tmp"
    ):
        self.host_name = host_name
        self.profile_lines = profile_lines
        self.output_dir = Path(output_dir)

    def profile_execution(self, func):
        """Execute function with profiling enabled."""
        import os

        # Check if profiling is enabled via environment variable
        if not os.environ.get("BATOU_PROFILE"):
            # Profiling disabled - just execute function without profiling
            return func()

        # Profiling enabled - proceed with cProfile
        import cProfile
        import pstats

        pr = cProfile.Profile()
        pr.enable()
        result = func()
        pr.disable()

        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats("cumtime")
        lines = self.profile_lines
        if lines < 0:
            ps.print_stats()  # all calls
        else:
            ps.print_stats(lines)
        profile_output = s.getvalue()

        profile_path = self.output_dir / f"batou_remote_profile_{self.host_name}.txt"
        with open(profile_path, "w") as f:
            f.write(f"=== Profile for host {self.host_name} ===\n")
            f.write(profile_output)

        return result

    def get_profiling_results(self) -> dict | None:
        """Retrieve profiling results from remote host."""
        profile_path = self.output_dir / f"batou_remote_profile_{self.host_name}.txt"
        if not profile_path.exists():
            return None

        with open(profile_path) as f:
            content = f.read()

        return {
            "host": self.host_name,
            "profile_path": str(profile_path),
            "content": content,
        }
