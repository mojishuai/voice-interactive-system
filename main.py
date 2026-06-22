"""
语音人机交互系统 - 主程序入口
支持语音识别、命令解析、设备控制和语音合成
"""

import sys
import os
import yaml
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from client.gui import VoiceInteractionGUI
from client.audio import AudioManager
from models.speech_recognition import SpeechRecognizer
from models.speech_synthesis import SpeechSynthesizer
from models.command_parser import CommandParser
from client.network import ClientNetwork


def load_config(config_path="config.yaml"):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """主程序"""
    print("=" * 60)
    print("语音人机交互系统")
    print("=" * 60)
    
    # 加载配置
    try:
        config = load_config()
        print("[✓] 配置加载成功")
    except Exception as e:
        print(f"[✗] 配置加载失败: {e}")
        return
    
    # 初始化各个模块
    try:
        print("\n[*] 初始化模块...")
        
        # 音频管理器
        audio_manager = AudioManager(config['audio'])
        print("[✓] 音频管理器初始化成功")
        
        # 语音识别器
        asr = SpeechRecognizer(config['asr'])
        print("[✓] 语音识别器初始化成功")
        
        # 语音合成器
        tts = SpeechSynthesizer(config['tts'])
        print("[✓] 语音合成器初始化成功")
        
        # 命令解析器
        cmd_parser = CommandParser()
        print("[✓] 命令解析器初始化成功")
        
        # 网络客户端
        network = ClientNetwork(config['server']['host'], config['server']['port'])
        print("[✓] 网络客户端初始化成功")
        
    except Exception as e:
        print(f"[✗] 模块初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 启动GUI
    try:
        print("\n[*] 启动图形界面...")
        app = VoiceInteractionGUI(
            audio_manager=audio_manager,
            asr=asr,
            tts=tts,
            cmd_parser=cmd_parser,
            network=network,
            config=config
        )
        app.run()
    except Exception as e:
        print(f"[✗] GUI启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
