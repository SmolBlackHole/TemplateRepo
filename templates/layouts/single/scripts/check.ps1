# SPDX-FileCopyrightText: {{year}} {{author}}
#
# SPDX-License-Identifier: MPL-2.0

& python (Join-Path $PSScriptRoot "project.py") check
exit $LASTEXITCODE
