# TemplateRepo

A small project generator with a shared documentation foundation and focused
Python, Node.js and C++ profiles.

The generator creates a new directory. It never rewrites this repository and
it copies `.editorconfig` byte for byte into the generated project.

## Create a project

PowerShell:

```powershell
.\scripts\new-project.ps1 `
    -Name "Example Project" `
    -Profile python `
    -Destination D:\Projects\example-project
```

Linux or macOS:

```bash
./scripts/new-project.sh \
    --name "Example Project" \
    --profile python \
    --destination ../example-project
```

Available profiles:

| Profile  | Runtime foundation                         | Local quality command       |
| -------- | ------------------------------------------ | --------------------------- |
| `python` | `src/` package, pytest, Ruff, mypy, Pyright | `./scripts/check.*`          |
| `node`   | Dependency-free ESM and `node:test`        | `./scripts/check.*`          |
| `cpp`    | CMake, Ninja, C++20, library and test      | `./scripts/check.*`          |

Python 3.11 or newer is the only requirement for running the generator. Git is
used to initialize the result unless `--no-git` is passed.

## Work on the generator

```powershell
.\scripts\setup.ps1
.\scripts\check.ps1
```

The setup command is intentionally idempotent. The generator has no third-party
runtime dependencies, so setup verifies the local prerequisites and runs the
repository checks.

To generate and exercise every profile in temporary directories, run:

```powershell
python scripts/verify_profiles.py
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
