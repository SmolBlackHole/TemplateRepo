# SPDX-License-Identifier: MPL-2.0

& python (Join-Path $PSScriptRoot "check_container.py")
exit $LASTEXITCODE
