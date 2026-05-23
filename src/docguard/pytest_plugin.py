"""Pytest adapter for docguard."""

from __future__ import annotations

from pathlib import Path

import pytest

from docguard.config import ConfigurationError, find_project_root, load_docguard_configuration
from docguard.diagnostics import Diagnostic
from docguard.discovery import discover_documents
from docguard.formatters import format_document_diagnostics_human
from docguard.runner import DocguardConfigurationFailure, run_docguard_checks

DOCGUARD_COLLECTOR_NAME = "docguard"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--docguard",
        action="store_true",
        default=False,
        help="Run docguard checks against configured Markdown documents.",
    )


def pytest_configure(config: pytest.Config) -> None:
    if config.getoption("--docguard"):
        config.addinivalue_line(
            "markers",
            "docguard: docguard document structure check",
        )


def pytest_collection_modifyitems(
    session: pytest.Session,
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    if not config.getoption("--docguard"):
        return

    docguard_collector = DocguardRootCollector.from_parent(
        session,
        name=DOCGUARD_COLLECTOR_NAME,
    )
    items.extend(docguard_collector.collect())


class DocguardRootCollector(pytest.Collector):
    def collect(self) -> list[pytest.Item]:
        project_root = find_project_root(self.config.rootpath)
        if project_root is None:
            project_root = self.config.rootpath.resolve()

        try:
            configuration = load_docguard_configuration(
                project_root=project_root,
                config_path=None,
                cli_paths=tuple(),
            )
            run_result = run_docguard_checks(configuration)
            document_contexts = discover_documents(configuration)
        except ConfigurationError as error:
            raise DocguardConfigurationFailure(str(error)) from error

        diagnostics_by_document: dict[str, list[Diagnostic]] = {}
        for diagnostic in run_result.diagnostics:
            diagnostics_by_document.setdefault(diagnostic.document_path, []).append(
                diagnostic
            )

        collected_items: list[pytest.Item] = []
        for inspection_context in document_contexts:
            document_path = inspection_context.parsed_document.repository_relative_path
            collected_items.append(
                DocguardMarkdownItem.from_parent(
                    self,
                    name=f"{document_path}::docguard",
                    document_path=document_path,
                    diagnostics=tuple(diagnostics_by_document.get(document_path, [])),
                )
            )
        return collected_items


class DocguardMarkdownItem(pytest.Item):
    def __init__(
        self,
        name: str,
        parent: pytest.Collector,
        document_path: str,
        diagnostics: tuple[Diagnostic, ...],
        **kwargs: object,
    ) -> None:
        super().__init__(name, parent, **kwargs)
        self.document_path = document_path
        self.diagnostics = diagnostics

    def runtest(self) -> None:
        if not self.diagnostics:
            return
        failure_message = format_document_diagnostics_human(
            self.document_path,
            self.diagnostics,
        )
        pytest.fail(failure_message)

    def reportinfo(self) -> tuple[Path, int | None, str]:
        return self.config.rootpath / self.document_path, None, "docguard"
