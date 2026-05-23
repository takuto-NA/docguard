"""Tests for document discovery and ignore handling."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.discovery import discover_documents


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_discover_documents_excludes_ignored_paths(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    archive_directory = docs_directory / "archive"
    archive_directory.mkdir(parents=True)
    (docs_directory / "active.md").write_text("# Active\n", encoding="utf-8")
    (archive_directory / "old.md").write_text("# Old\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
ignore_globs = ["docs/archive/**"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    discovered_documents = discover_documents(configuration)
    discovered_paths = {
        context.parsed_document.repository_relative_path
        for context in discovered_documents
    }
    assert discovered_paths == {"docs/active.md"}


def test_discover_documents_skips_missing_configured_paths(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs", "missing"]
""",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "active.md").write_text("# Active\n", encoding="utf-8")
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    discovered_documents = discover_documents(configuration)
    discovered_paths = {
        context.parsed_document.repository_relative_path
        for context in discovered_documents
    }
    assert discovered_paths == {"docs/active.md"}


def test_cli_paths_override_configured_paths(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (temporary_project_directory / "README.md").write_text("# Readme\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=("README.md",),
    )
    discovered_documents = discover_documents(configuration)
    discovered_paths = {
        context.parsed_document.repository_relative_path
        for context in discovered_documents
    }
    assert discovered_paths == {"README.md"}


def test_explicit_non_markdown_cli_path_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    text_file = temporary_project_directory / "notes.txt"
    text_file.write_text("not markdown", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=("notes.txt",),
    )
    with pytest.raises(ConfigurationError, match="not a Markdown file"):
        discover_documents(configuration)
