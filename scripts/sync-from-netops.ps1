<#
.SYNOPSIS
    Sync reusable source files from opensource/NetOps-toolkit into api/app/.

.DESCRIPTION
    Defined by docs/NetOps-toolkit reuse plan section 3.
    Re-run this script after upstream updates. Pure copy + rename, no source modification.

.NOTES
    Run from repo root: powershell -File scripts/sync-from-netops.ps1
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = ''
)

$ErrorActionPreference = 'Stop'

if (-not $RepoRoot) {
    $scriptPath = if ($PSScriptRoot) { $PSScriptRoot } `
                  elseif ($MyInvocation.MyCommand.Path) { Split-Path -Parent $MyInvocation.MyCommand.Path } `
                  else { (Get-Location).Path }
    $RepoRoot = (Resolve-Path (Join-Path $scriptPath '..')).Path
}

$Src = Join-Path $RepoRoot 'opensource\NetOps-toolkit'
$Dst = Join-Path $RepoRoot 'api\app'

if (-not (Test-Path $Src)) {
    throw "Source directory not found: $Src"
}

Write-Host "Source: $Src"
Write-Host "Target: $Dst"
Write-Host ""

# 1. Ensure package directories exist with empty __init__.py
$pkgDirs = @(
    'core',
    'tools',
    'data',
    'data/manual',
    'engine',
    'engine/vendors',
    'engine/vendors/huawei',
    'engine/adapters'
)

foreach ($d in $pkgDirs) {
    $full = Join-Path $Dst $d
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
        Write-Host "  + mkdir $d"
    }
    $init = Join-Path $full '__init__.py'
    if (-not (Test-Path $init)) {
        New-Item -ItemType File -Path $init -Force | Out-Null
    }
}

# 2. Section 3.1 zero-modification files (source -> target)
$copyMap = @(
    # network tools
    @{ From = 'utils/network_tools/subnet_calculator.py'; To = 'tools/subnet.py' },
    @{ From = 'utils/network_tools/ping_tool.py';        To = 'tools/ping.py' },
    @{ From = 'utils/network_tools/trace_route.py';      To = 'tools/trace.py' },
    @{ From = 'utils/network_tools/port_scanner.py';     To = 'tools/portscan.py' },
    @{ From = 'utils/network_tools/dns_tool.py';         To = 'tools/dns.py' },

    # validator
    @{ From = 'utils/validator.py';                      To = 'core/validator.py' },

    # command manuals
    @{ From = 'utils/manual/huawei_manual.py';           To = 'data/manual/huawei.py' },
    @{ From = 'utils/manual/h3c_manual.py';              To = 'data/manual/h3c.py' },
    @{ From = 'utils/manual/ruijie_manual.py';           To = 'data/manual/ruijie.py' },
    @{ From = 'utils/manual/maipu_manual.py';            To = 'data/manual/maipu.py' },

    # config cases
    @{ From = 'data/command_reference.py';               To = 'data/cases.py' },

    # Section 3.2 vendor generators
    @{ From = 'modules/basic_config.py';                 To = 'engine/vendors/huawei/basic.py' },
    @{ From = 'modules/vlan_config.py';                  To = 'engine/vendors/huawei/vlan.py' },
    @{ From = 'modules/routing_config.py';               To = 'engine/vendors/huawei/routing.py' },
    @{ From = 'modules/security_config.py';              To = 'engine/vendors/huawei/security.py' },
    @{ From = 'modules/interface_config.py';             To = 'engine/vendors/huawei/interface.py' },
    @{ From = 'modules/qos_config.py';                   To = 'engine/vendors/huawei/qos.py' },
    @{ From = 'modules/h3c_config.py';                   To = 'engine/vendors/h3c.py' },
    @{ From = 'modules/ruijie_config.py';                To = 'engine/vendors/ruijie.py' },
    @{ From = 'modules/maipu_config.py';                 To = 'engine/vendors/maipu.py' }
)

$copied = 0
foreach ($item in $copyMap) {
    $from = Join-Path $Src $item.From
    $to   = Join-Path $Dst $item.To
    if (-not (Test-Path $from)) {
        Write-Warning "  ! source missing, skip: $($item.From)"
        continue
    }
    $toDir = Split-Path -Parent $to
    if (-not (Test-Path $toDir)) {
        New-Item -ItemType Directory -Path $toDir -Force | Out-Null
    }
    Copy-Item -Path $from -Destination $to -Force
    Write-Host "  + $($item.From)  =>  app/$($item.To)"
    $copied++
}

# 3. copy LICENSE
$licSrc = Join-Path $Src 'LICENSE'
$licDst = Join-Path $RepoRoot 'api\LICENSE-NetOps-toolkit'
if (Test-Path $licSrc) {
    Copy-Item -Path $licSrc -Destination $licDst -Force
    Write-Host "  + LICENSE  =>  api/LICENSE-NetOps-toolkit"
}

Write-Host ""
Write-Host "Done. $copied files synced."
