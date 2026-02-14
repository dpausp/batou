from batou.component import (
    ComponentDefinition,
    RootComponent,
)
from batou.environment import Environment
from batou.lib.cron import CronTab
from batou.utils import CycleError
from traceback import StackSummary
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)


def prepare_error(error: Union[KeyError, ValueError, IndexError]) -> str: ...


def prepare_traceback(tb: None) -> str: ...


def prepare_traceback_from_stack(stack: StackSummary) -> str: ...


class ComponentLoadingError:
    @classmethod
    def from_context(cls, filename: str, exception: ValueError, tb: None) -> ComponentLoadingError: ...
    def report(self): ...


class ConfigurationError:
    def __str__(self) -> str: ...
    @classmethod
    def from_context(cls, message: str, component: Optional[CronTab] = ...) -> ConfigurationError: ...
    def report(self): ...
    @property
    def sort_key(self) -> Tuple[int, str]: ...


class ConversionError:
    @property
    def sort_key(self) -> Tuple[int, str, str, str]: ...


class CycleErrorDetected:
    @classmethod
    def from_context(cls, error: Union[ValueError, CycleError, str]) -> CycleErrorDetected: ...


class DuplicateComponent:
    @classmethod
    def from_context(
        cls,
        a: ComponentDefinition,
        b: ComponentDefinition
    ) -> DuplicateComponent: ...
    @property
    def sort_key(self) -> Tuple[int, str]: ...


class DuplicateHostError:
    @classmethod
    def from_context(cls, hostname: str) -> DuplicateHostError: ...
    @property
    def sort_key(self): ...


class DuplicateHostMapping:
    @classmethod
    def from_context(cls, hostname: str, a: str, b: str) -> DuplicateHostMapping: ...
    @property
    def sort_key(self) -> Tuple[int, str, str, str]: ...


class DuplicateOverride:
    @classmethod
    def from_context(cls, component_name: str, attribute: str) -> DuplicateOverride: ...
    def report(self): ...


class GPGCallError:
    @classmethod
    def from_context(cls, command: List[str], exitcode: int, output: bytes) -> GPGCallError: ...


class InvalidIPAddressError:
    @classmethod
    def from_context(cls, address: str) -> InvalidIPAddressError: ...


class MissingComponent:
    @classmethod
    def from_context(cls, component_name: str, hostname: str) -> MissingComponent: ...
    def report(self): ...


class MissingEnvironment:
    @classmethod
    def from_context(cls, environment: Environment) -> MissingEnvironment: ...


class MissingOverrideAttributes:
    @property
    def sort_key(self) -> Tuple[int, str, str]: ...


class NonConvergingWorkingSet:
    @classmethod
    def from_context(
        cls,
        roots: Union[List[RootComponent], Set[RootComponent]]
    ) -> NonConvergingWorkingSet: ...


class RepositoryDifferentError:
    @classmethod
    def from_context(cls, local: str, remote: str) -> RepositoryDifferentError: ...


class SuperfluousComponentSection:
    @classmethod
    def from_context(cls, component_name: str) -> SuperfluousComponentSection: ...
    def report(self): ...


class SuperfluousSecretsSection:
    def __str__(self) -> str: ...
    @classmethod
    def from_context(cls, component_name: str) -> SuperfluousSecretsSection: ...
    def report(self): ...


class SuperfluousSection:
    @classmethod
    def from_context(cls, section: str) -> SuperfluousSection: ...
    def report(self): ...


class UnknownComponentConfigurationError:
    @property
    def sort_key(self) -> Tuple[int, str, int]: ...


class UnknownHostSecretsSection:
    @classmethod
    def from_context(cls, hostname: str) -> UnknownHostSecretsSection: ...


class UnsatisfiedResources:
    @classmethod
    def from_context(
        cls,
        resources: Union[Dict[Tuple[str, None], List[RootComponent]], Dict[Tuple[str, None], Set[RootComponent]], Dict[Union[Tuple[str, str], Tuple[str, None]], Set[RootComponent]], Dict[Tuple[str, str], Set[RootComponent]]]
    ) -> UnsatisfiedResources: ...


class UnusedComponentsInitialized:
    def __str__(self) -> str: ...


class UnusedResources:
    @classmethod
    def from_context(
        cls,
        resources: Dict[str, Union[Dict[RootComponent, int], Dict[RootComponent, List[int]]]]
    ) -> UnusedResources: ...
