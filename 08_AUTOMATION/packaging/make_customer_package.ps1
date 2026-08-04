param(
    [Parameter(Mandatory=$true)][string]$DebPath,
    [Parameter(Mandatory=$true)][string]$RelayZipPath,
    [Parameter(Mandatory=$true)][string]$ReadmePath,
    [Parameter(Mandatory=$true)][string]$OutputDir
)

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

Copy-Item -LiteralPath $DebPath -Destination $OutputDir -Force
Copy-Item -LiteralPath $RelayZipPath -Destination $OutputDir -Force
Copy-Item -LiteralPath $ReadmePath -Destination (Join-Path $OutputDir "README.md") -Force

& "$PSScriptRoot\make_sha256sums.ps1" -Root $OutputDir -Output "SHA256SUMS.txt"

Write-Host "Customer package ready: $OutputDir"

