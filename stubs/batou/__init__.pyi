from traceback import StackSummary
from typing import Any

from batou.component import Component

__version__: str
output: Any  # from _output module

def prepare_error(error: Exception) -> str: ...
def prepare_traceback(tb: Any) -> str: ...
def prepare_traceback_from_stack(stack: StackSummary) -> str: ...

class ReportingException(Exception):
    affected_hostname: str | None

    def __str__(self) -> str: ...  # noqa: PYI029
    def report(self) -> None: ...
    def should_merge(self, other: ReportingException) -> bool: ...
    @classmethod
    def merge(
        cls,
        selfs: list[ReportingException],
    ) -> tuple[ReportingException, set[str] | None]: ...

class AgeCallError(ReportingException):
    command: str
    exitcode: str
    output: str

    @classmethod
    def from_context(
        cls,
        command: list[str],
        exitcode: int,
        output: bytes,
    ) -> AgeCallError: ...
    def report(self): ...

class AttributeExpansionError(ConfigurationError):
    component_breadcrumbs: str
    value_repr: str
    error: str
    error_str: str
    key: str

    @classmethod
    def from_context(
        cls,
        component: Any,
        key: str,
        value: Any,
        error: Exception,
    ) -> AttributeExpansionError: ...
    @property
    def sort_key(self) -> tuple[int, str, str, str]: ...

class ComponentLoadingError(ReportingException):
    filename: str
    exception_str: str
    traceback: str

    @classmethod
    def from_context(
        cls,
        filename: str,
        exception: Exception,
        tb: Any,
    ) -> ComponentLoadingError: ...
    def report(self): ...

class ComponentUsageError(ConfigurationError):
    message: str
    traceback: str

    @classmethod
    def from_context(cls, message: str) -> ComponentUsageError: ...
    @property
    def sort_key(self) -> tuple[int, str]: ...

class ComponentWithUpdateWithoutVerify(ConfigurationError):
    components: list[str]
    roots: list[str]

    @classmethod
    def from_context(
        cls,
        components: list[Any],
        roots: list[Any],
    ) -> ComponentWithUpdateWithoutVerify: ...

class ConfigurationError(ReportingException):
    message: str
    has_component: bool
    component_root_name: str | None

    @classmethod
    def from_context(
        cls,
        message: str,
        component: Component | None = ...,
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

    @classmethod
    def from_context(
        cls,
        component: Any,
        key: str,
        value: Any,
        conversion: Any,
        error: Exception,
    ) -> ConversionError: ...
    @property
    def sort_key(self) -> tuple[int, str, str, str, str]: ...

class CycleErrorDetected(ConfigurationError):
    error_str: str

    @classmethod
    def from_context(cls, error: Any) -> CycleErrorDetected: ...

class DeploymentError(ReportingException):
    sort_key: tuple[int, ...]

    def report(self): ...

class DuplicateComponent(ConfigurationError):
    a_name: str
    a_filename: str
    b_filename: str

    @classmethod
    def from_context(cls, a: Any, b: Any) -> DuplicateComponent: ...
    @property
    def sort_key(self) -> tuple[int, str]: ...

class DuplicateHostError(ConfigurationError):
    @classmethod
    def from_context(cls, hostname: str) -> DuplicateHostError: ...
    @property
    def sort_key(self) -> tuple[int, str]: ...

class DuplicateHostMapping(ConfigurationError):
    a: str
    b: str

    @classmethod
    def from_context(
        cls,
        hostname: str,
        a: str,
        b: str,
    ) -> DuplicateHostMapping: ...
    @property
    def sort_key(self) -> tuple[int, str, str, str]: ...

class DuplicateOverride(ConfigurationError):
    component_name: str
    attribute: str

    @classmethod
    def from_context(
        cls,
        component_name: str,
        attribute: str,
    ) -> DuplicateOverride: ...

class DuplicateSecretsComponentAttribute(ConfigurationError):
    component_name: str
    attribute: str

    @classmethod
    def from_context(
        cls,
        component_name: str,
        attribute: str,
    ) -> DuplicateSecretsComponentAttribute: ...

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
        cls,
        command: list[str],
        exitcode: int,
        output: bytes,
    ) -> GPGCallError: ...
    def report(self): ...

