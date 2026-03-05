"""Template cache statistics tracking for debugging."""

from typing import TypedDict

from batou import output
from batou.component import Component


class TemplateCacheStats(TypedDict):
    """Snapshot of template cache statistics."""

    hits: int
    misses: int
    size: int


class TemplateStats:
    """Track template cache statistics."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.size = 0

    def record_hit(self, count=1):
        """Record template cache hit(s)."""
        self.hits += count

    def record_miss(self, count=1):
        """Record template cache miss(es)."""
        self.misses += count

    def update_size(self, size):
        """Update current cache size (maximum across all components)."""
        if size > self.size:
            self.size = size

    def collect_component_stats(self, components: list[Component]):
        """Collect template cache statistics from components."""
        for component in components:
            template_engine = getattr(component, "_template_engine", None)
            if template_engine is not None:
                retrieve_stats = getattr(template_engine, "retrieve_cache_stats", None)
                if callable(retrieve_stats):
                    stats = retrieve_stats()
                    if stats:
                        self.record_hit(stats["hits"])
                        self.record_miss(stats["misses"])
                        self.update_size(stats["currsize"])

    def get_stats(self) -> TemplateCacheStats:
        """Return current statistics as a dictionary."""
        return {"hits": self.hits, "misses": self.misses, "size": self.size}

    def show_stats(self):
        stats = self.get_stats()
        total_hits = stats["hits"]
        total_misses = stats["misses"]
        total_size = stats["size"]

        if total_hits + total_misses > 0:
            hit_rate = 100 * total_hits / (total_hits + total_misses)
            output.annotate(
                f"Template cache: {total_hits} hits, {total_misses} misses, "
                f"{total_size} cached templates ({hit_rate:.1f}% hit rate)"
            )
