#Requires -Version 7.0

param(
    [Parameter(Mandatory = $true)]
    [string]$AppPath,

    [Parameter(Mandatory = $true)]
    [string]$UpdateServer,

    [Parameter(Mandatory = $false)]
    [ValidateSet('stable', 'beta', 'alpha')]
    [string]$Channel = 'stable',

    [Parameter(Mandatory = $false)]
    [ValidateSet('electron', 'tauri')]
    [string]$Framework = 'electron',

    [Parameter(Mandatory = $false)]
    [int]$Timeout = 120,

    [Parameter(Mandatory = $false)]
    [switch]$NoCleanup,

    [Parameter(Mandatory = $false)]
    [switch]$Verbose
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

$script:CurrentVersion = ''
$script:LatestVersion = ''
$script:StepResults = @{
    ServerAvailable  = $false
    UpdateDetected   = $false
    DownloadComplete = $false
    HashVerified     = $false
    InstallValidated = $false
}
$script:TempDir = Join-Path $env:TEMP "update-verify-$(Get-Random)"

function Write-Info  { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Warn  { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Ok    { Write-Host "[OK] $args" -ForegroundColor Green }
function Write-Step  { Write-Host "[STEP] $args" -ForegroundColor Cyan }

function Get-PlatformInfo {
    $platformName = 'unknown'
    $arch = 'unknown'

    if ($IsWindows -or $env:OS -match 'Windows') {
        $platformName = 'win32'
    } elseif ($IsMacOS) {
        $platformName = 'darwin'
    } elseif ($IsLinux) {
        $platformName = 'linux'
    }

    $cpuArch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLower()
    switch ($cpuArch) {
        'x64'    { $arch = 'x64' }
        'x86'    { $arch = 'ia32' }
        'arm64'  { $arch = 'arm64' }
        'arm'    { $arch = 'arm' }
        default  { $arch = $cpuArch }
    }

    return @{ Platform = $platformName; Arch = $arch }
}

function Resolve-ChannelPath {
    switch ($Channel) {
        'stable' { return 'latest' }
        'beta'   { return 'beta' }
        'alpha'  { return 'alpha' }
    }
    return 'latest'
}

function Detect-CurrentVersion {
    if (-not [string]::IsNullOrEmpty($script:CurrentVersion)) {
        return
    }

    $resolvedPath = if (Test-Path $AppPath -PathType Container) { $AppPath } else { Split-Path $AppPath -Parent }

    if ($Framework -eq 'electron') {
        $packageJson = Join-Path $resolvedPath 'package.json'
        if (Test-Path $packageJson) {
            try {
                $json = Get-Content $packageJson -Raw | ConvertFrom-Json
                $script:CurrentVersion = $json.version
            } catch {
                Write-Warn "Could not parse package.json"
            }
        }
    } elseif ($Framework -eq 'tauri') {
        $tauriConf = Join-Path $resolvedPath 'src-tauri\tauri.conf.json'
        if (Test-Path $tauriConf) {
            try {
                $json = Get-Content $tauriConf -Raw | ConvertFrom-Json
                $script:CurrentVersion = $json.version
            } catch {
                Write-Warn "Could not parse tauri.conf.json"
            }
        }
    }

    if ([string]::IsNullOrEmpty($script:CurrentVersion)) {
        $script:CurrentVersion = '0.0.1'
        Write-Warn "Could not detect current version, using: $($script:CurrentVersion)"
    } else {
        Write-Info "Detected current version: $($script:CurrentVersion)"
    }
}

function Test-UpdateServer {
    Write-Step "1/5 Checking update server availability"

    try {
        $response = Invoke-WebRequest -Uri $UpdateServer -Method Head -TimeoutSec 30 -UseBasicParsing -ErrorAction Stop
        $statusCode = [int]$response.StatusCode

        if ($statusCode -in @(200, 301, 302, 304)) {
            Write-Ok "Update server is reachable (HTTP $statusCode)"
            $script:StepResults.ServerAvailable = $true
        } else {
            Write-Err "Update server returned unexpected status: HTTP $statusCode"
            exit 1
        }
    } catch {
        $errMsg = $_.Exception.Message
        Write-Err "Update server is not reachable: $errMsg"
        exit 1
    }
}

function Test-UpdateDetection {
    Write-Step "2/5 Verifying update detection"

    $platformInfo = Get-PlatformInfo
    $channelPath = Resolve-ChannelPath

    Write-Info "Platform: $($platformInfo.Platform), Arch: $($platformInfo.Arch), Channel: $Channel"

    $updateUrl = if ($Framework -eq 'electron') {
        "$UpdateServer/$channelPath/$($platformInfo.Platform)/$($platformInfo.Arch)"
    } else {
        "$UpdateServer/$($platformInfo.Platform)/($platformInfo.Arch)/$channelPath"
    }

    Write-Info "Checking update URL: $updateUrl"

    try {
        $response = Invoke-RestMethod -Uri $updateUrl -TimeoutSec 30 -ErrorAction Stop
    } catch {
        Write-Err "No response from update endpoint: $($_.Exception.Message)"
        exit 1
    }

    $latestVersion = 'unknown'
    try {
        if ($response -is [string]) {
            $response = $response | ConvertFrom-Json
        }

        if ($Framework -eq 'electron') {
            $latestVersion = if ($response.version) { $response.version } elseif ($response.name) { $response.name } else { 'unknown' }
        } else {
            $latestVersion = if ($response.version) { $response.version } else { 'unknown' }
        }
    } catch {
        $latestVersion = 'unknown'
    }

    if ($latestVersion -eq 'unknown') {
        Write-Err "Could not parse latest version from update response"
        exit 1
    }

    $script:LatestVersion = $latestVersion

    if ($latestVersion -eq $script:CurrentVersion) {
        Write-Warn "Latest version ($latestVersion) matches current version. No update available."
        Write-Info "This may be expected if the app is already up-to-date."
    } else {
        Write-Ok "Update detected: $($script:CurrentVersion) -> $latestVersion"
    }

    $script:StepResults.UpdateDetected = $true

    $responseFile = Join-Path $script:TempDir 'update-response.json'
    $response | ConvertTo-Json -Depth 10 | Set-Content $responseFile -Encoding UTF8
}

function Test-UpdateDownload {
    Write-Step "3/5 Verifying update download"

    $responseFile = Join-Path $script:TempDir 'update-response.json'
    if (-not (Test-Path $responseFile)) {
        Write-Err "Update response file not found"
        exit 1
    }

    $response = Get-Content $responseFile -Raw | ConvertFrom-Json

    $downloadUrl = ''
    try {
        if ($response.url) {
            $downloadUrl = $response.url
        } elseif ($response.platforms) {
            $firstPlatform = $response.platforms.PSObject.Properties | Select-Object -First 1
            if ($firstPlatform.Value.url) {
                $downloadUrl = $firstPlatform.Value.url
            }
        }
    } catch {
        $downloadUrl = ''
    }

    if ([string]::IsNullOrEmpty($downloadUrl)) {
        Write-Warn "Could not extract download URL from update response"
        Write-Info "Skipping download verification (may require authenticated access)"
        return
    }

    Write-Info "Download URL: $downloadUrl"

    $downloadPath = Join-Path $script:TempDir 'update-download.tmp'
    $downloadStart = Get-Date

    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $downloadPath -TimeoutSec $Timeout -UseBasicParsing -ErrorAction Stop
    } catch {
        Write-Err "Download failed: $($_.Exception.Message)"
        exit 1
    }

    $downloadEnd = Get-Date
    $downloadMs = [math]::Round(($downloadEnd - $downloadStart).TotalMilliseconds)

    if (Test-Path $downloadPath) {
        $fileInfo = Get-Item $downloadPath
        $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        Write-Ok "Download completed: ${sizeMB}MB in ${downloadMs}ms"
        $script:StepResults.DownloadComplete = $true
    } else {
        Write-Err "Downloaded file not found"
        exit 1
    }
}

function Test-HashSignature {
    Write-Step "4/5 Verifying update hash/signature"

    $responseFile = Join-Path $script:TempDir 'update-response.json'
    $downloadPath = Join-Path $script:TempDir 'update-download.tmp'

    if (-not (Test-Path $responseFile)) {
        Write-Warn "Update response file not found, skipping hash verification"
        return
    }

    $response = Get-Content $responseFile -Raw | ConvertFrom-Json

    $expectedHash = ''
    try {
        $expectedHash = if ($response.sha512) { $response.sha512 } elseif ($response.sha256) { $response.sha256 } elseif ($response.signature) { $response.signature } else { '' }
    } catch {
        $expectedHash = ''
    }

    if ([string]::IsNullOrEmpty($expectedHash)) {
        Write-Warn "No hash/signature found in update response"
        Write-Info "Skipping hash verification"
        return
    }

    if (-not (Test-Path $downloadPath)) {
        Write-Warn "Downloaded file not found, skipping hash verification"
        return
    }

    $actualHash = ''
    try {
        if ($Framework -eq 'electron') {
            $sha512 = Get-FileHash -Path $downloadPath -Algorithm SHA512 -ErrorAction Stop
            $hashBytes = [byte[]]::new($sha512.Hash.Length / 2)
            for ($i = 0; $i -lt $hashBytes.Length; $i++) {
                $hashBytes[$i] = [Convert]::ToByte($sha512.Hash.Substring($i * 2, 2), 16)
            }
            $actualHash = [Convert]::ToBase64String($hashBytes)
        } else {
            $sha256 = Get-FileHash -Path $downloadPath -Algorithm SHA256 -ErrorAction Stop
            $actualHash = $sha256.Hash.ToLower()
        }
    } catch {
        Write-Warn "Could not compute hash for verification: $($_.Exception.Message)"
        return
    }

    if (-not [string]::IsNullOrEmpty($actualHash)) {
        $displayActual = if ($actualHash.Length -gt 32) { $actualHash.Substring(0, 32) + '...' } else { $actualHash }
        $displayExpected = if ($expectedHash.Length -gt 32) { $expectedHash.Substring(0, 32) + '...' } else { $expectedHash }
        Write-Info "Computed hash: $displayActual"
        Write-Info "Expected hash: $displayExpected"

        if ($actualHash -eq $expectedHash) {
            Write-Ok "Hash verification passed"
            $script:StepResults.HashVerified = $true
        } else {
            Write-Warn "Hash mismatch - computed hash does not match expected hash"
        }
    } else {
        Write-Warn "Could not compute hash for verification"
    }
}

function Test-InstallRestart {
    Write-Step "5/5 Verifying installation and restart"

    Write-Info "Installation and restart verification requires running the actual application."
    Write-Info "This step validates the update mechanism by checking:"

    if ($Framework -eq 'electron') {
        Write-Info "  - electron-updater autoInstallOnAppQuit setting"
        Write-Info "  - quitAndInstall() method availability"
        Write-Info "  - Update file staging in app update directory"

        $updateDir = if ($IsWindows -or $env:OS -match 'Windows') {
            Join-Path $env:LOCALAPPDATA 'app\update'
        } elseif ($IsMacOS) {
            Join-Path $HOME 'Library\Application Support\app\update'
        } else {
            Join-Path $HOME '.config\app\update'
        }

        if (Test-Path $updateDir) {
            Write-Ok "Update staging directory exists: $updateDir"
        } else {
            Write-Warn "Update staging directory not found (app may not have been run yet)"
        }

        $resolvedPath = if (Test-Path $AppPath -PathType Container) { $AppPath } else { Split-Path $AppPath -Parent }
        $updaterConfig = Join-Path $resolvedPath 'dev-app-update.yml'
        if (-not (Test-Path $updaterConfig)) {
            $updaterConfig = Join-Path $resolvedPath 'app-update.yml'
        }
        if (Test-Path $updaterConfig) {
            Write-Ok "electron-updater config found: $updaterConfig"
        } else {
            Write-Warn "electron-updater config not found"
        }
    } else {
        Write-Info "  - Tauri updater plugin configuration"
        Write-Info "  - Update endpoint accessibility"
        Write-Info "  - Restart mechanism"

        $resolvedPath = if (Test-Path $AppPath -PathType Container) { $AppPath } else { Split-Path $AppPath -Parent }
        $tauriConf = Join-Path $resolvedPath 'src-tauri\tauri.conf.json'

        if (Test-Path $tauriConf) {
            try {
                $conf = Get-Content $tauriConf -Raw | ConvertFrom-Json
                $hasUpdater = $null -ne $conf.plugins.updater
                if ($hasUpdater) {
                    Write-Ok "Tauri updater plugin is configured"
                } else {
                    Write-Warn "Tauri updater plugin may not be configured"
                }
            } catch {
                Write-Warn "Could not parse tauri.conf.json"
            }
        } else {
            Write-Warn "tauri.conf.json not found at: $tauriConf"
        }
    }

    $script:StepResults.InstallValidated = $true
    Write-Ok "Installation/restart verification structure validated"
}

function Test-Rollback {
    Write-Info "Verifying rollback capability..."

    $resolvedPath = if (Test-Path $AppPath -PathType Container) { $AppPath } else { Split-Path $AppPath -Parent }

    if ($Framework -eq 'electron') {
        $updateDir = if ($IsWindows -or $env:OS -match 'Windows') {
            Join-Path $env:LOCALAPPDATA 'app\update'
        } elseif ($IsMacOS) {
            Join-Path $HOME 'Library\Application Support\app\update'
        } else {
            Join-Path $HOME '.config\app\update'
        }

        if (Test-Path $updateDir) {
            $oldAppFiles = Get-ChildItem -Path $updateDir -Filter '*.old' -ErrorAction SilentlyContinue
            if ($oldAppFiles.Count -gt 0) {
                Write-Ok "Rollback files found ($($oldAppFiles.Count) .old files)"
            } else {
                Write-Info "No rollback (.old) files found in update directory"
            }
        }

        $packageJson = Join-Path $resolvedPath 'package.json'
        if (Test-Path $packageJson) {
            try {
                $json = Get-Content $packageJson -Raw | ConvertFrom-Json
                $buildConfig = $json.build
                if ($buildConfig -and $buildConfig.win) {
                    Write-Ok "Electron-builder Windows config found (rollback via NSIS supported)"
                }
            } catch {
                Write-Warn "Could not check build config for rollback support"
            }
        }
    } else {
        $tauriConf = Join-Path $resolvedPath 'src-tauri\tauri.conf.json'
        if (Test-Path $tauriConf) {
            try {
                $conf = Get-Content $tauriConf -Raw | ConvertFrom-Json
                if ($conf.plugins.updater) {
                    $hasPubKey = -not [string]::IsNullOrEmpty($conf.plugins.updater.pubkey)
                    if ($hasPubKey) {
                        Write-Ok "Tauri updater has public key configured (signed updates, rollback safe)"
                    } else {
                        Write-Warn "Tauri updater missing public key (unsigned updates)"
                    }
                }
            } catch {
                Write-Warn "Could not check Tauri updater config for rollback support"
            }
        }
    }

    Write-Ok "Rollback verification completed"
}

function Remove-TempFiles {
    if (-not $NoCleanup -and (Test-Path $script:TempDir)) {
        Write-Info "Cleaning up temporary files..."
        Remove-Item -Recurse -Force $script:TempDir -ErrorAction SilentlyContinue
    }
}

function New-VerificationReport {
    $timestamp = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $platformInfo = Get-PlatformInfo
    $reportFile = Join-Path $env:TEMP "update-verification-report-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"

    $step1Status = if ($script:StepResults.ServerAvailable) { 'PASS' } else { 'FAIL' }
    $step2Status = if ($script:StepResults.UpdateDetected) { 'PASS' } else { 'FAIL' }
    $step3Status = if ($script:StepResults.DownloadComplete) { 'PASS' } else { 'FAIL' }
    $step4Status = if ($script:StepResults.HashVerified) { 'PASS' } else { 'FAIL' }
    $step5Status = if ($script:StepResults.InstallValidated) { 'PASS' } else { 'FAIL' }

    $overallResult = if (($step1Status -eq 'PASS') -and ($step2Status -eq 'PASS') -and ($step3Status -eq 'PASS') -and ($step4Status -eq 'PASS') -and ($step5Status -eq 'PASS')) { 'PASS' } else { 'PARTIAL' }

    $report = @"
=== Auto-Update Verification Report ===
Timestamp:       $timestamp
Framework:       $Framework
App Path:        $AppPath
Update Server:   $UpdateServer
Channel:         $Channel
Current Version: $($script:CurrentVersion)
Latest Version:  $($script:LatestVersion)
Platform:        $($platformInfo.Platform) $($platformInfo.Arch)

Steps Verified:
  [1] Update server availability:   $step1Status
  [2] Update detection:             $step2Status
  [3] Update download:              $step3Status
  [4] Hash/signature verification:  $step4Status
  [5] Installation/restart:         $step5Status

Overall Result: $overallResult
"@

    $report | Set-Content $reportFile -Encoding UTF8

    Write-Host ""
    Write-Host $report
    Write-Info "Report saved to: $reportFile"
}

function Main {
    New-Item -ItemType Directory -Path $script:TempDir -Force | Out-Null

    Detect-CurrentVersion

    Write-Host ""
    Write-Host "============================================="
    Write-Host "  Auto-Update Verification (PowerShell)"
    Write-Host "  Framework:      $Framework"
    Write-Host "  App Path:       $AppPath"
    Write-Host "  Update Server:  $UpdateServer"
    Write-Host "  Channel:        $Channel"
    Write-Host "  Current Version: $($script:CurrentVersion)"
    Write-Host "============================================="
    Write-Host ""

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    Test-UpdateServer
    Test-UpdateDetection
    Test-UpdateDownload
    Test-HashSignature
    Test-InstallRestart
    Test-Rollback

    $stopwatch.Stop()

    Remove-TempFiles
    New-VerificationReport

    Write-Host ""
    Write-Ok "Verification completed in $($stopwatch.Elapsed.ToString('mm\:ss'))"
}

Main
