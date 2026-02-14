from batou.environment import Environment
from typing import (
    Optional,
    Union,
)

def main(
    environment: str,
    platform: None,
    timeout: None,
    dirty: bool,
    consistency_only: bool,
    predict_only: bool,
    check_and_predict_local: bool,
    jobs: None,
    provision_rebuild: bool,
): ...

class Deployment:
    def __init__(
        self,
        environment: Environment | str,
        platform: str | None,
        timeout: int | None,
        dirty: bool,
        jobs: int | None,
        consistency_only: bool = ...,
        predict_only: bool = ...,
        check_and_predict_local: bool = ...,
        provision_rebuild: bool = ...,
    ): ...
    def _connections(self): ...
    def connect(self): ...
    def disconnect(self): ...
    def load(self): ...
    @property
    def local_consistency_check(self) -> bool: ...
    def provision(self): ...
