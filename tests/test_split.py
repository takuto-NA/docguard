"""Tests for deterministic split suggestions."""

from __future__ import annotations

from pathlib import Path

from docguard.markdown import parse_markdown_document
from docguard.split import build_split_suggestion


def test_build_split_suggestion_uses_headings(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "docs" / "architecture.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text(
        """# Architecture

## Overview
Overview text.

## Runtime Model
Runtime text.

## Data Flow
Data flow text.
""",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "docs/architecture.md",
    )
    suggestion = build_split_suggestion(parsed_document)
    assert "docs/architecture/overview.md" in suggestion
    assert "docs/architecture/runtime-model.md" in suggestion


def test_build_split_suggestion_falls_back_to_generic_message(
    temporary_project_directory: Path,
) -> None:
    markdown_path = temporary_project_directory / "docs" / "notes.md"
    markdown_path.parent.mkdir(parents=True)
    markdown_path.write_text(
        "# Notes\n\nLong unstructured content.\n",
        encoding="utf-8",
    )
    parsed_document = parse_markdown_document(
        markdown_path,
        "docs/notes.md",
    )
    suggestion = build_split_suggestion(parsed_document)
    assert "Split the document by major topic" in suggestion
