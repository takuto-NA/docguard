"""Build a wheel, install it in a temporary uv environment, and verify entry points.

Responsibility: prove the PyPI artifact works outside editable source layout.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DIST_DIRECTORY = REPOSITORY_ROOT / "dist"
WHEEL_FILE_GLOB = "*.whl"

MINIMAL_SAMPLE_PROJECT_NAME = "sample-docguard-project"
MINIMAL_SAMPLE_DOCUMENT_RELATIVE_PATH = "docs/example.md"
MINIMAL_SAMPLE_DOCUMENT_CONTENT = "# Example\n"
MINIMAL_SAMPLE_PYPROJECT_CONTENT = """\
[project]
name = "sample-docguard-project"
version = "0.0.0"
requires-python = ">=3.11"

[tool.docguard]
paths = ["docs"]
"""


def resolve_uv_executable() -> str:
    uv_executable = shutil.which("uv")
    if uv_executable is None:
        raise RuntimeError(
            "uv is required for wheel smoke verification but was not found on PATH."
        )
    return uv_executable


def run_command(
    command: list[str],
    *,
    working_directory: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed_process = subprocess.run(
        command,
        cwd=working_directory,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed_process.returncode != 0:
        raise RuntimeError(
            "Command failed: "
            f"{' '.join(command)}\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )
    return completed_process


def build_wheel_distribution() -> Path:
    run_command(
        [sys.executable, "-m", "build", "--wheel", str(REPOSITORY_ROOT)],
        working_directory=REPOSITORY_ROOT,
    )

    wheel_files = sorted(DIST_DIRECTORY.glob(WHEEL_FILE_GLOB))
    if not wheel_files:
        raise RuntimeError("No wheel file was produced in dist/.")

    return wheel_files[-1]


def create_temporary_virtual_environment(
    temporary_directory: Path,
    uv_executable: str,
) -> Path:
    virtual_environment_directory = temporary_directory / ".venv"
    run_command(
        [uv_executable, "venv", str(virtual_environment_directory)],
        working_directory=temporary_directory,
    )
    return virtual_environment_directory


def install_wheel_into_virtual_environment(
    wheel_file_path: Path,
    virtual_environment_directory: Path,
    uv_executable: str,
) -> None:
    run_command(
        [
            uv_executable,
            "pip",
            "install",
            "--python",
            str(virtual_environment_directory / "Scripts" / "python.exe")
            if sys.platform == "win32"
            else str(virtual_environment_directory / "bin" / "python"),
            str(wheel_file_path),
            "pytest>=8.0",
        ],
        working_directory=REPOSITORY_ROOT,
    )


def resolve_virtual_environment_python(
    virtual_environment_directory: Path,
) -> Path:
    if sys.platform == "win32":
        return virtual_environment_directory / "Scripts" / "python.exe"
    return virtual_environment_directory / "bin" / "python"


def resolve_virtual_environment_docguard_executable(
    virtual_environment_directory: Path,
) -> Path:
    if sys.platform == "win32":
        return virtual_environment_directory / "Scripts" / "docguard.exe"
    return virtual_environment_directory / "bin" / "docguard"


def verify_console_script_help(
    docguard_executable_path: Path,
) -> None:
    completed_process = run_command(
        [str(docguard_executable_path), "--help"],
        check=False,
    )
    if completed_process.returncode != 0:
        raise RuntimeError(
            "Installed docguard console script failed --help.\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )
    if "Check Markdown document structure" not in completed_process.stdout:
        raise RuntimeError(
            "Installed docguard --help output did not include expected description."
        )


def create_minimal_sample_project(sample_project_directory: Path) -> None:
    sample_document_path = sample_project_directory / MINIMAL_SAMPLE_DOCUMENT_RELATIVE_PATH
    sample_document_path.parent.mkdir(parents=True, exist_ok=True)
    sample_document_path.write_text(MINIMAL_SAMPLE_DOCUMENT_CONTENT, encoding="utf-8")
    sample_pyproject_path = sample_project_directory / "pyproject.toml"
    sample_pyproject_path.write_text(MINIMAL_SAMPLE_PYPROJECT_CONTENT, encoding="utf-8")


def verify_installed_pytest_plugin(
    virtual_environment_python: Path,
    sample_project_directory: Path,
) -> None:
    completed_process = run_command(
        [
            str(virtual_environment_python),
            "-m",
            "pytest",
            "--docguard-only",
            "-q",
        ],
        working_directory=sample_project_directory,
        check=False,
    )
    if completed_process.returncode != 0:
        raise RuntimeError(
            "Installed pytest plugin failed --docguard-only in sample project.\n"
            f"stdout:\n{completed_process.stdout}\n"
            f"stderr:\n{completed_process.stderr}"
        )


def run_wheel_smoke() -> None:
    uv_executable = resolve_uv_executable()
    wheel_file_path = build_wheel_distribution()

    with tempfile.TemporaryDirectory(prefix="docguard-wheel-smoke-") as temporary_directory_name:
        temporary_directory = Path(temporary_directory_name)
        virtual_environment_directory = create_temporary_virtual_environment(
            temporary_directory,
            uv_executable,
        )
        install_wheel_into_virtual_environment(
            wheel_file_path,
            virtual_environment_directory,
            uv_executable,
        )

        docguard_executable_path = resolve_virtual_environment_docguard_executable(
            virtual_environment_directory
        )
        verify_console_script_help(docguard_executable_path)

        sample_project_directory = temporary_directory / MINIMAL_SAMPLE_PROJECT_NAME
        create_minimal_sample_project(sample_project_directory)

        virtual_environment_python = resolve_virtual_environment_python(
            virtual_environment_directory
        )
        verify_installed_pytest_plugin(
            virtual_environment_python,
            sample_project_directory,
        )


def main() -> int:
    try:
        run_wheel_smoke()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        return 1
    print("Wheel smoke verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
