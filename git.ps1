<#
.SYNOPSIS
    Factory R&D PMS - Git 版本控制工具
.DESCRIPTION
    封装常用 Git 操作，支持交互式菜单和命令行参数两种模式。
    菜单模式下显示当前分支和状态概要，方便快速了解仓库情况。
.PARAMETER Action
    非交互模式下的操作名称，支持:
      menu     - 交互式菜单（默认）
      status   - 查看仓库状态
      commit   - 暂存并提交
      push     - 推送到远程仓库
      pull     - 拉取远程更新
      log      - 查看提交历史
      diff     - 查看未暂存的修改
      branch   - 分支管理（查看/创建/切换）
      remote   - 远程仓库信息
      undo     - 撤销未提交的修改（恢复文件）
.EXAMPLE
    .\git.ps1              # 打开交互式菜单
    .\git.ps1 menu         # 同上
    .\git.ps1 status       # 直接查看状态
    .\git.ps1 commit "修复登录bug"  # 直接提交
    .\git.ps1 push         # 直接推送
    .\git.ps1 pull         # 直接拉取
#>

param(
    [string]$Action = "menu",
    [string]$Message = ""
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$GitExe = "git"

# ============================================================
# 工具函数
# ============================================================

function Write-Banner {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   工厂研发项目管理系统 - Git 版本控制" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host ">>> $Text" -ForegroundColor Yellow
}

function Write-OK {
    param([string]$Text)
    Write-Host "    [OK] $Text" -ForegroundColor Green
}

function Write-Err {
    param([string]$Text)
    Write-Host "    [错误] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "    [提示] $Text" -ForegroundColor Gray
}

function Test-GitRepo {
    try {
        Push-Location $ScriptDir
        $result = & $GitExe rev-parse --is-inside-work-tree 2>&1
        $ok = ($LASTEXITCODE -eq 0)
        Pop-Location
        return $ok
    } catch {
        return $false
    }
}

function Test-GitInstalled {
    try {
        & $GitExe --version 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Get-GitBranch {
    try {
        Push-Location $ScriptDir
        $branch = & $GitExe branch --show-current 2>&1
        Pop-Location
        return $branch.Trim()
    } catch {
        return "(unknown)"
    }
}

function Get-GitRemote {
    try {
        Push-Location $ScriptDir
        $remote = & $GitExe remote get-url origin 2>&1
        Pop-Location
        if ($LASTEXITCODE -eq 0) {
            return $remote.Trim()
        }
        return $null
    } catch {
        return $null
    }
}

# ============================================================
# 核心操作
# ============================================================

function Invoke-Status {
    Write-Step "仓库状态..."
    Push-Location $ScriptDir
    Write-Host ""
    & $GitExe status -s
    Write-Host ""
    $branch = Get-GitBranch
    $remote = Get-GitRemote
    Write-Host "  分支: $branch" -ForegroundColor Cyan
    if ($remote) {
        Write-Host "  远程: $remote" -ForegroundColor Gray
    } else {
        Write-Host "  远程: 未配置（仅本地仓库）" -ForegroundColor Yellow
    }
    Pop-Location
}

function Invoke-Diff {
    Write-Step "未暂存的修改..."
    Push-Location $ScriptDir
    Write-Host ""
    & $GitExe diff --stat
    Write-Host ""
    $choice = Read-Host "  是否查看详细差异？(y/n)"
    if ($choice.ToUpper() -eq "Y") {
        & $GitExe diff
    }
    Pop-Location
}

function Invoke-StagedDiff {
    Write-Step "已暂存的修改..."
    Push-Location $ScriptDir
    Write-Host ""
    & $GitExe diff --cached --stat
    Write-Host ""
    $choice = Read-Host "  是否查看详细差异？(y/n)"
    if ($choice.ToUpper() -eq "Y") {
        & $GitExe diff --cached
    }
    Pop-Location
}

function Invoke-Add {
    Write-Step "正在暂存所有修改..."
    Push-Location $ScriptDir
    $result = & $GitExe add . 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "已暂存所有修改"
    } else {
        Write-Err "暂存失败"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-Commit {
    Write-Step "正在提交..."
    Push-Location $ScriptDir

    # 检查是否有未暂存的修改
    $changes = & $GitExe status --porcelain 2>&1
    if ([string]::IsNullOrWhiteSpace($changes)) {
        Write-Info "没有需要提交的修改，工作区是干净的。"
        Pop-Location
        return
    }

    # 如果有修改但还没 add，先暂存
    $staged = & $GitExe diff --cached --stat 2>&1
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($staged)) {
        Write-Info "自动暂存所有修改..."
        & $GitExe add . 2>&1 | Out-Null
    }

    Write-Host ""
    Write-Host "  提交类型参考:" -ForegroundColor Gray
    Write-Host "    feat:     新功能" -ForegroundColor White
    Write-Host "    fix:      修复 Bug" -ForegroundColor White
    Write-Host "    refactor: 代码重构" -ForegroundColor White
    Write-Host "    docs:     文档更新" -ForegroundColor White
    Write-Host "    chore:    配置/脚本/依赖" -ForegroundColor White
    Write-Host "    style:    代码格式（不影响功能）" -ForegroundColor White
    Write-Host "    test:     测试相关" -ForegroundColor White
    Write-Host ""

    if ($Message -ne "") {
        $msg = $Message
    } else {
        $msg = Read-Host "  请输入提交信息（如: fix: 修复库存超卖问题）"
        if ([string]::IsNullOrWhiteSpace($msg)) {
            Write-Err "提交信息不能为空"
            Pop-Location
            return
        }
    }

    $result = & $GitExe commit -m $msg 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "提交完成"
        Write-Host ""
        Write-Host "  $($result | Select-Object -Last 3)" -ForegroundColor Gray
    } else {
        Write-Err "提交失败"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-Push {
    Write-Step "正在推送到远程仓库..."
    Push-Location $ScriptDir

    $remote = Get-GitRemote
    if (-not $remote) {
        Write-Err "没有配置远程仓库。"
        Write-Host ""
        Write-Host "  配置远程仓库:" -ForegroundColor Yellow
        Write-Host "    git remote add origin <仓库地址>" -ForegroundColor White
        Write-Host ""
        Write-Host "  示例:" -ForegroundColor Gray
        Write-Host "    GitHub:  git remote add origin https://github.com/账号/factory-pms.git" -ForegroundColor Gray
        Write-Host "    Gitee:   git remote add origin https://gitee.com/账号/factory-pms.git" -ForegroundColor Gray
        Pop-Location
        return
    }

    $branch = Get-GitBranch
    $result = & $GitExe push -u origin $branch 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "推送完成 ($branch -> origin/$branch)"
    } else {
        Write-Err "推送失败"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-Pull {
    Write-Step "正在拉取远程更新..."
    Push-Location $ScriptDir

    $remote = Get-GitRemote
    if (-not $remote) {
        Write-Err "没有配置远程仓库。"
        Pop-Location
        return
    }

    # 先 fetch
    Write-Info "获取远程分支信息..."
    & $GitExe fetch 2>&1 | Out-Null

    $result = & $GitExe pull 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "拉取完成"
        Write-Host ""
        Write-Host "  $result" -ForegroundColor Gray
    } else {
        Write-Err "拉取失败（可能存在冲突，请手动解决）"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-Log {
    Write-Step "提交历史（最近 10 条）..."
    Push-Location $ScriptDir
    Write-Host ""
    & $GitExe log --oneline --graph --decorate -10
    Write-Host ""

    $choice = Read-Host "  是否查看完整历史？(y/n)"
    if ($choice.ToUpper() -eq "Y") {
        Write-Host ""
        & $GitExe log --pretty=format:"%C(yellow)%h%Creset %C(cyan)%ad%Creset %s %C(green)(%an)%Creset" --date=short -20
        Write-Host ""
    }
    Pop-Location
}

function Invoke-ShowBranch {
    Write-Step "分支列表..."
    Push-Location $ScriptDir
    Write-Host ""
    & $GitExe branch -a
    Write-Host ""
    $current = Get-GitBranch
    Write-Host "  当前分支: $current" -ForegroundColor Cyan
    Pop-Location
}

function Invoke-CreateBranch {
    Write-Step "创建新分支..."
    Push-Location $ScriptDir

    $name = Read-Host "  请输入新分支名称"
    if ([string]::IsNullOrWhiteSpace($name)) {
        Write-Err "分支名称不能为空"
        Pop-Location
        return
    }

    $result = & $GitExe checkout -b $name 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "已创建并切换到分支: $name"
    } else {
        Write-Err "创建分支失败"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-SwitchBranch {
    Write-Step "切换分支..."
    Push-Location $ScriptDir

    # 显示分支列表
    Write-Host ""
    & $GitExe branch
    Write-Host ""
    $current = Get-GitBranch
    Write-Host "  当前分支: $current" -ForegroundColor Cyan
    Write-Host ""

    $name = Read-Host "  请输入要切换到的分支名称"
    if ([string]::IsNullOrWhiteSpace($name)) {
        Write-Err "分支名称不能为空"
        Pop-Location
        return
    }

    $result = & $GitExe checkout $name 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "已切换到分支: $name"
    } else {
        Write-Err "切换分支失败"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-RemoteInfo {
    Write-Step "远程仓库信息..."
    Push-Location $ScriptDir

    $remote = Get-GitRemote
    if (-not $remote) {
        Write-Info "未配置远程仓库。"
        Write-Host ""
        Write-Host "  配置远程仓库:" -ForegroundColor Yellow
        Write-Host "    git remote add origin <仓库地址>" -ForegroundColor White
        Write-Host ""
        Write-Host "  示例:" -ForegroundColor Gray
        Write-Host "    GitHub:  git remote add origin https://github.com/账号/factory-pms.git" -ForegroundColor Gray
        Write-Host "    Gitee:   git remote add origin https://gitee.com/账号/factory-pms.git" -ForegroundColor Gray
        Pop-Location
        return
    }

    Write-Host ""
    Write-Host "  远程地址: $remote" -ForegroundColor Cyan
    Write-Host ""

    & $GitExe remote -v
    Write-Host ""

    Pop-Location
}

function Invoke-AddRemote {
    Write-Step "添加远程仓库..."
    Push-Location $ScriptDir

    Write-Host ""
    Write-Host "  远程仓库类型:" -ForegroundColor Yellow
    Write-Host "    [1] GitHub (github.com)" -ForegroundColor White
    Write-Host "    [2] Gitee (gitee.com)" -ForegroundColor White
    Write-Host "    [3] 自定义地址" -ForegroundColor White
    Write-Host ""

    $choice = Read-Host "  请选择 (1/2/3)"
    $url = ""

    switch ($choice) {
        "1" {
            $account = Read-Host "  请输入 GitHub 账号名"
            if ([string]::IsNullOrWhiteSpace($account)) { Write-Err "账号名不能为空"; Pop-Location; return }
            $url = "https://github.com/$account/factory-pms.git"
        }
        "2" {
            $account = Read-Host "  请输入 Gitee 账号名"
            if ([string]::IsNullOrWhiteSpace($account)) { Write-Err "账号名不能为空"; Pop-Location; return }
            $url = "https://gitee.com/$account/factory-pms.git"
        }
        "3" {
            $url = Read-Host "  请输入完整的 Git 仓库地址"
        }
        default {
            Write-Err "无效选项"
            Pop-Location
            return
        }
    }

    if ([string]::IsNullOrWhiteSpace($url)) {
        Write-Err "仓库地址不能为空"
        Pop-Location
        return
    }

    $result = & $GitExe remote add origin $url 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "远程仓库已添加: $url"
        Write-Host ""
        Write-Host "  下一步:" -ForegroundColor Cyan
        Write-Host "    1. 在远程平台创建同名仓库 factory-pms" -ForegroundColor White
        Write-Host "    2. 执行推送: .\git.ps1 push" -ForegroundColor White
    } else {
        Write-Err "添加远程仓库失败（可能已存在，请先检查）"
        Write-Host $result
    }
    Pop-Location
}

function Invoke-Undo {
    Write-Step "撤销修改..."
    Push-Location $ScriptDir

    $changes = & $GitExe status --porcelain 2>&1
    if ([string]::IsNullOrWhiteSpace($changes)) {
        Write-Info "工作区是干净的，没有需要撤销的修改。"
        Pop-Location
        return
    }

    Write-Host ""
    Write-Host "  ===== 警告 =====" -ForegroundColor Red
    Write-Host "  此操作将丢弃工作区所有未提交的修改！" -ForegroundColor Red
    Write-Host "  已暂存的修改也会取消暂存，但不会影响已提交的内容。" -ForegroundColor Red
    Write-Host ""
    Write-Host "  当前修改的文件:" -ForegroundColor Yellow
    & $GitExe status -s
    Write-Host ""

    $confirm = Read-Host "  请输入 'yes' 确认撤销"
    if ($confirm -ne "yes") {
        Write-Info "已取消"
        Pop-Location
        return
    }

    # 先取消暂存
    & $GitExe reset HEAD . 2>&1 | Out-Null
    Write-Info "已取消所有暂存"

    # 恢复文件到最新提交状态
    & $GitExe checkout -- . 2>&1 | Out-Null

    # 清理未跟踪的文件
    & $GitExe clean -fd 2>&1 | Out-Null

    Write-OK "所有未提交的修改已撤销，工作区恢复到最新提交状态"

    Pop-Location
}

# ============================================================
# 交互式菜单
# ============================================================

function Show-Menu {
    Write-Banner

    $branch = Get-GitBranch
    $remote = Get-GitRemote
    $remoteInfo = if ($remote) { "已配置" } else { "未配置" }

    # 修改计数
    Push-Location $ScriptDir
    $statusLines = & $GitExe status --porcelain 2>&1
    $modCount = ($statusLines | Where-Object { $_ -ne "" }).Count
    Pop-Location

    $branchColor = if ($branch -eq "main") { "Green" } else { "Yellow" }
    Write-Host "  分支: " -NoNewline
    Write-Host $branch -ForegroundColor $branchColor -NoNewline
    Write-Host "    远程: $remoteInfo" -ForegroundColor Gray
    if ($modCount -gt 0) {
        Write-Host "  修改: ${modCount} 个文件待提交" -ForegroundColor Yellow
    } else {
        Write-Host "  修改: 工作区干净" -ForegroundColor Green
    }

    Write-Host ""
    Write-Host "  --- 日常操作 ---" -ForegroundColor Cyan
    Write-Host "  [1] 查看仓库状态" -ForegroundColor White
    Write-Host "  [2] 暂存所有修改 (git add .)" -ForegroundColor White
    Write-Host "  [3] 提交 (commit)" -ForegroundColor White
    Write-Host "  [4] 推送到远程 (push)" -ForegroundColor White
    Write-Host "  [5] 拉取更新 (pull)" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 查看 ---" -ForegroundColor Cyan
    Write-Host "  [6] 查看提交历史 (log)" -ForegroundColor White
    Write-Host "  [7] 查看未暂存的修改 (diff)" -ForegroundColor White
    Write-Host "  [8] 查看已暂存的修改 (diff --cached)" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 分支管理 ---" -ForegroundColor Cyan
    Write-Host "  [B] 查看分支列表" -ForegroundColor White
    Write-Host "  [C] 创建新分支" -ForegroundColor White
    Write-Host "  [S] 切换分支" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 远程仓库 ---" -ForegroundColor Cyan
    Write-Host "  [R] 查看远程仓库配置" -ForegroundColor White
    Write-Host "  [A] 添加远程仓库" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 其他 ---" -ForegroundColor Cyan
    Write-Host "  [U] 撤销所有未提交的修改" -ForegroundColor Red
    Write-Host "  [Q] 退出" -ForegroundColor White
    Write-Host ""
}

function Invoke-Menu {
    while ($true) {
        Write-Host ""
        Write-Host "`n`n`n`n`n`n`n`n`n`n"
        Show-Menu
        $choice = Read-Host "  请选择操作"
        Write-Host ""

        switch ($choice.ToUpper()) {
            "1" { Invoke-Status }
            "2" { Invoke-Add }
            "3" { Invoke-Commit }
            "4" { Invoke-Push }
            "5" { Invoke-Pull }
            "6" { Invoke-Log }
            "7" { Invoke-Diff }
            "8" { Invoke-StagedDiff }
            "B" { Invoke-ShowBranch }
            "C" { Invoke-CreateBranch }
            "S" { Invoke-SwitchBranch }
            "R" { Invoke-RemoteInfo }
            "A" { Invoke-AddRemote }
            "U" { Invoke-Undo }
            "Q" {
                Write-Host "  再见！" -ForegroundColor Cyan
                break
            }
            default {
                Write-Host "  无效选项，请重新选择" -ForegroundColor Red
            }
        }

        Write-Host ""
        Write-Host "  按任意键继续..." -ForegroundColor Gray
        while ($true) { $key = [Console]::ReadKey($true); if ($key.KeyChar -ne 0) { break } }
    }
}

# ============================================================
# 入口
# ============================================================

# 检查 Git 是否安装
if (-not (Test-GitInstalled)) {
    Write-Host ""
    Write-Host "  [错误] 未检测到 Git！" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Git for Windows:" -ForegroundColor Yellow
    Write-Host "    https://git-scm.com/download/win" -ForegroundColor White
    Write-Host ""
    Write-Host "  安装后重新打开终端即可使用。" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# 检查当前目录是否是 Git 仓库
if (-not (Test-GitRepo)) {
    Write-Host ""
    Write-Host "  [提示] 当前目录不是 Git 仓库" -ForegroundColor Yellow
    Write-Host ""
    $init = Read-Host "  是否初始化 Git 仓库？(y/n)"
    if ($init.ToUpper() -eq "Y") {
        Push-Location $ScriptDir
        & $GitExe init 2>&1 | Out-Null
        & $GitExe branch -m main 2>&1 | Out-Null
        Pop-Location
        Write-Host "  [OK] Git 仓库已初始化（默认分支: main）" -ForegroundColor Green
        Write-Host ""
    } else {
        Write-Host "  已取消。请在 Git 仓库目录中运行此脚本。" -ForegroundColor Gray
        exit 0
    }
}

switch ($Action) {
    "menu"    { Invoke-Menu }
    "status"  { Invoke-Status }
    "commit"  { Invoke-Commit }
    "push"    { Invoke-Push }
    "pull"    { Invoke-Pull }
    "log"     { Invoke-Log }
    "diff"    { Invoke-Diff }
    "branch"  { Invoke-ShowBranch }
    "remote"  { Invoke-RemoteInfo }
    "undo"    { Invoke-Undo }
    default {
        Write-Host "未知操作: $Action" -ForegroundColor Red
        Write-Host ""
        Write-Host "用法: .\git.ps1 [操作]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "支持的操作:" -ForegroundColor Cyan
        Write-Host "  menu        交互式菜单（默认）" -ForegroundColor White
        Write-Host "  status      查看仓库状态" -ForegroundColor White
        Write-Host "  commit      暂存并提交" -ForegroundColor White
        Write-Host "  push        推送到远程仓库" -ForegroundColor White
        Write-Host "  pull        拉取远程更新" -ForegroundColor White
        Write-Host "  log         查看提交历史" -ForegroundColor White
        Write-Host "  diff        查看未暂存的修改" -ForegroundColor White
        Write-Host "  branch      查看分支列表" -ForegroundColor White
        Write-Host "  remote      查看远程仓库配置" -ForegroundColor White
        Write-Host "  undo        撤销所有未提交的修改" -ForegroundColor White
        Write-Host ""
        Write-Host "提交示例:" -ForegroundColor Cyan
        Write-Host '  .\git.ps1 commit "feat: 添加用户导出功能"' -ForegroundColor White
        Write-Host ""
    }
}
