# Contributing to TemplateRepo

Parent: [Project README](README.md)

Keep the shared base small. A rule belongs in the base only when every generated
project needs it. Runtime-specific files belong to exactly one profile.

## Set up the repository

Use [the development guide](docs/development.md) for the supported commands.

## Change a profile

Update the profile under `templates/profiles/<profile>/`, add or adjust focused
generator tests, and run the complete repository check. Do not solve a profile
problem by adding its dependencies to the shared base.

## Change documentation

Read [Writing and maintaining documentation](docs/writing-and-maintaining-docs.md)
before adding or moving a page. Every public Markdown page must be reachable
from the root README.

## Pull requests

Describe the generated behavior that changed, the profiles affected, the checks
that passed and any platform verification that was skipped.
