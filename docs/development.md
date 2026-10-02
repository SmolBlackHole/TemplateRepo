# Develop and verify TemplateRepo

Parent: [Documentation index](README.md)

Python 3.11 or newer and Git are the only generator prerequisites.
Recommended VS Code extensions live in `.vscode/extensions.json`. Generated
projects receive only the common documentation helpers and extensions relevant
to their selected runtime profile.

## Table of contents

- [Develop and verify TemplateRepo](#develop-and-verify-templaterepo)
  - [Table of contents](#table-of-contents)
  - [Set up](#set-up)
  - [Run checks](#run-checks)
  - [Test one generated profile](#test-one-generated-profile)
  - [Verify an optional feature](#verify-an-optional-feature)
  - [Acceptance criteria](#acceptance-criteria)

## Set up

PowerShell:

```powershell
.\scripts\setup.ps1
```

POSIX shell:

```bash
./scripts/setup.sh
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

## Verify an optional feature

Generate all profiles with the Docker-based Linux precheck included:

```powershell
python scripts/verify_profiles.py --feature local-ci
```

This verifies generation, setup and each profile's native checks. Generator
tests also cover adding the feature later, repeated installation and conflict
handling. Running the generated Docker images remains an explicit acceptance
step because it needs Docker Desktop or Docker Engine.

## Acceptance criteria

- All three profiles generate without unresolved tokens.
- An existing destination is rejected without modification.
- Generated `.editorconfig` bytes equal the source file.
- Every generated Markdown page is reachable from its root README.
- Profile setup is idempotent.
- Profile checks build or execute the smallest meaningful smoke test.
- Optional features are absent by default and do not overwrite existing files.
