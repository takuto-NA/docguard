"""Tests for docguard MVP rule diagnostics."""

from __future__ import annotations

from pathlib import Path

from docguard.config import load_docguard_configuration
from docguard.constants import (
    DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG,
    DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    DIAGNOSTIC_CODE_MISSING_FRONT_MATTER,
    DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
    DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING,
    DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
    DIAGNOSTIC_CODE_ORPHAN_DOCUMENT,
    DIAGNOSTIC_CODE_SECTION_TOO_LONG,
    DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
    DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX,
    EXIT_CODE_SUCCESS,
)
from docguard.diagnostics import Diagnostic, SeverityLevel, resolve_exit_code_from_diagnostics
from docguard.runner import run_docguard_checks


def write_pyproject(project_root: Path, contents: str) -> None:
    (project_root / "pyproject.toml").write_text(contents, encoding="utf-8")


def write_orphan_detection_project(project_root: Path, *, enabled: bool) -> None:
    docs_directory = project_root / "docs"
    docs_directory.mkdir()
    (project_root / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
    write_pyproject(
        project_root,
        f"""
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_orphan_detection = {"true" if enabled else "false"}
""",
    )


def diagnostics_by_code(run_result, diagnostic_code: str) -> list[Diagnostic]:
    return [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == diagnostic_code
    ]


def test_mixed_role_detection_off_emits_no_split001(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "mixed.md").write_text(
        """## Overview

Overview text.

## Deployment

Deployment text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = false
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    split001_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
    )
    assert split001_diagnostics == []


def test_mixed_document_roles_diagnostic_when_detection_enabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "mixed.md").write_text(
        """## Overview

Overview text.

## Deployment

Deployment text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_mixed_role_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    split001_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
    )

    assert len(split001_diagnostics) == 1
    split001_diagnostic = split001_diagnostics[0]
    assert split001_diagnostic.document_path == "docs/mixed.md"
    assert split001_diagnostic.severity is SeverityLevel.WARNING
    assert "narrative" in split001_diagnostic.message
    assert "operations" in split001_diagnostic.message
    assert split001_diagnostic.why_it_matters
    assert split001_diagnostic.suggestion


def test_typed_document_is_never_flagged_for_mixed_roles(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """---
status: accepted
date: 2026-05-24
---

# Example

## Status
Accepted

## Context
Context text.

## Decision
Decision text.

## Consequences
Consequence text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs/adr"]
require_mixed_role_detection = true

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    split001_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MIXED_DOCUMENT_ROLES,
    )
    assert split001_diagnostics == []


def test_heading_order_off_emits_no_format002(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "skip.md").write_text(
        """## Section

#### Deep
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_heading_order_check = false
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    format002_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
    )
    assert format002_diagnostics == []


def test_heading_level_skip_diagnostic_when_check_enabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "skip.md").write_text(
        """## Section

#### Deep
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_heading_order_check = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    format002_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_UNEXPECTED_HEADING_ORDER,
    )

    assert len(format002_diagnostics) == 1
    format002_diagnostic = format002_diagnostics[0]
    assert format002_diagnostic.document_path == "docs/skip.md"
    assert format002_diagnostic.severity is SeverityLevel.WARNING
    assert format002_diagnostic.location == "line 3"
    assert format002_diagnostic.why_it_matters
    assert format002_diagnostic.suggestion


def test_orphan_document_diagnostic_when_detection_enabled(
    temporary_project_directory: Path,
) -> None:
    write_orphan_detection_project(temporary_project_directory, enabled=True)
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    orphan_diagnostics = diagnostics_by_code(run_result, DIAGNOSTIC_CODE_ORPHAN_DOCUMENT)

    assert len(orphan_diagnostics) == 1
    orphan_diagnostic = orphan_diagnostics[0]
    assert orphan_diagnostic.document_path == "docs/orphan.md"
    assert orphan_diagnostic.severity is SeverityLevel.WARNING
    assert orphan_diagnostic.why_it_matters
    assert orphan_diagnostic.suggestion


def test_orphan_detection_off_emits_no_org001(
    temporary_project_directory: Path,
) -> None:
    write_orphan_detection_project(temporary_project_directory, enabled=False)
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_ORPHAN_DOCUMENT not in diagnostic_codes


def test_index_file_is_never_orphan_when_detection_enabled(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md"]
index_files = ["README.md"]
require_orphan_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_ORPHAN_DOCUMENT not in diagnostic_codes


def test_linked_cluster_is_unreachable_not_orphan(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    (docs_directory / "alpha.md").write_text("# Alpha\n\n[Beta](beta.md)\n", encoding="utf-8")
    (docs_directory / "beta.md").write_text("# Beta\n\n[Alpha](alpha.md)\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_index_reachability = true
require_orphan_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    unreachable_paths = {
        diagnostic.document_path
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX
    }

    assert DIAGNOSTIC_CODE_ORPHAN_DOCUMENT not in diagnostic_codes
    assert unreachable_paths == {"docs/alpha.md", "docs/beta.md"}


def test_hub_missing_outgoing_links_diagnostic(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_hub_outgoing_links = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    hub_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
    )

    assert len(hub_diagnostics) == 1
    hub_diagnostic = hub_diagnostics[0]
    assert hub_diagnostic.document_path == "README.md"
    assert hub_diagnostic.severity is SeverityLevel.WARNING
    assert hub_diagnostic.why_it_matters
    assert hub_diagnostic.suggestion


def test_hub_outgoing_off_emits_no_org002(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md"]
index_files = ["README.md"]
require_hub_outgoing_links = false
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS not in diagnostic_codes


def test_leaf_document_never_gets_org002(
    temporary_project_directory: Path,
) -> None:
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_hub_outgoing_links = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    hub_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
    )
    assert all(
        diagnostic.document_path != "docs/design.md"
        for diagnostic in hub_diagnostics
    )


def test_hub_glob_triggers_org002_only_on_match(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "index-page.md").write_text("# Index Page\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_hub_outgoing_links = true
hub_globs = ["docs/index-*.md"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    hub_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_MISSING_OUTGOING_LINKS,
    )

    assert len(hub_diagnostics) == 1
    assert hub_diagnostics[0].document_path == "docs/index-page.md"


def test_zero_hubs_with_hub_flag_on_is_noop(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
index_files = []
require_hub_outgoing_links = true
hub_globs = []
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert run_result.diagnostics == tuple()


def test_org001_severity_override_to_error(
    temporary_project_directory: Path,
) -> None:
    write_orphan_detection_project(temporary_project_directory, enabled=True)
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_orphan_detection = true

[tool.docguard.severity]
DG-ORG001 = "error"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    orphan_diagnostics = diagnostics_by_code(run_result, DIAGNOSTIC_CODE_ORPHAN_DOCUMENT)

    assert len(orphan_diagnostics) == 1
    assert orphan_diagnostics[0].severity is SeverityLevel.ERROR


def test_org_diagnostics_sorted_by_document_path(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    (docs_directory / "alpha-orphan.md").write_text("# Alpha\n", encoding="utf-8")
    (docs_directory / "beta-orphan.md").write_text("# Beta\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_orphan_detection = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    orphan_diagnostics = diagnostics_by_code(run_result, DIAGNOSTIC_CODE_ORPHAN_DOCUMENT)
    orphan_paths = [diagnostic.document_path for diagnostic in orphan_diagnostics]

    assert orphan_paths == sorted(orphan_paths)
    assert orphan_paths == ["docs/alpha-orphan.md", "docs/beta-orphan.md"]


def test_document_too_long_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    long_lines = "\n".join(["line"] * 401)
    (docs_directory / "architecture.md").write_text(
        f"# Architecture\n\n{long_lines}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_document_lines = 400
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    diagnostic_codes = {diagnostic.code for diagnostic in run_result.diagnostics}
    assert DIAGNOSTIC_CODE_DOCUMENT_TOO_LONG in diagnostic_codes


def test_missing_required_heading_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """---
status: accepted
date: 2026-05-23
---

# Example

## Status
Accepted

## Context
Context text.

## Decision
Decision text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs/adr"]

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    missing_heading_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_MISSING_REQUIRED_HEADING
    ]
    assert len(missing_heading_diagnostics) == 1
    assert "Consequences" in missing_heading_diagnostics[0].message


