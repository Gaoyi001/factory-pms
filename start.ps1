param(
    [string]$Action = "start"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ScriptDir "backend"
$FrontendDir = Join-Path $ScriptDir "frontend"
$DbFile = Join-Path $BackendDir "factory_pms.db"
$PidDir = Join-Path $ScriptDir ".runtime"
$BackendPidFile = Join-Path $PidDir "backend.pid"
$FrontendPidFile = Join-Path $PidDir "frontend.pid"
$BackendLog = Join-Path $PidDir "backend.log"
$FrontendLog = Join-Path $PidDir "frontend.log"

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$host.UI.RawUI.WindowTitle = "工厂研发项目管理系统 - 一键启动"

function Write-Step { param($msg) Write-Host ">>> $msg" -ForegroundColor Cyan }
function Write-OK   { param($msg) Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "    [!] $msg" -ForegroundColor Yellow }
function Write-Err  { param($msg) Write-Host "    [X] $msg" -ForegroundColor Red }

# ==== Find Python ====
$PythonExe = $null
$wbPython = Join-Path $env:USERPROFILE ".workbuddy\binaries\python\versions"
if (Test-Path $wbPython) {
    $versions = Get-ChildItem $wbPython -Directory | Sort-Object Name -Descending
    foreach ($v in $versions) {
        $candidate = Join-Path $v.FullName "python.exe"
        if (Test-Path $candidate) { $PythonExe = $candidate; break }
    }
}
if (-not $PythonExe) {
    $sysPy = @("C:\Python\Python313\python.exe","C:\Python\Python312\python.exe","C:\Python\Python311\python.exe","python","python3")
    foreach ($c in $sysPy) {
        if ($c -eq "python" -or $c -eq "python3") {
            $check = Get-Command $c -ErrorAction SilentlyContinue
            if ($check) { $PythonExe = $c; break }
        } elseif (Test-Path $c) { $PythonExe = $c; break }
    }
}
if (-not $PythonExe) {
    Write-Err "未找到可用的 Python 解释器"
    Write-Host "请确保 Python 3.11+ 已安装。"
    pause; exit 1
}
Write-Host "[Env] Python: $PythonExe" -ForegroundColor Gray

# ==== Find Node.js ====
$NodeExe = $null
$wbNode = Join-Path $env:USERPROFILE ".workbuddy\binaries\node\versions"
if (Test-Path $wbNode) {
    $versions = Get-ChildItem $wbNode -Directory | Sort-Object Name -Descending
    foreach ($v in $versions) {
        $candidate = Join-Path $v.FullName "node.exe"
        if (Test-Path $candidate) { $NodeExe = $candidate; break }
    }
}
if (-not $NodeExe) {
    $sysNode = @(
        (Join-Path $env:LOCALAPPDATA "Programs\nodejs\node.exe"),
        (Join-Path $env:ProgramFiles "nodejs\node.exe"),
        "node"
    )
    foreach ($c in $sysNode) {
        if ($c -eq "node") {
            $check = Get-Command node -ErrorAction SilentlyContinue
            if ($check) { $NodeExe = $check.Source; break }
        } elseif (Test-Path $c) { $NodeExe = $c; break }
    }
}
if (-not $NodeExe) {
    Write-Err "未找到可用的 Node.js"
    Write-Host "请确保 Node.js 18+ 已安装。"
    pause; exit 1
}
Write-Host "[Env] Node.js: $NodeExe" -ForegroundColor Gray

$NpmPath = Split-Path -Parent $NodeExe
$NpmCmd = Join-Path $NpmPath "npm.cmd"
if (-not (Test-Path $NpmCmd)) { $NpmCmd = Join-Path $NpmPath "npm" }
Write-Host "[Env] npm: $NpmCmd" -ForegroundColor Gray

# ==== Check Backend Deps ====
function Check-BackendDeps {
    Write-Step "检查后端依赖..."
    $check = & $PythonExe -c "import fastapi,uvicorn,sqlalchemy,pydantic" 2>&1
    if ($LASTEXITCODE -eq 0) { Write-OK "后端环境就绪"; return }
    Write-Warn "后端依赖未安装，正在安装..."
    Push-Location $BackendDir
    try {
        & $PythonExe -m pip install -r requirements.txt 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Err "后端依赖安装失败，请检查网络连接"
            pause; exit 1
        }
        Write-OK "后端依赖安装完成"
    } finally { Pop-Location }
}

