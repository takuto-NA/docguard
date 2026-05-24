"""Regression tests for docs/usage.md canonical guidance ownership.

Verifies the four duplicate-guidance feedback categories stay resolved:
install, CLI/pytest blocks, configuration examples, and flag/exit-code prose.
"""

from __future__ import annotations

import re
from pathlib import Path

USAGE_RELATIVE_PATH = "docs/usage.md"

INSTALL_HEADING = "## Install"
USE_IN_ANOTHER_REPOSITORY_HEADING = "## Use in another repository"
WHAT_YOU_CAN_DO_HEADING = "## What you can do today"
SCAN_CLI_HEADING = "## Scan Markdown from the CLI"
PYTEST_HEADING = "## Run the same checks through pytest"
OUTPUT_MODES_HEADING = "## Output modes"
EXIT_CODES_HEADING = "## Use predictable CI exit codes"
UNICODE_HEADING = "## Unicode and UTF-8 support"
PHASE_15_HEADING = "## Phase 1.5 UX and reliability"
CONFIGURATION_HEADING = "## Configuration"

FULL_CONFIGURATION_MARKER = 'paths = ["docs", "adr", "README.md"]'

CANONICAL_CLI_COMMAND_MARKERS = (
    "docguard docs/ --summary",
    "docguard docs/ --format json",
)

CANONICAL_PYTEST_COMMAND_MARKERS = (
    "pytest --docguard",
    "pytest --docguard-only",
)

OUTPUT_MODE_FLAG_RULES_OWNED_BY_OUTPUT_MODES_SECTION = (
    "`--quiet` cannot be combined with `--summary` or `--verbose`",
    "`--verbose` cannot be used with `--format json`",
)

PHASE_15_FORBIDDEN_EXIT_CODE_EXPLANATIONS = (
    "invalid configuration is rejected before scanning",
    "non-UTF-8 Markdown files fail during discovery",
    "missing, out-of-project, or non-Markdown explicit CLI paths exit with code `2`",
)


def resolve_repository_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_usage_text() -> str:
    usage_path = resolve_repository_root() / USAGE_RELATIVE_PATH
    return usage_path.read_text(encoding="utf-8")


def extract_section_between_headings(
    document_text: str,
    section_heading: str,
    next_section_heading: str | None = None,
) -> str:
    section_start = document_text.find(section_heading)
    if section_start == -1:
        return ""

    content_start = section_start + len(section_heading)
    if next_section_heading is None:
        return document_text[content_start:]

    next_section_start = document_text.find(next_section_heading, content_start)
    if next_section_start == -1:
        return document_text[content_start:]
    return document_text[content_start:next_section_start]


def count_fenced_code_blocks(section_text: str) -> int:
    return len(re.findall(r"^\s*```", section_text, flags=re.MULTILINE)) // 2


def count_fenced_blocks_containing_all_markers(
    section_text: str,
    required_markers: tuple[str, ...],
) -> int:
    fenced_blocks = re.findall(
        r"```[^\n]*\n(.*?)```",
        section_text,
        flags=re.DOTALL,
    )
    matching_block_count = 0
    for fenced_block in fenced_blocks:
        if all(marker in fenced_block for marker in required_markers):
            matching_block_count += 1
    return matching_block_count


def test_use_in_another_repository_links_to_install_without_install_blocks() -> None:
    usage_text = read_usage_text()
    adoption_section = extract_section_between_headings(
        usage_text,
        USE_IN_ANOTHER_REPOSITORY_HEADING,
        WHAT_YOU_CAN_DO_HEADING,
    )

    assert "[Install](#install)" in adoption_section
    assert count_fenced_blocks_containing_all_markers(
        adoption_section,
        ("uv add docguard",),
    ) == 0
    assert count_fenced_blocks_containing_all_markers(
        adoption_section,
        ("pip install docguard",),
    ) == 0


