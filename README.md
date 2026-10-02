# TemplateRepo

A small interactive generator for single projects, monorepos and two
independent sibling repositories. Every result starts with a shared
documentation foundation and focused Python, Node.js or C++ components.

The generator creates a new directory. It never rewrites this repository and
it copies `.editorconfig` byte for byte into the generated project.

## Create interactively

Python 3.11 or newer is required. PowerShell and POSIX shell files are only
entrypoints into Python.

```powershell
.\scripts\new.ps1
```

The wizard selects a single project, monorepo or dual-repo, collects runtime
profiles and optional features, then shows the complete result before writing.

## Create non-interactively

Single project:

PowerShell:

```powershell
.\scripts\new-project.ps1 `
    -Name "Example Project" `
    -Profile python `
    -Feature local-ci `
    -Destination D:\Projects\example-project
```

Linux or macOS:

```bash
sh scripts/new-project.sh \
    --name "Example Project" \
    --profile python \
    --feature local-ci \
    --destination ../example-project
```

Monorepo or dual-repo:

```powershell
.\scripts\new-workspace.ps1 `
    -Name "Example Platform" `
    -Layout monorepo `
    -Component frontend:node `
    -Component backend:python `
    -Feature local-ci `
    -Destination D:\Projects\example-platform
```

`monorepo` creates one Git repository with components below `apps/`.
`dual-repo` creates exactly two complete sibling projects, each with its own
Git repository. The grouping directory owns no additional files.

Available profiles:

| Profile  | Runtime foundation                         | Local quality command       |
| -------- | ------------------------------------------ | --------------------------- |
| `python` | `src/` package, pytest, Ruff, mypy, Pyright | `./scripts/check.*`          |
| `node`   | Dependency-free ESM and `node:test`        | `./scripts/check.*`          |
| `cpp`    | CMake, Ninja, C++20, library and test      | `./scripts/check.*`          |

Git initializes the result unless `--no-git` or `-NoGit` is passed to a
non-interactive generator.

`local-ci` is an optional feature. It adds a disposable Docker-based Linux
precheck without changing the profile's quality command. Omit `--feature` when
the project does not need container verification.

Add the same feature later to an existing generated project from the
TemplateRepo root:

```powershell
python scripts/add_feature.py `
    --destination D:\Projects\example-project `
    --profile python `
    --feature local-ci
```

The installer is idempotent for unchanged feature files and refuses to replace
project-owned files.

## Work on the generator

```powershell
.\scripts\setup.ps1
.\scripts\check.ps1
```

The setup command is intentionally idempotent. The generator has no third-party
runtime dependencies, so setup verifies the local prerequisites and runs the
repository checks.

To generate and exercise every profile and workspace layout in temporary
directories, run:

```powershell
python scripts/verify_profiles.py
python scripts/verify_workspaces.py
```

## Documentation

The [documentation index](docs/README.md) routes by task. Start with:

- [Architecture](docs/architecture.md) for template and profile ownership.
- [Development](docs/development.md) for commands and verification.
- [Writing and maintaining docs](docs/writing-and-maintaining-docs.md) before
  adding or moving documentation.
- [Roadmap](ROADMAP.md) for unfinished work.

## License

TemplateRepo and generated starter files are licensed under the
[Mozilla Public License 2.0](LICENSE).
