$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js/npm is required. Install Node.js LTS, then run this script again."
}

npm install

if ((Test-Path "android") -or (Test-Path "ios")) {
    npx cap sync
}

Write-Host ""
Write-Host "Mobile app dependencies are ready."
Write-Host "Android: run 'npm run android:add' once, then 'npm run open:android'."
Write-Host "iOS: on macOS, run 'npm run ios:add' once, then 'npm run open:ios'."
