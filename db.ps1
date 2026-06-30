<#
.SYNOPSIS
    Factory R&D PMS - 数据库管理工具
.DESCRIPTION
    封装 Alembic 迁移、种子数据、数据库重置等常用操作。
    支持交互式菜单和非交互式命令行参数两种模式。
.PARAMETER Action
    非交互模式下的操作名称，支持:
      menu     - 交互式菜单（默认）
      migrate  - 执行所有未完成的迁移
      revision - 生成新的迁移文件
      upgrade  - 执行迁移（同 migrate）
      downgrade - 回滚最近一次迁移
      reset    - 重置数据库（删除 + 重建 + 种子数据）
      seed     - 仅插入种子数据
      init     - 自动建表 + 种子数据
      status   - 查看当前迁移状态
      history  - 查看迁移历史
      backup   - 备份数据库文件
      pwd-reset - 重置 admin 密码
      db-size  - 查看数据库大小与各表行数
.NOTES
    如果遇到 PowerShell 执行策略限制，可使用以下命令运行:
      powershell -ExecutionPolicy Bypass -File .\db.ps1 [操作]
    或临时设置执行策略:
      Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
.EXAMPLE
    .\db.ps1              # 打开交互式菜单
    .\db.ps1 menu         # 同上
    .\db.ps1 migrate      # 直接执行迁移
    .\db.ps1 reset        # 直接重置数据库
    .\db.ps1 revision     # 创建迁移文件向导
#>

param(
    [string]$Action = "menu"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$DbFile = Join-Path $BackendDir "factory_pms.db"
$BackupDir = Join-Path $ScriptDir ".db-backups"

# 优先使用项目虚拟环境，其次 WorkBuddy 管理版本
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$VenvAlembic = Join-Path $BackendDir ".venv\Scripts\alembic.exe"
$MbPython = Join-Path $env:USERPROFILE ".workbuddy\binaries\python\versions\3.13.12\python.exe"
$MbAlembic = Join-Path $env:USERPROFILE ".workbuddy\binaries\python\versions\3.13.12\Scripts\alembic.exe"

if (Test-Path $VenvPython) {
    $PythonExe = $VenvPython
    if (Test-Path $VenvAlembic) {
        $AlembicExe = $VenvAlembic
    } else {
        $AlembicExe = "alembic"
    }
} elseif (Test-Path $MbPython) {
    $PythonExe = $MbPython
    if (Test-Path $MbAlembic) {
        $AlembicExe = $MbAlembic
    } else {
        $AlembicExe = "alembic"
    }
} else {
    $PythonExe = "python"
    $AlembicExe = "alembic"
}

# ============================================================
# 工具函数
# ============================================================

function Write-Banner {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   工厂研发项目管理系统 - 数据库管理工具" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host ">>> $Text" -ForegroundColor Yellow
}

function Write-OK {
    param([string]$Text)
    Write-Host "    [成功] $Text" -ForegroundColor Green
}

function Write-Err {
    param([string]$Text)
    Write-Host "    [错误] $Text" -ForegroundColor Red
}

function Write-Info {
    param([string]$Text)
    Write-Host "    [提示] $Text" -ForegroundColor Gray
}

function Test-BackendDir {
    if (-not (Test-Path $BackendDir)) {
        Write-Err "未找到后端目录: $BackendDir"
        exit 1
    }
}

function Test-Alembic {
    try {
        Push-Location $BackendDir
        & $AlembicExe --version 2>&1 | Out-Null
        $ok = ($LASTEXITCODE -eq 0)
        Pop-Location
        return $ok
    } catch {
        return $false
    }
}

# ============================================================
# 核心操作
# ============================================================

function Invoke-Migrate {
    Write-Step "正在执行数据库迁移..."
    Test-BackendDir
    if (-not (Test-Alembic)) {
        Write-Err "未找到 Alembic。请执行: pip install alembic"
        return
    }
    try {
        Push-Location $BackendDir
        $result = & $AlembicExe upgrade head 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "迁移执行完成"
        } else {
            Write-Err "迁移执行失败"
            Write-Host $result
        }
    } finally {
        Pop-Location
    }
}

