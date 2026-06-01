# =====================================================================
# NetCmdGen 开源项目一键克隆脚本
# 用法：
#   1. 在 PowerShell 中执行：powershell -ExecutionPolicy Bypass -File clone-opensource.ps1
#   2. 默认克隆到 E:\NetCmdGen\opensource\ 目录
#   3. 已克隆的项目会自动跳过
# 前置条件：已安装 Git（https://git-scm.com/）
# =====================================================================

$ErrorActionPreference = "Continue"
$baseDir = "E:\NetCmdGen\opensource"

# 确保目录存在
if (-not (Test-Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir -Force | Out-Null
}

# 项目清单：名称, 仓库地址, 优先级说明
$repos = @(
    # ===== 第零优先级（与 qsxwl 形态高度相似，最值得优先研究）=====
    @{ Name = "NetOps-toolkit";              Url = "https://github.com/shiwenxin123/NetOps-toolkit.git";              Priority = "P0-qsxwl同类⭐⭐⭐" }
    @{ Name = "NetAxe";                      Url = "https://github.com/iflytek/NetAxe.git";                            Priority = "P0-讯飞Web平台⭐⭐" }
    @{ Name = "network-sketcher";            Url = "https://github.com/cisco-open/network-sketcher.git";              Priority = "P0-思科AI设计⭐⭐" }
    @{ Name = "mkrjconfig";                  Url = "https://github.com/zyh001/mkrjconfig.git";                        Priority = "P0-轻量批量生成" }

    # ===== 第一优先级（MVP 必备）=====
    @{ Name = "X6";                          Url = "https://github.com/antvis/X6.git";                                Priority = "P1-画图引擎" }
    @{ Name = "drawio";                      Url = "https://github.com/jgraph/drawio.git";                            Priority = "P1-画图引擎备选" }
    @{ Name = "jinja";                       Url = "https://github.com/pallets/jinja.git";                            Priority = "P1-模板引擎" }
    @{ Name = "The-Network-Config-Generator";Url = "https://github.com/careed23/The-Network-Config-Generator.git";    Priority = "P1-参考实现⭐" }
    @{ Name = "ConfPlate";                   Url = "https://github.com/ktbyers/ConfPlate.git";                        Priority = "P1-轻量参考" }

    # ===== 第二优先级（后端集成）=====
    @{ Name = "netmiko";                     Url = "https://github.com/ktbyers/netmiko.git";                          Priority = "P2-SSH连接库" }
    @{ Name = "napalm";                      Url = "https://github.com/napalm-automation/napalm.git";                 Priority = "P2-配置抽象层" }
    @{ Name = "nornir";                      Url = "https://github.com/nornir-automation/nornir.git";                 Priority = "P2-批量编排" }

    # ===== 第三优先级（高级特性）=====
    @{ Name = "batfish";                     Url = "https://github.com/batfish/batfish.git";                          Priority = "P3-配置仿真" }
    @{ Name = "N2G";                         Url = "https://github.com/dmulyalin/N2G.git";                            Priority = "P3-反向画图" }
    @{ Name = "NetBrain_MCP";                Url = "https://github.com/IKoreyoshiI/NetBrain_MCP.git";                 Priority = "P3-国内参考⭐" }

    # ===== 第四优先级（参考）=====
    @{ Name = "awesome-network-automation";  Url = "https://github.com/networktocode/awesome-network-automation.git"; Priority = "P4-资源索引" }
    @{ Name = "Cisco-Config-Jinja-CSV";      Url = "https://github.com/Tes3awy/Cisco-Configuration-Using-Python-Jinja-CSV.git"; Priority = "P4-思科模板" }
    @{ Name = "multivendor-network-labs";    Url = "https://github.com/akarneliuk/multivendor-network-labs.git";      Priority = "P4-多厂商实验" }
    @{ Name = "network-config-checker";      Url = "https://github.com/akintunero/network-config-checker.git";        Priority = "P4-配置审计参考" }
)

# 开始克隆
$total   = $repos.Count
$current = 0
$success = 0
$skipped = 0
$failed  = 0

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " NetCmdGen 开源项目克隆器" -ForegroundColor Cyan
Write-Host " 目标目录: $baseDir" -ForegroundColor Cyan
Write-Host " 待克隆项目: $total 个" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

foreach ($repo in $repos) {
    $current++
    $name = $repo.Name
    $url  = $repo.Url
    $pri  = $repo.Priority
    $dest = Join-Path $baseDir $name

    Write-Host ""
    Write-Host "[$current/$total] [$pri] $name" -ForegroundColor Yellow

    if (Test-Path $dest) {
        Write-Host "  → 已存在，跳过（如需更新请到目录内 git pull）" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    # 使用 --depth=1 加快下载（只取最新提交）
    Write-Host "  → 克隆 $url ..." -ForegroundColor Gray
    git clone --depth=1 $url $dest 2>&1 | Out-String | Write-Host

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ 成功" -ForegroundColor Green
        $success++
    } else {
        Write-Host "  ✗ 失败（可能网络问题，可稍后单独重试）" -ForegroundColor Red
        $failed++
    }
}

Write-Host ""
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " 完成！" -ForegroundColor Cyan
Write-Host "   ✓ 成功: $success" -ForegroundColor Green
Write-Host "   - 跳过: $skipped" -ForegroundColor DarkGray
Write-Host "   ✗ 失败: $failed" -ForegroundColor Red
Write-Host "===================================================" -ForegroundColor Cyan

if ($failed -gt 0) {
    Write-Host ""
    Write-Host "提示：如果失败，可能是 GitHub 网络问题，建议：" -ForegroundColor Yellow
    Write-Host "  1. 配置 Git 走代理：git config --global http.proxy http://127.0.0.1:7890" -ForegroundColor Yellow
    Write-Host "  2. 或使用 GitHub 镜像：把脚本中的 https://github.com 替换成 https://gh.llkk.cc/https://github.com" -ForegroundColor Yellow
    Write-Host "  3. 或单独重试失败的仓库" -ForegroundColor Yellow
}
