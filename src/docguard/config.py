"""Configuration loading, validation, and path normalization for docguard."""

from __future__ import annotations

import fnmatch
import re
import tomllib
from dataclasses import replace
from pathlib import Path
from typing import Any

from docguard.constants import (
    ALLOWED_DUPLICATE_GUIDANCE_KINDS,
    DEFAULT_ADR_MAX_DOCUMENT_LINES,
    DEFAULT_ADR_MAX_SECTION_LINES,
    DEFAULT_DUPLICATE_GUIDANCE_KINDS,
    DEFAULT_INDEX_FILES,
    DEFAULT_MAX_DOCUMENT_LINES,
    DEFAULT_MAX_SECTION_LINES,
    DEFAULT_MIN_DOCUMENT_LINES,
    DEFAULT_MAX_STRONG_EMPHASIS_PAIRS,
    DEFAULT_SEVERITIES,
    DEFAULT_STRICT_SCAN_PATHS,
    PYPROJECT_FILENAME,
    ZERO_CONFIG_ADR_PATH_GLOB,
    ZERO_CONFIG_ADR_REQUIRED_FRONT_MATTER_KEYS,
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
    "min_document_lines",
    "index_files",
    "require_index_reachability",
    "require_orphan_detection",
    "require_hub_outgoing_links",
    "require_mixed_role_detection",
    "require_heading_order_check",
    "require_duplicate_guidance_detection",
    "duplicate_guidance_kinds",
    "allowed_duplicate_patterns",
    "max_strong_emphasis_pairs",
    "allowed_prose_phrases",
    "extra_prohibited_prose_patterns",
    "allowed_documentation_style_phrases",
    "extra_prohibited_documentation_style_patterns",
    "hub_globs",
    "severity",
    "document_types",
    "experimental_rules_enabled",
    "relaxations",
}

ALLOWED_DOCUMENT_TYPE_KEYS = {
    "name",
    "glob",
    "required_headings",
    "required_front_matter_keys",
    "max_document_lines",
    "max_section_lines",
}

RELAXATION_REASON_MINIMUM_LENGTH = 20

RELAXATION_PARAMETERS = {
    "allowed_duplicate_patterns",
    "allowed_prose_phrases",
    "allowed_documentation_style_phrases",
    "duplicate_guidance_kinds",
    "max_document_lines",
    "max_section_lines",
    "max_strong_emphasis_pairs",
    "min_document_lines",
    "require_duplicate_guidance_detection",
    "require_index_reachability",
}

