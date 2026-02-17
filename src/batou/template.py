"""batou templating support

Currently we support one templating engine:

Jinja2::
    {% for server in servers %}
    server {{ server.name }}
    {% endfor %}

"""

# There is a weird bug going on with Jinja2 on Python3.6 where this
# test fails if Jinja tries to import ctypes itself ... o_O
import hashlib
import io
import os

import jinja2

from batou import TemplatingError, output


class TemplateEngine:
    """Abstract templating wrapper class.

    Use a subclass that connects to a specific template engine.
    """

    @classmethod
    def get(cls, enginename):
        """Return TemplateEngine instance for `enginename`."""
        if enginename.lower() == "jinja2":
            return Jinja2Engine()
        raise NotImplementedError("template engine not known", enginename)

    def template(self, sourcefile, args):
        """Render template from `sourcefile` and return the value."""
        try:
            return self._render_template_file(sourcefile, args).getvalue()
        except jinja2.exceptions.TemplateError as e:
            raise TemplatingError.from_context(e, sourcefile)

    def _render_template_file(self, sourcefile, args):
        """Expand template found in `sourcefile` and return it as StringIO."""
        raise NotImplementedError

    def expand(self, templatestr, args):
        """Expand template in `templatestr` and return it as string."""
        raise NotImplementedError


class Jinja2Engine(TemplateEngine):
    # Global singleton for sharing template cache across all components
    _instance = None
    _max_cache_size = 1000  # Hard limit to prevent memory leaks
    _enable_cache = True  # Cache enabled by default

    @classmethod
    def enable_cache(cls, enabled: bool = True):
        """Enable or disable template caching for the Jinja2Engine.

        Args:
            enabled: True to enable caching, False to disable.
        """
        cls._enable_cache = enabled

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.env = jinja2.Environment(
                line_statement_prefix="@@",
                keep_trailing_newline=True,
                undefined=jinja2.StrictUndefined,
            )
            caching = os.environ.get("BATOU_ENABLE_TEMPLATE_CACHE", "1") != "0"
            cls._instance.cache_enabled = caching
            cls._cache_stats_retrieved = False
            if caching:
                cls._instance._template_cache = {}
                cls._instance._cache_order = []  # Track insertion order for LRU
                cls._instance._reset_cache_stats()
        return cls._instance

    def __init__(self, *args, **kwargs):
        # Skip super().__init__ since we're a singleton
        pass

    def _reset_cache_stats(self):
        self._cache_stats = {"hits": 0, "misses": 0}

    def reset_cache(self):
        if not self.cache_enabled:
            return
        self._template_cache.clear()
        self._cache_order.clear()
        self._reset_cache_stats()

    def _evict_lru(self):
        """Evict least recently used cache entry if limit reached."""
        if len(self._template_cache) >= self._max_cache_size:
            # Remove oldest entry (LRU)
            oldest_hash = self._cache_order.pop(0)
            del self._template_cache[oldest_hash]

    def _compile_template(self, templatestr):
        """Compile template string - cached by content hash."""
        if not self.enable_cache:
            return self.env.from_string(templatestr)

        # Hash template string for content-based caching
        template_hash = hashlib.sha256(templatestr.encode()).hexdigest()

        if template_hash in self._template_cache:
            self._cache_stats["hits"] += 1
            # Move to end of cache_order (mark as recently used)
            self._cache_order.remove(template_hash)
            self._cache_order.append(template_hash)
            return self._template_cache[template_hash]
        else:
            self._cache_stats["misses"] += 1
            self._evict_lru()  # Evict if needed
            template = self.env.from_string(templatestr)
            self._template_cache[template_hash] = template
            self._cache_order.append(template_hash)
            return template

    def _render_template_file(self, sourcefile, args):
        with open(sourcefile) as f:
            templatestr = f.read()
        tmpl = self._compile_template(templatestr)
        output = io.StringIO()
        print(tmpl.render(args), file=output)
        return output

    def expand(self, templatestr, args, identifier="<template>"):
        if len(templatestr) > 100 * 1024:
            output.error(
                "You are trying to render a template that is bigger than "
                "100KiB we've seen that Jinja can crash at large templates "
                "and suggest you find alternatives for this. The affected "
                "template starts with:"
            )
            output.annotate(templatestr[:100])
        try:
            tmpl = self._compile_template(templatestr)
            tmpl.filename = identifier
            return tmpl.render(**args)
        except Exception as e:
            raise TemplatingError.from_context(e, identifier)

    def retrieve_cache_stats(self):
        """Get cache stats and block further access to stats to detect double-counting."""

        if not self.cache_enabled:
            return {}

        """Return template cache statistics."""
        stats = {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "currsize": len(self._template_cache),
        }
        self._reset_cache_stats()
        return stats
