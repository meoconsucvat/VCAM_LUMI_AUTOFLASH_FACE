param(
    [string]$Root = ".",
    [string]$Output = "SHA256SUMS.txt"
)

$base = (Resolve-Path -LiteralPath $Root).Path
$outPath = Join-Path $base $Output

Get-ChildItem -LiteralPath $base -Recurse -File |
    Where-Object { $_.FullName -ne $outPath } |
    Sort-Object FullName |
    ForEach-Object {
        $hash = Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName
        $rel = $_.FullName.Substring($base.Length + 1)
        "$($hash.Hash.ToLower())  $rel"
    } | Set-Content -LiteralPath $outPath -Encoding UTF8

Write-Host "Wrote $outPath"

