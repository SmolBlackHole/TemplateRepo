# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

& python (Join-Path $PSScriptRoot "setup.py")
exit $LASTEXITCODE
