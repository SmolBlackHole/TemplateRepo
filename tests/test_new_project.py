# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from new_project import (  # noqa: E402
    PROFILES,
    create_project,
    install_features,
    project_values,
)
from repository_checks import repository_errors  # noqa: E402


class ProjectGenerationTests(unittest.TestCase):
    def test_every_profile_generates_a_valid_repository(self) -> None:
        source_editorconfig = (ROOT / ".editorconfig").read_bytes()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            for profile in PROFILES:
                with self.subTest(profile=profile):
                    destination = temporary_root / profile
                    values = project_values(
                        name="Tiny Example",
                        profile=profile,
                        description="Generated during a regression test.",
                        author="Template Test",
                    )
                    create_project(
                        destination=destination,
                        values=values,
                        initialize_git=False,
                    )

                    self.assertEqual(
                        (destination / ".editorconfig").read_bytes(),
                        source_editorconfig,
                    )
                    self.assertEqual(repository_errors(destination), ())
                    self.assertTrue((destination / "scripts" / "dev.py").is_file())
                    self.assertFalse((destination / "Dockerfile.ci").exists())

    def test_local_ci_feature_generates_for_every_profile(self) -> None:
        expected_bases = {
            "python": "FROM python:3.12-slim-bookworm",
            "node": "FROM node:22-bookworm-slim AS node",
            "cpp": "ninja-build",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            for profile in PROFILES:
                with self.subTest(profile=profile):
                    destination = temporary_root / profile
                    values = project_values(
                        name=f"Container {profile.title()}",
                        profile=profile,
                        description="Generated with the local CI feature.",
                        author="Template Test",
                    )
                    create_project(
                        destination=destination,
                        values=values,
                        initialize_git=False,
                        features=("local-ci",),
                    )

                    dockerfile = (destination / "Dockerfile.ci").read_text(
                        encoding="utf-8"
                    )
                    runner = (destination / "scripts" / "check_container.py").read_text(
                        encoding="utf-8"
                    )
                    development = (destination / "docs" / "development.md").read_text(
                        encoding="utf-8"
                    )
                    self.assertIn(expected_bases[profile], dockerfile)
                    self.assertIn(
                        'CMD ["python", "scripts/dev.py", "check"]', dockerfile
                    )
                    self.assertIn('"--init", "--rm"', runner)
                    self.assertIn("## Run the Linux CI precheck", development)
                    self.assertTrue((destination / ".dockerignore").is_file())
                    self.assertEqual(repository_errors(destination), ())

    def test_local_ci_can_be_added_to_an_existing_project_idempotently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "existing"
            values = project_values(
                name="Existing",
                profile="python",
                description=None,
                author="Template Test",
            )
            create_project(
                destination=destination,
                values=values,
                initialize_git=False,
            )

            install_features(
                destination=destination,
                profile="python",
                features=("local-ci",),
            )
            development = destination / "docs" / "development.md"
            first = development.read_text(encoding="utf-8")
            install_features(
                destination=destination,
                profile="python",
                features=("local-ci", "local-ci"),
            )

            self.assertEqual(development.read_text(encoding="utf-8"), first)
            self.assertEqual(first.count("## Run the Linux CI precheck"), 1)

    def test_feature_conflict_leaves_existing_project_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "existing"
            values = project_values(
                name="Existing",
                profile="node",
                description=None,
                author="Template Test",
            )
            create_project(
                destination=destination,
                values=values,
                initialize_git=False,
            )
            dockerfile = destination / "Dockerfile.ci"
            dockerfile.write_text("keep me\n", encoding="utf-8")
            development = destination / "docs" / "development.md"
            before = development.read_bytes()

            with self.assertRaisesRegex(FileExistsError, "would replace"):
                install_features(
                    destination=destination,
                    profile="node",
                    features=("local-ci",),
                )

            self.assertEqual(dockerfile.read_text(encoding="utf-8"), "keep me\n")
            self.assertEqual(development.read_bytes(), before)

    def test_existing_destination_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "existing"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("user data\n", encoding="utf-8")
            values = project_values(
                name="Existing",
                profile="python",
                description=None,
                author="Template Test",
            )

            with self.assertRaises(FileExistsError):
                create_project(
                    destination=destination,
                    values=values,
                    initialize_git=False,
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "user data\n")

    @unittest.skipIf(shutil.which("git") is None, "git is not installed")
    def test_git_initialization_creates_no_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "git-project"
            values = project_values(
                name="Git Project",
                profile="node",
                description=None,
                author="Template Test",
            )
            create_project(
                destination=destination,
                values=values,
                initialize_git=True,
            )

            branch = subprocess.run(
                ("git", "branch", "--show-current"),
                cwd=destination,
                check=True,
                capture_output=True,
                text=True,
            )
            head = subprocess.run(
                ("git", "rev-parse", "--verify", "HEAD"),
                cwd=destination,
                check=False,
                capture_output=True,
            )

            self.assertEqual(branch.stdout.strip(), "main")
            self.assertNotEqual(head.returncode, 0)

    def test_identifiers_are_safe_for_all_profiles(self) -> None:
        values = project_values(
            name="2026 Über Tool!",
            profile="cpp",
            description=None,
            author="Template Test",
        )

        self.assertEqual(values.project_slug, "2026-uber-tool")
        self.assertEqual(values.project_symbol, "project_2026_uber_tool")
        self.assertEqual(values.python_package, "project_2026_uber_tool")

    def test_empty_name_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            project_values(
                name="   ",
                profile="node",
                description=None,
                author="Template Test",
            )

    def test_string_values_are_escaped_for_profile_formats(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            for profile in PROFILES:
                with self.subTest(profile=profile):
                    destination = temporary_root / profile
                    values = project_values(
                        name='A "Quoted" Project',
                        profile=profile,
                        description='Handles "quotes" and backslashes \\ safely.',
                        author='A "Quoted" Author',
                    )
                    create_project(
                        destination=destination,
                        values=values,
                        initialize_git=False,
                    )
                    if profile == "python":
                        with (destination / "pyproject.toml").open("rb") as stream:
                            parsed = tomllib.load(stream)
                        self.assertEqual(
                            parsed["project"]["description"],
                            values.description,
                        )
                    elif profile == "node":
                        parsed = json.loads(
                            (destination / "package.json").read_text(encoding="utf-8")
                        )
                        self.assertEqual(parsed["description"], values.description)
                    else:
                        source = (destination / "src" / "project_info.cpp").read_text(
                            encoding="utf-8"
                        )
                        self.assertIn(r"\"Quoted\"", source)

    def test_multiline_values_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "single line"):
            project_values(
                name="Two\nLines",
                profile="node",
                description=None,
                author="Template Test",
            )


if __name__ == "__main__":
    unittest.main()
