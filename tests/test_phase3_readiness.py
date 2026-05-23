"""Dogfood readiness gate tests for Phase 3 structure rules."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.rules import (
    collect_heading_skip_violations,
    collect_mixed_role_candidates,
)

MAXIMUM_MIXED_ROLE_CANDIDATES = 0
MAXIMUM_HEADING_SKIP_VIOLATIONS = 0

EXPECTED_MIXED_ROLE_CANDIDATES = frozenset()
EXPECTED_HEADING_SKIP_VIOLATIONS = frozenset()


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_phase3_contexts():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    phase3_configuration = replace(
        configuration,
        require_mixed_role_detection=True,
        require_heading_order_check=True,
    )
    document_contexts = discover_documents(configuration)
    return phase3_configuration, document_contexts


def test_repository_mixed_role_candidates_match_adr_expectations() -> None:
    phase3_configuration, document_contexts = load_repository_phase3_contexts()
    mixed_role_candidates = collect_mixed_role_candidates(
        phase3_configuration,
        document_contexts,
    )

    assert mixed_role_candidates == EXPECTED_MIXED_ROLE_CANDIDATES


def test_repository_heading_skip_violations_match_adr_expectations() -> None:
    phase3_configuration, document_contexts = load_repository_phase3_contexts()
    heading_skip_violations = collect_heading_skip_violations(
        phase3_configuration,
        document_contexts,
    )

    assert heading_skip_violations == EXPECTED_HEADING_SKIP_VIOLATIONS


def test_enabling_phase3_rules_would_not_mass_fail_dogfood() -> None:
    phase3_configuration, document_contexts = load_repository_phase3_contexts()
    mixed_role_candidates = collect_mixed_role_candidates(
        phase3_configuration,
        document_contexts,
    )
    heading_skip_violations = collect_heading_skip_violations(
        phase3_configuration,
        document_contexts,
    )

    assert len(mixed_role_candidates) <= MAXIMUM_MIXED_ROLE_CANDIDATES
    assert len(heading_skip_violations) <= MAXIMUM_HEADING_SKIP_VIOLATIONS
