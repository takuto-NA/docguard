"""Rule implementations for docguard MVP diagnostics."""

from __future__ import annotations

from docguard.constants import (
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
    DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
    DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
    DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
    DIAGNOSTIC_CODE_ORPHAN_DOCUMENT,
    DIAGNOSTIC_CODE_SECTION_TOO_LONG,
    DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
    WHY_DOCUMENT_TOO_LONG,
    WHY_DUPLICATE_GUIDANCE,
    WHY_MISSING_FRONT_MATTER,
    WHY_MISSING_OUTGOING_LINKS,
    WHY_MISSING_REQUIRED_HEADING,
    WHY_MIXED_DOCUMENT_ROLES,
    WHY_ORPHAN_DOCUMENT,
    WHY_SECTION_TOO_LONG,
    WHY_UNEXPECTED_HEADING_ORDER,
    WHY_UNREACHABLE_FROM_INDEX,
    SUGGESTION_DUPLICATE_GUIDANCE,
    SUGGESTION_DUPLICATE_HEADING_GUIDANCE,
)
from docguard.diagnostics import Diagnostic, resolve_severity_for_code
from docguard.duplicate_guidance import (
    DuplicateGuidanceGroup,
    GuidanceAtomKind,
    collect_duplicate_guidance_groups,
    format_duplicate_occurrence_references,
)
from docguard.prose_style import (
    ProseStyleCandidate,
    check_prose_style as run_prose_style_checks,
    collect_prose_style_candidates as collect_prose_style_candidate_groups,
)
from docguard.graph import (
    collect_hub_outgoing_violations,
    collect_orphan_candidates,
    resolve_hub_document_paths,
    resolve_index_path_in_scope,
)
from docguard.models import DocguardConfiguration, DocumentGraph, DocumentInspectionContext, MarkdownSection
from docguard.heading_order import find_heading_level_skips
from docguard.role_families import RoleFamily, detect_mixed_role_families
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


def check_heading_level_skips(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    if not configuration.require_heading_order_check:
        return []

    parsed_document = inspection_context.parsed_document
    diagnostics: list[Diagnostic] = []
    for violation in find_heading_level_skips(parsed_document.headings):
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
                    configuration.severities,
                ),
                document_path=parsed_document.repository_relative_path,
                message=(
                    f"Heading '{violation.heading_text}' at line "
                    f"{violation.line_number} skips from H"
                    f"{violation.previous_level} to H{violation.current_level}."
                ),
                why_it_matters=WHY_UNEXPECTED_HEADING_ORDER,
                suggestion=(
                    f"Insert intermediate heading levels between H"
                    f"{violation.previous_level} and H{violation.current_level}, "
                    f"or restructure this section."
                ),
                location=f"line {violation.line_number}",
                document_type_name=(
                    inspection_context.document_type.name
                    if inspection_context.document_type is not None
                    else None
                ),
            )
        )
    return diagnostics


def format_role_family_names(role_families: frozenset[RoleFamily]) -> str:
    return ", ".join(
        sorted(role_family.value for role_family in role_families)
    )


def check_mixed_document_roles(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> Diagnostic | None:
    if not configuration.require_mixed_role_detection:
        return None
    if inspection_context.document_type is not None:
        return None

    parsed_document = inspection_context.parsed_document
    mixed_role_families = detect_mixed_role_families(parsed_document.headings)
    if len(mixed_role_families) < 2:
        return None

    family_names = format_role_family_names(mixed_role_families)
    return Diagnostic(
        code=DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
        severity=resolve_severity_for_code(
            DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
            configuration.severities,
        ),
        document_path=parsed_document.repository_relative_path,
        message=(
            f"{parsed_document.repository_relative_path} may mix document roles: "
            f"{family_names}."
        ),
        why_it_matters=WHY_MIXED_DOCUMENT_ROLES,
        suggestion=build_split_suggestion(parsed_document),
    )


def resolve_in_scope_index_paths(
    configuration: DocguardConfiguration,
    document_graph: DocumentGraph,
) -> frozenset[str]:
    in_scope_index_paths: set[str] = set()
    for index_file in configuration.index_files:
        index_path_in_scope = resolve_index_path_in_scope(
            configuration,
            index_file,
            set(document_graph.document_paths),
        )
        if index_path_in_scope is None:
            continue
        in_scope_index_paths.add(index_path_in_scope)
    return frozenset(in_scope_index_paths)


def check_orphan_documents(
    configuration: DocguardConfiguration,
    document_graph: DocumentGraph,
) -> list[Diagnostic]:
    if not configuration.require_orphan_detection:
        return []

    excluded_index_paths = resolve_in_scope_index_paths(
        configuration,
        document_graph,
    )
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=excluded_index_paths,
    )
    diagnostics: list[Diagnostic] = []
    for orphan_document_path in sorted(orphan_candidates):
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_ORPHAN_DOCUMENT,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_ORPHAN_DOCUMENT,
                    configuration.severities,
                ),
                document_path=orphan_document_path,
                message=(
                    f"{orphan_document_path} has no incoming links from other "
                    "in-scope Markdown documents."
                ),
                why_it_matters=WHY_ORPHAN_DOCUMENT,
                suggestion=(
                    "Link to this document from another in-scope Markdown document."
                ),
            )
        )
    return diagnostics


