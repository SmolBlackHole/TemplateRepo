# SPDX-FileCopyrightText: 2026 SmolBlackHole
#
# SPDX-License-Identifier: MPL-2.0

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $Name,

    [Parameter(Mandatory)]
    [ValidateSet("python", "node", "cpp")]
    [string] $Profile,

    [Parameter(Mandatory)]
    [string] $Destination,

    [string] $Description,
    [string] $Author = "SmolBlackHole",
    [switch] $NoGit
)

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonArguments = @()
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    $pythonArguments = @("-3")
}
if (-not $pythonCommand) {
    throw "Python 3.11 or newer is required."
}

$generator = Join-Path $PSScriptRoot "new_project.py"
$pythonArguments += @(
    $generator,
    "--name", $Name,
    "--profile", $Profile,
    "--destination", $Destination,
    "--author", $Author
)
if ($Description) {
    $pythonArguments += @("--description", $Description)
}
if ($NoGit) {
    $pythonArguments += "--no-git"
}

& $pythonCommand.Source @pythonArguments
exit $LASTEXITCODE
