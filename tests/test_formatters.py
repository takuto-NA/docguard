"""Tests for docguard output formatters."""

from __future__ import annotations

import json

from docguard.diagnostics import Diagnostic, DiagnosticRunResult, SeverityLevel
from docguard.formatters import format_run_result_human, format_run_result_json


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
    run_result = DiagnosticRunResult(diagnostics=(build_sample_diagnostic(),))
    formatted_output = format_run_result_json(run_result)
    parsed_output = json.loads(formatted_output)
    assert parsed_output["diagnostics"][0]["code"] == "DG-SIZE001"
    assert parsed_output["diagnostics"][0]["severity"] == "error"
