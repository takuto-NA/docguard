"""Dogfood readiness gate tests for Phase 2 organization rules."""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.graph import (
    build_document_graph,
    collect_hub_outgoing_violations,
    collect_orphan_candidates,
    resolve_hub_document_paths,
)

MAXIMUM_ORPHAN_CANDIDATES = 0
MAXIMUM_HUB_OUTGOING_VIOLATIONS = 0

EXPECTED_REPOSITORY_INCOMING_LINKS = {
    "README.md": frozenset(),
    "CONTEXT.md": frozenset({"README.md"}),
    "docs/usage.md": frozenset({"README.md"}),
    "docs/adr/0001-cli-first-docguard.md": frozenset({"README.md"}),
    "docs/adr/0002-structured-diagnostics-and-strict-config.md": frozenset({"README.md"}),
    "docs/adr/0003-organization-link-rules.md": frozenset(
        {"README.md", "docs/usage.md"}
    ),
}

EXPECTED_REPOSITORY_OUTGOING_LINKS = {
    "README.md": frozenset(
        {
            "CONTEXT.md",
            "docs/usage.md",
            "docs/adr/0001-cli-first-docguard.md",
            "docs/adr/0002-structured-diagnostics-and-strict-config.md",
            "docs/adr/0003-organization-link-rules.md",
        }
    ),
    "CONTEXT.md": frozenset(),
    "docs/usage.md": frozenset({"docs/adr/0003-organization-link-rules.md"}),
    "docs/adr/0001-cli-first-docguard.md": frozenset(),
    "docs/adr/0002-structured-diagnostics-and-strict-config.md": frozenset(),
    "docs/adr/0003-organization-link-rules.md": frozenset(),
}

EXPECTED_ORPHAN_CANDIDATES = frozenset()
EXPECTED_HUB_OUTGOING_VIOLATIONS = frozenset()


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def load_repository_document_graph():
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)
    document_graph = build_document_graph(configuration, document_contexts)
    return configuration, document_graph


def test_repository_graph_incoming_outgoing_snapshot() -> None:
    configuration, document_graph = load_repository_document_graph()

    assert document_graph.document_paths == frozenset(
        EXPECTED_REPOSITORY_INCOMING_LINKS.keys()
    )
    for document_path, expected_incoming_paths in (
        EXPECTED_REPOSITORY_INCOMING_LINKS.items()
    ):
        assert document_graph.incoming_links[document_path] == expected_incoming_paths
    for document_path, expected_outgoing_paths in (
        EXPECTED_REPOSITORY_OUTGOING_LINKS.items()
    ):
        assert document_graph.outgoing_links[document_path] == expected_outgoing_paths
    assert configuration.index_files == ("README.md",)


def test_repository_orphan_candidates_match_adr_expectations() -> None:
    configuration, document_graph = load_repository_document_graph()
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=frozenset(configuration.index_files),
    )

    assert orphan_candidates == EXPECTED_ORPHAN_CANDIDATES


def test_repository_hub_violations_match_adr_expectations() -> None:
    configuration, document_graph = load_repository_document_graph()
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=frozenset(configuration.index_files),
    )
    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )

    assert hub_outgoing_violations == EXPECTED_HUB_OUTGOING_VIOLATIONS


def test_enabling_phase2_rules_would_not_mass_fail_dogfood() -> None:
    configuration, document_graph = load_repository_document_graph()
    orphan_candidates = collect_orphan_candidates(
        document_graph,
        excluded_index_paths=frozenset(configuration.index_files),
    )
    hub_document_paths = resolve_hub_document_paths(
        document_graph,
        index_file_paths=frozenset(configuration.index_files),
    )
    hub_outgoing_violations = collect_hub_outgoing_violations(
        document_graph,
        hub_document_paths,
    )

    assert len(orphan_candidates) <= MAXIMUM_ORPHAN_CANDIDATES
    assert len(hub_outgoing_violations) <= MAXIMUM_HUB_OUTGOING_VIOLATIONS
