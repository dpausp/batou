from typing import (
    Any,
    Dict,
    List,
    Union,
)


def _int_to_literal(value: Union[int, str]) -> int: ...


def get_debug_settings() -> DebugSettings: ...


class DebugSettings:
    def describe(self) -> List[Dict[str, Any]]: ...
    def show(self): ...
