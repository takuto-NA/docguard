"""Self-test coverage for this repository's own docguard configuration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from docguard.cli import main as docguard_main
from docguard.config import find_project_root
from docguard.constants import EXIT_CODE_SUCCESS
from docguard.diagnostics import resolve_exit_code_from_diagnostics
from docguard.runner import run_docguard_from_paths

SELF_TEST_SUBPROCESS_ENVIRONMENT_VARIABLE = "DOCGUARD_SELF_TEST_SUBPROCESS"
REPOSITORY_DOCUMENTATION_PATHS = (
    "README.md",
    "CONTEXT.md",
    "docs",
)


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def test_repository_documentation_passes_docguard_runner() -> None:
    project_root = resolve_repository_root()
    run_result = run_docguard_from_paths(
        project_root=project_root,
        cli_paths=tuple(),
    )
    error_diagnostics = [
        f"{diagnostic.document_path}: {diagnostic.code} {diagnostic.message}"
        for diagnostic in run_result.diagnostics
        if diagnostic.severity.value == "error"
    ]
    assert error_diagnostics == []
    assert resolve_exit_code_from_diagnostics(run_result.diagnostics) == EXIT_CODE_SUCCESS


def test_repository_documentation_passes_docguard_cli(
    monkeypatch,
) -> None:
    project_root = resolve_repository_root()
    monkeypatch.chdir(project_root)
    exit_code = docguard_main(list(REPOSITORY_DOCUMENTATION_PATHS))
    assert exit_code == EXIT_CODE_SUCCESS


def test_repository_documentation_passes_docguard_cli_json(
    monkeypatch,
    capsys,
) -> None:
    project_root = resolve_repository_root()
    monkeypatch.chdir(project_root)
    exit_code = docguard_main(
        [*REPOSITORY_DOCUMENTATION_PATHS, "--format", "json"]
    )
    captured_output = capsys.readouterr()
    parsed_output = json.loads(captured_output.out)
    assert exit_code == EXIT_CODE_SUCCESS
    assert parsed_output["diagnostics"] == []


def test_repository_documentation_passes_pytest_docguard_mode() -> None:
    if os.environ.get(SELF_TEST_SUBPROCESS_ENVIRONMENT_VARIABLE):
        pytest.skip("Skip recursive subprocess self-test.")

    project_root = resolve_repository_root()
    environment = os.environ.copy()
    environment[SELF_TEST_SUBPROCESS_ENVIRONMENT_VARIABLE] = "1"
    completed_process = subprocess.run(
        [sys.executable, "-m", "pytest", "--docguard", "-q"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
        env=environment,
    )
    assert completed_process.returncode == EXIT_CODE_SUCCESS, completed_process.stdout
