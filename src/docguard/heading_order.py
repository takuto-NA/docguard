"""Heading level skip detection for DG-FORMAT002."""

from __future__ import annotations

from dataclasses import dataclass

from docguard.models import Heading


@dataclass(frozen=True)
class HeadingLevelSkipViolation:
    line_number: int
    previous_level: int
    current_level: int
    heading_text: str


def find_heading_level_skips(
    headings: tuple[Heading, ...],
) -> tuple[HeadingLevelSkipViolation, ...]:
    if not headings:
        return tuple()

    violations: list[HeadingLevelSkipViolation] = []
    previous_level = headings[0].level
    for heading in headings[1:]:
        if heading.level > previous_level + 1:
            violations.append(
                HeadingLevelSkipViolation(
                    line_number=heading.line_number,
                    previous_level=previous_level,
                    current_level=heading.level,
                    heading_text=heading.text,
                )
            )
        previous_level = heading.level
    return tuple(violations)
