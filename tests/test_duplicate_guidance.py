"""Tests for duplicate guidance extraction, normalization, and grouping."""

from __future__ import annotations

from pathlib import Path

from docguard.duplicate_guidance import (
    GuidanceAtomKind,
    collect_duplicate_guidance_groups,
    collect_guidance_atoms,
    normalize_code_block,
)
from docguard.markdown import parse_markdown_document
from docguard.models import DocumentInspectionContext


def build_inspection_context(
    temporary_project_directory: Path,
    repository_relative_path: str,
    raw_text: str,
) -> DocumentInspectionContext:
    markdown_path = temporary_project_directory / repository_relative_path
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(raw_text, encoding="utf-8")
    parsed_document = parse_markdown_document(
        markdown_path,
        repository_relative_path,
    )
    return DocumentInspectionContext(
        parsed_document=parsed_document,
        document_type=None,
        max_document_lines=400,
        max_section_lines=120,
    )


def test_collects_duplicate_fenced_code_blocks_across_documents(
    temporary_project_directory: Path,
) -> None:
    shared_install_block = """```bash
uv add docguard
uv run docguard docs/ --summary
```"""
    first_document_context = build_inspection_context(
        temporary_project_directory,
        "docs/first.md",
        f"# First\n\n{shared_install_block}\n",
    )
    second_document_context = build_inspection_context(
        temporary_project_directory,
        "docs/second.md",
        f"# Second\n\n{shared_install_block}\n",
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        (first_document_context, second_document_context),
        allowed_duplicate_patterns=tuple(),
    )

    assert len(duplicate_groups) == 1
    duplicate_group = duplicate_groups[0]
    assert duplicate_group.kind is GuidanceAtomKind.CODE_BLOCK
    assert len(duplicate_group.atoms) == 2
    assert duplicate_group.atoms[0].document_path == "docs/first.md"
    assert duplicate_group.atoms[1].document_path == "docs/second.md"


def test_collects_duplicate_headings_after_three_occurrences(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n## Configuration\n\nText.\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
    )

    heading_duplicate_groups = [
        duplicate_group
        for duplicate_group in duplicate_groups
        if duplicate_group.kind is GuidanceAtomKind.HEADING
    ]
    assert len(heading_duplicate_groups) == 1
    assert heading_duplicate_groups[0].normalized_text == "Configuration"
    assert len(heading_duplicate_groups[0].atoms) == 3


def test_collects_duplicate_list_items_after_three_occurrences(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            "# Title\n\n- Run docguard locally before opening a pull request.\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
    )

    list_item_duplicate_groups = [
        duplicate_group
        for duplicate_group in duplicate_groups
        if duplicate_group.kind is GuidanceAtomKind.LIST_ITEM
    ]
    assert len(list_item_duplicate_groups) == 1
    assert (
        list_item_duplicate_groups[0].normalized_text
        == "Run docguard locally before opening a pull request."
    )
    assert len(list_item_duplicate_groups[0].atoms) == 3


def test_allowed_duplicate_patterns_suppress_matching_normalized_text(
    temporary_project_directory: Path,
) -> None:
    shared_install_block = """```bash
uv add docguard
uv run docguard docs/ --summary
```"""
    first_document_context = build_inspection_context(
        temporary_project_directory,
        "docs/first.md",
        f"# First\n\n{shared_install_block}\n",
    )
    second_document_context = build_inspection_context(
        temporary_project_directory,
        "docs/second.md",
        f"# Second\n\n{shared_install_block}\n",
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        (first_document_context, second_document_context),
        allowed_duplicate_patterns=(r"uv add docguard",),
    )

    assert duplicate_groups == tuple()


def test_normalize_code_block_removes_shell_comment_only_lines() -> None:
    normalized_code_block = normalize_code_block(
        [
            "uv add docguard",
            "# install dependency",
            "uv run docguard docs/ --summary",
        ]
    )

    assert normalized_code_block == (
        "uv add docguard\n"
        "uv run docguard docs/ --summary"
    )


def test_code_block_requires_at_least_two_non_empty_normalized_lines(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "single-line.md"
    markdown_path.write_text(
        """# Title

```bash
docguard docs/
```
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "single-line.md",
    )
    guidance_atoms = collect_guidance_atoms(parsed_document)

    assert guidance_atoms == tuple()
