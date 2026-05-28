"""Unit tests for prose style extraction and diagnostics."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import load_docguard_configuration
from docguard.constants import (
    DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
    DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
)
from docguard.discovery import discover_documents
from docguard.models import DocguardConfiguration, DocumentInspectionContext
from docguard.prose_style import (
    count_strong_emphasis_pairs,
    extract_prose_lines,
    find_prohibited_prose_pattern_matches,
)
from docguard.rules import check_prose_style
from docguard.runner import run_docguard_checks


def build_parsed_document(markdown_text: str, document_path: str = "docs/sample.md"):
    from docguard.markdown import parse_markdown_document

    temporary_directory = Path(__file__).resolve().parent / "fixtures"
    temporary_directory.mkdir(exist_ok=True)
    absolute_path = temporary_directory / "sample.md"
    absolute_path.write_text(markdown_text, encoding="utf-8")
    return parse_markdown_document(absolute_path, document_path)


def build_inspection_context(
    markdown_text: str,
    document_path: str = "docs/sample.md",
) -> DocumentInspectionContext:
    parsed_document = build_parsed_document(markdown_text, document_path)
    return DocumentInspectionContext(
        parsed_document=parsed_document,
        document_type=None,
        max_document_lines=400,
        max_section_lines=120,
    )


def build_configuration(**overrides: object) -> DocguardConfiguration:
    project_root = Path(__file__).resolve().parents[1]
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    return DocguardConfiguration(
        **{
            **configuration.__dict__,
            **overrides,
        }
    )


@pytest.mark.parametrize(
    ("line_text", "expected_pair_count"),
    [
        ("one **bold** line", 1),
        ("**open", 0),
        ("**a** and **b**", 2),
    ],
)
def test_count_strong_emphasis_pairs(line_text: str, expected_pair_count: int) -> None:
    assert count_strong_emphasis_pairs(line_text) == expected_pair_count


def test_code_fence_strong_emphasis_is_excluded_from_prose() -> None:
    markdown_text = """# Title

```toml
ignore_globs = ["docs/archive/**"]
```

Plain line.
"""
    parsed_document = build_parsed_document(markdown_text)
    prose_lines = extract_prose_lines(parsed_document)
    assert len(prose_lines) == 1
    assert count_strong_emphasis_pairs(prose_lines[0].line_text) == 0


def test_table_row_strong_emphasis_is_excluded_from_prose() -> None:
    markdown_text = """# Title

| Column | Value |
| --- | --- |
| default | **warnings print** |
"""
    parsed_document = build_parsed_document(markdown_text)
    prose_lines = extract_prose_lines(parsed_document)
    assert prose_lines == tuple()


def test_glossary_term_line_is_excluded_from_prose() -> None:
    markdown_text = """# Title

**Docguard**:
A CLI-first tool.
"""
    parsed_document = build_parsed_document(markdown_text)
    prose_lines = extract_prose_lines(parsed_document)
    assert len(prose_lines) == 1
    assert prose_lines[0].line_text.startswith("A CLI-first tool.")


def test_example_dialogue_section_is_excluded_from_prose() -> None:
    markdown_text = """# Title

Body without emphasis.

## Example dialogue

**Developer**: This uses **bold** words.
"""
    parsed_document = build_parsed_document(markdown_text)
    prose_lines = extract_prose_lines(parsed_document)
    assert len(prose_lines) == 1
    assert "Body without emphasis." in prose_lines[0].line_text


def test_inline_code_strong_emphasis_is_ignored() -> None:
    assert count_strong_emphasis_pairs("Use `--quiet` not **bold**") == 1
    assert count_strong_emphasis_pairs("Default is `**warning**` severity") == 0
    assert count_strong_emphasis_pairs("Install **`docguard-structure`**") == 1


def test_prohibited_pattern_does_not_match_inline_code_token() -> None:
    matched_patterns = find_prohibited_prose_pattern_matches(
        "Built-in patterns include `you`, `your`, `we`, and `our`.",
        allowed_prose_phrases=tuple(),
        extra_prohibited_prose_patterns=tuple(),
    )
    assert matched_patterns == tuple()


def test_prohibited_pattern_does_not_match_url_host() -> None:
    matched_patterns = find_prohibited_prose_pattern_matches(
        "See https://easy.example/docs for details.",
        allowed_prose_phrases=tuple(),
        extra_prohibited_prose_patterns=tuple(),
    )
    assert matched_patterns == tuple()


def test_allowed_prose_phrase_suppresses_prohibited_pattern() -> None:
    matched_patterns = find_prohibited_prose_pattern_matches(
        "What you can check today",
        allowed_prose_phrases=("What you can check",),
        extra_prohibited_prose_patterns=tuple(),
    )
    assert matched_patterns == tuple()


def test_check_prose_style_reports_excess_strong_emphasis() -> None:
    inspection_context = build_inspection_context("Plain **bold** prose.\n")
    configuration = build_configuration(max_strong_emphasis_pairs=0)
    diagnostics = check_prose_style(configuration, inspection_context)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS


def test_check_prose_style_reports_prohibited_pattern() -> None:
    inspection_context = build_inspection_context(
        "This is easy to overlook during review.\n"
    )
    configuration = build_configuration()
    diagnostics = check_prose_style(configuration, inspection_context)
    assert any(
        diagnostic.code == DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN
        for diagnostic in diagnostics
    )


def test_typed_document_skips_prose_style_checks() -> None:
    project_root = Path(__file__).resolve().parents[1]
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=project_root / "pyproject.toml",
        cli_paths=tuple(),
    )
    adr_path = project_root / "docs" / "adr" / "0001-cli-first-docguard.md"
    if not adr_path.is_file():
        pytest.skip("ADR fixture not available")
    from docguard.markdown import parse_markdown_document

    parsed_document = parse_markdown_document(
        adr_path,
        "docs/adr/0001-cli-first-docguard.md",
    )
    from docguard.config import resolve_document_type_for_path

    document_type = resolve_document_type_for_path(
        parsed_document.repository_relative_path,
        configuration.document_types,
    )
    inspection_context = DocumentInspectionContext(
        parsed_document=parsed_document,
        document_type=document_type,
        max_document_lines=160,
        max_section_lines=60,
    )
    diagnostics = check_prose_style(configuration, inspection_context)
    assert diagnostics == []


def test_run_docguard_checks_includes_prose_style_diagnostics(tmp_path: Path) -> None:
    project_root = tmp_path
    document_path = project_root / "docs"
    document_path.mkdir()
    sample_document = document_path / "sample.md"
    sample_document.write_text("This is **bold** and easy prose.\n", encoding="utf-8")
    configuration = DocguardConfiguration(
        project_root=project_root,
        paths=("docs",),
        ignore_globs=tuple(),
        max_document_lines=400,
        max_section_lines=120,
        min_document_lines=0,
        index_files=tuple(),
        require_index_reachability=False,
        require_orphan_detection=False,
        require_hub_outgoing_links=False,
        require_mixed_role_detection=False,
        require_heading_order_check=False,
        require_duplicate_guidance_detection=False,
        duplicate_guidance_kinds=("code_block", "list_item"),
        allowed_duplicate_patterns=tuple(),
        max_strong_emphasis_pairs=0,
        allowed_prose_phrases=tuple(),
        extra_prohibited_prose_patterns=tuple(),
        hub_globs=tuple(),
        severities={},
        document_types=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS in diagnostic_codes
    assert DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN in diagnostic_codes