class IPAddressConfigurationError(ConfigurationError):
    address: Any
    kind: int

    @classmethod
    def from_context(cls, address: Any, kind: int) -> IPAddressConfigurationError: ...

class InvalidIPAddressError(ConfigurationError):
    address: str

    @classmethod
    def from_context(cls, address: str) -> InvalidIPAddressError: ...

class MissingComponent(ConfigurationError):
    component_name: str

    @classmethod
    def from_context(
        cls,
        component_name: str,
        hostname: str,
    ) -> MissingComponent: ...

class MissingEnvironment(ConfigurationError):
    environment_name: str

    @classmethod
    def from_context(cls, environment: Any) -> MissingEnvironment: ...

class MissingOverrideAttributes(ConfigurationError):
    component_breadcrumbs: str
    attributes: list[str]

    @classmethod
    def from_context(
        cls,
        component: Any,
        attributes: list[str],
    ) -> MissingOverrideAttributes: ...
    @property
    def sort_key(self) -> tuple[int, str, str]: ...

class NonConvergingWorkingSet(ConfigurationError):
    roots_len: int
    root_names: str

    @classmethod
    def from_context(cls, roots: Any) -> NonConvergingWorkingSet: ...

class RepositoryDifferentError(DeploymentError):
    local: str
    remote: str

    @classmethod
    def from_context(cls, local: str, remote: str) -> RepositoryDifferentError: ...

class SilentConfigurationError(Exception): ...

class SuperfluousComponentSection(ConfigurationError):
    component_name: str

    @classmethod
    def from_context(cls, component_name: str) -> SuperfluousComponentSection: ...

class SuperfluousSecretsSection(ConfigurationError):
    component_name: str

    @classmethod
    def from_context(cls, component_name: str) -> SuperfluousSecretsSection: ...

class SuperfluousSection(ConfigurationError):
    section: str

    @classmethod
    def from_context(cls, section: str) -> SuperfluousSection: ...

class TemplatingError(ReportingException):
    exception_str: str
    template_identifier: str

    @classmethod
    def from_context(
        cls,
        exception: Exception,
        template_identifier: str,
    ) -> TemplatingError: ...

class UnknownComponentConfigurationError(ConfigurationError):
    root_name: str
    root_host_name: str
    exception_repr: str
    traceback: str

    @classmethod
    def from_context(
        cls,
        root: Any,
        exception: Exception,
        tb: Any,
    ) -> UnknownComponentConfigurationError: ...
    @property
    def sort_key(self) -> tuple[int, str, int]: ...

class UnknownHostSecretsSection(ConfigurationError):
    hostname: str

    @classmethod
    def from_context(cls, hostname: str) -> UnknownHostSecretsSection: ...

class UnsatisfiedResources(ConfigurationError):
    unsatisfied_resources: list[tuple[str, str | None, list[str]]]

    @classmethod
    def from_context(cls, resources: Any) -> UnsatisfiedResources: ...

class UnusedComponentsInitialized(ConfigurationError):
    unused_components: list[str]
    breadcrumbs: list[list[str]]
    init_file_paths: list[str]
    init_line_numbers: list[int]
    root_name: str

    @classmethod
    def from_context(
        cls,
        components: list[Any],
        root: Any,
    ) -> UnusedComponentsInitialized: ...

class UnusedResources(ConfigurationError):
    unused_resources: list[tuple[str, str, str]]

    @classmethod
    def from_context(cls, resources: Any) -> UnusedResources: ...

class UpdateNeeded(AssertionError): ...
