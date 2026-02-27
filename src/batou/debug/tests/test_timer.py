"""Tests for Timer class."""

import time

import pytest

from batou.utils import Timer, format_duration

pytestmark = pytest.mark.debug


def test_timer_basic_context_manager():
    """Test Timer as context manager for timing operations."""
    timer = Timer("test")
    with timer.step("operation"):
        time.sleep(0.01)

    assert "operation" in timer.durations
    assert timer.durations["operation"] >= 0.01


def test_timer_multiple_steps():
    """Test Timer with multiple sequential steps."""
    timer = Timer("test")
    with timer.step("step1"):
        time.sleep(0.01)
    with timer.step("step2"):
        time.sleep(0.02)

    assert timer.durations["step1"] >= 0.01
    assert timer.durations["step2"] >= 0.02


def test_timer_tag():
    """Test Timer stores tag for identification."""
    timer = Timer("my_component")
    assert timer.tag == "my_component"


def test_timer_total_step_forbidden():
    """Test that 'total' is forbidden as a step name."""
    timer = Timer("test")
    try:
        timer.step("total")
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "Cannot use 'total' as a step name" in str(e)


def test_timer_above_threshold_no_exceed():
    """Test above_threshold returns False when no step exceeds threshold."""
    timer = Timer("test")
    with timer.step("fast"):
        time.sleep(0.01)

    exceeded, steps = timer.above_threshold(fast=1.0)
    assert exceeded is False
    assert steps == []


def test_timer_above_threshold_exceeds():
    """Test above_threshold returns True when step exceeds threshold."""
    timer = Timer("test")
    with timer.step("slow"):
        time.sleep(0.05)

    exceeded, steps = timer.above_threshold(slow=0.01)
    assert exceeded is True
    assert steps == ["slow"]


def test_timer_above_threshold_total():
    """Test above_threshold checks total duration."""
    timer = Timer("test")
    with timer.step("step1"):
        time.sleep(0.02)
    with timer.step("step2"):
        time.sleep(0.02)

    exceeded, steps = timer.above_threshold(total=0.03)
    assert exceeded is True
    assert "total" in steps


def test_timer_above_threshold_multiple_steps():
    """Test above_threshold detects multiple exceeding steps."""
    timer = Timer("test")
    with timer.step("step1"):
        time.sleep(0.05)
    with timer.step("step2"):
        time.sleep(0.02)
    with timer.step("step3"):
        time.sleep(0.06)

    exceeded, steps = timer.above_threshold(step1=0.01, step3=0.01)
    assert exceeded is True
    assert set(steps) == {"step1", "step3"}


def test_timer_humanize_basic():
    """Test humanize returns formatted duration string."""
    timer = Timer("test")
    with timer.step("step1"):
        time.sleep(0.01)
    with timer.step("step2"):
        time.sleep(0.02)

    result = timer.humanize("step1", "step2", "total")
    assert "step1=" in result
    assert "step2=" in result
    assert "total=" in result


def test_timer_humanize_nonexistent_step():
    """Test humanize handles non-existent steps gracefully."""
    timer = Timer("test")
    with timer.step("step1"):
        time.sleep(0.01)

    result = timer.humanize("step1", "nonexistent")
    assert "step1=" in result
    assert "nonexistent=" in result


def test_format_duration_none():
    """Test format_duration handles None value."""
    result = format_duration(None)
    assert result == "∅"


def test_format_duration_seconds():
    """Test format_duration formats seconds correctly."""
    result = format_duration(1.23124)
    assert "1.23" in result
    assert "s" in result


def test_format_duration_minutes():
    """Test format_duration formats minutes correctly."""
    result = format_duration(61)
    assert "1m" in result
    assert "1s" in result


def test_format_duration_large_minutes():
    """Test format_duration formats large minute values."""
    result = format_duration(125)
    assert "2m" in result
    assert "5s" in result


def test_timer_accumulates_durations():
    """Test Timer accumulates durations when step is called multiple times."""
    timer = Timer("test")
    with timer.step("operation"):
        time.sleep(0.01)
    with timer.step("operation"):
        time.sleep(0.01)
    with timer.step("operation"):
        time.sleep(0.01)

    assert timer.durations["operation"] >= 0.03