def check_hub_missing_outgoing_links(
    configuration: DocguardConfiguration,
    document_graph: DocumentGraph,
) -> list[Diagnostic]:
    if not configuration.require_hub_outgoing_links:
        return []

    in_scope_index_paths = resolve_in_scope_index_paths(
        configuration,
        document_graph,
    )
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=in_scope_index_paths,
        hub_glob_patterns=frozenset(configuration.hub_globs),
    )
    if not hub_document_paths:
        return []

    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )
    diagnostics: list[Diagnostic] = []
    for hub_document_path in sorted(hub_outgoing_violations):
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
                    configuration.severities,
                ),
                document_path=hub_document_path,
                message=(
                    f"{hub_document_path} has no outgoing links to other "
                    "in-scope Markdown documents."
                ),
                why_it_matters=WHY_MISSING_OUTGOING_LINKS,
                suggestion=(
                    "Add relative Markdown links from this hub document to other "
                    "in-scope documents."
                ),
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


def collect_mixed_role_candidates(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> frozenset[str]:
    if not configuration.require_mixed_role_detection:
        return frozenset()

    mixed_role_candidates: set[str] = set()
    for inspection_context in document_contexts:
        if inspection_context.document_type is not None:
            continue
        mixed_role_families = detect_mixed_role_families(
            inspection_context.parsed_document.headings
        )
        if len(mixed_role_families) < 2:
            continue
        mixed_role_candidates.add(
            inspection_context.parsed_document.repository_relative_path
        )
    return frozenset(mixed_role_candidates)


def collect_heading_skip_violations(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> frozenset[tuple[str, int]]:
    if not configuration.require_heading_order_check:
        return frozenset()

    heading_skip_violations: set[tuple[str, int]] = set()
    for inspection_context in document_contexts:
        document_path = inspection_context.parsed_document.repository_relative_path
        for violation in find_heading_level_skips(
            inspection_context.parsed_document.headings
        ):
            heading_skip_violations.add((document_path, violation.line_number))
    return frozenset(heading_skip_violations)


def resolve_duplicate_guidance_suggestion(
    duplicate_group: DuplicateGuidanceGroup,
) -> str:
    if duplicate_group.kind is GuidanceAtomKind.HEADING:
        return SUGGESTION_DUPLICATE_HEADING_GUIDANCE
    return SUGGESTION_DUPLICATE_GUIDANCE


def check_duplicate_guidance(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> list[Diagnostic]:
    if not configuration.require_duplicate_guidance_detection:
        return []

    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        configuration.allowed_duplicate_patterns,
        configuration.duplicate_guidance_kinds,
    )
    diagnostics: list[Diagnostic] = []
    for duplicate_group in duplicate_groups:
        primary_atom = duplicate_group.atoms[0]
        occurrence_references = format_duplicate_occurrence_references(
            duplicate_group
        )
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
                    configuration.severities,
                ),
                document_path=primary_atom.document_path,
                message=(
                    f"Duplicate {duplicate_group.kind.value} guidance appears "
                    f"{len(duplicate_group.atoms)} times "
                    f"({occurrence_references})."
                ),
                why_it_matters=WHY_DUPLICATE_GUIDANCE,
                suggestion=resolve_duplicate_guidance_suggestion(duplicate_group),
                location=f"line {primary_atom.line_number}",
            )
        )
    return diagnostics


def collect_duplicate_guidance_candidates(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> tuple[DuplicateGuidanceGroup, ...]:
    if not configuration.require_duplicate_guidance_detection:
        return tuple()
    return collect_duplicate_guidance_groups(
        document_contexts,
        configuration.allowed_duplicate_patterns,
        configuration.duplicate_guidance_kinds,
    )


def check_prose_style(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    return run_prose_style_checks(configuration, inspection_context)


def collect_prose_style_candidates(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> tuple[ProseStyleCandidate, ...]:
    return collect_prose_style_candidate_groups(configuration, document_contexts)
