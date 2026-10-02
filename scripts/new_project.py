# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Create a project from the shared base and one runtime profile."""

from __future__ import annotations

import argparse
from pathlib import Path

from generation import (
    FEATURES,
    PROFILES,
    ROOT,
    TEMPLATES,
    ProjectValues,
    copy_shared_files,
    copy_template_tree,
    initialize_git_repository,
    install_features,
    project_values,
    staged_destination,
    validate_generated_project,
)


def create_project(
    *,
    destination: Path,
    values: ProjectValues,
    initialize_git: bool,
    features: tuple[str, ...] = (),
) -> Path:
    """Create one complete project without overwriting an existing path."""
    with staged_destination(destination, values.project_slug) as (destination, staging):
        copy_template_tree(TEMPLATES / "repository", staging, values)
        copy_template_tree(TEMPLATES / "layouts" / "single", staging, values)
        profile_root = TEMPLATES / "profiles" / values.profile
        copy_template_tree(profile_root / "component", staging, values)
        copy_template_tree(profile_root / "repository", staging, values)
        copy_shared_files(staging)
        install_features(
            destination=staging,
            profile=values.profile,
            features=features,
            tokens=values.tokens(),
        )
        validate_generated_project(staging)
        if initialize_git:
            initialize_git_repository(staging)

    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--name", "-Name", required=True, help="Human-readable project name."
    )
    parser.add_argument("--profile", "-Profile", required=True, choices=PROFILES)
    parser.add_argument(
        "--destination", "-Destination", type=Path, help="New project directory."
    )
    parser.add_argument(
        "--description", "-Description", help="One-sentence project description."
    )
    parser.add_argument("--author", "-Author", default="SmolBlackHole")
    parser.add_argument(
        "--feature",
        "-Feature",
        action="append",
        choices=FEATURES,
        default=[],
        help="Optional feature to include. Repeat to select multiple features.",
    )
    parser.add_argument(
        "--no-git",
        "-NoGit",
        action="store_true",
        help="Do not initialize a Git repository.",
    )
    return parser


def main() -> None:
    args = _parser().parse_args()
    values = project_values(
        name=args.name,
        profile=args.profile,
        description=args.description,
        author=args.author,
    )
    destination = args.destination or ROOT.parent / values.project_slug
    created = create_project(
        destination=destination,
        values=values,
        initialize_git=not args.no_git,
        features=tuple(args.feature),
    )
    print(f"Created {values.profile} project at {created}")
    print(f"Next: {created / 'scripts' / 'setup.ps1'}")


if __name__ == "__main__":
    main()
