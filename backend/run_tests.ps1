# FastAPI 后端一键测试脚本
# 用法: .\run_tests.ps1 [-v] [-q] [-m <module>] [-k <keyword>]

param(
    [switch]$Verbose,      # 显示详细输出 (-v)
    [switch]$Quiet,        # 静默模式，只显示摘要 (-q)
    [string]$Module,       # 只运行指定模块: bom,inventory,samples,projects,experiments,documents,auth,users,roles,departments,integration
    [string]$Keyword       # 按关键字过滤测试: -k "test_name"
)

$ErrorActionPreference = "Continue"
$BackendDir = $PSScriptRoot
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

# 颜色定义
function Write-ColorOutput {
    param($Message, $Color = "White")
    $colorMap = @{
        "Red" = [ConsoleColor]::Red
        "Green" = [ConsoleColor]::Green
        "Yellow" = [ConsoleColor]::Yellow
        "Cyan" = [ConsoleColor]::Cyan
        "White" = [ConsoleColor]::White
    }
    Write-Host $Message -ForegroundColor $colorMap[$Color]
}

# 显示横幅
function Show-Banner {
    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   工厂研发项目管理系统 - 测试脚本" "Cyan"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""
}

# 清理测试数据库
function Clear-TestDatabases {
    $testDbs = Get-ChildItem -Path $BackendDir -Filter "test_*.db" -ErrorAction SilentlyContinue
    if ($testDbs) {
        Write-ColorOutput "[清理] 删除临时测试数据库..." "Yellow"
        foreach ($db in $testDbs) {
            Remove-Item $db.FullName -Force -ErrorAction SilentlyContinue
            Write-Host "  - $($db.Name)" -ForegroundColor Gray
        }
    }
}

# 构建pytest命令
function Build-PytestCommand {
    $cmd = @($VenvPython, "-m", "pytest", "tests/")

    # 输出格式
    if ($Quiet) {
        $cmd += @("-q", "--tb=no")
    } elseif ($Verbose) {
        $cmd += @("-v", "--tb=short")
    } else {
        $cmd += @("-v", "--tb=line")
    }

    # 覆盖率
    $cmd += @("--no-cov", "-p", "no:warnings")

    # 模块过滤
    if ($Module) {
        $testFile = "tests/test_$Module.py"
        if (Test-Path (Join-Path $BackendDir $testFile)) {
            $cmd += @("-k", $Module)
            Write-ColorOutput "[模块] 运行 $Module 测试" "Yellow"
        } else {
            Write-ColorOutput "[警告] 模块 '$Module' 不存在，将运行所有测试" "Yellow"
        }
    }

    # 关键字过滤
    if ($Keyword) {
        $cmd += @("-k", $Keyword)
        Write-ColorOutput "[过滤] 关键字: $Keyword" "Yellow"
    }

    return $cmd
}

# 主流程
function Run-Tests {
    Show-Banner

    # 检查Python虚拟环境
    if (-not (Test-Path $VenvPython)) {
        Write-ColorOutput "[错误] 虚拟环境不存在: $VenvPython" "Red"
        Write-ColorOutput "请先运行: .\install_deps.ps1 或手动创建虚拟环境" "Yellow"
        exit 1
    }

    # 清理旧数据库
    Clear-TestDatabases

    # 构建命令
    $pytestCmd = Build-PytestCommand

    Write-ColorOutput "[命令] $($pytestCmd -join ' ')" "Gray" -NoNewline
    Write-Host ""

    # 执行测试
    Write-ColorOutput "[运行] 开始测试..." "Cyan"
    Write-Host ""

    $startTime = Get-Date
    $result = & $VenvPython -m pytest tests/ @pytestCmd[1..($pytestCmd.Length - 1)]
    $exitCode = $LASTEXITCODE
    $endTime = Get-Date
    $duration = $endTime - $startTime

    Write-Host ""
    Write-ColorOutput "========================================" "Cyan"
    Write-ColorOutput "   测试结果摘要" "Cyan"
    Write-ColorOutput "========================================" "Cyan"

    if ($exitCode -eq 0) {
        Write-ColorOutput "  ✓ 所有测试通过!" "Green"
    } else {
        Write-ColorOutput "  ✗ 存在测试失败" "Red"
    }

    Write-Host "  耗时: $($duration.ToString('mm\ss\ff'))"
    Write-ColorOutput "========================================" "Cyan"
    Write-Host ""

    exit $exitCode
}

# 显示帮助
function Show-Help {
    Show-Banner
    Write-Host @"
使用方法:
  .\run_tests.ps1 [选项]

选项:
  -v          显示详细输出 (verbose)
  -q          静默模式，只显示摘要
  -m <模块>   运行指定模块测试
              可选值: bom, inventory, samples, projects,
                      experiments, documents, auth, users,
                      roles, departments, integration

  -k <关键字> 按关键字过滤测试 (可用于运行单个测试)

示例:
  # 运行所有测试
  .\run_tests.ps1

  # 运行所有测试，显示详细输出
  .\run_tests.ps1 -v

  # 只运行 BOM 模块测试
  .\run_tests.ps1 -m bom

  # 只运行库存模块测试
  .\run_tests.ps1 -m inventory

  # 运行包含 'test_create' 的测试
  .\run_tests.ps1 -k "test_create"

  # 静默模式，只显示摘要
  .\run_tests.ps1 -q

"@
}

# 处理帮助
if ($args -contains "-h" -or $args -contains "--help") {
    Show-Help
    exit 0
}

# 执行测试
Run-Tests