SEVERITY_RANKS = {
    "experimental": 0,
    "warning": 1,
    "error": 2,
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
    if not isinstance(raw_value, int) or isinstance(raw_value, bool) or raw_value <= 0:
        raise ConfigurationError(f"{field_name} must be a positive integer.")
    return raw_value


def require_non_negative_integer(
    raw_value: Any,
    field_name: str,
) -> int:
    if not isinstance(raw_value, int) or isinstance(raw_value, bool) or raw_value < 0:
        raise ConfigurationError(f"{field_name} must be a non-negative integer.")
    return raw_value


def require_boolean(
    raw_value: Any,
    field_name: str,
) -> bool:
    if not isinstance(raw_value, bool):
        raise ConfigurationError(f"{field_name} must be a boolean.")
    return raw_value


def validate_extra_prohibited_prose_patterns(
    extra_prohibited_prose_patterns: tuple[str, ...],
) -> None:
    for pattern_text in extra_prohibited_prose_patterns:
        try:
            re.compile(pattern_text, re.IGNORECASE)
        except re.error as error:
            raise ConfigurationError(
                f"Invalid extra_prohibited_prose_patterns regex: {pattern_text}"
            ) from error


def validate_extra_prohibited_documentation_style_patterns(
    extra_prohibited_documentation_style_patterns: tuple[str, ...],
) -> None:
    for pattern_text in extra_prohibited_documentation_style_patterns:
        try:
            re.compile(pattern_text, re.IGNORECASE)
        except re.error as error:
            raise ConfigurationError(
                "Invalid extra_prohibited_documentation_style_patterns regex: "
                f"{pattern_text}"
            ) from error


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


def parse_duplicate_guidance_kinds(raw_value: Any) -> tuple[str, ...]:
    if raw_value is None:
        return DEFAULT_DUPLICATE_GUIDANCE_KINDS
    if not isinstance(raw_value, list) or not all(
        isinstance(item, str) for item in raw_value
    ):
        raise ConfigurationError("duplicate_guidance_kinds must be a list of strings.")
    if len(raw_value) == 0:
        raise ConfigurationError("duplicate_guidance_kinds must not be empty.")
    seen_kind_names: set[str] = set()
    parsed_kind_names: list[str] = []
    for kind_index, raw_kind_name in enumerate(raw_value):
        normalized_kind_name = raw_kind_name.strip()
        if normalized_kind_name not in ALLOWED_DUPLICATE_GUIDANCE_KINDS:
            raise ConfigurationError(
                "duplicate_guidance_kinds["
                f"{kind_index}] is not supported: {raw_kind_name}"
            )
        if normalized_kind_name in seen_kind_names:
            raise ConfigurationError(
                "duplicate_guidance_kinds contains duplicate value: "
                f"{raw_kind_name}"
            )
        seen_kind_names.add(normalized_kind_name)
        parsed_kind_names.append(normalized_kind_name)
    return tuple(parsed_kind_names)


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


def build_strict_baseline_configuration(
    project_root: Path,
    cli_paths: tuple[str, ...],
) -> DocguardConfiguration:
    default_paths = cli_paths if cli_paths else DEFAULT_STRICT_SCAN_PATHS
    return DocguardConfiguration(
        project_root=project_root,
        paths=default_paths,
        ignore_globs=tuple(),
        max_document_lines=DEFAULT_MAX_DOCUMENT_LINES,
        max_section_lines=DEFAULT_MAX_SECTION_LINES,
        min_document_lines=DEFAULT_MIN_DOCUMENT_LINES,
        index_files=DEFAULT_INDEX_FILES,
        require_index_reachability=True,
        require_orphan_detection=False,
        require_hub_outgoing_links=False,
        require_mixed_role_detection=False,
        require_heading_order_check=False,
        require_duplicate_guidance_detection=True,
        duplicate_guidance_kinds=DEFAULT_DUPLICATE_GUIDANCE_KINDS,
        allowed_duplicate_patterns=tuple(),
        max_strong_emphasis_pairs=DEFAULT_MAX_STRONG_EMPHASIS_PAIRS,
        allowed_prose_phrases=tuple(),
        extra_prohibited_prose_patterns=tuple(),
        allowed_documentation_style_phrases=tuple(),
        extra_prohibited_documentation_style_patterns=tuple(),
        hub_globs=tuple(),
        severities=dict(DEFAULT_SEVERITIES),
        document_types=(
            DocumentTypeConfiguration(
                name="adr",
                glob_pattern=ZERO_CONFIG_ADR_PATH_GLOB,
                required_headings=tuple(ZERO_CONFIG_ADR_REQUIRED_HEADINGS),
                required_front_matter_keys=tuple(
                    ZERO_CONFIG_ADR_REQUIRED_FRONT_MATTER_KEYS
                ),
                max_document_lines=DEFAULT_ADR_MAX_DOCUMENT_LINES,
                max_section_lines=DEFAULT_ADR_MAX_SECTION_LINES,
            ),
        ),
        policy_name="strict baseline",
        relaxation_count=0,
        experimental_rules_enabled=False,
        validate_explicit_paths=bool(cli_paths),
    )


def is_severity_parameter(parameter_name: str) -> bool:
    return parameter_name.startswith("severity.")


def validate_relaxation_parameter(parameter_name: str) -> None:
    if parameter_name in RELAXATION_PARAMETERS:
        return
    if is_severity_parameter(parameter_name) and parameter_name != "severity.":
        return
    raise ConfigurationError(f"Unknown relaxation parameter: {parameter_name}")


def parse_relaxations(raw_relaxations: Any) -> tuple[dict[str, Any], ...]:
    if raw_relaxations is None:
        return tuple()
    if not isinstance(raw_relaxations, list):
        raise ConfigurationError("relaxations must be a list of tables.")

    parsed_relaxations: list[dict[str, Any]] = []
    for relaxation_index, raw_relaxation in enumerate(raw_relaxations):
        if not isinstance(raw_relaxation, dict):
            raise ConfigurationError(
                f"relaxations[{relaxation_index}] must be a table."
            )
        validate_unknown_keys(
            raw_relaxation,
            {"parameter", "value", "reason"},
            f"relaxations[{relaxation_index}]",
        )
        parameter_name = raw_relaxation.get("parameter")
        if not isinstance(parameter_name, str) or not parameter_name.strip():
            raise ConfigurationError(
                f"relaxations[{relaxation_index}].parameter must be a non-empty string."
            )
        normalized_parameter_name = parameter_name.strip()
        validate_relaxation_parameter(normalized_parameter_name)
        if "value" not in raw_relaxation:
            raise ConfigurationError(
                f"relaxations[{relaxation_index}].value is required."
            )
        reason = raw_relaxation.get("reason")
        if not isinstance(reason, str) or len(reason.strip()) < RELAXATION_REASON_MINIMUM_LENGTH:
            raise ConfigurationError(
                f"relaxations[{relaxation_index}].reason must be at least "
                f"{RELAXATION_REASON_MINIMUM_LENGTH} characters."
            )
        parsed_relaxations.append(
            {
                "parameter": normalized_parameter_name,
                "value": raw_relaxation["value"],
                "reason": reason.strip(),
            }
        )
    return tuple(parsed_relaxations)


def severity_is_looser(candidate_severity: str, baseline_severity: str) -> bool:
    return SEVERITY_RANKS[candidate_severity] < SEVERITY_RANKS[baseline_severity]


def validate_direct_integer_budget(
    raw_configuration: dict[str, Any],
    field_name: str,
    baseline_value: int,
    *,
    lower_is_looser: bool = False,
) -> None:
    if field_name not in raw_configuration:
        return
    candidate_value = (
        require_non_negative_integer(raw_configuration[field_name], field_name)
        if lower_is_looser
        else require_positive_integer(raw_configuration[field_name], field_name)
    )
    is_looser = (
        candidate_value < baseline_value
        if lower_is_looser
        else candidate_value > baseline_value
    )
    if is_looser:
        raise ConfigurationError(
            f"{field_name} relaxes the strict baseline. Use "
            "[[tool.docguard.relaxations]] with a reason instead."
        )


def validate_direct_boolean_requirement(
    raw_configuration: dict[str, Any],
    field_name: str,
    baseline_value: bool,
) -> None:
    if field_name not in raw_configuration:
        return
    candidate_value = require_boolean(raw_configuration[field_name], field_name)
    if baseline_value and not candidate_value:
        raise ConfigurationError(
            f"{field_name} relaxes the strict baseline. Use "
            "[[tool.docguard.relaxations]] with a reason instead."
        )


def validate_direct_string_list_relaxation(
    raw_configuration: dict[str, Any],
    field_name: str,
) -> None:
    if field_name not in raw_configuration:
        return
    configured_values = require_string_list(raw_configuration[field_name], field_name)
    if configured_values:
        raise ConfigurationError(
            f"{field_name} relaxes the strict baseline. Use "
            "[[tool.docguard.relaxations]] with a reason instead."
        )


def validate_direct_duplicate_guidance_kinds(
    raw_configuration: dict[str, Any],
) -> None:
    if "duplicate_guidance_kinds" not in raw_configuration:
        return
    candidate_kinds = parse_duplicate_guidance_kinds(
        raw_configuration["duplicate_guidance_kinds"]
    )
    missing_baseline_kinds = set(DEFAULT_DUPLICATE_GUIDANCE_KINDS) - set(candidate_kinds)
    if missing_baseline_kinds:
        raise ConfigurationError(
            "duplicate_guidance_kinds relaxes the strict baseline. Use "
            "[[tool.docguard.relaxations]] with a reason instead."
        )


def validate_direct_severity_relaxations(
    raw_configuration: dict[str, Any],
) -> None:
    raw_severities = raw_configuration.get("severity")
    if raw_severities is None:
        return
    parsed_severities = parse_severity_table(raw_severities)
    for diagnostic_code, configured_severity in parsed_severities.items():
        baseline_severity = DEFAULT_SEVERITIES.get(diagnostic_code)
        if baseline_severity is None:
            continue
        if severity_is_looser(configured_severity, baseline_severity):
            raise ConfigurationError(
                f"severity.{diagnostic_code} relaxes the strict baseline. Use "
                "[[tool.docguard.relaxations]] with a reason instead."
            )


def validate_direct_relaxations(
    raw_configuration: dict[str, Any],
    baseline_configuration: DocguardConfiguration,
) -> None:
    validate_direct_integer_budget(
        raw_configuration,
        "max_document_lines",
        baseline_configuration.max_document_lines,
    )
    validate_direct_integer_budget(
        raw_configuration,
        "max_section_lines",
        baseline_configuration.max_section_lines,
    )
    validate_direct_integer_budget(
        raw_configuration,
        "min_document_lines",
        baseline_configuration.min_document_lines,
        lower_is_looser=True,
    )
    validate_direct_integer_budget(
        raw_configuration,
        "max_strong_emphasis_pairs",
        baseline_configuration.max_strong_emphasis_pairs,
    )
    validate_direct_boolean_requirement(
        raw_configuration,
        "require_index_reachability",
        baseline_configuration.require_index_reachability,
    )
    validate_direct_boolean_requirement(
        raw_configuration,
        "require_duplicate_guidance_detection",
        baseline_configuration.require_duplicate_guidance_detection,
    )
    validate_direct_string_list_relaxation(raw_configuration, "allowed_prose_phrases")
    validate_direct_string_list_relaxation(
        raw_configuration,
        "allowed_documentation_style_phrases",
    )
    validate_direct_string_list_relaxation(raw_configuration, "allowed_duplicate_patterns")
    validate_direct_duplicate_guidance_kinds(raw_configuration)
    validate_direct_severity_relaxations(raw_configuration)


def apply_relaxation(
    configuration: DocguardConfiguration,
    relaxation: dict[str, Any],
) -> DocguardConfiguration:
    parameter_name = relaxation["parameter"]
    raw_value = relaxation["value"]

    if parameter_name == "max_document_lines":
        return replace(
            configuration,
            max_document_lines=require_positive_integer(raw_value, parameter_name),
        )
    if parameter_name == "max_section_lines":
        return replace(
            configuration,
            max_section_lines=require_positive_integer(raw_value, parameter_name),
        )
    if parameter_name == "min_document_lines":
        return replace(
            configuration,
            min_document_lines=require_non_negative_integer(raw_value, parameter_name),
        )
    if parameter_name == "max_strong_emphasis_pairs":
        return replace(
            configuration,
            max_strong_emphasis_pairs=require_non_negative_integer(
                raw_value,
                parameter_name,
            ),
        )
    if parameter_name == "require_index_reachability":
        return replace(
            configuration,
            require_index_reachability=require_boolean(raw_value, parameter_name),
        )
    if parameter_name == "require_duplicate_guidance_detection":
        return replace(
            configuration,
            require_duplicate_guidance_detection=require_boolean(
                raw_value,
                parameter_name,
            ),
        )
    if parameter_name == "allowed_prose_phrases":
        return replace(
            configuration,
            allowed_prose_phrases=require_string_list(raw_value, parameter_name),
        )
    if parameter_name == "allowed_documentation_style_phrases":
        return replace(
            configuration,
            allowed_documentation_style_phrases=require_string_list(
                raw_value,
                parameter_name,
            ),
        )
    if parameter_name == "allowed_duplicate_patterns":
        allowed_duplicate_patterns = require_string_list(raw_value, parameter_name)
        validate_allowed_duplicate_patterns(allowed_duplicate_patterns)
        return replace(
            configuration,
            allowed_duplicate_patterns=allowed_duplicate_patterns,
        )
    if parameter_name == "duplicate_guidance_kinds":
        return replace(
            configuration,
            duplicate_guidance_kinds=parse_duplicate_guidance_kinds(raw_value),
        )
    if is_severity_parameter(parameter_name):
        diagnostic_code = parameter_name.removeprefix("severity.")
        if not isinstance(raw_value, str):
            raise ConfigurationError(f"{parameter_name} must be a severity string.")
        try:
            parse_severity_level(raw_value)
        except ValueError as error:
            raise ConfigurationError(
                f"{parameter_name} unsupported value: {raw_value}"
            ) from error
        severities = dict(configuration.severities)
        severities[diagnostic_code] = raw_value
        return replace(configuration, severities=severities)

    raise ConfigurationError(f"Unknown relaxation parameter: {parameter_name}")


def apply_relaxations(
    configuration: DocguardConfiguration,
    relaxations: tuple[dict[str, Any], ...],
) -> DocguardConfiguration:
    relaxed_configuration = configuration
    for relaxation in relaxations:
        relaxed_configuration = apply_relaxation(relaxed_configuration, relaxation)
    return replace(
        relaxed_configuration,
        relaxation_count=len(relaxations),
    )


def parse_docguard_configuration(
    project_root: Path,
    raw_configuration: dict[str, Any],
    cli_paths: tuple[str, ...],
) -> DocguardConfiguration:
    baseline_configuration = build_strict_baseline_configuration(project_root, cli_paths)
    if not raw_configuration:
        return baseline_configuration

    validate_unknown_keys(
        raw_configuration,
        ALLOWED_TOP_LEVEL_KEYS,
        "[tool.docguard]",
    )
    validate_direct_relaxations(raw_configuration, baseline_configuration)
    relaxations = parse_relaxations(raw_configuration.get("relaxations"))

    configured_paths = require_string_list(
        raw_configuration.get("paths"),
        "paths",
    )
    effective_paths = (
        cli_paths
        if cli_paths
        else configured_paths or baseline_configuration.paths
    )

    raw_document_types = raw_configuration.get("document_types", [])
    if raw_document_types is None:
        raw_document_types = []
    if not isinstance(raw_document_types, list):
        raise ConfigurationError("document_types must be a list of tables.")

    document_types = (
        tuple(
            parse_document_type_configuration(raw_document_type, index)
            for index, raw_document_type in enumerate(raw_document_types)
        )
        if raw_document_types
        else baseline_configuration.document_types
    )
    allowed_duplicate_patterns = require_string_list(
        raw_configuration.get("allowed_duplicate_patterns"),
        "allowed_duplicate_patterns",
    )
    validate_allowed_duplicate_patterns(allowed_duplicate_patterns)
    duplicate_guidance_kinds = parse_duplicate_guidance_kinds(
        raw_configuration.get("duplicate_guidance_kinds")
    )
    allowed_prose_phrases = require_string_list(
        raw_configuration.get("allowed_prose_phrases"),
        "allowed_prose_phrases",
    )
    extra_prohibited_prose_patterns = require_string_list(
        raw_configuration.get("extra_prohibited_prose_patterns"),
        "extra_prohibited_prose_patterns",
    )
    validate_extra_prohibited_prose_patterns(extra_prohibited_prose_patterns)
    allowed_documentation_style_phrases = require_string_list(
        raw_configuration.get("allowed_documentation_style_phrases"),
        "allowed_documentation_style_phrases",
    )
    extra_prohibited_documentation_style_patterns = require_string_list(
        raw_configuration.get("extra_prohibited_documentation_style_patterns"),
        "extra_prohibited_documentation_style_patterns",
    )
    validate_extra_prohibited_documentation_style_patterns(
        extra_prohibited_documentation_style_patterns
    )

    direct_configuration = DocguardConfiguration(
        project_root=project_root,
        paths=effective_paths,
        ignore_globs=require_string_list(
            raw_configuration.get("ignore_globs"),
            "ignore_globs",
        ),
        max_document_lines=require_positive_integer(
            raw_configuration.get(
                "max_document_lines",
                baseline_configuration.max_document_lines,
            ),
            "max_document_lines",
        ),
        max_section_lines=require_positive_integer(
            raw_configuration.get(
                "max_section_lines",
                baseline_configuration.max_section_lines,
            ),
            "max_section_lines",
        ),
        min_document_lines=require_non_negative_integer(
            raw_configuration.get(
                "min_document_lines",
                baseline_configuration.min_document_lines,
            ),
            "min_document_lines",
        ),
        index_files=require_string_list(
            raw_configuration.get("index_files", list(baseline_configuration.index_files)),
            "index_files",
        ),
        require_index_reachability=require_boolean(
            raw_configuration.get(
                "require_index_reachability",
                baseline_configuration.require_index_reachability,
            ),
            "require_index_reachability",
        ),
        require_orphan_detection=require_boolean(
            raw_configuration.get(
                "require_orphan_detection",
                baseline_configuration.require_orphan_detection,
            ),
            "require_orphan_detection",
        ),
        require_hub_outgoing_links=require_boolean(
            raw_configuration.get(
                "require_hub_outgoing_links",
                baseline_configuration.require_hub_outgoing_links,
            ),
            "require_hub_outgoing_links",
        ),
        require_mixed_role_detection=require_boolean(
            raw_configuration.get(
                "require_mixed_role_detection",
                baseline_configuration.require_mixed_role_detection,
            ),
            "require_mixed_role_detection",
        ),
        require_heading_order_check=require_boolean(
            raw_configuration.get(
                "require_heading_order_check",
                baseline_configuration.require_heading_order_check,
            ),
            "require_heading_order_check",
        ),
        require_duplicate_guidance_detection=require_boolean(
            raw_configuration.get(
                "require_duplicate_guidance_detection",
                baseline_configuration.require_duplicate_guidance_detection,
            ),
            "require_duplicate_guidance_detection",
        ),
        duplicate_guidance_kinds=duplicate_guidance_kinds,
        allowed_duplicate_patterns=allowed_duplicate_patterns,
        max_strong_emphasis_pairs=require_non_negative_integer(
            raw_configuration.get(
                "max_strong_emphasis_pairs",
                DEFAULT_MAX_STRONG_EMPHASIS_PAIRS,
            ),
            "max_strong_emphasis_pairs",
        ),
        allowed_prose_phrases=allowed_prose_phrases,
        extra_prohibited_prose_patterns=extra_prohibited_prose_patterns,
        allowed_documentation_style_phrases=allowed_documentation_style_phrases,
        extra_prohibited_documentation_style_patterns=(
            extra_prohibited_documentation_style_patterns
        ),
        hub_globs=require_string_list(
            raw_configuration.get("hub_globs"),
            "hub_globs",
        ),
        severities=parse_severity_table(raw_configuration.get("severity")),
        document_types=document_types,
        policy_name=baseline_configuration.policy_name,
        relaxation_count=0,
        experimental_rules_enabled=require_boolean(
            raw_configuration.get(
                "experimental_rules_enabled",
                baseline_configuration.experimental_rules_enabled,
            ),
            "experimental_rules_enabled",
        ),
        validate_explicit_paths=bool(cli_paths),
    )
    return apply_relaxations(direct_configuration, relaxations)


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
        return build_strict_baseline_configuration(project_root, cli_paths)

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
