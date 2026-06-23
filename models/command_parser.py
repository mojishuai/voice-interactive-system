"""
命令解析模块 - 将识别的文本转换为可执行的命令
支持命令映射、参数提取、命令优先级
"""

import re
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CommandParser:
    """命令解析器"""
    
    # 命令映射表：命令名 -> {执行器, 参数, 描述}
    COMMAND_MAP = {
        # 光照控制
        "开灯": {
            "executor": "light_on",
            "params": {"room": "all", "brightness": 100},
            "description": "打开所有灯光",
            "priority": 10
        },
        "关灯": {
            "executor": "light_off",
            "params": {"room": "all"},
            "description": "关闭所有灯光",
            "priority": 10
        },
        
        # 浏览器控制
        "打开浏览器": {
            "executor": "open_browser",
            "params": {"url": ""},
            "description": "打开网络浏览器",
            "priority": 5
        },
        "关闭浏览器": {
            "executor": "close_browser",
            "params": {},
            "description": "关闭网络浏览器",
            "priority": 5
        },
        
        # 应用程序控制
        "打开计算器": {
            "executor": "open_app",
            "params": {"app": "calculator"},
            "description": "打开计算器应用",
            "priority": 5
        },
        "打开记事本": {
            "executor": "open_app",
            "params": {"app": "notepad"},
            "description": "打开记事本应用",
            "priority": 5
        },
        "打开文件管理器": {
            "executor": "open_app",
            "params": {"app": "file_manager"},
            "description": "打开文件管理器",
            "priority": 5
        },
        
        # 系统控制
        "截屏": {
            "executor": "screenshot",
            "params": {},
            "description": "截屏保存",
            "priority": 5
        },
        
        # 音量控制
        "调高音量": {
            "executor": "volume_up",
            "params": {"step": 5},
            "description": "提高音量",
            "priority": 8
        },
        "调低音量": {
            "executor": "volume_down",
            "params": {"step": 5},
            "description": "降低音量",
            "priority": 8
        },
        "静音": {
            "executor": "mute",
            "params": {},
            "description": "静音",
            "priority": 8
        },
        
        # 媒体控制
        "打开音乐": {
            "executor": "play_media",
            "params": {"type": "music"},
            "description": "打开音乐播放器",
            "priority": 5
        },
        "停止播放": {
            "executor": "media_pause",
            "params": {},
            "description": "暂停媒体播放",
            "priority": 8
        },
        "下一首": {
            "executor": "media_next",
            "params": {},
            "description": "播放下一个",
            "priority": 8
        },
        "上一首": {
            "executor": "media_previous",
            "params": {},
            "description": "播放上一个",
            "priority": 8
        },
        
        "打开视频": {
            "executor": "play_media",
            "params": {"type": "video"},
            "description": "打开视频播放器",
            "priority": 5
        },
        "全屏": {
            "executor": "fullscreen",
            "params": {"mode": "on"},
            "description": "进入全屏模式",
            "priority": 5
        },
        "退出全屏": {
            "executor": "fullscreen",
            "params": {"mode": "off"},
            "description": "退出全屏模式",
            "priority": 5
        },
        
        # 系统操作
        "系统关机": {
            "executor": "system_shutdown",
            "params": {"delay": 0},
            "description": "关闭系统",
            "priority": 1
        },
        "系统重启": {
            "executor": "system_reboot",
            "params": {"delay": 0},
            "description": "重启系统",
            "priority": 1
        },
    }
    
    def __init__(self):
        """初始化命令解析器"""
        logger.info(f"命令解析器初始化，支持 {len(self.COMMAND_MAP)} 个命令")
    
    def parse(self, command_name: str, recognized_text: str = "") -> Optional[Dict[str, Any]]:
        """
        解析命令
        
        Args:
            command_name: 识别的命令名称
            recognized_text: 完整的识别文本（用于提取参数）
            
        Returns:
            解析结果字典，包含 executor, params, description 等
        """
        if command_name not in self.COMMAND_MAP:
            logger.warning(f"未知命令: {command_name}")
            return None
        
        command_info = self.COMMAND_MAP[command_name].copy()
        
        # 尝试从识别文本中提取额外参数
        extracted_params = self._extract_parameters(command_name, recognized_text)
        command_info["params"].update(extracted_params)
        
        logger.info(f"命令已解析: {command_name} -> {command_info['executor']}")
        logger.debug(f"参数: {command_info['params']}")
        
        return command_info
    
    def _extract_parameters(self, command_name: str, text: str) -> Dict[str, Any]:
        """
        从文本中提取命令参数
        
        Args:
            command_name: 命令名称
            text: 识别的文本
            
        Returns:
            提取的参数字典
        """
        params = {}
        
        # 提取URL（用于浏览器打开）
        if command_name == "打开浏览器":
            urls = re.findall(r'https?://[^\s]+', text)
            if urls:
                params['url'] = urls[0]
        
        # 提取亮度值
        if "灯" in command_name:
            brightness_match = re.search(r'(\d+)%|(\d+)亮度', text)
            if brightness_match:
                brightness = int(brightness_match.group(1) or brightness_match.group(2))
                params['brightness'] = min(100, max(0, brightness))
        
        # 提取房间名称
        rooms = ['卧室', '客厅', '厨房', '卫生间', '书房']
        for room in rooms:
            if room in text:
                params['room'] = room
                break
        
        # 提取数字参数
        numbers = re.findall(r'\d+', text)
        if numbers and command_name in ["调高音量", "调低音量"]:
            params['step'] = int(numbers[0])
        
        return params
    
    def get_all_commands(self) -> Dict[str, Dict[str, Any]]:
        """获取所有支持的命令"""
        return self.COMMAND_MAP
    
    def get_command_by_priority(self) -> List[Tuple[str, int]]:
        """
        按优先级排序的命令列表
        
        Returns:
            [(命令名, 优先级), ...] 按优先级降序排列
        """
        commands = [
            (name, info.get('priority', 0))
            for name, info in self.COMMAND_MAP.items()
        ]
        commands.sort(key=lambda x: x[1], reverse=True)
        return commands
    
    def is_critical_command(self, command_name: str) -> bool:
        """
        判断是否为关键命令（需要二次确认）
        
        Args:
            command_name: 命令名称
            
        Returns:
            是否为关键命令
        """
        if command_name in self.COMMAND_MAP:
            priority = self.COMMAND_MAP[command_name].get('priority', 5)
            return priority < 3  # 优先级 < 3 视为关键命令
        return False
    
    def add_custom_command(self, command_name: str, executor: str, 
                          params: Dict[str, Any] = None, 
                          description: str = "", priority: int = 5):
        """
        添加自定义命令
        
        Args:
            command_name: 命令名称
            executor: 执行器名称
            params: 默认参数
            description: 命令描述
            priority: 优先级（1-10）
        """
        if params is None:
            params = {}
        
        self.COMMAND_MAP[command_name] = {
            "executor": executor,
            "params": params,
            "description": description,
            "priority": priority
        }
        logger.info(f"添加自定义命令: {command_name}")
    
    def get_command_suggestions(self, partial_text: str) -> List[str]:
        """
        根据部分文本获取命令建议
        
        Args:
            partial_text: 部分文本
            
        Returns:
            建议的命令列表
        """
        suggestions = []
        partial_lower = partial_text.lower()
        
        for command_name in self.COMMAND_MAP.keys():
            if partial_lower in command_name.lower():
                suggestions.append(command_name)
        
        return suggestions[:5]  # 返回前5个建议
    
    def validate_command(self, command_name: str) -> bool:
        """
        验证命令是否有效
        
        Args:
            command_name: 命令名称
            
        Returns:
            是否有效
        """
        return command_name in self.COMMAND_MAP
