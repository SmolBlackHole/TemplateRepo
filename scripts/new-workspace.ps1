# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

& python (Join-Path $PSScriptRoot "new_workspace.py") @args
exit $LASTEXITCODE
