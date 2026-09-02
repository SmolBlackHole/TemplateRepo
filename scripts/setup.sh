#!/usr/bin/env sh
# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

set -eu

echo "TemplateRepo has no third-party runtime dependencies."
echo "Verifying the generator and its templates..."
script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec "$script_directory/check.sh"
