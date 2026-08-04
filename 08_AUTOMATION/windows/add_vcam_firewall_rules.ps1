param(
    [string]$RelayPath = "C:\VcamPlusRelay\relay.exe",
    [int]$Port = 1935
)

Write-Host "== Add VCAM Firewall Rules =="
Write-Host "RelayPath: $RelayPath"
Write-Host "Port: $Port"

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "Please run PowerShell as Administrator."
    exit 1
}

if (-not (Test-Path -LiteralPath $RelayPath)) {
    Write-Warning "Relay path does not exist yet: $RelayPath"
    Write-Warning "Create the port rule now; add program rule after relay.exe is placed there."
}

$portRule = Get-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -ErrorAction SilentlyContinue
if (-not $portRule) {
    New-NetFirewallRule -DisplayName "VCAM RTMP 1935 TCP" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -Profile Any | Out-Null
    Write-Host "Created port rule."
} else {
    Write-Host "Port rule already exists."
}

if (Test-Path -LiteralPath $RelayPath) {
    $programRule = Get-NetFirewallRule -DisplayName "VCAM Relay Program" -ErrorAction SilentlyContinue
    if ($programRule) {
        Remove-NetFirewallRule -DisplayName "VCAM Relay Program"
    }
    New-NetFirewallRule -DisplayName "VCAM Relay Program" -Direction Inbound -Action Allow -Program $RelayPath -Profile Any | Out-Null
    Write-Host "Created/updated program rule."
}

Write-Host "Done."

