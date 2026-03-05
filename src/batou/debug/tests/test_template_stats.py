"""Tests for TemplateStats class."""

import pytest

from batou.debug.template_stats import TemplateStats

pytestmark = pytest.mark.debug


def test_template_stats_initial_values():
    """Test TemplateStats initializes with zeros."""
    stats = TemplateStats()
    assert stats.hits == 0
    assert stats.misses == 0
    assert stats.size == 0


def test_template_stats_record_hit():
    """Test recording cache hits."""
    stats = TemplateStats()
    stats.record_hit()
    assert stats.hits == 1
    assert stats.misses == 0


def test_template_stats_record_multiple_hits():
    """Test recording multiple cache hits."""
    stats = TemplateStats()
    stats.record_hit(5)
    assert stats.hits == 5


def test_template_stats_record_miss():
    """Test recording cache misses."""
    stats = TemplateStats()
    stats.record_miss()
    assert stats.hits == 0
    assert stats.misses == 1


def test_template_stats_record_multiple_misses():
    """Test recording multiple cache misses."""
    stats = TemplateStats()
    stats.record_miss(3)
    assert stats.misses == 3


def test_template_stats_accumulates():
    """Test hits and misses accumulate across calls."""
    stats = TemplateStats()
    stats.record_hit(10)
    stats.record_miss(5)
    stats.record_hit(3)
    assert stats.hits == 13
    assert stats.misses == 5


def test_template_stats_update_size():
    """Test updating cache size."""
    stats = TemplateStats()
    stats.update_size(100)
    assert stats.size == 100


def test_template_stats_update_size_maximum():
    """Test size tracks maximum value."""
    stats = TemplateStats()
    stats.update_size(100)
    stats.update_size(50)
    stats.update_size(200)
    assert stats.size == 200


def test_template_stats_get_stats():
    """Test get_stats returns dictionary with all values."""
    stats = TemplateStats()
    stats.record_hit(10)
    stats.record_miss(5)
    stats.update_size(100)

    result = stats.get_stats()
    assert result["hits"] == 10
    assert result["misses"] == 5
    assert result["size"] == 100
