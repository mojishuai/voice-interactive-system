"""
PyQt5 GUI模块 - 语音交互界面
"""

import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTextEdit, QStatusBar, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor


class VoiceInteractionGUI(QMainWindow):
    """语音交互GUI"""
    
    def __init__(self, audio_manager, asr, tts, cmd_parser, network, config):
        """初始化GUI"""
        super().__init__()
        
        self.audio_manager = audio_manager
        self.asr = asr
        self.tts = tts
        self.cmd_parser = cmd_parser
        self.network = network
        self.config = config
        
        self.is_recording = False
        self.audio_data = None
        
        self.init_ui()
        self.setup_network()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("语音人机交互系统")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("语音人机交互系统")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 状态显示
        status_layout = QHBoxLayout()
        self.status_label = QLabel("状态: 就绪")
        self.device_label = QLabel("设备: 未连接")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.device_label)
        main_layout.addLayout(status_layout)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.record_btn = QPushButton("开始录音 (Space)")
        self.record_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.record_btn.clicked.connect(self.toggle_recording)
        button_layout.addWidget(self.record_btn)
        
        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self.clear_output)
        button_layout.addWidget(self.clear_btn)
        
        main_layout.addLayout(button_layout)
        
        # 输出文本框
        output_label = QLabel("识别结果与执行反馈:")
        main_layout.addWidget(output_label)
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("background-color: #f5f5f5; font-family: 'Courier New';")
        main_layout.addWidget(self.output_text)
        
        # 命令列表
        commands_label = QLabel("支持的命令:")
        main_layout.addWidget(commands_label)
        
        self.commands_text = QTextEdit()
        self.commands_text.setReadOnly(True)
        self.commands_text.setMaximumHeight(150)
        self.commands_text.setStyleSheet("background-color: #f0f0f0;")
        
        # 显示所有支持的命令
        commands = self.cmd_parser.get_all_commands()
        commands_str = ", ".join(commands)
        self.commands_text.setText(commands_str)
        main_layout.addWidget(self.commands_text)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        # 设置快捷键
        self.setFocusPolicy(Qt.StrongFocus)
    
    def setup_network(self):
        """设置网络连接"""
        def on_server_response(message):
            self.update_output(f"[服务器] {message}")
        
        if self.network.connect(callback=on_server_response):
            self.device_label.setText("设备: 已连接")
            self.device_label.setStyleSheet("color: green;")
        else:
            self.device_label.setText("设备: 连接失败")
            self.device_label.setStyleSheet("color: red;")
    
    def toggle_recording(self):
        """切换录音"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录音"""
        self.is_recording = True
        self.record_btn.setText("停止录音 (Space)")
        self.record_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 14px;")
        self.status_label.setText("状态: 录音中...")
        self.statusBar().showMessage("正在录音...")
        
        self.audio_manager.start_recording()
    
    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        self.record_btn.setText("开始录音 (Space)")
        self.record_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 14px;")
        self.status_label.setText("状态: 处理中...")
        self.statusBar().showMessage("处理音频...")
        
        # 获取音频数据
        self.audio_data = self.audio_manager.stop_recording()
        
        # 处理音频
        self.process_audio()
    
    def process_audio(self):
        """处理音频"""
        if len(self.audio_data) == 0:
            self.update_output("[错误] 没有录入音频")
            self.status_label.setText("状态: 就绪")
            return
        
        # 语音识别
        self.update_output("[识别中...] 处理音频...")
        asr_result = self.asr.recognize(self.audio_data)
        
        if not asr_result['success']:
            self.update_output(f"[识别失败] {asr_result['error']}")
            self.status_label.setText("状态: 识别失败")
            return
        
        text = asr_result['text']
        confidence = asr_result['confidence']
        
        self.update_output(f"[识别结果] {text}")
        self.update_output(f"[置信度] {confidence:.2%}")
        
        # 命令解析
        self.update_output("[解析中...] 解析命令...")
        cmd_result = self.cmd_parser.parse(text)
        
        if not cmd_result['success']:
            feedback = f"[解析失败] {cmd_result['error']}"
            self.update_output(feedback)
            # 播放反馈语音
            audio = self.tts.synthesize(cmd_result['error'])
            if len(audio) > 0:
                self.audio_manager.play_audio(audio)
            self.status_label.setText("状态: 解析失败")
            return
        
        self.update_output(f"[命令] {cmd_result['desc']}")
        
        # 执行命令
        self.update_output("[执行中...] 向服务器发送命令...")
        self.network.send_command({
            'type': cmd_result['type'],
            'package': cmd_result['command'].get('package') if isinstance(cmd_result['command'], dict) else None,
            'activity': cmd_result['command'].get('activity') if isinstance(cmd_result['command'], dict) else None,
            'command': cmd_result['command'] if isinstance(cmd_result['command'], str) else None
        })
        
        # 合成反馈语音
        feedback = f"已执行: {cmd_result['desc']}"
        self.update_output(f"[反馈] {feedback}")
        
        audio = self.tts.synthesize(feedback)
        if len(audio) > 0:
            self.audio_manager.play_audio(audio)
        
        self.status_label.setText("状态: 执行完成")
        self.statusBar().showMessage("就绪")
    
    def update_output(self, text: str):
        """更新输出"""
        self.output_text.append(text)
        # 自动滚动到底部
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )
    
    def clear_output(self):
        """清空输出"""
        self.output_text.clear()
    
    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Space and not event.isAutoRepeat():
            self.toggle_recording()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            '确认',
            '确定要退出吗?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.audio_manager.cleanup()
            self.network.disconnect()
            event.accept()
        else:
            event.ignore()
    
    def run(self):
        """运行GUI"""
        self.show()
        sys.exit(QApplication.instance().exec_())
