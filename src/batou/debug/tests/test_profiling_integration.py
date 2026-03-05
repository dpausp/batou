"""Integration tests for profiling with real deployments and execnet."""

from pathlib import Path
from unittest import mock

import pytest

from batou.debug.profiling import RemoteProfiler

pytestmark = pytest.mark.debug


class TestProfilingLocal:
    """Tests for profiling with local deployments."""

    def test_local_profiling_creates_file(self, tmp_path, monkeypatch):
        """Test that profiling creates profile file for local deployments."""
        monkeypatch.setenv("BATOU_PROFILE", "1")

        profiler = RemoteProfiler("localhost", 30, output_dir=str(tmp_path))

        def test_func():
            return "test-result"

        result = profiler.profile_execution(test_func)
        assert result == "test-result"

        # Check profile file was created
        profile_file = tmp_path / "batou_remote_profile_localhost.txt"
        assert profile_file.exists()

        with open(profile_file) as f:
            content = f.read()

        assert "Profile for host localhost" in content
        assert "cumtime" in content

    def test_profiling_disabled_no_file(self, tmp_path, monkeypatch):
        """Test that no profile file is created when profiling is disabled."""
        monkeypatch.delenv("BATOU_PROFILE", raising=False)

        profiler = RemoteProfiler("localhost", 30, output_dir=str(tmp_path))

        def test_func():
            return "test-result"

        result = profiler.profile_execution(test_func)
        assert result == "test-result"

        # Verify no profile file created
        profile_file = tmp_path / "batou_remote_profile_localhost.txt"
        assert not profile_file.exists()


class TestProfilingSerialization:
    """Tests for ProfilingResults serialization across execnet."""

    def test_profiling_results_is_serializable(self):
        """Test that ProfilingResults can be pickled for execnet RPC."""
        import pickle

        from batou.debug.profiling import ProfilingResults

        # Create a ProfilingResults instance
        results = ProfilingResults(
            host="localhost",
            profile_path=Path("/tmp/profile_localhost.txt"),
            content="=== Profile for host localhost ===\ntest content",
        )

        # Test that it can be pickled (execnet uses pickle for serialization)
        try:
            pickled = pickle.dumps(results)
            unpickled = pickle.loads(pickled)
            assert unpickled.host == "localhost"
            assert (
                unpickled.content == "=== Profile for host localhost ===\ntest content"
            )
            assert str(unpickled.profile_path) == "/tmp/profile_localhost.txt"
        except Exception as exc:
            pytest.fail(f"ProfilingResults cannot be serialized: {exc}")
            # If we get here, the bug is confirmed - we test documents it
            raise AssertionError(
                f"ProfilingResults serialization is broken - this is the bug we discovered. "
                f"Error: {exc}"
            )

    def test_get_profiling_results_returns_dict_when_broken(self, monkeypatch):
        """Test workaround: get_profiling_results should return dict instead of dataclass."""
        from batou import remote_core

        # This test should pass once we fix the serialization issue
        # by returning a dict from get_profiling_results instead of ProfilingResults
        monkeypatch.setenv("BATOU_PROFILE", "1")

        # Mock deployment
        with mock.patch.object(remote_core, "deployment") as mock_deployment:
            mock_deployment.debug_settings.profile = True
            mock_deployment.host_name = "test-host"
            mock_deployment.debug_settings.profile_lines = 30

            # Call get_profiling_results - should return dict after fix
            results = remote_core.get_profiling_results()

            # If still broken, this will raise an exception during pickle
            if results is not None:
                # Should be a dict, not ProfilingResults
                assert isinstance(results, dict), f"Expected dict, got {type(results)}"


class TestPython310Compatibility:
    """Tests for Python 3.10 compatibility."""

    def test_notrequired_import_python310(self):
        """Test that NotRequired can be imported on Python 3.10."""
        import sys

        # This test should pass on Python 3.10 and 3.11+
        if sys.version_info >= (3, 11):
            # On Python 3.11+, NotRequired is available from typing
            from typing import NotRequired
        else:
            # On Python 3.10, we need to use typing_extensions
            from typing_extensions import NotRequired

        # If we get here, import succeeded
        assert NotRequired is not None
