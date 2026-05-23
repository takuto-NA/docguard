"""Tests for UTF-8 encoding contract and Unicode document support."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from docguard.config import ConfigurationError, load_docguard_configuration
from docguard.constants import (
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
    EXIT_CODE_CONFIGURATION_FAILURE,
)
from docguard.discovery import discover_documents
from docguard.formatters import format_run_result_json
from docguard.graph import build_document_graph
from docguard.markdown import parse_markdown_document
from docguard.runner import DocguardConfigurationFailure, run_docguard_from_paths

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SHIFT_JIS_ENCODING_NAME = "cp932"


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def build_subprocess_environment() -> dict[str, str]:
    environment = os.environ.copy()
    source_directory = str(REPOSITORY_ROOT / "src")
    existing_pythonpath = environment.get("PYTHONPATH", "")
    if existing_pythonpath:
        environment["PYTHONPATH"] = f"{source_directory}{os.pathsep}{existing_pythonpath}"
    else:
        environment["PYTHONPATH"] = source_directory
    return environment


def write_shift_jis_markdown_file(markdown_path: Path) -> None:
    invalid_bytes = "# 見出し\n".encode(SHIFT_JIS_ENCODING_NAME)
    markdown_path.write_bytes(invalid_bytes)


def test_non_utf8_markdown_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "invalid.md"
    write_shift_jis_markdown_file(markdown_path)

    with pytest.raises(ConfigurationError, match="not valid UTF-8: invalid.md"):
        parse_markdown_document(markdown_path, "invalid.md")


def test_runner_non_utf8_markdown_raises_configuration_failure(
    temporary_project_directory: Path,
) -> None:
    write_shift_jis_markdown_file(temporary_project_directory / "invalid.md")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["invalid.md"]
""",
    )

    with pytest.raises(DocguardConfigurationFailure, match="invalid.md"):
        run_docguard_from_paths(
            project_root=temporary_project_directory,
            cli_paths=tuple(),
        )


def test_cli_non_utf8_markdown_exits_with_code_two(
    temporary_project_directory: Path,
) -> None:
    write_shift_jis_markdown_file(temporary_project_directory / "invalid.md")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["invalid.md"]
""",
    )
    completed_process = subprocess.run(
        [sys.executable, "-m", "docguard.cli", "invalid.md"],
        cwd=temporary_project_directory,
        capture_output=True,
        text=True,
        check=False,
        env=build_subprocess_environment(),
    )

    assert completed_process.returncode == EXIT_CODE_CONFIGURATION_FAILURE
    assert "invalid.md" in completed_process.stderr
    assert "Traceback" not in completed_process.stderr


def test_import_docguard_module_succeeds() -> None:
    import docguard
    from docguard.runner import run_docguard_from_paths

    assert docguard is not None
    assert run_docguard_from_paths is not None


def test_parse_japanese_headings_and_body(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "docs" / "概要.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text(
        """# プロジェクト概要

## 概要

日本語の本文です。
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "docs/概要.md",
    )

    assert parsed_document.physical_line_count > 0
    assert any(heading.text == "概要" for heading in parsed_document.headings)
    assert "日本語の本文です。" in parsed_document.raw_text


def test_japanese_required_headings_diagnostic(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "guide.md").write_text(
        """# ガイド

## 背景

本文のみ。
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.document_types]]
name = "guide"
glob = "docs/*.md"
required_headings = ["概要"]
""",
    )
    run_result = run_docguard_from_paths(
        project_root=temporary_project_directory,
        cli_paths=tuple(),
    )
    format001_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING
    ]

    assert len(format001_diagnostics) == 1
    assert "概要" in format001_diagnostics[0].message


def test_japanese_document_graph_links(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[設計](docs/設計.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "設計.md").write_text("# 設計\n", encoding="utf-8")
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

    assert "docs/設計.md" in document_graph.outgoing_links["README.md"]
    assert document_graph.incoming_links["docs/設計.md"] == frozenset({"README.md"})


def test_run_docguard_from_paths_with_japanese_documents(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[概要](docs/概要.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "概要.md").write_text(
        """# 概要

## 背景

日本語の本文です。
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_index_reachability = true
""",
    )
    run_result = run_docguard_from_paths(
        project_root=temporary_project_directory,
        cli_paths=tuple(),
    )

    assert run_result.diagnostics == ()
    assert run_result.checked_document_count == 2


def test_json_output_preserves_japanese_in_diagnostics(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "guide.md").write_text(
        """# ガイド

## 背景

本文のみ。
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.document_types]]
name = "guide"
glob = "docs/*.md"
required_headings = ["概要"]
""",
    )
    run_result = run_docguard_from_paths(
        project_root=temporary_project_directory,
        cli_paths=tuple(),
    )
    json_output = format_run_result_json(run_result)

    assert "概要" in json_output
    assert "\\u6982\\u8981" not in json_output
    parsed_output = json.loads(json_output)
    assert parsed_output["diagnostics"][0]["message"] == "Expected heading: ## 概要"


def test_pyproject_with_japanese_required_headings(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.document_types]]
name = "guide"
glob = "docs/*.md"
required_headings = ["概要"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )

    assert configuration.document_types[0].required_headings == ("概要",)


def test_utf8_bom_markdown_parses(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "bom.md"
    markdown_path.write_bytes(
        "\ufeff# タイトル\n\n## 概要\n".encode("utf-8")
    )
    parsed_document = parse_markdown_document(markdown_path, "bom.md")

    assert parsed_document.headings[0].text == "タイトル"
    assert any(heading.text == "概要" for heading in parsed_document.headings)