function Invoke-Downgrade {
    param([string]$Revision = "-1")
    Write-Step "正在回滚迁移..."
    Test-BackendDir
    try {
        Push-Location $BackendDir
        $result = & $AlembicExe downgrade $Revision 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "回滚完成（目标版本: $Revision）"
        } else {
            Write-Err "回滚失败"
            Write-Host $result
        }
    } finally {
        Pop-Location
    }
}

function Invoke-NewRevision {
    Write-Step "创建新的迁移文件..."
    Write-Host ""
    Write-Host "  将从模型变更自动生成迁移内容..." -ForegroundColor Gray
    Write-Host "  （对比 SQLAlchemy 模型与当前数据库结构的差异）" -ForegroundColor Gray
    Write-Host ""

    $message = Read-Host "  请输入迁移描述（如: add_user_phone）"
    if ([string]::IsNullOrWhiteSpace($message)) {
        Write-Err "迁移描述不能为空"
        return
    }

    Test-BackendDir
    try {
        Push-Location $BackendDir
        $result = & $AlembicExe revision --autogenerate -m $message 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "迁移文件已生成"
            Write-Host ""
            Write-Host "  下一步: 检查 alembic/versions/ 下生成的文件，" -ForegroundColor Cyan
            Write-Host "  确认无误后执行: .\db.ps1 migrate" -ForegroundColor Cyan
        } else {
            Write-Err "迁移文件生成失败"
            Write-Host $result
        }
    } finally {
        Pop-Location
    }
}

function Invoke-Init {
    Write-Step "正在初始化数据库..."
    Test-BackendDir
    try {
        Push-Location $BackendDir
        & $PythonExe run.py init 2>&1
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -eq 0) {
        Write-OK "数据库初始化完成"
    }
}

function Invoke-Reset {
    Write-Host ""
    Write-Host "  ===== 警告 =====" -ForegroundColor Red
    Write-Host "  此操作将删除所有数据并重建数据库。" -ForegroundColor Red
    Write-Host "  所有表将被清空，此操作不可撤销！" -ForegroundColor Red
    Write-Host ""

    $confirm = Read-Host "  请输入 'yes' 确认"
    if ($confirm -ne "yes") {
        Write-Info "已取消"
        return
    }

    Test-BackendDir

    # 先备份
    if (Test-Path $DbFile) {
        Write-Step "正在备份当前数据库..."
        Invoke-Backup
    }

    try {
        Push-Location $BackendDir

        # 删除现有数据库文件
        if (Test-Path $DbFile) {
            Remove-Item $DbFile -Force
            Write-OK "已删除现有数据库文件"
        }

        # 删除 WAL 和 SHM 文件
        Get-ChildItem $BackendDir -Filter "factory_pms.db*" | Remove-Item -Force -ErrorAction SilentlyContinue

        # 重新初始化
        & $PythonExe run.py init 2>&1
    } finally {
        Pop-Location
    }

    if ($LASTEXITCODE -eq 0) {
        Write-OK "数据库重置完成"
        Write-Host ""
        Write-Host "  默认账号: admin" -ForegroundColor Cyan
        Write-Host "  密码说明: 若设置了 ADMIN_PASSWORD 环境变量则使用该值，否则自动生成随机密码（见上方输出）" -ForegroundColor Gray
    }
}

function Invoke-Seed {
    Write-Step "正在插入种子数据..."
    Test-BackendDir
    try {
        Push-Location $BackendDir
        & $PythonExe run.py seed 2>&1
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -eq 0) {
        Write-OK "种子数据插入完成"
    }
}

function Invoke-Status {
    Write-Step "当前迁移状态..."
    Test-BackendDir
    try {
        Push-Location $BackendDir
        & $AlembicExe current 2>&1
    } finally {
        Pop-Location
    }
}

function Invoke-History {
    Write-Step "迁移历史记录..."
    Test-BackendDir
    try {
        Push-Location $BackendDir
        & $AlembicExe history 2>&1
    } finally {
        Pop-Location
    }
}

