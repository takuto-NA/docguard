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
DIAGNOSTIC_CODE_MISSING_FRONT_MATTER = "DG-FORMAT003"
DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX = "DG-ORG003"

DIAGNOSTIC_TITLES: dict[str, str] = {
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG: "document too long",
    DIAGNOSTIC_CODE_SECTION_TOO_LONG: "section too long",
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING: "missing required heading",
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER: "missing front matter",
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX: "unreachable from index",
}

PYPROJECT_FILENAME = "pyproject.toml"
TOOL_DOCGUARD_SECTION = "tool.docguard"

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
WHY_MISSING_FRONT_MATTER = (
    "Front matter makes document status and ownership visible without reading the body."
)
WHY_UNREACHABLE_FROM_INDEX = (
    "Documents that cannot be reached from an index file are easy to miss during review."
)

DEFAULT_SEVERITIES: dict[str, str] = {
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG: "error",
    DIAGNOSTIC_CODE_SECTION_TOO_LONG: "error",
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING: "error",
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER: "error",
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX: "error",
}

ZERO_CONFIG_ADR_PATH_GLOB = "adr/*.md"
ZERO_CONFIG_ADR_REQUIRED_HEADINGS = [
    "Status",
    "Context",
    "Decision",
    "Consequences",
]
