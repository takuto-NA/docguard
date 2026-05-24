"""Tests for duplicate guidance extraction, normalization, and grouping."""

from __future__ import annotations

from pathlib import Path

from docguard.constants import DEFAULT_DUPLICATE_GUIDANCE_KINDS
from docguard.duplicate_guidance import (
    GuidanceAtomKind,
    collect_duplicate_guidance_groups,
    collect_guidance_atoms,
    normalize_code_block,
    normalize_paragraph_text,
    resolve_enabled_guidance_atom_kinds,
)

SHARED_DUPLICATE_PARAGRAPH_TEXT = (
    "The loader must reject packages above 12288 bytes until "
    "chunked transfer is verified on hardware."
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


def test_collects_duplicate_headings_after_three_occurrences_when_opted_in(
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
        duplicate_guidance_kinds=("heading",),
    )

    heading_duplicate_groups = [
        duplicate_group
        for duplicate_group in duplicate_groups
        if duplicate_group.kind is GuidanceAtomKind.HEADING
    ]
    assert len(heading_duplicate_groups) == 1
    assert heading_duplicate_groups[0].normalized_text == "Configuration"
    assert len(heading_duplicate_groups[0].atoms) == 3


def test_template_headings_are_not_duplicate_by_default(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n## 目的\n\nText.\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
    )

    assert duplicate_groups == tuple()


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
        duplicate_guidance_kinds=("code_block", "list_item", "heading"),
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


def test_allowed_duplicate_patterns_suppress_matching_heading_when_opted_in(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n## Purpose\n\nText.\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=(r"^Purpose$",),
        duplicate_guidance_kinds=("heading",),
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
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(
        DEFAULT_DUPLICATE_GUIDANCE_KINDS
    )
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert guidance_atoms == tuple()


def test_collects_duplicate_paragraphs_after_three_occurrences_when_opted_in(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n{SHARED_DUPLICATE_PARAGRAPH_TEXT}\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
        duplicate_guidance_kinds=("paragraph",),
    )

    paragraph_duplicate_groups = [
        duplicate_group
        for duplicate_group in duplicate_groups
        if duplicate_group.kind is GuidanceAtomKind.PARAGRAPH
    ]
    assert len(paragraph_duplicate_groups) == 1
    assert (
        paragraph_duplicate_groups[0].normalized_text
        == normalize_paragraph_text(SHARED_DUPLICATE_PARAGRAPH_TEXT)
    )
    assert len(paragraph_duplicate_groups[0].atoms) == 3


def test_repeated_paragraphs_are_not_duplicate_by_default(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n{SHARED_DUPLICATE_PARAGRAPH_TEXT}\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
    )

    assert duplicate_groups == tuple()


def test_collects_duplicate_multiline_paragraphs_when_opted_in(
    temporary_project_directory: Path,
) -> None:
    shared_multiline_paragraph = (
        "The loader must reject packages above 12288 bytes until chunked transfer "
        "is verified on hardware.\n"
        "Do not raise the limit without a new RAM measurement."
    )
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n{shared_multiline_paragraph}\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=tuple(),
        duplicate_guidance_kinds=("paragraph",),
    )

    paragraph_duplicate_groups = [
        duplicate_group
        for duplicate_group in duplicate_groups
        if duplicate_group.kind is GuidanceAtomKind.PARAGRAPH
    ]
    assert len(paragraph_duplicate_groups) == 1
    assert (
        paragraph_duplicate_groups[0].normalized_text
        == normalize_paragraph_text(shared_multiline_paragraph)
    )
    assert len(paragraph_duplicate_groups[0].atoms) == 3


def test_heading_lines_are_not_collected_as_paragraph_atoms(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "with-heading.md"
    markdown_path.write_text(
        f"""# Title

## Gate limits

{SHARED_DUPLICATE_PARAGRAPH_TEXT}
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "with-heading.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert len(guidance_atoms) == 1
    assert guidance_atoms[0].normalized_text == normalize_paragraph_text(
        SHARED_DUPLICATE_PARAGRAPH_TEXT
    )
    assert guidance_atoms[0].line_number == 5


def test_short_paragraphs_are_not_collected_as_atoms(
    temporary_project_directory: Path,
) -> None:
    short_paragraph_text = "Keep one canonical owner for this note."
    markdown_path = temporary_project_directory / "short-paragraph.md"
    markdown_path.write_text(
        f"# Title\n\n{short_paragraph_text}\n",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "short-paragraph.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert guidance_atoms == tuple()


def test_fenced_code_is_not_collected_as_paragraph_atom(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "fenced-code.md"
    markdown_path.write_text(
        f"""# Title

```bash
{SHARED_DUPLICATE_PARAGRAPH_TEXT}
```
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "fenced-code.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert guidance_atoms == tuple()


def test_list_items_are_not_collected_as_paragraph_atoms(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "list-item.md"
    markdown_path.write_text(
        f"# Title\n\n- {SHARED_DUPLICATE_PARAGRAPH_TEXT}\n",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "list-item.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert guidance_atoms == tuple()


def test_table_rows_are_not_collected_as_paragraph_atoms(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "table-row.md"
    markdown_path.write_text(
        f"# Title\n\n| Column |\n| --- |\n| {SHARED_DUPLICATE_PARAGRAPH_TEXT} |\n",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "table-row.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    assert guidance_atoms == tuple()


def test_front_matter_is_not_collected_as_paragraph_atom(
    temporary_project_directory: Path,
) -> None:
    long_body_paragraph = (
        "Body text that is long enough to qualify as a paragraph when repeated "
        "across multiple documents in the configured scan scope."
    )
    markdown_path = temporary_project_directory / "front-matter.md"
    markdown_path.write_text(
        f"""---
status: accepted
summary: {SHARED_DUPLICATE_PARAGRAPH_TEXT}
---

# Title

{long_body_paragraph}
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "front-matter.md",
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(("paragraph",))
    guidance_atoms = collect_guidance_atoms(
        parsed_document,
        enabled_guidance_atom_kinds,
    )

    normalized_paragraph_texts = {
        guidance_atom.normalized_text for guidance_atom in guidance_atoms
    }
    assert normalize_paragraph_text(SHARED_DUPLICATE_PARAGRAPH_TEXT) not in (
        normalized_paragraph_texts
    )


def test_allowed_duplicate_patterns_suppress_matching_paragraph_when_opted_in(
    temporary_project_directory: Path,
) -> None:
    document_contexts = tuple(
        build_inspection_context(
            temporary_project_directory,
            f"docs/page-{page_index}.md",
            f"# Title {page_index}\n\n{SHARED_DUPLICATE_PARAGRAPH_TEXT}\n",
        )
        for page_index in range(1, 4)
    )
    duplicate_groups = collect_duplicate_guidance_groups(
        document_contexts,
        allowed_duplicate_patterns=(r"12288 bytes",),
        duplicate_guidance_kinds=("paragraph",),
    )

    assert duplicate_groups == tuple()
