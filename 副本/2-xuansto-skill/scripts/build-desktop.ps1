#Requires -Version 7.0

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('electron', 'tauri', 'flutter')]
    [string]$Framework,

    [Parameter(Mandatory = $false)]
    [ValidateSet('win', 'macos', 'linux', 'all')]
    [string]$Platform = 'all',

    [Parameter(Mandatory = $false)]
    [switch]$Sign,

    [Parameter(Mandatory = $false)]
    [switch]$Clean,

    [Parameter(Mandatory = $false)]
    [string]$EnvFile = '',

    [Parameter(Mandatory = $false)]
    [string]$OutputDir = 'release',

    [Parameter(Mandatory = $false)]
    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Resolve-Path (Join-Path $ScriptDir '..\..')

function Write-Info  { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Warn  { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Ok    { Write-Host "[OK] $args" -ForegroundColor Green }

function Load-Env {
    if ($EnvFile -and (Test-Path $EnvFile)) {
        Get-Content $EnvFile | ForEach-Object {
            if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
                $name = $Matches[1].Trim()
                $value = $Matches[2].Trim()
                Set-Item -Path "env:$name" -Value $value
            }
        }
        Write-Info "Loaded environment from: $EnvFile"
    }
    elseif ($EnvFile) {
        Write-Warn "Environment file not found: $EnvFile"
    }
}

function Check-Prerequisites {
    Write-Info "Checking prerequisites..."

    if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Err "Node.js is not installed."
        exit 1
    }
    Write-Ok "Node.js $(node --version)"

    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        Write-Err "npm is not installed."
        exit 1
    }
    Write-Ok "npm $(npm --version)"

    if ($Framework -eq 'tauri') {
        if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
            Write-Err "Rust/Cargo is not installed. Required for Tauri builds."
            exit 1
        }
        Write-Ok "Cargo $(cargo --version)"

        if (-not (Get-Command rustc -ErrorAction SilentlyContinue)) {
            Write-Err "Rust compiler is not installed."
            exit 1
        }
        Write-Ok "Rust $(rustc --version)"
    }

    if ($Framework -eq 'flutter') {
        $flutterCmd = Get-Command flutter -ErrorAction SilentlyContinue
        if (-not $flutterCmd) {
            Write-Err "Flutter SDK is not installed. Required for Flutter Desktop builds."
            exit 1
        }
        $flutterVer = & flutter --version 2>&1 | Select-Object -First 1
        Write-Ok "Flutter available: $flutterVer"
    }

    if ($Sign) {
        Check-SigningPrerequisites
    }

    Write-Ok "All prerequisites met"
}

function Check-SigningPrerequisites {
    Write-Info "Checking signing prerequisites for platform: $Platform"

    if ($Platform -in @('win', 'all')) {
        if (-not $env:WINDOWS_CERT_PASSWORD -and -not $env:CSC_KEY_PASSWORD) {
            Write-Warn "Windows signing certificate password not set (WINDOWS_CERT_PASSWORD or CSC_KEY_PASSWORD)"
        } else {
            Write-Ok "Windows signing credentials found"
        }
    }

    if ($Platform -in @('macos', 'all')) {
        Write-Warn "macOS signing requires running on macOS with Xcode"
    }

    if ($Platform -in @('linux', 'all')) {
        if (-not (Get-Command gpg -ErrorAction SilentlyContinue)) {
            Write-Warn "GPG not found. Required for Linux signing."
        } else {
            Write-Ok "GPG available"
        }
    }
}

function Clean-Build {
    if ($Clean) {
        Write-Info "Cleaning build artifacts..."
        $pathsToClean = @(
            (Join-Path $ProjectDir 'dist'),
            (Join-Path $ProjectDir $OutputDir)
        )
        if ($Framework -eq 'electron') {
            $pathsToClean += (Join-Path $ProjectDir 'node_modules' '.cache')
        }
        if ($Framework -eq 'tauri') {
            $pathsToClean += (Join-Path $ProjectDir 'src-tauri' 'target')
        }
        if ($Framework -eq 'flutter') {
            $pathsToClean += (Join-Path $ProjectDir 'build')
        }
        foreach ($p in $pathsToClean) {
            if (Test-Path $p) {
                Remove-Item -Recurse -Force $p
                Write-Info "  Removed: $p"
            }
        }
        Write-Ok "Build artifacts cleaned"
    }
}

function Install-Deps {
    Write-Info "Installing dependencies..."
    Push-Location $ProjectDir

    try {
        if (Test-Path 'package-lock.json') {
            npm ci
        } elseif (Test-Path 'yarn.lock') {
            yarn install --frozen-lockfile
        } elseif (Test-Path 'pnpm-lock.yaml') {
            pnpm install --frozen-lockfile
        } else {
            npm install
        }

        if ($Framework -eq 'tauri') {
            Write-Info "Installing Tauri CLI..."
            if (-not (Get-Command cargo-tauri -ErrorAction SilentlyContinue)) {
                cargo install tauri-cli
            }
        }

        if ($Framework -eq 'flutter') {
            Write-Info "Getting Flutter dependencies..."
            & flutter pub get
            if ($LASTEXITCODE -ne 0) {
                Write-Err "Flutter pub get failed"
                exit 1
            }
        }

        Write-Ok "Dependencies installed"
    } finally {
        Pop-Location
    }
}

