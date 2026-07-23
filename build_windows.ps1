$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name TwinHunter `
    --icon "assets\icon.png" `
    --add-data "assets;assets" `
    main.py

Write-Host "Built: $projectRoot\dist\TwinHunter.exe"
