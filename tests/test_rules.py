"""Tests for docguard MVP rule diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import load_docguard_configuration
from docguard.constants import (
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
    DIAGNOSTIC_CODE_SECTION_TOO_LONG,
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
    EXIT_CODE_SUCCESS,
)
from docguard.diagnostics import Diagnostic, SeverityLevel, resolve_exit_code_from_diagnostics
from docguard.runner import run_docguard_checks


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_document_too_long_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    long_lines = "\n".join(["line"] * 401)
    (docs_directory / "architecture.md").write_text(
        f"# Architecture\n\n{long_lines}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_document_lines = 400
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG in diagnostic_codes


def test_missing_required_heading_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """---
status: accepted
date: 2026-05-23
---

# Example

## Status
Accepted

## Context
Context text.

## Decision
Decision text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs/adr"]

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
    run_result = run_docguard_checks(configuration)
    missing_heading_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING
    ]
    assert len(missing_heading_diagnostics) == 1
    assert "Consequences" in missing_heading_diagnostics[0].message


def test_unreachable_from_index_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "hidden.md").write_text("# Hidden\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_index_reachability = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    unreachable_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX
    ]
    assert len(unreachable_diagnostics) == 1
    assert unreachable_diagnostics[0].document_path == "docs/hidden.md"


def test_section_too_long_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    section_body = "\n".join(["detail"] * 121)
    (docs_directory / "design.md").write_text(
        f"## Architecture\n{section_body}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_section_lines = 120
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    section_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_SECTION_TOO_LONG
    ]
    assert len(section_diagnostics) == 1


def test_missing_front_matter_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """# Example

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
    run_result = run_docguard_checks(configuration)
    front_matter_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_MISSING_FRONT_MATTER
    ]
    assert len(front_matter_diagnostics) == 1


def test_warning_severity_does_not_fail_run(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    long_lines = "\n".join(["line"] * 401)
    (docs_directory / "architecture.md").write_text(
        f"{long_lines}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_document_lines = 400

[tool.docguard.severity]
DG-SIZE001 = "warning"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert len(run_result.diagnostics) == 1
    assert run_result.diagnostics[0].severity is SeverityLevel.WARNING
    assert resolve_exit_code_from_diagnostics(run_result.diagnostics) == EXIT_CODE_SUCCESS