function Build-Frontend {
    Write-Info "Building frontend..."
    Push-Location $ProjectDir

    try {
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Frontend build failed"
            exit 1
        }
        Write-Ok "Frontend built successfully"
    } finally {
        Pop-Location
    }
}

function Build-Electron {
    Write-Info "Building Electron application..."
    Push-Location $ProjectDir

    try {
        $builderArgs = @()

        switch ($Platform) {
            'win'   { $builderArgs += '--win' }
            'macos'   { $builderArgs += '--mac' }
            'linux' { $builderArgs += '--linux' }
            'all'   { }
        }

        $builderArgs += '--publish', 'never'

        if (-not $Sign) {
            $builderArgs += '-c.win.sign=false', '-c.mac.identity=null'
        }

        $builderArgs += '--output', $OutputDir

        if ($VerboseOutput) {
            $builderArgs += '--verbose'
        }

        & npx electron-builder @builderArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Electron build failed"
            exit 1
        }
        Write-Ok "Electron build completed"
    } finally {
        Pop-Location
    }
}

function Build-Tauri {
    Write-Info "Building Tauri application..."
    Push-Location $ProjectDir

    try {
        $tauriArgs = @('build')

        switch ($Platform) {
            'win'   { $tauriArgs += '--target', 'x86_64-pc-windows-msvc' }
            'macos'   { $tauriArgs += '--target', 'universal-apple-darwin' }
            'linux' { $tauriArgs += '--target', 'x86_64-unknown-linux-gnu' }
            'all'   { }
        }

        if ($VerboseOutput) {
            $tauriArgs += '--verbose'
        }

        & cargo tauri @tauriArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Tauri build failed"
            exit 1
        }
        Write-Ok "Tauri build completed"
    } finally {
        Pop-Location
    }
}

function Build-Flutter {
    Write-Info "Building Flutter Desktop application..."
    Push-Location $ProjectDir

    try {
        $flutterArgs = @('build')

        switch ($Platform) {
            'win'   { $flutterArgs += 'windows' }
            'macos'   { $flutterArgs += 'macos' }
            'linux' { $flutterArgs += 'linux' }
            'all'   { $flutterArgs += 'windows', 'macos', 'linux' }
        }

        if ($VerboseOutput) {
            $flutterArgs += '--verbose'
        }

        & flutter @flutterArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Flutter build failed"
            exit 1
        }
        Write-Ok "Flutter build completed"
    } finally {
        Pop-Location
    }
}

function Sign-Build {
    if ($Sign) {
        Write-Info "Signing build artifacts..."
        $signScript = Join-Path $ScriptDir 'sign-desktop.ps1'
        if (Test-Path $signScript) {
            & $signScript -Platform $Platform -BuildDir (Join-Path $ProjectDir $OutputDir)
            Write-Ok "Build artifacts signed"
        } else {
            Write-Warn "Signing script not found: $signScript"
        }
    }
}

function Verify-Build {
    Write-Info "Verifying build output..."
    $outputPath = Join-Path $ProjectDir $OutputDir

    if (-not (Test-Path $outputPath)) {
        Write-Err "Build output directory not found: $outputPath"
        exit 1
    }

    $artifacts = Get-ChildItem -Path $outputPath -Recurse -File -Include '*.exe', '*.msi', '*.dmg', '*.AppImage', '*.deb', '*.zip', '*.snap', '*.flatpak'
    if ($artifacts.Count -eq 0) {
        $allFiles = Get-ChildItem -Path $outputPath -Recurse -File
        if ($allFiles.Count -eq 0) {
            Write-Err "No build artifacts found in: $outputPath"
            exit 1
        }
    }

    Write-Info "Build artifacts:"
    $artifacts | ForEach-Object {
        $sizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Info "  $($_.Name) ($sizeMB MB)"
    }

    Write-Ok "Build verification passed"
}

function Main {
    Load-Env

    Write-Host ""
    Write-Host "============================================="
    Write-Host "  Desktop Build Script (PowerShell)"
    Write-Host "  Framework: $Framework"
    Write-Host "  Platform:  $Platform"
    Write-Host "  Sign:      $Sign"
    Write-Host "  Clean:     $Clean"
    Write-Host "============================================="
    Write-Host ""

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    Check-Prerequisites
    Clean-Build
    Install-Deps
    Build-Frontend

    switch ($Framework) {
        'electron' { Build-Electron }
        'tauri'    { Build-Tauri }
        'flutter'  { Build-Flutter }
    }

    Sign-Build
    Verify-Build

    $stopwatch.Stop()

    Write-Host ""
    Write-Host "============================================="
    Write-Ok "Build completed in $($stopwatch.Elapsed.ToString('mm\:ss'))"
    Write-Host "  Output: $(Join-Path $ProjectDir $OutputDir)"
    Write-Host "============================================="
}

Main
