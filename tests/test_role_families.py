"""Tests for document role family classification (DG-SPLIT001)."""

from __future__ import annotations

from docguard.models import Heading
from docguard.role_families import RoleFamily, classify_heading_text, detect_mixed_role_families


def build_heading(level: int, text: str, line_number: int) -> Heading:
    return Heading(level=level, text=text, line_number=line_number)


def test_classify_heading_text_matches_english_keywords() -> None:
    assert classify_heading_text("Overview") is RoleFamily.NARRATIVE
    assert classify_heading_text("API Reference") is RoleFamily.REFERENCE
    assert classify_heading_text("Deployment") is RoleFamily.OPERATIONS


def test_classify_heading_text_matches_japanese_keywords() -> None:
    assert classify_heading_text("概要") is RoleFamily.NARRATIVE
    assert classify_heading_text("運用手順") is RoleFamily.OPERATIONS


def test_classify_heading_text_returns_none_for_unmatched_heading() -> None:
    assert classify_heading_text("Quick start") is None


def test_detect_mixed_role_families_requires_two_distinct_families() -> None:
    headings = (
        build_heading(2, "Overview", 1),
        build_heading(2, "Deployment", 5),
    )
    assert detect_mixed_role_families(headings) == frozenset(
        {RoleFamily.NARRATIVE, RoleFamily.OPERATIONS}
    )


def test_detect_mixed_role_families_ignores_non_level_two_headings() -> None:
    headings = (
        build_heading(1, "Title", 1),
        build_heading(3, "Deployment", 5),
    )
    assert detect_mixed_role_families(headings) == frozenset()


def test_detect_mixed_role_families_returns_empty_for_single_family() -> None:
    headings = (
        build_heading(2, "Overview", 1),
        build_heading(2, "Background", 5),
    )
    assert detect_mixed_role_families(headings) == frozenset()


def test_detect_mixed_role_families_matches_japanese_headings() -> None:
    headings = (
        build_heading(2, "概要", 1),
        build_heading(2, "運用手順", 5),
    )
    assert detect_mixed_role_families(headings) == frozenset(
        {RoleFamily.NARRATIVE, RoleFamily.OPERATIONS}
    )
