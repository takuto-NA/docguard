"""Phase 2 graph contract tests and candidate helper acceptance tests."""

from __future__ import annotations

from pathlib import Path

from docguard.config import load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.graph import (
    build_document_graph,
    collect_hub_outgoing_violations,
    collect_orphan_candidates,
    resolve_hub_document_paths,
)


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_orphan_candidate_has_zero_incoming_links(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
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
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=frozenset({"README.md"}),
    )

    assert document_graph.incoming_links["docs/orphan.md"] == frozenset()
    assert orphan_candidates == frozenset({"docs/orphan.md"})


def test_linked_cluster_without_index_is_not_orphan(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    (docs_directory / "alpha.md").write_text("# Alpha\n\n[Beta](beta.md)\n", encoding="utf-8")
    (docs_directory / "beta.md").write_text("# Beta\n\n[Alpha](alpha.md)\n", encoding="utf-8")
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
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=frozenset({"README.md"}),
    )

    assert document_graph.incoming_links["docs/alpha.md"] == frozenset({"docs/beta.md"})
    assert document_graph.incoming_links["docs/beta.md"] == frozenset({"docs/alpha.md"})
    assert orphan_candidates == frozenset()
    assert document_graph.reachable_paths == frozenset({"README.md"})


def test_index_file_is_excluded_from_orphan_candidates(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=frozenset({"README.md"}),
    )

    assert document_graph.incoming_links["README.md"] == frozenset()
    assert "README.md" not in orphan_candidates


def test_hub_without_outgoing_links_is_candidate(
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
paths = ["README.md", "docs"]
index_files = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=frozenset({"README.md"}),
    )
    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )

    assert hub_document_paths == frozenset({"README.md"})
    assert hub_outgoing_violations == frozenset({"README.md"})


def test_leaf_document_is_not_hub_outgoing_candidate(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=frozenset({"README.md"}),
    )
    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )

    assert "docs/design.md" not in hub_document_paths
    assert hub_outgoing_violations == frozenset()


def test_hub_glob_patterns_include_matching_documents(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "index-page.md").write_text("# Index Page\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=frozenset({"README.md"}),
        hub_glob_patterns=frozenset({"docs/index-*.md"}),
    )
    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )

    assert hub_document_paths == frozenset({"README.md", "docs/index-page.md"})
    assert hub_outgoing_violations == frozenset({"docs/index-page.md"})


def test_external_markdown_links_stay_out_of_graph(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Outside](../outside.md)\n",
        encoding="utf-8",
    )
    outside_file = temporary_project_directory.parent / "outside.md"
    outside_file.write_text("# Outside\n", encoding="utf-8")
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
