"""
Android设备控制模块 - 通过ADB命令控制手机
"""

import subprocess
import re
from typing import Dict, List, Optional


class DeviceController:
    """Android设备控制器"""
    
    def __init__(self, config: dict):
        """初始化设备控制器"""
        self.config = config
        self.adb_host = config.get('adb_host', '127.0.0.1')
        self.adb_port = config.get('adb_port', 5037)
        self.device_serial = config.get('device_serial', '')
        self.connected_devices = []
        self.timeout = config.get('connection_timeout', 5)
        
        self._detect_devices()
    
    def _detect_devices(self):
        """检测连接的设备"""
        try:
            result = subprocess.run(
                ['adb', 'devices'],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            lines = result.stdout.strip().split('\n')[1:]
            self.connected_devices = []
            
            for line in lines:
                if line.strip() and 'device' in line:
                    device_id = line.split()[0]
                    self.connected_devices.append(device_id)
            
            print(f"[✓] 检测到{len(self.connected_devices)}个设备: {self.connected_devices}")
            
        except Exception as e:
            print(f"[!] 设备检测失败: {e}")
    
    def get_device(self) -> Optional[str]:
        """获取目标设备"""
        if self.device_serial and self.device_serial in self.connected_devices:
            return self.device_serial
        elif self.connected_devices:
            return self.connected_devices[0]
        else:
            return None
    
    def execute_adb_command(self, command: str) -> Dict:
        """执行ADB命令"""
        device = self.get_device()
        if not device:
            return {
                'success': False,
                'error': '没有可用的设备',
                'output': ''
            }
        
        try:
            cmd = ['adb', '-s', device] + command.split()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            return {
                'success': result.returncode == 0,
                'error': result.stderr if result.returncode != 0 else None,
                'output': result.stdout
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'output': ''
            }
    
    def launch_app(self, package: str, activity: str) -> Dict:
        """启动应用"""
        command = f'shell am start -n {package}/{activity}'
        result = self.execute_adb_command(command)
        
        if result['success']:
            print(f"[✓] 应用启动成功: {package}")
        else:
            print(f"[✗] 应用启动失败: {package}")
        
        return result
    
    def input_keyevent(self, keycode: int) -> Dict:
        """输入按键事件"""
        command = f'shell input keyevent {keycode}'
        return self.execute_adb_command(command)
    
    def input_text(self, text: str) -> Dict:
        """输入文本"""
        command = f'shell input text "{text}"'
        return self.execute_adb_command(command)
    
    def tap(self, x: int, y: int) -> Dict:
        """点击屏幕"""
        command = f'shell input tap {x} {y}'
        return self.execute_adb_command(command)
    
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 300) -> Dict:
        """滑动屏幕"""
        command = f'shell input swipe {x1} {y1} {x2} {y2} {duration}'
        return self.execute_adb_command(command)
    
    def get_screen_shot(self, save_path: str = '/tmp/screenshot.png') -> Dict:
        """截屏"""
        try:
            device = self.get_device()
            if not device:
                return {'success': False, 'error': '没有可用的设备'}
            
            # 在设备上截屏
            subprocess.run(
                ['adb', '-s', device, 'shell', 'screencap', '-p', '/sdcard/screenshot.png'],
                timeout=self.timeout
            )
            
            # 拉取文件
            subprocess.run(
                ['adb', '-s', device, 'pull', '/sdcard/screenshot.png', save_path],
                timeout=self.timeout
            )
            
            print(f"[✓] 截屏保存到: {save_path}")
            return {'success': True, 'path': save_path}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_device_info(self) -> Dict:
        """获取设备信息"""
        device = self.get_device()
        if not device:
            return {'success': False, 'error': '没有可用的设备'}
        
        info = {
            'device_id': device,
            'model': '',
            'android_version': '',
            'screen_size': ''
        }
        
        try:
            # 获取型号
            result = self.execute_adb_command('shell getprop ro.product.model')
            info['model'] = result['output'].strip()
            
            # 获取Android版本
            result = self.execute_adb_command('shell getprop ro.build.version.release')
            info['android_version'] = result['output'].strip()
            
            # 获取屏幕尺寸
            result = self.execute_adb_command('shell wm size')
            info['screen_size'] = result['output'].strip()
            
            info['success'] = True
            
        except Exception as e:
            info['success'] = False
            info['error'] = str(e)
        
        return info
