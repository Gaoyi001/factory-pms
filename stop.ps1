param(
    [string]$Action = "stop"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PidDir = Join-Path $ScriptDir ".runtime"
$BackendPidFile = Join-Path $PidDir "backend.pid"
$FrontendPidFile = Join-Path $PidDir "frontend.pid"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   停止工厂研发项目管理系统服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

function StopServiceByPidFile {
    param($PidFile, $Name)
    if (Test-Path $PidFile) {
        $procId = Get-Content $PidFile
        if (-not [string]::IsNullOrWhiteSpace($procId)) {
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if ($proc) {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "  [成功] $Name 已停止（进程ID: $procId）" -ForegroundColor Green
            } else {
                Write-Host "  [跳过] $Name 未在运行" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  [跳过] $Name PID 文件为空" -ForegroundColor Yellow
        }
        Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "  [跳过] 未找到 $Name PID 文件" -ForegroundColor Yellow
    }
}

function StopServiceByPort {
    param($Port, $Name)
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($conn in $conns) {
            $procId = $conn.OwningProcess
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            Write-Host "  [成功] $Name（端口 $Port）已停止（进程ID: $procId）" -ForegroundColor Green
        }
    } else {
        Write-Host "  [跳过] $Name（端口 $Port）未在运行" -ForegroundColor Yellow
    }
}

Write-Host "[1/2] 通过进程文件停止..." -ForegroundColor Yellow
StopServiceByPidFile -PidFile $FrontendPidFile -Name "前端"
StopServiceByPidFile -PidFile $BackendPidFile -Name "后端"
Write-Host ""

Write-Host "[2/2] 通过端口停止（兜底）..." -ForegroundColor Yellow
StopServiceByPort -Port 5173 -Name "前端"
StopServiceByPort -Port 8000 -Name "后端"
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  所有服务已停止！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
