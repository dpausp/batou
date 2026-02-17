from io import StringIO
from typing import Any, Self

from jinja2.environment import Environment, Template

class TemplateEngine:
    @classmethod
    def get(cls, enginename: str) -> Jinja2Engine: ...
    def _render_template_file(
        self,
        sourcefile: str,
        args: dict[str, Any],
    ) -> StringIO: ...
    def expand(self, templatestr: str, args: dict[str, Any]) -> str: ...
    def template(self, sourcefile: str, args: dict[str, Any]) -> str: ...

class Jinja2Engine(TemplateEngine):
    env: Environment
    cache_enabled: bool
    _instance: Jinja2Engine | None
    _max_cache_size: int
    _enable_cache: bool
    _template_cache: dict[str, Template]
    _cache_order: list[str]
    _cache_stats: dict[str, int]

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    @staticmethod
    def __new__(cls: type[Jinja2Engine], *args: Any, **kwargs: Any) -> Self: ...
    def _compile_template(self, templatestr: str) -> Template: ...
    def _evict_lru(self) -> None: ...
    def _render_template_file(
        self,
        sourcefile: str,
        args: dict[str, Any],
    ) -> StringIO: ...
    def _reset_cache_stats(self) -> None: ...
    @classmethod
    def enable_cache(cls, enabled: bool = ...) -> None: ...
    def expand(
        self,
        templatestr: str,
        args: dict[str, Any],
        identifier: str = ...,
    ) -> str: ...
    def reset_cache(self) -> None: ...
    def retrieve_cache_stats(self) -> dict[str, int]: ...
