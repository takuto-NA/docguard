"""Tests for heading level skip detection (DG-FORMAT002)."""

from __future__ import annotations

import pytest

from docguard.heading_order import find_heading_level_skips
from docguard.models import Heading


def build_heading(level: int, text: str, line_number: int) -> Heading:
    return Heading(level=level, text=text, line_number=line_number)


def test_first_heading_never_creates_skip_violation() -> None:
    headings = (build_heading(1, "Title", 1),)
    assert find_heading_level_skips(headings) == tuple()


@pytest.mark.parametrize(
    ("headings", "expected_line_numbers"),
    [
        (
            (
                build_heading(2, "Section", 1),
                build_heading(4, "Deep", 5),
            ),
            (5,),
        ),
        (
            (
                build_heading(1, "Title", 1),
                build_heading(2, "Section", 3),
                build_heading(4, "Deep", 8),
            ),
            (8,),
        ),
    ],
)
def test_heading_level_skip_is_detected(
    headings: tuple[Heading, ...],
    expected_line_numbers: tuple[int, ...],
) -> None:
    violations = find_heading_level_skips(headings)
    assert tuple(violation.line_number for violation in violations) == expected_line_numbers


@pytest.mark.parametrize(
    "headings",
    [
        (
            build_heading(1, "Title", 1),
            build_heading(2, "Section", 3),
            build_heading(3, "Subsection", 5),
        ),
        (
            build_heading(2, "Section", 1),
            build_heading(3, "Subsection", 5),
            build_heading(2, "Another section", 10),
        ),
    ],
)
def test_valid_heading_progression_has_no_skip_violations(
    headings: tuple[Heading, ...],
) -> None:
    assert find_heading_level_skips(headings) == tuple()
