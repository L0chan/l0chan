$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$MobileRoot = Join-Path $ProjectRoot "mobile_app"

if (-not (Test-Path $MobileRoot)) {
    throw "mobile_app folder was not found."
}

Set-Location $MobileRoot
& .\build_mobile.ps1
