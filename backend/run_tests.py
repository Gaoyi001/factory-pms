#!/usr/bin/env python3
"""
FastAPI 后端一键测试脚本
用法: python run_tests.py [-v] [-q] [-m <module>] [-k <keyword>]
"""

import argparse
import subprocess
import sys
import os
import shutil
from pathlib import Path

# 颜色输出
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'


def color_print(text, color=None):
    if color is None:
        color = Colors.WHITE
    print(f"{color}{text}{Colors.END}")


def show_banner():
    print()
    color_print("=" * 45, Colors.CYAN)
    color_print("  工厂研发项目管理系统 - 测试脚本", Colors.CYAN)
    color_print("=" * 45, Colors.CYAN)
    print()


def clear_test_databases(backend_dir):
    """清理测试数据库"""
    test_dbs = list(Path(backend_dir).glob("test_*.db"))
    if test_dbs:
        color_print("[清理] 删除临时测试数据库...", Colors.YELLOW)
        for db in test_dbs:
            try:
                db.unlink()
                print(f"  - {db.name}")
            except Exception as e:
                print(f"  ! {db.name}: {e}")


def run_tests(args):
    show_banner()

    backend_dir = Path(__file__).parent.resolve()
    venv_python = backend_dir / ".venv" / "Scripts" / "python.exe"

    # Windows兼容处理
    if not venv_python.exists():
        venv_python = backend_dir / ".venv" / "bin" / "python"
    if not venv_python.exists():
        venv_python = "python"

    # 检查虚拟环境
    if not venv_python.exists() or str(venv_python) == "python":
        # 尝试直接用python
        venv_python = "python"
        if not shutil.which("pytest"):
            color_print("[错误] pytest 未安装或虚拟环境不存在", Colors.RED)
            print(f"请先运行: pip install pytest pytest-anyio")
            return 1

    # 清理旧数据库
    clear_test_databases(backend_dir)

    # 构建pytest命令
    pytest_args = ["tests/"]

    # 输出格式
    if args.quiet:
        pytest_args.extend(["-q", "--tb=no"])
    elif args.verbose:
        pytest_args.extend(["-v", "--tb=short"])
    else:
        pytest_args.extend(["-v", "--tb=line"])

    # 覆盖率
    pytest_args.extend(["--no-cov", "-p", "no:warnings"])

    # 模块过滤
    if args.module:
        # -m 参数在argparse中是dest='module'，这里用-k实现模块过滤
        pytest_args.extend(["-k", args.module])
        color_print(f"[模块] 运行 {args.module} 测试", Colors.YELLOW)

    # 关键字过滤
    if args.keyword:
        pytest_args.extend(["-k", args.keyword])
        color_print(f"[过滤] 关键字: {args.keyword}", Colors.YELLOW)

    # 打印命令
    cmd_str = f"{venv_python} -m pytest " + " ".join(pytest_args)
    color_print(f"[命令] {cmd_str}", Colors.WHITE)
    print()

    # 执行测试
    color_print("[运行] 开始测试...", Colors.CYAN)
    print()

    cmd = [str(venv_python), "-m", "pytest"] + pytest_args
    result = subprocess.run(cmd, cwd=str(backend_dir))

    print()
    color_print("=" * 45, Colors.CYAN)
    if result.returncode == 0:
        color_print("  ✓ 所有测试通过!", Colors.GREEN)
    else:
        color_print("  ✗ 存在测试失败", Colors.RED)
    color_print("=" * 45, Colors.CYAN)
    print()

    return result.returncode


def show_help():
    show_banner()
    help_text = """使用方法:
  python run_tests.py [选项]

选项:
  -v          显示详细输出 (verbose)
  -q          静默模式，只显示摘要
  -m <模块>   运行指定模块测试
              可选值: bom, inventory, samples, projects,
                      experiments, documents, auth, users,
                      roles, departments, integration

  -k <关键字> 按关键字过滤测试

示例:
  # 运行所有测试
  python run_tests.py

  # 运行所有测试，显示详细输出
  python run_tests.py -v

  # 只运行 BOM 模块测试
  python run_tests.py -m bom

  # 只运行库存模块测试
  python run_tests.py -m inventory

  # 运行包含 'test_create' 的测试
  python run_tests.py -k "test_create"

  # 静默模式，只显示摘要
  python run_tests.py -q
"""
    print(help_text)


def main():
    parser = argparse.ArgumentParser(description="FastAPI后端测试脚本", add_help=False)
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    parser.add_argument("-m", "--module", type=str, help="指定模块")
    parser.add_argument("-k", "--keyword", type=str, help="关键字过滤")
    parser.add_argument("-h", "--help", action="store_true", help="显示帮助")

    args = parser.parse_args()

    if args.help:
        show_help()
        return 0

    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
