"""Human-readable and JSON formatters for docguard diagnostics."""

from __future__ import annotations

import json
from dataclasses import asdict

from docguard.constants import DIAGNOSTIC_TITLES
from docguard.diagnostics import (
    Diagnostic,
    DiagnosticPolicySummary,
    DiagnosticRunResult,
    SeverityLevel,
)


def format_document_diagnostics_human(
    document_path: str,
    diagnostics: tuple[Diagnostic, ...],
) -> str:
    if not diagnostics:
        return ""

    lines = [f"FAILED {document_path}::docguard", ""]
    for diagnostic in diagnostics:
        diagnostic_title = DIAGNOSTIC_TITLES.get(diagnostic.code, "diagnostic")
        lines.append(f"{diagnostic.code} {diagnostic_title}")
        for message_line in diagnostic.message.splitlines():
            lines.append(f"  {message_line}")
        lines.append("")
        if diagnostic.document_type_name is not None:
            lines.append("Document type:")
            lines.append(f"  {diagnostic.document_type_name}")
            lines.append("")
        lines.append("Why this matters:")
        lines.append(f"  {diagnostic.why_it_matters}")
        lines.append("")
        if diagnostic.suggestion is not None:
            if diagnostic.suggestion.startswith("Suggested split:"):
                lines.append("Suggested split:")
                for suggestion_line in diagnostic.suggestion.splitlines()[1:]:
                    cleaned_line = suggestion_line.strip()
                    if cleaned_line.startswith("- "):
                        cleaned_line = cleaned_line[2:]
                    lines.append(f"  - {cleaned_line}")
            else:
                lines.append(diagnostic.suggestion)
            lines.append("")
    return "\n".join(lines).rstrip()


def format_run_result_human(run_result: DiagnosticRunResult) -> str:
    diagnostics_by_document: dict[str, list[Diagnostic]] = {}
    for diagnostic in run_result.diagnostics:
        diagnostics_by_document.setdefault(diagnostic.document_path, []).append(
            diagnostic
        )

    formatted_blocks: list[str] = []
    for document_path in sorted(diagnostics_by_document):
        formatted_blocks.append(
            format_document_diagnostics_human(
                document_path,
                tuple(diagnostics_by_document[document_path]),
            )
        )
    return "\n\n".join(formatted_blocks)


def diagnostic_to_dict(diagnostic: Diagnostic) -> dict[str, object]:
    diagnostic_dict = asdict(diagnostic)
    diagnostic_dict["severity"] = diagnostic.severity.value
    return diagnostic_dict


def format_run_result_json(run_result: DiagnosticRunResult) -> str:
    payload = {
        "checked_document_count": run_result.checked_document_count,
        "diagnostics": [
            diagnostic_to_dict(diagnostic)
            for diagnostic in run_result.diagnostics
        ]
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def format_run_summary(run_result: DiagnosticRunResult) -> str:
    diagnostic_count = len(run_result.diagnostics)
    summary_line = (
        f"Checked {run_result.checked_document_count} documents. "
        f"Found {diagnostic_count} diagnostics."
    )
    if run_result.policy_summary is None:
        return summary_line
    return f"{summary_line}\n{format_policy_summary(run_result.policy_summary)}"


def format_enabled_flag(enabled: bool) -> str:
    return "on" if enabled else "off"


def format_policy_summary(policy_summary: DiagnosticPolicySummary) -> str:
    return (
        f"Policy: {policy_summary.name} "
        f"(max document {policy_summary.max_document_lines}, "
        f"min document {policy_summary.min_document_lines}, "
        f"max section {policy_summary.max_section_lines}, "
        "index reachability "
        f"{format_enabled_flag(policy_summary.require_index_reachability)}, "
        "duplicate guidance "
        f"{format_enabled_flag(policy_summary.require_duplicate_guidance_detection)}, "
        f"{policy_summary.relaxation_count} relaxations)."
    )


def format_run_verbose(run_result: DiagnosticRunResult) -> str:
    if not run_result.diagnostics:
        return (
            f"Checked {run_result.checked_document_count} documents. "
            "No diagnostics."
        )

    non_error_diagnostics = tuple(
        diagnostic
        for diagnostic in run_result.diagnostics
        if diagnostic.severity is not SeverityLevel.ERROR
    )
    if not non_error_diagnostics:
        return format_run_summary(run_result)

    summary_line = (
        f"Checked {run_result.checked_document_count} documents. "
        f"Found {len(non_error_diagnostics)} diagnostics."
    )
    diagnostic_blocks = format_run_result_human(
        DiagnosticRunResult(
            diagnostics=non_error_diagnostics,
            checked_document_count=run_result.checked_document_count,
            checked_document_paths=run_result.checked_document_paths,
        )
    )
    return f"{summary_line}\n\n{diagnostic_blocks}"
