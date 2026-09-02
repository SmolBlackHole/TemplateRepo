# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        & $pythonCommand.Source -3 (Join-Path $PSScriptRoot "check.py")
        exit $LASTEXITCODE
    }
}
if (-not $pythonCommand) {
    throw "Python 3.11 or newer is required."
}

& $pythonCommand.Source (Join-Path $PSScriptRoot "check.py")
exit $LASTEXITCODE
