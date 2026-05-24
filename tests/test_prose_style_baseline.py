"""Baseline inventory for prose style violations in this repository."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.prose_style import ProseStyleViolationKind, collect_prose_style_candidates
from docguard.rules import collect_prose_style_candidates as collect_candidates_from_rules

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


def count_candidates_by_kind(candidates) -> dict[ProseStyleViolationKind, int]:
    counts = {
        ProseStyleViolationKind.EXCESS_STRONG_EMPHASIS: 0,
        ProseStyleViolationKind.PROHIBITED_PROSE_PATTERN: 0,
    }
    for candidate in candidates:
        counts[candidate.kind] += 1
    return counts


def test_repository_prose_style_baseline_is_documented() -> None:
    configuration, document_contexts = load_repository_prose_style_contexts()
    candidates = collect_prose_style_candidates(configuration, document_contexts)
    candidate_counts = count_candidates_by_kind(candidates)

    assert (
        candidate_counts[ProseStyleViolationKind.EXCESS_STRONG_EMPHASIS]
        <= MAXIMUM_STRONG_EMPHASIS_CANDIDATES
    ), (
        "Strong emphasis candidates: "
        f"{candidate_counts[ProseStyleViolationKind.EXCESS_STRONG_EMPHASIS]}"
    )
    assert (
        candidate_counts[ProseStyleViolationKind.PROHIBITED_PROSE_PATTERN]
        <= MAXIMUM_PROHIBITED_PATTERN_CANDIDATES
    ), (
        "Prohibited pattern candidates: "
        f"{candidate_counts[ProseStyleViolationKind.PROHIBITED_PROSE_PATTERN]}"
    )


def test_rules_collect_prose_style_candidates_matches_core() -> None:
    configuration, document_contexts = load_repository_prose_style_contexts()
    core_candidates = collect_prose_style_candidates(configuration, document_contexts)
    rules_candidates = collect_candidates_from_rules(configuration, document_contexts)
    assert core_candidates == rules_candidates
