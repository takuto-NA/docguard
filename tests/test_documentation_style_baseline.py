"""Baseline inventory for documentation style violations in this repository."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.documentation_style import (
    DocumentationStyleViolationKind,
    collect_documentation_style_candidates,
)
from docguard.rules import collect_documentation_style_candidates as collect_candidates_from_rules

MAXIMUM_FORBIDDEN_DOCUMENTATION_EXPRESSION_CANDIDATES = 0


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_documentation_style_contexts():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    return configuration, document_contexts


def count_candidates_by_kind(candidates) -> dict[DocumentationStyleViolationKind, int]:
    counts = {
        DocumentationStyleViolationKind.FORBIDDEN_DOCUMENTATION_EXPRESSION: 0,
    }
    for candidate in candidates:
        counts[candidate.kind] += 1
    return counts


def test_repository_documentation_style_baseline_is_documented() -> None:
    configuration, document_contexts = load_repository_documentation_style_contexts()
    candidates = collect_documentation_style_candidates(configuration, document_contexts)
    candidate_counts = count_candidates_by_kind(candidates)

    assert (
        candidate_counts[
            DocumentationStyleViolationKind.FORBIDDEN_DOCUMENTATION_EXPRESSION
        ]
        <= MAXIMUM_FORBIDDEN_DOCUMENTATION_EXPRESSION_CANDIDATES
    ), (
        "Forbidden documentation expression candidates: "
        f"{candidate_counts[DocumentationStyleViolationKind.FORBIDDEN_DOCUMENTATION_EXPRESSION]}"
    )


def test_rules_collect_documentation_style_candidates_matches_core() -> None:
    configuration, document_contexts = load_repository_documentation_style_contexts()
    core_candidates = collect_documentation_style_candidates(configuration, document_contexts)
    rules_candidates = collect_candidates_from_rules(configuration, document_contexts)
    assert core_candidates == rules_candidates
