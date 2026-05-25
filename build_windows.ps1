$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppName = "COMPARE2SAVE"
$EntryPoint = Join-Path $ProjectRoot "desktop_launcher.py"
$ReleaseDir = Join-Path $ProjectRoot "release"
$ZipPath = Join-Path $ReleaseDir "$AppName-Windows.zip"

Set-Location $ProjectRoot

function Invoke-Checked {
    param([Parameter(Mandatory = $true)][string]$Command)

    Invoke-Expression $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

Invoke-Checked "python -m pip install -r requirements.txt"
Invoke-Checked "python -m pip install pyinstaller"

if (Test-Path "build") {
    Remove-Item "build" -Recurse -Force
}

if (Test-Path "dist") {
    Remove-Item "dist" -Recurse -Force
}

if (Test-Path "$AppName.spec") {
    Remove-Item "$AppName.spec" -Force
}

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name $AppName `
    --add-data "frontend;frontend" `
    --add-data "templates;templates" `
    --add-data "database.db;." `
    --add-data "backend;backend" `
    $EntryPoint

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null

if (Test-Path $ZipPath) {
    Remove-Item $ZipPath -Force
}

$DistPath = Join-Path $ProjectRoot "dist\$AppName\*"
$compressed = $false

for ($attempt = 1; $attempt -le 5; $attempt++) {
    try {
        Compress-Archive -Path $DistPath -DestinationPath $ZipPath -Force
        $compressed = $true
        break
    }
    catch {
        if ($attempt -eq 5) {
            throw
        }

        Start-Sleep -Seconds 2
    }
}

Write-Host ""
Write-Host "Windows downloadable app created:"
Write-Host $ZipPath
Write-Host ""
Write-Host "Share this zip. Users can extract it and run $AppName.exe."
