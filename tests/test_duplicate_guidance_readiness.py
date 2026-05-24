"""Dogfood readiness gate tests for duplicate guidance detection."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.constants import DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE
from docguard.discovery import discover_documents
from docguard.rules import (
    check_duplicate_guidance,
    collect_duplicate_guidance_candidates,
)
from docguard.runner import run_docguard_checks


MAXIMUM_DUPLICATE_GUIDANCE_GROUPS = 0


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_duplicate_guidance_contexts():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    duplicate_guidance_configuration = replace(
        configuration,
        require_duplicate_guidance_detection=True,
    )
    document_contexts = discover_documents(configuration)
    return duplicate_guidance_configuration, document_contexts


def test_repository_duplicate_guidance_candidates_are_zero() -> None:
    duplicate_guidance_configuration, document_contexts = (
        load_repository_duplicate_guidance_contexts()
    )
    duplicate_guidance_groups = collect_duplicate_guidance_candidates(
        duplicate_guidance_configuration,
        document_contexts,
    )

    assert len(duplicate_guidance_groups) <= MAXIMUM_DUPLICATE_GUIDANCE_GROUPS


def test_repository_duplicate_guidance_diagnostics_are_zero_when_enabled() -> None:
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    duplicate_guidance_configuration = replace(
        configuration,
        require_duplicate_guidance_detection=True,
    )
    run_result = run_docguard_checks(duplicate_guidance_configuration)
    duplicate_guidance_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE
    ]

    assert duplicate_guidance_diagnostics == []


def test_duplicate_guidance_collector_is_noop_when_flag_disabled() -> None:
    duplicate_guidance_configuration, document_contexts = (
        load_repository_duplicate_guidance_contexts()
    )
    disabled_configuration = replace(
        duplicate_guidance_configuration,
        require_duplicate_guidance_detection=False,
    )

    assert collect_duplicate_guidance_candidates(
        disabled_configuration,
        document_contexts,
    ) == tuple()
    assert check_duplicate_guidance(disabled_configuration, document_contexts) == []