function Invoke-Backup {
    Write-Step "正在备份数据库..."
    Test-BackendDir
    if (-not (Test-Path $DbFile)) {
        Write-Err "未找到数据库文件: $DbFile"
        return
    }

    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = Join-Path $BackupDir "factory_pms_$timestamp.db"
    Copy-Item $DbFile $backupFile -Force

    $size = (Get-Item $DbFile).Length
    $sizeMB = [math]::Round($size / 1MB, 2)

    Write-OK "备份已保存: $backupFile"
    Write-Info "文件大小: ${sizeMB} MB"

    # 列出已有备份
    $backups = Get-ChildItem $BackupDir -Filter "factory_pms_*.db" | Sort-Object LastWriteTime -Descending
    if ($backups.Count -gt 0) {
        Write-Host ""
        Write-Host "  历史备份列表:" -ForegroundColor Gray
        $count = 0
        foreach ($b in $backups) {
            $count++
            $bs = [math]::Round($b.Length / 1MB, 2)
            Write-Host "    $($b.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))  ${bs}MB  $($b.Name)" -ForegroundColor Gray
            if ($count -ge 5) { break }
        }
        if ($backups.Count -gt 5) {
            Write-Host "    ... 还有 $($backups.Count - 5) 个备份" -ForegroundColor Gray
        }
    }
}

function Invoke-ResetPassword {
    Write-Step "正在重置管理员密码..."
    Test-BackendDir
    if (-not (Test-Path $DbFile)) {
        Write-Err "未找到数据库文件。请先执行初始化。"
        return
    }

    $newPwd = $env:ADMIN_PASSWORD
    if (-not $newPwd) {
        Write-Host ""
        Write-Host "  默认密码: admin123" -ForegroundColor Gray
        Write-Host "  也可设置 ADMIN_PASSWORD 环境变量自定义密码" -ForegroundColor Gray
        Write-Host ""
        $input = Read-Host "  请输入新密码（直接回车使用默认值 admin123）"
        if ([string]::IsNullOrWhiteSpace($input)) {
            $newPwd = "admin123"
        } else {
            $newPwd = $input
        }
    }

    try {
        Push-Location $BackendDir
        $result = & $PythonExe -c @"
from app.core.security import get_password_hash
import sqlite3, sys
try:
    conn = sqlite3.connect('factory_pms.db')
    cur = conn.cursor()
    new_hash = get_password_hash('$newPwd')
    cur.execute('UPDATE users SET password_hash = ? WHERE username = ?', (new_hash, 'admin'))
    if cur.rowcount == 0:
        print('ERROR: admin account not found')
        sys.exit(1)
    conn.commit()
    conn.close()
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
"@ 2>&1
    } finally {
        Pop-Location
    }

    if ($LASTEXITCODE -eq 0 -and $result -match "OK") {
        Write-OK "管理员密码已重置为: admin / $newPwd"
    } else {
        Write-Err "密码重置失败"
        Write-Host $result
    }
}

