# ============================================================
# NetCmdGen Doc Sync Automation
# ============================================================

param(
    [string]$CommitMsg = '',
    [string]$Branch = 'main',
    [switch]$SkipVerify = $false
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
# 使用通配符避免中文文件名编码问题
$DocFile = (Get-ChildItem -Path $RepoRoot -Filter '*规划*.md' | Select-Object -First 1).FullName
if (-not $DocFile) { $DocFile = Join-Path $RepoRoot '项目规划.md' }

Write-Host "=== Step 1/5: Read planning doc ===" -ForegroundColor Cyan

if (-not (Test-Path $DocFile)) {
    Write-Error "Doc not found: $DocFile"
    exit 1
}

$DocLines = (Get-Content $DocFile -Encoding UTF8).Count
$DocHash  = (Get-FileHash $DocFile -Algorithm SHA256).Hash
Write-Host "  File: $DocFile"
Write-Host "  Lines: $DocLines"
Write-Host "  SHA256: $($DocHash.Substring(0,16))..."

Write-Host ""
Write-Host "=== Step 2/5: Git status ===" -ForegroundColor Cyan

Push-Location $RepoRoot
try {
    $gitRoot = git rev-parse --show-toplevel 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "Not a git repo"; exit 2 }

    $curBranch = git branch --show-current 2>&1
    Write-Host "  Current branch: $curBranch -> Target: $Branch"

    if ($curBranch -ne $Branch) {
        Write-Host "  Switching to $Branch ..."
        git checkout $Branch 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Error "Switch failed"; exit 3 }
    }

    $staged   = @(git diff --cached --name-only 2>&1 | Where-Object { $_ -and $_ -notlike 'warning:*' }).Count
    $unstaged = @(git diff --name-only 2>&1 | Where-Object { $_ -and $_ -notlike 'warning:*' }).Count
    $untracked = @(git ls-files --others --exclude-standard 2>&1 | Where-Object { $_ -and $_ -notlike 'warning:*' }).Count

    Write-Host "  Staged: $staged  Unstaged: $unstaged  Untracked: $untracked"

    if ($staged -eq 0 -and $unstaged -eq 0 -and $untracked -eq 0) {
        Write-Host "  Nothing to commit." -ForegroundColor Yellow
        exit 0
    }

    Write-Host ""
    Write-Host "=== Step 3/5: Stage + Commit ===" -ForegroundColor Cyan

    if (-not $CommitMsg) {
        $ts = Get-Date -Format 'yyyy-MM-dd HH:mm'
        $CommitMsg = "feat: Sprint update — $ts"
    }
    Write-Host "  Message: $CommitMsg"

    git add -A 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Write-Error "git add failed"; exit 4 }
    Write-Host "  [OK] git add -A"

    git commit -m $CommitMsg 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "git commit failed"; exit 5 }
    $hash = git log -1 --format='%h' 2>&1
    Write-Host "  [OK] Committed: $hash"

    Write-Host ""
    Write-Host "=== Step 4/5: Push to remote ===" -ForegroundColor Cyan

    git push origin $Branch 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Error "git push failed"; exit 6 }

    $remoteHash = (git ls-remote origin $Branch 2>&1 | ForEach-Object { ($_ -split '\s+')[0] }) -join ''
    $shortRemote = if ($remoteHash.Length -ge 12) { $remoteHash.Substring(0,12) } else { $remoteHash }
    Write-Host "  [OK] Pushed: origin/$Branch @ $shortRemote"

    Write-Host ""
    Write-Host "=== Step 5/5: Integrity check ===" -ForegroundColor Cyan

    if (-not $SkipVerify) {
        $localFull  = git rev-parse HEAD 2>&1
        $remoteFull = (git ls-remote origin $Branch 2>&1 | ForEach-Object { ($_ -split '\s+')[0] }) -join ''

        $localShort  = if ($localFull.Length -ge 12)  { $localFull.Substring(0,12) }  else { $localFull }
        $remoteShort = if ($remoteFull.Length -ge 12) { $remoteFull.Substring(0,12) } else { $remoteFull }

        if ($localShort -eq $remoteShort) {
            Write-Host "  [OK] Local HEAD == Remote HEAD: $localShort"
        } else {
            Write-Host "  [FAIL] Local: $localShort != Remote: $remoteShort" -ForegroundColor Red
            Write-Error "Push verification failed: local/remote mismatch"
            exit 7
        }

        Write-Host "  Key file hashes:"
        $keyFiles = @(
            @{N='项目规划.md';     P='项目规划.md'},
            @{N='App.vue';         P='web/src/App.vue'},
            @{N='Home.vue';        P='web/src/views/Home.vue'},
            @{N='Tools.vue';       P='web/src/views/Tools.vue'},
            @{N='Generator.vue';   P='web/src/views/Generator.vue'}
        )
        foreach ($kf in $keyFiles) {
            $p = Join-Path $RepoRoot $kf.P
            if (Test-Path $p) {
                $h = (Get-FileHash $p -Algorithm SHA256).Hash.Substring(0,16)
                Write-Host "    $($kf.N): SHA256=$h [OK]"
            }
        }
    }

    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  SUCCESS: Read -> Commit -> Push -> Verify" -ForegroundColor Green
    Write-Host "  Commit : $hash" -ForegroundColor Green
    Write-Host "  Branch : origin/$Branch" -ForegroundColor Green
    Write-Host "  Doc    : $DocLines lines" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green

} finally {
    Pop-Location
}
