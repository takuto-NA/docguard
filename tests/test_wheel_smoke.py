"""Pytest wrapper for scripts/wheel_smoke.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
WHEEL_SMOKE_SCRIPT_PATH = REPOSITORY_ROOT / "scripts" / "wheel_smoke.py"


def test_wheel_smoke_script_passes() -> None:
    if shutil.which("uv") is None:
        import pytest

        pytest.skip("uv is not available on PATH.")

    completed_process = subprocess.run(
        [sys.executable, str(WHEEL_SMOKE_SCRIPT_PATH)],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed_process.returncode == 0, (
        "Wheel smoke script failed.\n"
        f"stdout:\n{completed_process.stdout}\n"
        f"stderr:\n{completed_process.stderr}"
    )