# ==== Check Frontend Deps ====
function Check-FrontendDeps {
    Write-Step "检查前端依赖..."
    if (-not (Test-Path (Join-Path $FrontendDir "node_modules\vite"))) {
        Write-Warn "前端依赖未安装，正在安装..."
        Push-Location $FrontendDir
        try {
            $oldPath = $env:PATH
            $env:PATH = "$NpmPath;$oldPath"
            & $NpmCmd install 2>&1 | Out-Null
            $env:PATH = $oldPath
            Write-OK "前端依赖安装完成"
        } finally { Pop-Location }
    } else { Write-OK "前端依赖已就绪" }
}

# ==== Init Database ====
function Init-Database {
    Write-Step "检查数据库..."
    if (-not (Test-Path $DbFile)) {
        Write-Warn "数据库不存在，正在初始化..."
        Push-Location $BackendDir
        try {
            & $PythonExe run.py init 2>&1 | Out-Null
            Write-OK "数据库初始化完成"
        } finally { Pop-Location }
    } else { Write-OK "数据库已就绪" }
}

# ==== Start Services ====
function Start-Backend {
    Write-Step "启动后端服务 (端口 8000)..."
    if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
    Push-Location $BackendDir
    try {
        $proc = Start-Process -FilePath $PythonExe `
            -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" `
            -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $BackendLog `
            -RedirectStandardError (Join-Path $PidDir "backend.err.log")
        $proc.Id | Out-File $BackendPidFile
        Write-OK "后端已启动 (PID: $($proc.Id))"
    } finally { Pop-Location }
}

function Start-Frontend {
    Write-Step "启动前端服务 (端口 5173)..."
    if (-not (Test-Path $PidDir)) { New-Item -ItemType Directory -Path $PidDir -Force | Out-Null }
    Push-Location $FrontendDir
    try {
        $oldPath = $env:PATH
        $env:PATH = "$NpmPath;$oldPath"
        $proc = Start-Process -FilePath $NpmCmd `
            -ArgumentList "run","dev" `
            -PassThru -WindowStyle Hidden `
            -RedirectStandardOutput $FrontendLog `
            -RedirectStandardError (Join-Path $PidDir "frontend.err.log")
        $env:PATH = $oldPath
        $proc.Id | Out-File $FrontendPidFile
        Write-OK "前端已启动 (PID: $($proc.Id))"
    } finally { Pop-Location }
}

function Show-Status {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "   服务状态" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    $be = $false
    if (Test-Path $BackendPidFile) {
        $pid = Get-Content $BackendPidFile
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($p) { $be = $true }
    }
    if (-not $be) {
        $c = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if ($c) { $be = $true }
    }
    if ($be) {
        Write-Host "  Backend: Running (http://localhost:8000)" -ForegroundColor Green
        Write-Host "  API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Gray
    } else { Write-Host "  Backend: Stopped" -ForegroundColor Red }
    $fe = $false
    if (Test-Path $FrontendPidFile) {
        $pid = Get-Content $FrontendPidFile
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($p) { $fe = $true }
    }
    if (-not $fe) {
        $c = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
        if ($c) { $fe = $true }
    }
    if ($fe) {
        Write-Host "  Frontend: Running (http://localhost:5173)" -ForegroundColor Green
    } else { Write-Host "  Frontend: Stopped" -ForegroundColor Red }
    Write-Host ""
}

switch ($Action) {
    "status" {
        Show-Status
        exit 0
    }
    "start" {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "   工厂研发项目管理系统 - 一键启动" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Check-BackendDeps
        Check-FrontendDeps
        Init-Database
        Write-Host ""
        Start-Backend
        Start-Sleep -Seconds 2
        Start-Frontend
        Start-Sleep -Seconds 4
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "   启动完成！" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
        Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
        Write-Host "  API Docs: http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Default: admin / admin123" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to check status..." -ForegroundColor Gray
        while ($true) { $key = [Console]::ReadKey($true); if ($key.KeyChar -ne 0) { break } }
        Show-Status
        Write-Host "Press any key to close..." -ForegroundColor Gray
        while ($true) { $key = [Console]::ReadKey($true); if ($key.KeyChar -ne 0) { break } }
    }
    default {
        Write-Err "未知操作: $Action"
        Write-Host "可用操作: start, status"
        pause
    }
}
