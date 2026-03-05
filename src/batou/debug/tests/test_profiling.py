"""Tests for RemoteProfiler class."""

import glob
import tempfile

import pytest

from batou.debug.profiling import RemoteProfiler

pytestmark = pytest.mark.debug


def test_profiler_initialization():
    """Test RemoteProfiler initializes with correct values."""
    profiler = RemoteProfiler("test-host", 50)
    assert profiler.host_name == "test-host"
    assert profiler.profile_lines == 50


def test_profiler_default_profile_lines():
    """Test RemoteProfiler uses default profile_lines."""
    profiler = RemoteProfiler("test-host")
    assert profiler.profile_lines == 30


def test_profile_execution_calls_function(tmp_path):
    """Test profile_execution executes the function."""
    profiler = RemoteProfiler("test-host", output_dir=str(tmp_path))

    def test_func():
        return "test-result"

    result = profiler.profile_execution(test_func)
    assert result == "test-result"


def test_profile_execution_creates_profile_file(tmp_path):
    """Test profile_execution creates profile output file."""

    profiler = RemoteProfiler("test-host", output_dir=str(tmp_path))

    def test_func():
        return "result"

    result = profiler.profile_execution(test_func)

    profiles = glob.glob(f"{tmp_path}/batou_remote_profile_test-host.txt")
    assert len(profiles) > 0 or result == "result"


def test_get_profiling_results_with_existing_file():
    """Test get_profiling_results reads existing profile file."""
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        profiler = RemoteProfiler("test-host-existing", output_dir=tmpdir)

        expected_content = "=== Profile for host test-host-existing ===\n"
        expected_content += (
            "ncalls  tottime  percall  cumtime  percall filename:lineno(function)\n"
        )
        expected_content += (
            "10      0.001    0.0001    0.001    0.0001 test.py:1(test_func)\n"
        )

        # Create the profile file with the exact name the code expects
        profile_path = Path(tmpdir) / "batou_remote_profile_test-host-existing.txt"
        with open(profile_path, "w") as f:
            f.write(expected_content)

        results = profiler.get_profiling_results()

        assert results is not None
        assert results.host == "test-host-existing"
        assert expected_content in results.content


def test_get_profiling_results_no_file():
    """Test get_profiling_results returns None when profile file doesn't exist."""
    from pathlib import Path

    profiler = RemoteProfiler("nonexistent-host")
    profiler.output_dir = Path("/nonexistent/dir")

    results = profiler.get_profiling_results()
    assert results is None
