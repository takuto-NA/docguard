"""Tests for docguard configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import (
    ConfigurationError,
    load_docguard_configuration,
    resolve_document_type_for_path,
)
from docguard.constants import (
    DEFAULT_DUPLICATE_GUIDANCE_KINDS,
    DEFAULT_MAX_DOCUMENT_LINES,
    DEFAULT_MIN_DOCUMENT_LINES,
)


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def test_strict_baseline_uses_cli_paths(temporary_project_directory: Path) -> None:
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=None,
        cli_paths=("docs",),
    )
    assert configuration.paths == ("docs",)
    assert configuration.max_document_lines == DEFAULT_MAX_DOCUMENT_LINES
    assert configuration.min_document_lines == DEFAULT_MIN_DOCUMENT_LINES
    assert configuration.index_files == ("README.md",)
    assert configuration.require_index_reachability is True
    assert configuration.require_duplicate_guidance_detection is True
    assert configuration.severities["DG-SPLIT002"] == "error"
    assert configuration.severities["DG-STYLE001"] == "error"
    assert configuration.severities["DG-STYLE003"] == "error"


def test_empty_docguard_table_uses_strict_baseline(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.paths == ("README.md", "CONTEXT.md", "docs")
    assert configuration.max_document_lines == 300
    assert configuration.min_document_lines == 20
    assert configuration.require_index_reachability is True


def test_unknown_configuration_key_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
unknown_key = true
""",
    )
    with pytest.raises(ConfigurationError, match="Unknown keys"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_duplicate_document_type_match_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"

[[tool.docguard.document_types]]
name = "decision"
glob = "docs/adr/*.md"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    with pytest.raises(ConfigurationError, match="matched multiple document types"):
        resolve_document_type_for_path(
            "docs/adr/0001-example.md",
            configuration.document_types,
        )


def test_cli_paths_override_configured_paths(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=("README.md",),
    )
    assert configuration.paths == ("README.md",)


def test_stricter_severity_override_is_loaded(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard.severity]
DG-ORG001 = "error"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.severities["DG-ORG001"] == "error"


def test_direct_looser_severity_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard.severity]
DG-STYLE001 = "warning"
""",
    )
    with pytest.raises(ConfigurationError, match="severity.DG-STYLE001"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_invalid_severity_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard.severity]
DG-SIZE001 = "banana"
""",
    )
    with pytest.raises(ConfigurationError, match="unsupported value"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_invalid_max_document_lines_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
max_document_lines = "400"
""",
    )
    with pytest.raises(ConfigurationError, match="max_document_lines"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_direct_looser_max_document_lines_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
max_document_lines = 400
""",
    )
    with pytest.raises(ConfigurationError, match="max_document_lines"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_direct_stricter_max_document_lines_is_loaded(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
max_document_lines = 240
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.max_document_lines == 240


def test_phase2_configuration_defaults_are_false(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.require_orphan_detection is False
    assert configuration.require_hub_outgoing_links is False
    assert configuration.hub_globs == tuple()


def test_phase2_configuration_keys_are_loaded(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_orphan_detection = true
require_hub_outgoing_links = true
hub_globs = ["docs/index-*.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.require_orphan_detection is True
    assert configuration.require_hub_outgoing_links is True
    assert configuration.hub_globs == ("docs/index-*.md",)


def test_duplicate_guidance_configuration_keys_are_parsed(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_duplicate_guidance_detection = true

[tool.docguard.severity]
DG-SPLIT002 = "error"

[[tool.docguard.relaxations]]
parameter = "allowed_duplicate_patterns"
value = ["^Run docguard locally"]
reason = "Legacy duplicated command guidance is being consolidated."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.require_duplicate_guidance_detection is True
    assert configuration.allowed_duplicate_patterns == ("^Run docguard locally",)
    assert configuration.duplicate_guidance_kinds == DEFAULT_DUPLICATE_GUIDANCE_KINDS
    assert configuration.severities["DG-SPLIT002"] == "error"


def test_duplicate_guidance_kinds_default_to_code_block_and_list_item(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_duplicate_guidance_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.duplicate_guidance_kinds == DEFAULT_DUPLICATE_GUIDANCE_KINDS


def test_duplicate_guidance_kinds_can_include_heading(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = ["code_block", "list_item", "heading"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.duplicate_guidance_kinds == (
        "code_block",
        "list_item",
        "heading",
    )


def test_duplicate_guidance_kinds_can_include_paragraph(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = ["code_block", "list_item", "paragraph"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.duplicate_guidance_kinds == (
        "code_block",
        "list_item",
        "paragraph",
    )


def test_empty_duplicate_guidance_kinds_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = []
""",
    )
    with pytest.raises(ConfigurationError, match="duplicate_guidance_kinds must not be empty"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_unknown_duplicate_guidance_kind_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = ["prose"]
""",
    )
    with pytest.raises(ConfigurationError, match="duplicate_guidance_kinds"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_duplicate_duplicate_guidance_kind_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = ["code_block", "code_block"]
""",
    )
    with pytest.raises(ConfigurationError, match="duplicate value"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_non_string_duplicate_guidance_kind_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
duplicate_guidance_kinds = [true]
""",
    )
    with pytest.raises(ConfigurationError, match="duplicate_guidance_kinds"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_invalid_allowed_duplicate_pattern_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.relaxations]]
parameter = "allowed_duplicate_patterns"
value = ["["]
reason = "Legacy duplicate guidance patterns are being migrated."
""",
    )
    with pytest.raises(ConfigurationError, match="allowed_duplicate_patterns"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_relaxation_requires_reason(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]

[[tool.docguard.relaxations]]
parameter = "max_document_lines"
value = 400
reason = "too short"
""",
    )
    with pytest.raises(ConfigurationError, match="reason"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_relaxation_requires_value(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]

[[tool.docguard.relaxations]]
parameter = "max_document_lines"
reason = "Legacy documents need migration time before splitting."
""",
    )
    with pytest.raises(ConfigurationError, match="value"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_unknown_relaxation_parameter_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]

[[tool.docguard.relaxations]]
parameter = "unknown"
value = true
reason = "Legacy documents need migration time before splitting."
""",
    )
    with pytest.raises(ConfigurationError, match="Unknown relaxation parameter"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_valid_relaxation_is_applied(temporary_project_directory: Path) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]

[[tool.docguard.relaxations]]
parameter = "max_document_lines"
value = 400
reason = "Legacy documents need migration time before splitting."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.max_document_lines == 400
    assert configuration.relaxation_count == 1


def test_non_string_allowed_duplicate_pattern_raises_configuration_error(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]

[[tool.docguard.relaxations]]
parameter = "allowed_duplicate_patterns"
value = [true]
reason = "Legacy duplicate guidance patterns are being migrated."
""",
    )
    with pytest.raises(ConfigurationError, match="allowed_duplicate_patterns"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_phase3_configuration_keys_are_parsed(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = true
require_heading_order_check = true

[tool.docguard.severity]
DG-SPLIT001 = "warning"
DG-FORMAT002 = "warning"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.require_mixed_role_detection is True
    assert configuration.require_heading_order_check is True
    assert configuration.severities["DG-SPLIT001"] == "warning"
    assert configuration.severities["DG-FORMAT002"] == "warning"


def test_phase3_unknown_key_still_rejected(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = true
unexpected_phase3_key = true
""",
    )
    with pytest.raises(ConfigurationError, match="Unknown keys"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_prose_style_configuration_keys_are_parsed(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
extra_prohibited_prose_patterns = ["\\\\bkindly\\\\b"]

[tool.docguard.severity]
DG-STYLE002 = "error"

[[tool.docguard.relaxations]]
parameter = "max_strong_emphasis_pairs"
value = 2
reason = "Legacy prose cleanup needs a temporary emphasis allowance."

[[tool.docguard.relaxations]]
parameter = "allowed_prose_phrases"
value = ["What you can check"]
reason = "Usage documentation keeps this exact heading during migration."

[[tool.docguard.relaxations]]
parameter = "severity.DG-STYLE001"
value = "warning"
reason = "Legacy prose style diagnostics are being migrated gradually."
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    assert configuration.max_strong_emphasis_pairs == 2
    assert configuration.allowed_prose_phrases == ("What you can check",)
    assert configuration.extra_prohibited_prose_patterns == ("\\bkindly\\b",)
    assert configuration.severities["DG-STYLE001"] == "warning"
    assert configuration.severities["DG-STYLE002"] == "error"


def test_invalid_extra_prohibited_prose_pattern_rejected(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
extra_prohibited_prose_patterns = ["(["]
""",
    )
    with pytest.raises(ConfigurationError, match="extra_prohibited_prose_patterns"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_phase2_unknown_key_still_rejected(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_orphan_detection = true
unexpected_phase2_key = true
""",
    )
    with pytest.raises(ConfigurationError, match="Unknown keys"):
        load_docguard_configuration(
            project_root=temporary_project_directory,
            config_path=temporary_project_directory / "pyproject.toml",
            cli_paths=tuple(),
        )


def test_find_project_root_walks_up_parent_directories(
    temporary_project_directory: Path,
) -> None:
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
""",
    )
    nested_directory = temporary_project_directory / "packages" / "app"
    nested_directory.mkdir(parents=True)
    configuration = load_docguard_configuration(
        project_root=nested_directory,
        config_path=None,
        cli_paths=tuple(),
    )
    assert configuration.project_root == temporary_project_directory.resolve()
    assert configuration.paths == ("docs",)
