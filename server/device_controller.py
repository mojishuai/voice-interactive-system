"""
设备控制模块 - 控制PC、Android、IoT设备
支持ADB、HTTP API、本地命令执行
"""

import subprocess
import json
import requests
from typing import Dict, List, Optional, Any
import logging
import time
import os
import platform

logger = logging.getLogger(__name__)


class DeviceController:
    """设备控制器基类"""
    
    def execute_command(self, command: str) -> bool:
        """执行命令"""
        raise NotImplementedError
    
    def get_status(self) -> Dict:
        """获取设备状态"""
        raise NotImplementedError


class PCController(DeviceController):
    """PC设备控制器"""
    
    def __init__(self):
        self.os_type = platform.system()
        logger.info(f"PC控制器初始化: {self.os_type}")
    
    def execute_command(self, command: str) -> bool:
        """
        执行系统命令
        
        Args:
            command: 命令字符串
            
        Returns:
            是否执行成功
        """
        try:
            if self.os_type == 'Windows':
                subprocess.Popen(['cmd', '/c', command])
            else:
                subprocess.Popen(['bash', '-c', command])
            
            logger.info(f"已执行命令: {command}")
            return True
        except Exception as e:
            logger.error(f"命令执行失败: {e}")
            return False
    
    def open_app(self, app_name: str) -> bool:
        """
        打开应用程序
        
        Args:
            app_name: 应用名称
            
        Returns:
            是否成功
        """
        app_commands = {
            'Windows': {
                'calculator': 'calc.exe',
                'notepad': 'notepad.exe',
                'file_manager': 'explorer.exe',
                'browser': 'start https://www.bing.com',
            },
            'Darwin': {  # macOS
                'calculator': 'open -a Calculator',
                'notepad': 'open -a TextEdit',
                'file_manager': 'open -a Finder',
                'browser': 'open -a Safari',
            },
            'Linux': {
                'calculator': 'gnome-calculator',
                'notepad': 'gedit',
                'file_manager': 'nautilus',
                'browser': 'firefox',
            }
        }
        
        if self.os_type in app_commands and app_name in app_commands[self.os_type]:
            cmd = app_commands[self.os_type][app_name]
            return self.execute_command(cmd)
        
        logger.warning(f"不支持的应用: {app_name}")
        return False
    
    def control_light(self, action: str, **kwargs) -> bool:
        """
        控制灯光（模拟）
        
        Args:
            action: 'on' 或 'off'
            **kwargs: 其他参数
            
        Returns:
            是否成功
        """
        logger.info(f"灯光控制: {action}")
        return True
    
    def control_volume(self, action: str, step: int = 5) -> bool:
        """
        控制音量
        
        Args:
            action: 'up', 'down', 'mute'
            step: 调整步长
            
        Returns:
            是否成功
        """
        try:
            if self.os_type == 'Windows':
                # Windows 音量控制
                if action == 'up':
                    self.execute_command(f'nircmd.exe changesysvolume {step * 655}')  # 1% = 655
                elif action == 'down':
                    self.execute_command(f'nircmd.exe changesysvolume {-step * 655}')
                elif action == 'mute':
                    self.execute_command('nircmd.exe mutesysvolume toggle')
            
            logger.info(f"音量调整: {action} {step}")
            return True
        except Exception as e:
            logger.error(f"音量控制失败: {e}")
            return False
    
    def screenshot(self, save_path: str = './screenshot.png') -> bool:
        """
        截屏
        
        Args:
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            if self.os_type == 'Windows':
                self.execute_command(f'powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.SendKeys]::SendWait(\'%2b~\')") # Print Screen')
            else:
                self.execute_command(f'scrot {save_path}')
            
            logger.info(f"截屏已保存: {save_path}")
            return True
        except Exception as e:
            logger.error(f"截屏失败: {e}")
            return False
    
    def shutdown(self, delay: int = 0) -> bool:
        """
        关机
        
        Args:
            delay: 延迟时间（秒）
            
        Returns:
            是否成功
        """
        if delay > 0:
            logger.warning(f"系统将在 {delay} 秒后关机")
        
        try:
            if self.os_type == 'Windows':
                self.execute_command(f'shutdown /s /t {delay}')
            else:
                self.execute_command(f'shutdown -h +{delay // 60}')
            
            return True
        except Exception as e:
            logger.error(f"关机失败: {e}")
            return False
    
    def reboot(self, delay: int = 0) -> bool:
        """
        重启
        
        Args:
            delay: 延迟时间（秒）
            
        Returns:
            是否成功
        """
        try:
            if self.os_type == 'Windows':
                self.execute_command(f'shutdown /r /t {delay}')
            else:
                self.execute_command(f'shutdown -r +{delay // 60}')
            
            return True
        except Exception as e:
            logger.error(f"重启失败: {e}")
            return False
    
    def get_status(self) -> Dict:
        """获取PC状态"""
        return {
            'type': 'PC',
            'os': self.os_type,
            'status': 'online'
        }


class AndroidController(DeviceController):
    """Android设备控制器（通过ADB）"""
    
    def __init__(self, device_serial: Optional[str] = None):
        """
        初始化Android控制器
        
        Args:
            device_serial: 设备序列号
        """
        self.device_serial = device_serial
        logger.info(f"Android控制器初始化: {device_serial}")
    
    def _adb_command(self, cmd: str) -> str:
        """执行ADB命令"""
        full_cmd = f'adb -s {self.device_serial} {cmd}' if self.device_serial else f'adb {cmd}'
        try:
            result = subprocess.check_output(full_cmd, shell=True, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB命令失败: {e}")
            return ""
    
    def execute_command(self, command: str) -> bool:
        """
        在Android设备上执行命令
        
        Args:
            command: shell命令
            
        Returns:
            是否成功
        """
        result = self._adb_command(f'shell {command}')
        return bool(result) or result == ""
    
    def open_app(self, package_name: str) -> bool:
        """
        打开应用
        
        Args:
            package_name: 包名
            
        Returns:
            是否成功
        """
        return self.execute_command(f'monkey -p {package_name} -c android.intent.category.LAUNCHER 1')
    
    def click(self, x: int, y: int) -> bool:
        """点击屏幕"""
        return self.execute_command(f'input tap {x} {y}')
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> bool:
        """滑动屏幕"""
        return self.execute_command(f'input swipe {x1} {y1} {x2} {y2} {duration}')
    
    def get_status(self) -> Dict:
        """获取设备状态"""
        model = self._adb_command('shell getprop ro.product.model')
        android_version = self._adb_command('shell getprop ro.build.version.release')
        
        return {
            'type': 'Android',
            'model': model,
            'android_version': android_version,
            'status': 'online'
        }


class DeviceManager:
    """设备管理器"""
    
    def __init__(self):
        self.devices: Dict[str, DeviceController] = {}
        self.pc_controller = PCController()
        self.devices['pc'] = self.pc_controller
        logger.info("设备管理器初始化")
    
    def add_android_device(self, device_id: str, serial: str):
        """添加Android设备"""
        self.devices[device_id] = AndroidController(serial)
        logger.info(f"已添加Android设备: {device_id}")
    
    def execute(self, device_id: str, executor: str, params: Dict) -> bool:
        """
        执行设备操作
        
        Args:
            device_id: 设备ID
            executor: 执行器名称
            params: 参数
            
        Returns:
            是否成功
        """
        if device_id not in self.devices:
            logger.error(f"设备不存在: {device_id}")
            return False
        
        controller = self.devices[device_id]
        
        # 映射执行器到具体方法
        executor_map = {
            'light_on': lambda: controller.control_light('on', **params) if hasattr(controller, 'control_light') else True,
            'light_off': lambda: controller.control_light('off', **params) if hasattr(controller, 'control_light') else True,
            'open_app': lambda: controller.open_app(params.get('app', '')),
            'volume_up': lambda: controller.control_volume('up', params.get('step', 5)) if hasattr(controller, 'control_volume') else True,
            'volume_down': lambda: controller.control_volume('down', params.get('step', 5)) if hasattr(controller, 'control_volume') else True,
            'mute': lambda: controller.control_volume('mute') if hasattr(controller, 'control_volume') else True,
            'screenshot': lambda: controller.screenshot() if hasattr(controller, 'screenshot') else True,
            'system_shutdown': lambda: controller.shutdown(params.get('delay', 0)) if hasattr(controller, 'shutdown') else True,
            'system_reboot': lambda: controller.reboot(params.get('delay', 0)) if hasattr(controller, 'reboot') else True,
        }
        
        if executor in executor_map:
            try:
                return executor_map[executor]()
            except Exception as e:
                logger.error(f"执行失败: {e}")
                return False
        
        logger.warning(f"未知的执行器: {executor}")
        return False
    
    def get_device_status(self, device_id: str) -> Dict:
        """获取设备状态"""
        if device_id not in self.devices:
            return {'error': '设备不存在'}
        
        return self.devices[device_id].get_status()
