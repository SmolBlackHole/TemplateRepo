# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Generate profiles in temporary directories and run their real checks."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from new_project import FEATURES, PROFILES, create_project, project_values


def _wrapper_command(destination: Path, command: str) -> tuple[str, ...]:
    if os.name == "nt":
        powershell = shutil.which("powershell")
        if powershell is None:
            raise SystemExit("PowerShell is required to verify Windows wrappers.")
        return (
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(destination / "scripts" / f"{command}.ps1"),
        )
    shell = shutil.which("sh")
    if shell is None:
        raise SystemExit("A POSIX shell is required to verify shell wrappers.")
    return (shell, str(destination / "scripts" / f"{command}.sh"))


def verify_profile(
    profile: str, temporary_root: Path, features: tuple[str, ...]
) -> None:
    """Generate, set up and check one selected profile."""
    destination = temporary_root / profile
    values = project_values(
        name=f"Verification {profile.title()}",
        profile=profile,
        description=f"Temporary {profile} profile verification.",
        author="TemplateRepo",
    )
    create_project(
        destination=destination,
        values=values,
        initialize_git=False,
        features=features,
    )
    for command in ("setup", "setup", "check"):
        print(f"\n> [{profile}] {command}", flush=True)
        subprocess.run(
            _wrapper_command(destination, command),
            cwd=destination,
            check=True,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        action="append",
        choices=PROFILES,
        help="Profile to verify. Repeat the option to select multiple profiles.",
    )
    parser.add_argument(
        "--feature",
        action="append",
        choices=FEATURES,
        help="Optional generated feature. Repeat to select multiple features.",
    )
    args = parser.parse_args()
    profiles = tuple(args.profile or PROFILES)
    features = tuple(args.feature or ())

    with tempfile.TemporaryDirectory(prefix="templaterepo-verification-") as temporary:
        temporary_root = Path(temporary)
        for profile in profiles:
            verify_profile(profile, temporary_root, features)


if __name__ == "__main__":
    main()
