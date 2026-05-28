"""Tests for docguard output formatters."""

from __future__ import annotations

import json

from docguard.diagnostics import (
    Diagnostic,
    DiagnosticPolicySummary,
    DiagnosticRunResult,
    SeverityLevel,
)
from docguard.formatters import (
    format_run_result_human,
    format_run_result_json,
    format_run_summary,
    format_run_verbose,
)


def build_sample_diagnostic() -> Diagnostic:
    return Diagnostic(
        code="DG-SIZE001",
        severity=SeverityLevel.ERROR,
        document_path="docs/architecture.md",
        message="docs/architecture.md has 812 lines.\nLimit: 400 lines.",
        why_it_matters="Large Markdown files tend to mix overview and operations.",
        suggestion="Suggested split:\n- docs/architecture/overview.md",
        document_type_name="design",
    )


def test_format_run_result_human_includes_failure_header() -> None:
    run_result = DiagnosticRunResult(diagnostics=(build_sample_diagnostic(),))
    formatted_output = format_run_result_human(run_result)
    assert "FAILED docs/architecture.md::docguard" in formatted_output
    assert "DG-SIZE001 document too long" in formatted_output
    assert formatted_output.count("docs/architecture.md has 812 lines.") == 1
    assert "Why this matters:" in formatted_output
    assert "Suggested split:" in formatted_output


def test_format_run_result_json_contains_structured_fields() -> None:
    run_result = DiagnosticRunResult(
        diagnostics=(build_sample_diagnostic(),),
        checked_document_count=3,
    )
    formatted_output = format_run_result_json(run_result)
    parsed_output = json.loads(formatted_output)
    assert parsed_output["checked_document_count"] == 3
    assert parsed_output["diagnostics"][0]["code"] == "DG-SIZE001"
    assert parsed_output["diagnostics"][0]["severity"] == "error"


def test_format_run_summary_reports_checked_document_count() -> None:
    run_result = DiagnosticRunResult(
        diagnostics=tuple(),
        checked_document_count=4,
    )
    formatted_output = format_run_summary(run_result)
    assert formatted_output == "Checked 4 documents. Found 0 diagnostics."


def test_format_run_summary_includes_policy_summary_when_available() -> None:
    run_result = DiagnosticRunResult(
        diagnostics=tuple(),
        checked_document_count=4,
        policy_summary=DiagnosticPolicySummary(
            name="strict baseline",
            max_document_lines=300,
            min_document_lines=20,
            max_section_lines=120,
            require_index_reachability=True,
            require_duplicate_guidance_detection=True,
            relaxation_count=0,
        ),
    )
    formatted_output = format_run_summary(run_result)
    assert "Checked 4 documents. Found 0 diagnostics." in formatted_output
    assert "Policy: strict baseline" in formatted_output
    assert "max document 300" in formatted_output
    assert "0 relaxations" in formatted_output


def test_format_run_verbose_reports_no_diagnostics_on_clean_run() -> None:
    run_result = DiagnosticRunResult(
        diagnostics=tuple(),
        checked_document_count=4,
    )
    formatted_output = format_run_verbose(run_result)
    assert formatted_output == "Checked 4 documents. No diagnostics."


def test_format_run_verbose_includes_warning_diagnostics() -> None:
    warning_diagnostic = Diagnostic(
        code="DG-SIZE001",
        severity=SeverityLevel.WARNING,
        document_path="docs/architecture.md",
        message="docs/architecture.md has 812 lines.",
        why_it_matters="Large Markdown files tend to mix overview and operations.",
        suggestion=None,
    )
    run_result = DiagnosticRunResult(
        diagnostics=(warning_diagnostic,),
        checked_document_count=2,
    )
    formatted_output = format_run_verbose(run_result)
    assert "Checked 2 documents. Found 1 diagnostics." in formatted_output
    assert "DG-SIZE001 document too long" in formatted_output
