"""Tests for the docguard pytest adapter."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from docguard.constants import EXIT_CODE_CONFIGURATION_FAILURE

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


def test_pytest_docguard_creates_one_item_per_document(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "hidden.md").write_text(
        "# Hidden\n\n" + "line\n" * 401,
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.relaxations]]
parameter = "require_index_reachability"
value = false
reason = "Focused pytest adapter test does not define repository navigation."
""",
    )
    completed_process = subprocess.run(
        [sys.executable, "-m", "pytest", "--docguard", "-q"],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
        env=build_subprocess_environment(),
    )
    assert completed_process.returncode == 1
    assert "docs/hidden.md::docguard" in completed_process.stdout


def test_pytest_docguard_invalid_configuration_exits_with_code_two(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
unknown_key = true
""",
    )
    completed_process = subprocess.run(
        [sys.executable, "-m", "pytest", "--docguard", "-q"],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
        env=build_subprocess_environment(),
    )
    assert completed_process.returncode == 2
    assert "Unknown keys" in completed_process.stdout + completed_process.stderr


def test_pytest_docguard_non_utf8_markdown_exits_with_code_two(
    temporary_project_directory: Path,
) -> None:
    invalid_bytes = "# 見出し\n".encode("cp932")
    (temporary_project_directory / "invalid.md").write_bytes(invalid_bytes)
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["invalid.md"]
""",
    )
    completed_process = subprocess.run(
        [sys.executable, "-m", "pytest", "--docguard", "-q"],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
        env=build_subprocess_environment(),
    )
    assert completed_process.returncode == EXIT_CODE_CONFIGURATION_FAILURE
    assert "invalid.md" in completed_process.stdout + completed_process.stderr
    assert "Traceback" not in completed_process.stdout + completed_process.stderr
