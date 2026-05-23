"""Markdown parsing helpers for headings, sections, front matter, and links."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from docguard.constants import (
    MARKDOWN_FILE_SUFFIX,
    MAXIMUM_HEADING_LEVEL,
    MINIMUM_HEADING_LEVEL,
    YAML_FRONT_MATTER_DELIMITER,
)
from docguard.models import (
    Heading,
    MarkdownLink,
    MarkdownSection,
    ParsedMarkdownDocument,
)

MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def strip_trailing_blank_lines(raw_lines: list[str]) -> list[str]:
    trimmed_lines = list(raw_lines)
    while trimmed_lines and trimmed_lines[-1].strip() == "":
        trimmed_lines.pop()
    return trimmed_lines


def count_physical_lines(raw_text: str) -> int:
    raw_lines = raw_text.splitlines()
    return len(strip_trailing_blank_lines(raw_lines))


def normalize_heading_text(raw_heading_text: str) -> str:
    return raw_heading_text.strip()


def parse_heading_line(line_text: str, line_number: int) -> Heading | None:
    match = HEADING_PATTERN.match(line_text)
    if match is None:
        return None
    heading_level = len(match.group(1))
    if heading_level < MINIMUM_HEADING_LEVEL or heading_level > MAXIMUM_HEADING_LEVEL:
        return None
    return Heading(
        level=heading_level,
        text=normalize_heading_text(match.group(2)),
        line_number=line_number,
    )


def extract_headings(raw_lines: list[str]) -> tuple[Heading, ...]:
    headings: list[Heading] = []
    inside_code_block = False
    for line_index, line_text in enumerate(raw_lines, start=1):
        if line_text.strip().startswith("```"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue
        heading = parse_heading_line(line_text, line_index)
        if heading is not None:
            headings.append(heading)
    return tuple(headings)


def extract_front_matter(raw_lines: list[str]) -> dict[str, object] | None:
    if len(raw_lines) < 3:
        return None
    if raw_lines[0].strip() != YAML_FRONT_MATTER_DELIMITER:
        return None
    closing_line_index = None
    for line_index in range(1, len(raw_lines)):
        if raw_lines[line_index].strip() == YAML_FRONT_MATTER_DELIMITER:
            closing_line_index = line_index
            break
    if closing_line_index is None:
        return None
    front_matter_text = "\n".join(raw_lines[1:closing_line_index])
    parsed_front_matter = yaml.safe_load(front_matter_text)
    if parsed_front_matter is None:
        return {}
    if not isinstance(parsed_front_matter, dict):
        return None
    return parsed_front_matter


def is_relative_markdown_link(link_target: str) -> bool:
    if link_target.startswith(("http://", "https://", "mailto:", "#")):
        return False
    if "://" in link_target:
        return False
    link_path = link_target.split("#", maxsplit=1)[0]
    if not link_path:
        return False
    return link_path.endswith(MARKDOWN_FILE_SUFFIX)


def extract_markdown_links(raw_lines: list[str]) -> tuple[MarkdownLink, ...]:
    markdown_links: list[MarkdownLink] = []
    inside_code_block = False
    for line_index, line_text in enumerate(raw_lines, start=1):
        if line_text.strip().startswith("```"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue
        for match in MARKDOWN_LINK_PATTERN.finditer(line_text):
            link_target = match.group(1).strip()
            if not is_relative_markdown_link(link_target):
                continue
            markdown_links.append(
                MarkdownLink(
                    link_text=match.group(0),
                    target=link_target,
                    line_number=line_index,
                )
            )
    return tuple(markdown_links)


def build_heading_subtree_sections(
    raw_lines: list[str],
    headings: tuple[Heading, ...],
) -> tuple[MarkdownSection, ...]:
    physical_line_count = len(strip_trailing_blank_lines(raw_lines))
    if not headings:
        return tuple()

    sections: list[MarkdownSection] = []
    for heading_index, heading in enumerate(headings):
        end_line_number = physical_line_count
        for candidate_heading in headings[heading_index + 1 :]:
            if candidate_heading.level <= heading.level:
                end_line_number = candidate_heading.line_number - 1
                break
        line_count = max(end_line_number - heading.line_number + 1, 0)
        sections.append(
            MarkdownSection(
                heading=heading,
                start_line_number=heading.line_number,
                end_line_number=end_line_number,
                line_count=line_count,
            )
        )
    return tuple(sections)


def parse_markdown_document(
    absolute_path: Path,
    repository_relative_path: str,
) -> ParsedMarkdownDocument:
    raw_text = absolute_path.read_text(encoding="utf-8")
    raw_lines = raw_text.splitlines()
    headings = extract_headings(raw_lines)
    return ParsedMarkdownDocument(
        repository_relative_path=repository_relative_path,
        absolute_path=absolute_path,
        raw_text=raw_text,
        physical_line_count=count_physical_lines(raw_text),
        headings=headings,
        sections=build_heading_subtree_sections(raw_lines, headings),
        front_matter=extract_front_matter(raw_lines),
        markdown_links=extract_markdown_links(raw_lines),
    )


def resolve_markdown_link_target(
    source_document_path: str,
    link_target: str,
) -> str:
    from posixpath import normpath

    link_path = link_target.split("#", maxsplit=1)[0]
    source_directory = Path(source_document_path).parent.as_posix()
    if source_directory in ("", "."):
        combined_path = link_path
    else:
        combined_path = f"{source_directory}/{link_path}"
    return normpath(combined_path).replace("\\", "/")
