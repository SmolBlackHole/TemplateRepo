# Develop and verify TemplateRepo

Parent: [Documentation index](README.md)

Python 3.11 or newer and Git are the only generator prerequisites. PowerShell
and POSIX shell files only select the platform's Python executable and entrypoint.
Recommended VS Code extensions live in `.vscode/extensions.json`. Generated
projects receive only the common documentation helpers and extensions relevant
to their selected runtime profile.

## Table of contents

- [Develop and verify TemplateRepo](#develop-and-verify-templaterepo)
  - [Table of contents](#table-of-contents)
  - [Set up](#set-up)
  - [Run checks](#run-checks)
  - [Test one generated profile](#test-one-generated-profile)
  - [Verify workspace layouts](#verify-workspace-layouts)
  - [Verify an optional feature](#verify-an-optional-feature)
  - [Acceptance criteria](#acceptance-criteria)

## Set up

PowerShell:

```powershell
.\scripts\setup.ps1
```

POSIX shell:

```bash
sh scripts/setup.sh
```

The command is idempotent and does not install global dependencies.

## Run checks

```powershell
.\scripts\check.ps1
```

The check validates text files, local Markdown links, documentation reachability,
unresolved template tokens and generator tests for all profiles.

## Test one generated profile

Generate into a disposable directory, then run the setup and check scripts from
that project. Each profile documents the external tools it needs in its
generated `docs/development.md`.

The automated equivalent runs setup twice to prove idempotence, then verifies
one profile or all profiles:

```powershell
python scripts/verify_profiles.py --profile python
python scripts/verify_profiles.py
```

## Verify workspace layouts

Generate a three-component monorepo and a two-component dual-repo, run setup
twice and execute every native component check:

```powershell
python scripts/verify_workspaces.py
```

Use `--layout monorepo` or `--layout dual-repo` to select one layout.

## Verify an optional feature

Generate all profiles with the Docker-based Linux precheck included:

```powershell
python scripts/verify_profiles.py --feature local-ci
python scripts/verify_workspaces.py --feature local-ci
```

This verifies generation, setup and each profile's native checks. Generator
tests also cover adding the feature later, repeated installation and conflict
handling. Running the generated Docker images remains an explicit acceptance
step because it needs Docker Desktop or Docker Engine. Run every generated
container check with:

```powershell
python scripts/verify_workspaces.py --containers
```

## Acceptance criteria

- All three profiles generate without unresolved tokens.
- An existing destination is rejected without modification.
- Generated `.editorconfig` bytes equal the source file.
- Every generated Markdown page is reachable from its root README.
- Profile setup is idempotent.
- Profile checks build or execute the smallest meaningful smoke test.
- Optional features are absent by default and do not overwrite existing files.
- A monorepo contains one root `.git` and no nested repositories.
- A dual-repo contains two child repositories and no parent `.git`.
- Interactive cancellation leaves no destination behind.
