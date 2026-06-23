"""
服务器 - 接收客户端命令并控制设备
支持多客户端连接、命令队列、状态管理
"""

import socket
import json
import threading
from typing import Dict, Optional, List
import logging
from server.device_controller import DeviceManager
import time

logger = logging.getLogger(__name__)


class VoiceServer:
    """语音交互系统服务器"""
    
    def __init__(self, host: str, port: int, config: Dict):
        """
        初始化服务器
        
        Args:
            host: 监听地址
            port: 监听端口
            config: 配置字典
        """
        self.host = host
        self.port = port
        self.config = config
        self.device_manager = DeviceManager()
        self.clients: Dict[str, socket.socket] = {}
        self.running = False
        self.server_socket = None
        self.command_queue = []
        
        # 配置Android设备
        if 'android' in config and config['android'].get('device_serial'):
            self.device_manager.add_android_device(
                'android',
                config['android']['device_serial']
            )
        
        logger.info(f"服务器初始化: {host}:{port}")
    
    def start(self):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            
            logger.info(f"服务器已启动，监听 {self.host}:{self.port}")
            
            # 启动命令处理线程
            cmd_thread = threading.Thread(target=self._process_commands)
            cmd_thread.daemon = True
            cmd_thread.start()
            
            # 接受客户端连接
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    client_id = f"{client_address[0]}:{client_address[1]}"
                    self.clients[client_id] = client_socket
                    
                    logger.info(f"新客户端连接: {client_id}")
                    
                    # 为每个客户端创建处理线程
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_id, client_socket)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"接受连接失败: {e}")
        
        except Exception as e:
            logger.error(f"服务器启动失败: {e}")
        
        finally:
            self.stop()
    
    def _handle_client(self, client_id: str, client_socket: socket.socket):
        """处理客户端连接"""
        buffer = ""
        try:
            while self.running:
                try:
                    data = client_socket.recv(4096).decode('utf-8')
                    if not data:
                        break
                    
                    buffer += data
                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        if line.strip():
                            try:
                                message = json.loads(line)
                                self._process_message(client_id, message)
                            except json.JSONDecodeError as e:
                                logger.error(f"JSON解析失败: {e}")
                
                except Exception as e:
                    logger.error(f"接收数据失败: {e}")
                    break
        
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            try:
                client_socket.close()
            except:
                pass
            logger.info(f"客户端已断开: {client_id}")
    
    def _process_message(self, client_id: str, message: Dict):
        """处理客户端消息"""
        message_type = message.get('type')
        
        if message_type == 'command':
            # 执行命令
            device_id = message.get('device_id', 'pc')
            executor = message.get('executor')
            params = message.get('params', {})
            
            success = self.device_manager.execute(device_id, executor, params)
            
            # 发送响应
            response = {
                'type': 'command_response',
                'success': success,
                'executor': executor
            }
            self._send_to_client(client_id, response)
        
        elif message_type == 'status_request':
            # 返回设备状态
            status = self.device_manager.get_device_status('pc')
            response = {
                'type': 'status_response',
                'status': status
            }
            self._send_to_client(client_id, response)
        
        else:
            logger.warning(f"未知消息类型: {message_type}")
    
    def _process_commands(self):
        """处理命令队列"""
        while self.running:
            try:
                if self.command_queue:
                    command = self.command_queue.pop(0)
                    device_id = command.get('device_id', 'pc')
                    executor = command.get('executor')
                    params = command.get('params', {})
                    
                    logger.info(f"执行命令: {executor}")
                    self.device_manager.execute(device_id, executor, params)
                
                time.sleep(0.1)
            
            except Exception as e:
                logger.error(f"命令处理异常: {e}")
    
    def _send_to_client(self, client_id: str, message: Dict) -> bool:
        """发送消息给客户端"""
        if client_id not in self.clients:
            logger.warning(f"客户端不存在: {client_id}")
            return False
        
        try:
            json_data = json.dumps(message, ensure_ascii=False)
            self.clients[client_id].sendall((json_data + '\n').encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False
    
    def broadcast(self, message: Dict):
        """广播消息给所有客户端"""
        for client_id in list(self.clients.keys()):
            self._send_to_client(client_id, message)
    
    def stop(self):
        """停止服务器"""
        self.running = False
        for client_id, client_socket in list(self.clients.items()):
            try:
                client_socket.close()
            except:
                pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("服务器已停止")


def run_server(config: Dict):
    """运行服务器"""
    host = config['server']['host']
    port = config['server']['port']
    
    server = VoiceServer(host, port, config)
    server.start()
