# Generator architecture

Parent: [Documentation index](README.md)

TemplateRepo combines repository policy, one or more runtime components and any
explicitly selected optional features, then atomically writes a new destination.

## Table of contents

- [Generator architecture](#generator-architecture)
  - [Table of contents](#table-of-contents)
  - [Generation flow](#generation-flow)
  - [Ownership](#ownership)
  - [Safety boundaries](#safety-boundaries)

## Generation flow

1. The interactive or argument-based Python entrypoint validates all input.
2. Repository templates under `templates/repository/` provide shared policy and
   documentation.
3. A template under `templates/layouts/` defines the repository boundary.
4. Component files under `templates/profiles/<profile>/component/` add runtime
   code and tooling. Single projects also receive that profile's repository
   integration.
5. Selected features add new files or append an owned documentation section.
   Existing feature targets are never silently replaced.
6. The generator rejects unresolved tokens and verifies every repository-root
   `.editorconfig` against the source bytes.
7. Git is initialized without a commit unless `--no-git` was selected.
8. The completed temporary directory is moved to the requested destination.

An existing destination is never overwritten.

## Ownership

| Concern | Owner |
| ------- | ----- |
| Interactive input | `scripts/new.py` |
| Shared generation primitives | `scripts/generation.py` |
| Single-project generation | `scripts/new_project.py` |
| Workspace generation | `scripts/new_workspace.py` |
| Repository-wide defaults | `templates/repository/` |
| Git and file layout | `templates/layouts/` |
| Runtime source and tooling | Profile `component/` directory |
| Single-project CI, docs and editor integration | Profile `repository/` directory |
| Optional local container precheck | `templates/features/local-ci/` |
| Regression coverage | `tests/` |

Profile-specific dependencies must not move into repository or layout templates
merely to reduce duplication.

Features are opt-in overlays. Common files live under `files/`, runtime-specific
files under `profiles/<profile>/`, and concise additions to an existing document
under `append/`. `scripts/add_feature.py` applies the same boundary to an
existing generated project.

## Safety boundaries

The generator creates only the requested new directory. It does not install
global tools, create commits, configure remotes or modify the source template.
A monorepo owns one root Git repository. A dual-repo owns exactly two child Git
repositories and no parent repository. Setup scripts operate only inside their
generated project or workspace.
