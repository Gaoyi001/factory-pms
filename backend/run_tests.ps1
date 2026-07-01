
<#
.SYNOPSIS
    工厂研发项目管理系统 - 后端测试运行器

.DESCRIPTION
    测试管理工具，支持交互式菜单和命令行参数运行 pytest 测试。
#>

param(
    [string]$Action = "menu",
    [switch]$Verbose,
    [switch]$Quiet,
    [string]$Module,
    [string]$Keyword,
    [switch]$InstallDependencies
)

$ErrorActionPreference = "Continue"
$BackendDir = $PSScriptRoot
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"
$VenvDir = Join-Path $BackendDir ".venv"
$RequirementsFile = Join-Path $BackendDir "requirements.txt"

function Write-ColorOutput {
    param($Message, $Color = "White")
    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
        "Gray" = [ConsoleColor]::Gray
    }
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

function Show-Banner {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   工厂研发项目管理系统 - 测试运行器" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""
}

function Clear-TestDatabases {
    $testDbs = Get-ChildItem -Path $BackendDir -Filter "test_*.db" -Recurse -ErrorAction SilentlyContinue
    if ($testDbs) {
        foreach ($db in $testDbs) {
            $removed = $false
            for ($i = 1; $i -le 5; $i++) {
                try {
                    Remove-Item $db.FullName -Force
                    Write-Host "  - $($db.FullName.Replace($BackendDir, '.'))" -ForegroundColor Gray
                    $removed = $true
                    break
                } catch {
                    if ($i -eq 5) {
                        Write-Host "  - $($db.FullName.Replace($BackendDir, '.')) (被锁定，跳过)" -ForegroundColor Yellow
                    } else {
                        Start-Sleep -Milliseconds 500
                    }
                }
            }
        }
    }
}

function Install-Dependencies {
    Write-ColorOutput "[设置] 检查依赖..." "Cyan"

    Write-ColorOutput "[设置] 停止运行中的进程..." "Yellow"
    Get-Process -Name uvicorn -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1

    if (-not (Test-Path $VenvDir)) {
        Write-ColorOutput "[设置] 创建虚拟环境..." "Yellow"
        python -m venv $VenvDir
        if ($LASTEXITCODE -ne 0) {
            Write-ColorOutput "[错误] 创建虚拟环境失败" "Red"
            return $false
        }
        Write-ColorOutput "[设置] 虚拟环境创建成功" "Green"
    }

    if (-not (Test-Path $VenvPython)) {
        Write-ColorOutput "[错误] 未找到虚拟环境 Python: $VenvPython" "Red"
        return $false
    }

    Write-ColorOutput "[设置] 升级 pip..." "Yellow"
    & $VenvPython -m pip install --upgrade pip

    if (Test-Path $RequirementsFile) {
        Write-ColorOutput "[设置] 从 requirements.txt 安装依赖..." "Yellow"
        & $VenvPython -m pip install -r $RequirementsFile
    } else {
        Write-ColorOutput "[设置] 未找到 requirements.txt，安装默认依赖..." "Yellow"
        $defaultDeps = @(
            "fastapi==0.115.0",
            "uvicorn==0.31.0",
            "sqlalchemy==2.0.49",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-multipart==0.0.12",
            "anyio==4.14.1",
            "alembic==1.13.3",
            "python-dotenv==1.0.1",
            "pytest==9.1.1",
            "pytest-cov==7.1.0",
            "httpx==0.27.2"
        )
        & $VenvPython -m pip install @defaultDeps
    }

    if ($LASTEXITCODE -eq 0) {
        Write-ColorOutput "[设置] 依赖安装成功" "Green"
        return $true
    } else {
        Write-ColorOutput "[错误] 依赖安装失败" "Red"
        return $false
    }
}

