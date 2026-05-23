"""Deterministic split suggestions for oversized Markdown documents."""

from __future__ import annotations

import re

from docguard.constants import GENERIC_SPLIT_SUGGESTION_MESSAGE
from docguard.models import ParsedMarkdownDocument

MINIMUM_HEADINGS_FOR_SPLIT_SUGGESTION = 2
MAXIMUM_SUGGESTED_SPLIT_FILES = 5

SLUG_INVALID_CHARACTER_PATTERN = re.compile(r"[^a-z0-9]+")


def slugify_heading_text(heading_text: str) -> str:
    normalized_text = heading_text.strip().lower()
    slug_text = SLUG_INVALID_CHARACTER_PATTERN.sub("-", normalized_text).strip("-")
    return slug_text or "section"


def build_split_suggestion(
    parsed_document: ParsedMarkdownDocument,
) -> str:
    top_level_headings = [
        heading for heading in parsed_document.headings if heading.level == 2
    ]
    if len(top_level_headings) < MINIMUM_HEADINGS_FOR_SPLIT_SUGGESTION:
        top_level_headings = list(parsed_document.headings)

    if len(top_level_headings) < MINIMUM_HEADINGS_FOR_SPLIT_SUGGESTION:
        return GENERIC_SPLIT_SUGGESTION_MESSAGE

    source_path = parsed_document.repository_relative_path
    source_stem = source_path.rsplit(".", maxsplit=1)[0]
    suggested_paths: list[str] = []
    for heading in top_level_headings[:MAXIMUM_SUGGESTED_SPLIT_FILES]:
        slug = slugify_heading_text(heading.text)
        suggested_paths.append(f"- {source_stem}/{slug}.md")
    return "Suggested split:\n" + "\n".join(suggested_paths)
