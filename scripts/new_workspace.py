# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Create a monorepo or two independent sibling repositories."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
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
    substitute,
    template_token,
    validate_generated_project,
)
from new_project import create_project

LAYOUTS = ("monorepo", "dual-repo")
COMPONENT_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
PROFILE_LABELS = {"python": "Python", "node": "Node.js", "cpp": "C++"}


@dataclass(frozen=True)
class ComponentSpec:
    """One named runtime component inside a generated workspace."""

    name: str
    profile: str


@dataclass(frozen=True)
class WorkspaceValues:
    """Validated workspace metadata and its selected components."""

    project: ProjectValues
    layout: str
    components: tuple[ComponentSpec, ...]
    features: tuple[str, ...]

    def tokens(self) -> dict[str, str]:
        tokens = self.project.tokens()
        tokens[template_token("profile")] = self.layout
        tokens[template_token("component_table")] = _component_table(self.components)
        tokens[template_token("components_toml")] = _components_toml(self.components)
        tokens[template_token("profile_links")] = _profile_links(self.components)
        tokens[template_token("runtime_setup_steps")] = _runtime_setup_steps(
            self.components
        )
        tokens[template_token("local_ci_docs")] = _local_ci_docs(
            self.components, self.features
        )
        return tokens


def parse_component(value: str) -> ComponentSpec:
    """Parse and validate a ``name:profile`` component declaration."""
    name, separator, profile = value.partition(":")
    if not separator or not name or not profile:
        raise ValueError("component must use the form <name>:<profile>")
    if not COMPONENT_NAME.fullmatch(name):
        raise ValueError(
            "component name must contain lowercase letters, digits and single hyphens"
        )
    if profile not in PROFILES:
        raise ValueError(f"unsupported profile: {profile}")
    return ComponentSpec(name=name, profile=profile)


def workspace_values(
    *,
    name: str,
    layout: str,
    components: tuple[ComponentSpec, ...],
    description: str | None,
    author: str,
    features: tuple[str, ...] = (),
) -> WorkspaceValues:
    """Validate workspace input and derive its repository metadata."""
    if layout not in LAYOUTS:
        raise ValueError(f"unsupported layout: {layout}")
    minimum = 2
    if len(components) < minimum:
        raise ValueError(f"{layout} requires at least {minimum} components")
    if layout == "dual-repo" and len(components) != 2:
        raise ValueError("dual-repo requires exactly two components")
    names = tuple(component.name for component in components)
    if len(set(names)) != len(names):
        raise ValueError("component names must be unique")
    unsupported = tuple(feature for feature in features if feature not in FEATURES)
    if unsupported:
        raise ValueError(f"unsupported feature: {unsupported[0]}")
    selected_features = tuple(dict.fromkeys(features))
    project = project_values(
        name=name,
        profile=components[0].profile,
        description=description or f"A {layout} workspace generated from TemplateRepo.",
        author=author,
    )
    return WorkspaceValues(
        project=project,
        layout=layout,
        components=components,
        features=selected_features,
    )


def _component_table(components: tuple[ComponentSpec, ...]) -> str:
    rows = [
        "| Component | Profile | Path |",
        "| --------- | ------- | ---- |",
    ]
    rows.extend(
        f"| `{component.name}` | [{PROFILE_LABELS[component.profile]}](docs/profiles/{component.profile}.md) | `apps/{component.name}/` |"
        for component in components
    )
    return "\n".join(rows)


def _components_toml(components: tuple[ComponentSpec, ...]) -> str:
    sections: list[str] = []
    for component in components:
        sections.extend(
            (
                "[[components]]",
                f'name = "{component.name}"',
                f'profile = "{component.profile}"',
                f'path = "apps/{component.name}"',
                "",
            )
        )
    return "\n".join(sections).rstrip()


def _profile_links(components: tuple[ComponentSpec, ...]) -> str:
    profiles = tuple(dict.fromkeys(component.profile for component in components))
    return "\n".join(
        f"- [{PROFILE_LABELS[profile]} profile](profiles/{profile}.md)"
        for profile in profiles
    )


def _runtime_setup_steps(components: tuple[ComponentSpec, ...]) -> str:
    profiles = {component.profile for component in components}
    steps: list[str] = []
    if "node" in profiles:
        steps.extend(
            (
                "            - name: Set up Node.js",
                "              uses: actions/setup-node@v6",
                "              with:",
                '                  node-version: "22"',
            )
        )
    return "\n".join(steps)


def _local_ci_docs(
    components: tuple[ComponentSpec, ...], features: tuple[str, ...]
) -> str:
    if "local-ci" not in features:
        return ""
    commands = "\n".join(
        f"python apps/{component.name}/scripts/check_container.py"
        for component in components
    )
    return f"""
## Run the Linux CI precheck

Each component owns a disposable Docker-based Linux check:

```powershell
{commands}
```

Docker Desktop or Docker Engine must be running. Images remain available for
the next build cache; containers are removed after each run.
""".strip()


