#Requires -Version 7.0

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('win', 'macos', 'linux', 'all')]
    [string]$Platform,

    [Parameter(Mandatory = $false)]
    [string]$CertPath = '',

    [Parameter(Mandatory = $false)]
    [System.Security.SecureString]$CertPassword,

    [Parameter(Mandatory = $false)]
    [string]$TimestampServer = 'http://timestamp.digicert.com',

    [Parameter(Mandatory = $false)]
    [switch]$Notarize,

    [Parameter(Mandatory = $false)]
    [string]$AppPath = '',

    [Parameter(Mandatory = $false)]
    [string]$Keychain = '',

    [Parameter(Mandatory = $false)]
    [string]$KeychainPassword = '',

    [Parameter(Mandatory = $false)]
    [string]$GpgKey = '',

    [Parameter(Mandatory = $false)]
    [string]$GpgPassphrase = '',

    [Parameter(Mandatory = $false)]
    [string]$AppleId = '',

    [Parameter(Mandatory = $false)]
    [string]$AppleIdPassword = '',

    [Parameter(Mandatory = $false)]
    [string]$TeamId = '',

    [Parameter(Mandatory = $false)]
    [string]$SignIdentity = '',

    [Parameter(Mandatory = $false)]
    [switch]$VerboseOutput
)

$ErrorActionPreference = 'Stop'
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Info  { Write-Host "[INFO] $args" -ForegroundColor Blue }
function Write-Warn  { Write-Host "[WARN] $args" -ForegroundColor Yellow }
function Write-Err   { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Ok    { Write-Host "[OK] $args" -ForegroundColor Green }

function Resolve-CertPassword {
    if ($CertPassword) {
        $ptr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($CertPassword)
        try {
            return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
        } finally {
            [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
        }
    }
    if ($env:CERT_PASSWORD) { return $env:CERT_PASSWORD }
    if ($env:CSC_KEY_PASSWORD) { return $env:CSC_KEY_PASSWORD }
    return ''
}

function Resolve-BuildDir {
    if ($AppPath -and (Test-Path $AppPath)) {
        return (Resolve-Path $AppPath).Path
    }
    $defaultDir = Join-Path $ScriptDir '..\..\release'
    if (Test-Path $defaultDir) {
        return (Resolve-Path $defaultDir).Path
    }
    Write-Err "Build directory not found: $defaultDir"
    Write-Err "Specify -AppPath or ensure release/ directory exists"
    exit 1
}

function Find-SignTool {
    $signToolPaths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x86\signtool.exe"
    )

    foreach ($pattern in $signToolPaths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue |
            Sort-Object Name -Descending |
            Select-Object -First 1
        if ($found) {
            return $found.FullName
        }
    }

    $signtool = Get-Command signtool.exe -ErrorAction SilentlyContinue
    if ($signtool) { return $signtool.Source }

    return ''
}

function Sign-WindowsArtifacts {
    Write-Info "Signing Windows artifacts..."

    $certPwd = Resolve-CertPassword
    if ([string]::IsNullOrEmpty($certPwd)) {
        Write-Err "Certificate password not provided. Use -CertPassword or set CERT_PASSWORD / CSC_KEY_PASSWORD env var."
        exit 1
    }

    if ($CertPath -and -not (Test-Path $CertPath)) {
        Write-Err "Certificate file not found: $CertPath"
        exit 1
    }

    $buildDir = Resolve-BuildDir

    $signToolPath = Find-SignTool
    $useOssl = $false

    if ([string]::IsNullOrEmpty($signToolPath)) {
        $ossl = Get-Command osslsigncode -ErrorAction SilentlyContinue
        if ($ossl) {
            $useOssl = $true
            Write-Info "Using osslsigncode for signing"
        } else {
            Write-Err "No signing tool found. Install signtool.exe (Windows SDK) or osslsigncode."
            exit 1
        }
    } else {
        Write-Info "Using signtool: $signToolPath"
    }

    $exeFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.exe' -File -ErrorAction SilentlyContinue
    $msiFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.msi' -File -ErrorAction SilentlyContinue
    $allFiles = @($exeFiles) + @($msiFiles)

    if ($allFiles.Count -eq 0) {
        Write-Warn "No Windows artifacts (.exe/.msi) found to sign"
        return
    }

    foreach ($file in $allFiles) {
        Write-Info "Signing: $($file.Name)"

        if ($useOssl) {
            $signedFile = "$($file.FullName).signed"
            & osslsigncode sign `
                -pkcs12 $CertPath `
                -pass $certPwd `
                -t $TimestampServer `
                -sha256 `
                -in $file.FullName `
                -out $signedFile
            if ($LASTEXITCODE -ne 0) {
                Write-Err "Failed to sign: $($file.Name)"
                exit 1
            }
            Move-Item -Force $signedFile $file.FullName
        } else {
            & $signToolPath sign `
                /f $CertPath `
                /p $certPwd `
                /tr $TimestampServer `
                /td sha256 `
                /fd sha256 `
                $file.FullName
            if ($LASTEXITCODE -ne 0) {
                Write-Err "Failed to sign: $($file.Name)"
                exit 1
            }
        }

        Write-Ok "Signed: $($file.Name)"
    }

    Verify-WindowsSignatures -BuildDir $buildDir -SignToolPath $signToolPath
}

function Verify-WindowsSignatures {
    param(
        [string]$BuildDir,
        [string]$SignToolPath
    )

    Write-Info "Verifying Windows signatures..."

    $exeFiles = Get-ChildItem -Path $BuildDir -Recurse -Filter '*.exe' -File -ErrorAction SilentlyContinue
    $msiFiles = Get-ChildItem -Path $BuildDir -Recurse -Filter '*.msi' -File -ErrorAction SilentlyContinue
    $allFiles = @($exeFiles) + @($msiFiles)

    foreach ($file in $allFiles) {
        if (-not [string]::IsNullOrEmpty($SignToolPath)) {
            & $SignToolPath verify /pa /all $file.FullName 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Signature verified: $($file.Name)"
            } else {
                Write-Warn "Signature verification issue: $($file.Name)"
            }
        } else {
            try {
                $sig = Get-AuthenticodeSignature -FilePath $file.FullName
                if ($sig.Status -eq 'Valid') {
                    Write-Ok "Signature verified: $($file.Name)"
                } else {
                    Write-Warn "Signature status '$($sig.Status)' for: $($file.Name)"
                }
            } catch {
                Write-Warn "Could not verify signature for: $($file.Name)"
            }
        }
    }
}

