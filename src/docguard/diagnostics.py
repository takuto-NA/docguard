"""Diagnostic data models and severity handling for docguard."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence

from docguard.constants import DEFAULT_SEVERITIES


class SeverityLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    EXPERIMENTAL = "experimental"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    severity: SeverityLevel
    document_path: str
    message: str
    why_it_matters: str
    suggestion: str | None = None
    location: str | None = None
    document_type_name: str | None = None


@dataclass(frozen=True)
class DiagnosticRunResult:
    diagnostics: tuple[Diagnostic, ...] = field(default_factory=tuple)
    checked_document_count: int = 0
    checked_document_paths: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_error_severity(self) -> bool:
        return any(
            diagnostic.severity is SeverityLevel.ERROR
            for diagnostic in self.diagnostics
        )


def parse_severity_level(raw_severity: str) -> SeverityLevel:
    normalized_severity = raw_severity.strip().lower()
    try:
        return SeverityLevel(normalized_severity)
    except ValueError as error:
        raise ValueError(f"Unsupported severity value: {raw_severity}") from error


def resolve_severity_for_code(
    diagnostic_code: str,
    configured_severities: dict[str, str],
) -> SeverityLevel:
    raw_severity = configured_severities.get(
        diagnostic_code,
        DEFAULT_SEVERITIES.get(diagnostic_code, "error"),
    )
    return parse_severity_level(raw_severity)


def resolve_exit_code_from_diagnostics(
    diagnostics: Sequence[Diagnostic],
) -> int:
    from docguard.constants import (
        EXIT_CODE_DIAGNOSTIC_FAILURE,
        EXIT_CODE_SUCCESS,
    )

    if any(diagnostic.severity is SeverityLevel.ERROR for diagnostic in diagnostics):
        return EXIT_CODE_DIAGNOSTIC_FAILURE
    return EXIT_CODE_SUCCESS
