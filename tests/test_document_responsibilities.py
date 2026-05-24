"""Dogfood gate tests for document responsibility boundaries.

Ensures README stays an entry-point summary and does not absorb detailed
reference responsibilities owned by docs/usage.md and phase-specific rule pages.
"""

from __future__ import annotations

import re
from pathlib import Path

README_RELATIVE_PATH = "README.md"
WHAT_THIS_TOOL_CHECKS_HEADING = "## What this tool checks"

# Any third-level heading under the summary section indicates leaked detail pages.
FORBIDDEN_README_SUMMARY_SUBHEADING_PATTERN = re.compile(r"^### .+$", re.MULTILINE)

# Full diagnostic catalog tables belong in docs/usage.md, not README.
FORBIDDEN_README_DIAGNOSTIC_TABLE_HEADER = "| Code | Check |"
FORBIDDEN_README_PHASE_DEFAULT_TABLE_HEADER = "| Code | Check | Default |"

# Detail markers that belong in canonical pages, not README.
FORBIDDEN_README_DETAIL_MARKERS = (
    "how these checks differ from reachability",
    "With Phase 3 enabled you can:",
    "You can scan from the CLI, emit JSON for CI, override severity per rule",
)

# README should report current scope, not use a future-plan heading for status text.
FORBIDDEN_README_ROADMAP_HEADING = "## Roadmap"
ALLOWED_README_STATUS_HEADINGS = ("## Status", "## Current scope")

# README may keep one phase summary table aligned with docs/usage.md.
REQUIRED_README_PHASE_SUMMARY_TABLE_HEADER = "| Phase | What you can check | Diagnostics | Typical default |"


def resolve_repository_root() -> Path:
    repository_root = Path(__file__).resolve().parents[1]
    return repository_root


def read_readme_text() -> str:
    readme_path = resolve_repository_root() / README_RELATIVE_PATH
    return readme_path.read_text(encoding="utf-8")


def extract_section_after_heading(document_text: str, heading: str) -> str:
    heading_start = document_text.find(heading)
    if heading_start == -1:
        return ""

    section_start = heading_start + len(heading)
    next_heading_match = re.search(r"\n## ", document_text[section_start:])
    if next_heading_match is None:
        return document_text[section_start:]
    section_end = section_start + next_heading_match.start()
    return document_text[section_start:section_end]


def collect_forbidden_summary_subheadings(readme_text: str) -> list[str]:
    what_this_tool_checks_section = extract_section_after_heading(
        readme_text,
        WHAT_THIS_TOOL_CHECKS_HEADING,
    )
    return FORBIDDEN_README_SUMMARY_SUBHEADING_PATTERN.findall(
        what_this_tool_checks_section
    )


def collect_forbidden_diagnostic_tables(readme_text: str) -> list[str]:
    what_this_tool_checks_section = extract_section_after_heading(
        readme_text,
        WHAT_THIS_TOOL_CHECKS_HEADING,
    )
    forbidden_tables_found: list[str] = []
    if FORBIDDEN_README_DIAGNOSTIC_TABLE_HEADER in what_this_tool_checks_section:
        forbidden_tables_found.append(FORBIDDEN_README_DIAGNOSTIC_TABLE_HEADER)
    if FORBIDDEN_README_PHASE_DEFAULT_TABLE_HEADER in what_this_tool_checks_section:
        forbidden_tables_found.append(FORBIDDEN_README_PHASE_DEFAULT_TABLE_HEADER)
    return forbidden_tables_found


def collect_forbidden_detail_markers(readme_text: str) -> list[str]:
    what_this_tool_checks_section = extract_section_after_heading(
        readme_text,
        WHAT_THIS_TOOL_CHECKS_HEADING,
    )
    forbidden_markers_found: list[str] = []
    for forbidden_marker in FORBIDDEN_README_DETAIL_MARKERS:
        if forbidden_marker in what_this_tool_checks_section:
            forbidden_markers_found.append(forbidden_marker)
    return forbidden_markers_found


def collect_status_heading_violations(readme_text: str) -> list[str]:
    violations: list[str] = []
    if FORBIDDEN_README_ROADMAP_HEADING in readme_text:
        violations.append(
            f"uses '{FORBIDDEN_README_ROADMAP_HEADING}' instead of a status heading"
        )
    if not any(
        allowed_heading in readme_text
        for allowed_heading in ALLOWED_README_STATUS_HEADINGS
    ):
        violations.append(
            f"missing one of: {ALLOWED_README_STATUS_HEADINGS}"
        )
    return violations


def test_readme_does_not_include_summary_subheadings() -> None:
    readme_text = read_readme_text()
    forbidden_subheadings_found = collect_forbidden_summary_subheadings(readme_text)

    assert forbidden_subheadings_found == [], (
        "README must not include detail subheadings under "
        f"'{WHAT_THIS_TOOL_CHECKS_HEADING}'. Found: {forbidden_subheadings_found}"
    )


def test_readme_does_not_include_detailed_diagnostic_tables() -> None:
    readme_text = read_readme_text()
    forbidden_tables_found = collect_forbidden_diagnostic_tables(readme_text)

    assert forbidden_tables_found == [], (
        "README must not include full diagnostic catalog tables. "
        f"Use a phase summary table and link to docs/usage.md. Found: {forbidden_tables_found}"
    )


def test_readme_does_not_include_forbidden_detail_markers() -> None:
    readme_text = read_readme_text()
    forbidden_markers_found = collect_forbidden_detail_markers(readme_text)

    assert forbidden_markers_found == [], (
        "README must not include detailed rule or configuration explanations. "
        "Link to docs/usage.md and phase-specific rule pages instead. "
        f"Found: {forbidden_markers_found}"
    )


def test_readme_uses_status_heading_instead_of_roadmap() -> None:
    readme_text = read_readme_text()
    status_heading_violations = collect_status_heading_violations(readme_text)

    assert status_heading_violations == [], (
        "README must use a current-scope heading. "
        f"Violations: {status_heading_violations}"
    )


def test_readme_includes_phase_summary_table() -> None:
    readme_text = read_readme_text()
    what_this_tool_checks_section = extract_section_after_heading(
        readme_text,
        WHAT_THIS_TOOL_CHECKS_HEADING,
    )

    assert REQUIRED_README_PHASE_SUMMARY_TABLE_HEADER in what_this_tool_checks_section, (
        "README must include a single phase summary table under "
        f"'{WHAT_THIS_TOOL_CHECKS_HEADING}'."
    )