def test_usage_has_one_canonical_install_section() -> None:
    usage_text = read_usage_text()
    install_section = extract_section_between_headings(
        usage_text,
        INSTALL_HEADING,
        USE_IN_ANOTHER_REPOSITORY_HEADING,
    )

    assert count_fenced_blocks_containing_all_markers(
        install_section,
        ("uv add docguard", "uv run docguard docs/ --summary"),
    ) == 1
    assert count_fenced_blocks_containing_all_markers(
        install_section,
        ("pip install docguard", "docguard docs/ --summary"),
    ) == 1


def test_usage_has_one_canonical_cli_block_and_one_pytest_block() -> None:
    usage_text = read_usage_text()
    cli_section = extract_section_between_headings(
        usage_text,
        SCAN_CLI_HEADING,
        OUTPUT_MODES_HEADING,
    )
    pytest_section = extract_section_between_headings(
        usage_text,
        PYTEST_HEADING,
        EXIT_CODES_HEADING,
    )
    what_you_can_do_section = extract_section_between_headings(
        usage_text,
        WHAT_YOU_CAN_DO_HEADING,
        SCAN_CLI_HEADING,
    )
    unicode_section = extract_section_between_headings(
        usage_text,
        UNICODE_HEADING,
        PHASE_15_HEADING,
    )

    assert count_fenced_blocks_containing_all_markers(
        cli_section,
        CANONICAL_CLI_COMMAND_MARKERS,
    ) == 1
    assert count_fenced_blocks_containing_all_markers(
        pytest_section,
        CANONICAL_PYTEST_COMMAND_MARKERS,
    ) == 1
    assert count_fenced_code_blocks(what_you_can_do_section) == 0
    assert count_fenced_blocks_containing_all_markers(
        what_you_can_do_section,
        ("docguard docs/",),
    ) == 0
    assert count_fenced_blocks_containing_all_markers(
        unicode_section,
        ("docguard docs/",),
    ) == 0
    assert count_fenced_blocks_containing_all_markers(
        unicode_section,
        CANONICAL_PYTEST_COMMAND_MARKERS,
    ) == 0


def test_usage_has_one_full_configuration_example() -> None:
    usage_text = read_usage_text()
    adoption_section = extract_section_between_headings(
        usage_text,
        USE_IN_ANOTHER_REPOSITORY_HEADING,
        WHAT_YOU_CAN_DO_HEADING,
    )
    configuration_section = extract_section_between_headings(
        usage_text,
        CONFIGURATION_HEADING,
        "## Example output",
    )

    assert count_fenced_blocks_containing_all_markers(
        adoption_section,
        (FULL_CONFIGURATION_MARKER,),
    ) == 0
    assert count_fenced_blocks_containing_all_markers(
        usage_text,
        (FULL_CONFIGURATION_MARKER,),
    ) == 1
    assert "[[tool.docguard.document_types]]" in configuration_section


def test_phase_15_links_to_output_modes_and_exit_codes_instead_of_repeating_them() -> None:
    usage_text = read_usage_text()
    output_modes_section = extract_section_between_headings(
        usage_text,
        OUTPUT_MODES_HEADING,
        "## Enforce diagnostics",
    )
    exit_codes_section = extract_section_between_headings(
        usage_text,
        EXIT_CODES_HEADING,
        "## Add docguard to CI",
    )
    phase_15_section = extract_section_between_headings(
        usage_text,
        PHASE_15_HEADING,
        CONFIGURATION_HEADING,
    )

    for output_mode_flag_rule in OUTPUT_MODE_FLAG_RULES_OWNED_BY_OUTPUT_MODES_SECTION:
        assert output_mode_flag_rule in output_modes_section
        assert output_mode_flag_rule not in phase_15_section

    assert "[Output modes](#output-modes)" in phase_15_section
    assert "[Use predictable CI exit codes](#use-predictable-ci-exit-codes)" in phase_15_section

    for forbidden_exit_code_explanation in PHASE_15_FORBIDDEN_EXIT_CODE_EXPLANATIONS:
        assert forbidden_exit_code_explanation not in phase_15_section

    assert "Invalid `[tool.docguard]` configuration" in exit_codes_section
