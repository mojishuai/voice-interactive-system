"""
命令解析模块 - 将识别的文本转换为可执行的命令
"""

from typing import Dict, Tuple, List
import re


class CommandParser:
    """命令解析器"""
    
    # 定义支持的命令映射
    COMMAND_MAP = {
        # QQ和社交应用
        "打开QQ": {
            "package": "com.tencent.mobileqq",
            "activity": ".SplashActivity",
            "desc": "打开QQ应用"
        },
        "打开微信": {
            "package": "com.tencent.mm",
            "activity": ".ui.LauncherUI",
            "desc": "打开微信应用"
        },
        "打开钉钉": {
            "package": "com.alibaba.android.gtalking",
            "activity": ".DingTalkLauncherUI",
            "desc": "打开钉钉应用"
        },
        
        # 媒体应用
        "打开相机": {
            "package": "com.android.camera",
            "activity": ".Camera",
            "desc": "打开相机应用"
        },
        "打开相册": {
            "package": "com.android.gallery3d",
            "activity": ".Gallery",
            "desc": "打开相册应用"
        },
        "打开音乐": {
            "package": "com.netease.cloudmusic",
            "activity": ".MainActivity",
            "desc": "打开网易云音乐"
        },
        
        # 浏览器
        "打开浏览器": {
            "package": "com.android.chrome",
            "activity": "com.google.android.apps.chrome.Main",
            "desc": "打开Chrome浏览器"
        },
        
        # 系统控制命令
        "锁屏": {
            "command": "input keyevent 26",
            "desc": "锁定屏幕"
        },
        "返回": {
            "command": "input keyevent 4",
            "desc": "点击返回按钮"
        },
        "主页": {
            "command": "input keyevent 3",
            "desc": "返回主页"
        },
        "截屏": {
            "command": "input keyevent 120",
            "desc": "截屏"
        },
        "音量增加": {
            "command": "input keyevent 24",
            "desc": "增加音量"
        },
        "音量减少": {
            "command": "input keyevent 25",
            "desc": "减少音量"
        },
        
        # 拍照
        "拍照": {
            "command": "input keyevent 27",
            "desc": "拍照"
        },
        
        # 电源控制
        "关闭屏幕": {
            "command": "shell input keyevent 26",
            "desc": "关闭屏幕"
        },
        
        # 文件管理
        "打开文件管理器": {
            "package": "com.android.documentsui",
            "activity": ".DocumentsActivity",
            "desc": "打开文件管理器"
        },
        
        # 计算器
        "打开计算器": {
            "package": "com.android.calculator2",
            "activity": ".Calculator",
            "desc": "打开计算器"
        },
        
        # 设置
        "打开设置": {
            "package": "com.android.settings",
            "activity": ".Settings",
            "desc": "打开系统设置"
        },
        
        # 短信
        "打开短信": {
            "package": "com.android.mms",
            "activity": ".ui.ConversationList",
            "desc": "打开短信应用"
        },
        
        # 邮件
        "打开邮件": {
            "package": "com.android.email",
            "activity": ".activity.MessageList",
            "desc": "打开邮件应用"
        },
        
        # 地图
        "打开地图": {
            "package": "com.baidu.BaiduMap",
            "activity": ".BaiduMapActivity",
            "desc": "打开百度地图"
        },
        
        # 支付应用
        "打开支付宝": {
            "package": "com.eg.android.AlipayGphone",
            "activity": ".AlipayLogin",
            "desc": "打开支付宝"
        },
        
        # 视频应用
        "打开抖音": {
            "package": "com.ss.android.ugc.aweme",
            "activity": ".splash.SplashActivity",
            "desc": "打开抖音"
        },
    }
    
    def __init__(self):
        """初始化命令解析器"""
        self.command_count = len(self.COMMAND_MAP)
        print(f"[✓] 命令解析器初始化成功，支持{self.command_count}个命令")
    
    def parse(self, text: str) -> Dict:
        """
        解析文本为命令
        
        Args:
            text: 识别的文本
            
        Returns:
            命令字典，包含命令类型和参数
        """
        if not text or not isinstance(text, str):
            return self._error_result("输入文本无效")
        
        # 清理文本
        text = text.strip()
        
        # 完全匹配
        if text in self.COMMAND_MAP:
            return self._make_result(self.COMMAND_MAP[text])
        
        # 模糊匹配（包含关键词）
        for cmd, info in self.COMMAND_MAP.items():
            if self._fuzzy_match(text, cmd):
                return self._make_result(info)
        
        return self._error_result(f"无法识别命令: {text}")
    
    def _fuzzy_match(self, text: str, pattern: str) -> bool:
        """模糊匹配"""
        # 检查是否包含主要关键词
        keywords = pattern.split()
        return all(kw in text for kw in keywords)
    
    def _make_result(self, command_info: Dict) -> Dict:
        """构造命令结果"""
        result = {
            "success": True,
            "type": None,
            "command": None,
            "desc": command_info.get("desc", ""),
            "error": None
        }
        
        if "package" in command_info:
            result["type"] = "launch_app"
            result["command"] = {
                "package": command_info["package"],
                "activity": command_info["activity"]
            }
        elif "command" in command_info:
            result["type"] = "shell_command"
            result["command"] = command_info["command"]
        
        return result
    
    def _error_result(self, error: str) -> Dict:
        """错误结果"""
        return {
            "success": False,
            "type": None,
            "command": None,
            "desc": "",
            "error": error
        }
    
    def get_all_commands(self) -> List[str]:
        """获取所有支持的命令"""
        return list(self.COMMAND_MAP.keys())
    
    def add_command(self, text: str, command_info: Dict):
        """动态添加命令"""
        self.COMMAND_MAP[text] = command_info
        self.command_count += 1
        print(f"[+] 添加新命令: {text}")
    
    def remove_command(self, text: str):
        """删除命令"""
        if text in self.COMMAND_MAP:
            del self.COMMAND_MAP[text]
            self.command_count -= 1
            print(f"[-] 删除命令: {text}")
