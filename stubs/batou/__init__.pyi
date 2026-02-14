from batou.component import (
    Component,
    ComponentDefinition,
    RootComponent,
)
from batou.environment import Environment
from batou.utils import CycleError
from traceback import StackSummary
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

def prepare_error(error: Exception) -> str: ...
def prepare_traceback(tb: Any) -> str: ...
def prepare_traceback_from_stack(stack: StackSummary) -> str: ...

class ReportingException(Exception):
    affected_hostname: Optional[str]

    def report(self): ...
    def should_merge(self, other: "ReportingException") -> bool: ...
    @classmethod
    def merge(
        cls, selfs: List["ReportingException"]
    ) -> Tuple["ReportingException", Optional[Set[str]]]: ...

class AgeCallError(ReportingException):
    command: str
    exitcode: str
    output: str

    @classmethod
    def from_context(
        cls, command: List[str], exitcode: int, output: bytes
    ) -> "AgeCallError": ...
    def report(self): ...

class AttributeExpansionError(ReportingException):
    component_breadcrumbs: str
    value_repr: str
    error_str: str
    key: str

    @property
    def sort_key(self) -> Tuple[int, str, str, str]: ...
    @classmethod
    def from_context(
        cls, component: Component, key: str, value: Any, error: Exception
    ) -> "AttributeExpansionError": ...

class ComponentLoadingError(ReportingException):
    filename: str
    exception_str: str
    traceback: str

    @classmethod
    def from_context(
        cls, filename: str, exception: Exception, tb: Any
    ) -> "ComponentLoadingError": ...
    def report(self): ...

class ComponentUsageError(ReportingException):
    message: str
    traceback: str

    @property
    def sort_key(self) -> Tuple[int, str]: ...
    @classmethod
    def from_context(cls, message: str) -> "ComponentUsageError": ...

class ComponentWithUpdateWithoutVerify(ReportingException):
    components: List[str]
    roots: List[str]

    @classmethod
    def from_context(
        cls, components: List[Component], roots: List[RootComponent]
    ) -> "ComponentWithUpdateWithoutVerify": ...

class ConfigurationError(ReportingException):
    message: str
    has_component: bool
    component_root_name: Optional[str]

    def __str__(self) -> str: ...
    @classmethod
    def from_context(
        cls, message: str, component: Optional[Component] = ...
    ) -> "ConfigurationError": ...
    def report(self): ...
    @property
    def sort_key(self) -> Tuple[int, str]: ...

class ConversionError(ConfigurationError):
    component_breadcrumbs: str
    conversion_name: str
    value_repr: str
    error_str: str
    key: str

    @property
    def sort_key(self) -> Tuple[int, str, str, str, str]: ...
    # Note: from_context has different signature but this is intentional

class CycleErrorDetected(ConfigurationError):
    error_str: str
    # Note: from_context has different signature but this is intentional

class DeploymentError(ReportingException):
    def report(self): ...

class DuplicateComponent(ConfigurationError):
    a_name: str
    a_filename: str
    b_filename: str

    @property
    def sort_key(self) -> Tuple[int, str]: ...
    # Note: from_context has different signature but this is intentional

class DuplicateHostError(ConfigurationError):
    @property
    def sort_key(self) -> Tuple[int, str]: ...
    # Note: from_context has different signature but this is intentional

class DuplicateHostMapping(ConfigurationError):
    a: str
    b: str

    @property
    def sort_key(self) -> Tuple[int, str, str, str]: ...
    # Note: from_context has different signature but this is intentional

class DuplicateOverride(ConfigurationError):
    component_name: str
    attribute: str
    # Note: from_context has different signature but this is intentional

class DuplicateSecretsComponentAttribute(ConfigurationError):
    component_name: str
    attribute: str
    # Note: from_context has different signature but this is intentional

class FileLockedError(ReportingException):
    filename: str

    @classmethod
    def from_context(cls, filename: str) -> "FileLockedError": ...
    def report(self): ...

class GetAddressInfoError(ReportingException):
    hostname: str
    error: str

    @classmethod
    def from_context(cls, hostname: str, error: str) -> "GetAddressInfoError": ...

class GPGCallError(ReportingException):
    command: str
    exitcode: str
    output: str

    @classmethod
    def from_context(
        cls, command: List[str], exitcode: int, output: bytes
    ) -> "GPGCallError": ...
    def report(self): ...

class IPAddressConfigurationError(ConfigurationError):
    address: Any
    kind: int
    # Note: from_context has different signature but this is intentional

class InvalidIPAddressError(ConfigurationError):
    address: str
    # Note: from_context has different signature but this is intentional

class MissingComponent(ConfigurationError):
    component_name: str
    # Note: from_context has different signature but this is intentional

class MissingEnvironment(ConfigurationError):
    environment_name: str
    # Note: from_context has different signature but this is intentional

class MissingOverrideAttributes(ConfigurationError):
    component_breadcrumbs: str
    attributes: List[str]

    @property
    def sort_key(self) -> Tuple[int, str, str]: ...
    # Note: from_context has different signature but this is intentional

class NonConvergingWorkingSet(ConfigurationError):
    roots_len: int
    root_names: str
    # Note: from_context has different signature but this is intentional

class RepositoryDifferentError(DeploymentError):
    local: str
    remote: str
    # Note: from_context has different signature but this is intentional

class SilentConfigurationError(Exception):
    pass

class SuperfluousComponentSection(ConfigurationError):
    component_name: str
    # Note: from_context has different signature but this is intentional

class SuperfluousSecretsSection(ConfigurationError):
    component_name: str

    def __str__(self) -> str: ...
    # Note: from_context has different signature but this is intentional

class SuperfluousSection(ConfigurationError):
    section: str
    # Note: from_context has different signature but this is intentional

class TemplatingError(ReportingException):
    exception_str: str
    template_identifier: str

    @classmethod
    def from_context(
        cls, exception: Exception, template_identifier: str
    ) -> "TemplatingError": ...

class UnknownComponentConfigurationError(ConfigurationError):
    root_name: str
    root_host_name: str
    exception_repr: str
    traceback: str

    @property
    def sort_key(self) -> Tuple[int, str, int]: ...
    # Note: from_context has different signature but this is intentional

class UnknownHostSecretsSection(ConfigurationError):
    hostname: str
    # Note: from_context has different signature but this is intentional

class UnsatisfiedResources(ConfigurationError):
    unsatisfied_resources: List[Tuple[str, Optional[str], List[str]]]
    # Note: from_context has different signature but this is intentional

class UnusedComponentsInitialized(ConfigurationError):
    unused_components: List[str]
    breadcrumbs: List[List[str]]
    init_file_paths: List[str]
    init_line_numbers: List[int]
    root_name: str

    def __str__(self) -> str: ...
    # Note: from_context has different signature but this is intentional

class UnusedResources(ConfigurationError):
    unused_resources: List[Tuple[str, str, str]]
    # Note: from_context has different signature but this is intentional

class UpdateNeeded(AssertionError):
    pass
