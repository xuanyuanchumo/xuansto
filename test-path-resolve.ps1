$p = 'D:\Projects\TraeProjects\skiller\..\skiller-dev'
$result = Resolve-Path -Path $p -ErrorAction SilentlyContinue
Write-Host "Resolve-Path result type: $($result.GetType().Name)"
Write-Host "Resolve-Path result: '$result'"
Write-Host "GetFullPath: '$([System.IO.Path]::GetFullPath($p))'"
Write-Host ""

$p2 = 'D:\Projects\TraeProjects\skiller\..\skiller-nonexistent'
$result2 = Resolve-Path -Path $p2 -ErrorAction SilentlyContinue
Write-Host "Nonexistent - Resolve-Path result: '$result2'"
Write-Host "Nonexistent - GetFullPath: '$([System.IO.Path]::GetFullPath($p2))'"
