"""Dogfood gate tests for repository documentation budget immutability."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents

# Fixed repository dogfood ceiling (ADR 0006). Intentionally not tied to
# DEFAULT_MAX_DOCUMENT_LINES so product default changes cannot weaken this gate.
REPOSITORY_GLOBAL_DOCUMENT_BUDGET_LINES = 300
REPOSITORY_UNTYPED_DOCUMENT_FLOOR_LINES = 20


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_document_contexts():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    return configuration, document_contexts


def resolve_max_document_lines_for_context(
    inspection_context,
) -> int:
    if inspection_context.document_type is not None:
        document_type_max_lines = inspection_context.document_type.max_document_lines
        if document_type_max_lines is not None:
            return document_type_max_lines
    return inspection_context.max_document_lines


def test_repository_global_document_budget_is_not_inflated() -> None:
    configuration, _document_contexts = load_repository_document_contexts()

    assert configuration.max_document_lines <= REPOSITORY_GLOBAL_DOCUMENT_BUDGET_LINES


def test_in_scope_documents_respect_configured_budgets() -> None:
    _configuration, document_contexts = load_repository_document_contexts()

    budget_violations: list[str] = []
    for inspection_context in document_contexts:
        document_path = inspection_context.parsed_document.repository_relative_path
        physical_line_count = inspection_context.parsed_document.physical_line_count
        configured_budget = resolve_max_document_lines_for_context(inspection_context)
        if physical_line_count <= configured_budget:
            continue
        budget_violations.append(
            f"{document_path}: {physical_line_count} lines exceeds budget {configured_budget}"
        )

    assert budget_violations == []


def test_untyped_in_scope_documents_respect_document_floor() -> None:
    configuration, document_contexts = load_repository_document_contexts()
    index_files = set(configuration.index_files)

    floor_violations: list[str] = []
    for inspection_context in document_contexts:
        if inspection_context.document_type is not None:
            continue
        document_path = inspection_context.parsed_document.repository_relative_path
        if document_path in index_files:
            continue
        physical_line_count = inspection_context.parsed_document.physical_line_count
        if physical_line_count >= REPOSITORY_UNTYPED_DOCUMENT_FLOOR_LINES:
            continue
        floor_violations.append(
            f"{document_path}: {physical_line_count} lines below floor "
            f"{REPOSITORY_UNTYPED_DOCUMENT_FLOOR_LINES}"
        )

    assert floor_violations == []