function Invoke-TestRun {
    param(
        [string]$TestModule = "",
        [string]$TestKeyword = "",
        [switch]$IsVerbose = $false,
        [switch]$IsQuiet = $false
    )

    if (-not (Test-Path $VenvPython)) {
        Write-ColorOutput "[错误] 未找到虚拟环境: $VenvPython" "Red"
        Write-ColorOutput "请先安装依赖" "Yellow"
        return
    }

    Clear-TestDatabases

    $pytestArgs = @()

    if ($IsQuiet) {
        $pytestArgs += @("-q", "--tb=no")
    } elseif ($IsVerbose) {
        $pytestArgs += @("-v", "--tb=short")
    } else {
        $pytestArgs += @("-v", "--tb=line")
    }

    $pytestArgs += @("--no-cov", "-p", "no:warnings")

    if ($TestModule) {
        $testFile = Join-Path (Join-Path $BackendDir "tests") "test_$TestModule.py"
        if (Test-Path $testFile) {
            $pytestArgs += @("tests/test_$TestModule.py")
            Write-ColorOutput "[模块] 运行 $TestModule 测试" "Yellow"
        } else {
            Write-ColorOutput "[警告] 模块 '$TestModule' 未找到，运行所有测试" "Yellow"
            $pytestArgs += @("tests/")
        }
    } else {
        $pytestArgs += @("tests/")
    }

    if ($TestKeyword) {
        $pytestArgs += @("-k", $TestKeyword)
        Write-ColorOutput "[过滤] 关键词: $TestKeyword" "Yellow"
    }

    Write-ColorOutput "[命令] $VenvPython -m pytest $($pytestArgs -join ' ')" "Gray"
    Write-Host ""

    Write-ColorOutput "[运行] 开始测试..." "Cyan"
    Write-Host ""

    $startTime = Get-Date
    $allArgs = @("-m", "pytest")
    foreach ($arg in $pytestArgs) {
        $allArgs += $arg
    }
    $pytestProcess = Start-Process -FilePath $VenvPython -ArgumentList $allArgs -Wait -PassThru -NoNewWindow -WorkingDirectory $BackendDir
    $exitCode = $pytestProcess.ExitCode
    $endTime = Get-Date
    $duration = $endTime - $startTime

    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   测试结果汇总" "Cyan"
    Write-ColorOutput "========================================" "Cyan"

    if ($exitCode -eq 0) {
        Write-ColorOutput "  所有测试通过！" "Green"
    } else {
        Write-ColorOutput "  部分测试失败！" "Red"
    }

    Write-Host "  耗时: $($duration.ToString())"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""

    Write-ColorOutput "[清理] 删除测试数据库..." "Yellow"
    Start-Sleep -Seconds 1
    Clear-TestDatabases
    Write-ColorOutput "[清理] 完成" "Green"
}

function Invoke-InstallDeps {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   安装依赖" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""

    $result = Install-Dependencies

    Write-Host ""
    if ($result) {
        Write-ColorOutput "依赖安装成功！" "Green"
        Write-Host ""
        Write-ColorOutput "环境信息:" "Cyan"
        Write-Host "  Python: $VenvPython" -ForegroundColor Gray
        Write-Host "  虚拟环境: $VenvDir" -ForegroundColor Gray
        Write-Host ""
        Write-ColorOutput "现在可以运行测试了！" "Yellow"
    } else {
        Write-ColorOutput "依赖安装失败" "Red"
        Write-Host ""
        Write-ColorOutput "请检查 Python 安装和网络连接。" "Yellow"
    }
}

function Invoke-IntegrationTests {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   集成测试" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""

    Write-ColorOutput "[警告] 集成测试可能需要较长时间完成。" "Yellow"
    Write-ColorOutput "[信息] 这些测试验证多个模块之间的端到端工作流程。" "Gray"
    Write-Host ""

    $confirm = Read-Host "  运行集成测试？(y/N)"
    if ($confirm.ToUpper() -ne "Y") {
        Write-ColorOutput "已取消。" "Yellow"
        return
    }

    Invoke-TestRun -TestModule "integration" -IsVerbose $true
}

