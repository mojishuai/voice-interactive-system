"""
TCP服务器模块 - 接收客户端命令并控制设备
"""

import socket
import json
import threading
from server.device_control import DeviceController


class Server:
    """TCP服务器"""
    
    def __init__(self, config: dict):
        """初始化服务器"""
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 5000)
        self.socket = None
        self.is_running = False
        self.device_controller = DeviceController(config.get('android', {}))
        
    def start(self):
        """启动服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.is_running = True
            
            print(f"[✓] 服务器启动成功，监听 {self.host}:{self.port}")
            
            # 启动接收线程
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
        except Exception as e:
            print(f"[✗] 服务器启动失败: {e}")
    
    def _accept_connections(self):
        """接受连接"""
        while self.is_running:
            try:
                client_socket, client_address = self.socket.accept()
                print(f"[+] 客户端连接: {client_address}")
                
                # 为每个客户端创建处理线程
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except Exception as e:
                if self.is_running:
                    print(f"[!] 接受连接失败: {e}")
    
    def _handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        buffer = ""
        try:
            while self.is_running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # 处理多个消息
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        try:
                            command = json.loads(line)
                            result = self._execute_command(command)
                            response = json.dumps(result, ensure_ascii=False)
                            client_socket.sendall(response.encode('utf-8') + b'\n')
                        except json.JSONDecodeError:
                            print(f"[!] 无效的JSON: {line}")
        
        except Exception as e:
            print(f"[!] 处理客户端错误: {e}")
        
        finally:
            client_socket.close()
            print(f"[-] 客户端断开: {client_address}")
    
    def _execute_command(self, command: dict) -> dict:
        """执行命令"""
        try:
            cmd_type = command.get('type')
            
            if cmd_type == 'launch_app':
                package = command.get('package')
                activity = command.get('activity')
                result = self.device_controller.launch_app(package, activity)
                return {
                    'success': result['success'],
                    'message': f"启动应用: {package}",
                    'error': result['error']
                }
            
            elif cmd_type == 'shell_command':
                cmd = command.get('command')
                result = self.device_controller.execute_adb_command(cmd)
                return {
                    'success': result['success'],
                    'message': f"执行命令: {cmd}",
                    'error': result['error']
                }
            
            elif cmd_type == 'get_device_info':
                info = self.device_controller.get_device_info()
                return {
                    'success': info.get('success', False),
                    'data': info
                }
            
            else:
                return {
                    'success': False,
                    'error': f"未知的命令类型: {cmd_type}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop(self):
        """停止服务器"""
        self.is_running = False
        if self.socket:
            self.socket.close()
        print("[✓] 服务器已停止")


def run_server(config: dict):
    """运行服务器"""
    server = Server(config)
    server.start()
    
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\n[*] 正在关闭服务器...")
        server.stop()
