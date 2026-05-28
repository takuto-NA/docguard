"""Unit tests for documentation style extraction and diagnostics."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.constants import DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
from docguard.documentation_style import (
    DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES,
    DocumentationStyleSourceKind,
    EnforcementStatus,
    EXPECTED_RANKED_EXPRESSION_COUNT,
    extract_documentation_style_inspection_targets,
    find_forbidden_documentation_expression_matches,
)
from docguard.models import DocguardConfiguration, DocumentInspectionContext, DocumentTypeConfiguration
from docguard.rules import check_documentation_style
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
    document_type: DocumentTypeConfiguration | None = None,
) -> DocumentInspectionContext:
    parsed_document = build_parsed_document(markdown_text, document_path)
    return DocumentInspectionContext(
        parsed_document=parsed_document,
        document_type=document_type,
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


def test_ranked_expression_manifest_is_complete() -> None:
    ranks = {rule.rank for rule in DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES}
    assert ranks == set(range(1, EXPECTED_RANKED_EXPRESSION_COUNT + 1))
    assert len(DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES) == (
        EXPECTED_RANKED_EXPRESSION_COUNT
    )


def test_ranked_expression_manifest_has_no_unclassified_entries() -> None:
    for rule in DEFAULT_FORBIDDEN_DOCUMENTATION_EXPRESSION_RULES:
        assert rule.enforcement_status in {
            EnforcementStatus.ACTIVE,
            EnforcementStatus.SCOPED,
            EnforcementStatus.CANDIDATE,
        }
        assert rule.label.strip() != ""
        assert rule.recommended_replacement.strip() != ""
        assert rule.source_scopes


@pytest.mark.parametrize(
    ("markdown_text", "expected_label"),
    [
        ("## 主題 — 補足\n", "heading em dash subtitle"),
        ("## このプラグインでできること\n", "できること heading phrase"),
        ("## 結局何ができるか\n", "結局何ができるか heading phrase"),
        ("## 一言\n", "一言 heading phrase"),
        ("## 調査結果 — 何がわかったか\n", "何がわかったか heading phrase"),
        ("### Run 入力（共通）\n", "heading parenthetical subtitle"),
        ("## 何を変えていないか\n", "question-form heading"),
        ("## 読み方\n", "読み方 heading phrase"),
        ("## Gate2 手順メモ\n", "手順メモ or 成果の整理 heading phrase"),
        ("## 変更なし／追加\n", "heading parallel slash phrasing"),
    ],
)
def test_heading_patterns_are_detected(markdown_text: str, expected_label: str) -> None:
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    assert len(inspection_targets) == 1
    matches = find_forbidden_documentation_expression_matches(
        inspection_targets[0],
        allowed_documentation_style_phrases=tuple(),
        extra_prohibited_documentation_style_patterns=tuple(),
    )
    assert any(match.rule.label == expected_label for match in matches)


def test_table_header_labels_are_detected() -> None:
    markdown_text = """# Title

| 以前 | 現在 |
| --- | --- |
| old | new |
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    table_header_targets = [
        target
        for target in inspection_targets
        if target.source_kind is DocumentationStyleSourceKind.TABLE_HEADER
    ]
    assert len(table_header_targets) == 2
    assert all(
        find_forbidden_documentation_expression_matches(
            target,
            allowed_documentation_style_phrases=tuple(),
            extra_prohibited_documentation_style_patterns=tuple(),
        )
        for target in table_header_targets
    )


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_prose_responsibility_prefix_is_detected() -> None:
    markdown_text = """# Title

責務: GH 利用者が CLI を選べるようにする。
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    prose_targets = [
        target
        for target in inspection_targets
        if target.source_kind is DocumentationStyleSourceKind.PROSE
    ]
    assert len(prose_targets) == 1
    matches = find_forbidden_documentation_expression_matches(
        prose_targets[0],
        allowed_documentation_style_phrases=tuple(),
        extra_prohibited_documentation_style_patterns=tuple(),
    )
    assert any(
        match.rule.label == "prose responsibility prefix"
        for match in matches
    )


def test_body_em_dash_is_not_detected() -> None:
    markdown_text = """# Title

Entry points: same as other rules — `docguard`, `--format json`.
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    matches = find_forbidden_documentation_expression_matches(
        inspection_targets[0],
        allowed_documentation_style_phrases=tuple(),
        extra_prohibited_documentation_style_patterns=tuple(),
    )
    assert matches == tuple()


