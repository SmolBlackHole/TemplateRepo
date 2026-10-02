#!/usr/bin/env sh
# SPDX-License-Identifier: MPL-2.0

set -eu

script_directory=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$script_directory/check_container.py"
