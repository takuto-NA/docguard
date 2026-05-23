"""Command-line interface for docguard."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from docguard.config import find_project_root
from docguard.constants import (
    EXIT_CODE_CONFIGURATION_FAILURE,
    EXIT_CODE_DIAGNOSTIC_FAILURE,
    EXIT_CODE_SUCCESS,
)
from docguard.diagnostics import resolve_exit_code_from_diagnostics
from docguard.formatters import (
    format_run_result_human,
    format_run_result_json,
    format_run_summary,
    format_run_verbose,
)
from docguard.runner import DocguardConfigurationFailure, run_docguard_from_paths

OUTPUT_FORMAT_HUMAN = "human"
OUTPUT_FORMAT_JSON = "json"


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(
        prog="docguard",
        description="Check Markdown document structure in a repository.",
    )
    argument_parser.add_argument(
        "paths",
        nargs="*",
        help="Markdown files or directories to scan. Overrides configured paths.",
    )
    argument_parser.add_argument(
        "--config",
        type=Path,
        help="Path to a pyproject.toml file containing [tool.docguard].",
    )
    argument_parser.add_argument(
        "--format",
        choices=[OUTPUT_FORMAT_HUMAN, OUTPUT_FORMAT_JSON],
        default=OUTPUT_FORMAT_HUMAN,
        help="Output format for diagnostics.",
    )
    argument_parser.add_argument(
        "--summary",
        action="store_true",
        help=(
            "Print checked document count and diagnostic count when the run "
            "succeeds with no diagnostics."
        ),
    )
    argument_parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print checked document count and any non-error diagnostics.",
    )
    argument_parser.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "Suppress human output on success, including warnings. "
            "Errors still print."
        ),
    )
    return argument_parser


def resolve_project_root(config_path: Path | None) -> Path:
    if config_path is not None:
        return config_path.parent.resolve()
    discovered_project_root = find_project_root(Path.cwd())
    if discovered_project_root is not None:
        return discovered_project_root
    return Path.cwd().resolve()


def main(argv: list[str] | None = None) -> int:
    argument_parser = build_argument_parser()
    arguments = argument_parser.parse_args(argv)

    if arguments.verbose and arguments.format == OUTPUT_FORMAT_JSON:
        argument_parser.error("--verbose cannot be used with --format json")

    if arguments.quiet and arguments.summary:
        argument_parser.error("--quiet cannot be used with --summary")

    if arguments.quiet and arguments.verbose:
        argument_parser.error("--quiet cannot be used with --verbose")

    project_root = resolve_project_root(arguments.config)
    cli_paths = tuple(arguments.paths)

    try:
        run_result = run_docguard_from_paths(
            project_root=project_root,
            cli_paths=cli_paths,
            config_path=arguments.config,
        )
    except DocguardConfigurationFailure as error:
        print(str(error), file=sys.stderr)
        return EXIT_CODE_CONFIGURATION_FAILURE

    if arguments.format == OUTPUT_FORMAT_JSON:
        print(format_run_result_json(run_result))
    elif run_result.has_error_severity:
        print(format_run_result_human(run_result))
    elif arguments.verbose:
        print(format_run_verbose(run_result))
    elif arguments.quiet:
        pass
    elif run_result.diagnostics:
        print(format_run_result_human(run_result))
    elif arguments.summary:
        print(format_run_summary(run_result))

    return resolve_exit_code_from_diagnostics(run_result.diagnostics)


if __name__ == "__main__":
    raise SystemExit(main())
