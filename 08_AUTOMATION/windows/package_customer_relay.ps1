param(
    [Parameter(Mandatory=$true)][string]$RelayFolder,
    [Parameter(Mandatory=$true)][string]$OutputZip
)

if (-not (Test-Path -LiteralPath $RelayFolder)) {
    throw "RelayFolder not found: $RelayFolder"
}

$temp = Join-Path ([System.IO.Path]::GetTempPath()) ("vcam_relay_package_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Force -Path $temp | Out-Null

try {
    Copy-Item -LiteralPath $RelayFolder -Destination $temp -Recurse -Force
    Get-ChildItem -LiteralPath $temp -Recurse -Force -File |
        Where-Object { $_.Name -in @('relaykey.bin','runtime.log','codex_relay_stdout.log','codex_relay_stderr.log') -or $_.Extension -eq '.log' } |
        Remove-Item -Force

    if (Test-Path -LiteralPath $OutputZip) {
        Remove-Item -LiteralPath $OutputZip -Force
    }
    Compress-Archive -LiteralPath (Join-Path $temp '*') -DestinationPath $OutputZip -Force
    Write-Host "Created $OutputZip"
} finally {
    Remove-Item -LiteralPath $temp -Recurse -Force
}

