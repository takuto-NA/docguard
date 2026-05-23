"""Document graph construction for link and reachability analysis."""

from __future__ import annotations

from docguard.config import ConfigurationError, resolve_configured_path
from docguard.markdown import resolve_markdown_link_target
from docguard.models import (
    DocguardConfiguration,
    DocumentGraph,
    DocumentInspectionContext,
)


def build_document_path_set(
    document_contexts: list[DocumentInspectionContext],
) -> set[str]:
    return {
        context.parsed_document.repository_relative_path
        for context in document_contexts
    }


def build_outgoing_links(
    document_contexts: list[DocumentInspectionContext],
    in_scope_paths: set[str],
) -> dict[str, frozenset[str]]:
    outgoing_links: dict[str, set[str]] = {
        document_path: set() for document_path in in_scope_paths
    }
    for inspection_context in document_contexts:
        source_path = inspection_context.parsed_document.repository_relative_path
        linked_paths: set[str] = set()
        for markdown_link in inspection_context.parsed_document.markdown_links:
            linked_path = resolve_markdown_link_target(
                source_path,
                markdown_link.target,
            )
            if linked_path in in_scope_paths:
                linked_paths.add(linked_path)
        outgoing_links[source_path] = linked_paths
    return {
        document_path: frozenset(linked_targets)
        for document_path, linked_targets in outgoing_links.items()
    }


def build_incoming_links(
    outgoing_links: dict[str, frozenset[str]],
    in_scope_paths: set[str],
) -> dict[str, frozenset[str]]:
    incoming_links: dict[str, set[str]] = {
        document_path: set() for document_path in in_scope_paths
    }
    for source_path, linked_targets in outgoing_links.items():
        for linked_target in linked_targets:
            incoming_links[linked_target].add(source_path)
    return {
        document_path: frozenset(source_paths)
        for document_path, source_paths in incoming_links.items()
    }


def resolve_index_path_in_scope(
    configuration: DocguardConfiguration,
    index_file: str,
    in_scope_paths: set[str],
) -> str | None:
    index_path = resolve_configured_path(
        configuration.project_root,
        index_file,
    )
    resolved_project_root = configuration.project_root.resolve()
    try:
        repository_relative_index_path = index_path.relative_to(
            resolved_project_root
        ).as_posix()
    except ValueError as error:
        raise ConfigurationError(
            f"Index file is outside project root: {index_file}"
        ) from error
    if repository_relative_index_path not in in_scope_paths:
        return None
    return repository_relative_index_path


def collect_reachable_document_paths(
    configuration: DocguardConfiguration,
    document_contexts: list[DocumentInspectionContext],
    in_scope_paths: set[str],
    outgoing_links: dict[str, frozenset[str]],
) -> frozenset[str]:
    if not configuration.require_index_reachability:
        return frozenset(in_scope_paths)

    if not configuration.index_files:
        raise ConfigurationError(
            "require_index_reachability is true but index_files is empty."
        )

    pending_paths: list[str] = []
    for index_file in configuration.index_files:
        index_path_in_scope = resolve_index_path_in_scope(
            configuration,
            index_file,
            in_scope_paths,
        )
        if index_path_in_scope is not None:
            pending_paths.append(index_path_in_scope)

    if not pending_paths:
        raise ConfigurationError(
            "No configured index_files are within the scanned document scope."
        )

    reachable_paths: set[str] = set()

    while pending_paths:
        current_path = pending_paths.pop()
        if current_path in reachable_paths:
            continue
        reachable_paths.add(current_path)
        for linked_path in outgoing_links.get(current_path, frozenset()):
            if linked_path not in reachable_paths:
                pending_paths.append(linked_path)

    return frozenset(reachable_paths)


def build_document_graph(
    configuration: DocguardConfiguration,
    document_contexts: list[DocumentInspectionContext],
) -> DocumentGraph:
    in_scope_paths = build_document_path_set(document_contexts)
    outgoing_links = build_outgoing_links(document_contexts, in_scope_paths)
    incoming_links = build_incoming_links(outgoing_links, in_scope_paths)
    reachable_paths = collect_reachable_document_paths(
        configuration,
        document_contexts,
        in_scope_paths,
        outgoing_links,
    )
    return DocumentGraph(
        document_paths=frozenset(in_scope_paths),
        outgoing_links=outgoing_links,
        incoming_links=incoming_links,
        reachable_paths=reachable_paths,
    )
