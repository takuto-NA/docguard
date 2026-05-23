"""Rule implementations for docguard MVP diagnostics."""

from __future__ import annotations

from docguard.constants import (
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
    DIAGNOSTIC_CODE_SECTION_TOO_LONG,
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
    WHY_DOCUMENT_TOO_LONG,
    WHY_MISSING_FRONT_MATTER,
    WHY_MISSING_REQUIRED_HEADING,
    WHY_SECTION_TOO_LONG,
    WHY_UNREACHABLE_FROM_INDEX,
)
from docguard.diagnostics import Diagnostic, resolve_severity_for_code
from docguard.models import DocguardConfiguration, DocumentGraph, DocumentInspectionContext, MarkdownSection
from docguard.split import build_split_suggestion


def check_document_length(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> Diagnostic | None:
    parsed_document = inspection_context.parsed_document
    if parsed_document.physical_line_count <= inspection_context.max_document_lines:
        return None
    return Diagnostic(
        code=DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
        severity=resolve_severity_for_code(
            DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
            configuration.severities,
        ),
        document_path=parsed_document.repository_relative_path,
        message=(
            f"{parsed_document.repository_relative_path} has "
            f"{parsed_document.physical_line_count} lines. "
            f"Limit: {inspection_context.max_document_lines} lines."
        ),
        why_it_matters=WHY_DOCUMENT_TOO_LONG,
        suggestion=build_split_suggestion(parsed_document),
        document_type_name=(
            inspection_context.document_type.name
            if inspection_context.document_type is not None
            else None
        ),
    )


def should_check_section_length(
    sections: tuple[MarkdownSection, ...],
    section: MarkdownSection,
) -> bool:
    if section.heading is None:
        return True
    if section.heading.level != 1:
        return True
    has_lower_level_sections = any(
        candidate_section.heading is not None
        and candidate_section.heading.level > 1
        for candidate_section in sections
    )
    return not has_lower_level_sections


def check_section_lengths(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    parsed_document = inspection_context.parsed_document
    for section in parsed_document.sections:
        if not should_check_section_length(parsed_document.sections, section):
            continue
        if section.line_count <= inspection_context.max_section_lines:
            continue
        heading_label = (
            section.heading.text if section.heading is not None else "Document body"
        )
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_SECTION_TOO_LONG,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_SECTION_TOO_LONG,
                    configuration.severities,
                ),
                document_path=parsed_document.repository_relative_path,
                message=(
                    f"Section '{heading_label}' has {section.line_count} lines. "
                    f"Limit: {inspection_context.max_section_lines} lines."
                ),
                why_it_matters=WHY_SECTION_TOO_LONG,
                suggestion=(
                    f"Split '{heading_label}' into a dedicated document or smaller subsections."
                ),
                location=f"line {section.start_line_number}",
                document_type_name=(
                    inspection_context.document_type.name
                    if inspection_context.document_type is not None
                    else None
                ),
            )
        )
    return diagnostics


def check_required_headings(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    if inspection_context.document_type is None:
        return []

    diagnostics: list[Diagnostic] = []
    present_heading_texts = {
        heading.text for heading in inspection_context.parsed_document.headings
    }
    for required_heading in inspection_context.document_type.required_headings:
        if required_heading in present_heading_texts:
            continue
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
                    configuration.severities,
                ),
                document_path=inspection_context.parsed_document.repository_relative_path,
                message=f"Expected heading: ## {required_heading}",
                why_it_matters=WHY_MISSING_REQUIRED_HEADING,
                suggestion=f"Add a '## {required_heading}' section to this document.",
                document_type_name=inspection_context.document_type.name,
            )
        )
    return diagnostics


def check_required_front_matter(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    if inspection_context.document_type is None:
        return []
    if not inspection_context.document_type.required_front_matter_keys:
        return []

    diagnostics: list[Diagnostic] = []
    front_matter = inspection_context.parsed_document.front_matter
    if front_matter is None:
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
                    configuration.severities,
                ),
                document_path=inspection_context.parsed_document.repository_relative_path,
                message="Missing YAML front matter block.",
                why_it_matters=WHY_MISSING_FRONT_MATTER,
                suggestion="Add a YAML front matter block at the top of the document.",
                document_type_name=inspection_context.document_type.name,
            )
        )
        return diagnostics

    for required_key in inspection_context.document_type.required_front_matter_keys:
        if required_key in front_matter:
            continue
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
                    configuration.severities,
                ),
                document_path=inspection_context.parsed_document.repository_relative_path,
                message=f"Missing front matter key: {required_key}",
                why_it_matters=WHY_MISSING_FRONT_MATTER,
                suggestion=f"Add '{required_key}' to the YAML front matter block.",
                document_type_name=inspection_context.document_type.name,
            )
        )
    return diagnostics


def check_unreachable_from_index(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
    document_graph: DocumentGraph,
) -> Diagnostic | None:
    if not configuration.require_index_reachability:
        return None
    document_path = inspection_context.parsed_document.repository_relative_path
    if document_path in document_graph.reachable_paths:
        return None
    return Diagnostic(
        code=DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
        severity=resolve_severity_for_code(
            DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
            configuration.severities,
        ),
        document_path=document_path,
        message=f"{document_path} is not reachable from configured index files.",
        why_it_matters=WHY_UNREACHABLE_FROM_INDEX,
        suggestion="Link this document from an index file or another reachable document.",
        document_type_name=(
            inspection_context.document_type.name
            if inspection_context.document_type is not None
            else None
        ),
    )