function Sign-MacOSArtifacts {
    Write-Info "Signing macOS artifacts..."

    $isMacOS = $IsMacOS -or ($env:OS -eq 'Darwin')
    if (-not $isMacOS) {
        $hasSsh = Get-Command ssh -ErrorAction SilentlyContinue
        if (-not $hasSsh) {
            Write-Err "macOS signing must be performed on macOS or via SSH to a macOS host"
            exit 1
        }
        Write-Warn "Not running on macOS. Signing via SSH requires a remote macOS host."
        Write-Err "Set up remote macOS signing or run this script on macOS."
        exit 1
    }

    $codesign = Get-Command codesign -ErrorAction SilentlyContinue
    if (-not $codesign) {
        Write-Err "codesign not found. Install Xcode Command Line Tools."
        exit 1
    }

    $identity = if ($SignIdentity) { $SignIdentity } else { $env:APPLE_SIGNING_IDENTITY }
    if ([string]::IsNullOrEmpty($identity)) {
        $identity = 'Developer ID Application'
    }

    if ($CertPath) {
        Import-MacOSCertificate
    }

    $buildDir = Resolve-BuildDir

    $appFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.app' -Directory -ErrorAction SilentlyContinue
    $dmgFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.dmg' -File -ErrorAction SilentlyContinue

    foreach ($app in $appFiles) {
        Write-Info "Signing app: $($app.Name)"

        $dylibFiles = Get-ChildItem -Path $app.FullName -Recurse -Include '*.dylib', '*.so' -File -ErrorAction SilentlyContinue
        foreach ($lib in $dylibFiles) {
            & codesign --force --sign $identity --timestamp --options runtime $lib.FullName
            if ($LASTEXITCODE -ne 0) {
                Write-Err "Failed to sign library: $($lib.Name)"
                exit 1
            }
        }

        $frameworkDirs = Get-ChildItem -Path $app.FullName -Recurse -Filter '*.framework' -Directory -ErrorAction SilentlyContinue
        foreach ($fw in $frameworkDirs) {
            & codesign --force --sign $identity --timestamp --options runtime $fw.FullName
            if ($LASTEXITCODE -ne 0) {
                Write-Err "Failed to sign framework: $($fw.Name)"
                exit 1
            }
        }

        & codesign --force --deep --sign $identity --timestamp --options runtime $app.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to sign: $($app.Name)"
            exit 1
        }
        Write-Ok "Signed: $($app.Name)"

        & codesign --verify --deep --strict $app.FullName
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "Verification passed: $($app.Name)"
        } else {
            Write-Warn "Verification issue: $($app.Name)"
        }
    }

    foreach ($dmg in $dmgFiles) {
        Write-Info "Signing DMG: $($dmg.Name)"
        & codesign --force --sign $identity --timestamp $dmg.FullName
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to sign: $($dmg.Name)"
            exit 1
        }
        Write-Ok "Signed: $($dmg.Name)"
    }

    if ($Notarize) {
        Notarize-MacOSArtifacts
    }
}

function Import-MacOSCertificate {
    Write-Info "Importing certificate into keychain..."

    $keychainName = if ($Keychain) { $Keychain } else { 'build.keychain' }
    $keychainPwd = if ($KeychainPassword) { $KeychainPassword } else { 'temp-password-12345' }
    $certPwd = Resolve-CertPassword

    & security create-keychain -p $keychainPwd $keychainName 2>$null
    & security unlock-keychain -p $keychainPwd $keychainName

    & security import $CertPath `
        -k $keychainName `
        -P $certPwd `
        -T /usr/bin/codesign

    & security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k $keychainPwd $keychainName

    $existingKeychains = & security list-keychains -d user 2>$null
    & security list-keychains -d user -s $keychainName @existingKeychains

    Write-Ok "Certificate imported"
}

function Notarize-MacOSArtifacts {
    Write-Info "Notarizing macOS application..."

    $appleId = if ($AppleId) { $AppleId } else { $env:NOTARIZATION_APPLE_ID }
    $applePwd = if ($AppleIdPassword) { $AppleIdPassword } else { $env:NOTARIZATION_PASSWORD }
    $team = if ($TeamId) { $TeamId } else { $env:NOTARIZATION_TEAM_ID }

    if ([string]::IsNullOrEmpty($appleId) -or [string]::IsNullOrEmpty($applePwd) -or [string]::IsNullOrEmpty($team)) {
        Write-Err "Notarization requires -AppleId, -AppleIdPassword, and -TeamId (or corresponding env vars)"
        exit 1
    }

    $buildDir = Resolve-BuildDir
    $appFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.app' -Directory -ErrorAction SilentlyContinue

    if ($appFiles.Count -eq 0) {
        Write-Warn "No .app bundles found for notarization"
        return
    }

    foreach ($app in $appFiles) {
        $zipPath = Join-Path $env:TEMP "$($app.Name).zip"

        & ditto -c -k --keepParent $app.FullName $zipPath

        Write-Info "Submitting for notarization: $($app.Name)"
        $submitOutput = & xcrun notarytool submit $zipPath `
            --apple-id $appleId `
            --password $applePwd `
            --team-id $team `
            --wait 2>&1

        if ($submitOutput -match 'status: Accepted') {
            Write-Ok "Notarization accepted: $($app.Name)"

            Write-Info "Stapling notarization ticket..."
            & xcrun stapler staple $app.FullName
            Write-Ok "Stapled: $($app.Name)"
        } else {
            Write-Err "Notarization failed for: $($app.Name)"
            $submitOutput | ForEach-Object { Write-Host $_ }
            Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
            exit 1
        }

        Remove-Item -Force $zipPath -ErrorAction SilentlyContinue
    }
}

function Sign-LinuxArtifacts {
    Write-Info "Signing Linux artifacts..."

    $gpg = Get-Command gpg -ErrorAction SilentlyContinue
    if (-not $gpg) {
        Write-Err "GPG is not installed. Required for Linux signing."
        exit 1
    }

    $gpgKeyId = if ($GpgKey) { $GpgKey } else { $env:GPG_KEY }
    if ([string]::IsNullOrEmpty($gpgKeyId)) {
        Write-Err "GPG key ID is required. Use -GpgKey or set GPG_KEY env var."
        exit 1
    }

    $gpgPass = if ($GpgPassphrase) { $GpgPassphrase } else { $env:GPG_PASSPHRASE }
    $buildDir = Resolve-BuildDir

    $debFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.deb' -File -ErrorAction SilentlyContinue
    $appImageFiles = Get-ChildItem -Path $buildDir -Recurse -Filter '*.AppImage' -File -ErrorAction SilentlyContinue

    foreach ($deb in $debFiles) {
        Write-Info "Signing DEB: $($deb.Name)"
        if ($gpgPass) {
            $gpgOutput = echo $gpgPass | & gpg --batch --yes --passphrase-fd 0 --default-key $gpgKeyId --detach-sign --armor $deb.FullName 2>&1
        } else {
            $gpgOutput = & gpg --default-key $gpgKeyId --detach-sign --armor $deb.FullName 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to sign: $($deb.Name)"
            Write-Host $gpgOutput
            exit 1
        }
        Write-Ok "Signed: $($deb.Name)"
    }

    foreach ($appimg in $appImageFiles) {
        Write-Info "Signing AppImage: $($appimg.Name)"
        if ($gpgPass) {
            $gpgOutput = echo $gpgPass | & gpg --batch --yes --passphrase-fd 0 --default-key $gpgKeyId --detach-sign $appimg.FullName 2>&1
        } else {
            $gpgOutput = & gpg --default-key $gpgKeyId --detach-sign $appimg.FullName 2>&1
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Err "Failed to sign: $($appimg.Name)"
            Write-Host $gpgOutput
            exit 1
        }
        Write-Ok "Signed: $($appimg.Name)"
    }

    Verify-LinuxSignatures -BuildDir $buildDir -GpgKeyId $gpgKeyId
}

function Verify-LinuxSignatures {
    param(
        [string]$BuildDir,
        [string]$GpgKeyId
    )

    Write-Info "Verifying Linux signatures..."

    $sigFiles = Get-ChildItem -Path $BuildDir -Recurse -Filter '*.sig' -File -ErrorAction SilentlyContinue
    $ascFiles = Get-ChildItem -Path $BuildDir -Recurse -Filter '*.asc' -File -ErrorAction SilentlyContinue
    $allSigs = @($sigFiles) + @($ascFiles)

    foreach ($sig in $allSigs) {
        $baseFile = $sig.FullName -replace '\.(sig|asc)$', ''
        if (Test-Path $baseFile) {
            $verifyOutput = & gpg --verify $sig.FullName $baseFile 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Ok "Signature verified: $(Split-Path $baseFile -Leaf)"
            } else {
                Write-Warn "Signature verification issue: $(Split-Path $baseFile -Leaf)"
            }
        }
    }
}

function Main {
    Write-Host ""
    Write-Host "============================================="
    Write-Host "  Code Signing Script (PowerShell)"
    Write-Host "  Platform:  $Platform"
    Write-Host "  Build Dir: $(Resolve-BuildDir)"
    Write-Host "============================================="
    Write-Host ""

    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()

    switch ($Platform) {
        'win'   { Sign-WindowsArtifacts }
        'macos'   { Sign-MacOSArtifacts }
        'linux' { Sign-LinuxArtifacts }
        'all'   {
            Sign-WindowsArtifacts
            Sign-MacOSArtifacts
            Sign-LinuxArtifacts
        }
    }

    $stopwatch.Stop()

    Write-Host ""
    Write-Ok "Signing completed for platform: $Platform ($($stopwatch.Elapsed.ToString('mm\:ss')))"
}

Main
