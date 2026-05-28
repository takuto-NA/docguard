"""Core runner that executes docguard rules and returns structured diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.constants import EXIT_CODE_CONFIGURATION_FAILURE
from docguard.diagnostics import Diagnostic, DiagnosticRunResult
from docguard.diagnostics import DiagnosticPolicySummary
from docguard.discovery import discover_documents
from docguard.graph import build_document_graph
from docguard.models import DocguardConfiguration
from docguard.rules import (
    check_document_length,
    check_document_minimum_length,
    check_duplicate_guidance,
    check_documentation_style,
    check_heading_level_skips,
    check_hub_missing_outgoing_links,
    check_mixed_document_roles,
    check_orphan_documents,
    check_prose_style,
    check_required_front_matter,
    check_required_headings,
    check_section_lengths,
    check_unreachable_from_index,
)


def run_docguard_checks(
    configuration: DocguardConfiguration,
) -> DiagnosticRunResult:
    try:
        document_contexts = discover_documents(configuration)
    except ConfigurationError as error:
        raise DocguardConfigurationFailure(str(error)) from error
    try:
        document_graph = build_document_graph(configuration, document_contexts)
    except ConfigurationError as error:
        raise DocguardConfigurationFailure(str(error)) from error

    diagnostics: list[Diagnostic] = []
    for inspection_context in document_contexts:
        document_minimum_length_diagnostic = check_document_minimum_length(
            configuration,
            inspection_context,
        )
        if document_minimum_length_diagnostic is not None:
            diagnostics.append(document_minimum_length_diagnostic)

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
        diagnostics.extend(
            check_heading_level_skips(configuration, inspection_context)
        )
        diagnostics.extend(
            check_prose_style(configuration, inspection_context)
        )
        diagnostics.extend(
            check_documentation_style(configuration, inspection_context)
        )
        mixed_roles_diagnostic = check_mixed_document_roles(
            configuration,
            inspection_context,
        )
        if mixed_roles_diagnostic is not None:
            diagnostics.append(mixed_roles_diagnostic)

        unreachable_diagnostic = check_unreachable_from_index(
            configuration,
            inspection_context,
            document_graph,
        )
        if unreachable_diagnostic is not None:
            diagnostics.append(unreachable_diagnostic)

    diagnostics.extend(check_orphan_documents(configuration, document_graph))
    diagnostics.extend(check_hub_missing_outgoing_links(configuration, document_graph))
    diagnostics.extend(check_duplicate_guidance(configuration, document_contexts))

    checked_document_paths = tuple(
        context.parsed_document.repository_relative_path
        for context in document_contexts
    )
    return DiagnosticRunResult(
        diagnostics=tuple(diagnostics),
        checked_document_count=len(document_contexts),
        checked_document_paths=checked_document_paths,
        policy_summary=DiagnosticPolicySummary(
            name=configuration.policy_name,
            max_document_lines=configuration.max_document_lines,
            min_document_lines=configuration.min_document_lines,
            max_section_lines=configuration.max_section_lines,
            require_index_reachability=configuration.require_index_reachability,
            require_duplicate_guidance_detection=(
                configuration.require_duplicate_guidance_detection
            ),
            relaxation_count=configuration.relaxation_count,
        ),
    )


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
