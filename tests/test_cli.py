"""Integration tests for the docguard CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.cli import main
from docguard.constants import (
    EXIT_CODE_CONFIGURATION_FAILURE,
    EXIT_CODE_DIAGNOSTIC_FAILURE,
    EXIT_CODE_SUCCESS,
)


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_cli_help_exits_successfully() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == EXIT_CODE_SUCCESS


def test_cli_reports_diagnostic_failure(
    temporary_project_directory: Path,
    monkeypatch,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "architecture.md").write_text(
        "\n".join(["# Architecture", ""] + ["line"] * 401),
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
    monkeypatch.chdir(temporary_project_directory)
    exit_code = main(["docs"])
    assert exit_code == EXIT_CODE_DIAGNOSTIC_FAILURE


def test_cli_configuration_error_exits_with_code_two(
    temporary_project_directory: Path,
    monkeypatch,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
unknown_key = true
""",
    )
    monkeypatch.chdir(temporary_project_directory)
    exit_code = main([])
    assert exit_code == EXIT_CODE_CONFIGURATION_FAILURE


def test_cli_json_output_exits_successfully_when_no_errors(
    temporary_project_directory: Path,
    monkeypatch,
    capsys,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Readme\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md"]
""",
    )
    monkeypatch.chdir(temporary_project_directory)
    exit_code = main(["--format", "json"])
    captured_output = capsys.readouterr()
    assert exit_code == EXIT_CODE_SUCCESS
    assert '"diagnostics"' in captured_output.out
