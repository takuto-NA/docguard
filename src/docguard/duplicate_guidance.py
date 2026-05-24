"""Duplicate guidance detection across scanned Markdown documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from docguard.constants import (
    DEFAULT_DUPLICATE_GUIDANCE_KINDS,
)
from docguard.markdown import (
    extract_headings,
    normalize_heading_text,
    parse_heading_line,
)
from docguard.models import DocumentInspectionContext, ParsedMarkdownDocument

FENCED_CODE_BLOCK_OPEN_PATTERN = re.compile(r"^\s*```")
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(.*)$")
SHELL_COMMENT_LINE_PATTERN = re.compile(r"^\s*#")
MARKDOWN_TABLE_ROW_PATTERN = re.compile(r"^\s*\|")

MINIMUM_CODE_BLOCK_NON_EMPTY_LINE_COUNT = 2
MINIMUM_DUPLICATE_CODE_BLOCK_OCCURRENCES = 2
MINIMUM_DUPLICATE_HEADING_OCCURRENCES = 3
MINIMUM_DUPLICATE_LIST_ITEM_OCCURRENCES = 3
MINIMUM_DUPLICATE_PARAGRAPH_OCCURRENCES = 3
MINIMUM_PARAGRAPH_CHARACTER_COUNT = 80
MAXIMUM_OCCURRENCE_REFERENCES_IN_MESSAGE = 3


class GuidanceAtomKind(str, Enum):
    CODE_BLOCK = "code_block"
    HEADING = "heading"
    LIST_ITEM = "list_item"
    PARAGRAPH = "paragraph"


@dataclass(frozen=True)
class GuidanceAtom:
    kind: GuidanceAtomKind
    normalized_text: str
    document_path: str
    line_number: int


@dataclass(frozen=True)
class DuplicateGuidanceGroup:
    kind: GuidanceAtomKind
    normalized_text: str
    atoms: tuple[GuidanceAtom, ...]


def compile_allowed_duplicate_patterns(
    allowed_duplicate_patterns: tuple[str, ...],
) -> tuple[re.Pattern[str], ...]:
    compiled_patterns: list[re.Pattern[str]] = []
    for pattern_index, raw_pattern in enumerate(allowed_duplicate_patterns):
        try:
            compiled_patterns.append(re.compile(raw_pattern))
        except re.error as error:
            raise ValueError(
                "allowed_duplicate_patterns["
                f"{pattern_index}] is not a valid regular expression: {raw_pattern}"
            ) from error
    return tuple(compiled_patterns)


def is_duplicate_text_allowed(
    normalized_text: str,
    compiled_allowed_patterns: tuple[re.Pattern[str], ...],
) -> bool:
    for compiled_pattern in compiled_allowed_patterns:
        if compiled_pattern.search(normalized_text):
            return True
    return False


def collapse_consecutive_blank_lines(raw_lines: list[str]) -> list[str]:
    collapsed_lines: list[str] = []
    previous_line_was_blank = False
    for raw_line in raw_lines:
        current_line_is_blank = raw_line.strip() == ""
        if current_line_is_blank and previous_line_was_blank:
            continue
        collapsed_lines.append(raw_line)
        previous_line_was_blank = current_line_is_blank
    return collapsed_lines


def strip_leading_and_trailing_blank_lines(raw_lines: list[str]) -> list[str]:
    start_index = 0
    end_index = len(raw_lines)
    while start_index < end_index and raw_lines[start_index].strip() == "":
        start_index += 1
    while end_index > start_index and raw_lines[end_index - 1].strip() == "":
        end_index -= 1
    return raw_lines[start_index:end_index]


def normalize_code_block(raw_lines: list[str]) -> str:
    trimmed_lines = [raw_line.rstrip() for raw_line in raw_lines]
    trimmed_lines = [
        raw_line
        for raw_line in trimmed_lines
        if not SHELL_COMMENT_LINE_PATTERN.match(raw_line)
    ]
    trimmed_lines = strip_leading_and_trailing_blank_lines(trimmed_lines)
    trimmed_lines = collapse_consecutive_blank_lines(trimmed_lines)
    return "\n".join(trimmed_lines).strip()


def count_non_empty_lines(raw_lines: list[str]) -> int:
    non_empty_line_count = 0
    for raw_line in raw_lines:
        if raw_line.strip() == "":
            continue
        non_empty_line_count += 1
    return non_empty_line_count


def extract_fenced_code_blocks(
    raw_lines: list[str],
) -> tuple[tuple[int, list[str]], ...]:
    fenced_code_blocks: list[tuple[int, list[str]]] = []
    block_start_line_number: int | None = None
    block_lines: list[str] = []
    inside_code_block = False

    for line_index, line_text in enumerate(raw_lines, start=1):
        if FENCED_CODE_BLOCK_OPEN_PATTERN.match(line_text):
            if not inside_code_block:
                inside_code_block = True
                block_start_line_number = line_index
                block_lines = []
                continue
            fenced_code_blocks.append((block_start_line_number, block_lines))
            inside_code_block = False
            block_start_line_number = None
            block_lines = []
            continue
        if inside_code_block:
            block_lines.append(line_text)

    return tuple(fenced_code_blocks)


def normalize_list_item_text(raw_list_item_text: str) -> str:
    collapsed_whitespace_text = " ".join(raw_list_item_text.strip().split())
    return collapsed_whitespace_text


def normalize_paragraph_text(raw_paragraph_text: str) -> str:
    collapsed_whitespace_text = " ".join(raw_paragraph_text.strip().split())
    return collapsed_whitespace_text


def resolve_front_matter_end_line_number(raw_lines: list[str]) -> int | None:
    if len(raw_lines) < 3:
        return None
    if raw_lines[0].strip() != "---":
        return None
    for line_index in range(1, len(raw_lines)):
        if raw_lines[line_index].strip() == "---":
            return line_index + 1
    return None


def is_non_prose_paragraph_line(line_text: str) -> bool:
    if parse_heading_line(line_text, line_number=0) is not None:
        return True
    if LIST_ITEM_PATTERN.match(line_text) is not None:
        return True
    if MARKDOWN_TABLE_ROW_PATTERN.match(line_text) is not None:
        return True
    return False


def extract_paragraphs(raw_lines: list[str]) -> tuple[tuple[int, str], ...]:
    paragraphs: list[tuple[int, str]] = []
    inside_code_block = False
    front_matter_end_line_number = resolve_front_matter_end_line_number(raw_lines)
    paragraph_buffer: list[str] = []
    paragraph_start_line_number: int | None = None

    for line_index, line_text in enumerate(raw_lines, start=1):
        if (
            front_matter_end_line_number is not None
            and line_index <= front_matter_end_line_number
        ):
            continue

        if FENCED_CODE_BLOCK_OPEN_PATTERN.match(line_text):
            if paragraph_buffer:
                raw_paragraph_text = "\n".join(paragraph_buffer)
                paragraphs.append((paragraph_start_line_number, raw_paragraph_text))
                paragraph_buffer = []
                paragraph_start_line_number = None
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue

        if line_text.strip() == "":
            if paragraph_buffer:
                raw_paragraph_text = "\n".join(paragraph_buffer)
                paragraphs.append((paragraph_start_line_number, raw_paragraph_text))
                paragraph_buffer = []
                paragraph_start_line_number = None
            continue

        if is_non_prose_paragraph_line(line_text):
            if paragraph_buffer:
                raw_paragraph_text = "\n".join(paragraph_buffer)
                paragraphs.append((paragraph_start_line_number, raw_paragraph_text))
                paragraph_buffer = []
                paragraph_start_line_number = None
            continue

        if paragraph_start_line_number is None:
            paragraph_start_line_number = line_index
        paragraph_buffer.append(line_text)

    if paragraph_buffer and paragraph_start_line_number is not None:
        raw_paragraph_text = "\n".join(paragraph_buffer)
        paragraphs.append((paragraph_start_line_number, raw_paragraph_text))

    return tuple(paragraphs)


def extract_list_items(raw_lines: list[str]) -> tuple[tuple[int, str], ...]:
    list_items: list[tuple[int, str]] = []
    inside_code_block = False

    for line_index, line_text in enumerate(raw_lines, start=1):
        if FENCED_CODE_BLOCK_OPEN_PATTERN.match(line_text):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue

        list_item_match = LIST_ITEM_PATTERN.match(line_text)
        if list_item_match is None:
            continue
        list_items.append((line_index, list_item_match.group(1)))

    return tuple(list_items)


def collect_code_block_atoms(
    parsed_document: ParsedMarkdownDocument,
) -> tuple[GuidanceAtom, ...]:
    raw_lines = parsed_document.raw_text.splitlines()
    code_block_atoms: list[GuidanceAtom] = []

    for block_start_line_number, block_lines in extract_fenced_code_blocks(raw_lines):
        normalized_code_block = normalize_code_block(block_lines)
        if normalized_code_block == "":
            continue
        normalized_lines = normalized_code_block.splitlines()
        if count_non_empty_lines(normalized_lines) < MINIMUM_CODE_BLOCK_NON_EMPTY_LINE_COUNT:
            continue
        code_block_atoms.append(
            GuidanceAtom(
                kind=GuidanceAtomKind.CODE_BLOCK,
                normalized_text=normalized_code_block,
                document_path=parsed_document.repository_relative_path,
                line_number=block_start_line_number,
            )
        )

    return tuple(code_block_atoms)


def collect_heading_atoms(
    parsed_document: ParsedMarkdownDocument,
) -> tuple[GuidanceAtom, ...]:
    heading_atoms: list[GuidanceAtom] = []

    for heading in extract_headings(parsed_document.raw_text.splitlines()):
        if heading.level == 1:
            continue
        heading_atoms.append(
            GuidanceAtom(
                kind=GuidanceAtomKind.HEADING,
                normalized_text=normalize_heading_text(heading.text),
                document_path=parsed_document.repository_relative_path,
                line_number=heading.line_number,
            )
        )

    return tuple(heading_atoms)


def collect_list_item_atoms(
    parsed_document: ParsedMarkdownDocument,
) -> tuple[GuidanceAtom, ...]:
    raw_lines = parsed_document.raw_text.splitlines()
    list_item_atoms: list[GuidanceAtom] = []

    for line_number, raw_list_item_text in extract_list_items(raw_lines):
        normalized_list_item_text = normalize_list_item_text(raw_list_item_text)
        if normalized_list_item_text == "":
            continue
        list_item_atoms.append(
            GuidanceAtom(
                kind=GuidanceAtomKind.LIST_ITEM,
                normalized_text=normalized_list_item_text,
                document_path=parsed_document.repository_relative_path,
                line_number=line_number,
            )
        )

    return tuple(list_item_atoms)


def collect_paragraph_atoms(
    parsed_document: ParsedMarkdownDocument,
) -> tuple[GuidanceAtom, ...]:
    raw_lines = parsed_document.raw_text.splitlines()
    paragraph_atoms: list[GuidanceAtom] = []

    for line_number, raw_paragraph_text in extract_paragraphs(raw_lines):
        normalized_paragraph_text = normalize_paragraph_text(raw_paragraph_text)
        if normalized_paragraph_text == "":
            continue
        if len(normalized_paragraph_text) < MINIMUM_PARAGRAPH_CHARACTER_COUNT:
            continue
        paragraph_atoms.append(
            GuidanceAtom(
                kind=GuidanceAtomKind.PARAGRAPH,
                normalized_text=normalized_paragraph_text,
                document_path=parsed_document.repository_relative_path,
                line_number=line_number,
            )
        )

    return tuple(paragraph_atoms)


def guidance_atom_kind_from_configuration_name(
    configuration_kind_name: str,
) -> GuidanceAtomKind:
    if configuration_kind_name == GuidanceAtomKind.CODE_BLOCK.value:
        return GuidanceAtomKind.CODE_BLOCK
    if configuration_kind_name == GuidanceAtomKind.HEADING.value:
        return GuidanceAtomKind.HEADING
    if configuration_kind_name == GuidanceAtomKind.LIST_ITEM.value:
        return GuidanceAtomKind.LIST_ITEM
    if configuration_kind_name == GuidanceAtomKind.PARAGRAPH.value:
        return GuidanceAtomKind.PARAGRAPH
    raise ValueError(
        "duplicate_guidance_kinds contains unsupported value: "
        f"{configuration_kind_name}"
    )


def resolve_enabled_guidance_atom_kinds(
    duplicate_guidance_kinds: tuple[str, ...],
) -> frozenset[GuidanceAtomKind]:
    enabled_guidance_atom_kinds: set[GuidanceAtomKind] = set()
    for configuration_kind_name in duplicate_guidance_kinds:
        enabled_guidance_atom_kinds.add(
            guidance_atom_kind_from_configuration_name(configuration_kind_name)
        )
    return frozenset(enabled_guidance_atom_kinds)


def collect_guidance_atoms(
    parsed_document: ParsedMarkdownDocument,
    enabled_guidance_atom_kinds: frozenset[GuidanceAtomKind],
) -> tuple[GuidanceAtom, ...]:
    guidance_atoms: list[GuidanceAtom] = []
    if GuidanceAtomKind.CODE_BLOCK in enabled_guidance_atom_kinds:
        guidance_atoms.extend(collect_code_block_atoms(parsed_document))
    if GuidanceAtomKind.HEADING in enabled_guidance_atom_kinds:
        guidance_atoms.extend(collect_heading_atoms(parsed_document))
    if GuidanceAtomKind.LIST_ITEM in enabled_guidance_atom_kinds:
        guidance_atoms.extend(collect_list_item_atoms(parsed_document))
    if GuidanceAtomKind.PARAGRAPH in enabled_guidance_atom_kinds:
        guidance_atoms.extend(collect_paragraph_atoms(parsed_document))
    return tuple(guidance_atoms)


def minimum_duplicate_occurrences_for_kind(kind: GuidanceAtomKind) -> int:
    if kind is GuidanceAtomKind.CODE_BLOCK:
        return MINIMUM_DUPLICATE_CODE_BLOCK_OCCURRENCES
    if kind is GuidanceAtomKind.HEADING:
        return MINIMUM_DUPLICATE_HEADING_OCCURRENCES
    if kind is GuidanceAtomKind.PARAGRAPH:
        return MINIMUM_DUPLICATE_PARAGRAPH_OCCURRENCES
    return MINIMUM_DUPLICATE_LIST_ITEM_OCCURRENCES


def group_guidance_atoms_by_kind_and_text(
    guidance_atoms: tuple[GuidanceAtom, ...],
) -> dict[tuple[GuidanceAtomKind, str], list[GuidanceAtom]]:
    grouped_atoms: dict[tuple[GuidanceAtomKind, str], list[GuidanceAtom]] = {}
    for guidance_atom in guidance_atoms:
        grouping_key = (guidance_atom.kind, guidance_atom.normalized_text)
        grouped_atoms.setdefault(grouping_key, []).append(guidance_atom)
    return grouped_atoms


def collect_duplicate_guidance_groups(
    document_contexts: tuple[DocumentInspectionContext, ...],
    allowed_duplicate_patterns: tuple[str, ...],
    duplicate_guidance_kinds: tuple[str, ...] = DEFAULT_DUPLICATE_GUIDANCE_KINDS,
) -> tuple[DuplicateGuidanceGroup, ...]:
    compiled_allowed_patterns = compile_allowed_duplicate_patterns(
        allowed_duplicate_patterns
    )
    enabled_guidance_atom_kinds = resolve_enabled_guidance_atom_kinds(
        duplicate_guidance_kinds
    )
    all_guidance_atoms: list[GuidanceAtom] = []
    for inspection_context in document_contexts:
        all_guidance_atoms.extend(
            collect_guidance_atoms(
                inspection_context.parsed_document,
                enabled_guidance_atom_kinds,
            )
        )

    duplicate_groups: list[DuplicateGuidanceGroup] = []
    grouped_atoms = group_guidance_atoms_by_kind_and_text(tuple(all_guidance_atoms))

    for (kind, normalized_text), atoms in sorted(grouped_atoms.items()):
        if is_duplicate_text_allowed(normalized_text, compiled_allowed_patterns):
            continue
        if len(atoms) < minimum_duplicate_occurrences_for_kind(kind):
            continue
        sorted_atoms = tuple(
            sorted(
                atoms,
                key=lambda atom: (atom.document_path, atom.line_number),
            )
        )
        duplicate_groups.append(
            DuplicateGuidanceGroup(
                kind=kind,
                normalized_text=normalized_text,
                atoms=sorted_atoms,
            )
        )

    return tuple(duplicate_groups)


def format_duplicate_occurrence_references(
    duplicate_group: DuplicateGuidanceGroup,
) -> str:
    occurrence_references = [
        f"{atom.document_path}:{atom.line_number}"
        for atom in duplicate_group.atoms[:MAXIMUM_OCCURRENCE_REFERENCES_IN_MESSAGE]
    ]
    return ", ".join(occurrence_references)
