"""Core runner that executes docguard rules and returns structured diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.constants import EXIT_CODE_CONFIGURATION_FAILURE
from docguard.diagnostics import Diagnostic, DiagnosticRunResult
from docguard.discovery import discover_documents
from docguard.graph import collect_reachable_documents
from docguard.models import DocguardConfiguration
from docguard.rules import (
    check_document_length,
    check_required_front_matter,
    check_required_headings,
    check_section_lengths,
    check_unreachable_from_index,
)


def run_docguard_checks(
    configuration: DocguardConfiguration,
) -> DiagnosticRunResult:
    document_contexts = discover_documents(configuration)
    reachable_document_paths = collect_reachable_documents(
        configuration,
        document_contexts,
    )

    diagnostics: list[Diagnostic] = []
    for inspection_context in document_contexts:
        document_length_diagnostic = check_document_length(
            configuration,
            inspection_context,
        )
        if document_length_diagnostic is not None:
            diagnostics.append(document_length_diagnostic)

        diagnostics.extend(
            check_section_lengths(configuration, inspection_context)
        )
        diagnostics.extend(
            check_required_headings(configuration, inspection_context)
        )
        diagnostics.extend(
            check_required_front_matter(configuration, inspection_context)
        )

        unreachable_diagnostic = check_unreachable_from_index(
            configuration,
            inspection_context,
            reachable_document_paths,
        )
        if unreachable_diagnostic is not None:
            diagnostics.append(unreachable_diagnostic)

    return DiagnosticRunResult(diagnostics=tuple(diagnostics))


def run_docguard_from_paths(
    project_root: Path,
    cli_paths: tuple[str, ...],
    config_path: Path | None = None,
) -> DiagnosticRunResult:
    try:
        configuration = load_docguard_configuration(
            project_root=project_root,
            config_path=config_path,
            cli_paths=cli_paths,
        )
    except ConfigurationError as error:
        raise DocguardConfigurationFailure(str(error)) from error
    return run_docguard_checks(configuration)


class DocguardConfigurationFailure(Exception):
    """Raised when configuration loading fails."""

    exit_code = EXIT_CODE_CONFIGURATION_FAILURE