function Show-Menu {
    Show-Banner

    if (Test-Path $VenvPython) {
        Write-Host "  Python: $VenvPython" -ForegroundColor Green
    } else {
        Write-Host "  Python: 未找到（请安装依赖）" -ForegroundColor Red
    }

    $testFiles = Get-ChildItem -Path (Join-Path $BackendDir "tests") -Filter "test_*.py" -ErrorAction SilentlyContinue
    if ($testFiles) {
        Write-Host "  测试模块: 可用 $($testFiles.Count) 个模块" -ForegroundColor Green
    } else {
        Write-Host "  测试模块: 未找到" -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "  --- 测试模块 ---" -ForegroundColor Cyan
    Write-Host "  [1] 运行全部测试" -ForegroundColor White
    Write-Host "  [2] BOM 测试" -ForegroundColor White
    Write-Host "  [3] 库存测试" -ForegroundColor White
    Write-Host "  [4] 项目测试" -ForegroundColor White
    Write-Host "  [5] 实验测试" -ForegroundColor White
    Write-Host "  [6] 文档测试" -ForegroundColor White
    Write-Host "  [7] 认证与用户测试" -ForegroundColor White
    Write-Host "  [8] 角色与权限测试" -ForegroundColor White
    Write-Host ""
    Write-Host "  --- 特殊功能 ---" -ForegroundColor Cyan
    Write-Host "  [A] 集成测试" -ForegroundColor White
    Write-Host "  [I] 安装依赖" -ForegroundColor Yellow
    Write-Host "  [V] 运行全部测试（详细模式）" -ForegroundColor White
    Write-Host "  [Q] 退出" -ForegroundColor White
    Write-Host ""
}

function Invoke-Menu {
    while ($true) {
        Write-Host ""
        Write-Host "`n`n`n`n`n`n`n`n`n`n"
        Show-Menu
        $choice = Read-Host "  请选择"
        Write-Host ""

        switch ($choice.ToUpper()) {
            "1" { Invoke-TestRun }
            "2" { Invoke-TestRun -TestModule "bom" }
            "3" { Invoke-TestRun -TestModule "inventory" }
            "4" { Invoke-TestRun -TestModule "projects" }
            "5" { Invoke-TestRun -TestModule "experiments" }
            "6" { Invoke-TestRun -TestModule "documents" }
            "7" { Invoke-TestRun -TestModule "auth" }
            "8" { Invoke-TestRun -TestModule "roles" }
            "A" { Invoke-IntegrationTests }
            "I" { Invoke-InstallDeps }
            "V" { Invoke-TestRun -IsVerbose $true }
            "Q" {
                Write-Host "  再见！" -ForegroundColor Cyan
                break
            }
            default {
                Write-Host "  无效选项，请重新选择" -ForegroundColor Red
            }
        }

        if ($choice.ToUpper() -ne "Q") {
            Write-Host ""
            Read-Host "  按 Enter 继续..."
        }
    }
}

function Show-Help {
    Show-Banner
    Write-Host "使用方法:"
    Write-Host "  .un_tests.ps1 [操作] [选项]"
    Write-Host ""
    Write-Host "操作:"
    Write-Host "  menu          交互式菜单（默认）"
    Write-Host "  run           直接运行测试"
    Write-Host ""
    Write-Host "选项:"
    Write-Host "  -v            详细输出"
    Write-Host "  -q            静默模式"
    Write-Host "  -m <模块>     运行指定模块测试"
    Write-Host "  -k <关键词>   按关键词过滤测试"
    Write-Host "  -InstallDependencies"
    Write-Host "                自动安装缺失的依赖"
    Write-Host ""
    Write-Host "示例:"
    Write-Host "  .un_tests.ps1"
    Write-Host "  .un_tests.ps1 run"
    Write-Host "  .un_tests.ps1 run -m bom"
    Write-Host "  .un_tests.ps1 run -InstallDependencies"
}

if ($args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

if ($Action -eq "menu") {
    Invoke-Menu
} elseif ($Action -eq "run") {
    if ($InstallDependencies) {
        Install-Dependencies | Out-Null
    }
    Invoke-TestRun -TestModule $Module -TestKeyword $Keyword -IsVerbose $Verbose -IsQuiet $Quiet
} else {
    Show-Help
}
