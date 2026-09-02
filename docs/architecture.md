# Generator architecture

Parent: [Documentation index](README.md)

TemplateRepo combines one shared base with exactly one runtime profile and
writes the result to a new directory.

## Table of contents

- [Generator architecture](#generator-architecture)
  - [Table of contents](#table-of-contents)
  - [Generation flow](#generation-flow)
  - [Ownership](#ownership)
  - [Safety boundaries](#safety-boundaries)

## Generation flow

1. `scripts/new_project.py` validates the project name, profile and destination.
2. Files under `templates/base/` are rendered into a temporary directory.
3. Files under `templates/profiles/<profile>/` are added.
4. Shared repository files are copied without template substitution.
5. The generator rejects unresolved tokens and verifies that `.editorconfig`
   is byte-for-byte identical to the source.
6. Git is initialized without a commit unless `--no-git` was selected.
7. The completed temporary directory is moved to the requested destination.

An existing destination is never overwritten.

## Ownership

| Concern                                    | Owner                        |
| ------------------------------------------ | ---------------------------- |
| Input validation and safe output creation  | `scripts/new_project.py`     |
| Documentation and repository-wide defaults | `templates/base/`            |
| Python setup, source and quality tools     | `templates/profiles/python/` |
| Node.js setup, source and quality tools    | `templates/profiles/node/`   |
| CMake/C++ setup, source and quality tools  | `templates/profiles/cpp/`    |
| VS Code recommendations for one runtime    | Selected profile `.vscode/`  |
| Generator regression coverage              | `tests/test_new_project.py`  |

Profile-specific dependencies must not move into the shared base merely to
reduce duplication.

## Safety boundaries

The generator creates only the requested new directory. It does not install
global tools, create commits, configure remotes or modify the source template.
Setup scripts operate only inside their generated project.
