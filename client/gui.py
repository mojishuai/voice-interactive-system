"""
GUI模块 - 使用PyQt5构建图形界面
支持实时录音、识别、合成、设备控制
"""

import sys
import threading
from typing import Dict, Optional, Callable
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QProgressBar, QComboBox, QSpinBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtGui import QFont, QColor
import logging
import numpy as np

logger = logging.getLogger(__name__)


class GuiSignals(QObject):
    """GUI信号发送器"""
    update_log = pyqtSignal(str)
    update_status = pyqtSignal(str)
    update_progress = pyqtSignal(int)
    recognition_done = pyqtSignal(str)
    synthesis_done = pyqtSignal()


class VoiceInteractionGUI(QMainWindow):
    """语音交互系统GUI"""
    
    def __init__(self, audio_manager=None, asr=None, tts=None, 
                 cmd_parser=None, network=None, config=None):
        """
        初始化GUI
        
        Args:
            audio_manager: 音频管理器
            asr: 语音识别模型
            tts: 语音合成模型
            cmd_parser: 命令解析器
            network: 网络客户端
            config: 配置字典
        """
        super().__init__()
        
        self.audio_manager = audio_manager
        self.asr = asr
        self.tts = tts
        self.cmd_parser = cmd_parser
        self.network = network
        self.config = config or {}
        
        self.is_recording = False
        self.signals = GuiSignals()
        
        self.initUI()
        self.setup_connections()
        
        logger.info("GUI已初始化")
    
    def initUI(self):
        """初始化UI"""
        # 主窗口
        self.setWindowTitle("语音人機交互系统")
        self.setGeometry(100, 100, 900, 700)
        
        # 中心窗口体
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("语音人機交互系统")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 状态行
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("是否连接:"))
        self.status_label = QLabel("已断开")
        self.status_label.setStyleSheet("color: red;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        main_layout.addLayout(status_layout)
        
        # 录音按銿
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("开始录音")
        self.record_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
        self.record_button.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.clear_button = QPushButton("清空日志")
        self.clear_button.clicked.connect(self.clear_log)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        main_layout.addWidget(self.progress_bar)
        
        # 日志业务
        log_label = QLabel("事件日志:")
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(400)
        main_layout.addWidget(self.log_text)
        
        # 控制设备
        control_label = QLabel("测试控制:")
        main_layout.addWidget(control_label)
        
        control_layout = QHBoxLayout()
        self.device_combo = QComboBox()
        self.device_combo.addItems(["主PC"])
        control_layout.addWidget(QLabel("设备:"))
        control_layout.addWidget(self.device_combo)
        
        test_button = QPushButton("测试语音合成")
        test_button.clicked.connect(self.test_synthesis)
        control_layout.addWidget(test_button)
        
        main_layout.addLayout(control_layout)
        
        central_widget.setLayout(main_layout)
        
        # 信号连接
        self.signals.update_log.connect(self.append_log)
        self.signals.update_status.connect(self.update_status)
        self.signals.update_progress.connect(self.progress_bar.setValue)
    
    def setup_connections(self):
        """设置信号连接"""
        if self.network:
            self.network.connect(self.on_network_message)
            self.signals.update_status.emit("已连接服务器")
            self.status_label.setText("已连接")
            self.status_label.setStyleSheet("color: green;")
    
    def toggle_recording(self):
        """开始/停止录音"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录音"""
        if self.audio_manager:
            self.is_recording = True
            self.record_button.setText("停止录音")
            self.record_button.setStyleSheet("background-color: #f44336; color: white; font-size: 14px; padding: 10px;")
            self.progress_bar.setValue(0)
            
            self.audio_manager.start_recording()
            self.signals.update_log.emit("[*] 录音已开始")
    
    def stop_recording(self):
        """停止录音并进行识别"""
        if self.audio_manager and self.is_recording:
            self.record_button.setText("处理中...")
            self.record_button.setEnabled(False)
            
            # 在后台线程中处理
            thread = threading.Thread(target=self._process_audio)
            thread.daemon = True
            thread.start()
    
    def _process_audio(self):
        """处理音频数据"""
        try:
            audio_data = self.audio_manager.stop_recording()
            self.is_recording = False
            
            if len(audio_data) > 0:
                self.signals.update_log.emit(f"[*] 录音结束，驼棍数：{len(audio_data)}")
                self.signals.update_progress.emit(30)
                
                # 识别音频
                self.signals.update_log.emit("[*] 识别中...")
                command, text, confidence = self.asr.recognize_command(audio_data) if self.asr else ("", "", 0)
                
                self.signals.update_log.emit(f"[✓] 识别结果: '{text}'")
                self.signals.update_log.emit(f"   置信度: {confidence:.2%}")
                self.signals.update_progress.emit(60)
                
                if command and command != "unknown":
                    self.signals.update_log.emit(f"[✓] 筞別命令: {command}")
                    
                    # 解析命令
                    if self.cmd_parser:
                        cmd_info = self.cmd_parser.parse(command, text)
                        if cmd_info:
                            self.signals.update_log.emit(f"   执行器: {cmd_info.get('executor')}")
                            self.signals.update_log.emit(f"   参数: {cmd_info.get('params')}")
                            
                            # 发送到服务器
                            if self.network and self.network.is_connected:
                                self.network.send_command({
                                    'type': 'command',
                                    'device_id': 'pc',
                                    'executor': cmd_info.get('executor'),
                                    'params': cmd_info.get('params')
                                })
                                self.signals.update_log.emit("[✓] 命令已发送")
                    
                    # 合成并播放相关识剽
                    if self.tts:
                        self.signals.update_log.emit("[*] 合成报读中...")
                        response = f"已执行{command}操作"
                        try:
                            self.tts.synthesize_sync(response)
                            self.signals.update_log.emit(f"[✓] 已播报: {response}")
                        except Exception as e:
                            self.signals.update_log.emit(f"[!] 合成失败: {e}")
                
                self.signals.update_progress.emit(100)
            else:
                self.signals.update_log.emit("[!] 未收录音数据")
        
        except Exception as e:
            self.signals.update_log.emit(f"[!] 处理失败: {e}")
        
        finally:
            self.record_button.setText("开始录音")
            self.record_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px; padding: 10px;")
            self.record_button.setEnabled(True)
    
    def test_synthesis(self):
        """测试语音合成"""
        if self.tts:
            thread = threading.Thread(target=self._test_synthesis_thread)
            thread.daemon = True
            thread.start()
    
    def _test_synthesis_thread(self):
        """测试合成线程"""
        try:
            self.signals.update_log.emit("[*] 正在测试语音合成...")
            self.tts.synthesize_sync("语音人機交互系统正常工作")
            self.signals.update_log.emit("[✓] 合成测试完成")
        except Exception as e:
            self.signals.update_log.emit(f"[!] 合成失败: {e}")
    
    def on_network_message(self, message: Dict):
        """接收网络消息"""
        msg_type = message.get('type')
        if msg_type == 'command_response':
            if message.get('success'):
                self.signals.update_log.emit(f"[✓] 操作成功: {message.get('executor')}")
            else:
                self.signals.update_log.emit(f"[!] 操作失败: {message.get('executor')}")
    
    @pyqtSlot(str)
    def append_log(self, text: str):
        """添加日志"""
        self.log_text.append(text)
        # 自动滚到下方
        if self.config.get('gui', {}).get('auto_scroll_log', True):
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
    
    @pyqtSlot(str)
    def update_status(self, status: str):
        """更新状态"""
        logger.info(f"GUI状态: {status}")
    
    def clear_log(self):
        """清空日志"""
        self.log_text.clear()
        self.progress_bar.setValue(0)
    
    def closeEvent(self, event):
        """窗口关闭event"""
        if self.audio_manager:
            self.audio_manager.close()
        if self.network and self.network.is_connected:
            self.network.disconnect()
        event.accept()
    
    def run(self):
        """运行GUI"""
        self.show()
        sys.exit(QApplication.exec_())
