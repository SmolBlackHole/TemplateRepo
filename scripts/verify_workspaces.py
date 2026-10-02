# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Generate representative workspaces and run their real quality commands."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

from generation import FEATURES
from new_workspace import ComponentSpec, create_workspace, workspace_values


def _run(root: Path, script: Path, command: str | None = None) -> None:
    arguments = [sys.executable, str(script)]
    if command is not None:
        arguments.append(command)
    subprocess.run(arguments, cwd=root, check=True)


def _verify_monorepo(root: Path, features: tuple[str, ...], containers: bool) -> None:
    values = workspace_values(
        name="Verification Monorepo",
        layout="monorepo",
        components=(
            ComponentSpec("frontend", "node"),
            ComponentSpec("backend", "python"),
            ComponentSpec("engine", "cpp"),
        ),
        description="Temporary monorepo verification.",
        author="TemplateRepo",
        features=features,
    )
    destination = create_workspace(
        destination=root / "monorepo",
        values=values,
        initialize_git=False,
    )
    runner = destination / "scripts" / "workspace.py"
    for command in ("setup", "setup", "check"):
        print(f"\n> [monorepo] {command}", flush=True)
        _run(destination, runner, command)
    if containers:
        for component in values.components:
            component_root = destination / "apps" / component.name
            print(f"\n> [monorepo/{component.name}] local-ci", flush=True)
            _run(
                component_root,
                component_root / "scripts" / "check_container.py",
            )


def _verify_dual_repo(root: Path, features: tuple[str, ...], containers: bool) -> None:
    values = workspace_values(
        name="Verification Dual Repo",
        layout="dual-repo",
        components=(
            ComponentSpec("frontend", "node"),
            ComponentSpec("backend", "python"),
        ),
        description="Temporary dual-repo verification.",
        author="TemplateRepo",
        features=features,
    )
    destination = create_workspace(
        destination=root / "dual-repo",
        values=values,
        initialize_git=False,
    )
    for component in values.components:
        component_root = destination / component.name
        runner = component_root / "scripts" / "project.py"
        for command in ("setup", "setup", "check"):
            print(f"\n> [dual-repo/{component.name}] {command}", flush=True)
            _run(component_root, runner, command)
        if containers:
            print(f"\n> [dual-repo/{component.name}] local-ci", flush=True)
            _run(
                component_root,
                component_root / "scripts" / "check_container.py",
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--layout",
        action="append",
        choices=("monorepo", "dual-repo"),
        help="Layout to verify. Repeat to select both.",
    )
    parser.add_argument(
        "--feature",
        action="append",
        choices=FEATURES,
        help="Feature to include. Repeat to select multiple features.",
    )
    parser.add_argument(
        "--containers",
        action="store_true",
        help="Build and run local-ci containers for every component.",
    )
    args = parser.parse_args()
    layouts = tuple(args.layout or ("monorepo", "dual-repo"))
    features = list(args.feature or ())
    if args.containers and "local-ci" not in features:
        features.append("local-ci")

    with tempfile.TemporaryDirectory(prefix="tr-") as temporary:
        root = Path(temporary)
        if "monorepo" in layouts:
            _verify_monorepo(root, tuple(features), args.containers)
        if "dual-repo" in layouts:
            _verify_dual_repo(root, tuple(features), args.containers)


if __name__ == "__main__":
    main()
