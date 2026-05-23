"""Document discovery and ignore handling for docguard."""

from __future__ import annotations

from pathlib import Path

from docguard.config import (
    path_matches_any_glob,
    resolve_configured_path,
    resolve_document_type_for_path,
)
from docguard.constants import MARKDOWN_FILE_SUFFIX
from docguard.models import DocguardConfiguration, DocumentInspectionContext
from docguard.markdown import parse_markdown_document


def is_markdown_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() == MARKDOWN_FILE_SUFFIX


def collect_markdown_files_from_path(
    configured_path: Path,
) -> list[Path]:
    if configured_path.is_file():
        if is_markdown_file(configured_path):
            return [configured_path]
        return []

    if not configured_path.is_dir():
        return []

    discovered_files: list[Path] = []
    for candidate_path in configured_path.rglob("*"):
        if is_markdown_file(candidate_path):
            discovered_files.append(candidate_path)
    return discovered_files


def discover_documents(
    configuration: DocguardConfiguration,
) -> list[DocumentInspectionContext]:
    discovered_documents: dict[str, DocumentInspectionContext] = {}

    for configured_path_string in configuration.paths:
        configured_path = resolve_configured_path(
            configuration.project_root,
            configured_path_string,
        )
        if not configured_path.exists():
            continue
        for markdown_file_path in collect_markdown_files_from_path(configured_path):
            repository_relative_path = markdown_file_path.relative_to(
                configuration.project_root
            ).as_posix()
            if path_matches_any_glob(
                repository_relative_path,
                configuration.ignore_globs,
            ):
                continue
            document_type = resolve_document_type_for_path(
                repository_relative_path,
                configuration.document_types,
            )
            parsed_document = parse_markdown_document(
                markdown_file_path,
                repository_relative_path,
            )
            max_document_lines = configuration.max_document_lines
            max_section_lines = configuration.max_section_lines
            if document_type is not None:
                if document_type.max_document_lines is not None:
                    max_document_lines = document_type.max_document_lines
                if document_type.max_section_lines is not None:
                    max_section_lines = document_type.max_section_lines
            discovered_documents[repository_relative_path] = DocumentInspectionContext(
                parsed_document=parsed_document,
                document_type=document_type,
                max_document_lines=max_document_lines,
                max_section_lines=max_section_lines,
            )

    return sorted(
        discovered_documents.values(),
        key=lambda context: context.parsed_document.repository_relative_path,
    )
