"""Tests for the docguard pytest adapter."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


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
max_document_lines = 400
""",
    )
    completed_process = subprocess.run(
        [sys.executable, "-m", "pytest", "--docguard", "-q"],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed_process.returncode == 1
    assert "docs/hidden.md::docguard" in completed_process.stdout