def test_unreachable_from_index_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text(
        "# Index\n\n[Design](docs/design.md)\n",
        encoding="utf-8",
    )
    (docs_directory / "design.md").write_text("# Design\n", encoding="utf-8")
    (docs_directory / "hidden.md").write_text("# Hidden\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_index_reachability = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    unreachable_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX
    ]
    assert len(unreachable_diagnostics) == 1
    assert unreachable_diagnostics[0].document_path == "docs/hidden.md"


def test_linked_cluster_not_connected_to_index_is_unreachable(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    (temporary_project_directory / "README.md").write_text("# Index\n", encoding="utf-8")
    (docs_directory / "alpha.md").write_text("# Alpha\n\n[Beta](beta.md)\n", encoding="utf-8")
    (docs_directory / "beta.md").write_text("# Beta\n", encoding="utf-8")
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["README.md", "docs"]
index_files = ["README.md"]
require_index_reachability = true
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    unreachable_paths = {
        diagnostic.document_path
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_UNREACHABLE_FROM_INDEX
    }
    assert unreachable_paths == {"docs/alpha.md", "docs/beta.md"}


def test_section_too_long_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    section_body = "\n".join(["detail"] * 121)
    (docs_directory / "design.md").write_text(
        f"## Architecture\n{section_body}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_section_lines = 120
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    section_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_SECTION_TOO_LONG
    ]
    assert len(section_diagnostics) == 1


def test_missing_front_matter_diagnostic_is_reported(
    temporary_project_directory: Path,
) -> None:
    adr_directory = temporary_project_directory / "docs" / "adr"
    adr_directory.mkdir(parents=True)
    (adr_directory / "0001-example.md").write_text(
        """# Example

## Status
Accepted

## Context
Context text.

## Decision
Decision text.

## Consequences
Consequence text.
""",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs/adr"]

[[tool.docguard.document_types]]
name = "adr"
glob = "docs/adr/*.md"
required_headings = ["Status", "Context", "Decision", "Consequences"]
required_front_matter_keys = ["status", "date"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    front_matter_diagnostics = [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == DIAGNOSTIC_CODE_MISSING_FRONT_MATTER
    ]
    assert len(front_matter_diagnostics) == 1


def test_warning_severity_does_not_fail_run(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    long_lines = "\n".join(["line"] * 401)
    (docs_directory / "architecture.md").write_text(
        f"{long_lines}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
max_document_lines = 400

[tool.docguard.severity]
DG-SIZE001 = "warning"
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    assert len(run_result.diagnostics) == 1
    assert run_result.diagnostics[0].severity is SeverityLevel.WARNING
    assert resolve_exit_code_from_diagnostics(run_result.diagnostics) == EXIT_CODE_SUCCESS


def diagnostics_by_code(run_result, diagnostic_code: str) -> list[Diagnostic]:
    return [
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.code == diagnostic_code
    ]


def test_template_headings_do_not_trigger_duplicate_guidance_diagnostic_by_default(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    for page_index in range(1, 4):
        (docs_directory / f"page-{page_index}.md").write_text(
            f"# Title {page_index}\n\n## 目的\n\nText.\n",
            encoding="utf-8",
        )
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
    run_result = run_docguard_checks(configuration)
    duplicate_guidance_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    )

    assert duplicate_guidance_diagnostics == []


def test_heading_duplicates_trigger_diagnostic_when_opted_in(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    for page_index in range(1, 4):
        (docs_directory / f"page-{page_index}.md").write_text(
            f"# Title {page_index}\n\n## 目的\n\nText.\n",
            encoding="utf-8",
        )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_duplicate_guidance_detection = true
duplicate_guidance_kinds = ["heading"]
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    duplicate_guidance_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    )

    assert len(duplicate_guidance_diagnostics) == 1
    assert duplicate_guidance_diagnostics[0].document_path == "docs/page-1.md"
    assert "heading" in duplicate_guidance_diagnostics[0].message
    assert "duplicate_guidance_kinds" in duplicate_guidance_diagnostics[0].suggestion


def test_duplicate_guidance_rule_is_silent_when_disabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    shared_install_block = """```bash
uv add docguard
uv run docguard docs/ --summary
```"""
    (docs_directory / "first.md").write_text(
        f"# First\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
    (docs_directory / "second.md").write_text(
        f"# Second\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
    write_pyproject(
        temporary_project_directory,
        """
[tool.docguard]
paths = ["docs"]
require_duplicate_guidance_detection = false
""",
    )
    configuration = load_docguard_configuration(
        project_root=temporary_project_directory,
        config_path=temporary_project_directory / "pyproject.toml",
        cli_paths=tuple(),
    )
    run_result = run_docguard_checks(configuration)
    duplicate_guidance_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    )
    assert duplicate_guidance_diagnostics == []


def test_duplicate_guidance_diagnostic_is_reported_when_enabled(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    shared_install_block = """```bash
uv add docguard
uv run docguard docs/ --summary
```"""
    (docs_directory / "first.md").write_text(
        f"# First\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
    (docs_directory / "second.md").write_text(
        f"# Second\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
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
    run_result = run_docguard_checks(configuration)
    duplicate_guidance_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    )
    assert len(duplicate_guidance_diagnostics) == 1
    assert duplicate_guidance_diagnostics[0].document_path == "docs/first.md"
    assert "code_block" in duplicate_guidance_diagnostics[0].message


def test_duplicate_guidance_uses_warning_by_default(
    temporary_project_directory: Path,
) -> None:
    docs_directory = temporary_project_directory / "docs"
    docs_directory.mkdir()
    shared_install_block = """```bash
uv add docguard
uv run docguard docs/ --summary
```"""
    (docs_directory / "first.md").write_text(
        f"# First\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
    (docs_directory / "second.md").write_text(
        f"# Second\n\n{shared_install_block}\n",
        encoding="utf-8",
    )
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
    run_result = run_docguard_checks(configuration)
    duplicate_guidance_diagnostics = diagnostics_by_code(
        run_result,
        DIAGNOSTIC_CODE_DUPLICATE_GUIDANCE,
    )
    assert len(duplicate_guidance_diagnostics) == 1
    assert duplicate_guidance_diagnostics[0].severity is SeverityLevel.WARNING
    assert resolve_exit_code_from_diagnostics(run_result.diagnostics) == EXIT_CODE_SUCCESS

