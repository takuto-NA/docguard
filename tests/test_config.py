"""Tests for docguard configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import (
    ConfigurationError,
    load_docguard_configuration,
    resolve_document_type_for_path,
)
from docguard.constants import DEFAULT_MAX_DOCUMENT_LINES


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_zero_config_fallback_uses_cli_paths(temporary_project_directory: Path) -> None:
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=None,
        cli_paths=("docs",),
    )
    assert configuration.paths == ("docs",)
    assert configuration.max_document_lines == DEFAULT_MAX_DOCUMENT_LINES
    assert configuration.require_index_reachability is False


def test_unknown_configuration_key_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
unknown_key = true
""",
    )
    with pytest.raises(ConfigurationError, match="Unknown keys"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_duplicate_document_type_match_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"

[[tool.docguard.document_types]]
name = "decision"
glob = "docs/adr/*.md"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    with pytest.raises(ConfigurationError, match="matched multiple document types"):
        resolve_document_type_for_path(
            "docs/adr/0001-example.md",
            configuration.document_types,
        )


def test_cli_paths_override_configured_paths(temporary_project_directory: Path) -> None:
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
    assert configuration.paths == ("README.md",)


def test_severity_override_is_loaded(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard.severity]
DG-SIZE001 = "warning"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.severities["DG-SIZE001"] == "warning"


def test_invalid_max_document_lines_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
max_document_lines = "400"
""",
    )
    with pytest.raises(ConfigurationError, match="max_document_lines"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_find_project_root_walks_up_parent_directories(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    nested_directory = temporary_project_directory / "packages" / "app"
    nested_directory.mkdir(parents=True)
    configuration = load_docguard_configuration(
        project_root=nested_directory,
        config_path=None,
        cli_paths=tuple(),
    )
    assert configuration.project_root == temporary_project_directory.resolve()
    assert configuration.paths == ("docs",)
