# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Shared primitives for project and workspace generation."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
PROFILES = ("python", "node", "cpp")
FEATURES = ("local-ci",)
TEMPLATE_SUFFIX = ".template"
TOKEN_PATTERN = re.compile(r"{{[a-z0-9_]+}}")


class TemplateValues(Protocol):
    """Values that can render template paths and contents."""

    def tokens(self) -> dict[str, str]:
        """Return template tokens including their delimiters."""
        ...


def template_token(name: str) -> str:
    """Return one token in the template delimiter format."""
    return "{" * 2 + name + "}" * 2


def _string_literal(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)[1:-1]


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
        return {
            template_token("project_name"): self.project_name,
            template_token("project_name_string"): _string_literal(self.project_name),
            template_token("project_slug"): self.project_slug,
            template_token("project_symbol"): self.project_symbol,
            template_token("python_package"): self.python_package,
            template_token("description"): self.description,
            template_token("description_string"): _string_literal(self.description),
            template_token("author"): self.author,
            template_token("author_string"): _string_literal(self.author),
            template_token("year"): self.year,
            template_token("profile"): self.profile,
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


def substitute(value: str, tokens: dict[str, str]) -> str:
    """Replace every known template token in a string."""
    for token, replacement in tokens.items():
        value = value.replace(token, replacement)
    return value


def _target_path(relative: Path, tokens: dict[str, str]) -> Path:
    parts = [substitute(part, tokens) for part in relative.parts]
    if parts and parts[-1].endswith(TEMPLATE_SUFFIX):
        parts[-1] = parts[-1][: -len(TEMPLATE_SUFFIX)]
    return Path(*parts)


def copy_template_tree(source: Path, destination: Path, values: TemplateValues) -> None:
    """Render one template tree into a generated destination."""
    tokens = values.tokens()
    for source_path in sorted(source.rglob("*")):
        if not source_path.is_file():
            continue
        relative = source_path.relative_to(source)
        target = destination / _target_path(relative, tokens)
        target.parent.mkdir(parents=True, exist_ok=True)
        contents = source_path.read_text(encoding="utf-8")
        target.write_text(substitute(contents, tokens), encoding="utf-8", newline="\n")


def _selected_features(features: tuple[str, ...]) -> tuple[str, ...]:
    selected = tuple(dict.fromkeys(features))
    unsupported = tuple(feature for feature in selected if feature not in FEATURES)
    if unsupported:
        raise ValueError(f"unsupported feature: {unsupported[0]}")
    return selected


def _feature_files(
    *, feature: str, profile: str, tokens: dict[str, str]
) -> tuple[tuple[Path, str], ...]:
    changes: list[tuple[Path, str]] = []
    feature_root = TEMPLATES / "features" / feature
    for source_root in (
        feature_root / "files",
        feature_root / "profiles" / profile,
    ):
        if not source_root.is_dir():
            continue
        for source_path in sorted(source_root.rglob("*")):
            if not source_path.is_file():
                continue
            relative = _target_path(source_path.relative_to(source_root), tokens)
            contents = substitute(source_path.read_text(encoding="utf-8"), tokens)
            changes.append((relative, contents))
    return tuple(changes)


def _feature_appends(
    *, feature: str, tokens: dict[str, str]
) -> tuple[tuple[Path, str], ...]:
    append_root = TEMPLATES / "features" / feature / "append"
    if not append_root.is_dir():
        return ()
    changes: list[tuple[Path, str]] = []
    for source_path in sorted(append_root.rglob("*")):
        if not source_path.is_file():
            continue
        relative = _target_path(source_path.relative_to(append_root), tokens)
        contents = substitute(source_path.read_text(encoding="utf-8"), tokens)
        changes.append((relative, contents))
    return tuple(changes)


def install_features(
    *,
    destination: Path,
    profile: str,
    features: tuple[str, ...],
    tokens: dict[str, str] | None = None,
    include_appends: bool = True,
) -> None:
    """Add optional feature files without replacing project-owned content."""
    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    selected = _selected_features(features)
    if not selected:
        return

    destination = destination.expanduser().resolve()
    if not destination.is_dir():
        raise FileNotFoundError(f"project directory does not exist: {destination}")

    substitutions = tokens or {}
    writes: dict[Path, str] = {}
    for feature in selected:
        for relative, contents in _feature_files(
            feature=feature,
            profile=profile,
            tokens=substitutions,
        ):
            target = destination / relative
            if target.exists():
                current = target.read_text(encoding="utf-8")
                if current != contents:
                    raise FileExistsError(
                        f"feature {feature} would replace existing file: {relative}"
                    )
            else:
                writes[target] = contents

        appends = (
            _feature_appends(feature=feature, tokens=substitutions)
            if include_appends
            else ()
        )
        for relative, addition in appends:
            target = destination / relative
            if not target.is_file():
                raise FileNotFoundError(
                    f"feature {feature} cannot extend missing file: {relative}"
                )
            current = target.read_text(encoding="utf-8")
            normalized_addition = addition.strip() + "\n"
            heading = normalized_addition.partition("\n")[0]
            if normalized_addition in current:
                continue
            if heading in current:
                raise FileExistsError(
                    f"feature {feature} conflicts with existing section: {relative}"
                )
            writes[target] = current.rstrip() + "\n\n" + normalized_addition

    unresolved = tuple(
        path for path, contents in writes.items() if TOKEN_PATTERN.search(contents)
    )
    if unresolved:
        formatted = ", ".join(
            str(path.relative_to(destination)) for path in sorted(unresolved)
        )
        raise ValueError(f"unresolved feature tokens in: {formatted}")

    for target, contents in writes.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(contents, encoding="utf-8", newline="\n")


def copy_shared_files(destination: Path) -> None:
    """Copy repository-root files that must remain byte-identical."""
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


def validate_generated_project(destination: Path) -> None:
    """Reject unresolved tokens and changed protected root configuration."""
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


def initialize_git_repository(destination: Path) -> None:
    """Initialize an empty main-branch repository at the owned boundary."""
    git = shutil.which("git")
    if git is None:
        raise RuntimeError("git is required unless --no-git is passed")
    subprocess.run(
        (git, "init", "--initial-branch=main"),
        cwd=destination,
        check=True,
    )


@contextmanager
def staged_destination(destination: Path, slug: str) -> Iterator[tuple[Path, Path]]:
    """Provide a temporary sibling and publish it only after successful generation."""
    resolved = destination.expanduser().resolve()
    if resolved.exists():
        raise FileExistsError(f"destination already exists: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=f".{slug}-", dir=resolved.parent
    ) as temporary_directory:
        staging = Path(temporary_directory)
        yield resolved, staging
        staging.replace(resolved)
