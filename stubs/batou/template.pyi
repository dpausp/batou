from io import StringIO
from batou.component import ConfigString
from batou.tests.test_template import Server
from jinja2.environment import Template
from mock.mock import Mock
from typing import (
    Any,
    Dict,
    List,
    Type,
    Union,
)


class Jinja2Engine:
    def __init__(self, *args, **kwargs): ...
    @staticmethod
    def __new__(cls: Type[Jinja2Engine], *args, **kwargs) -> Jinja2Engine: ...
    def _compile_template(self, templatestr: Union[ConfigString, str]) -> Template: ...
    def _evict_lru(self): ...
    def _render_template_file(
        self,
        sourcefile: str,
        args: Dict[str, Union[Mock, List[Server], str]]
    ) -> StringIO: ...
    def _reset_cache_stats(self): ...
    def expand(
        self,
        templatestr: Union[ConfigString, str],
        args: Dict[str, Any],
        identifier: str = ...
    ) -> str: ...
    def retrieve_cache_stats(self) -> Dict[str, int]: ...


class TemplateEngine:
    def _render_template_file(self, sourcefile: str, args: Dict[Any, Any]): ...
    def expand(self, templatestr: str, args: Dict[Any, Any]): ...
    @classmethod
    def get(cls, enginename: str) -> Jinja2Engine: ...
    def template(
        self,
        sourcefile: str,
        args: Dict[str, Union[Mock, List[Server], str]]
    ) -> str: ...
