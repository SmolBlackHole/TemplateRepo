# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

Write-Host "TemplateRepo has no third-party runtime dependencies."
Write-Host "Verifying the generator and its templates..."
& (Join-Path $PSScriptRoot "check.ps1")
exit $LASTEXITCODE
