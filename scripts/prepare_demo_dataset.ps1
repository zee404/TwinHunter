$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$sourceDir = Join-Path $projectRoot "demo_dataset\01 Originals"
New-Item -ItemType Directory -Force -Path $sourceDir | Out-Null

$headers = @{ "User-Agent" = "TwinHunter-demo-dataset/1.0" }
$downloads = @(
    @{
        Name = "01_mountain.jpg"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Mountain_landscape_(21827581301).jpg"
    },
    @{
        Name = "02_city.jpg"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Street_city.jpg"
    },
    @{
        Name = "03_beach.jpg"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Beach_image.jpg"
    }
)

foreach ($item in $downloads) {
    $destination = Join-Path $sourceDir $item.Name
    if (-not (Test-Path -LiteralPath $destination)) {
        Write-Host "Downloading $($item.Name)..."
        Invoke-WebRequest -Uri $item.Url -Headers $headers -OutFile $destination
    }
}

Push-Location $projectRoot
try {
    python "scripts\create_demo_variants.py"
}
finally {
    Pop-Location
}

Write-Host "Demo dataset ready: $projectRoot\demo_dataset"
