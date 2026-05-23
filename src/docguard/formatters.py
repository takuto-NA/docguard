"""Human-readable and JSON formatters for docguard diagnostics."""

from __future__ import annotations

import json
from dataclasses import asdict

from docguard.constants import DIAGNOSTIC_TITLES
from docguard.diagnostics import Diagnostic, DiagnosticRunResult


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
        "diagnostics": [
            diagnostic_to_dict(diagnostic)
            for diagnostic in run_result.diagnostics
        ]
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)
