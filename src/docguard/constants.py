"""Shared constants for docguard exit codes, defaults, and diagnostic codes."""

from __future__ import annotations

EXIT_CODE_SUCCESS = 0
EXIT_CODE_DIAGNOSTIC_FAILURE = 1
EXIT_CODE_CONFIGURATION_FAILURE = 2

DEFAULT_MAX_DOCUMENT_LINES = 400
DEFAULT_MAX_SECTION_LINES = 120

DEFAULT_ADR_MAX_DOCUMENT_LINES = 160
DEFAULT_ADR_MAX_SECTION_LINES = 60

DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG = "DG-SIZE001"
DIAGNOSTIC_CODE_SECTION_TOO_LONG = "DG-SIZE002"
DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING = "DG-FORMAT001"
DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER = "DG-FORMAT002"
DIAGNOSTIC_CODE_MISSING_FRONT_MATTER = "DG-FORMAT003"
DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES = "DG-SPLIT001"
DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE = "DG-SPLIT002"
DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX = "DG-ORG003"
DIAGNOSTIC_CODE_ORPHAN_DOCUMENT = "DG-ORG001"
DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS = "DG-ORG002"

DIAGNOSTIC_TITLES: dict[str, str] = {
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG: "document too long",
    DIAGNOSTIC_CODE_SECTION_TOO_LONG: "section too long",
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING: "missing required heading",
    DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER: "unexpected heading order",
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER: "missing front matter",
    DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES: "possible mixed document roles",
    DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE: "duplicate guidance",
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX: "unreachable from index",
    DIAGNOSTIC_CODE_ORPHAN_DOCUMENT: "orphan document",
    DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS: "missing outgoing links",
}

PYPROJECT_FILENAME = "pyproject.toml"

MARKDOWN_FILE_ENCODING = "utf-8-sig"
MARKDOWN_FILE_SUFFIX = ".md"
YAML_FRONT_MATTER_DELIMITER = "---"

MINIMUM_HEADING_LEVEL = 1
MAXIMUM_HEADING_LEVEL = 6

GENERIC_SPLIT_SUGGESTION_MESSAGE = (
    "Split the document by major topic so each file covers one concern."
)

WHY_DOCUMENT_TOO_LONG = (
    "Large Markdown files tend to mix overview, decisions, implementation details, "
    "and operations."
)
WHY_SECTION_TOO_LONG = (
    "Large sections are harder to navigate and often hide multiple topics that "
    "should be separate documents."
)
WHY_MISSING_REQUIRED_HEADING = (
    "Required headings keep documents of the same type comparable and complete."
)
WHY_UNEXPECTED_HEADING_ORDER = (
    "Skipped heading levels make document structure harder to navigate and render."
)
WHY_MIXED_DOCUMENT_ROLES = (
    "Documents that mix narrative, reference, decision, and operations content "
    "are harder to maintain and usually belong in separate files."
)
WHY_DUPLICATE_GUIDANCE = (
    "Repeated commands, headings, list guidance, or prose paragraphs make "
    "maintenance instructions harder to keep consistent without a clear "
    "canonical owner."
)
SUGGESTION_DUPLICATE_GUIDANCE = (
    "Consolidate repeated guidance into one canonical section "
    "and link to it elsewhere."
)
SUGGESTION_DUPLICATE_HEADING_GUIDANCE = (
    "If the shared heading is intentional template structure, remove `heading` "
    "from `duplicate_guidance_kinds` or add an `allowed_duplicate_patterns` "
    "entry instead of renaming headings."
)

DEFAULT_DUPLICATE_GUIDANCE_KINDS = ("code_block", "list_item")
ALLOWED_DUPLICATE_GUIDANCE_KINDS = frozenset(
    {"code_block", "heading", "list_item", "paragraph"}
)
WHY_MISSING_FRONT_MATTER = (
    "Front matter makes document status and ownership visible without reading the body."
)
WHY_UNREACHABLE_FROM_INDEX = (
    "Documents that cannot be reached from an index file are easy to miss during review."
)
WHY_ORPHAN_DOCUMENT = (
    "Documents with no incoming links from other in-scope documents are easy to overlook."
)
WHY_MISSING_OUTGOING_LINKS = (
    "Hub documents without outgoing links to other in-scope documents are navigation dead ends."
)

DEFAULT_SEVERITIES: dict[str, str] = {
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG: "error",
    DIAGNOSTIC_CODE_SECTION_TOO_LONG: "error",
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING: "error",
    DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER: "warning",
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER: "error",
    DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES: "warning",
    DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE: "warning",
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX: "error",
    DIAGNOSTIC_CODE_ORPHAN_DOCUMENT: "warning",
    DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS: "warning",
}

ZERO_CONFIG_ADR_PATH_GLOB = "adr/*.md"
ZERO_CONFIG_ADR_REQUIRED_HEADINGS = [
    "Status",
    "Context",
    "Decision",
    "Consequences",
]
