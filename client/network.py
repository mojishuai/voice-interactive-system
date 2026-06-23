"""
网络客户端 - 与服务器通信
支持命令发送、设备控制、实时反馈
"""

import socket
import json
import threading
from typing import Dict, Optional, Callable, Any
import logging
import time

logger = logging.getLogger(__name__)


class ClientNetwork:
    """网络客户端类"""
    
    def __init__(self, host: str, port: int, timeout: int = 5):
        """
        初始化网络客户端
        
        Args:
            host: 服务器地址
            port: 服务器端口
            timeout: 连接超时时间
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.is_connected = False
        self.recv_thread = None
        self.callback = None
        self.running = False
        
        logger.info(f"网络客户端初始化: {host}:{port}")
    
    def connect(self, callback: Optional[Callable] = None) -> bool:
        """
        连接到服务器
        
        Args:
            callback: 接收消息的回调函数
            
        Returns:
            是否连接成功
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.timeout)
            self.socket.connect((self.host, self.port))
            
            self.is_connected = True
            self.callback = callback
            self.running = True
            
            # 启动接收线程
            self.recv_thread = threading.Thread(target=self._receive_loop)
            self.recv_thread.daemon = True
            self.recv_thread.start()
            
            logger.info(f"已连接到服务器: {self.host}:{self.port}")
            return True
        
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.is_connected = False
        logger.info("已断开连接")
    
    def send_command(self, command: Dict[str, Any]) -> bool:
        """
        发送命令
        
        Args:
            command: 命令字典
            
        Returns:
            是否发送成功
        """
        if not self.is_connected:
            logger.error("未连接到服务器")
            return False
        
        try:
            json_data = json.dumps(command, ensure_ascii=False)
            self.socket.sendall((json_data + '\n').encode('utf-8'))
            logger.debug(f"已发送命令: {command}")
            return True
        except Exception as e:
            logger.error(f"发送命令失败: {e}")
            self.is_connected = False
            return False
    
    def _receive_loop(self):
        """接收消息循环"""
        buffer = ""
        try:
            while self.running:
                try:
                    data = self.socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line)
                                if self.callback:
                                    self.callback(message)
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON解析失败: {e}")
                
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"接收数据出错: {e}")
                    break
        
        except Exception as e:
            logger.error(f"接收线程异常: {e}")
        
        finally:
            self.is_connected = False
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
    
    def send_text(self, text: str) -> bool:
        """发送文本消息"""
        return self.send_command({
            'type': 'text',
            'content': text
        })
    
    def send_audio(self, audio_path: str) -> bool:
        """发送音频文件"""
        return self.send_command({
            'type': 'audio',
            'path': audio_path
        })
    
    def request_status(self) -> bool:
        """请求服务器状态"""
        return self.send_command({
            'type': 'status_request'
        })
    
    def __del__(self):
        """析构函数"""
        try:
            self.disconnect()
        except:
            pass
