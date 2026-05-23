"""Domain models for parsed Markdown documents and configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Heading:
    level: int
    text: str
    line_number: int


@dataclass(frozen=True)
class MarkdownSection:
    heading: Heading | None
    start_line_number: int
    end_line_number: int
    line_count: int


@dataclass(frozen=True)
class MarkdownLink:
    link_text: str
    target: str
    line_number: int


@dataclass(frozen=True)
class ParsedMarkdownDocument:
    repository_relative_path: str
    absolute_path: Path
    raw_text: str
    physical_line_count: int
    headings: tuple[Heading, ...]
    sections: tuple[MarkdownSection, ...]
    front_matter: dict[str, object] | None
    markdown_links: tuple[MarkdownLink, ...]


@dataclass(frozen=True)
class DocumentTypeConfiguration:
    name: str
    glob_pattern: str
    required_headings: tuple[str, ...] = field(default_factory=tuple)
    required_front_matter_keys: tuple[str, ...] = field(default_factory=tuple)
    max_document_lines: int | None = None
    max_section_lines: int | None = None


@dataclass(frozen=True)
class DocguardConfiguration:
    project_root: Path
    paths: tuple[str, ...]
    ignore_globs: tuple[str, ...]
    max_document_lines: int
    max_section_lines: int
    index_files: tuple[str, ...]
    require_index_reachability: bool
    severities: dict[str, str]
    document_types: tuple[DocumentTypeConfiguration, ...]
    experimental_rules_enabled: bool = False
    validate_explicit_paths: bool = False


@dataclass(frozen=True)
class DocumentInspectionContext:
    parsed_document: ParsedMarkdownDocument
    document_type: DocumentTypeConfiguration | None
    max_document_lines: int
    max_section_lines: int


@dataclass(frozen=True)
class DocumentGraph:
    document_paths: frozenset[str]
    outgoing_links: dict[str, frozenset[str]]
    incoming_links: dict[str, frozenset[str]]
    reachable_paths: frozenset[str]
