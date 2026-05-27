param(
    [string]$Action = "setup",
    [string]$Branch = "",
    [string]$WorktreePath = ""
)

$RepoRoot = "D:\Projects\TraeProjects\skiller"

function Test-GitInstalled {
    try {
        $null = git --version 2>$null
        return $true
    } catch {
        return $false
    }
}

function Test-WorktreeExists {
    param([string]$Path)
    $wtList = git worktree list --porcelain 2>$null
    $resolvedPath = [System.IO.Path]::GetFullPath($Path)
    foreach ($line in $wtList) {
        if ($line -match "^worktree (.+)$") {
            $wtPath = [System.IO.Path]::GetFullPath($Matches[1])
            if ($wtPath -eq $resolvedPath) {
                return $true
            }
        }
    }
    return $false
}

function Setup-Worktrees {
    if (-not (Test-GitInstalled)) {
        Write-Host "[ERROR] Git is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Git first:" -ForegroundColor Yellow
        Write-Host "  winget install --id Git.Git -e --source winget" -ForegroundColor Cyan
        Write-Host "  Then restart the terminal and run this script again." -ForegroundColor Yellow
        exit 1
    }

    Push-Location $RepoRoot
    try {
        Write-Host "`n=== Xuansto-Skill Git Worktree Setup ===" -ForegroundColor Green

        Write-Host "`n[1/6] Checking current git status..." -ForegroundColor Cyan
        git status --short
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] Not a git repository or git error." -ForegroundColor Red
            exit 1
        }

        Write-Host "`n[2/6] Adding xuansto-skill-v2 and xuansto-mcp-server to git tracking..." -ForegroundColor Cyan
        git add -f .trae/skills/xuansto-skill-v2/ 2>$null
        git add -f xuansto-mcp-server/src/ 2>$null
        git add -f xuansto-mcp-server/tests/ 2>$null
        git add -f xuansto-mcp-server/scripts/ 2>$null
        git add -f xuansto-mcp-server/pyproject.toml 2>$null
        git add -f xuansto-mcp-server/mcp-config.json 2>$null
        git add -f xuansto-mcp-server/README.md 2>$null
        git add -f xuansto-mcp-server/LICENSE 2>$null
        git add -f xuansto-mcp-server/.gitignore 2>$null
        git add -f xuansto-mcp-server/.github/ 2>$null
        git add -f xuansto-mcp-server/docs/ 2>$null
        git add -f .gitignore

        Write-Host "`n[3/6] Listing current worktrees..." -ForegroundColor Cyan
        git worktree list

        $devPath = [System.IO.Path]::GetFullPath("$RepoRoot\..\skiller-dev")
        $hotfixPath = [System.IO.Path]::GetFullPath("$RepoRoot\..\skiller-hotfix")

        $defaultWorktrees = @(
            @{
                Branch = "develop"
                Path   = $devPath
                Desc   = "Development branch for parallel feature work"
            },
            @{
                Branch = "hotfix"
                Path   = $hotfixPath
                Desc   = "Hotfix branch for urgent fixes"
            }
        )

        Write-Host "`n[4/6] Creating worktrees..." -ForegroundColor Cyan
        foreach ($wt in $defaultWorktrees) {
            if (Test-WorktreeExists $wt.Path) {
                Write-Host "  [SKIP] Worktree for '$($wt.Branch)' already exists at '$($wt.Path)'." -ForegroundColor Yellow
                continue
            }

            if (Test-Path $wt.Path) {
                Write-Host "  [SKIP] Directory at '$($wt.Path)' already exists (not a worktree)." -ForegroundColor Yellow
                continue
            }

            $branchExists = git rev-parse --verify $wt.Branch 2>$null
            if ($branchExists) {
                Write-Host "  Creating worktree for existing branch '$($wt.Branch)'..." -ForegroundColor White
                git worktree add $wt.Path $wt.Branch
            } else {
                Write-Host "  Creating worktree with new branch '$($wt.Branch)'..." -ForegroundColor White
                git worktree add -b $wt.Branch $wt.Path
            }

            if ($LASTEXITCODE -eq 0) {
                Write-Host "  [OK] Created: $($wt.Path) -> $($wt.Branch)" -ForegroundColor Green
                Write-Host "       $($wt.Desc)" -ForegroundColor Gray
            } else {
                Write-Host "  [FAIL] Could not create worktree for '$($wt.Branch)'." -ForegroundColor Red
            }
        }

        Write-Host "`n[5/6] Final worktree list:" -ForegroundColor Cyan
        git worktree list

        Write-Host "`n[6/6] Git status summary:" -ForegroundColor Cyan
        git status --short | Select-Object -First 20

        Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
        Write-Host @"
Worktree structure:
  $RepoRoot           -> main (stable)
  $devPath            -> develop (parallel development)
  $hotfixPath         -> hotfix (urgent fixes)

Each worktree contains all three components:
  - .trae/skills/xuansto-skill/      (v5, deprecated)
  - .trae/skills/xuansto-skill-v2/   (v7, current)
  - xuansto-mcp-server/              (MCP server)

Useful commands:
  git worktree list                   - List all worktrees
  git worktree add -b <branch> <path> - Add new worktree
  git worktree remove <path>          - Remove a worktree
  git worktree prune                  - Clean stale worktree records
"@ -ForegroundColor Gray
    } finally {
        Pop-Location
    }
}

function Add-SingleWorktree {
    if (-not (Test-GitInstalled)) {
        Write-Host "[ERROR] Git is not installed." -ForegroundColor Red
        exit 1
    }

    if (-not $Branch -or -not $WorktreePath) {
        Write-Host "Usage: .\setup-worktree.ps1 -Action add -Branch <branch-name> -WorktreePath <path>" -ForegroundColor Yellow
        exit 1
    }

    Push-Location $RepoRoot
    try {
        $resolvedPath = [System.IO.Path]::GetFullPath($WorktreePath)

        if (Test-WorktreeExists $resolvedPath) {
            Write-Host "[SKIP] Worktree already exists at '$resolvedPath'." -ForegroundColor Yellow
            git worktree list
            return
        }

        if (Test-Path $resolvedPath) {
            Write-Host "[ERROR] Directory at '$resolvedPath' already exists (not a worktree)." -ForegroundColor Red
            exit 1
        }

        $branchExists = git rev-parse --verify $Branch 2>$null
        if ($branchExists) {
            git worktree add $resolvedPath $Branch
        } else {
            git worktree add -b $Branch $resolvedPath
        }

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Created worktree: $resolvedPath -> $Branch" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Could not create worktree for '$Branch'." -ForegroundColor Red
        }

        git worktree list
    } finally {
        Pop-Location
    }
}

function Remove-Worktree {
    if (-not (Test-GitInstalled)) {
        Write-Host "[ERROR] Git is not installed." -ForegroundColor Red
        exit 1
    }

    if (-not $WorktreePath) {
        Write-Host "Usage: .\setup-worktree.ps1 -Action remove -WorktreePath <path>" -ForegroundColor Yellow
        Write-Host "`nCurrent worktrees:" -ForegroundColor Cyan
        Push-Location $RepoRoot
        try {
            git worktree list
        } finally {
            Pop-Location
        }
        exit 1
    }

    Push-Location $RepoRoot
    try {
        $resolvedPath = [System.IO.Path]::GetFullPath($WorktreePath)
        git worktree remove $resolvedPath
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] Removed worktree: $resolvedPath" -ForegroundColor Green
        } else {
            Write-Host "[FAIL] Could not remove worktree. Try --force:" -ForegroundColor Red
            Write-Host "  git worktree remove --force $resolvedPath" -ForegroundColor Yellow
        }
        git worktree list
    } finally {
        Pop-Location
    }
}

function Show-Status {
    if (-not (Test-GitInstalled)) {
        Write-Host "[ERROR] Git is not installed." -ForegroundColor Red
        exit 1
    }

    Push-Location $RepoRoot
    try {
        Write-Host "=== Worktree Status ===" -ForegroundColor Green
        git worktree list
        Write-Host ""
        foreach ($line in (git worktree list --porcelain 2>$null)) {
            if ($line -match "^worktree (.+)$") {
                $wtPath = $Matches[1]
                Write-Host "Worktree: $wtPath" -ForegroundColor Cyan
                if (Test-Path $wtPath) {
                    Push-Location $wtPath
                    try {
                        git status --short | Select-Object -First 5
                    } finally {
                        Pop-Location
                    }
                } else {
                    Write-Host "  [STALE] Directory does not exist. Run 'git worktree prune' to clean." -ForegroundColor Red
                }
                Write-Host ""
            }
        }
    } finally {
        Pop-Location
    }
}

switch ($Action) {
    "setup"  { Setup-Worktrees }
    "add"    { Add-SingleWorktree }
    "remove" { Remove-Worktree }
    "status" { Show-Status }
    default  {
        Write-Host @"
Usage: .\setup-worktree.ps1 -Action <action> [options]

Actions:
  setup              Create default worktrees (develop, hotfix)
  add                Add a single worktree (-Branch, -WorktreePath required)
  remove             Remove a worktree (-WorktreePath required)
  status             Show status of all worktrees

Examples:
  .\setup-worktree.ps1 -Action setup
  .\setup-worktree.ps1 -Action add -Branch feature/v2-mcp -WorktreePath D:\Projects\TraeProjects\skiller-v2
  .\setup-worktree.ps1 -Action remove -WorktreePath D:\Projects\TraeProjects\skiller-dev
  .\setup-worktree.ps1 -Action status
"@
    }
}
