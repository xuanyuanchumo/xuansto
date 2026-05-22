$errors = $null
$tokens = $null
[System.Management.Automation.Language.Parser]::ParseFile('D:\Projects\TraeProjects\skiller\setup-worktree.ps1', [ref]$tokens, [ref]$errors) | Out-Null
if ($errors.Count -eq 0) {
    Write-Host "Syntax: OK - No parse errors found"
} else {
    Write-Host "Syntax: ERRORS FOUND"
    foreach ($e in $errors) {
        Write-Host "  Line $($e.Extent.StartLineNumber): $($e.Message)"
    }
}
