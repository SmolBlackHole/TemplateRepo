# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Install an optional TemplateRepo feature into an existing project."""

from __future__ import annotations

import argparse
from pathlib import Path

from generation import FEATURES, PROFILES, install_features


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=PROFILES)
    parser.add_argument(
        "--feature",
        action="append",
        required=True,
        choices=FEATURES,
        help="Feature to install. Repeat to select multiple features.",
    )
    args = parser.parse_args()
    destination = args.destination.expanduser().resolve()
    install_features(
        destination=destination,
        profile=args.profile,
        features=tuple(args.feature),
    )
    print(f"Installed {', '.join(dict.fromkeys(args.feature))} in {destination}")


if __name__ == "__main__":
    main()