def test_candidate_phrases_are_not_detected_by_default() -> None:
    markdown_text = """# Title

1 回では分からないケースがあります。
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    matches = find_forbidden_documentation_expression_matches(
        inspection_targets[0],
        allowed_documentation_style_phrases=tuple(),
        extra_prohibited_documentation_style_patterns=tuple(),
    )
    assert matches == tuple()


def test_allowed_documentation_style_phrase_suppresses_match() -> None:
    markdown_text = """# Title

このリポジトリの構成を確認する。
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    matches = find_forbidden_documentation_expression_matches(
        inspection_targets[0],
        allowed_documentation_style_phrases=("このリポジトリ",),
        extra_prohibited_documentation_style_patterns=tuple(),
    )
    assert matches == tuple()


def test_typed_document_is_checked_for_documentation_style() -> None:
    adr_document_type = DocumentTypeConfiguration(
        name="adr",
        glob_pattern="docs/adr/*.md",
        required_headings=("Status", "Context", "Decision", "Consequences"),
    )
    inspection_context = build_inspection_context(
        "## 主題 — 補足\n",
        document_path="docs/adr/0001-example.md",
        document_type=adr_document_type,
    )
    configuration = build_configuration()
    diagnostics = check_documentation_style(configuration, inspection_context)
    assert any(
        diagnostic.code == DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
        for diagnostic in diagnostics
    )


def test_check_documentation_style_reports_rank_in_message() -> None:
    inspection_context = build_inspection_context("## 主題 — 補足\n")
    configuration = build_configuration()
    diagnostics = check_documentation_style(configuration, inspection_context)
    assert len(diagnostics) == 1
    assert diagnostics[0].code == DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
    assert "rank 1" in diagnostics[0].message
    assert diagnostics[0].location == "line 1"


def test_run_docguard_checks_includes_documentation_style_diagnostics(
    tmp_path: Path,
) -> None:
    project_root = tmp_path
    document_directory = project_root / "docs"
    document_directory.mkdir()
    (project_root / "README.md").write_text("# Project\n", encoding="utf-8")
    (document_directory / "guide.md").write_text(
        "## 主題 — 補足\n",
        encoding="utf-8",
    )
    write_pyproject = project_root / "pyproject.toml"
    write_pyproject.write_text(
        """
[tool.docguard]
paths = ["README.md", "docs"]
""",
        encoding="utf-8",
    )
    configuration = load_docguard_configuration(
        project_root=project_root,
        config_path=write_pyproject,
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert any(
        diagnostic.code == DIAGNOSTIC_CODE_FORBIDDEN_DOCUMENTATION_EXPRESSION
        for diagnostic in run_result.diagnostics
    )


def test_example_dialogue_section_is_excluded_from_documentation_style() -> None:
    markdown_text = """# Title

## 主題 — 補足

## Example dialogue

**Developer**: ## 主題 — 補足
"""
    parsed_document = build_parsed_document(markdown_text)
    inspection_targets = extract_documentation_style_inspection_targets(parsed_document)
    assert len(inspection_targets) == 2
    assert all(
        inspection_target.line_number < 5
        for inspection_target in inspection_targets
    )
    assert inspection_targets[0].source_kind is DocumentationStyleSourceKind.HEADING


def test_direct_allowed_documentation_style_phrases_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
allowed_documentation_style_phrases = ["このリポジトリ"]
""",
    )
    with pytest.raises(ConfigurationError, match="allowed_documentation_style_phrases"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_documentation_style_configuration_keys_are_parsed(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
extra_prohibited_documentation_style_patterns = ["\\\\blegacy\\\\b"]

[[tool.docguard.relaxations]]
parameter = "allowed_documentation_style_phrases"
value = ["このリポジトリ"]
reason = "Legacy migration keeps this repository label temporarily."

[[tool.docguard.relaxations]]
parameter = "severity.DG-STYLE003"
value = "warning"
reason = "Legacy documentation style cleanup is still in progress."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.allowed_documentation_style_phrases == ("このリポジトリ",)
    assert configuration.extra_prohibited_documentation_style_patterns == (
        "\\blegacy\\b",
    )
    assert configuration.severities["DG-STYLE003"] == "warning"


def test_invalid_extra_prohibited_documentation_style_pattern_rejected(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
extra_prohibited_documentation_style_patterns = ["(["]
""",
    )
    with pytest.raises(
        ConfigurationError,
        match="extra_prohibited_documentation_style_patterns",
    ):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )
