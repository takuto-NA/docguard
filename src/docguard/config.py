"""Configuration loading, validation, and path normalization for docguard."""

from __future__ import annotations

import fnmatch
import re
import tomllib
from pathlib import Path
from typing import Any

from docguard.constants import (
    DEFAULT_ADR_MAX_DOCUMENT_LINES,
    DEFAULT_ADR_MAX_SECTION_LINES,
    DEFAULT_MAX_DOCUMENT_LINES,
    DEFAULT_MAX_SECTION_LINES,
    DEFAULT_SEVERITIES,
    PYPROJECT_FILENAME,
    ZERO_CONFIG_ADR_PATH_GLOB,
    ZERO_CONFIG_ADR_REQUIRED_HEADINGS,
)
from docguard.diagnostics import parse_severity_level
from docguard.models import DocguardConfiguration, DocumentTypeConfiguration


class ConfigurationError(Exception):
    """Raised when docguard configuration is invalid."""


ALLOWED_TOP_LEVEL_KEYS = {
    "paths",
    "ignore_globs",
    "max_document_lines",
    "max_section_lines",
    "index_files",
    "require_index_reachability",
    "require_orphan_detection",
    "require_hub_outgoing_links",
    "require_mixed_role_detection",
    "require_heading_order_check",
    "require_duplicate_guidance_detection",
    "allowed_duplicate_patterns",
    "hub_globs",
    "severity",
    "document_types",
    "experimental_rules_enabled",
}

ALLOWED_DOCUMENT_TYPE_KEYS = {
    "name",
    "glob",
    "required_headings",
    "required_front_matter_keys",
    "max_document_lines",
    "max_section_lines",
}


def find_project_root(start_directory: Path) -> Path | None:
    current_directory = start_directory.resolve()
    while True:
        if (current_directory / PYPROJECT_FILENAME).is_file():
            return current_directory
        parent_directory = current_directory.parent
        if parent_directory == current_directory:
            return None
        current_directory = parent_directory


def load_configuration_file(config_path: Path) -> dict[str, Any]:
    if not config_path.is_file():
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    try:
        with config_path.open("rb") as configuration_file:
            parsed_toml = tomllib.load(configuration_file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigurationError(
            f"Invalid TOML in configuration file: {config_path}"
        ) from error
    tool_section = parsed_toml.get("tool")
    if not isinstance(tool_section, dict):
        return {}
    docguard_section = tool_section.get("docguard")
    if docguard_section is None:
        return {}
    if not isinstance(docguard_section, dict):
        raise ConfigurationError("[tool.docguard] must be a table.")
    return docguard_section


def validate_unknown_keys(
    configuration_section: dict[str, Any],
    allowed_keys: set[str],
    section_name: str,
) -> None:
    unknown_keys = sorted(set(configuration_section) - allowed_keys)
    if unknown_keys:
        joined_keys = ", ".join(unknown_keys)
        raise ConfigurationError(
            f"Unknown keys in {section_name}: {joined_keys}"
        )


def require_string_list(
    raw_value: Any,
    field_name: str,
) -> tuple[str, ...]:
    if raw_value is None:
        return tuple()
    if not isinstance(raw_value, list) or not all(
        isinstance(item, str) for item in raw_value
    ):
        raise ConfigurationError(f"{field_name} must be a list of strings.")
    return tuple(raw_value)


def require_positive_integer(
    raw_value: Any,
    field_name: str,
) -> int:
    if not isinstance(raw_value, int) or raw_value <= 0:
        raise ConfigurationError(f"{field_name} must be a positive integer.")
    return raw_value


def parse_document_type_configuration(
    raw_document_type: Any,
    index: int,
) -> DocumentTypeConfiguration:
    if not isinstance(raw_document_type, dict):
        raise ConfigurationError(
            f"document_types[{index}] must be a table."
        )
    validate_unknown_keys(
        raw_document_type,
        ALLOWED_DOCUMENT_TYPE_KEYS,
        f"document_types[{index}]",
    )
    name = raw_document_type.get("name")
    glob_pattern = raw_document_type.get("glob")
    if not isinstance(name, str) or not name.strip():
        raise ConfigurationError(f"document_types[{index}].name must be a non-empty string.")
    if not isinstance(glob_pattern, str) or not glob_pattern.strip():
        raise ConfigurationError(f"document_types[{index}].glob must be a non-empty string.")
    max_document_lines = raw_document_type.get("max_document_lines")
    max_section_lines = raw_document_type.get("max_section_lines")
    return DocumentTypeConfiguration(
        name=name.strip(),
        glob_pattern=glob_pattern.strip(),
        required_headings=require_string_list(
            raw_document_type.get("required_headings"),
            f"document_types[{index}].required_headings",
        ),
        required_front_matter_keys=require_string_list(
            raw_document_type.get("required_front_matter_keys"),
            f"document_types[{index}].required_front_matter_keys",
        ),
        max_document_lines=(
            require_positive_integer(
                max_document_lines,
                f"document_types[{index}].max_document_lines",
            )
            if max_document_lines is not None
            else None
        ),
        max_section_lines=(
            require_positive_integer(
                max_section_lines,
                f"document_types[{index}].max_section_lines",
            )
            if max_section_lines is not None
            else None
        ),
    )


def validate_allowed_duplicate_patterns(
    allowed_duplicate_patterns: tuple[str, ...],
) -> None:
    for pattern_index, raw_pattern in enumerate(allowed_duplicate_patterns):
        try:
            re.compile(raw_pattern)
        except re.error as error:
            raise ConfigurationError(
                "allowed_duplicate_patterns["
                f"{pattern_index}] is not a valid regular expression: {raw_pattern}"
            ) from error


def parse_severity_table(raw_severities: Any) -> dict[str, str]:
    if raw_severities is None:
        return dict(DEFAULT_SEVERITIES)
    if not isinstance(raw_severities, dict):
        raise ConfigurationError("[tool.docguard.severity] must be a table.")
    parsed_severities = dict(DEFAULT_SEVERITIES)
    for diagnostic_code, raw_severity in raw_severities.items():
        if not isinstance(diagnostic_code, str) or not isinstance(raw_severity, str):
            raise ConfigurationError(
                "[tool.docguard.severity] keys and values must be strings."
            )
        try:
            parse_severity_level(raw_severity)
        except ValueError as error:
            raise ConfigurationError(
                f"[tool.docguard.severity] unsupported value for "
                f"{diagnostic_code}: {raw_severity}"
            ) from error
        parsed_severities[diagnostic_code] = raw_severity
    return parsed_severities


def build_zero_config_configuration(
    project_root: Path,
    cli_paths: tuple[str, ...],
) -> DocguardConfiguration:
    default_paths = cli_paths if cli_paths else ("docs",)
    return DocguardConfiguration(
        project_root=project_root,
        paths=default_paths,
        ignore_globs=tuple(),
        max_document_lines=DEFAULT_MAX_DOCUMENT_LINES,
        max_section_lines=DEFAULT_MAX_SECTION_LINES,
        index_files=tuple(),
        require_index_reachability=False,
        require_orphan_detection=False,
        require_hub_outgoing_links=False,
        require_mixed_role_detection=False,
        require_heading_order_check=False,
        require_duplicate_guidance_detection=False,
        allowed_duplicate_patterns=tuple(),
        hub_globs=tuple(),
        severities=dict(DEFAULT_SEVERITIES),
        document_types=(
            DocumentTypeConfiguration(
                name="adr",
                glob_pattern=ZERO_CONFIG_ADR_PATH_GLOB,
                required_headings=tuple(ZERO_CONFIG_ADR_REQUIRED_HEADINGS),
                required_front_matter_keys=tuple(),
                max_document_lines=DEFAULT_ADR_MAX_DOCUMENT_LINES,
                max_section_lines=DEFAULT_ADR_MAX_SECTION_LINES,
            ),
        ),
        experimental_rules_enabled=False,
        validate_explicit_paths=bool(cli_paths),
    )


def parse_docguard_configuration(
    project_root: Path,
    raw_configuration: dict[str, Any],
    cli_paths: tuple[str, ...],
) -> DocguardConfiguration:
    if not raw_configuration:
        return build_zero_config_configuration(project_root, cli_paths)

    validate_unknown_keys(
        raw_configuration,
        ALLOWED_TOP_LEVEL_KEYS,
        "[tool.docguard]",
    )

    configured_paths = require_string_list(
        raw_configuration.get("paths"),
        "paths",
    )
    effective_paths = cli_paths if cli_paths else configured_paths
    if not effective_paths:
        effective_paths = ("docs",)

    raw_document_types = raw_configuration.get("document_types", [])
    if raw_document_types is None:
        raw_document_types = []
    if not isinstance(raw_document_types, list):
        raise ConfigurationError("document_types must be a list of tables.")

    document_types = tuple(
        parse_document_type_configuration(raw_document_type, index)
        for index, raw_document_type in enumerate(raw_document_types)
    )
    allowed_duplicate_patterns = require_string_list(
        raw_configuration.get("allowed_duplicate_patterns"),
        "allowed_duplicate_patterns",
    )
    validate_allowed_duplicate_patterns(allowed_duplicate_patterns)

    return DocguardConfiguration(
        project_root=project_root,
        paths=effective_paths,
        ignore_globs=require_string_list(
            raw_configuration.get("ignore_globs"),
            "ignore_globs",
        ),
        max_document_lines=require_positive_integer(
            raw_configuration.get("max_document_lines", DEFAULT_MAX_DOCUMENT_LINES),
            "max_document_lines",
        ),
        max_section_lines=require_positive_integer(
            raw_configuration.get("max_section_lines", DEFAULT_MAX_SECTION_LINES),
            "max_section_lines",
        ),
        index_files=require_string_list(
            raw_configuration.get("index_files"),
            "index_files",
        ),
        require_index_reachability=bool(
            raw_configuration.get("require_index_reachability", False)
        ),
        require_orphan_detection=bool(
            raw_configuration.get("require_orphan_detection", False)
        ),
        require_hub_outgoing_links=bool(
            raw_configuration.get("require_hub_outgoing_links", False)
        ),
        require_mixed_role_detection=bool(
            raw_configuration.get("require_mixed_role_detection", False)
        ),
        require_heading_order_check=bool(
            raw_configuration.get("require_heading_order_check", False)
        ),
        require_duplicate_guidance_detection=bool(
            raw_configuration.get("require_duplicate_guidance_detection", False)
        ),
        allowed_duplicate_patterns=allowed_duplicate_patterns,
        hub_globs=require_string_list(
            raw_configuration.get("hub_globs"),
            "hub_globs",
        ),
        severities=parse_severity_table(raw_configuration.get("severity")),
        document_types=document_types,
        experimental_rules_enabled=bool(
            raw_configuration.get("experimental_rules_enabled", False)
        ),
        validate_explicit_paths=bool(cli_paths),
    )


def load_docguard_configuration(
    project_root: Path,
    config_path: Path | None,
    cli_paths: tuple[str, ...],
) -> DocguardConfiguration:
    if config_path is not None:
        raw_configuration = load_configuration_file(config_path)
        return parse_docguard_configuration(project_root, raw_configuration, cli_paths)

    discovered_project_root = find_project_root(project_root)
    if discovered_project_root is None:
        return build_zero_config_configuration(project_root, cli_paths)

    raw_configuration = load_configuration_file(
        discovered_project_root / PYPROJECT_FILENAME
    )
    return parse_docguard_configuration(
        discovered_project_root,
        raw_configuration,
        cli_paths,
    )


def normalize_repository_relative_path(
    project_root: Path,
    candidate_path: Path,
) -> str:
    resolved_project_root = project_root.resolve()
    resolved_candidate_path = candidate_path.resolve()
    return resolved_candidate_path.relative_to(resolved_project_root).as_posix()


def resolve_configured_path(project_root: Path, configured_path: str) -> Path:
    candidate_path = Path(configured_path)
    if candidate_path.is_absolute():
        return candidate_path.resolve()
    return (project_root / candidate_path).resolve()


def path_matches_any_glob(
    repository_relative_path: str,
    glob_patterns: tuple[str, ...],
) -> bool:
    normalized_path = repository_relative_path.replace("\\", "/")
    for glob_pattern in glob_patterns:
        if fnmatch.fnmatch(normalized_path, glob_pattern):
            return True
    return False


def resolve_document_type_for_path(
    repository_relative_path: str,
    document_types: tuple[DocumentTypeConfiguration, ...],
) -> DocumentTypeConfiguration | None:
    matched_document_types: list[DocumentTypeConfiguration] = []
    normalized_path = repository_relative_path.replace("\\", "/")
    for document_type in document_types:
        if fnmatch.fnmatch(normalized_path, document_type.glob_pattern):
            matched_document_types.append(document_type)
    if len(matched_document_types) > 1:
        matched_names = ", ".join(document_type.name for document_type in matched_document_types)
        raise ConfigurationError(
            f"Document {repository_relative_path} matched multiple document types: {matched_names}"
        )
    if not matched_document_types:
        return None
    return matched_document_types[0]
