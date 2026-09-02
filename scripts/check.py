# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Run TemplateRepo's repository checks and generator tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from repository_checks import run_repository_checks

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    run_repository_checks(ROOT)
    completed = subprocess.run(
        (sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"),
        cwd=ROOT,
        check=False,
    )
    if completed.returncode:
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
