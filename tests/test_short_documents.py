"""Tests for short untyped document detection."""

from __future__ import annotations

from pathlib import Path

from docguard.config import load_docguard_configuration
from docguard.constants import DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT
from docguard.diagnostics import Diagnostic
from docguard.runner import run_docguard_checks


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def write_lines(markdown_file_path: Path, line_count: int) -> None:
    markdown_file_path.write_text(
        "\n".join(f"line {line_number}" for line_number in range(1, line_count + 1)),
        encoding="utf-8",
    )


def diagnostics_by_code(run_result, diagnostic_code: str) -> list[Diagnostic]:
    return [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == diagnostic_code
    ]


def write_short_document_project(project_root: Path) -> Path:
    docs_directory = project_root / "docs"
    docs_directory.mkdir()
    write_pyproject(
        project_root,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.relaxations]]
parameter = "require_index_reachability"
value = false
reason = "Focused rule test does not define repository navigation."
""",
    )
    return docs_directory


def test_untyped_document_below_floor_reports_size003(
    temporary_project_directory: Path,
) -> None:
    docs_directory = write_short_document_project(temporary_project_directory)
    write_lines(docs_directory / "stub.md", 19)
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    size003_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT,
    )
    assert len(size003_diagnostics) == 1
    assert size003_diagnostics[0].document_path == "docs/stub.md"


def test_untyped_document_at_floor_passes(
    temporary_project_directory: Path,
) -> None:
    docs_directory = write_short_document_project(temporary_project_directory)
    write_lines(docs_directory / "guide.md", 20)
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert diagnostics_by_code(run_result, DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT) == []


def test_typed_document_below_floor_is_excluded(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """---
status: accepted
date: 2026-05-28
---

# Example

## Status
Accepted.
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
required_headings = ["Status"]
required_front_matter_keys = ["status", "date"]

[[tool.docguard.relaxations]]
parameter = "require_index_reachability"
value = false
reason = "Focused typed document test does not define repository navigation."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert diagnostics_by_code(run_result, DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT) == []


def test_index_file_below_floor_is_excluded(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md"]
index_files = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert diagnostics_by_code(run_result, DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT) == []


def test_min_document_lines_relaxation_changes_floor(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    write_lines(docs_directory / "legacy-note.md", 12)
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.relaxations]]
parameter = "require_index_reachability"
value = false
reason = "Focused rule test does not define repository navigation."

[[tool.docguard.relaxations]]
parameter = "min_document_lines"
value = 10
reason = "Legacy notes are being merged over a temporary migration window."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert diagnostics_by_code(run_result, DIAGNOSTIC_CODE_DOCUMENT_TOO_SHORT) == []
