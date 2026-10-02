# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

& python (Join-Path $PSScriptRoot "new_project.py") @args
exit $LASTEXITCODE
