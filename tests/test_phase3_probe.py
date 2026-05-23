"""Dogfood probe for Phase 3 candidate diagnostics.

Uses production role_families and heading_order modules.
Run: pytest -k phase3_probe -s
"""

from __future__ import annotations

from pathlib import Path

from docguard.config import find_project_root, load_docguard_configuration
from docguard.discovery import discover_documents
from docguard.heading_order import find_heading_level_skips
from docguard.role_families import LEVEL_TWO_HEADING, RoleFamily, classify_heading_text, detect_mixed_role_families


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    project_root = find_project_root(repository_root)
    assert project_root is not None
    return project_root


def probe_repository_phase3_candidates() -> tuple[
    dict[str, list[tuple[str, RoleFamily | None]]],
    frozenset[str],
    frozenset[tuple[str, int]],
]:
    project_root = resolve_repository_root()
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    document_contexts = discover_documents(configuration)

    heading_family_table: dict[str, list[tuple[str, RoleFamily | None]]] = {}
    mixed_role_candidates: set[str] = set()
    heading_skip_violations: set[tuple[str, int]] = set()

    for inspection_context in document_contexts:
        parsed_document = inspection_context.parsed_document
        document_path = parsed_document.repository_relative_path

        if inspection_context.document_type is None:
            level_two_rows: list[tuple[str, RoleFamily | None]] = []
            for heading in parsed_document.headings:
                if heading.level != LEVEL_TWO_HEADING:
                    continue
                level_two_rows.append(
                    (heading.text, classify_heading_text(heading.text))
                )
            if level_two_rows:
                heading_family_table[document_path] = level_two_rows

            mixed_role_families = detect_mixed_role_families(parsed_document.headings)
            if len(mixed_role_families) >= 2:
                mixed_role_candidates.add(document_path)

        for violation in find_heading_level_skips(parsed_document.headings):
            heading_skip_violations.add((document_path, violation.line_number))

    return (
        heading_family_table,
        frozenset(mixed_role_candidates),
        frozenset(heading_skip_violations),
    )


def test_phase3_probe_prints_dogfood_candidate_table() -> None:
    heading_family_table, mixed_role_candidates, heading_skip_violations = (
        probe_repository_phase3_candidates()
    )

    print("\n--- Phase 3 dogfood probe: H2 -> family (untyped only) ---")
    for document_path, rows in sorted(heading_family_table.items()):
        print(document_path)
        for heading_text, family in rows:
            family_label = family.value if family is not None else "none"
            print(f"  ## {heading_text!r} -> {family_label}")

    print("\n--- SPLIT001 candidates ---")
    for document_path in sorted(mixed_role_candidates):
        print(document_path)

    print("\n--- FORMAT002 candidates (path, line) ---")
    for document_path, line_number in sorted(heading_skip_violations):
        print(f"{document_path}:{line_number}")

    assert mixed_role_candidates == frozenset()
    assert heading_skip_violations == frozenset()
