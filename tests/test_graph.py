"""Tests for the document graph model."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.graph import build_document_graph
from docguard.discovery import discover_documents


def write_pyproject(project_root: Path, contents: str) -> None:
    appended_relaxations = []
    if "parameter = \"min_document_lines\"" not in contents:
        appended_relaxations.append(
            """
[[tool.docguard.relaxations]]
parameter = "min_document_lines"
value = 0
reason = "Focused graph tests do not exercise document floor diagnostics."
"""
        )
    if (
        "require_index_reachability = true" not in contents
        and "parameter = \"require_index_reachability\"" not in contents
    ):
        appended_relaxations.append(
            """
[[tool.docguard.relaxations]]
parameter = "require_index_reachability"
value = false
reason = "Focused graph tests isolate link graph behavior."
"""
        )
    (project_root / "pyproject.toml").write_text(
        contents + "".join(appended_relaxations),
        encoding="utf-8",
    )


def test_build_document_graph_tracks_outgoing_and_incoming_links(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text(
        "# Design\n\n[Hidden](hidden.md)\n",
        encoding="utf-8",
    )
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
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)

    assert document_graph.outgoing_links["README.md"] == frozenset({"docs/design.md"})
    assert document_graph.incoming_links["docs/design.md"] == frozenset({"README.md"})
    assert document_graph.incoming_links["docs/hidden.md"] == frozenset({"docs/design.md"})
    assert document_graph.reachable_paths == frozenset(
        {"README.md", "docs/design.md", "docs/hidden.md"}
    )


def test_build_document_graph_excludes_ignored_documents(
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
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)

    assert "docs/active.md" in document_graph.document_paths
    assert "docs/archive/old.md" not in document_graph.document_paths


def test_build_document_graph_ignores_missing_link_targets(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Missing](docs/missing.md)\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)

    assert document_graph.outgoing_links["README.md"] == frozenset()


def test_build_document_graph_marks_all_documents_reachable_when_disabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
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
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)

    assert document_graph.reachable_paths == frozenset({"docs/orphan.md"})


def test_build_document_graph_rejects_index_outside_project_root(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    outside_index = temporary_project_directory.parent / "outside-index.md"
    outside_index.write_text("# Outside\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        f"""
[tool.docguard]
paths = ["docs"]
index_files = ["{outside_index.as_posix()}"]
require_index_reachability = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    with pytest.raises(ConfigurationError, match="outside project root"):
        build_document_graph(configuration, document_contexts)


def test_build_document_graph_rejects_index_not_in_scan_scope(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
index_files = ["README.md"]
require_index_reachability = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    with pytest.raises(ConfigurationError, match="within the scanned document scope"):
        build_document_graph(configuration, document_contexts)
