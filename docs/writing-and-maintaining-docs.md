# Writing and maintaining documentation

Parent: [Documentation index](README.md)

Give every fact one authoritative owner. Link to that owner instead of copying
the same explanation into multiple pages.

## Table of contents

- [Writing and maintaining documentation](#writing-and-maintaining-documentation)
  - [Table of contents](#table-of-contents)
  - [Choose the owner](#choose-the-owner)
  - [Structure docs as a small book](#structure-docs-as-a-small-book)
  - [Describe the present](#describe-the-present)
  - [Add or move a page](#add-or-move-a-page)
  - [Review checklist](#review-checklist)

## Choose the owner

| Content                                    | Owner                  |
| ------------------------------------------ | ---------------------- |
| Purpose, profile summary and first command | Root `README.md`       |
| Documentation navigation                   | `docs/README.md`       |
| Generator and profile boundaries           | `docs/architecture.md` |
| Setup, checks and acceptance               | `docs/development.md`  |
| Unfinished work and delivery order         | `ROADMAP.md`           |
| Contribution expectations                  | `CONTRIBUTING.md`      |
| Vulnerability reporting                    | `SECURITY.md`          |

If a paragraph contains facts owned by two rows, split it and link between the
owners.

## Structure docs as a small book

The root README is the cover and shortest entry point. `docs/README.md` is the
index. Every page below it starts with a `Parent:` link to its nearest index.
Pages with multiple main sections include a linked table of contents.

Link upward for navigation and sideways only to the authority that answers the
reader's next question.

## Describe the present

Unmarked prose describes implemented behavior. Put unfinished behavior in
`ROADMAP.md`; do not make a future idea look like a current feature.

## Add or move a page

1. Decide which fact the page owns.
2. Add its `Parent:` link and table of contents.
3. Link it from the nearest index.
4. Replace duplicated prose with links.
5. Run the repository check.

## Review checklist

- The page answers one reader question.
- No other page claims authority for the same fact.
- Parent and local links resolve.
- The page is reachable from the root README.
- Future work stays in the roadmap.
