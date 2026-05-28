"""Prose style extraction and diagnostics for strong emphasis and prohibited patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from docguard.constants import (
    DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
    DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
    SUGGESTION_EXCESS_STRONG_EMPHASIS,
    SUGGESTION_PROHIBITED_PROSE_PATTERN,
    WHY_EXCESS_STRONG_EMPHASIS,
    WHY_PROHIBITED_PROSE_PATTERN,
    YAML_FRONT_MATTER_DELIMITER,
)
from docguard.diagnostics import Diagnostic, resolve_severity_for_code
from docguard.markdown import HEADING_PATTERN, parse_heading_line
from docguard.models import (
    DocguardConfiguration,
    DocumentInspectionContext,
    Heading,
    ParsedMarkdownDocument,
)

CLOSED_STRONG_EMPHASIS_PATTERN = re.compile(r"\*\*(.+?)\*\*")
GLOSSARY_TERM_LINE_PATTERN = re.compile(r"^\*\*[^*]+\*\*:")
INLINE_CODE_SEGMENT_PATTERN = re.compile(r"`[^`\n]+`")
INLINE_CODE_DOUBLE_TICK_PATTERN = re.compile(r"``.+?``")
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\([^)]*\)")
BARE_URL_PATTERN = re.compile(r"https?://\S+")
EXAMPLE_DIALOGUE_HEADING_TEXT = "example dialogue"

DEFAULT_PROHIBITED_PRONOUN_PATTERNS = (
    re.compile(r"\byou\b", re.IGNORECASE),
    re.compile(r"\byour\b", re.IGNORECASE),
    re.compile(r"\bwe\b", re.IGNORECASE),
    re.compile(r"\bour\b", re.IGNORECASE),
)
DEFAULT_PROHIBITED_SLANG_PATTERNS = (
    re.compile(r"\beasy\b", re.IGNORECASE),
    re.compile(r"\bsimple\b", re.IGNORECASE),
    re.compile(r"\bjust\b", re.IGNORECASE),
)


class ProseStyleViolationKind(str, Enum):
    EXCESS_STRONG_EMPHASIS = "excess_strong_emphasis"
    PROHIBITED_PROSE_PATTERN = "prohibited_prose_pattern"


@dataclass(frozen=True)
class ProseLine:
    line_number: int
    line_text: str


@dataclass(frozen=True)
class ProseStyleCandidate:
    document_path: str
    line_number: int
    kind: ProseStyleViolationKind
    detail: str


def is_markdown_table_row(line_text: str) -> bool:
    stripped_line_text = line_text.strip()
    if not stripped_line_text:
        return False
    if "|" not in stripped_line_text:
        return False
    if stripped_line_text.startswith("|"):
        return True
    if re.match(r"^:?-{3,}:?(?:\s*\|\s*:?-{3,}:?)*\s*$", stripped_line_text):
        return True
    pipe_count = stripped_line_text.count("|")
    return pipe_count >= 2


def resolve_front_matter_end_line_index(raw_lines: list[str]) -> int | None:
    if len(raw_lines) < 3:
        return None
    if raw_lines[0].strip() != YAML_FRONT_MATTER_DELIMITER:
        return None
    for line_index in range(1, len(raw_lines)):
        if raw_lines[line_index].strip() == YAML_FRONT_MATTER_DELIMITER:
            return line_index
    return None


def resolve_example_dialogue_start_line(headings: tuple[Heading, ...]) -> int | None:
    for heading in headings:
        if heading.level != 2:
            continue
        if heading.text.strip().lower() == EXAMPLE_DIALOGUE_HEADING_TEXT:
            return heading.line_number
    return None


def is_inside_example_dialogue_section(
    headings: tuple[Heading, ...],
    line_number: int,
) -> bool:
    example_dialogue_start_line = resolve_example_dialogue_start_line(headings)
    if example_dialogue_start_line is None:
        return False
    return line_number >= example_dialogue_start_line


def is_glossary_term_line(line_text: str) -> bool:
    return GLOSSARY_TERM_LINE_PATTERN.match(line_text.strip()) is not None


def extract_prose_lines(parsed_document: ParsedMarkdownDocument) -> tuple[ProseLine, ...]:
    raw_lines = parsed_document.raw_text.splitlines()
    front_matter_end_line_index = resolve_front_matter_end_line_index(raw_lines)
    prose_lines: list[ProseLine] = []
    inside_code_block = False

    for line_index, line_text in enumerate(raw_lines, start=1):
        if line_text.strip().startswith("```"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue
        if front_matter_end_line_index is not None and line_index <= front_matter_end_line_index:
            continue
        if parse_heading_line(line_text, line_index) is not None:
            continue
        if is_markdown_table_row(line_text):
            continue
        if is_glossary_term_line(line_text):
            continue
        if is_inside_example_dialogue_section(parsed_document.headings, line_index):
            continue
        if line_text.strip() == "":
            continue
        prose_lines.append(ProseLine(line_number=line_index, line_text=line_text))

    return tuple(prose_lines)


def strip_inline_code_segments(line_text: str) -> str:
    text_without_double_tick_code = INLINE_CODE_DOUBLE_TICK_PATTERN.sub("", line_text)
    return INLINE_CODE_SEGMENT_PATTERN.sub("", text_without_double_tick_code)


def mask_inline_code_segments(line_text: str) -> str:
    text_with_masked_double_tick_code = INLINE_CODE_DOUBLE_TICK_PATTERN.sub(
        "INLINE_CODE",
        line_text,
    )
    return INLINE_CODE_SEGMENT_PATTERN.sub(
        "INLINE_CODE",
        text_with_masked_double_tick_code,
    )


def count_strong_emphasis_pairs(line_text: str) -> int:
    text_with_masked_inline_code = mask_inline_code_segments(line_text)
    return len(CLOSED_STRONG_EMPHASIS_PATTERN.findall(text_with_masked_inline_code))


def count_document_strong_emphasis_pairs(prose_lines: tuple[ProseLine, ...]) -> int:
    return sum(count_strong_emphasis_pairs(prose_line.line_text) for prose_line in prose_lines)


def strip_markdown_links_and_urls(line_text: str) -> str:
    text_without_links = MARKDOWN_LINK_PATTERN.sub("", line_text)
    return BARE_URL_PATTERN.sub("", text_without_links)


def build_allowed_prose_phrase_text(line_text: str, allowed_prose_phrases: tuple[str, ...]) -> str:
    normalized_line_text = line_text
    for allowed_phrase in allowed_prose_phrases:
        normalized_line_text = normalized_line_text.replace(allowed_phrase, "")
    return normalized_line_text


def compile_prohibited_prose_patterns(
    extra_prohibited_prose_patterns: tuple[str, ...],
) -> tuple[re.Pattern[str], ...]:
    compiled_patterns: list[re.Pattern[str]] = []
    for pattern_text in extra_prohibited_prose_patterns:
        compiled_patterns.append(re.compile(pattern_text, re.IGNORECASE))
    return tuple(compiled_patterns)


def find_prohibited_prose_pattern_matches(
    line_text: str,
    allowed_prose_phrases: tuple[str, ...],
    extra_prohibited_prose_patterns: tuple[re.Pattern[str], ...],
) -> tuple[str, ...]:
    language_guard_text = strip_markdown_links_and_urls(line_text)
    language_guard_text = strip_inline_code_segments(language_guard_text)
    language_guard_text = build_allowed_prose_phrase_text(
        language_guard_text,
        allowed_prose_phrases,
    )
    matched_patterns: list[str] = []
    all_patterns = (
        *DEFAULT_PROHIBITED_PRONOUN_PATTERNS,
        *DEFAULT_PROHIBITED_SLANG_PATTERNS,
        *extra_prohibited_prose_patterns,
    )
    for prohibited_pattern in all_patterns:
        if prohibited_pattern.search(language_guard_text) is None:
            continue
        matched_patterns.append(prohibited_pattern.pattern)
    return tuple(matched_patterns)


def should_skip_prose_style_for_document(
    inspection_context: DocumentInspectionContext,
) -> bool:
    return inspection_context.document_type is not None


def resolve_max_strong_emphasis_pairs(
    configuration: DocguardConfiguration,
) -> int:
    return configuration.max_strong_emphasis_pairs


def collect_prose_style_candidates(
    configuration: DocguardConfiguration,
    document_contexts: tuple[DocumentInspectionContext, ...],
) -> tuple[ProseStyleCandidate, ...]:
    candidates: list[ProseStyleCandidate] = []
    max_strong_emphasis_pairs = resolve_max_strong_emphasis_pairs(configuration)
    extra_prohibited_patterns = compile_prohibited_prose_patterns(
        configuration.extra_prohibited_prose_patterns,
    )

    for inspection_context in document_contexts:
        if should_skip_prose_style_for_document(inspection_context):
            continue

        parsed_document = inspection_context.parsed_document
        prose_lines = extract_prose_lines(parsed_document)
        strong_emphasis_pair_count = count_document_strong_emphasis_pairs(prose_lines)
        if strong_emphasis_pair_count > max_strong_emphasis_pairs:
            candidates.append(
                ProseStyleCandidate(
                    document_path=parsed_document.repository_relative_path,
                    line_number=prose_lines[0].line_number if prose_lines else 1,
                    kind=ProseStyleViolationKind.EXCESS_STRONG_EMPHASIS,
                    detail=(
                        f"{strong_emphasis_pair_count} pairs "
                        f"(limit {max_strong_emphasis_pairs})"
                    ),
                )
            )

        for prose_line in prose_lines:
            matched_patterns = find_prohibited_prose_pattern_matches(
                prose_line.line_text,
                configuration.allowed_prose_phrases,
                extra_prohibited_patterns,
            )
            if not matched_patterns:
                continue
            candidates.append(
                ProseStyleCandidate(
                    document_path=parsed_document.repository_relative_path,
                    line_number=prose_line.line_number,
                    kind=ProseStyleViolationKind.PROHIBITED_PROSE_PATTERN,
                    detail=matched_patterns[0],
                )
            )

    return tuple(candidates)


def check_prose_style(
    configuration: DocguardConfiguration,
    inspection_context: DocumentInspectionContext,
) -> list[Diagnostic]:
    if should_skip_prose_style_for_document(inspection_context):
        return []

    parsed_document = inspection_context.parsed_document
    prose_lines = extract_prose_lines(parsed_document)
    diagnostics: list[Diagnostic] = []
    max_strong_emphasis_pairs = resolve_max_strong_emphasis_pairs(configuration)
    extra_prohibited_patterns = compile_prohibited_prose_patterns(
        configuration.extra_prohibited_prose_patterns,
    )

    strong_emphasis_pair_count = count_document_strong_emphasis_pairs(prose_lines)
    if strong_emphasis_pair_count > max_strong_emphasis_pairs:
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_EXCESS_STRONG_EMPHASIS,
                    configuration.severities,
                ),
                document_path=parsed_document.repository_relative_path,
                message=(
                    f"{parsed_document.repository_relative_path} has "
                    f"{strong_emphasis_pair_count} strong emphasis pairs in prose. "
                    f"Limit: {max_strong_emphasis_pairs}."
                ),
                why_it_matters=WHY_EXCESS_STRONG_EMPHASIS,
                suggestion=SUGGESTION_EXCESS_STRONG_EMPHASIS,
            )
        )

    for prose_line in prose_lines:
        matched_patterns = find_prohibited_prose_pattern_matches(
            prose_line.line_text,
            configuration.allowed_prose_phrases,
            extra_prohibited_patterns,
        )
        if not matched_patterns:
            continue
        diagnostics.append(
            Diagnostic(
                code=DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
                severity=resolve_severity_for_code(
                    DIAGNOSTIC_CODE_PROHIBITED_PROSE_PATTERN,
                    configuration.severities,
                ),
                document_path=parsed_document.repository_relative_path,
                message=(
                    f"Prohibited prose pattern matched at line {prose_line.line_number}: "
                    f"{matched_patterns[0]}"
                ),
                why_it_matters=WHY_PROHIBITED_PROSE_PATTERN,
                suggestion=SUGGESTION_PROHIBITED_PROSE_PATTERN,
                location=f"line {prose_line.line_number}",
            )
        )

    return diagnostics
