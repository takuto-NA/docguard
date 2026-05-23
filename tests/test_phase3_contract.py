"""Phase 3 structure rule contract tests and candidate helper acceptance tests."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from docguard.config import load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.rules import (
    collect_heading_skip_violations,
    collect_mixed_role_candidates,
)


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_mixed_role_candidate_has_two_or_more_role_families(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "mixed.md").write_text(
        """## Overview

Overview text.

## Deployment

Deployment text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    mixed_role_candidates = collect_mixed_role_candidates(
        configuration,
        document_contexts,
    )

    assert mixed_role_candidates == frozenset({"docs/mixed.md"})


def test_typed_document_is_not_mixed_role_candidate(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """---
status: accepted
date: 2026-05-24
---

# Example

## Status
Accepted

## Context
Context text.

## Decision
Decision text.

## Consequences
Consequence text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs/adr"]
require_mixed_role_detection = true

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    mixed_role_candidates = collect_mixed_role_candidates(
        configuration,
        document_contexts,
    )

    assert mixed_role_candidates == frozenset()


def test_heading_skip_candidate_records_path_and_line(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "skip.md").write_text(
        """## Section

#### Deep
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_heading_order_check = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    heading_skip_violations = collect_heading_skip_violations(
        configuration,
        document_contexts,
    )

    assert heading_skip_violations == frozenset({("docs/skip.md", 3)})


def test_phase3_collectors_are_noop_when_flags_disabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "mixed.md").write_text(
        """## Overview

## Deployment
""",
        encoding="utf-8",
    )
    (docs_directory / "skip.md").write_text(
        """## Section

#### Deep
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = false
require_heading_order_check = false
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    phase3_enabled_configuration = replace(
        configuration,
        require_mixed_role_detection=True,
        require_heading_order_check=True,
    )

    assert collect_mixed_role_candidates(configuration, document_contexts) == frozenset()
    assert collect_heading_skip_violations(configuration, document_contexts) == frozenset()
    assert collect_mixed_role_candidates(
        phase3_enabled_configuration,
        document_contexts,
    ) == frozenset({"docs/mixed.md"})
    assert collect_heading_skip_violations(
        phase3_enabled_configuration,
        document_contexts,
    ) == frozenset({("docs/skip.md", 3)})
