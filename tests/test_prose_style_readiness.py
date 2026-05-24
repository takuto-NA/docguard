"""Dogfood readiness gate tests for prose style diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.constants import (
    DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
    DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
)
from docguard.discovery import discover_documents
from docguard.prose_style import ProseStyleViolationKind
from docguard.rules import check_prose_style, collect_prose_style_candidates
from docguard.runner import run_docguard_checks

MAXIMUM_STRONG_EMPHASIS_CANDIDATES = 0
MAXIMUM_PROHIBITED_PATTERN_CANDIDATES = 0


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_prose_style_contexts():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    return configuration, document_contexts


def test_repository_strong_emphasis_candidates_are_zero() -> None:
    configuration, document_contexts = load_repository_prose_style_contexts()
    candidates = collect_prose_style_candidates(configuration, document_contexts)
    strong_emphasis_candidates = [
        candidate
        for candidate in candidates
        if candidate.kind is ProseStyleViolationKind.EXCESS_STRONG_EMPHASIS
    ]
    assert len(strong_emphasis_candidates) <= MAXIMUM_STRONG_EMPHASIS_CANDIDATES


def test_repository_prohibited_pattern_candidates_are_zero() -> None:
    configuration, document_contexts = load_repository_prose_style_contexts()
    candidates = collect_prose_style_candidates(configuration, document_contexts)
    prohibited_pattern_candidates = [
        candidate
        for candidate in candidates
        if candidate.kind is ProseStyleViolationKind.PROHIBITED_PROSE_PATTERN
    ]
    assert len(prohibited_pattern_candidates) <= MAXIMUM_PROHIBITED_PATTERN_CANDIDATES


def test_run_docguard_checks_has_no_prose_style_errors() -> None:
    configuration, _document_contexts = load_repository_prose_style_contexts()
    run_result = run_docguard_checks(configuration)
    prose_style_errors = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code
        in {
            DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
            DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
        }
        and diagnostic.severity.value == "error"
    ]
    assert prose_style_errors == []


def test_check_prose_style_returns_no_diagnostics_for_repository_documents() -> None:
    configuration, document_contexts = load_repository_prose_style_contexts()
    diagnostics = []
    for inspection_context in document_contexts:
        diagnostics.extend(check_prose_style(configuration, inspection_context))
    assert diagnostics == []
