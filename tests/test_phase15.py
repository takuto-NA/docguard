"""Phase 1.5 reproduction and acceptance tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from docguard.cli import main
from docguard.config import load_docguard_configuration
from docguard.constants import (
    EXIT_CODE_CONFIGURATION_FAILURE,
    EXIT_CODE_SUCCESS,
)
from docguard.runner import run_docguard_checks

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def build_subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    source_directory = str(REPOSITORY_ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH", "")
    if existing_pythonpath:
        environment["PYTHONPATH"] = f"{source_directory}{os.pathsep}{existing_pythonpath}"
    else:
        environment["PYTHONPATH"] = source_directory
    return environment


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_cli_summary_prints_checked_document_count_on_success(
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
    exit_code = main(["--summary"])
    captured_output = capsys.readouterr()
    assert exit_code == EXIT_CODE_SUCCESS
    assert "Checked 1 documents." in captured_output.out
    assert "Found 0 diagnostics." in captured_output.out


def test_cli_summary_does_not_print_when_json_format_is_selected(
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
    exit_code = main(["--summary", "--format", "json"])
    captured_output = capsys.readouterr()
    parsed_output = json.loads(captured_output.out)
    assert exit_code == EXIT_CODE_SUCCESS
    assert parsed_output["diagnostics"] == []
    assert "Checked" not in captured_output.out


def test_cli_default_success_output_remains_quiet(
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
    exit_code = main([])
    captured_output = capsys.readouterr()
    assert exit_code == EXIT_CODE_SUCCESS
    assert captured_output.out == ""


def test_cli_out_of_project_path_exits_with_configuration_error(
    temporary_project_directory: Path,
    monkeypatch,
    capsys,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    outside_file = temporary_project_directory.parent / "outside.md"
    outside_file.write_text("# Outside\n", encoding="utf-8")
    monkeypatch.chdir(temporary_project_directory)
    exit_code = main([str(outside_file)])
    captured_output = capsys.readouterr()
    assert exit_code == EXIT_CODE_CONFIGURATION_FAILURE
    assert "outside project root" in captured_output.err.lower()


def test_cli_missing_explicit_path_exits_with_configuration_error(
    temporary_project_directory: Path,
    monkeypatch,
    capsys,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    monkeypatch.chdir(temporary_project_directory)
    exit_code = main(["docs/missing.md"])
    captured_output = capsys.readouterr()
    assert exit_code == EXIT_CODE_CONFIGURATION_FAILURE
    assert "not found" in captured_output.err.lower()


def test_document_title_section_is_not_checked_when_lower_sections_exist(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    section_body = "\n".join(["detail"] * 50)
    (docs_directory / "readme-style.md").write_text(
        "\n".join(
            [
                "# Project",
                "",
                "## Overview",
                section_body,
                "",
                "## Setup",
                section_body,
            ]
        ),
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
        if "Project" in diagnostic.message
    ]
    assert section_diagnostics == []


def test_document_title_section_is_checked_when_no_lower_sections_exist(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    section_body = "\n".join(["detail"] * 121)
    (docs_directory / "single-section.md").write_text(
        f"# Only Title\n\n{section_body}\n",
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
        if diagnostic.code == "DG-SIZE002"
    ]
    assert len(section_diagnostics) == 1
    assert "Only Title" in section_diagnostics[0].message


def test_pytest_docguard_only_runs_docguard_items(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    tests_directory = temporary_project_directory / "tests"
    tests_directory.mkdir()
    (tests_directory / "test_example.py").write_text(
        "def test_example():\n    assert True\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.docguard]
paths = ["docs"]
""",
    )
    completed_process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--docguard-only",
            "--collect-only",
            "-q",
        ],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
        env=build_subprocess_environment(),
    )
    assert completed_process.returncode == EXIT_CODE_SUCCESS
    assert "docs/design.md::docguard" in completed_process.stdout
    assert "test_example" not in completed_process.stdout
