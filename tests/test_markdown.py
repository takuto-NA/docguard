"""Tests for Markdown parsing helpers."""

from __future__ import annotations

from pathlib import Path

from docguard.markdown import (
    count_physical_lines,
    extract_front_matter,
    extract_headings,
    extract_markdown_links,
    parse_markdown_document,
    resolve_markdown_link_target,
)
from docguard.markdown import build_heading_subtree_sections


def test_count_physical_lines_excludes_trailing_blank_lines() -> None:
    raw_text = "line one\nline two\n\n\n"
    assert count_physical_lines(raw_text) == 2


def test_extract_headings_ignores_code_blocks() -> None:
    raw_lines = [
        "# Title",
        "```python",
        "# Not a heading",
        "```",
        "## Real Heading",
    ]
    headings = extract_headings(raw_lines)
    assert [heading.text for heading in headings] == ["Title", "Real Heading"]


def test_extract_front_matter_parses_yaml_keys() -> None:
    raw_lines = [
        "---",
        "status: accepted",
        "date: 2026-05-23",
        "---",
        "# Title",
    ]
    front_matter = extract_front_matter(raw_lines)
    assert front_matter is not None
    assert front_matter["status"] == "accepted"
    assert str(front_matter["date"]) == "2026-05-23"


def test_build_heading_subtree_sections_counts_nested_headings(
    temporary_project_directory: Path,
) -> None:
    raw_lines = [
        "# Title",
        "intro",
        "## Architecture",
        "overview",
        "### Runtime",
        "details",
        "## Risks",
        "risk text",
    ]
    headings = extract_headings(raw_lines)
    sections = build_heading_subtree_sections(raw_lines, headings)
    architecture_section = next(
        section for section in sections if section.heading and section.heading.text == "Architecture"
    )
    assert architecture_section.line_count == 4


def test_extract_markdown_links_filters_external_links() -> None:
    raw_lines = [
        "[local](./design.md)",
        "[external](https://example.com/design.md)",
    ]
    links = extract_markdown_links(raw_lines)
    assert len(links) == 1
    assert links[0].target == "./design.md"


def test_extract_markdown_links_ignores_non_markdown_targets() -> None:
    raw_lines = [
        "[readme](README)",
        "[design](./design.md)",
    ]
    links = extract_markdown_links(raw_lines)
    assert len(links) == 1
    assert links[0].target == "./design.md"


def test_parse_markdown_document_handles_empty_file(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "empty.md"
    markdown_path.write_text("", encoding="utf-8")
    parsed_document = parse_markdown_document(
        markdown_path,
        "empty.md",
    )
    assert parsed_document.physical_line_count == 0
    assert parsed_document.headings == tuple()


def test_resolve_markdown_link_target_normalizes_parent_segments() -> None:
    resolved_path = resolve_markdown_link_target(
        "docs/design/overview.md",
        "../adr/0001-example.md",
    )
    assert resolved_path == "docs/adr/0001-example.md"


def test_parse_markdown_document_reads_file(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "README.md"
    markdown_path.write_text("# Title\n\nBody\n", encoding="utf-8")
    parsed_document = parse_markdown_document(
        markdown_path,
        "README.md",
    )
    assert parsed_document.physical_line_count == 3
    assert parsed_document.headings[0].text == "Title"
