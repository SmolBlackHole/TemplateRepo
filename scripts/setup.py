# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

"""Verify TemplateRepo's dependency-free generator setup."""

from __future__ import annotations

from check import main as check


def main() -> None:
    print("TemplateRepo has no third-party runtime dependencies.")
    print("Verifying the generator and its templates...")
    check()


if __name__ == "__main__":
    main()
