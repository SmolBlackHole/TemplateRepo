# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import new as interactive_cli  # noqa: E402
from new import run_interactive  # noqa: E402
from new_workspace import (  # noqa: E402
    ComponentSpec,
    create_workspace,
    parse_component,
    workspace_values,
)
from repository_checks import repository_errors  # noqa: E402


def _values(layout: str, *, features: tuple[str, ...] = ()):
    return workspace_values(
        name="Example Platform",
        layout=layout,
        components=(
            ComponentSpec("frontend", "node"),
            ComponentSpec("backend", "python"),
        ),
        description="A generated workspace.",
        author="Template Test",
        features=features,
    )


class WorkspaceGenerationTests(unittest.TestCase):
    def test_interactive_entrypoint_rejects_redirected_input(self) -> None:
        with (
            mock.patch.object(interactive_cli.sys.stdin, "isatty", return_value=False),
            self.assertRaisesRegex(SystemExit, "requires a terminal"),
        ):
            interactive_cli.main()

    def test_component_parser_rejects_unsafe_or_unsupported_values(self) -> None:
        self.assertEqual(
            parse_component("web-app:node"),
            ComponentSpec("web-app", "node"),
        )
        for value in ("frontend", "../frontend:node", "Frontend:node", "web:rust"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_component(value)

    def test_monorepo_owns_shared_files_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "monorepo"
            create_workspace(
                destination=destination,
                values=_values("monorepo", features=("local-ci",)),
                initialize_git=False,
            )

            self.assertEqual(repository_errors(destination), ())
            self.assertEqual(
                (destination / ".editorconfig").read_bytes(),
                (ROOT / ".editorconfig").read_bytes(),
            )
            self.assertFalse((destination / "apps" / "frontend" / ".git").exists())
            self.assertFalse(
                (destination / "apps" / "frontend" / ".editorconfig").exists()
            )
            self.assertTrue(
                (destination / "apps" / "frontend" / "package.json").is_file()
            )
            self.assertTrue(
                (destination / "apps" / "backend" / "pyproject.toml").is_file()
            )
            for component in ("frontend", "backend"):
                self.assertTrue(
                    (destination / "apps" / component / "Dockerfile.ci").is_file()
                )
            development = (destination / "docs" / "development.md").read_text(
                encoding="utf-8"
            )
            self.assertEqual(development.count("## Run the Linux CI precheck"), 1)
            extensions = json.loads(
                (destination / ".vscode" / "extensions.json").read_text(
                    encoding="utf-8"
                )
            )["recommendations"]
            self.assertIn("ms-python.python", extensions)
            self.assertIn("github.vscode-github-actions", extensions)

    def test_dual_repo_contains_only_complete_sibling_projects(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "dual"
            create_workspace(
                destination=destination,
                values=_values("dual-repo", features=("local-ci",)),
                initialize_git=False,
            )

            self.assertEqual(
                {path.name for path in destination.iterdir()},
                {"frontend", "backend"},
            )
            for component in ("frontend", "backend"):
                root = destination / component
                self.assertEqual(repository_errors(root), ())
                self.assertEqual(
                    (root / ".editorconfig").read_bytes(),
                    (ROOT / ".editorconfig").read_bytes(),
                )
                self.assertTrue((root / "README.md").is_file())
                self.assertTrue((root / "Dockerfile.ci").is_file())

    @unittest.skipIf(shutil.which("git") is None, "git is not installed")
    def test_layouts_initialize_only_their_owned_git_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            monorepo = create_workspace(
                destination=temporary_root / "monorepo",
                values=_values("monorepo"),
                initialize_git=True,
            )
            dual = create_workspace(
                destination=temporary_root / "dual",
                values=_values("dual-repo"),
                initialize_git=True,
            )

            self.assertTrue((monorepo / ".git").is_dir())
            self.assertEqual(
                tuple(monorepo.glob("apps/*/.git")),
                (),
            )
            self.assertFalse((dual / ".git").exists())
            self.assertTrue((dual / "frontend" / ".git").is_dir())
            self.assertTrue((dual / "backend" / ".git").is_dir())
            for repository in (
                monorepo,
                dual / "frontend",
                dual / "backend",
            ):
                head = subprocess.run(
                    ("git", "rev-parse", "--verify", "HEAD"),
                    cwd=repository,
                    check=False,
                    capture_output=True,
                )
                self.assertNotEqual(head.returncode, 0)

    def test_existing_workspace_destination_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "existing"
            destination.mkdir()
            marker = destination / "keep.txt"
            marker.write_text("user data\n", encoding="utf-8")

            with self.assertRaises(FileExistsError):
                create_workspace(
                    destination=destination,
                    values=_values("monorepo"),
                    initialize_git=False,
                )

            self.assertEqual(marker.read_text(encoding="utf-8"), "user data\n")

    def test_interactive_cli_creates_the_same_monorepo_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "interactive"
            answers = iter(
                (
                    "",  # monorepo
                    "",  # frontend
                    "2",  # node
                    "",  # backend
                    "1",  # python
                    "",  # no third component
                    "Interactive Platform",
                    "",
                    "",
                    "",  # no local-ci
                    str(destination),
                    "",  # confirm
                )
            )
            output: list[str] = []

            created = run_interactive(
                read=lambda _prompt: next(answers),
                write=output.append,
                default_parent=Path(temporary_directory),
                initialize_git=False,
            )

            self.assertEqual(created, destination.resolve())
            self.assertEqual(repository_errors(destination), ())
            self.assertTrue((destination / "workspace.toml").is_file())
            self.assertTrue(any("Git repositories: 1" in line for line in output))

    def test_interactive_cli_cancels_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "cancelled"
            answers = iter(
                (
                    "1",  # single project
                    "1",  # python
                    "Cancelled Project",
                    "",
                    "",
                    "",  # no local-ci
                    str(destination),
                    "n",
                )
            )

            created = run_interactive(
                read=lambda _prompt: next(answers),
                write=lambda _message: None,
                default_parent=Path(temporary_directory),
                initialize_git=False,
            )

            self.assertIsNone(created)
            self.assertFalse(destination.exists())

    def test_interactive_cli_reprompts_invalid_choices_and_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "cancelled"
            answers = iter(
                (
                    "9",  # invalid layout
                    "",  # monorepo
                    "",  # frontend
                    "2",  # node
                    "frontend",  # duplicate component
                    "",  # backend
                    "1",  # python
                    "",  # no third component
                    "Validated Platform",
                    "",
                    "",
                    "",  # no local-ci
                    str(destination),
                    "n",
                )
            )
            output: list[str] = []

            created = run_interactive(
                read=lambda _prompt: next(answers),
                write=output.append,
                default_parent=Path(temporary_directory),
                initialize_git=False,
            )

            self.assertIsNone(created)
            self.assertFalse(destination.exists())
            self.assertIn("Choose one of the listed numbers.", output)
            self.assertIn("Component names must be unique.", output)


if __name__ == "__main__":
    unittest.main()
