"""Exception hierarchy and CLI exit codes.

The library raises typed exceptions; the CLI maps each to a stable exit code and a
structured ``{"error": {"code", "message"}}`` body (for ``--format json``). Exit
codes are part of the CLI's compatibility surface — see ``docs/cli.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class ExitCode(IntEnum):
    """Stable process exit codes for the CLI."""

    OK = 0
    ERROR = 1  # generic / unexpected
    USAGE = 2  # argparse usage error (argparse's own convention)
    NOT_FOUND = 3  # unknown id / no such reference
    INVALID_ARG = 4  # invalid filter, unsupported format, bad citation style
    SOURCE = 5  # unreachable source, malformed data, stale/missing cache


class NrdaxError(Exception):
    """Base class for every error this package raises deliberately."""

    #: Machine-readable code echoed in ``--format json`` error bodies.
    code: str = "internal"
    #: Exit code the CLI uses for this error class.
    exit_code: ExitCode = ExitCode.ERROR


class NotFoundError(NrdaxError):
    """An entity (technique id, reference) does not exist in the dataset."""

    code = "not_found"
    exit_code = ExitCode.NOT_FOUND


class InvalidArgumentError(NrdaxError):
    """A filter value, output format, or option is invalid."""

    code = "bad_request"
    exit_code = ExitCode.INVALID_ARG


class SourceError(NrdaxError):
    """A data source could not be loaded (network, missing file, bad cache)."""

    code = "source"
    exit_code = ExitCode.SOURCE


class DataFormatError(SourceError):
    """Loaded data was structurally malformed (bad JSON, wrong top-level shape)."""

    code = "malformed"


class SchemaVersionError(SourceError):
    """The data declares a schema/contract version this client cannot read."""

    code = "incompatible_schema"


@dataclass(frozen=True)
class ValidationIssue:
    """A single problem found while validating a record.

    Collected (not raised) during a lenient load so the whole dataset is never
    failed by one odd record. ``NRDAX.load(strict=True)`` raises on the first
    issue instead. ``locator`` points at the offending record/field so the
    *upstream* dataset can be corrected separately.
    """

    locator: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity}] {self.locator}: {self.message}"


class ValidationError(DataFormatError):
    """Raised in strict mode, carrying the collected issues."""

    def __init__(self, issues: list[ValidationIssue]):
        self.issues = issues
        super().__init__(
            f"{len(issues)} validation issue(s); first: {issues[0] if issues else 'none'}"
        )


@dataclass
class IssueCollector:
    """Accumulates :class:`ValidationIssue`s during a lenient load."""

    issues: list[ValidationIssue] = field(default_factory=list)
    strict: bool = False

    def add(self, locator: str, message: str, severity: str = "error") -> None:
        issue = ValidationIssue(locator=locator, message=message, severity=severity)
        self.issues.append(issue)
        if self.strict and severity == "error":
            raise ValidationError([issue])

    @property
    def errors(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]
