"""
网络通信模块 - 客户端与服务器通信
"""

import socket
import json
import threading
from typing import Dict, Callable, Optional
import time


class ClientNetwork:
    """网络客户端"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 5000):
        """初始化网络客户端"""
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.receive_thread = None
        self.is_running = False
        self.callback = None
        
    def connect(self, callback: Optional[Callable] = None) -> bool:
        """连接到服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            self.callback = callback
            self.is_running = True
            
            # 启动接收线程
            self.receive_thread = threading.Thread(target=self._receive_loop)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            print(f"[✓] 已连接到服务器 {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"[✗] 连接失败: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.connected = False
        print("[✓] 已断开连接")
    
    def send_command(self, command: Dict) -> bool:
        """发送命令到服务器"""
        if not self.connected:
            print("[!] 未连接到服务器")
            return False
        
        try:
            message = json.dumps(command, ensure_ascii=False)
            self.socket.sendall(message.encode('utf-8') + b'\n')
            print(f"[>] 发送命令: {command}")
            return True
        except Exception as e:
            print(f"[✗] 发送失败: {e}")
            self.connected = False
            return False
    
    def _receive_loop(self):
        """接收消息循环"""
        buffer = ""
        while self.is_running:
            try:
                data = self.socket.recv(4096)
                if not data:
                    self.connected = False
                    break
                
                buffer += data.decode('utf-8')
                
                # 处理多个消息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            message = json.loads(line)
                            if self.callback:
                                self.callback(message)
                        except json.JSONDecodeError:
                            print(f"[!] 无效的JSON: {line}")
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[!] 接收错误: {e}")
                self.connected = False
                break
        
        print("[*] 接收线程已停止")
