$ErrorActionPreference = 'Continue'
$src = "d:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill"
$dst = "d:\Projects\TraeProjects\skiller\.trae\skills\xuansto-skill-v2"

# Copy scripts directory
$srcScripts = Join-Path $src "scripts"
$dstScripts = Join-Path $dst "scripts"
New-Item -ItemType Directory -Path $dstScripts -Force | Out-Null

foreach ($f in Get-ChildItem $srcScripts -File) {
    if ($f.Extension -in '.py','.js','.ps1') {
        Copy-Item $f.FullName $dstScripts -Force
    }
}

foreach ($d in Get-ChildItem $srcScripts -Directory) {
    if ($d.Name -ne '__pycache__') {
        $dest = Join-Path $dstScripts $d.Name
        if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
        Copy-Item $d.FullName $dest -Recurse -Force
        Get-ChildItem $dest -Recurse -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force
        Get-ChildItem $dest -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
    }
}

# Copy memory directory
$memFiles = @("memory/patterns/testing/README.md", "memory/fixes/refactoring/README.md", "memory/fixes/README.md")
foreach ($rel in $memFiles) {
    $srcFile = Join-Path $src $rel
    $dstFile = Join-Path $dst $rel
    New-Item -ItemType Directory -Path (Split-Path $dstFile -Parent) -Force | Out-Null
    if (Test-Path $srcFile) {
        Copy-Item $srcFile $dstFile -Force
    } else {
        $dirName = (Split-Path $rel -Parent).Split('/')[-1]
        Set-Content -Path $dstFile -Value "# $dirName`n`nThis directory stores $dirName data.`n" -Encoding UTF8
    }
}

# Copy examples directory
$exDir = Join-Path $dst "examples"
New-Item -ItemType Directory -Path $exDir -Force | Out-Null
foreach ($name in @("desktop-app-development.md", "web-app-development.md")) {
    $srcFile = Join-Path $src "examples\$name"
    $dstFile = Join-Path $exDir $name
    if (Test-Path $srcFile) {
        Copy-Item $srcFile $dstFile -Force
    }
}

# Create migrations/.gitkeep
$gitkeep = Join-Path $dst "migrations\.gitkeep"
New-Item -ItemType Directory -Path (Split-Path $gitkeep -Parent) -Force | Out-Null
Set-Content -Path $gitkeep -Value "" -Encoding UTF8 -NoNewline

# Report
$scriptCount = (Get-ChildItem $dstScripts -Recurse -File).Count
Write-Host "Scripts copied: $scriptCount files"
Write-Host "Memory files: done"
Write-Host "Examples: done"
Write-Host "Migrations/.gitkeep: done"