def _component_values(
    workspace: WorkspaceValues, component: ComponentSpec
) -> ProjectValues:
    return project_values(
        name=f"{workspace.project.project_name} {component.name.replace('-', ' ').title()}",
        profile=component.profile,
        description=(
            f"The {component.name} component of {workspace.project.project_name}."
        ),
        author=workspace.project.author,
    )


def _write_profile_docs(staging: Path, workspace: WorkspaceValues) -> None:
    profile_root = staging / "docs" / "profiles"
    profile_root.mkdir(parents=True, exist_ok=True)
    for profile in dict.fromkeys(
        component.profile for component in workspace.components
    ):
        source = (
            TEMPLATES
            / "profiles"
            / profile
            / "repository"
            / "docs"
            / "profile.md.template"
        )
        contents = substitute(source.read_text(encoding="utf-8"), workspace.tokens())
        contents = contents.replace(
            "Parent: [Documentation index](README.md)",
            "Parent: [Documentation index](../README.md)",
        )
        (profile_root / f"{profile}.md").write_text(
            contents, encoding="utf-8", newline="\n"
        )


def _write_extensions(staging: Path, workspace: WorkspaceValues) -> None:
    recommendations: set[str] = set()
    for profile in dict.fromkeys(
        component.profile for component in workspace.components
    ):
        source = (
            TEMPLATES
            / "profiles"
            / profile
            / "repository"
            / ".vscode"
            / "extensions.json.template"
        )
        parsed = json.loads(source.read_text(encoding="utf-8"))
        recommendations.update(parsed["recommendations"])
    target = staging / ".vscode" / "extensions.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(
            {"recommendations": sorted(recommendations, key=str.casefold)},
            indent=4,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _create_monorepo(
    *, staging: Path, workspace: WorkspaceValues, initialize_git: bool
) -> None:
    copy_template_tree(TEMPLATES / "repository", staging, workspace)
    copy_template_tree(TEMPLATES / "layouts" / "monorepo", staging, workspace)
    copy_shared_files(staging)
    for component in workspace.components:
        values = _component_values(workspace, component)
        component_root = staging / "apps" / component.name
        copy_template_tree(
            TEMPLATES / "profiles" / component.profile / "component",
            component_root,
            values,
        )
        install_features(
            destination=component_root,
            profile=component.profile,
            features=workspace.features,
            tokens=values.tokens(),
            include_appends=False,
        )
    _write_profile_docs(staging, workspace)
    _write_extensions(staging, workspace)
    validate_generated_project(staging)
    if initialize_git:
        initialize_git_repository(staging)


def _create_dual_repo(
    *, staging: Path, workspace: WorkspaceValues, initialize_git: bool
) -> None:
    for component in workspace.components:
        create_project(
            destination=staging / component.name,
            values=_component_values(workspace, component),
            initialize_git=initialize_git,
            features=workspace.features,
        )


def create_workspace(
    *, destination: Path, values: WorkspaceValues, initialize_git: bool
) -> Path:
    """Create a complete workspace without overwriting an existing path."""
    with staged_destination(destination, values.project.project_slug) as (
        destination,
        staging,
    ):
        if values.layout == "monorepo":
            _create_monorepo(
                staging=staging,
                workspace=values,
                initialize_git=initialize_git,
            )
        else:
            _create_dual_repo(
                staging=staging,
                workspace=values,
                initialize_git=initialize_git,
            )
    return destination


def _component_argument(value: str) -> ComponentSpec:
    try:
        return parse_component(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", "-Name", required=True)
    parser.add_argument("--layout", "-Layout", required=True, choices=LAYOUTS)
    parser.add_argument(
        "--component",
        "-Component",
        action="append",
        required=True,
        type=_component_argument,
        help="Component in the form <name>:<profile>. Repeat for each component.",
    )
    parser.add_argument("--destination", "-Destination", type=Path)
    parser.add_argument("--description", "-Description")
    parser.add_argument("--author", "-Author", default="SmolBlackHole")
    parser.add_argument(
        "--feature",
        "-Feature",
        action="append",
        choices=FEATURES,
        default=[],
    )
    parser.add_argument("--no-git", "-NoGit", action="store_true")
    return parser


def main() -> None:
    args = _parser().parse_args()
    values = workspace_values(
        name=args.name,
        layout=args.layout,
        components=tuple(args.component),
        description=args.description,
        author=args.author,
        features=tuple(args.feature),
    )
    destination = args.destination or ROOT.parent / values.project.project_slug
    created = create_workspace(
        destination=destination,
        values=values,
        initialize_git=not args.no_git,
    )
    print(f"Created {values.layout} workspace at {created}")
    if values.layout == "monorepo":
        print(f"Next: {created / 'scripts' / 'setup.ps1'}")


if __name__ == "__main__":
    main()
