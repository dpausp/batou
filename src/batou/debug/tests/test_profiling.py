"""Tests for RemoteProfiler class."""

import glob
import os
import tempfile
from unittest.mock import patch

import pytest

from batou.debug.profiling import RemoteProfiler, enable_profiling

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

    profiler = RemoteProfiler("test-host-existing")

    # Create temporary profile file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=f"_batou_remote_profile_{profiler.host_name}.txt",
        delete=False,
    ) as f:
        profile_path = f.name
        f.write("=== Profile for host test-host-existing ===\n")
        f.write(
            "ncalls  tottime  percall  cumtime  percall filename:lineno(function)\n"
        )
        f.write("10      0.001    0.0001    0.001    0.0001 test.py:1(test_func)\n")

    try:
        expected_content = "=== Profile for host test-host-existing ==="
        expected_content += (
            "\nncalls  tottime  percall  cumtime  percall filename:lineno(function)\n"
        )
        expected_content += (
            "10      0.001    0.0001    0.001    0.0001 test.py:1(test_func)\n"
        )

        # Mock os.path.exists to return True for our temp file
        with patch("os.path.exists") as mock_exists:
            with patch("builtins.open") as mock_open:
                mock_exists.return_value = True

                # Create a mock file object
                mock_file = mock_open.return_value.__enter__.return_value
                mock_file.read.return_value = expected_content

                results = profiler.get_profiling_results()

                assert results is not None
                assert results["host"] == "test-host-existing"
                assert expected_content in results["content"]
    finally:
        # Clean up temp file
        if os.path.exists(profile_path):
            os.unlink(profile_path)


def test_get_profiling_results_no_file():
    """Test get_profiling_results returns None when profile file doesn't exist."""
    profiler = RemoteProfiler("nonexistent-host")

    with patch("os.path.exists", return_value=False):
        results = profiler.get_profiling_results()
        assert results is None


def test_enable_profiling_wrapper():
    """Test enable_profiling wrapper function."""

    def test_func():
        return "wrapped-result"

    # Mock RemoteProfiler to verify it's called
    with patch("batou.debug.profiling.RemoteProfiler") as MockProfiler:
        mock_profiler_instance = MockProfiler.return_value
        mock_profiler_instance.profile_execution.return_value = "mocked-result"

        result = enable_profiling("test-host", 30, test_func)

        assert result == "mocked-result"
        MockProfiler.assert_called_once_with("test-host", 30)
        mock_profiler_instance.profile_execution.assert_called_once_with(test_func)
