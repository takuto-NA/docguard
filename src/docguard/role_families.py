"""Document role family classification for DG-SPLIT001."""

from __future__ import annotations

from enum import Enum

from docguard.models import Heading

LEVEL_TWO_HEADING = 2
MINIMUM_DISTINCT_ROLE_FAMILIES_FOR_MIXED_ROLES = 2


class RoleFamily(str, Enum):
    NARRATIVE = "narrative"
    DECISION = "decision"
    REFERENCE = "reference"
    OPERATIONS = "operations"


ROLE_FAMILY_KEYWORDS: tuple[tuple[RoleFamily, tuple[str, ...]], ...] = (
    (
        RoleFamily.NARRATIVE,
        (
            "overview",
            "background",
            "introduction",
            "summary",
            "概要",
            "背景",
            "はじめに",
        ),
    ),
    (
        RoleFamily.DECISION,
        (
            "decision",
            "alternatives",
            "trade-off",
            "trade-offs",
            "consequences",
            "決定",
            "代替",
            "トレードオフ",
        ),
    ),
    (
        RoleFamily.REFERENCE,
        (
            "api",
            "schema",
            "configuration",
            "specification",
            "reference",
            "仕様",
            "設定",
            "リファレンス",
        ),
    ),
    (
        RoleFamily.OPERATIONS,
        (
            "runbook",
            "deployment",
            "troubleshooting",
            "operations",
            "monitoring",
            "運用",
            "デプロイ",
            "障害",
        ),
    ),
)


def classify_heading_text(heading_text: str) -> RoleFamily | None:
    normalized_heading_text = heading_text.strip().casefold()
    for role_family, keywords in ROLE_FAMILY_KEYWORDS:
        for keyword in keywords:
            if keyword.casefold() in normalized_heading_text:
                return role_family
    return None


def detect_mixed_role_families(
    headings: tuple[Heading, ...],
) -> frozenset[RoleFamily]:
    matched_families: set[RoleFamily] = set()
    for heading in headings:
        if heading.level != LEVEL_TWO_HEADING:
            continue
        matched_family = classify_heading_text(heading.text)
        if matched_family is None:
            continue
        matched_families.add(matched_family)
        if len(matched_families) >= MINIMUM_DISTINCT_ROLE_FAMILIES_FOR_MIXED_ROLES:
            return frozenset(matched_families)
    return frozenset()
