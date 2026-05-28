"""Dogfood readiness gate tests for documentation style diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.constants import DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
from docguard.discovery import discover_documents
from docguard.documentation_style import (
    DocumentationStyleViolationKind,
    collect_documentation_style_candidates,
)
from docguard.rules import (
    check_documentation_style,
    collect_documentation_style_candidates as collect_rules_documentation_style_candidates,
)
from docguard.runner import run_docguard_checks

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


def test_repository_forbidden_documentation_expression_candidates_are_zero() -> None:
    configuration, document_contexts = load_repository_documentation_style_contexts()
    candidates = collect_documentation_style_candidates(configuration, document_contexts)
    forbidden_expression_candidates = [
        candidate
        for candidate in candidates
        if candidate.kind is DocumentationStyleViolationKind.FORBIDDEN_DOCUMENTATION_EXPRESSION
    ]
    assert (
        len(forbidden_expression_candidates)
        <= MAXIMUM_FORBIDDEN_DOCUMENTATION_EXPRESSION_CANDIDATES
    )


def test_run_docguard_checks_has_no_documentation_style_errors() -> None:
    configuration, _document_contexts = load_repository_documentation_style_contexts()
    run_result = run_docguard_checks(configuration)
    documentation_style_errors = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
        and diagnostic.severity.value == "error"
    ]
    assert documentation_style_errors == []


def test_check_documentation_style_returns_no_diagnostics_for_repository_documents() -> None:
    configuration, document_contexts = load_repository_documentation_style_contexts()
    diagnostics = []
    for inspection_context in document_contexts:
        diagnostics.extend(check_documentation_style(configuration, inspection_context))
    assert diagnostics == []


def test_rules_collect_documentation_style_candidates_matches_core() -> None:
    configuration, document_contexts = load_repository_documentation_style_contexts()
    core_candidates = collect_documentation_style_candidates(configuration, document_contexts)
    rules_candidates = collect_rules_documentation_style_candidates(
        configuration,
        document_contexts,
    )
    assert core_candidates == rules_candidates
