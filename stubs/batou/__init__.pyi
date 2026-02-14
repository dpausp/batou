from traceback import StackSummary
from typing import (
    Any,
)

from batou.component import (
    Component,
    RootComponent,
)

def prepare_error(error: Exception) -> str: ...
def prepare_traceback(tb: Any) -> str: ...
def prepare_traceback_from_stack(stack: StackSummary) -> str: ...

class ReportingException(Exception):
    affected_hostname: str | None

    def report(self): ...
    def should_merge(self, other: ReportingException) -> bool: ...
    @classmethod
    def merge(
        cls, selfs: list[ReportingException]
    ) -> tuple[ReportingException, set[str] | None]: ...

class AgeCallError(ReportingException):
    command: str
    exitcode: str
    output: str

    @classmethod
    def from_context(
        cls, command: list[str], exitcode: int, output: bytes
    ) -> AgeCallError: ...
    def report(self): ...

class AttributeExpansionError(ReportingException):
    component_breadcrumbs: str
    value_repr: str
    error_str: str
    key: str

    @property
    def sort_key(self) -> tuple[int, str, str, str]: ...
    @classmethod
    def from_context(
        cls, component: Component, key: str, value: Any, error: Exception
    ) -> AttributeExpansionError: ...

class ComponentLoadingError(ReportingException):
    filename: str
    exception_str: str
    traceback: str

    @classmethod
    def from_context(
        cls, filename: str, exception: Exception, tb: Any
    ) -> ComponentLoadingError: ...
    def report(self): ...

class ComponentUsageError(ReportingException):
    message: str
    traceback: str

    @property
    def sort_key(self) -> tuple[int, str]: ...
    @classmethod
    def from_context(cls, message: str) -> ComponentUsageError: ...

class ComponentWithUpdateWithoutVerify(ReportingException):
    components: list[str]
    roots: list[str]

    @classmethod
    def from_context(
        cls, components: list[Component], roots: list[RootComponent]
    ) -> ComponentWithUpdateWithoutVerify: ...

class ConfigurationError(ReportingException):
    message: str
    has_component: bool
    component_root_name: str | None

    def __str__(self) -> str: ...
    @classmethod
    def from_context(
        cls, message: str, component: Component | None = ...
    ) -> ConfigurationError: ...
    def report(self): ...
    @property
    def sort_key(self) -> tuple[int, str]: ...

class ConversionError(ConfigurationError):
    component_breadcrumbs: str
    conversion_name: str
    value_repr: str
    error_str: str
    key: str

    @property
    def sort_key(self) -> tuple[int, str, str, str, str]: ...
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
    def sort_key(self) -> tuple[int, str]: ...
    # Note: from_context has different signature but this is intentional

class DuplicateHostError(ConfigurationError):
    @property
    def sort_key(self) -> tuple[int, str]: ...
    # Note: from_context has different signature but this is intentional

class DuplicateHostMapping(ConfigurationError):
    a: str
    b: str

    @property
    def sort_key(self) -> tuple[int, str, str, str]: ...
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
    def from_context(cls, filename: str) -> FileLockedError: ...
    def report(self): ...

class GetAddressInfoError(ReportingException):
    hostname: str
    error: str

    @classmethod
    def from_context(cls, hostname: str, error: str) -> GetAddressInfoError: ...

class GPGCallError(ReportingException):
    command: str
    exitcode: str
    output: str

    @classmethod
    def from_context(
        cls, command: list[str], exitcode: int, output: bytes
    ) -> GPGCallError: ...
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
    attributes: list[str]

    @property
    def sort_key(self) -> tuple[int, str, str]: ...
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
    ) -> TemplatingError: ...

class UnknownComponentConfigurationError(ConfigurationError):
    root_name: str
    root_host_name: str
    exception_repr: str
    traceback: str

    @property
    def sort_key(self) -> tuple[int, str, int]: ...
    # Note: from_context has different signature but this is intentional

class UnknownHostSecretsSection(ConfigurationError):
    hostname: str
    # Note: from_context has different signature but this is intentional

class UnsatisfiedResources(ConfigurationError):
    unsatisfied_resources: list[tuple[str, str | None, list[str]]]
    # Note: from_context has different signature but this is intentional

class UnusedComponentsInitialized(ConfigurationError):
    unused_components: list[str]
    breadcrumbs: list[list[str]]
    init_file_paths: list[str]
    init_line_numbers: list[int]
    root_name: str

    def __str__(self) -> str: ...
    # Note: from_context has different signature but this is intentional

class UnusedResources(ConfigurationError):
    unused_resources: list[tuple[str, str, str]]
    # Note: from_context has different signature but this is intentional

class UpdateNeeded(AssertionError):
    pass
