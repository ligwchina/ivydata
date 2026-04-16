#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整项目检查脚本 - 按原始需求进行检查测试
"""

import sys
import subprocess
import os

def run_script(script_name):
    """运行检查脚本"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    print(f"\n{'=' * 60}")
    print(f"运行: {script_name}")
    print(f"{'=' * 60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True
        )
        
        # 尝试不同的编码解码输出
        stdout = result.stdout
        stderr = result.stderr
        
        # 尝试 utf-8
        try:
            stdout_text = stdout.decode('utf-8')
        except:
            # 尝试 gbk
            try:
                stdout_text = stdout.decode('gbk', errors='replace')
            except:
                stdout_text = str(stdout)
        
        try:
            stderr_text = stderr.decode('utf-8')
        except:
            try:
                stderr_text = stderr.decode('gbk', errors='replace')
            except:
                stderr_text = str(stderr)
        
        print(stdout_text)
        if stderr_text:
            print(f"错误输出:\n{stderr_text}")
        
        return result.returncode == 0
    except Exception as e:
        print(f"运行脚本失败: {e}")
        return False

def main():
    print("=" * 60)
    print("IvyData 项目完整检查")
    print("=" * 60)
    
    results = {}
    
    # 1. 检查 PostgreSQL 连接
    results['PostgreSQL 连接'] = run_script('check_postgres_connection.py')
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results.items():
        status = "[OK] 通过" if passed else "[ERROR] 失败"
        print(f"  {check_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有检查通过!")
    else:
        print("[ERROR] 部分检查失败，请查看上面的详细信息")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
