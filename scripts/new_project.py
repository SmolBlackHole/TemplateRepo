# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Create a project from the shared base and one runtime profile."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
PROFILES = ("python", "node", "cpp")
TEMPLATE_SUFFIX = ".template"
TOKEN_PATTERN = re.compile(r"{{[a-z0-9_]+}}")


@dataclass(frozen=True, slots=True)
class ProjectValues:
    """Validated substitutions used in template paths and contents."""

    project_name: str
    project_slug: str
    project_symbol: str
    python_package: str
    description: str
    author: str
    year: str
    profile: str

    def tokens(self) -> dict[str, str]:
        """Return template tokens including their delimiters."""
        token = lambda name: "{" * 2 + name + "}" * 2
        string_literal = lambda value: json.dumps(value, ensure_ascii=False)[1:-1]
        return {
            token("project_name"): self.project_name,
            token("project_name_string"): string_literal(self.project_name),
            token("project_slug"): self.project_slug,
            token("project_symbol"): self.project_symbol,
            token("python_package"): self.python_package,
            token("description"): self.description,
            token("description_string"): string_literal(self.description),
            token("author"): self.author,
            token("author_string"): string_literal(self.author),
            token("year"): self.year,
            token("profile"): self.profile,
        }


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def _single_line(label: str, value: str) -> str:
    result = value.strip()
    if not result:
        raise ValueError(f"{label} must not be empty")
    if any(ord(character) < 32 for character in result):
        raise ValueError(f"{label} must be a single line without control characters")
    if "{{" in result or "}}" in result:
        raise ValueError(f"{label} must not contain template token delimiters")
    return result


def project_values(
    *, name: str, profile: str, description: str | None, author: str
) -> ProjectValues:
    """Validate command input and derive language-safe identifiers."""
    project_name = _single_line("project name", name)
    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")

    project_slug = _slugify(project_name)
    if not project_slug:
        raise ValueError("project name must contain at least one ASCII letter or digit")

    project_symbol = project_slug.replace("-", "_")
    if project_symbol[0].isdigit():
        project_symbol = f"project_{project_symbol}"

    project_description = _single_line(
        "description", description or f"{project_name} project."
    )
    project_author = _single_line("author", author or "SmolBlackHole")

    return ProjectValues(
        project_name=project_name,
        project_slug=project_slug,
        project_symbol=project_symbol,
        python_package=project_symbol,
        description=project_description,
        author=project_author,
        year=str(datetime.now(UTC).year),
        profile=profile,
    )


def _substitute(value: str, tokens: dict[str, str]) -> str:
    for token, replacement in tokens.items():
        value = value.replace(token, replacement)
    return value


def _target_path(relative: Path, tokens: dict[str, str]) -> Path:
    parts = [_substitute(part, tokens) for part in relative.parts]
    if parts and parts[-1].endswith(TEMPLATE_SUFFIX):
        parts[-1] = parts[-1][: -len(TEMPLATE_SUFFIX)]
    return Path(*parts)


def _copy_template_tree(source: Path, destination: Path, values: ProjectValues) -> None:
    tokens = values.tokens()
    for source_path in sorted(source.rglob("*")):
        if not source_path.is_file():
            continue
        relative = source_path.relative_to(source)
        target = destination / _target_path(relative, tokens)
        target.parent.mkdir(parents=True, exist_ok=True)
        contents = source_path.read_text(encoding="utf-8")
        target.write_text(_substitute(contents, tokens), encoding="utf-8", newline="\n")


def _copy_shared_files(destination: Path) -> None:
    for filename in (
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        ".markdownlint.yml",
        "LICENSE",
    ):
        shutil.copyfile(ROOT / filename, destination / filename)
    shutil.copyfile(
        ROOT / "scripts" / "repository_checks.py",
        destination / "scripts" / "repository_checks.py",
    )


def _validate_generated_project(destination: Path) -> None:
    leftovers: list[str] = []
    for path in destination.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        try:
            contents = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if TOKEN_PATTERN.search(contents):
            leftovers.append(path.relative_to(destination).as_posix())
    if leftovers:
        formatted = ", ".join(sorted(leftovers))
        raise ValueError(f"unresolved template tokens in: {formatted}")

    source_editorconfig = (ROOT / ".editorconfig").read_bytes()
    generated_editorconfig = (destination / ".editorconfig").read_bytes()
    if generated_editorconfig != source_editorconfig:
        raise ValueError("generated .editorconfig is not a byte-for-byte copy")


def _initialize_git(destination: Path) -> None:
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required unless --no-git is passed")
    subprocess.run(
        (git, "init", "--initial-branch=main"),
        cwd=destination,
        check=True,
    )


def create_project(
    *, destination: Path, values: ProjectValues, initialize_git: bool
) -> Path:
    """Create one complete project without overwriting an existing path."""
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{values.project_slug}-", dir=destination.parent
    ) as temporary_directory:
        staging = Path(temporary_directory)
        _copy_template_tree(TEMPLATES / "base", staging, values)
        _copy_template_tree(TEMPLATES / "profiles" / values.profile, staging, values)
        _copy_shared_files(staging)
        _validate_generated_project(staging)
        if initialize_git:
            _initialize_git(staging)
        staging.replace(destination)

    return destination


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Human-readable project name.")
    parser.add_argument("--profile", required=True, choices=PROFILES)
    parser.add_argument("--destination", type=Path, help="New project directory.")
    parser.add_argument("--description", help="One-sentence project description.")
    parser.add_argument("--author", default="SmolBlackHole")
    parser.add_argument(
        "--no-git", action="store_true", help="Do not initialize a Git repository."
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
    )
    print(f"Created {values.profile} project at {created}")
    print(f"Next: {created / 'scripts' / 'setup.ps1'}")


if __name__ == "__main__":
    main()
