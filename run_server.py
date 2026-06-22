#!/usr/bin/env python3
"""
启动服务器 - 控制Android设备
在Windows/Linux/Mac上运行此脚本启动服务器
需要连接ADB设备
"""

import sys
import yaml
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from server.server import run_server


def main():
    """主程序"""
    print("="*60)
    print("语音人机交互系统 - 服务器")
    print("="*60)
    
    # 加载配置
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("[✓] 配置加载成功")
    except Exception as e:
        print(f"[✗] 配置加载失败: {e}")
        return
    
    # 启动服务器
    try:
        print(f"\n[*] 启动服务器...")
        print(f"监听地址: {config['server']['host']}:{config['server']['port']}")
        print(f"\n按 Ctrl+C 停止服务器\n")
        run_server(config)
    except Exception as e:
        print(f"[✗] 服务器启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