function Invoke-DbSize {
    Write-Step "数据库统计信息..."
    Test-BackendDir
    if (Test-Path $DbFile) {
        $size = (Get-Item $DbFile).Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        $sizeKB = [math]::Round($size / 1KB, 2)
        Write-Host "    文件:   $DbFile" -ForegroundColor Gray
        Write-Host "    大小:   ${sizeMB} MB (${sizeKB} KB)" -ForegroundColor White

        # 表统计
        try {
            Push-Location $BackendDir
            $tmpPy = Join-Path $env:TEMP "factory_pms_db_size.py"
@'
import sqlite3
conn = sqlite3.connect("factory_pms.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
for row in cur.fetchall():
    t = row[0]
    cur.execute("SELECT COUNT(*) FROM [{}]".format(t))
    cnt = cur.fetchone()[0]
    print("{}: {}".format(t, cnt))
conn.close()
'@ | Out-File -FilePath $tmpPy -Encoding UTF8
            $stats = & $PythonExe $tmpPy 2>&1
            Remove-Item $tmpPy -Force -ErrorAction SilentlyContinue
        } finally {
            Pop-Location
        }

        Write-Host ""
        Write-Host "  各表行数:" -ForegroundColor Gray
        foreach ($line in $stats) {
            Write-Host "    $line" -ForegroundColor Gray
        }
    } else {
        Write-Err "未找到数据库文件"
    }
}

function Invoke-OpenDb {
    Write-Step "正在打开 SQLite 交互式命令行..."
    Test-BackendDir
    if (-not (Test-Path $DbFile)) {
        Write-Err "未找到数据库文件"
        return
    }
    Push-Location $BackendDir
    & $PythonExe -c "import sqlite3, os; os.system(f'sqlite3 {os.path.abspath('factory_pms.db')}')" 2>&1
    Pop-Location
}

# ============================================================
# 交互式菜单
# ============================================================

function Show-Menu {
    Write-Banner

    # 显示数据库状态
    if (Test-Path $DbFile) {
        $size = (Get-Item $DbFile).Length
        $sizeMB = [math]::Round($size / 1MB, 2)
        Write-Host "  数据库: factory_pms.db (${sizeMB} MB)" -ForegroundColor Green
    } else {
        Write-Host "  数据库: 未找到（请执行「初始化数据库」）" -ForegroundColor Red
    }

    # 迁移状态
    try {
        Push-Location $BackendDir
        $currentRev = & $AlembicExe current 2>&1 | Select-Object -Last 1
    } finally {
        Pop-Location
    }
    if ($currentRev -match "^([a-f0-9]+)") {
        Write-Host "  迁移版本: $currentRev" -ForegroundColor Green
    } elseif ($currentRev -match "head") {
        Write-Host "  迁移版本: 已是最新" -ForegroundColor Green
    } else {
        Write-Host "  迁移版本: $currentRev" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "  --- 数据迁移 ---" -ForegroundColor Cyan
    Write-Host "  [1] 执行迁移（升级到最新版本）" -ForegroundColor White
    Write-Host "  [2] 创建新迁移（从模型变更生成）" -ForegroundColor White
    Write-Host "  [3] 回滚最近一次迁移" -ForegroundColor White
    Write-Host "  [4] 查看当前迁移版本" -ForegroundColor White
    Write-Host "  [5] 查看迁移历史记录" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 数据库管理 ---" -ForegroundColor Cyan
    Write-Host "  [6] 初始化数据库（建表 + 种子数据）" -ForegroundColor White
    Write-Host "  [7] 仅插入种子数据" -ForegroundColor White
    Write-Host "  [8] 重置数据库（清空全部数据并重建）" -ForegroundColor Red
    Write-Host "  [9] 备份数据库" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 其他 ---" -ForegroundColor Cyan
    Write-Host "  [A] 重置管理员密码" -ForegroundColor White
    Write-Host "  [S] 查看数据库大小与统计" -ForegroundColor White
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
            "1" { Invoke-Migrate }
            "2" { Invoke-NewRevision }
            "3" { Invoke-Downgrade }
            "4" { Invoke-Status }
            "5" { Invoke-History }
            "6" { Invoke-Init }
            "7" { Invoke-Seed }
            "8" { Invoke-Reset }
            "9" { Invoke-Backup }
            "A" { Invoke-ResetPassword }
            "S" { Invoke-DbSize }
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

switch ($Action) {
    "menu"       { Invoke-Menu }
    "migrate"    { Invoke-Migrate }
    "upgrade"    { Invoke-Migrate }
    "downgrade"  { Invoke-Downgrade }
    "revision"   { Invoke-NewRevision }
    "init"       { Invoke-Init }
    "reset"      { Invoke-Reset }
    "seed"       { Invoke-Seed }
    "status"     { Invoke-Status }
    "history"    { Invoke-History }
    "backup"     { Invoke-Backup }
    "pwd-reset"  { Invoke-ResetPassword }
    "db-size"    { Invoke-DbSize }
    "open"       { Invoke-OpenDb }
    default {
        Write-Host "未知操作: $Action" -ForegroundColor Red
        Write-Host ""
        Write-Host "用法: .\db.ps1 [操作]" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "支持的操作:" -ForegroundColor Cyan
        Write-Host "  menu        交互式菜单（默认）" -ForegroundColor White
        Write-Host "  migrate     执行未完成的迁移" -ForegroundColor White
        Write-Host "  revision    创建新的迁移文件" -ForegroundColor White
        Write-Host "  downgrade   回滚最近一次迁移" -ForegroundColor White
        Write-Host "  init        建表 + 种子数据" -ForegroundColor White
        Write-Host "  reset       清空所有表并重建" -ForegroundColor White
        Write-Host "  seed        仅插入种子数据" -ForegroundColor White
        Write-Host "  status      查看当前迁移版本" -ForegroundColor White
        Write-Host "  history     查看迁移历史" -ForegroundColor White
        Write-Host "  backup      备份数据库文件" -ForegroundColor White
        Write-Host "  pwd-reset   重置管理员密码" -ForegroundColor White
        Write-Host "  db-size     查看数据库大小与统计" -ForegroundColor White
        Write-Host ""
    }
}
