"""Reachability graph construction for index-linked Markdown documents."""

from __future__ import annotations

from docguard.config import resolve_configured_path
from docguard.markdown import resolve_markdown_link_target
from docguard.models import DocguardConfiguration, DocumentInspectionContext


def build_document_path_set(
    document_contexts: list[DocumentInspectionContext],
) -> set[str]:
    return {
        context.parsed_document.repository_relative_path
        for context in document_contexts
    }


def collect_reachable_documents(
    configuration: DocguardConfiguration,
    document_contexts: list[DocumentInspectionContext],
) -> set[str]:
    if not configuration.require_index_reachability:
        return build_document_path_set(document_contexts)

    in_scope_paths = build_document_path_set(document_contexts)
    reachable_paths: set[str] = set()
    pending_paths: list[str] = []

    for index_file in configuration.index_files:
        index_path = resolve_configured_path(
            configuration.project_root,
            index_file,
        )
        repository_relative_index_path = index_path.relative_to(
            configuration.project_root
        ).as_posix()
        if repository_relative_index_path in in_scope_paths:
            pending_paths.append(repository_relative_index_path)

    documents_by_path = {
        context.parsed_document.repository_relative_path: context
        for context in document_contexts
    }

    while pending_paths:
        current_path = pending_paths.pop()
        if current_path in reachable_paths:
            continue
        reachable_paths.add(current_path)
        current_context = documents_by_path.get(current_path)
        if current_context is None:
            continue
        for markdown_link in current_context.parsed_document.markdown_links:
            linked_path = resolve_markdown_link_target(
                current_path,
                markdown_link.target,
            )
            if linked_path not in in_scope_paths:
                continue
            if linked_path not in reachable_paths:
                pending_paths.append(linked_path)

    return reachable_paths
