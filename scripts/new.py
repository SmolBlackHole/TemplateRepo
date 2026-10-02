# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Interactively create a project or workspace."""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from generation import FEATURES, PROFILES, ROOT, project_values
from new_project import create_project
from new_workspace import (
    COMPONENT_NAME,
    ComponentSpec,
    create_workspace,
    workspace_values,
)

Read = Callable[[str], str]
Write = Callable[[str], None]


def _ask(read: Read, prompt: str, *, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    value = read(f"{prompt}{suffix}: ").strip()
    return value or default or ""


def _required(
    read: Read, write: Write, prompt: str, *, default: str | None = None
) -> str:
    while True:
        value = _ask(read, prompt, default=default)
        if value:
            return value
        write("A value is required.")


def _choice(
    read: Read,
    write: Write,
    prompt: str,
    options: tuple[tuple[str, str], ...],
    *,
    default: str,
) -> str:
    while True:
        write(prompt)
        for key, label in options:
            write(f"  {key}. {label}")
        selected = _ask(read, "Selection", default=default)
        for key, _ in options:
            if selected == key:
                return key
        write("Choose one of the listed numbers.")


def _yes_no(read: Read, write: Write, prompt: str, *, default: bool) -> bool:
    label = "Y/n" if default else "y/N"
    while True:
        answer = read(f"{prompt} [{label}]: ").strip().casefold()
        if not answer:
            return default
        if answer in {"y", "yes", "j", "ja"}:
            return True
        if answer in {"n", "no", "nein"}:
            return False
        write("Answer yes or no.")


def _profile(read: Read, write: Write) -> str:
    options = tuple((str(index), profile) for index, profile in enumerate(PROFILES, 1))
    selected = _choice(read, write, "Runtime profile:", options, default="1")
    return options[int(selected) - 1][1]


def _component(
    read: Read,
    write: Write,
    *,
    default_name: str,
    existing: set[str],
) -> ComponentSpec:
    while True:
        name = _required(read, write, "Component name", default=default_name)
        if not COMPONENT_NAME.fullmatch(name):
            write("Use lowercase letters, digits and single hyphens only.")
            continue
        if name in existing:
            write("Component names must be unique.")
            continue
        return ComponentSpec(name=name, profile=_profile(read, write))


def _metadata(
    read: Read,
    write: Write,
    *,
    profile: str,
) -> tuple[str, str | None, str]:
    while True:
        name = _required(read, write, "Project name")
        description = _ask(read, "Description (optional)") or None
        author = _ask(read, "Author", default="SmolBlackHole")
        try:
            project_values(
                name=name,
                profile=profile,
                description=description,
                author=author,
            )
        except ValueError as error:
            write(f"Invalid metadata: {error}")
            continue
        return name, description, author


def run_interactive(
    *,
    read: Read = input,
    write: Write = print,
    default_parent: Path | None = None,
    initialize_git: bool = True,
) -> Path | None:
    """Collect input, show a summary and create the selected result."""
    write("TemplateRepo project generator")
    write("")
    layout_choice = _choice(
        read,
        write,
        "What do you want to create?",
        (
            ("1", "Single project"),
            ("2", "Monorepo (default)"),
            ("3", "Dual-repo"),
        ),
        default="2",
    )

    components: tuple[ComponentSpec, ...]
    if layout_choice == "1":
        profile = _profile(read, write)
        components = ()
    else:
        selected: list[ComponentSpec] = []
        names: set[str] = set()
        for default_name in ("frontend", "backend"):
            component = _component(
                read,
                write,
                default_name=default_name,
                existing=names,
            )
            selected.append(component)
            names.add(component.name)
        if layout_choice == "2":
            while _yes_no(read, write, "Add another component?", default=False):
                component = _component(
                    read,
                    write,
                    default_name=f"component-{len(selected) + 1}",
                    existing=names,
                )
                selected.append(component)
                names.add(component.name)
        components = tuple(selected)
        profile = components[0].profile

    name, description, author = _metadata(
        read,
        write,
        profile=profile,
    )
    features = tuple(
        feature
        for feature in FEATURES
        if _yes_no(read, write, f"Enable {feature}?", default=False)
    )

    if layout_choice == "1":
        values = project_values(
            name=name,
            profile=profile,
            description=description,
            author=author,
        )
        kind = "single project"
    else:
        layout = "monorepo" if layout_choice == "2" else "dual-repo"
        workspace = workspace_values(
            name=name,
            layout=layout,
            components=components,
            description=description,
            author=author,
            features=features,
        )
        values = workspace.project
        kind = layout

    parent = (default_parent or ROOT.parent).resolve()
    default_destination = parent / values.project_slug
    while True:
        destination = (
            Path(_ask(read, "Destination", default=str(default_destination)))
            .expanduser()
            .resolve()
        )
        if not destination.exists():
            break
        write(f"Destination already exists: {destination}")

    write("")
    write("Summary")
    write(f"  Type: {kind}")
    write(f"  Name: {name}")
    write(f"  Destination: {destination}")
    if layout_choice == "1":
        write(f"  Profile: {profile}")
        write("  Git repositories: 1")
    else:
        for component in components:
            write(f"  Component: {component.name} ({component.profile})")
        repository_count = 1 if layout_choice == "2" else 2
        write(f"  Git repositories: {repository_count}")
    write(f"  Features: {', '.join(features) if features else 'none'}")

    if not _yes_no(read, write, "Create now?", default=True):
        write("Cancelled. No files were created.")
        return None

    if layout_choice == "1":
        return create_project(
            destination=destination,
            values=values,
            initialize_git=initialize_git,
            features=features,
        )
    return create_workspace(
        destination=destination,
        values=workspace,
        initialize_git=initialize_git,
    )


def main() -> None:
    if not sys.stdin.isatty():
        raise SystemExit(
            "Interactive input requires a terminal. Use new_project.py or "
            "new_workspace.py for automation."
        )
    try:
        created = run_interactive()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled. No destination was completed.")
        raise SystemExit(130) from None
    if created is not None:
        print(f"Created at {created}")


if __name__ == "__main__":
    main()
